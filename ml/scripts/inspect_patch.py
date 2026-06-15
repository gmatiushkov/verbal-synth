#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspect_patch.py — инспектор патчей: нормализованные [0..1] → РЕАЛЬНЫЕ единицы (Шаг 1b).

Читает плоский пресет синта {имя_параметра: norm} ИЛИ store-JSON ({entries:[{params:...}]})
и печатает таблицу реальных значений (мс/Гц/центы/%/имена банков) через param_convert
(зеркало C++). Назначение: «увидеть, как на самом деле устроен ВЫВЕРЕННЫЙ на слух патч»,
чтобы переякорить role.base от эталонов (DATASET_v5_PLAN.md §4.1, §6).

Запуск:
  python ml/scripts/inspect_patch.py --golden                 # 12 ручных эталонов (с метками ролей)
  python ml/scripts/inspect_patch.py "<путь.json>" [...]      # произвольные пресеты/store
  + флаг --base — дополнительно печатать role.base-кандидат (идентичность в реальных ед.)
"""

import argparse
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
PATCHES = REPO / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"

# 12 ручных эталонов → роль (для группировки/переякоривания)
GOLDEN = [
    ("Reese Bass.json", "reese_bass"),
    ("Dirty Acid 303 Bass.json", "acid_bass"),
    ("Slow Ambient Pad.json", "warm_pad"),
    ("Voices Singing Yao.json", "choir_pad"),
    ("Piano.json", "piano"),
    ("Church Organ.json", "organ"),
    ("Rock Leslie Organ.json", "organ"),
    ("Thin Bell.json", "bell"),
    ("Violin.json", "string"),
    ("Cello.json", "string"),
    ("Guitar.json", "guitar"),
    ("Overdrive Short Guitar.json", "guitar"),
]

# параметры идентичности роли (то, что обычно есть в role.base)
BASE_KEYS = [
    "osc1_octave", "osc1_position", "osc2_position", "osc2_detune", "osc2_semitones",
    "mix_osc1", "mix_osc2", "mix_noise",
    "amp_attack", "amp_decay", "amp_sustain", "amp_release", "fenv_to_wt",
]

# показываем компактно сгруппированно
GROUPS = [
    ("осц",    ["osc1_table", "osc1_position", "osc1_octave", "osc2_table", "osc2_position", "osc2_detune", "osc2_semitones"]),
    ("микс",   ["mix_osc1", "mix_osc2", "mix_noise"]),
    ("фильтр", ["lp_cutoff", "lp_resonance", "hp_cutoff", "hp_resonance", "filter_keytrack"]),
    ("amp",    ["amp_attack", "amp_decay", "amp_sustain", "amp_release"]),
    ("fenv",   ["fenv_attack", "fenv_decay", "fenv_sustain", "fenv_release", "fenv_amount", "fenv_to_wt"]),
    ("lfo",    ["lfo1_rate", "lfo1_shape", "lfo1_to_pitch", "lfo1_to_filter", "lfo2_rate", "lfo2_shape", "lfo2_to_wt", "lfo2_to_amp"]),
    ("эфф",    ["drive_amount", "drive_tone", "reverb_time", "reverb_damp", "reverb_mix"]),
]


def load_norm_patches(path):
    """Возвращает [(label, {name:norm}), ...] из плоского пресета или store-JSON."""
    obj = json.loads(io.open(path, encoding="utf-8-sig").read())
    if isinstance(obj, dict) and "entries" in obj:
        return [(e.get("spec_id") or e.get("id") or f"#{i}", e["params"])
                for i, e in enumerate(obj["entries"])]
    return [(Path(path).stem, obj)]


def real_base(norm):
    """role.base-кандидат: идентичность в реальных единицах, аккуратно округлённая."""
    out = {}
    for k in BASE_KEYS:
        if k not in norm:
            continue
        r = pc.norm_to_real(k, norm[k])
        if k in ("amp_attack", "amp_decay", "amp_release"):
            out[k] = round(r, 3)
        elif k in ("osc2_semitones", "osc1_octave"):
            out[k] = int(r)
        else:
            out[k] = round(r, 1) if isinstance(r, float) else r
    return out


def print_patch(label, norm, role=None, want_base=False):
    head = f"── {label}" + (f"   [{role}]" if role else "")
    print("\n" + head)
    for gname, keys in GROUPS:
        cells = []
        for k in keys:
            if k not in norm:
                continue
            r = pc.norm_to_real(k, norm[k])
            cells.append(f"{k}={pc.format_real(k, r)}")
        if cells:
            print(f"  {gname:<7} " + "  ".join(cells))
    if want_base:
        print("  base→ " + json.dumps(real_base(norm), ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="Инспектор патчей norm→real.")
    ap.add_argument("files", nargs="*", help="пресеты/store JSON")
    ap.add_argument("--golden", action="store_true", help="12 ручных эталонов из Patches/")
    ap.add_argument("--base", action="store_true", help="печатать role.base-кандидат")
    args = ap.parse_args()

    items = []  # (path, role)
    if args.golden:
        for fn, role in GOLDEN:
            items.append((PATCHES / fn, role))
    for f in args.files:
        items.append((Path(f), None))
    if not items:
        ap.error("укажи файлы или --golden")

    for path, role in items:
        if not path.exists():
            print(f"\n⚠ нет файла: {path}")
            continue
        for label, norm in load_norm_patches(path):
            print_patch(label, norm, role=role, want_base=args.base)


if __name__ == "__main__":
    main()
