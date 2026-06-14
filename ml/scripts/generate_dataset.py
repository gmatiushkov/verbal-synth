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

import param_convert as pc  # конвертер реальные↔[0,1] (зеркало C++)

# ── Пути ──────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parents[1]          # .../ml
CONFIG    = ROOT / "config"
DATA      = ROOT / "data"
PARAM_REF = CONFIG / "param_reference.json"
TAXONOMY  = CONFIG / "sound_taxonomy.json"
SYS_TMPL  = CONFIG / "system_prompt.md"
WT_DOC    = CONFIG / "wavetable_doc.json"
API_CFG   = CONFIG / "api_config.local.json"

# Заводские пресеты для few-shot (реальные звучащие патчи) — берутся из сборки.
PRESET_DIRS = [
    ROOT.parent / "build" / "VerbalSynth_artefacts" / "Release" / "Patches",
    ROOT.parent / "build" / "VerbalSynth_artefacts" / "Debug" / "Patches",
]
# Эталонные заводские пресеты для few-shot. На тарифе с кэшем системный промпт
# (включая эти примеры) кэшируется и читается ~0.1× на последующих запросах —
# поэтому держим полный набор разнотипных рабочих звуков как обучающие образцы.
FEWSHOT_PRESETS = [
    "Piano", "Guitar", "Violin", "Cello", "Church Organ", "Rock Leslie Organ",
    "Overdrive Short Guitar", "Reese Bass", "Dirty Acid 303 Bass",
    "Slow Ambient Pad", "Voices Singing Yao", "Thin Bell",
]

DEFAULT_MODEL = "claude-opus-4-8"


# ── Утилиты загрузки ──────────────────────────────────────────────────────────
def load_json(path: Path):
    # utf-8-sig: терпим к BOM (его добавляет, напр., PowerShell Out-File -Encoding utf8)
    with open(path, encoding="utf-8-sig") as f:
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


# ── Сборка system-промпта (реальные единицы) ──────────────────────────────────
def _range_str(p) -> str:
    """Человекочитаемый диапазон параметра для таблицы промпта."""
    kind = p["kind"]
    if kind in ("log", "linpct", "morphpct"):
        u = p.get("unit", "")
        return f"{p['real_min']}…{p['real_max']} {u}".strip()
    if kind == "q":
        return f"{p['real_min']}…{p['real_max']} Q"
    if kind == "detune":
        return f"{p['real_min']}…{p['real_max']} центов"
    if kind == "semis":
        return f"{p['real_min']}…{p['real_max']} полутонов (целые)"
    if kind == "octave":
        return "−2…+2 октавы (целые)"
    if kind == "fenvamt":
        return f"{p['real_min']}…{p['real_max']} октав (0=нейтрально)"
    if kind == "modsemi":
        return f"{p['real_min']}…{p['real_max']} центов"
    if kind == "modoct":
        return f"{p['real_min']}…{p['real_max']} октав"
    if kind == "bank":
        return "имя банка"
    if kind == "lfoshape":
        return "имя формы"
    return ""


def build_param_table(param_ref) -> str:
    lines = []
    for p in param_ref["params"]:
        rng = _range_str(p)
        rng = f" [{rng}]" if rng else ""
        lines.append(f"[{p['i']:>2}] {p['name']}{rng}: {p['desc']}")
    return "\n".join(lines)


def build_wavetable_doc(wt_doc, param_ref) -> str:
    """name + perceptual_summary + position_map для каждого банка."""
    blocks = []
    for bank in wt_doc["banks"]:
        name = bank["name"]
        ps = bank.get("perceptual_summary", "").strip()
        pm = bank.get("position_map", {})
        pm_lines = "; ".join(f"{k} — {v}" for k, v in pm.items())
        blocks.append(f"### {name}\n{ps}\nПозиция (морф 0–100%): {pm_lines}")
    return "\n\n".join(blocks)


def _load_preset(name):
    for d in PRESET_DIRS:
        f = d / f"{name}.json"
        if f.exists():
            return load_json(f)
    return None


def _fewshot_value(pname, real):
    """Аккуратно округлённое реальное значение для few-shot (в единицах, что просим у Claude)."""
    if isinstance(real, str):
        return real
    unit = pc.unit_of(pname)
    kind = pc.PARAM_SPEC[pname][0]
    if kind in ("octave", "semis"):
        return f"{int(round(real))}"
    if unit == "s":                       # времена в секундах, 3 значимых
        if real < 0.01:
            return f"{real:.4f}"
        if real < 1:
            return f"{real:.3f}"
        return f"{real:.2f}"
    if unit == "Hz":
        return f"{real:.2f}" if real < 100 else f"{real:.0f}"
    if unit == "Q":
        return f"{real:.1f}"
    # проценты, центы, октавы-модуляции → целое
    return f"{round(real)}"


