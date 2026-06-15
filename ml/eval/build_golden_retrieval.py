#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_golden_retrieval.py — переразметка golden под RETRIEVAL (PIVOT_RETRIEVAL.md §5).

Превращает golden_prompts.json (запрос→перцептивные атрибуты) в golden_retrieval.json
(запрос→ОЖИДАЕМЫЙ прототип). Метрика пивота — identity (top-1/top-3 retrieval), не MSE.

ЧЕРНОВИК, не истина: для каждого промпта берём прототипы ТОЙ ЖЕ роли (role совпадает),
ранжируем по пересечению токенов запроса с именем+descriptors прототипа.
  • primary       — лучший кандидат (СТРОГАЯ метрика: точный прототип). ⚠ ПРОВЕРИТЬ вручную:
                    различает ли запрос вибрафон/маримбу и т.п. — пин нужного num руками.
  • expected      — вся семья роли, по убыванию релевантности (МЯГКАЯ метрика: верная роль).
Маппинг НЕ использует тот же энкодер, что и retrieval (иначе eval стал бы круговым) — только
роль (ручная разметка) + строковое пересечение.

Промпты без роли (модификатор-онли, §9) → expected=[] (исключаются из identity-метрики).

    python ml/eval/build_golden_retrieval.py          # пишет golden_retrieval.json
    python ml/eval/build_golden_retrieval.py --print   # без записи, в stdout
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

EVAL = Path(__file__).resolve().parent
LIB = EVAL.parent / "data" / "library" / "library.json"
SRC = EVAL / "golden_prompts.json"
OUT = EVAL / "golden_retrieval.json"

STOP = {"с", "и", "в", "на", "для", "очень", "звук", "тон", "тембр"}


def toks(s):
    """Грубая нормализация: токены ≥3 букв, обрезка до 4-символьного префикса (псевдо-стем)."""
    return {w[:4] for w in re.findall(r"[а-яёa-z0-9]+", (s or "").lower())
            if len(w) >= 3 and w not in STOP}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="show", action="store_true")
    args = ap.parse_args()

    lib = json.loads(io.open(LIB, encoding="utf-8-sig").read())["entries"]
    by_role = {}
    for e in lib:
        by_role.setdefault(e["role"], []).append(e)

    src = json.loads(io.open(SRC, encoding="utf-8-sig").read())
    out_prompts = []
    for p in src["prompts"]:
        role = p.get("role")
        fam = by_role.get(role, []) if role else []
        qt = toks(p["text"])
        scored = []
        for e in fam:
            et = toks(e.get("target", "")) | set().union(*(toks(d) for d in e.get("descriptors", [])) or [set()])
            scored.append((len(qt & et), -e["num"], e))   # больше пересечение, затем меньший num
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        expected = [e["num"] for _, _, e in scored]
        primary = expected[0] if expected else None
        out_prompts.append({
            "text": p["text"],
            "role": role,
            "primary": primary,
            "primary_target": (by_role[role][[e["num"] for e in by_role[role]].index(primary)]["target"]
                               if primary else None),
            "expected": expected,
        })

    out = {
        "version": "0.1-draft",
        "purpose": ("ЗОЛОТОЙ identity-эвал retrieval: запрос → ожидаемый прототип. primary — строгая "
                    "цель (точный прототип, ЧЕРНОВИК — проверить/пин руками), expected — приемлемая "
                    "семья роли (мягкая). Метрика: top-1 (#1∈?) и top-3. Промпты без роли = []."),
        "how_to_edit": ("Поправь primary под РЕАЛЬНОЕ намерение (различай вибрафон/маримбу и т.п.); "
                        "expected — допустимые альтернативы. Пустой expected исключается из метрики."),
        "prompts": out_prompts,
    }
    if args.show:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    n_role = sum(1 for x in out_prompts if x["role"])
    print(f"Записано {OUT.name}: {len(out_prompts)} промптов "
          f"({n_role} с ролью → identity-метрика, {len(out_prompts)-n_role} модификатор-онли исключены).")


if __name__ == "__main__":
    main()
