#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_patches_to_synth.py — выгрузка патчей из store в загружаемые пресеты синта.

Синт грузит пресеты как плоский JSON {имя_параметра: norm[0..1]} из папки Patches рядом
с .exe. Это ровно поле `params` записи store. Скрипт пишет по файлу на патч, чтобы их
можно было послушать в менеджере пресетов.

Использование:
  python ml/scripts/export_patches_to_synth.py --in ml/data/test_batch/v4/patches_v4_test.json
  (--out по умолчанию — build/.../Release/Patches; --prefix — префикс имени; --clean — снести
   ранее выгруженные с тем же префиксом)
"""

import argparse
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # корень репозитория
DEFAULT_OUT = ROOT / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"


def main():
    ap = argparse.ArgumentParser(description="Экспорт патчей store → пресеты синта.")
    ap.add_argument("--in", dest="inp", required=True, help="store JSON (patches_*.json)")
    ap.add_argument("--out", default=None, help="папка Patches (деф. Release)")
    ap.add_argument("--prefix", default="v4 ", help="префикс имени файла (деф. 'v4 ')")
    ap.add_argument("--clean", action="store_true", help="удалить ранее выгруженные с этим префиксом")
    args = ap.parse_args()

    out = Path(args.out) if args.out else DEFAULT_OUT
    if not out.exists():
        raise SystemExit(f"Папка не найдена: {out}\nУкажи --out (где лежат заводские пресеты).")

    store = json.loads(io.open(args.inp, encoding="utf-8-sig").read())
    entries = store["entries"]

    if args.clean:
        for f in out.glob(f"{args.prefix}*.json"):
            f.unlink()

    written = []
    for e in entries:
        params = e["params"]
        name = f"{args.prefix}{e['spec_id']}"
        path = out / f"{name}.json"
        # плоский {param: float} — формат заводских пресетов
        with io.open(path, "w", encoding="utf-8") as f:
            json.dump(params, f, ensure_ascii=False)
        written.append((name, e.get("concept", "")))

    print(f"Выгружено {len(written)} пресетов → {out}")
    for name, concept in written:
        print(f"  {name}   «{concept}»")


if __name__ == "__main__":
    main()