def build_fewshot() -> str:
    """Реальные заводские патчи → блок few-shot в реальных единицах (аккуратно округлённый)."""
    blocks = []
    for name in FEWSHOT_PRESETS:
        norm = _load_preset(name)
        if not norm:
            continue
        lines = [f"### {name}"]
        for pname in pc.PARAM_ORDER:
            if pname not in norm:
                continue
            real = pc.norm_to_real(pname, norm[pname])
            val = _fewshot_value(pname, real)
            unit = "" if isinstance(real, str) else f" {pc.unit_of(pname)}"
            lines.append(f"  {pname}: {val}{unit}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) if blocks else "(эталоны недоступны)"


def build_system_prompt(param_ref, wt_doc) -> str:
    tmpl = SYS_TMPL.read_text(encoding="utf-8")
    tmpl = tmpl.replace("{{PARAM_TABLE}}", build_param_table(param_ref))
    tmpl = tmpl.replace("{{WAVETABLE_DOC}}", build_wavetable_doc(wt_doc, param_ref))
    tmpl = tmpl.replace("{{BANK_NAMES}}", ", ".join(pc.BANK_NAMES))
    tmpl = tmpl.replace("{{LFO_SHAPES}}", ", ".join(pc.LFO_SHAPE_NAMES))
    tmpl = tmpl.replace("{{FEWSHOT}}", build_fewshot())
    return tmpl


STYLES = ["functional", "instrument", "psychoacoustic", "emotional", "metaphor", "telegraphic"]


# ── User-сообщение на батч ────────────────────────────────────────────────────
def build_user_message(category, target, n, axes, made_so_far=0) -> str:
    """Батч посвящён ОДНОЙ цели: просим N её РАЗНЫХ прочтений. Так мандат «не-близнецы»
    обеспечивает разнообразие именно между повторами одной цели (главная дыра прежней схемы)."""
    axes_txt = "\n".join(f"  · {a}" for a in axes)
    tail = (
        f"Для каждого варианта — все 38 параметров в РЕАЛЬНЫХ единицах (банки и формы LFO — строками; "
        f"октавы/полутоны — целыми; времена в секундах) и 6 описаний ({', '.join(STYLES)}). "
        f"Верни СТРОГО JSON по формату из system-промпта, без текста вне JSON. "
        f"Не вызывай инструменты/функции — ответ только текст с JSON."
    )
    head = (
        f"Категория: **{category['name']}** (id: {category['id']}).\n"
        f"Замысел категории: {category['intent']}\n\n"
        f"Цель этого запроса — звук **«{target}»**.\n"
    )
    if n == 1:
        return head + (
            f"Спроектируй 1 патч этого звука — с выраженным характером, узнаваемо «{target}».\n\n"
        ) + tail
    cont = ""
    if made_so_far > 0:
        cont = (f" Для этой цели уже сделано {made_so_far} вариантов — уйди в ДРУГИЕ области осей, "
                f"не повторяй типовые/очевидные решения.")
    return head + (
        f"Спроектируй {n} ЗАМЕТНО РАЗНЫХ вариантов ИМЕННО этого звука: это разные прочтения одной "
        f"и той же цели (один инструмент/роль), а НЕ разные инструменты — каждый узнаваемо «{target}», "
        f"но звучит по-своему.{cont}\n\n"
        f"Разводи варианты по осям разнообразия (для каждого — своя комбинация):\n{axes_txt}\n\n"
        f"Требования: никаких близнецов — варианты различаются ≥3 осей; часть моно-OSC, часть слойные "
        f"(OSC2); где уместно — разные банки/регистры/артикуляции. "
    ) + tail


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


def _one_call(client, kwargs, anthropic, verbose):
    """Один запрос (стрим → create fallback). Возвращает (data, usage). Бросает при пустом/битом."""
    # Прокси инжектит агентные инструменты, и при stop_reason=tool_use ответ не содержит текста
    # (модель «уходит» в фиктивный вызов WebFetch). Стрим в этом случае отдаёт пустой SSE.
    # Нестриминговый create стабильнее; стрим оставляем запасным. Запрет инструментов — в промпте.
    try:
        msg = client.messages.create(**kwargs)
    except (anthropic.APIError, TypeError) as create_err:
        if verbose:
            print(f"    [create→stream fallback: {type(create_err).__name__}]")
        with client.messages.stream(**kwargs) as stream:
            msg = stream.get_final_message()
    text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
    if not text.strip():
        raise ValueError(f"пустой текстовый ответ (stop={getattr(msg, 'stop_reason', None)})")
    return extract_json(text), getattr(msg, "usage", None)


def call_model(client, model, system_blocks, user_text, max_tokens, effort, verbose,
               max_retries=4):
    """
    JSON через требование в промпте + extract_json (structured outputs у прокси нестабилен).
    Прокси периодически отдаёт ПУСТОЙ ответ — это транзиентно, поэтому батч повторяется
    с экспоненциальной паузой. Возвращает (dict, usage|None).
    """
    import anthropic

    base = dict(model=model, max_tokens=max_tokens, system=system_blocks,
                messages=[{"role": "user", "content": user_text}])
    # Стоимость провала = главный рычаг бюджета. adaptive thinking даёт лучшее проектирование,
    # но НА ПЕРВОМ заходе: при пустом/битом ответе прокси повтор идёт БЕЗ thinking (дёшево) —
    # чтобы провал не стоил как полноценная генерация (раньше thinking жгли на каждом повторе).
    THINK = dict(thinking={"type": "adaptive"})
    CHEAP = dict()  # без thinking — запасной/повторный вариант, стоит копейки

    def attempts_for(round_idx):
        # Первый заход: thinking, затем дешёвый запасной (если thinking отвергнут).
        # Все последующие повторы (после транзиентного провала прокси): только дёшево.
        return [THINK, CHEAP] if round_idx == 0 else [CHEAP]

    last_err = None
    for r in range(max_retries):
        for i, extra in enumerate(attempts_for(r)):
            try:
                data, usage = _one_call(client, {**base, **extra}, anthropic, verbose)
                if (r > 0 or i > 0) and verbose:
                    print("    [использован дешёвый вариант запроса (без thinking)]")
                return data, usage
            except (anthropic.BadRequestError, anthropic.NotFoundError, TypeError) as e:
                last_err = e
                if verbose:
                    print(f"    [вариант отклонён: {type(e).__name__}: {e}; пробую проще]")
                continue
            except (json.JSONDecodeError, ValueError, anthropic.APIError) as e:
                last_err = e
                if verbose:
                    print(f"    [попытка {r+1}/{max_retries}: {type(e).__name__}: {e}]")
                continue
        if r < max_retries - 1:
            delay = 2 ** r  # 1,2,4 c
            if verbose:
                print(f"    [пустой/битый ответ прокси — дешёвый повтор батча через {delay}c]")
            time.sleep(delay)
    raise RuntimeError(f"Все попытки не удались. Последняя ошибка: {last_err}")


# ── Хранилище патчей (чекпойнт) ───────────────────────────────────────────────
def load_store(out_path: Path):
    if out_path.exists():
        return load_json(out_path)
    return {"version": "3.0", "entries": []}


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


def convert_patch_params(real_params):
    """Реальные параметры от Claude → (params_real_clean, params_norm).
       Неизвестные ключи игнорируются; недостающие заполнит param_convert дефолтом."""
    # Берём только известные параметры; конверсия real→norm зеркалит C++.
    norm = pc.patch_real_to_norm(real_params)               # {name: [0..1]}, все 38
    # обратно в реальные из norm — даёт «очищенные» реальные (после кламп/снап) для ревью
    real_clean = pc.patch_norm_to_real(norm)
    # сколько ключей Claude реально прислал из 38
    present = sum(1 for k in pc.PARAM_ORDER if k in real_params and real_params[k] is not None)
    return real_clean, norm, present


def distribute(count, k):
    """count экземпляров РАВНОМЕРНО на k целей; первые (count % k) целей получают +1."""
    if k <= 0:
        return []
    base, rem = divmod(count, k)
    return [base + (1 if i < rem else 0) for i in range(k)]


# ── Основной цикл генерации одной категории ───────────────────────────────────
def generate_category(client, model, system_blocks, store, out_path,
                      category, axes, target_count, batch_size, max_tokens, effort, verbose,
                      target_limit=None):
    """Набирает target_count патчей категории. Объём РАВНОМЕРНО распределяется по целям,
    и КАЖДЫЙ батч = N разных вариантов ОДНОЙ цели (внутрибатчевый мандат «не-близнецы»
    обеспечивает разнообразие между повторами одной цели). target_limit — взять только
    первые K целей (тест-режим)."""
    cat_id = category["id"]
    targets = category["targets"]
    if target_limit:
        targets = targets[:target_limit]
    alloc = distribute(target_count, len(targets))   # желаемое число патчей на каждую цель

    have_per = {}                                    # уже сделано по каждой цели (для резюме)
    for e in store["entries"]:
        if e.get("category") == cat_id:
            have_per[e.get("target")] = have_per.get(e.get("target"), 0) + 1

    total_need = sum(max(0, alloc[i] - have_per.get(targets[i], 0)) for i in range(len(targets)))
    have_total = count_by_category(store, cat_id)
    if total_need == 0:
        print(f"  [{cat_id}] уже есть {have_total}/{target_count} — пропуск")
        return 0
    print(f"  [{cat_id}] есть {have_total}, нужно ещё {total_need} "
          f"(цель {target_count}, целей {len(targets)})")

    produced = 0
    for i, target in enumerate(targets):
        want = alloc[i]
        got = have_per.get(target, 0)
        while got < want:
            n = min(batch_size, want - got)
            user_text = build_user_message(category, target, n, axes, made_so_far=got)
            try:
                data, usage = call_model(client, model, system_blocks, user_text,
                                         max_tokens, effort, verbose)
            except Exception as e:
                print(f"    ОШИБКА батча [{target}]: {e}\n    Пропускаю цель (прогресс сохранён).")
                break

            patches = data.get("patches", [])
            if not patches:
                print(f"    Пустой батч [{target}] — пропуск цели.")
                break

            added = 0
            idx = next_index(store, cat_id)
            for p in patches:
                raw = p.get("params")
                if not isinstance(raw, dict):
                    print(f"    ⚠ патч без объекта params — пропуск ({p.get('concept')})")
                    continue
                try:
                    real_clean, norm, present = convert_patch_params(raw)
                except Exception as e:
                    print(f"    ⚠ конверсия не удалась ({p.get('concept')}): {e} — пропуск")
                    continue
                if present < 30:  # слишком мало реальных параметров — подозрительно
                    print(f"    ⚠ патч прислал лишь {present}/38 параметров — пропуск ({p.get('concept')})")
                    continue
                entry = {
                    "id": f"{cat_id}_{idx:03d}",
                    "concept": p.get("concept", f"{cat_id}_{idx}"),
                    "category": cat_id,
                    "target": target,               # исходная цель — для резюме и анализа разнообразия
                    "source": model,
                    "osc2_active": bool(p.get("osc2_active", False)),
                    "params": norm,                 # нормализованные [0..1] — для синта/обучения
                    "params_real": real_clean,       # реальные единицы — для ревью глазами
                    "descriptions": p.get("descriptions", []),
                }
                store["entries"].append(entry)
                idx += 1
                added += 1
                got += 1
                produced += 1

            save_store(out_path, store)  # чекпойнт после каждого батча
            u = ""
            if usage:
                # cache_read/creation покажут, работает ли кэширование системного промпта у прокси
                cr = getattr(usage, "cache_read_input_tokens", None)
                cc = getattr(usage, "cache_creation_input_tokens", None)
                cache = ""
                if cr is not None or cc is not None:
                    cache = f", cache_read={cr or 0}, cache_write={cc or 0}"
                u = (f" (in={getattr(usage,'input_tokens','?')}, "
                     f"out={getattr(usage,'output_tokens','?')}{cache})")
            print(f"    [{target}] +{added} → {got}/{want}{u}")
            if added == 0:  # батч не дал валидных патчей — не зацикливаемся
                print(f"    ⚠ батч [{target}] без валидных патчей — пропуск цели.")
                break

    return produced


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Генерация датасета патчей VerbalSynth (v3, реальные единицы).")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--test", action="store_true", help="по N патчей на каждую категорию (см. --count)")
    mode.add_argument("--all", action="store_true", help="полный датасет по долям share")
    mode.add_argument("--category", help="ID одной категории из taxonomy")
    ap.add_argument("--count", type=int, default=None,
                    help="--test: патчей/категория по первым 2 целям (деф. 6); --category: всего патчей; --all: общий объём (деф. 800)")
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
        per = args.count or 6
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
        print(build_user_message(c0, c0["targets"][0], min(args.batch_size, 6), axes))
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
    grand_total = sum(n for _, n in plan)
    for category, target in plan:
        total_new += generate_category(
            client, model, system_blocks, store, out_path,
            category, axes, target, args.batch_size, args.max_tokens, args.effort, verbose,
            target_limit=(2 if args.test else None))
        done = len(store["entries"])
        el = (time.time() - t0) / 60.0
        pct = 100 * done // max(1, grand_total)
        print(f"  ══► ПРОГРЕСС: {done}/{grand_total} патчей ({pct}%) · прошло {el:.0f} мин · "
              f"новых за сессию {total_new} ══")

    dt = time.time() - t0
    print("=" * 70)
    print(f"Готово. Новых патчей: {total_new}. Всего в файле: {len(store['entries'])}.")
    print(f"Время: {dt:.0f} c. Файл: {out_path}")
    print("Дальше: python ml/scripts/validate_patches.py --in", out_path)


if __name__ == "__main__":
    main()
