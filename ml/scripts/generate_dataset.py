#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_dataset.py — Фаза 1/2 пайплайна VerbalSynth (подход v2).

Claude САМ проектирует звук: придумывает задумку, выставляет 38 нормализованных
параметров [0..1] и пишет 6 русских описаний. Один запрос = батч патчей.

Объединяет старые generate_patches.py + generate_texts.py.

Источники (config/):
  - param_reference.json   — 38 параметров + маппинг 0..1↔реальные + правила
  - sound_taxonomy.json    — категории целевых звуков (без диапазонов)
  - system_prompt.md       — шаблон system-промпта ({{PARAM_TABLE}}, {{WAVETABLE_DOC}})
  - wavetable_doc.json      — перцептивные описания банков (Фаза 0)

Режимы:
  --test                 ~N патчей на каждую категорию (по умолчанию 4)
  --all                  полный датасет по долям share из taxonomy
  --category ID --count N конкретная категория
  --dry-run              собрать промпт и вывести (без вызова API, без трат)

Чекпойнты: результат дописывается в out-файл после КАЖДОГО успешного батча,
запуск можно прерывать и продолжать — уже сгенерированное не перегенерируется.

API: прокси aiprimetech (Anthropic-совместимый). Креды берутся из
  1) переменных окружения ANTHROPIC_AUTH_TOKEN / ANTHROPIC_BASE_URL, либо
  2) ml/config/api_config.local.json (gitignored).
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# ── Пути ──────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parents[1]          # .../ml
CONFIG    = ROOT / "config"
DATA      = ROOT / "data"
PARAM_REF = CONFIG / "param_reference.json"
TAXONOMY  = CONFIG / "sound_taxonomy.json"
SYS_TMPL  = CONFIG / "system_prompt.md"
WT_DOC    = CONFIG / "wavetable_doc.json"
API_CFG   = CONFIG / "api_config.local.json"

DEFAULT_MODEL = "claude-opus-4-8"


# ── Утилиты загрузки ──────────────────────────────────────────────────────────
def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_api_config():
    """env > api_config.local.json. Возвращает (base_url, auth_token, model)."""
    base = os.environ.get("ANTHROPIC_BASE_URL")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    model = os.environ.get("VERBALSYNTH_MODEL")
    if API_CFG.exists():
        cfg = load_json(API_CFG)
        base = base or cfg.get("base_url")
        token = token or cfg.get("auth_token") or cfg.get("api_key")
        model = model or cfg.get("model")
    return base, token, (model or DEFAULT_MODEL)


# ── Сборка system-промпта ─────────────────────────────────────────────────────
def build_param_table(param_ref) -> str:
    """Компактный, но полный список параметров — desc уже содержит ключевые точки."""
    lines = []
    for p in param_ref["params"]:
        extra = ""
        if "min" in p and "max" in p:
            extra = f" [{p['min']}–{p['max']} {p.get('unit', '')}]".rstrip()
        lines.append(f"[{p['i']:>2}] {p['name']} ({p['kind']}){extra}: {p['desc']}")
    return "\n".join(lines)


def build_wavetable_doc(wt_doc, param_ref) -> str:
    """name + perceptual_summary + position_map для каждого банка."""
    # name -> селектор osc_table (из param_reference.banks: {"0.0":"Basic",...})
    name_to_sel = {v: k for k, v in param_ref["banks"].items()}
    blocks = []
    for bank in wt_doc["banks"]:
        name = bank["name"]
        sel = name_to_sel.get(name, "?")
        ps = bank.get("perceptual_summary", "").strip()
        pm = bank.get("position_map", {})
        pm_lines = "; ".join(f"{k} — {v}" for k, v in pm.items())
        blocks.append(f"### {name} (osc_table={sel})\n{ps}\nПозиция (морф): {pm_lines}")
    return "\n\n".join(blocks)


