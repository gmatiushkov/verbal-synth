#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dataset.py — СБОРКА датасета v5 (DATASET_v5_PLAN.md §7 Шаг 4).

Конвейер:
  1) v5_sampler.sample        — спеки (цель/роль/банк/оси) по таксономии (без LLM);
  2) param_rules.generate     — 38 norm на спеку (детерминированно, без LLM); для канонического
     варианта цели с УТВЕРЖДЁННЫМ реф-якорем берём параметры якоря (ground truth, не выход генератора);
  3) Claude (дёшево, батчами) — ТОЛЬКО короткие описания из смысловой палитры спеки (роль+оси+лексикон);
  4) строки датасета          — 1 строка на описание: {text, params(38 norm), meta} → dataset.jsonl.

Описания — единственная работа LLM. Дешёвая модель + короткий выход. Кэш системного промпта у
прокси не переиспользуется — поэтому батчим по многу патчей в один запрос.

Запуск:
  python ml/scripts/build_dataset.py --per-target 4 --dry-run     # план + образцы + проекция трат
  python ml/scripts/build_dataset.py --per-target 1 --limit 2     # смоук-тест (2 батча через API)
  python ml/scripts/build_dataset.py --total 600 --out ml/data/v5/dataset.jsonl
"""

import argparse
import io
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import generate_dataset as gd      # обвязка API: call_model / load_api_config / load_json / build_*
import param_convert as pc
import param_rules
import v4_specs
import v5_sampler

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]                 # .../ml
CONFIG = ROOT / "config"
DESC_TMPL = CONFIG / "system_prompt_descriptions.md"
REF_STORE = ROOT / "data" / "reference" / "reference_anchors.json"
DEFAULT_OUT = ROOT / "data" / "v5" / "dataset.jsonl"
MANIFEST = "manifest.json"                                 # рядом с dataset.jsonl: спеки+params+провенанс

# Модель для перефраза описаний. На тарифе юзера доступны только Opus и Sonnet (haiku нет) —
# берём Sonnet (Opus для перефраза избыточен и дороже). Переопределяется --desc-model.
DEFAULT_DESC_MODEL = "claude-sonnet-4-6"
PALETTE_CAP = 18                                           # слов в палитре на патч (компактный промпт)


def load_anchor_params():
    """target -> norm-params утверждённого реф-якоря (ground truth для канонического варианта)."""
    if not REF_STORE.exists():
        return {}
    store = gd.load_json(REF_STORE)
    out = {}
    for e in store.get("entries", []):
        if e.get("approved") and isinstance(e.get("params"), dict) and e.get("target"):
            out[e["target"]] = e["params"]                 # последний утверждённый по цели
    return out


def build_palette(spec, lex):
    """Смысловые слова для описания: дескрипторы цели ⊕ слова КАЖДОГО уровня осей ⊕ слова роли.
    Порядок важен: сперва идентичность цели, затем ОБЯЗАТЕЛЬНО слова осей (чтобы вариант с
    другой яркостью/атакой отличался в описании от канона — иначе текст одинаков, а params разные),
    роль-синонимы — добивка. Per-source cap, чтобы 8 синонимов роли не вытеснили слова осей."""
    words, seen = [], set()

    def add(seq, cap):
        c = 0
        for w in seq or []:
            k = w.strip().lower()
            if k and k not in seen:
                seen.add(k)
                words.append(w)
                c += 1
                if c >= cap:
                    break

    add(spec.get("descriptors"), 6)                        # имена/синонимы цели — самые важные
    for ax, lv in spec.get("axis_levels", {}).items():     # характер именно этого варианта
        add(lex["axis_levels"].get(f"{ax}.{lv}"), 2)
    add(lex["roles"].get(spec["role"]), 3)                 # добивка синонимами роли
    return words[:PALETTE_CAP]


def desc_system_prompt():
    return DESC_TMPL.read_text(encoding="utf-8")


def build_desc_user_message(batch, lex, n_desc):
    """batch: список (id, spec). Запрос на N описаний каждому. БЕЗ параметров — только семантика."""
    lines = [f"Опиши КАЖДЫЙ звук ниже. Для каждого id верни {n_desc} РАЗНЫХ запросов "
             f"(в основном короткие, 1–4 слова; 1–2 фразы; стили перемешай). Пиши про звук, не про параметры.\n"]
    for i, spec in batch:
        pal = ", ".join(build_palette(spec, lex))
        lines.append(f"[id={i}] звук: «{spec['target']}» (роль-архетип: {spec['role']})")
        lines.append(f"    палитра: {pal}")
    lines.append(f'\nФормат: {{"items":[{{"id":1,"descriptions":["...", ...]}}, ...]}} — строго JSON, '
                 f"без текста вне JSON, без вызова инструментов.")
    return "\n".join(lines)


def params_for(spec, roles, attrs, anchors):
    """38 norm для спеки. Канон + есть утверждённый якорь цели → параметры якоря (ground truth)."""
    if spec.get("is_canonical") and spec["target"] in anchors:
        return anchors[spec["target"]], "anchor"
    return param_rules.generate(spec, roles, attrs, mode="rules"), "rules"


def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# ── проекция стоимости (dry-run) ──────────────────────────────────────────────
def estimate_cost(specs, sys_len, sample_user_len, batch, n_desc, desc_model):
    """Грубая оценка токенов/$. Прайс — ориентировочный (haiku-класс); печатаем оговорку."""
    n_batches = math.ceil(len(specs) / batch)
    in_per_batch = (sys_len + sample_user_len) / 4               # ~4 симв/токен
    # выход: n_desc описаний на патч, ~9 токенов на короткое описание + JSON-обвязка
    out_per_batch = batch * n_desc * 9 + batch * 6
    in_tok = int(in_per_batch * n_batches)
    out_tok = int(out_per_batch * n_batches)
    # ориентировочные ставки (sonnet-класс), $/Mtok
    P_IN, P_OUT = 3.0, 15.0
    usd = in_tok / 1e6 * P_IN + out_tok / 1e6 * P_OUT
    rows = len(specs) * n_desc
    print("── ПРОЕКЦИЯ (грубо) ──")
    print(f"  патчей: {len(specs)} | батчей: {n_batches} (по {batch}) | описаний/патч: {n_desc}")
    print(f"  строк датасета (text->params): ~{rows}")
    print(f"  токены: in≈{in_tok:,} (sys кэш у прокси НЕ переиспользуется → ×{n_batches}), out≈{out_tok:,}")
    print(f"  ≈ ${usd:,.2f} при ставках sonnet-класса (in ${P_IN}/Mtok, out ${P_OUT}/Mtok) — ОРИЕНТИР, "
          f"модель {desc_model}")
    print(f"  время: ~{n_batches*8//60} мин при ~8 c/батч (грубо)")


# ── запись датасета ───────────────────────────────────────────────────────────
def write_rows(out_path, rows, mode="a"):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(out_path, mode, encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def save_manifest(out_path, manifest):
    p = out_path.parent / MANIFEST
    tmp = p.with_suffix(".tmp")
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    tmp.replace(p)


def main():
    ap = argparse.ArgumentParser(description="Сборка датасета v5 (параметры из кода + описания Claude).")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--per-target", type=int, help="вариантов на цель")
    g.add_argument("--total", type=int, help="всего патчей (доли категорий)")
    ap.add_argument("--specs", default=None, help="готовый JSON спек (вместо сэмплинга на лету)")
    ap.add_argument("--n-desc", type=int, default=6, help="описаний на патч (деф. 6)")
    ap.add_argument("--batch", type=int, default=20, help="патчей в одном запросе описаний (деф. 20)")
    ap.add_argument("--limit", type=int, default=None, help="взять только первые N батчей (смоук-тест)")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="выход .jsonl")
    ap.add_argument("--desc-model", default=DEFAULT_DESC_MODEL, help="модель для описаний (дешёвая)")
    ap.add_argument("--max-tokens", type=int, default=8000, help="лимит выхода на батч описаний")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true", help="план + образцы + проекция, без API")
    ap.add_argument("--fresh", action="store_true", help="перезаписать выход (иначе дозапись)")
    args = ap.parse_args()

    if args.per_target is None and args.total is None and not args.specs:
        args.per_target = 4

    roles, attrs, lex = v4_specs.load_specs()
    anchors = load_anchor_params()

    # 1) спеки
    if args.specs:
        specs = gd.load_json(Path(args.specs))["specs"]
    else:
        mp = v5_sampler._load(v5_sampler.MAP_PATH)
        taxonomy = v5_sampler._load(v5_sampler.TAXONOMY)
        specs = v5_sampler.sample(roles, attrs, mp, taxonomy,
                                  per_target=args.per_target, total=args.total, seed=args.seed)

    out_path = Path(args.out)
    sys_prompt = desc_system_prompt()
    batches = list(chunked(list(enumerate(specs, 1)), args.batch))
    if args.limit:
        batches = batches[: args.limit]

    src_counts = Counter()
    for s in specs:
        _, src = params_for(s, roles, attrs, anchors)
        src_counts[src] += 1

    print("=" * 74)
    print(f"Сборка датасета v5 · патчей={len(specs)} · батчей={len(batches)} (по {args.batch}) · "
          f"описаний/патч={args.n_desc}")
    print(f"  params: rules={src_counts.get('rules',0)}, anchor(ground-truth)={src_counts.get('anchor',0)} "
          f"(целей с утверждённым якорем: {len(anchors)})")
    print(f"  модель описаний: {args.desc_model} | system-промпт ~{len(sys_prompt)} симв.")
    print(f"  выход: {out_path}")
    print("=" * 74)

    sample_user = build_desc_user_message(batches[0], lex, args.n_desc) if batches else ""
    estimate_cost(specs, len(sys_prompt), len(sample_user), args.batch, args.n_desc, args.desc_model)

    if args.dry_run:
        s0 = specs[0]
        p0, src0 = params_for(s0, roles, attrs, anchors)
        real0 = pc.patch_norm_to_real(p0)
        print("\n──── ОБРАЗЕЦ СПЕКИ ────")
        print(f"  target={s0['target']} | role={s0['role']} | bank={s0['bank']} | "
              f"variant={s0['variant']} | params_src={src0}")
        print(f"  axis_levels={s0['axis_levels']}")
        print(f"  палитра={build_palette(s0, lex)}")
        print("  параметры (реальные, выборка): "
              + ", ".join(f"{k}={pc.format_real(k, real0[k])}" for k in
                          ["osc1_table", "osc1_position", "osc1_octave", "lp_cutoff",
                           "amp_attack", "amp_decay", "amp_sustain", "amp_release"]))
        print("\n──── ОБРАЗЕЦ USER-СООБЩЕНИЯ (первый батч, усечён) ────\n")
        print(sample_user[:1600] + ("\n…(усечено)" if len(sample_user) > 1600 else ""))
        return

    # ── API ──
    base_url, auth_token, cfg_model = gd.load_api_config()
    if not auth_token:
        sys.exit("Нет API-ключа (ANTHROPIC_AUTH_TOKEN или ml/config/api_config.local.json).")
    try:
        import anthropic
    except ImportError:
        sys.exit("Нет пакета 'anthropic' (pip install anthropic).")
    client_kwargs = {"auth_token": auth_token, "timeout": 600.0, "max_retries": 3}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = anthropic.Anthropic(**client_kwargs)
    system_blocks = [{"type": "text", "text": sys_prompt, "cache_control": {"type": "ephemeral"}}]

    if args.fresh and out_path.exists():
        out_path.unlink()

    # манифест: спеки + параметры (раз посчитанные) — чтобы не пересчитывать и хранить провенанс
    manifest = {"version": "5.0", "seed": args.seed, "n_desc": args.n_desc,
                "desc_model": args.desc_model, "specs": []}
    spec_params = {}
    for i, s in enumerate(specs, 1):
        p, src = params_for(s, roles, attrs, anchors)
        spec_params[i] = p
        manifest["specs"].append({"row_id": i, **{k: s[k] for k in
                                  ("target", "category", "role", "bank", "variant", "is_canonical")},
                                  "axis_levels": s["axis_levels"], "params_src": src})

    t0 = time.time()
    total_rows, in_tok, out_tok, done_patches = 0, 0, 0, 0
    for bi, batch in enumerate(batches, 1):
        user_text = build_desc_user_message(batch, lex, args.n_desc)
        try:
            data, usage = gd.call_model(client, args.desc_model, system_blocks, user_text,
                                        args.max_tokens, "low", verbose=True)
        except Exception as e:
            print(f"  ✗ батч {bi}/{len(batches)}: {e} — пропуск")
            continue
        items = {it.get("id"): it.get("descriptions", []) for it in data.get("items", [])}
        rows = []
        for i, spec in batch:
            descs = items.get(i) or items.get(str(i)) or []
            params = spec_params[i]
            # train.py ждёт params СПИСКОМ из 38 в порядке PARAM_ORDER (как v3-датасет), не словарём
            params_list = [params[n] for n in pc.PARAM_ORDER]
            for d in descs:
                if not isinstance(d, str) or not d.strip():
                    continue
                rows.append({"text": d.strip(), "params": params_list,
                             "source_patch": spec["spec_id"],   # train.py: сплит по патчу (анти-течь)
                             "target": spec["target"], "role": spec["role"],
                             "category": spec["category"], "variant": spec["variant"],
                             "params_src": manifest["specs"][i - 1]["params_src"],
                             "source": "v5"})
            done_patches += 1
        write_rows(out_path, rows, mode="a")
        total_rows += len(rows)
        if usage:
            in_tok += getattr(usage, "input_tokens", 0) or 0
            out_tok += getattr(usage, "output_tokens", 0) or 0
        print(f"  ✓ батч {bi}/{len(batches)}: +{len(rows)} строк (патчей {len(batch)}) · всего {total_rows}")

    save_manifest(out_path, manifest)
    dt = time.time() - t0
    print("=" * 74)
    print(f"Готово. Строк: {total_rows} (патчей {done_patches}). Токены: in={in_tok:,}, out={out_tok:,}.")
    print(f"Время: {dt:.0f} c. Датасет: {out_path} | манифест: {out_path.parent / MANIFEST}")
    print("Дальше: обучение (train.py) с B1-маской неактивных + дискретные как классы.")


if __name__ == "__main__":
    main()
