#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_modifiers.py — НАПРАВЛЕННЫЙ эвал модификаторов (PIVOT §5, фаза 2).

Без рендера: берём базовый прототип (retrieval по base-запросу), применяем модификатор и проверяем,
что нужный параметр сдвинулся в ОЖИДАЕМУЮ сторону (срез↑ для «ярче», release↓ для «короче», …).
✓ — сдвиг в нужную сторону; ⊘ — параметр уже на границе (нечего двигать); ✗ — не туда/нет сдвига.

    python ml/scripts/eval_modifiers.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import param_convert as pc
from modifiers import apply_modifiers
from retrieval import Retriever, DEFAULT_ENCODER

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# (модификатор, base-запрос, параметр, ожидаемый знак сдвига)
CASES = [
    ("яркий", "бас", "lp_cutoff", +1),
    ("тёмный", "лид", "lp_cutoff", -1),
    ("тёплый", "пэд", "lp_cutoff", -1),
    ("пронзительный", "лид", "lp_cutoff", +1),
    ("короткий", "пэд", "amp_release", -1),
    ("длинный тянущийся", "плак", "amp_release", +1),
    ("длинный тянущийся", "плак", "amp_sustain", +1),
    ("агрессивный грязный", "лид", "drive_amount", +1),
    ("чистый гладкий", "acid бас", "drive_amount", -1),
    ("просторный", "пэд", "reverb_mix", +1),
    ("сухой", "пэд", "reverb_mix", -1),
    ("ниже", "лид", "osc1_octave", -1),
    ("выше", "суббас", "osc1_octave", +1),
    ("плавно нарастающий", "плак", "amp_attack", +1),
    ("резкая атака щипок", "пэд", "amp_attack", -1),
]


def main():
    r = Retriever(encoder_name=DEFAULT_ENCODER)
    ok = sat = bad = 0
    print(f"Энкодер: {DEFAULT_ENCODER}\n")
    print(f"{'модификатор+база':<34} {'параметр':<14} {'было→стало (реал)':<26} итог")
    print("-" * 84)
    for mod, base, param, sign in CASES:
        hits = r.search(base, k=1)
        p0 = r.params_of(hits[0]["num"])
        p1, applied = apply_modifiers(p0, f"{mod} {base}")
        r0 = pc.norm_to_real(param, p0[param])
        r1 = pc.norm_to_real(param, p1[param])
        d = r1 - r0
        eps = abs(r0) * 1e-3 + 1e-6
        if (d > eps and sign > 0) or (d < -eps and sign < 0):
            mark, res = "✓", "ok"; ok += 1
        elif abs(d) <= eps:
            mark, res = "⊘", "сатур."; sat += 1
        else:
            mark, res = "✗", "не туда"; bad += 1
        fmt = (lambda x: f"{x:.0f}") if abs(r0) >= 10 or param == "osc1_octave" else (lambda x: f"{x:.2f}")
        base_proto = hits[0]["target"][:16]
        print(f"{(mod+' '+base):<34} {param:<14} {fmt(r0)+'→'+fmt(r1):<26} {mark} {res}  [{base_proto}]")
    n = len(CASES)
    print("-" * 84)
    print(f"Верное направление: {ok}/{n}  | сатурация: {sat}  | мимо: {bad}")


if __name__ == "__main__":
    main()
