#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe_queries.py — прогон набора «трудных»/вне-обучения запросов через ПРОДАКШН-логику
(классификатор L2 + модификаторы L4) за один проход (энкодер грузится один раз).
Для диагностики слабых мест: куда уводит классификатор и достаточно ли двигают модификаторы.

    python ml/scripts/probe_queries.py                 # встроенный диагностический набор
    python ml/scripts/probe_queries.py "свой запрос" "другой"
    python ml/scripts/probe_queries.py --method retrieval   # сравнить с baseline
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import predict as P

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

PROBE = [
    # --- голые существительные: реальные инструменты (НЕТ дословно в обучении) ---
    "барабан", "скрипка", "орган", "флейта", "гитара", "труба", "саксофон", "пианино",
    # --- размытые роли (были провалами сырого retrieval) ---
    "бас", "лид", "пэд", "клавиши",
    # --- композиции / гибриды (главное слабое место) ---
    "бас гитара", "саб бас", "органный бас", "гитарный пэд", "вокальный лид", "хрустящий снейр",
    # --- модификаторо-тяжёлые: проверяем СИЛУ сдвига у дна диапазона ---
    "плавный колокольчик", "очень яркий бас", "мягкий тёплый пэд",
    "длинный космический пэд", "короткий резкий лид", "просторный далёкий звон",
    # --- абстракции / метафоры ---
    "что-то холодное и металлическое", "тёплый винтажный звук", "космос", "страшный звук",
    # --- отрицание / относительность / английский ---
    "не яркий бас", "бас без перегруза", "бас но повыше", "warm pad",
]


def short(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"


def main():
    args = list(sys.argv[1:])
    method = None
    if "--method" in args:
        i = args.index("--method")
        method = args[i + 1]
        del args[i:i + 2]
    queries = args or PROBE
    for q in queries:
        patch, hits, applied, ex = P.predict(q, method=method)
        print("─" * 78)
        m = "clf" if ex["method"] == "clf" else "retr"
        t3 = "  |  ".join(f"#{h['num']} {short(h['target'], 20)} ({h['role']},{h['score']})"
                          for h in ex["retrieval"])
        print(f"«{q}»   [{m}]")
        print(f"   top3: {t3}")
        mods = ", ".join(ex["modifiers"]) if ex["modifiers"] else "—"
        ch = "; ".join(f"{c['param']} {c['before_real']}→{c['after_real']}{c['unit']}" for c in ex["changes"])
        print(f"   модификаторы: {mods}" + (f"\n   изменения: {ch}" if ch else ""))
    print("─" * 78)


if __name__ == "__main__":
    main()
