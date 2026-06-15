#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_reference.py — догенерация ЭТАЛОННЫХ патчей (реф-база v5, Шаг 2) через Claude API.

НЕЗАВИСИМЫЕ от детерминированного генератора эталоны (план §5: «нельзя калибровать против
своего же выхода»). Claude СВОБОДНО проектирует патч под конкретную цель (v3-стиль, реальные
единицы) — ровно тот пайплайн, что сделал заводские/[TEST]/[DIV]/[DS]. Затем человек слушает,
правит в синте и пересохраняет файл — утверждённый патч и есть эталон.

ФОКУС (выбор юзера): 8 безъякорных ролей из аудита Шага 2 —
  mallet, brass, pure_tone, square_lead, snare_clap, tom, cymbal, saw_bass.
По 1 патчу на цель, целей ~14 (широкие роли — по 2 цели для разброса регистра/яркости).

Переиспользует обвязку generate_dataset.py (промпт, прокси, конверсия real→norm).

Выход:
  • build/.../Release/Patches/«[REF] <role> — <target>».json — плоский norm, грузится синтом;
  • ml/data/reference/reference_anchors.json — стор с провенансом (concept/descriptions/real/norm,
    флаг approved=false; поднимаешь в true после утверждения).

Запуск:
  python ml/scripts/gen_reference.py --dry-run        # план + образец промпта, без API/трат
  python ml/scripts/gen_reference.py --limit 1        # смоук-тест пайплайна (1 вызов)
  python ml/scripts/gen_reference.py                  # весь фокус-набор
