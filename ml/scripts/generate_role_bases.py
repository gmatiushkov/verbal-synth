#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_role_bases.py — собрать СТОР БАЗ РОЛЕЙ: роль → параметры ЭТАЛОНА (38 norm).

Идентичность роли (acid → фильтр-огибающая+резонанс, organ → драубары, bell → металл+звон) берётся
из РУЧНОГО эталона, а не угадывается. Источник по ролям (из audit_role_bases.py):
  • [REF]-якорь (approved) — приоритет; для ролей с >1 якорем берём КАНОНИЧНУЮ цель (CANON ниже);
  • заводской golden-пресет — для ролей без [REF] (+ bell/guitar, не слинкованные в карте).

Выход: ml/config/v5/role_bases.json — {role: {source, ident, params{38 norm}}}. Это база для рендера
«роль→эталон ⊕ оси» (param_rules). roles.json/CALIB_BASE остаются фолбэком там, где базы нет.
"""

import io
import json
import sys
from pathlib import Path

import param_convert as pc

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
ROLES = ROOT / "config" / "v4" / "roles.json"
REF_STORE = ROOT / "data" / "reference" / "reference_anchors.json"
PATCHES = REPO / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"
OUT = ROOT / "config" / "v5" / "role_bases.json"

# Каноничная цель для ролей с >1 [REF]-якорем (одна база на роль; остальные тембры — через оси/банк
# или позже сплит роли). Поправишь — перегенери.
CANON = {
    "brass": "труба (открытая/сурдина)",
    "mallet": "вибрафон",
    "pure_tone": "свист",
    "snare_clap": "снэр (нойз+тон)",
    "square_lead": "PWM/квадратный лид",
    "tom": "том (настроенный, питч-дроп)",
}
# Роли без [REF] → заводской golden (файл в Patches).
FACTORY = {
    "acid_bass": "Dirty Acid 303 Bass.json",
    "choir_pad": "Voices Singing Yao.json",
    "organ":     "Church Organ.json",
    "piano":     "Piano.json",
    "reese_bass": "Reese Bass.json",
    "string":    "Cello.json",
    "warm_pad":  "Slow Ambient Pad.json",
    "bell":      "Thin Bell.json",       # не слинкован в карте, но это и есть эталон колокола
    "guitar":    "Guitar.json",
}


def _load(p):
    return json.loads(io.open(p, encoding="utf-8-sig").read())


def main():
    roles = list(_load(ROLES)["roles"].keys())
    store = _load(REF_STORE)
    ref_by_role = {}
    for e in store["entries"]:
        if e.get("approved") and isinstance(e.get("params"), dict):
            ref_by_role.setdefault(e["role"], []).append(e)

    bases, gaps = {}, []
    for r in roles:
        refs = ref_by_role.get(r, [])
        if refs:
            chosen = next((e for e in refs if e.get("target") == CANON.get(r)), refs[0])
            bases[r] = {"source": "ref", "ident": chosen.get("target"),
                        "file": chosen.get("preset_file"), "params": chosen["params"]}
        elif r in FACTORY and (PATCHES / FACTORY[r]).exists():
            params = _load(PATCHES / FACTORY[r])
            bases[r] = {"source": "factory", "ident": FACTORY[r], "file": FACTORY[r], "params": params}
        else:
            gaps.append(r)

    # дополним до полного 38-вектора (на случай отсутствующих ключей у заводских)
    for r, b in bases.items():
        full = pc.patch_norm_to_real(b["params"])          # клампит/добивает дефолтами
        b["params"] = pc.patch_real_to_norm(full)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump({"version": "5.0", "note": "роль→эталон-база (38 norm) для рендера роль⊕оси",
                   "canon": CANON, "bases": bases}, f, ensure_ascii=False, indent=2)
    print(f"Собрано баз: {len(bases)}/{len(roles)} → {OUT.relative_to(REPO)}")
    if gaps:
        print(f"ПРОБЕЛЫ (нет ни [REF], ни заводского): {gaps}")
    src = {}
    for r, b in bases.items():
        src[b["source"]] = src.get(b["source"], 0) + 1
    print(f"Источники: {src}")


if __name__ == "__main__":
    main()
