#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_synthetic.py — АВТОМАТИЧЕСКИЙ identity-эвал на самозамеченных запросах (PIVOT §5).

queries.json (gen_queries.py): на каждый прототип #N ~30 пользовательских формулировок → верный
ответ известен ПО ПОСТРОЕНИЮ (#N). Раз синонимы в индексе ВЫКЛЮЧЕНЫ (DEFAULT_SYN_WEIGHT=0), это
НЕ круговая логика: индекс матчит по target+descriptors, а тестируем по независимым формулировкам.
Даёт честный top-1/top-3 на сотнях запросов без новых трат API. Дополняет ручной golden (56 промптов).

  • strict — top-1/top-3 по ТОЧНОМУ прототипу (#N).
  • role   — top-1/top-3 по верной РОЛИ (мягче: pluck-бас vs reese-бас — одна семья).
Разбивка по категориям + худшие прототипы (низкий recall) — куда копать.

    python ml/scripts/eval_synthetic.py
    python ml/scripts/eval_synthetic.py --per 10           # по 10 запросов с прототипа (быстрее)
    python ml/scripts/eval_synthetic.py --syn-weight 0.9   # сравнить с включёнными синонимами
    python ml/scripts/eval_synthetic.py --worst 15
"""

import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from retrieval import Retriever, DEFAULT_ENCODER, QUERIES, detect_axes

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def main():
    ap = argparse.ArgumentParser(description="Автоэвал retrieval на самозамеченных queries.json.")
    ap.add_argument("--encoder", default=DEFAULT_ENCODER)
    ap.add_argument("--syn-weight", type=float, default=None)
    ap.add_argument("--attr-lambda", type=float, default=None, help="вес атрибутного ре-ранка (0=выкл)")
    ap.add_argument("--per", type=int, default=None, help="ограничить N запросов на прототип")
    ap.add_argument("--worst", type=int, default=12, help="сколько худших прототипов показать")
    args = ap.parse_args()

    if not QUERIES.exists():
        sys.exit("Нет queries.json — сгенерируй gen_queries.py.")
    qdata = json.loads(io.open(QUERIES, encoding="utf-8-sig").read())["entries"]

    rkw = {"encoder_name": args.encoder}
    if args.syn_weight is not None:
        rkw["syn_weight"] = args.syn_weight
    if args.attr_lambda is not None:
        rkw["attr_lambda"] = args.attr_lambda
    r = Retriever(**rkw)
    role_by_num = {e["num"]: e["role"] for e in r.entries}
    cat_by_num = {e["num"]: e["category"] for e in r.entries}
    cand = set(role_by_num)

    # собрать (запрос, верный num) только для прототипов, реально присутствующих в индексе
    pairs = []
    for snum, qs in qdata.items():
        num = int(snum)
        if num not in cand:
            continue
        use = qs[: args.per] if args.per else qs
        for q in use:
            pairs.append((q, num))
    if not pairs:
        sys.exit("Нет пар запрос→прототип.")

    # батч-кодирование всех запросов разом (быстро), затем матрица сходств
    texts = [r.q_prefix + q for q, _ in pairs]
    qemb = r._encode(texts)                                # (Nq, dim) L2-норм
    sims_all = (qemb @ r.emb.T) * r.weights                # (Nq, Nphrases)

    s1 = s3 = rl1 = rl3 = 0
    per_cat = defaultdict(lambda: [0, 0])                  # cat → [hits_strict1, total]
    per_proto = defaultdict(lambda: [0, 0])                # num → [hits_strict1, total]
    n = len(pairs)
    owner = r.owner
    nptypes = len(r.entries)
    for i, (q, num) in enumerate(pairs):
        sims = sims_all[i]
        best = np.full(nptypes, -1.0, dtype=np.float32)
        np.maximum.at(best, owner, sims)                   # max-pool фраз → прототипы
        if r.attr_rerank and r.attr_lambda > 0:            # атрибутный ре-ранк (как в search)
            det = detect_axes(q)
            if any(det.values()):
                best = best + r.attr_lambda * r._attr_bonus_vec(det)
        order = np.argsort(-best)[:3]
        top_nums = [r.entries[int(j)]["num"] for j in order]
        top_roles = [role_by_num[t] for t in top_nums]
        exp_role = role_by_num[num]
        h1 = top_nums[0] == num
        h3 = num in top_nums
        s1 += h1; s3 += h3
        rl1 += top_roles[0] == exp_role
        rl3 += exp_role in top_roles
        per_cat[cat_by_num[num]][0] += h1; per_cat[cat_by_num[num]][1] += 1
        per_proto[num][0] += h1; per_proto[num][1] += 1

    print(f"Энкодер: {args.encoder}  |  вес синонимов: {r.syn_weight}")
    print(f"Запросов: {n} из {len(set(num for _, num in pairs))} прототипов"
          f"{f' (≤{args.per}/прототип)' if args.per else ''}\n")
    print(f"  strict top-1:  {s1:>4}/{n} = {s1/n:5.1%}      strict top-3: {s3:>4}/{n} = {s3/n:5.1%}")
    print(f"  role   top-1:  {rl1:>4}/{n} = {rl1/n:5.1%}      role   top-3: {rl3:>4}/{n} = {rl3/n:5.1%}\n")

    print("По категориям (strict top-1):")
    for cat, (h, t) in sorted(per_cat.items(), key=lambda x: x[1][0] / max(x[1][1], 1)):
        print(f"  {cat:<22} {h:>4}/{t:<4} = {h/t:5.1%}")

    worst = sorted(per_proto.items(), key=lambda x: x[1][0] / max(x[1][1], 1))[: args.worst]
    print(f"\nХудшие {args.worst} прототипов (strict top-1 recall):")
    nm = {e["num"]: e["target"] for e in r.entries}
    for num, (h, t) in worst:
        print(f"  #{num:>3} {nm[num][:40]:<42} {h:>2}/{t} = {h/t:4.0%}")


if __name__ == "__main__":
    main()
