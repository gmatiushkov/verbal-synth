#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_golden.py — АВТО-СКОРЕР модели против золотого набора (ml/eval/golden_prompts.json).

Северная звезда качества: гоняем РЕАЛЬНЫЕ пользовательские запросы через модель (predict.py),
декодируем выход в атрибуты (attr_decode) и сравниваем с размеченным ожиданием. Это меряет то,
что юзер реально набирает (а не Sonnet-стиль held-out). Ординальные оси (регистр/яркость/тело)
дают и точное совпадение, и «в пределах 1 уровня». Печатает таблицу + список промахов.

Один и тот же скорер подойдёт и будущей классиф.модели (та же decode_all на её рендере).

Запуск:  python ml/scripts/eval_golden.py            # текущая живая модель (ml/models)
         python ml/scripts/eval_golden.py --show-all # печать предсказаний по всем промптам
"""

import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import attr_decode as ad
import predict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "eval" / "golden_prompts.json"
ATTRS = ["bank", "register", "brightness", "body"]


def main():
    ap = argparse.ArgumentParser(description="Скорер модели против золотого набора.")
    ap.add_argument("--golden", default=str(GOLDEN))
    ap.add_argument("--show-all", action="store_true", help="печать предсказаний по каждому промпту")
    args = ap.parse_args()

    data = json.loads(io.open(args.golden, encoding="utf-8-sig").read())
    prompts = data["prompts"]

    exact = defaultdict(int)
    near = defaultdict(int)        # в пределах 1 уровня (ординальные)
    total = defaultdict(int)
    misses = []
    rows = []

    for pr in prompts:
        text = pr["text"]
        patch = predict.predict(text)
        dec = ad.decode_all(patch)
        line = {"text": text, "pred": {}, "exp": {}}
        bad = []
        for a in ATTRS:
            exp = pr.get(a)
            line["pred"][a] = dec.get(a)
            line["exp"][a] = exp
            if exp is None:
                continue
            total[a] += 1
            got = dec.get(a)
            if got == exp:
                exact[a] += 1
                near[a] += 1
            else:
                d = ad.ordinal_dist(a, got, exp)
                if d is not None and d <= 1:
                    near[a] += 1
                    bad.append(f"{a}: {got}≈{exp}")   # близко, но не точно
                else:
                    bad.append(f"{a}: {got}≠{exp}")
        rows.append((text, dec, pr, bad))
        if bad:
            misses.append((text, bad))

    print("=" * 72)
    print(f"ЗОЛОТОЙ ЭВАЛ · модель: ml/models (живая) · промптов: {len(prompts)}")
    print("=" * 72)
    print(f"{'атрибут':<12} {'точно':>10} {'±1 ур.':>10}   (из размеченных)")
    print("-" * 50)
    for a in ATTRS:
        t = total[a]
        if not t:
            continue
        ex = 100 * exact[a] / t
        ne = 100 * near[a] / t
        nn = "  (номинал.)" if a == "bank" else ""
        print(f"{a:<12} {ex:>8.0f}% {ne:>9.0f}%   n={t}{nn}")
    # средняя точная по 4 атрибутам
    allt = sum(total[a] for a in ATTRS)
    alle = sum(exact[a] for a in ATTRS)
    print("-" * 50)
    print(f"{'СРЕДНЕЕ':<12} {100*alle/max(1,allt):>8.0f}%   (точных {alle}/{allt})")

    if args.show_all:
        print("\n── ВСЕ ПРЕДСКАЗАНИЯ (pred | exp) ──")
        for text, dec, pr, bad in rows:
            mark = "OK " if not bad else "!! "
            print(f"{mark}{text}")
            for a in ATTRS:
                e = pr.get(a)
                tag = "" if e is None else (" ✓" if dec[a] == e else " ✗")
                print(f"      {a:<11} pred={str(dec[a]):<10} exp={str(e)}{tag}")
    else:
        print(f"\n── ПРОМАХИ ({len(misses)}/{len(prompts)} промптов) ──")
        for text, bad in misses:
            print(f"  {text:<36} {' | '.join(bad)}")


if __name__ == "__main__":
    main()
