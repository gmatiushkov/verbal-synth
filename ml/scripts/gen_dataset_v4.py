#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_dataset_v4.py — оркестратор генерации датасета v4 (подход A6-Claude, ГИБРИД).

Поток:
  v4_sampler  → спеки (роль + банк + уровни осей) с бюджетом покрытия
  v4_specs    → каркас патча (реальные единицы) + locks (банк/октава/Vocal-позиция)
  ЗДЕСЬ       → system-промпт v4 (факты движка + позиция WT + контракт + стили описаний),
                батч по роли → Claude доводит непрерывные параметры и пишет N описаний,
                пост-обработчик ФОРСИТ locks (Claude не уводит определяющее → нет «размазывания»
                банка/октавы, давшего потолок v3), real→norm, чекпойнт в patches store.
  --build      патчи-store → dataset.jsonl (1 строка на описание, вектор 38 в PARAM_ORDER).

Переиспользует API-слой generate_dataset (call_model: ретраи, стрим-fallback, деградация
thinking; extract_json; checkpoint), конфиг API и param_convert.

Режимы:
  --dry-run                собрать промпт + пример батча, без API (без трат)
  --roles R...             только эти роли (деф. все)
  --per-role N             патчей на роль (деф. 40; тест — ставь 2-4)
  --batch-size N           спек на один запрос (деф. 5)
  --out PATH               store-файл (деф. зависит от режима)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import param_convert as pc
import generate_dataset as g3          # переиспользуем API-слой и сборку таблиц
import v4_specs as vs
import v4_sampler as vsamp

ROOT = g3.ROOT                          # .../ml
CONFIG = g3.CONFIG
DATA = g3.DATA
SYS_TMPL_V4 = CONFIG / "v4" / "system_prompt_v4.md"

# Стили описаний (регистры речи) — учим модель ВСЕМУ спектру слов о звуке.
STYLES = [
    "функциональное (роль в миксе / жанр / назначение)",
    "по инструменту-аналогу (на что похоже, имя инструмента)",
    "психоакустическое (тембр: тёплый/резкий/полый/стеклянный…)",
    "эмоциональное (настроение, ассоциация)",
    "метафора/образ (кросс-сенсорно: как лёд, бархат, лазер…)",
    "телеграфное (2-4 слова, как поисковый запрос)",
]


# ── сборка system-промпта v4 ────────────────────────────────────────────────────
def build_position_semantics(attrs):
    ps = attrs.get("position_semantics", {})
    lines = []
    for bank in pc.BANK_NAMES:
        b = ps.get(bank)
        if not b:
            continue
        anchors = "; ".join(f"{k}%→{v}" for k, v in b.get("anchors", {}).items())
        lines.append(f"• {bank}: {b['meaning']} | яркость {b['couples_brightness']} | {anchors}")
    return "\n".join(lines)


ENGINE_LIMITS = (
    "• Резонанс Q 0.5–10; cutoff 20–18000 Гц (лог-кривая).\n"
    "• Времена ADSR: attack 0.5мс–5с, decay 1мс–5с, release 5мс–10с (лог-кривая).\n"
    "• LFO 0.01–20 Гц; lfo*_to_pitch до ±200 ц; lfo1_to_filter до ±2 окт; fenv_amount до ±4 окт.\n"
    "• НЕТ pitch-огибающей: огибающая фильтра (fenv) двигает ТОЛЬКО LP-cutoff и позицию WT "
    "(fenv_to_wt), но НЕ высоту тона. One-shot питч-дроп/свип недостижим; периодическое "
    "движение высоты — только через lfo*_to_pitch.\n"
    "• osc*_octave целые −2…+2; osc2_semitones целые ±24; osc2_detune ±50 ц."
)


def build_system_prompt_v4(param_ref, wt_doc, attrs):
    tmpl = SYS_TMPL_V4.read_text(encoding="utf-8")
    styles_txt = "\n".join(f"  {i+1}) {s}" for i, s in enumerate(STYLES))
    repl = {
        "{{PARAM_TABLE}}": g3.build_param_table(param_ref),
        "{{WAVETABLE_DOC}}": g3.build_wavetable_doc(wt_doc, param_ref),
        "{{POSITION_SEMANTICS}}": build_position_semantics(attrs),
        "{{BANK_NAMES}}": ", ".join(pc.BANK_NAMES),
        "{{LFO_SHAPES}}": ", ".join(pc.LFO_SHAPE_NAMES),
        "{{ENGINE_LIMITS}}": ENGINE_LIMITS,
        "{{N_DESC}}": str(len(STYLES)),
        "{{STYLES}}": styles_txt,
    }
    for k, v in repl.items():
        tmpl = tmpl.replace(k, v)
    return tmpl