"""

import argparse
import io
import json
import re
import sys
import time
from pathlib import Path

import generate_dataset as gd   # обвязка v3: промпт/прокси/конверсия
import param_convert as pc

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]                 # .../ml
REPO = ROOT.parent
PATCHES_OUT = REPO / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"
REF_STORE = ROOT / "data" / "reference" / "reference_anchors.json"
PREFIX = "[REF] "
_ILLEGAL = re.compile(r'[<>:"\\/|?*]')


def safe_name(s):
    return " ".join(_ILLEGAL.sub("-", s).split()).strip(" .")


# Фокус-набор: (role, target, category_id). target строго как в sound_taxonomy.json.
REF_TARGETS = [
    ("mallet",      "вибрафон",                              "acoustic_emulation"),
    ("mallet",      "маримба/ксилофон",                      "acoustic_emulation"),
    ("brass",       "труба (открытая/сурдина)",              "acoustic_emulation"),
    ("brass",       "тромбон",                               "acoustic_emulation"),
    ("pure_tone",   "свист",                                 "acoustic_emulation"),
    ("pure_tone",   "терменвокс-подобный непрерывный тон",   "acoustic_emulation"),
    ("square_lead", "PWM/квадратный лид",                    "synth_roles"),
    ("square_lead", "чиптюн-лид",                            "synth_roles"),
    ("saw_bass",    "пилообразный синт-бас (аналоговый)",    "synth_roles"),
    ("tom",         "литавры (настроенный барабан)",         "acoustic_emulation"),
    ("tom",         "том (настроенный, питч-дроп)",          "drums"),
    ("snare_clap",  "снэр (нойз+тон)",                       "drums"),
    ("snare_clap",  "клэп",                                  "drums"),
    ("cymbal",      "крэш/райд (металл+нойз)",               "drums"),
    # ── батч 2: по 1 якорю на ранее непокрытые роли (доводим все 31 роли до ≥1 эталона) ──
    ("sub_bass",     "суббас (чистый син)",                  "synth_roles"),
    ("saw_lead",     "supersaw-лид",                         "synth_roles"),
    ("glass_pad",    "стеклянный/кристаллический пэд",        "synth_roles"),
    ("epiano",       "электропиано/родес",                   "acoustic_emulation"),
    ("pluck",        "плак (короткий, перкуссивный)",        "synth_roles"),
    ("flute",        "флейта (с придыханием)",               "acoustic_emulation"),
    ("drone",        "бесконечный дрон (низкий)",            "texture_atmos"),
    ("riser_fx",     "взлёт/ризер (медленный подъём)",       "percussive_fx"),
    ("kick",         "синт-кик (808, сабовый синус)",        "drums"),
    ("hihat",        "хай-хэт закрытый (короткий)",          "drums"),
    ("reed",         "кларнет (полый, нечётные обертоны)",   "acoustic_emulation"),
    ("noise_texture","ветер/шумовой бриз",                   "texture_atmos"),
    ("gong",         "храмовый гонг",                        "percussive_fx"),
    ("digital_fx",   "глитч/артефакт",                       "percussive_fx"),
]


CONFIG = ROOT / "config"
REF_SYS_TMPL = CONFIG / "system_prompt_reference.md"


def build_reference_system_prompt(param_ref, wt_doc):
    """Лин-промпт эталонов: param-таблица + банки + механика движка + few-shot, БЕЗ блока описаний."""
    t = REF_SYS_TMPL.read_text(encoding="utf-8")
    t = t.replace("{{PARAM_TABLE}}", gd.build_param_table(param_ref))
    t = t.replace("{{WAVETABLE_DOC}}", gd.build_wavetable_doc(wt_doc, param_ref))
    t = t.replace("{{BANK_NAMES}}", ", ".join(pc.BANK_NAMES))
    t = t.replace("{{LFO_SHAPES}}", ", ".join(pc.LFO_SHAPE_NAMES))
    t = t.replace("{{FEWSHOT}}", gd.build_fewshot())
    return t


def build_reference_user_message(category, role, target):
    """Запрос ОДНОГО каноничного эталона — только параметры (без 6 описаний)."""
    return (
        f"Спроектируй ОДИН эталонный патч звука «{target}» "
        f"(роль-архетип: {role}; категория: {category['name']} — {category['intent']}).\n"
        f"Это РЕФЕРЕНС для калибровки: сделай максимально узнаваемый, каноничный «{target}» — "
        f"чистое образцовое прочтение, без экзотики.\n"
        f"Сначала по докам банков выбери БАНК и ПОЗИЦИЮ wavetable так, чтобы они реально давали тембр "
        f"источника (помни: на Basic пилообразный/жужжащий тон — высокая позиция ~80–95%, а не у нуля). "
        f"Затем огибающая под тип звука, фильтр, модуляция.\n"
        f"Верни СТРОГО JSON: {{\"concept\": \"...\", \"osc2_active\": <bool>, "
        f"\"params\": {{все 38 параметров в реальных единицах}}}}. Без описаний, без текста вне JSON, "
        f"без вызова инструментов."
    )


def load_store():
    if REF_STORE.exists():
        return gd.load_json(REF_STORE)
    return {"version": "5.0-reference", "purpose": "Реф-якоря Шага 2 (Claude, свободный дизайн).",
            "entries": []}


def save_store(store):
    REF_STORE.parent.mkdir(parents=True, exist_ok=True)
    tmp = REF_STORE.with_suffix(".tmp")
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    tmp.replace(REF_STORE)


def done_targets(store):
    return {(e.get("role"), e.get("target")) for e in store["entries"]}


def main():
    ap = argparse.ArgumentParser(description="Догенерация эталонных патчей реф-базы (Claude API).")
    ap.add_argument("--limit", type=int, default=None, help="взять только первые N целей (смоук-тест)")
    ap.add_argument("--max-tokens", type=int, default=6000, help="1 патч без описаний (деф. 6000)")
    ap.add_argument("--model", default=None, help="переопределить модель")
    ap.add_argument("--dry-run", action="store_true", help="план + образец промпта, без API")
    ap.add_argument("--no-export", action="store_true", help="не писать пресеты в синт (только стор)")
    ap.add_argument("--regen", action="store_true", help="перегенерить даже уже сделанные цели")
    args = ap.parse_args()

    taxonomy = gd.load_json(gd.TAXONOMY)
    param_ref = gd.load_json(gd.PARAM_REF)
    wt_doc = gd.load_json(gd.WT_DOC)
    axes = taxonomy["diversity_axes"]
    cats = {c["id"]: c for c in taxonomy["categories"]}

    plan = REF_TARGETS[: args.limit] if args.limit else REF_TARGETS

    system_prompt = build_reference_system_prompt(param_ref, wt_doc)
    print("=" * 70)
    print(f"Реф-генерация: {len(plan)} целей (8 безъякорных ролей). Модель: "
          f"{args.model or gd.load_api_config()[2]}")
    print(f"System-промпт: ~{len(system_prompt)} симв. (≈{len(system_prompt)//4} ток.)")
    for role, target, cat in plan:
        print(f"  {role:<12} | {cat:<20} | {target}")
    print("=" * 70)

    if args.dry_run:
        c0 = cats[plan[0][2]]
        print("\n──── ОБРАЗЕЦ USER-СООБЩЕНИЯ ────\n")
        print(build_reference_user_message(c0, plan[0][0], plan[0][1]))
        return

    base_url, auth_token, cfg_model = gd.load_api_config()
    if not auth_token:
        sys.exit("Нет API-ключа (ANTHROPIC_AUTH_TOKEN или ml/config/api_config.local.json).")
    model = args.model or cfg_model
    try:
        import anthropic
    except ImportError:
        sys.exit("Нет пакета 'anthropic' (pip install anthropic).")
    client_kwargs = {"auth_token": auth_token, "timeout": 600.0, "max_retries": 3}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = anthropic.Anthropic(**client_kwargs)
    system_blocks = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]

    store = load_store()
    have = done_targets(store)
    t0 = time.time()
    made, in_tok, out_tok = 0, 0, 0

    for role, target, cat_id in plan:
        if not args.regen and (role, target) in have:
            print(f"  ∙ уже есть [{role}] «{target}» — пропуск")
            continue
        category = cats[cat_id]
        user_text = build_reference_user_message(category, role, target)
        try:
            data, usage = gd.call_model(client, model, system_blocks, user_text,
                                        args.max_tokens, "medium", verbose=True)
        except Exception as e:
            print(f"  ✗ [{role}] «{target}»: {e}")
            continue

        # новый формат — один патч {concept, osc2_active, params}; терпим и к v3-обёртке {patches:[...]}
        if isinstance(data.get("params"), dict):
            p = data
        elif data.get("patches"):
            p = data["patches"][0]
        else:
            print(f"  ✗ [{role}] «{target}»: нет params в ответе")
            continue
        raw = p.get("params")
        if not isinstance(raw, dict):
            print(f"  ✗ [{role}] «{target}»: нет params")
            continue
        try:
            real_clean, norm, present = gd.convert_patch_params(raw)
        except Exception as e:
            print(f"  ✗ [{role}] «{target}»: конверсия — {e}")
            continue
        if present < 30:
            print(f"  ⚠ [{role}] «{target}»: лишь {present}/38 параметров — пропуск")
            continue

        fname = f"{PREFIX}{role} — {safe_name(target)}"
        if not args.no_export:
            with io.open(PATCHES_OUT / f"{fname}.json", "w", encoding="utf-8") as f:
                json.dump(norm, f, ensure_ascii=False)

        store["entries"].append({
            "id": f"ref_{role}_{len([e for e in store['entries'] if e.get('role')==role])+1:02d}",
            "role": role, "target": target, "category": cat_id,
            "concept": p.get("concept", target), "source": model,
            "osc2_active": bool(p.get("osc2_active", False)),
            "preset_file": f"{fname}.json", "approved": False,
            "params": norm, "params_real": real_clean,
            "descriptions": p.get("descriptions", []),
        })
        save_store(store)   # чекпойнт после каждой цели
        made += 1
        u = ""
        if usage:
            it = getattr(usage, "input_tokens", 0) or 0
            ot = getattr(usage, "output_tokens", 0) or 0
            in_tok += it
            out_tok += ot
            u = f" (in={it}, out={ot})"
        print(f"  ✓ [{role}] «{target}» → {fname}.json  «{p.get('concept','')}»{u}")

    dt = time.time() - t0
    print("=" * 70)
    print(f"Готово. Новых эталонов: {made}. Всего в сторе: {len(store['entries'])}.")
    print(f"Токены сессии: in={in_tok}, out={out_tok}. Время: {dt:.0f} c. Стор: {REF_STORE.relative_to(REPO)}")
    if made:
        print(f"Дальше: слушай «{PREFIX}…» в синте, правь, пересохраняй; ставь approved=true в сторе.")


if __name__ == "__main__":
    main()
