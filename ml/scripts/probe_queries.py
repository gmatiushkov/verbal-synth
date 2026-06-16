#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe_queries.py — прогон набора «трудных» запросов через ПРОДАКШН-логику (retrieval + strip + модификаторы)
за один проход (одна загрузка энкодера). Для диагностики слабых мест системы.

    python ml/scripts/probe_queries.py              # встроенный диагностический набор
    python ml/scripts/probe_queries.py "свой запрос" "другой"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from retrieval import Retriever
from modifiers import strip_modifier_words, apply_modifiers
import predict as P

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

PROBE = [
    # композиционная идентичность (определение+существительное)
    "бас гитара", "электрогитара", "органный бас", "духовой лид",
    # размытое существительное
    "бас", "лид", "пэд", "клавиши",
    # гибриды
    "гитарный пэд", "вокальный лид", "колокольный пэд",
    # абстракции / метафоры
    "что-то холодное и металлическое", "тёплый винтажный звук", "космос", "страшный звук",
    # жанр/роль
    "транс лид", "дабстеп бас", "лоу-фай клавиши",
    # мульти-модификатор и over-stripping
    "очень тёплый мягкий низкий бас", "короткий звук", "тёмная атмосфера",
    # коллизия модификатор↔идентичность, отрицание/относительность, английский
    "длинный затухающий колокол", "яркая стальная гитара", "не яркий бас", "бас но повыше", "warm pad",
]


def short(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"


def main():
    queries = sys.argv[1:] or PROBE
    r = Retriever()
    for q in queries:
        ident = strip_modifier_words(q)
        hits = r.search(ident, k=3)
        before = dict(r.params_of(hits[0]["num"]))
        after, applied = apply_modifiers(before, q)
        ex = P._build_explain(q, ident, hits, before, after, applied)
        print("─" * 70)
        strip = ex["stripped"]
        print(f"«{q}»   →  идентичность=«{ident}»" + (f"   (убрано: {' '.join(strip)})" if strip else ""))
        t3 = "  |  ".join(f"#{h['num']} {short(h['target'],22)} ({h['role']},{h['score']})"
                          for h in ex["retrieval"])
        print(f"   top3: {t3}")
        mods = ", ".join(ex["modifiers"]) if ex["modifiers"] else "—"
        ch = "; ".join(f"{c['param']} {c['before_real']}→{c['after_real']}{c['unit']}" for c in ex["changes"])
        print(f"   модификаторы: {mods}" + (f"   |  изменения: {ch}" if ch else ""))
    print("─" * 70)


if __name__ == "__main__":
    main()