# ── форматирование спеки для user-сообщения ──────────────────────────────────────
def _skeleton_str(real_full, locked):
    """Каркас 38 параметров в одну компактную строку; 🔒 — залоченные."""
    parts = []
    for name in pc.PARAM_ORDER:
        val = g3._fewshot_value(name, real_full[name])
        lock = "🔒" if name in locked else ""
        parts.append(f"{name}={val}{lock}")
    return " ".join(parts)


def _palette_str(spec, lex):
    pal = vs.lexicon_palette(spec, lex)
    chunks = []
    for key, words in pal.items():
        chunks.append(", ".join(words[:7]))
    return " ┃ ".join(chunks)


def resolve_for_prompt(spec, roles, attrs, lex):
    """Резолв спеки + готовые строки для промпта. Возвращает dict с locked для пост-обработки."""
    real, locked, character, osc2_active = vs.resolve_skeleton(spec, roles, attrs)
    # полный каркас 38 (через round-trip заполняем неуказанные нейтралью) — для показа
    norm = pc.patch_real_to_norm(real)
    real_full = pc.patch_norm_to_real(norm)
    return {
        "spec": spec, "locked": locked, "character": character,
        "osc2_active": osc2_active, "real_full": real_full,
        "skeleton_str": _skeleton_str(real_full, locked),
        "palette_str": _palette_str(spec, lex),
    }


def build_batch_message(resolved_list, roles, lex):
    n = len(resolved_list)
    head = (
        f"Сгенерируй {n} {'патч' if n == 1 else 'патчей'} по спекам ниже. Для КАЖДОГО верни "
        f"объект в массиве \"patches\" с ТЕМ ЖЕ spec_id, доведёнными 38 параметрами (реальные "
        f"единицы; 🔒 — вернуть без изменений) и {len(STYLES)} описаниями разных регистров.\n"
    )
    blocks = []
    for rz in resolved_list:
        spec = rz["spec"]
        role_words = lex["roles"].get(spec["role"], [spec["role"]])
        axes_txt = ", ".join(f"{ax}={lv}" for ax, lv in spec["axis_levels"].items())
        b = (
            f"\n[{spec['spec_id']}] роль «{role_words[0]}» ({spec['role']}), банк {spec['bank']}.\n"
            f"  Оси: {axes_txt}\n"
            f"  Каркас: {rz['skeleton_str']}\n"
        )
        if rz["character"]:
            b += f"  Характер: {rz['character']} — вырази параметрически и в словах.\n"
        b += f"  Палитра (черпай, не копируй дословно): {rz['palette_str']}\n"
        blocks.append(b)
    return head + "".join(blocks)


# ── разбор ответа + пост-обработка locks ─────────────────────────────────────────
def process_patch(p, resolved_by_id, model):
    """Returned patch dict → store-entry или (None, reason). Форсит locks."""
    spec_id = p.get("spec_id")
    rz = resolved_by_id.get(spec_id)
    if rz is None:
        return None, f"неизвестный spec_id={spec_id}"
    raw = p.get("params")
    if not isinstance(raw, dict):
        return None, f"{spec_id}: нет объекта params"
    real_locked, overrides = vs.enforce_locks(raw, rz["locked"])
    try:
        norm = pc.patch_real_to_norm(real_locked)
        real_clean = pc.patch_norm_to_real(norm)
    except Exception as e:
        return None, f"{spec_id}: конверсия не удалась: {e}"
    present = sum(1 for k in pc.PARAM_ORDER if k in raw and raw[k] is not None)
    if present < 30:
        return None, f"{spec_id}: прислано лишь {present}/38 параметров"
    descs = p.get("descriptions", [])
    if not isinstance(descs, list) or len([d for d in descs if str(d).strip()]) < 2:
        return None, f"{spec_id}: мало описаний"
    spec = rz["spec"]
    role = spec["role"]
    entry = {
        "id": spec_id,
        "spec_id": spec_id,
        "role": role,
        "bank": spec["bank"],
        "category": ROLE_CAT.get(role, role),
        "target": role,
        "axis_levels": spec["axis_levels"],
        "character": rz["character"],
        "concept": p.get("concept", spec_id),
        "source": model,
        "osc2_active": bool(p.get("osc2_active", rz["osc2_active"])),
        "lock_overrides": {k: [str(o), str(nv)] for k, (o, nv) in overrides.items()},
        "params": norm,
        "params_real": real_clean,
        "descriptions": [str(d).strip() for d in descs if str(d).strip()],
    }
    return entry, None


