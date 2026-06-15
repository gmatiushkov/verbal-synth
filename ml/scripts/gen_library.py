#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_library.py — СТРИМИНГ-генерация патчей-кандидатов для ПРОБЕЛОВ библиотеки (PIVOT_RETRIEVAL.md §7).

Claude свободно проектирует патч под цель (params, реальные единицы) — переиспользует промпт и
обвязку gen_reference/generate_dataset. КАЖДЫЙ патч сразу:
  • пишется нумерованным пресетом в Patches → появляется в синте, юзер тюнит НЕ дожидаясь остальных;
  • заносится в library.json (params/attributes, source=gen, approved=false) — чекпойнт после каждого.
Резюмируемо: уже сгенерённые (params!=null) пропускаются. Прерывать/стопать можно в любой момент.

Запуск:  python ml/scripts/gen_library.py --limit 12     # первая волна
         python ml/scripts/gen_library.py                 # все оставшиеся пробелы
         python ml/scripts/gen_library.py --dry-run        # план/стоимость без API
"""

import argparse
import io
import json
import sys
import time
from pathlib import Path

import attr_decode as ad
import generate_dataset as gd
import gen_reference as gr

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
LIB = ROOT / "data" / "library" / "library.json"
PATCHES = REPO / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"


def load_lib():
    return json.loads(io.open(LIB, encoding="utf-8-sig").read())


def save_lib(lib):
    tmp = LIB.with_suffix(".tmp")
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(lib, f, ensure_ascii=False, indent=2)
    tmp.replace(LIB)


def main():
    ap = argparse.ArgumentParser(description="Стриминг-генерация пробелов библиотеки (Claude).")
    ap.add_argument("--limit", type=int, default=None, help="взять только первые N пробелов")
    ap.add_argument("--max-tokens", type=int, default=6000)
    ap.add_argument("--model", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lib = load_lib()
    gaps = [e for e in lib["entries"] if e.get("source") == "gen" and e.get("params") is None]
    plan = gaps[: args.limit] if args.limit else gaps

    taxonomy = gd.load_json(gd.TAXONOMY)
    param_ref = gd.load_json(gd.PARAM_REF)
    wt_doc = gd.load_json(gd.WT_DOC)
    cats = {c["id"]: c for c in taxonomy["categories"]}
    system_prompt = gr.build_reference_system_prompt(param_ref, wt_doc)

    print("=" * 72)
    print(f"Генерация кандидатов: пробелов всего {len(gaps)}, в этой волне {len(plan)}. "
          f"Модель: {args.model or gd.load_api_config()[2]}")
    print(f"Оценка: ~$0.5/патч, ~1 мин/патч (ориентир) → волна ≈ ${0.5*len(plan):.0f}, ~{len(plan)} мин")
    print("=" * 72)
    if args.dry_run:
        for e in plan[:8]:
            print(f"  {e['name']:<42} роль={e['role']}")
        print(f"  ... ({len(plan)} целей). Пример запроса:\n")
        e0 = plan[0]
        print(gr.build_reference_user_message(cats[e0["category"]], e0["role"], e0["target"])[:500])
        return

    base_url, auth_token, cfg_model = gd.load_api_config()
    if not auth_token:
        sys.exit("Нет API-ключа (ml/config/api_config.local.json).")
    model = args.model or cfg_model
    import anthropic
    ckw = {"auth_token": auth_token, "timeout": 600.0, "max_retries": 3}
    if base_url:
        ckw["base_url"] = base_url
    client = anthropic.Anthropic(**ckw)
    sysblocks = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]

    by_num = {e["num"]: e for e in lib["entries"]}
    t0, made, in_tok, out_tok = time.time(), 0, 0, 0
    for e in plan:
        cat = cats[e["category"]]
        user = gr.build_reference_user_message(cat, e["role"], e["target"])
        try:
            data, usage = gd.call_model(client, model, sysblocks, user, args.max_tokens, "medium", verbose=True)
        except Exception as ex:
            print(f"  ✗ {e['name']}: {ex}")
            continue
        p = data if isinstance(data.get("params"), dict) else (data["patches"][0] if data.get("patches") else None)
        if not p or not isinstance(p.get("params"), dict):
            print(f"  ✗ {e['name']}: нет params")
            continue
        try:
            _real, norm, present = gd.convert_patch_params(p["params"])
        except Exception as ex:
            print(f"  ✗ {e['name']}: конверсия {ex}")
            continue
        if present < 30:
            print(f"  ⚠ {e['name']}: лишь {present}/38 — пропуск")
            continue
        with io.open(PATCHES / e["preset_file"], "w", encoding="utf-8") as f:
            json.dump(norm, f, ensure_ascii=False)
        ent = by_num[e["num"]]
        ent["params"] = norm
        ent["attributes"] = ad.decode_all(norm)
        ent["concept"] = p.get("concept", "")
        ent["approved"] = False
        save_lib(lib)                                       # чекпойнт + импорт в синт сразу
        made += 1
        if usage:
            in_tok += getattr(usage, "input_tokens", 0) or 0
            out_tok += getattr(usage, "output_tokens", 0) or 0
        print(f"  ✓ {e['name']}  «{p.get('concept','')}»  ({made}/{len(plan)})")

    dt = time.time() - t0
    print("=" * 72)
    print(f"Готово волны: +{made}. Покрыто библиотеки: "
          f"{sum(1 for e in lib['entries'] if e.get('params'))}/{len(lib['entries'])}. "
          f"Токены in={in_tok}, out={out_tok}. Время {dt:.0f}c.")
    print("Тюнингуй нумерованные пресеты в синте; потом sync_library.py подтянет правки. "
          "Остаток догенерить: повторный запуск (сделанные пропустятся).")


if __name__ == "__main__":
    main()
