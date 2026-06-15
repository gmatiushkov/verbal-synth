#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_queries.py — синонимы-ФОРМУЛИРОВКИ на каждый прототип для retrieval-индекса (PIVOT §4).

Генерим НЕ патчи, а 20–40 РАЗНЫХ пользовательских запросов на прототип: синонимы, сленг,
англицизмы, жанровые/эмоциональные/бытовые описания («acid bass» → кислотный бас / tb303 /
резонансный бас / рейв-бас / писклявый бас с вахвахом …). Основа — СЕМАНТИКА из library.json
(target/role/descriptors/attributes), НЕ 38 чисел. Эти фразы добавляются к target+descriptors
(retrieval.py подмешивает их max-pool'ом) и закрывают разговорные запросы, которых нет в descriptors.

Модель — Sonnet (дёшево, текст). Стриминг+чекпойнт после каждого прототипа, резюмируемо
(уже сделанные num пропускаются). Прерывать можно в любой момент.

    python ml/scripts/gen_queries.py --limit 3 --dry-run   # план/стоимость, без API
    python ml/scripts/gen_queries.py --limit 5             # первая волна (проверить качество)
    python ml/scripts/gen_queries.py                       # все оставшиеся
    python ml/scripts/gen_queries.py --regen 33,34         # перегенерить конкретные num
"""

import argparse
import io
import json
import sys
import time
from pathlib import Path

import generate_dataset as gd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "data" / "library" / "library.json"
OUT = ROOT / "data" / "library" / "queries.json"
DEFAULT_MODEL = "claude-sonnet-4-6"
N_TARGET = 30                                          # ориентир числа формулировок на прототип

SYSTEM = (
    "Ты — продукт-аналитик музыкального софта. Тебе дают ОПИСАНИЕ пресета синтезатора "
    "(тип звука, роль, тембральные атрибуты). Твоя задача — выдать список РАЗНЫХ коротких "
    "поисковых запросов на РУССКОМ, какими реальный пользователь искал бы ИМЕННО этот звук "
    "в строке Generate.\n"
    "Что включать: синонимы и народные названия; англицизмы и сленг (acid, reese, pluck, lead); "
    "жанровые ассоциации (транс, фанк, дабстеп, лоу-фай); эмоциональные/метафорические описания; "
    "запросы с модификаторами (тёплый/яркий/низкий/короткий) И без них; короткие (1–2 слова) "
    "и фразы. Разнообразь формулировки, избегай near-дубликатов.\n"
    "Чего НЕ делать: не выдумывай ДРУГОЙ инструмент/звук; не пиши параметры синтеза и числа; "
    "не повторяй дословно данные descriptors (они уже учтены); без эмодзи и пояснений.\n"
    f"Верни СТРОГО JSON-объект: {{\"queries\": [\"...\", ...]}} — около {N_TARGET} строк, без иного текста."
)


def load_json(p):
    return json.loads(io.open(p, encoding="utf-8-sig").read())


def save_out(data):
    tmp = OUT.with_suffix(".tmp")
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(OUT)


def user_msg(e):
    a = e.get("attributes") or {}
    attr = ", ".join(f"{k}={v}" for k, v in a.items() if v)
    return (
        f"Тип звука (target): {e.get('target','')}\n"
        f"Роль: {e.get('role','')} | банк: {e.get('bank','')}\n"
        f"Тембральные атрибуты: {attr or '—'}\n"
        f"Известные descriptors (НЕ дублировать дословно): {', '.join(e.get('descriptors', [])) or '—'}\n\n"
        f"Выдай ~{N_TARGET} разных пользовательских запросов, которыми искали бы этот звук."
    )


def main():
    ap = argparse.ArgumentParser(description="Генерация синонимов-запросов на прототип (Sonnet).")
    ap.add_argument("--limit", type=int, default=None, help="взять только первые N невыполненных")
    ap.add_argument("--regen", default="", help="перегенерить эти num (через запятую), даже если есть")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-tokens", type=int, default=1500)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lib = load_json(LIB)
    done = load_json(OUT) if OUT.exists() else {"version": "1.0", "model": args.model, "entries": {}}
    regen = {int(x) for x in args.regen.replace(" ", "").split(",") if x}

    todo = [e for e in lib["entries"]
            if str(e["num"]) not in done["entries"] or e["num"] in regen]
    plan = todo[: args.limit] if args.limit else todo

    print("=" * 72)
    print(f"Запросы-синонимы: всего прототипов {len(lib['entries'])}, "
          f"уже есть {len(done['entries'])}, в этой волне {len(plan)}. Модель: {args.model}")
    print(f"Оценка: ~{N_TARGET} строк/прототип, ~$0.01–0.03/прототип → волна ≈ ${0.02*len(plan):.1f}")
    print("=" * 72)
    if args.dry_run:
        for e in plan[:6]:
            print(f"  #{e['num']:>3} {e['target']}")
        print(f"  ... ({len(plan)} прототипов)\n--- пример user-сообщения ---")
        if plan:
            print(user_msg(plan[0]))
        return

    base_url, token, _ = gd.load_api_config()
    if not token:
        sys.exit("Нет API-ключа (ml/config/api_config.local.json).")
    import anthropic
    ckw = {"auth_token": token, "timeout": 300.0, "max_retries": 3}
    if base_url:
        ckw["base_url"] = base_url
    client = anthropic.Anthropic(**ckw)
    sysblocks = [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}]

    t0, made, in_tok, out_tok = time.time(), 0, 0, 0
    for e in plan:
        try:
            data, usage = gd.call_model(client, args.model, sysblocks, user_msg(e),
                                        args.max_tokens, "low", verbose=True)
        except Exception as ex:
            print(f"  ✗ #{e['num']} {e['target']}: {ex}")
            continue
        qs = data.get("queries") if isinstance(data, dict) else None
        if not isinstance(qs, list) or not qs:
            print(f"  ✗ #{e['num']} {e['target']}: нет queries")
            continue
        # чистим: строки, без дублей, без пустых
        seen, clean = set(), []
        for q in qs:
            q = (str(q) or "").strip()
            k = q.lower()
            if q and k not in seen:
                seen.add(k)
                clean.append(q)
        done["entries"][str(e["num"])] = clean
        save_out(done)                                  # чекпойнт после каждого
        made += 1
        if usage:
            in_tok += getattr(usage, "input_tokens", 0) or 0
            out_tok += getattr(usage, "output_tokens", 0) or 0
        print(f"  ✓ #{e['num']:>3} {e['target']}  ({len(clean)} запросов)  [{made}/{len(plan)}]")

    dt = time.time() - t0
    print("=" * 72)
    print(f"Готово волны: +{made}. Покрыто синонимами: {len(done['entries'])}/{len(lib['entries'])}. "
          f"Токены in={in_tok}, out={out_tok}. Время {dt:.0f}c.")
    print("Пересобери индекс/прогон: python ml/scripts/eval_retrieval.py")


if __name__ == "__main__":
    main()
