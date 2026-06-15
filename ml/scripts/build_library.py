#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_library.py — собрать БИБЛИОТЕКУ ПРОТОТИПОВ (пивот на retrieval, PIVOT_RETRIEVAL.md).

1 прототип = 1 цель таксономии (140). Источник параметров:
  • утверждённый [REF]-якорь (reference_anchors.json) — приоритет;
  • заводской golden-пресет (FACTORY ниже);
  • иначе ПРОБЕЛ (params=null) → сгенерим Claude'ом (gen_library.py), юзер дотюнит.

Нумерация: глобальный 3-значный номер в порядке таксономии (блоки категорий) → синт сортирует
по имени, юзер идёт по порядку. Имя файла = "NNN <русское имя цели>.json".

Выход:
  • ml/data/library/library.json — ИСТОЧНИК ПРАВДЫ (num/name/target/role/bank/source/approved/params/
    descriptors/attributes). descriptors+attributes = семантика для будущей генерации запросов (не из 38 чисел).
  • нумерованные пресеты в Patches для ПОКРЫТЫХ целей; чистка старых имён ([REF]/[V5]/заводские/v4/v5ref).

Запуск:  python ml/scripts/build_library.py            (пишет library + пресеты + чистит)
         python ml/scripts/build_library.py --dry-run  (только план/счётчики)
"""

import argparse
import io
import json
import re
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
MAP_PATH = ROOT / "config" / "v5" / "taxonomy_to_role.json"
ROLES = ROOT / "config" / "v4" / "roles.json"
REF_STORE = ROOT / "data" / "reference" / "reference_anchors.json"
PATCHES = REPO / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"
LIB_OUT = ROOT / "data" / "library" / "library.json"
_ILLEGAL = re.compile(r'[<>:"\\/|?*]')

# Заводские golden-эталоны → цель таксономии (params из файла в Patches).
FACTORY = {
    "виолончель (смычок, вибрато)": "Cello.json",
    "скрипка (вибрато, яркая)": "Violin.json",
    "церковный орган": "Church Organ.json",
    "орган Хаммонд с лесли": "Rock Leslie Organ.json",
    "фортепиано (мягкий плак)": "Piano.json",
    "acid-бас (резонанс+огибающая)": "Dirty Acid 303 Bass.json",
    "reese-бас (детюн, грязный)": "Reese Bass.json",
    "тёплый аналоговый пэд": "Slow Ambient Pad.json",
    "хор/вокальный ах": "Voices Singing Yao.json",
    "классическая гитара (щипок)": "Guitar.json",
    "стальная акустическая гитара": "Overdrive Short Guitar.json",
    "колокол (длинный затухающий)": "Thin Bell.json",
}
# Старые схемы имён (префиксы), которые чистим из Patches (заменяются нумерованными).
# ВНИМАНИЕ: pathlib.glob трактует [..] как класс символов — матчим по startswith, не glob.
CLEAN_PREFIXES = ["[REF] ", "[V5] ", "v5ref ", "v4 ", "v5b "]


def _load(p):
    return json.loads(io.open(p, encoding="utf-8-sig").read())


def safe(s):
    return " ".join(_ILLEGAL.sub("-", s).split()).strip(" .")


def main():
    ap = argparse.ArgumentParser(description="Сборка библиотеки прототипов (retrieval).")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    mp = _load(MAP_PATH)
    roles = _load(ROLES)["roles"]
    store = _load(REF_STORE)
    ref_by_target = {}
    for e in store["entries"]:
        if e.get("approved") and isinstance(e.get("params"), dict):
            ref_by_target[e["target"]] = e["params"]

    entries, num = [], 0
    cov_ref = cov_fact = gaps = 0
    for cat, items in mp["mapping"].items():
        for ent in items:
            num += 1
            tgt = ent["target"]
            role = ent["role"]
            bank = ent.get("bank") or roles[role]["banks"][0]
            name = f"{num:03d} {safe(tgt)}"
            numbered = PATCHES / f"{name}.json"
            # ПРИОРИТЕТ params (идемпотентно): [REF] > заводской оригинал > нумерованный пресет на диске
            # (восстанавливает после чистки оригиналов И подхватывает ручной тюнинг при ре-ране).
            params, source = None, "gen"
            if tgt in ref_by_target:
                params, source = ref_by_target[tgt], "ref"
                cov_ref += 1
            elif tgt in FACTORY and (PATCHES / FACTORY[tgt]).exists():
                params, source = _load(PATCHES / FACTORY[tgt]), "factory"
                cov_fact += 1
            elif numbered.exists():
                params = _load(numbered)
                source = "factory" if tgt in FACTORY else "gen"
                if source == "factory":
                    cov_fact += 1
            else:
                gaps += 1
            # добить до 38 и декодировать атрибуты (для семантики запросов)
            attrs = None
            if params is not None:
                params = pc.patch_real_to_norm(pc.patch_norm_to_real(params))
                attrs = ad.decode_all(params)
            name = f"{num:03d} {safe(tgt)}"
            entries.append({
                "num": num, "name": name, "preset_file": f"{name}.json",
                "target": tgt, "category": cat, "role": role, "bank": bank,
                "source": source, "approved": source in ("ref", "factory"),
                "descriptors": list(ent.get("descriptors", [])),
                "attributes": attrs, "params": params,
            })

    print("=" * 78)
    print(f"Библиотека: {len(entries)} целей | покрыто [REF]={cov_ref} + заводских={cov_fact} "
          f"= {cov_ref+cov_fact} | ПРОБЕЛОВ (генерить)={gaps}")
    print("=" * 78)
    if args.dry_run:
        for e in entries[:6]:
            print(f"  {e['name']:<42} [{e['source']}] {e['attributes'] or ''}")
        print(f"  ... всего {len(entries)}")
        print(f"\nПервые ПРОБЕЛЫ: " + ", ".join(e['name'] for e in entries if e['source'] == 'gen')[:300])
        return

    LIB_OUT.parent.mkdir(parents=True, exist_ok=True)
    with io.open(LIB_OUT, "w", encoding="utf-8") as f:
        json.dump({"version": "1.0", "note": "библиотека прототипов retrieval; источник правды",
                   "count": len(entries), "entries": entries}, f, ensure_ascii=False, indent=2)
    print(f"library.json → {LIB_OUT.relative_to(REPO)}")

    # чистка старых имён (по префиксу — bracket-имена glob не ловит)
    removed = 0
    for fp in PATCHES.iterdir():
        if fp.is_file() and any(fp.name.startswith(p) for p in CLEAN_PREFIXES):
            fp.unlink()
            removed += 1
    for f in FACTORY.values():
        fp = PATCHES / f
        if fp.exists():
            fp.unlink()
            removed += 1
    # нумерованные пресеты для покрытых
    wrote = 0
    for e in entries:
        if e["params"] is None:
            continue
        with io.open(PATCHES / e["preset_file"], "w", encoding="utf-8") as f:
            json.dump(e["params"], f, ensure_ascii=False)
        wrote += 1
    print(f"Patches: удалено старых {removed}, записано нумерованных {wrote} (пробелы появятся при генерации)")


if __name__ == "__main__":
    main()
