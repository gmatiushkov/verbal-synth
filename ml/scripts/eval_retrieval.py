#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_retrieval.py — IDENTITY-эвал retrieval-MVP (PIVOT_RETRIEVAL.md §5).

Северная звезда пивота: правильно ли выбран ПРОТОТИП по запросу. Метрика — top-1/top-3,
НЕ MSE параметров. Гоняет Retriever на golden_retrieval.json (запрос→ожидаемый прототип).

Две строгости (см. build_golden_retrieval.py):
  • strict — retrieved #1 == primary (точный прототип; primary — черновик, проверить руками).
  • role   — retrieved #1/#3 ∈ expected (верная семья роли).

Дешёвый A/B энкодера без обучения:  --encoder intfloat/multilingual-e5-base

    python ml/scripts/eval_retrieval.py
    python ml/scripts/eval_retrieval.py --encoder intfloat/multilingual-e5-base --show-misses
"""

import argparse
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from retrieval import Retriever, DEFAULT_ENCODER

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

GOLDEN = Path(__file__).resolve().parents[1] / "eval" / "golden_retrieval.json"


def main():
    ap = argparse.ArgumentParser(description="Identity-эвал retrieval на golden.")
    ap.add_argument("--encoder", default=DEFAULT_ENCODER)
    ap.add_argument("--approved-only", action="store_true")
    ap.add_argument("--syn-weight", type=float, default=None,
                    help="вес синонимов (0=выкл; по умолчанию DEFAULT_SYN_WEIGHT)")
    ap.add_argument("--golden", default=str(GOLDEN))
    ap.add_argument("--show-misses", action="store_true", help="показать промахи (role top-1)")
    args = ap.parse_args()

    gold = json.loads(io.open(args.golden, encoding="utf-8-sig").read())["prompts"]
    scored = [p for p in gold if p.get("expected")]       # без модификатор-онли (expected=[])
    skipped = len(gold) - len(scored)

    rkw = {"encoder_name": args.encoder, "approved_only": args.approved_only}
    if args.syn_weight is not None:
        rkw["syn_weight"] = args.syn_weight
    r = Retriever(**rkw)
    cand = {e["num"] for e in r.entries}                  # что реально доступно (есть params)

    strict1 = role1 = role3 = 0
    misses = []
    for p in scored:
        hits = r.search(p["text"], k=3)
        nums = [h["num"] for h in hits]
        exp = set(p["expected"]) & cand                   # ожидаемые, реально присутствующие
        s1 = bool(nums) and nums[0] == p["primary"]
        r1 = bool(nums) and nums[0] in exp
        r3 = any(n in exp for n in nums[:3])
        strict1 += s1
        role1 += r1
        role3 += r3
        if not r1:
            misses.append((p, hits, exp))

    n = len(scored)
    print(f"Энкодер: {args.encoder}  |  вес синонимов: {r.syn_weight}"
          f"  ({len(r.phrases)} фраз)")
    print(f"Кандидатов в библиотеке (с params): {len(cand)}"
          f"{' [approved-only]' if args.approved_only else ''}")
    print(f"Промптов в эвале: {n} (исключено модификатор-онли: {skipped})\n")
    print(f"  strict top-1 (точный прототип):  {strict1:>3}/{n}  = {strict1/n:5.1%}")
    print(f"  role   top-1 (верная семья):     {role1:>3}/{n}  = {role1/n:5.1%}")
    print(f"  role   top-3:                    {role3:>3}/{n}  = {role3/n:5.1%}")

    if args.show_misses and misses:
        print(f"\nПромахи role top-1 ({len(misses)}):")
        for p, hits, exp in misses:
            got = ", ".join(f"#{h['num']}({h['score']})" for h in hits)
            print(f"  «{p['text']}»  ожид={sorted(exp)}  получил=[{got}]")


if __name__ == "__main__":
    main()