def build_system_prompt(param_ref, wt_doc) -> str:
    tmpl = SYS_TMPL.read_text(encoding="utf-8")
    tmpl = tmpl.replace("{{PARAM_TABLE}}", build_param_table(param_ref))
    tmpl = tmpl.replace("{{WAVETABLE_DOC}}", build_wavetable_doc(wt_doc, param_ref))
    return tmpl


# ── JSON-схема вывода (structured outputs) ────────────────────────────────────
STYLES = ["functional", "instrument", "psychoacoustic", "emotional", "metaphor", "telegraphic"]


def build_output_schema(param_ref):
    names = [p["name"] for p in param_ref["params"]]
    params_schema = {
        "type": "object",
        "properties": {n: {"type": "number", "minimum": 0, "maximum": 1} for n in names},
        "required": names,
        "additionalProperties": False,
    }
    desc_schema = {
        "type": "object",
        "properties": {
            "style": {"type": "string", "enum": STYLES},
            "text": {"type": "string"},
        },
        "required": ["style", "text"],
        "additionalProperties": False,
    }
    patch_schema = {
        "type": "object",
        "properties": {
            "concept": {"type": "string"},
            "category": {"type": "string"},
            "osc2_active": {"type": "boolean"},
            "params": params_schema,
            "descriptions": {"type": "array", "items": desc_schema, "minItems": 6, "maxItems": 6},
        },
        "required": ["concept", "category", "osc2_active", "params", "descriptions"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {"patches": {"type": "array", "items": patch_schema}},
        "required": ["patches"],
        "additionalProperties": False,
    }


# ── User-сообщение на батч ────────────────────────────────────────────────────
def build_user_message(category, targets_slice, n, axes) -> str:
    targets_txt = "\n".join(f"  - {t}" for t in targets_slice)
    axes_txt = "\n".join(f"  · {a}" for a in axes)
    return (
        f"Категория: **{category['name']}** (id: {category['id']}).\n"
        f"Замысел категории: {category['intent']}\n\n"
        f"Спроектируй ровно {n} РАЗНЫХ патчей. Отталкивайся от этих целей "
        f"(можно интерпретировать свободно, но покрой их разнообразно):\n{targets_txt}\n\n"
        f"Обязательно варьируй патчи по осям разнообразия:\n{axes_txt}\n\n"
        f"Требования: никаких близнецов (соседние патчи различаются ≥3 осей); "
        f"часть моно-OSC, часть слойные (OSC2); используй разные банки/приёмы там, где это уместно. "
        f"Для каждого патча — все 38 параметров (значения дискретных строго из snap-наборов) и 6 описаний "
        f"({', '.join(STYLES)}). Верни СТРОГО JSON по схеме, без текста вне JSON."
    )


# ── Вызов модели с мягкой деградацией параметров ──────────────────────────────
def extract_json(text: str):
    """Достаёт JSON-объект из ответа (срезает ```-ограждения и прелюдии)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    # на случай прелюдии — берём от первой { до последней }
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def call_model(client, model, system_blocks, user_text, schema, max_tokens, effort, verbose):
    """
    Пытается structured outputs + thinking, при отказе прокси/SDK деградирует.
    Возвращает (dict, usage|None).
    """
    import anthropic

    base = dict(model=model, max_tokens=max_tokens, system=system_blocks,
                messages=[{"role": "user", "content": user_text}])

    attempts = [
        dict(thinking={"type": "adaptive"},
             output_config={"format": {"type": "json_schema", "name": "patch_batch", "schema": schema},
                            "effort": effort}),
        dict(thinking={"type": "adaptive"},
             output_config={"format": {"type": "json_schema", "name": "patch_batch", "schema": schema}}),
        dict(thinking={"type": "adaptive"}),
        dict(),
    ]

    last_err = None
    for i, extra in enumerate(attempts):
        try:
            kwargs = {**base, **extra}
            # стримим, чтобы не упереться в таймаут на длинном выводе
            try:
                with client.messages.stream(**kwargs) as stream:
                    msg = stream.get_final_message()
            except (anthropic.APIError, TypeError) as stream_err:
                if verbose:
                    print(f"    [stream→create fallback: {type(stream_err).__name__}]")
                msg = client.messages.create(**kwargs)

            text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
            if not text.strip():
                raise ValueError("пустой текстовый ответ")
            data = extract_json(text)
            usage = getattr(msg, "usage", None)
            if i > 0 and verbose:
                print(f"    [деградация: использован вариант запроса #{i}]")
            return data, usage
        except (anthropic.BadRequestError, anthropic.NotFoundError, TypeError) as e:
            last_err = e
            if verbose:
                print(f"    [вариант #{i} отклонён: {type(e).__name__}: {e}; пробую проще]")
            continue
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            if verbose:
                print(f"    [не удалось разобрать JSON (вариант #{i}): {e}]")
            continue
    raise RuntimeError(f"Все варианты запроса не удались. Последняя ошибка: {last_err}")


# ── Хранилище патчей (чекпойнт) ───────────────────────────────────────────────
def load_store(out_path: Path):
    if out_path.exists():
        return load_json(out_path)
    return {"version": "2.0", "entries": []}


def save_store(out_path: Path, store):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    tmp.replace(out_path)


def count_by_category(store, cat_id):
    return sum(1 for e in store["entries"] if e.get("category") == cat_id)


def next_index(store, cat_id):
    mx = 0
    for e in store["entries"]:
        if e.get("category") == cat_id:
            m = re.search(rf"{re.escape(cat_id)}_(\d+)$", e.get("id", ""))
            if m:
                mx = max(mx, int(m.group(1)))
    return mx + 1


# ── Основной цикл генерации одной категории ───────────────────────────────────
def generate_category(client, model, system_blocks, schema, store, out_path,
                      category, axes, target_count, batch_size, max_tokens, effort, verbose):
    have = count_by_category(store, category["id"])
    need = max(0, target_count - have)
    if need == 0:
        print(f"  [{category['id']}] уже есть {have}/{target_count} — пропуск")
        return 0

    print(f"  [{category['id']}] есть {have}, нужно ещё {need} (цель {target_count})")
    targets = category["targets"]
    produced = 0
    t_off = have  # сдвиг по списку целей, чтобы продолжать с нового места

    while produced < need:
        n = min(batch_size, need - produced)
        # вырезаем циклический срез целей для этого батча
        sl = [targets[(t_off + k) % len(targets)] for k in range(n)]
        t_off += n
        user_text = build_user_message(category, sl, n, axes)

        try:
            data, usage = call_model(client, model, system_blocks, user_text,
                                     schema, max_tokens, effort, verbose)
        except Exception as e:
            print(f"    ОШИБКА батча: {e}\n    Прерываю категорию (прогресс сохранён).")
            break

        patches = data.get("patches", [])
        if not patches:
            print("    Пустой батч (0 патчей) — пропуск.")
            continue

        added = 0
        idx = next_index(store, category["id"])
        for p in patches:
            if "params" not in p or len(p["params"]) < 38:
                print(f"    ⚠ патч без полного набора params — пропуск ({p.get('concept')})")
                continue
            entry = {
                "id": f"{category['id']}_{idx:03d}",
                "concept": p.get("concept", f"{category['id']}_{idx}"),
                "category": category["id"],
                "source": model,
                "osc2_active": bool(p.get("osc2_active", False)),
                "params": p["params"],
                "descriptions": p.get("descriptions", []),
            }
            store["entries"].append(entry)
            idx += 1
            added += 1
            produced += 1

        save_store(out_path, store)  # чекпойнт после каждого батча
        u = ""
        if usage:
            u = f" (in={getattr(usage,'input_tokens','?')}, out={getattr(usage,'output_tokens','?')})"
        print(f"    +{added} патчей → всего {count_by_category(store, category['id'])}/{target_count}{u}")

    return produced


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Генерация датасета патчей VerbalSynth (v2).")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--test", action="store_true", help="по N патчей на каждую категорию (см. --count)")
    mode.add_argument("--all", action="store_true", help="полный датасет по долям share")
    mode.add_argument("--category", help="ID одной категории из taxonomy")
    ap.add_argument("--count", type=int, default=None,
                    help="--test: патчей/категория (деф. 4); --category: всего патчей; --all: общий объём (деф. 800)")
    ap.add_argument("--out", default=None, help="выходной JSON (деф. зависит от режима)")
    ap.add_argument("--batch-size", type=int, default=6, help="патчей за один запрос (деф. 6)")
    ap.add_argument("--max-tokens", type=int, default=24000)
    ap.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--model", default=None, help="переопределить модель")
    ap.add_argument("--dry-run", action="store_true", help="собрать промпт и выйти (без API)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    verbose = not args.quiet
    param_ref = load_json(PARAM_REF)
    taxonomy = load_json(TAXONOMY)
    wt_doc = load_json(WT_DOC)
    axes = taxonomy["diversity_axes"]
    cats = {c["id"]: c for c in taxonomy["categories"]}

    system_prompt = build_system_prompt(param_ref, wt_doc)
    schema = build_output_schema(param_ref)

    # план: список (category, target_count)
    if args.category:
        if args.category not in cats:
            sys.exit(f"Неизвестная категория '{args.category}'. Доступно: {', '.join(cats)}")
        plan = [(cats[args.category], args.count or 20)]
        default_out = DATA / f"patches_{args.category}.json"
    elif args.all:
        total = args.count or 800
        plan = [(c, max(1, round(total * c["share"]))) for c in taxonomy["categories"]]
        default_out = DATA / "patches_raw.json"
    else:  # --test (деф.)
        per = args.count or 4
        plan = [(c, per) for c in taxonomy["categories"]]
        default_out = DATA / "test_batch" / "patches_test.json"

    out_path = Path(args.out) if args.out else default_out
    model = args.model or load_api_config()[2]

    print("=" * 70)
    print(f"System-промпт собран: ~{len(system_prompt)} символов "
          f"(≈{len(system_prompt)//4} токенов).")
    print(f"Режим: {'--category '+args.category if args.category else ('--all' if args.all else '--test')}")
    print("План генерации:")
    grand = 0
    for c, n in plan:
        print(f"  {c['id']:<20} {n} патчей × 6 описаний = {n*6}")
        grand += n
    print(f"Итого патчей: {grand} → выход: {out_path}")
    print(f"Модель: {model}")
    print("=" * 70)

    if args.dry_run:
        print("\n──── SYSTEM PROMPT (dry-run) ────\n")
        print(system_prompt)
        print("\n──── ПРИМЕР USER-СООБЩЕНИЯ ────\n")
        c0 = plan[0][0]
        print(build_user_message(c0, c0["targets"][:min(args.batch_size, 6)], min(args.batch_size, 6), axes))
        return

    # ── API клиент ──
    base_url, auth_token, cfg_model = load_api_config()
    if not auth_token:
        sys.exit("Нет API-ключа. Задайте ANTHROPIC_AUTH_TOKEN или ml/config/api_config.local.json")
    try:
        import anthropic
    except ImportError:
        sys.exit("Не установлен пакет 'anthropic'. Установите: pip install anthropic")

    client_kwargs = {"auth_token": auth_token, "timeout": 600.0, "max_retries": 3}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = anthropic.Anthropic(**client_kwargs)

    system_blocks = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]

    store = load_store(out_path)
    t0 = time.time()
    total_new = 0
    for category, target in plan:
        total_new += generate_category(
            client, model, system_blocks, schema, store, out_path,
            category, axes, target, args.batch_size, args.max_tokens, args.effort, verbose)

    dt = time.time() - t0
    print("=" * 70)
    print(f"Готово. Новых патчей: {total_new}. Всего в файле: {len(store['entries'])}.")
    print(f"Время: {dt:.0f} c. Файл: {out_path}")
    print("Дальше: python ml/scripts/validate_patches.py --in", out_path)


if __name__ == "__main__":
    main()
