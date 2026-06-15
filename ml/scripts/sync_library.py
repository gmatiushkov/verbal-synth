#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_library.py — замыкает цикл ТЮНИНГА (PIVOT_RETRIEVAL.md §7, шаг 3/E).

Юзер правит нумерованные пресеты в синте и пересохраняет их в Patches/ под тем же именем.
Этот скрипт тянет params из Patches/<preset_file> ОБРАТНО в library.json (источник правды),
переdecode-ит attributes под новые params. Retrieval сразу подхватывает (params читаются на лету),
но в git коммитим именно library.json — поэтому синк нужен перед коммитом и для бэкапа тюнинга.

Что НЕ трогает: descriptors/target/role/num/name (семантика для retrieval-индекса).
approved: по умолчанию НЕ меняем; --approve "1,33,48" помечает перечисленные num как утверждённые;
          --approve-changed помечает approved=true у всех, чьи params изменились в этот синк.

    python ml/scripts/sync_library.py                 # синк params из Patches → library.json
    python ml/scripts/sync_library.py --dry-run       # показать дифф, не писать
    python ml/scripts/sync_library.py --approve 33,34  # синк + пометить #33,#34 утверждёнными
"""

import argparse
import io
import json
import sys
from pathlib import Path

import attr_decode as ad
import param_convert as pc

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
LIB = ROOT / "data" / "library" / "library.json"
PATCHES = REPO / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"
TOL = 1e-4                                              # порог «параметр изменился»


def _load(p):
    return json.loads(io.open(p, encoding="utf-8-sig").read())


def _changed(old, new):
    """Какие из 38 параметров отличаются (по PARAM_ORDER, с допуском TOL)."""
    diff = []
    for name in pc.PARAM_ORDER:
        a = float((old or {}).get(name, 0.0))
        b = float((new or {}).get(name, 0.0))
        if abs(a - b) > TOL:
            diff.append(name)
    return diff


def main():
    ap = argparse.ArgumentParser(description="Синк тюнинга из Patches/ обратно в library.json.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--approve", default="", help="список num через запятую → approved=true")
    ap.add_argument("--approve-changed", action="store_true",
                    help="пометить approved=true у всех изменившихся в этот синк")
    args = ap.parse_args()

    approve_nums = {int(x) for x in args.approve.replace(" ", "").split(",") if x}
    lib = _load(LIB)

    updated, missing, unchanged, approved_now = [], [], 0, []
    for e in lib["entries"]:
        pf = e.get("preset_file")
        fp = PATCHES / pf if pf else None
        if not fp or not fp.exists():
            if e.get("params") is not None:            # покрытый, но файла на диске нет
                missing.append(e["name"])
            continue
        disk = _load(fp)
        # нормализуем формат: берём только 38 известных имён
        norm = {n: min(max(float(disk.get(n, (e.get("params") or {}).get(n, 0.0))), 0.0), 1.0)
                for n in pc.PARAM_ORDER}
        diff = _changed(e.get("params"), norm)
        if diff:
            updated.append((e["num"], e["name"], len(diff)))
            if not args.dry_run:
                e["params"] = norm
                e["attributes"] = ad.decode_all(norm)
                if args.approve_changed:
                    e["approved"] = True
                    approved_now.append(e["num"])
        else:
            unchanged += 1
        if e["num"] in approve_nums and not args.dry_run:
            e["approved"] = True
            approved_now.append(e["num"])

    print(f"Синк Patches → library.json{'  [DRY-RUN]' if args.dry_run else ''}")
    print(f"  изменены params:  {len(updated)}")
    for num, name, nd in updated[:40]:
        print(f"      #{num:>3} {name}  (Δ{nd} параметр.)")
    if len(updated) > 40:
        print(f"      … и ещё {len(updated)-40}")
    print(f"  без изменений:    {unchanged}")
    if missing:
        print(f"  нет файла в Patches ({len(missing)}): {', '.join(missing[:8])}{' …' if len(missing) > 8 else ''}")
    if approved_now:
        print(f"  approved=true:    {sorted(set(approved_now))}")

    if args.dry_run:
        print("\n(dry-run — library.json не изменён)")
        return
    if updated or approved_now:
        tmp = LIB.with_suffix(".tmp")
        with io.open(tmp, "w", encoding="utf-8") as f:
            json.dump(lib, f, ensure_ascii=False, indent=2)
        tmp.replace(LIB)
        print(f"\nlibrary.json обновлён ({LIB.relative_to(REPO)}).")
    else:
        print("\nНечего синкать — library.json не тронут.")


if __name__ == "__main__":
    main()
