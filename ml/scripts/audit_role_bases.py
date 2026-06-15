#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_role_bases.py — АУДИТ: у каких ролей база может быть = ТВОЙ ЭТАЛОН, а у каких пробел.

Для реворка «роль→эталон-база» нужно знать, на что опереться по каждой из 31 роли:
  1) УТВЕРЖДЁННЫЙ [REF]-якорь (ml/data/reference/reference_anchors.json, approved=true) — лучший источник;
  2) заводской/golden пресет (файл из поля reference карты taxonomy_to_role, если ещё лежит в Patches);
  3) иначе ПРОБЕЛ — база роли сейчас «угадана» (roles.json/CALIB), её стоит создать/дотюнить.

Печатает по каждой роли: источник базы + файл/цель + ключевые параметры эталона + список ПРОБЕЛОВ.
"""

import io
import json
import sys
from collections import defaultdict
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
MAP_PATH = ROOT / "config" / "v5" / "taxonomy_to_role.json"
PATCHES = REPO / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"

KEY = ["osc1_table", "osc1_position", "osc2_table", "osc2_position", "mix_osc2",
       "lp_cutoff", "lp_resonance", "fenv_amount", "amp_sustain", "amp_release"]


def _load(p):
    return json.loads(io.open(p, encoding="utf-8-sig").read())


def keyparams(params):
    """params (norm-словарь) → краткая сводка реальных значений идентичности."""
    out = []
    for n in KEY:
        if n in params:
            out.append(f"{n.split('_',1)[-1] if n.startswith('osc') else n}={pc.format_real(n, pc.norm_to_real(n, params[n]))}")
    return " ".join(out)


def main():
    roles = list(_load(ROLES)["roles"].keys())
    store = _load(REF_STORE)
    mp = _load(MAP_PATH)

    # 1) утверждённые [REF]-якоря по ролям
    ref_by_role = defaultdict(list)
    for e in store["entries"]:
        if e.get("approved") and isinstance(e.get("params"), dict):
            ref_by_role[e["role"]].append(e)

    # 2) заводские/golden пресеты из карты, ЕЩЁ существующие в Patches
    fact_by_role = defaultdict(list)
    for _cat, entries in mp["mapping"].items():
        for ent in entries:
            ref = ent.get("reference")
            if not ref or ref == "none":
                continue
            f = PATCHES / ref
            if f.exists() and ref not in [x[0] for x in fact_by_role[ent["role"]]]:
                fact_by_role[ent["role"]].append((ref, ent["target"]))

    have_ref, have_fact, gaps = [], [], []
    print("=" * 100)
    print("АУДИТ БАЗ РОЛЕЙ (источник идентичности для рендера)")
    print("=" * 100)
    print(f"{'роль':<14} {'источник базы':<22} {'эталон':<34} что внутри")
    print("-" * 100)
    for r in sorted(roles):
        refs = ref_by_role.get(r, [])
        facts = fact_by_role.get(r, [])
        if refs:
            src = f"[REF] x{len(refs)}"
            best = refs[0]
            ident = best.get("target", "")[:32]
            kp = keyparams(best["params"])
            have_ref.append(r)
        elif facts:
            src = "заводской"
            ident = facts[0][0][:32]
            try:
                kp = keyparams(_load(PATCHES / facts[0][0]))
            except Exception:
                kp = "(не прочитан)"
            have_fact.append(r)
        else:
            src = "ПРОБЕЛ (база угадана)"
            ident = "—"
            kp = ""
            gaps.append(r)
        print(f"{r:<14} {src:<22} {ident:<34} {kp[:46]}")

    print("-" * 100)
    print(f"ИТОГО ролей: {len(roles)} | с [REF]-эталоном: {len(have_ref)} | "
          f"на заводском: {len(have_fact)} | ПРОБЕЛОВ: {len(gaps)}")
    if gaps:
        print(f"\nПРОБЕЛЫ (нужен ручной эталон): {', '.join(gaps)}")
    # роли с несколькими [REF] — можно выбрать самый каноничный таргет под базу
    multi = {r: [e.get("target") for e in ref_by_role[r]] for r in have_ref if len(ref_by_role[r]) > 1}
    if multi:
        print("\nУ ролей >1 [REF]-якоря (выберешь, какой каноничный под базу):")
        for r, tgts in multi.items():
            print(f"  {r}: {tgts}")


if __name__ == "__main__":
    main()
