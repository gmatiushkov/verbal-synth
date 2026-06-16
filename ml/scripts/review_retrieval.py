#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_retrieval.py — ТАБЛИЦА-ГЛЯНЕЦ: прогоняет запросы через retrieval и пишет читаемую
таблицу «запрос → что вернулось (top-3)», чтобы человек на глаз оценил правильность
(не нужно руками размечать golden — просто читаешь имена и судишь).

Источник запросов:
  • по умолчанию — тексты из ml/eval/golden_retrieval.json;
  • --queries FILE — свой список (по запросу на строку, # = комментарий);
  • остатком аргументов — запросы прямо из командной строки.

Пишет ml/eval/RETRIEVAL_REVIEW.md (открой в редакторе) и краткое summary в stdout.

    python ml/scripts/review_retrieval.py
    python ml/scripts/review_retrieval.py "тёплый бас" "что-то яркое" "гитарный пэд"
    python ml/scripts/review_retrieval.py --queries my_queries.txt
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

EVAL = Path(__file__).resolve().parents[1] / "eval"
GOLDEN = EVAL / "golden_retrieval.json"
OUT = EVAL / "RETRIEVAL_REVIEW.md"


def load_queries(args):
    if args.queries:
        lines = io.open(args.queries, encoding="utf-8-sig").read().splitlines()
        return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
    if args.text:
        return [" ".join(args.text)] if False else list(args.text)
    g = json.loads(io.open(GOLDEN, encoding="utf-8-sig").read())["prompts"]
    return [p["text"] for p in g]


def main():
    ap = argparse.ArgumentParser(description="Глянец-таблица retrieval: запрос → результат.")
    ap.add_argument("text", nargs="*", help="запросы прямо в аргументах")
    ap.add_argument("--queries", help="файл со списком запросов (строка = запрос)")
    ap.add_argument("--encoder", default=DEFAULT_ENCODER)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    queries = load_queries(args)
    if not queries:
        sys.exit("Нет запросов.")
    r = Retriever(encoder_name=args.encoder)

    rows = []
    for q in queries:
        hits = r.search(q, k=3)
        rows.append((q, hits))

    # markdown
    lines = ["# Retrieval review — глянец «запрос → что вернулось»", "",
             f"Энкодер: `{args.encoder}` · прототипов: {len(r.entries)} · запросов: {len(queries)}", "",
             "Читай слева направо: верный ли top-1 на слух? Если нет — верный ли вариант в top-2/3?", "",
             "| запрос | top-1 | top-2 | top-3 |", "|---|---|---|---|"]
    for q, hits in rows:
        def cell(h):
            if not h:
                return "—"
            return f"#{h['num']} {h['target']} ({h['score']})"
        c = [cell(hits[i]) if i < len(hits) else "—" for i in range(3)]
        lines.append(f"| {q} | {c[0]} | {c[1]} | {c[2]} |")
    io.open(args.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # stdout — компактно
    print(f"Запросов: {len(queries)} · энкодер: {args.encoder}")
    for q, hits in rows:
        top = hits[0] if hits else None
        alt = "  ".join(f"#{h['num']} {h['target']}" for h in hits[1:3])
        print(f"  {q:<34} → {('#'+str(top['num'])+' '+top['target']) if top else '—':<34}  | {alt}")
    print(f"\nТаблица записана: {Path(args.out)}")


if __name__ == "__main__":
    main()