# роль → категория (для отчётов/совместимости с v3-анализом)
ROLE_CAT = {}


def _fill_role_cat(roles):
    for rn, r in roles.items():
        ROLE_CAT[rn] = r.get("category", rn)


# ── dataset.jsonl из store ───────────────────────────────────────────────────────
def build_dataset_jsonl(store, out_path):
    rows = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for e in store["entries"]:
            vec = pc.norm_vector(e["params"])
            for text in e["descriptions"]:
                f.write(json.dumps(
                    {"source_patch": e["id"], "text": text, "params": vec},
                    ensure_ascii=False) + "\n")
                rows += 1
    return rows


# ── главный цикл генерации ───────────────────────────────────────────────────────
def generate(client, model, system_blocks, store, store_path,
             specs, roles, attrs, lex, batch_size, max_tokens, verbose):
    done_ids = {e["id"] for e in store["entries"]}
    # группируем по роли (порядок ролей сохраняем)
    by_role = {}
    for s in specs:
        if s["spec_id"] in done_ids:
            continue
        by_role.setdefault(s["role"], []).append(s)
    total_todo = sum(len(v) for v in by_role.values())
    if total_todo == 0:
        print("  все спеки уже сгенерированы — нечего делать.")
        return 0
    print(f"  к генерации: {total_todo} спек по {len(by_role)} ролям "
          f"(уже есть {len(done_ids)}).")

    produced = 0
    for role, rspecs in by_role.items():
        for i in range(0, len(rspecs), batch_size):
            batch = rspecs[i:i + batch_size]
            resolved = [resolve_for_prompt(s, roles, attrs, lex) for s in batch]
            resolved_by_id = {r["spec"]["spec_id"]: r for r in resolved}
            user_text = build_batch_message(resolved, roles, lex)
            try:
                data, usage = g3.call_model(client, model, system_blocks, user_text,
                                            max_tokens, "medium", verbose)
            except Exception as e:
                print(f"    ОШИБКА батча [{role} {i}]: {e} — пропуск (прогресс сохранён).")
                continue
            patches = data.get("patches", []) if isinstance(data, dict) else []
            if not patches:
                print(f"    пустой батч [{role} {i}] — пропуск.")
                continue
            added = 0
            for p in patches:
                entry, reason = process_patch(p, resolved_by_id, model)
                if entry is None:
                    if verbose:
                        print(f"    ⚠ {reason}")
                    continue
                if entry["id"] in {e["id"] for e in store["entries"]}:
                    continue
                if entry["lock_overrides"] and verbose:
                    print(f"      locks форснуты [{entry['id']}]: "
                          f"{list(entry['lock_overrides'].keys())}")
                store["entries"].append(entry)
                added += 1
                produced += 1
            g3.save_store(store_path, store)   # чекпойнт после каждого батча
            u = ""
            if usage:
                u = f" (in={getattr(usage,'input_tokens','?')}, out={getattr(usage,'output_tokens','?')})"
            print(f"    [{role}] батч +{added}/{len(batch)} → всего {len(store['entries'])}{u}")
    return produced


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Генерация датасета VerbalSynth v4 (A6-Claude, гибрид).")
    ap.add_argument("--roles", nargs="*", help="только эти роли (деф. все)")
    ap.add_argument("--per-role", type=int, default=40, help="патчей на роль (деф. 40; тест 2-4)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--batch-size", type=int, default=5, help="спек на запрос (деф. 5)")
    ap.add_argument("--max-tokens", type=int, default=24000)
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", default=None, help="store-файл (patches JSON)")
    ap.add_argument("--dataset", default=None, help="dataset.jsonl (деф. рядом со store)")
    ap.add_argument("--specs", default=None, help="готовый файл спек (вместо инлайн-сэмпла)")
    ap.add_argument("--dry-run", action="store_true", help="промпт + пример батча, без API")
    ap.add_argument("--build", action="store_true", help="только пересобрать dataset.jsonl из store")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    verbose = not args.quiet
    roles, attrs, lex = vs.load_specs()
    issues = vs.validate(roles, attrs, lex)
    if issues:
        sys.exit("Спеки v4 не валидны:\n  " + "\n  ".join(issues))
    _fill_role_cat(roles)

    is_test = (args.per_role <= 6) or bool(args.roles)
    if args.out:
        store_path = Path(args.out)
    elif is_test:
        store_path = DATA / "test_batch" / "v4" / "patches_v4_test.json"
    else:
        store_path = DATA / "v4" / "patches_v4.json"
    dataset_path = Path(args.dataset) if args.dataset else store_path.with_name(
        store_path.stem.replace("patches", "dataset") + ".jsonl")

    # режим только сборки jsonl
    if args.build:
        store = g3.load_store(store_path)
        rows = build_dataset_jsonl(store, dataset_path)
        print(f"dataset собран: {len(store['entries'])} патчей → {rows} строк → {dataset_path}")
        return

    # спеки
    if args.specs:
        specs = json.loads(Path(args.specs).read_text(encoding="utf-8-sig"))["specs"]
    else:
        specs = vsamp.sample_all(roles, attrs, per_role=args.per_role,
                                 only_roles=args.roles, seed=args.seed)

    param_ref = g3.load_json(g3.PARAM_REF)
    wt_doc = g3.load_json(g3.WT_DOC)
    system_prompt = build_system_prompt_v4(param_ref, wt_doc, attrs)
    model = args.model or g3.load_api_config()[2]

    print("=" * 72)
    print(f"v4 генерация · спек: {len(specs)} · батч: {args.batch_size} · "
          f"описаний/патч: {len(STYLES)}")
    print(f"System-промпт: ~{len(system_prompt)} символов (≈{len(system_prompt)//4} ток.)")
    print(f"Store: {store_path}")
    print(f"Dataset: {dataset_path}")
    print(f"Модель: {model}")
    vsamp.coverage_report(specs, roles, attrs)
    print("=" * 72)

    if args.dry_run:
        print("\n──── SYSTEM PROMPT (dry-run) ────\n")
        print(system_prompt)
        print("\n──── ПРИМЕР USER-СООБЩЕНИЯ (первый батч) ────\n")
        ex = specs[:args.batch_size]
        resolved = [resolve_for_prompt(s, roles, attrs, lex) for s in ex]
        print(build_batch_message(resolved, roles, lex))
        return

    base_url, auth_token, _ = g3.load_api_config()
    if not auth_token:
        sys.exit("Нет API-ключа. Задайте ANTHROPIC_AUTH_TOKEN или ml/config/api_config.local.json")
    try:
        import anthropic
    except ImportError:
        sys.exit("Не установлен пакет 'anthropic'. pip install anthropic")
    client_kwargs = {"auth_token": auth_token, "timeout": 600.0, "max_retries": 3}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = anthropic.Anthropic(**client_kwargs)
    system_blocks = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]

    store = g3.load_store(store_path)
    if "version" not in store or not store.get("version", "").startswith("4"):
        store["version"] = "4.0"
    t0 = time.time()
    produced = generate(client, model, system_blocks, store, store_path,
                        specs, roles, attrs, lex, args.batch_size, args.max_tokens, verbose)
    rows = build_dataset_jsonl(store, dataset_path)
    dt = (time.time() - t0) / 60.0
    print("=" * 72)
    print(f"Готово. Новых патчей: {produced}. Всего: {len(store['entries'])}. "
          f"Строк в датасете: {rows}. Время: {dt:.0f} мин.")
    print(f"Store: {store_path}\nDataset: {dataset_path}")
    print(f"Дальше: python ml/scripts/validate_patches.py --in {store_path}  (ревью)")


if __name__ == "__main__":
    main()
