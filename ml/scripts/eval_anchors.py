#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_anchors.py — EVAL-ПЕТЛЯ Шага 3 (DATASET_v5_PLAN.md §4.9).

Насколько детерминированный генератор (param_rules.generate) попадает в УТВЕРЖДЁННЫЕ
реф-якоря. Для каждого якоря из ml/data/reference/reference_anchors.json берём его вход
(роль, axis_preset, банк) из config/v5/taxonomy_to_role.json, генерим 38 параметров и
меряем расстояние до реальных параметров якоря (= «правильного ответа» от руки).

Это калибровочный сигнал: какие ПАРАМЕТРЫ и какие ЗВУКИ генератор врёт сильнее всего →
по нему правим role.base / param_bounds / правила (3a–3e) и смотрим, как падает ошибка.

Метрики:
  • непрерывные параметры — средняя |Δ| в norm-пространстве [0..1] (MAE);
  • дискретные (банк/октава/полутоны/форма LFO) — доля несовпадений (по реальным значениям).

Запуск:  python ml/scripts/eval_anchors.py            (mode baseline)
         python ml/scripts/eval_anchors.py --top 8   (сколько худших звуков печатать)
"""

import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import param_convert as pc
import param_rules
import v4_specs

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
REF_STORE = ROOT / "data" / "reference" / "reference_anchors.json"
MAP_PATH = ROOT / "config" / "v5" / "taxonomy_to_role.json"

DISCRETE = [n for n in pc.PARAM_ORDER if pc.PARAM_SPEC[n][0] in ("bank", "octave", "semis", "lfoshape")]
CONT = [n for n in pc.PARAM_ORDER if n not in DISCRETE]


# Зависимые под-параметры модулей: значимы, только если модуль ВКЛючён. Их роутеры
# (mix_osc2, fenv_amount/fenv_to_wt, lfo*_to_*, reverb_mix, drive_amount, hp_cutoff) сами
# скорятся ВСЕГДА — они и ловят «генератор не включил модуль, который есть у эталона».
DEP = {"osc2_table", "osc2_position", "osc2_detune", "osc2_semitones",
       "fenv_attack", "fenv_decay", "fenv_sustain", "fenv_release",
       "lfo1_rate", "lfo1_shape", "lfo2_rate", "lfo2_shape",
       "reverb_time", "reverb_damp", "drive_tone", "hp_resonance"}


def deps_on(p):
    """Какие зависимые под-параметры реально задействованы в патче (norm-словарь)."""
    def v(n):
        return float(p.get(n, 0.0))
    on = set()
    if v("mix_osc2") > 0.01:
        on |= {"osc2_table", "osc2_position", "osc2_detune", "osc2_semitones"}
    if abs(v("fenv_amount") - 0.5) > 0.02 or v("fenv_to_wt") > 0.02:
        on |= {"fenv_attack", "fenv_decay", "fenv_sustain", "fenv_release"}
    if abs(v("lfo1_to_pitch") - 0.5) > 0.02 or abs(v("lfo1_to_filter") - 0.5) > 0.02:
        on |= {"lfo1_rate", "lfo1_shape"}
    if v("lfo2_to_wt") > 0.02 or v("lfo2_to_amp") > 0.02:
        on |= {"lfo2_rate", "lfo2_shape"}
    if v("reverb_mix") > 0.02:
        on |= {"reverb_time", "reverb_damp"}
    if v("drive_amount") > 0.02:
        on |= {"drive_tone"}
    if v("hp_cutoff") > 0.03:
        on |= {"hp_resonance"}
    return on


def scored_params(gen, ref):
    """Роутеры/основные — всегда; зависимая деталь — только если модуль ВКЛ у обоих."""
    return (set(pc.PARAM_ORDER) - DEP) | (deps_on(gen) & deps_on(ref))


def _load(p):
    return json.loads(io.open(p, encoding="utf-8-sig").read())


def map_index(mp):
    """target → mapping-entry (роль, axis_preset, опц. bank)."""
    idx = {}
    for _cat, entries in mp["mapping"].items():
        for e in entries:
            idx[e["target"]] = e
    return idx


def real_equal(name, a, b):
    """Совпадение дискретного параметра по реальному значению."""
    ra, rb = pc.norm_to_real(name, a), pc.norm_to_real(name, b)
    if isinstance(ra, str) or isinstance(rb, str):
        return str(ra).strip().lower() == str(rb).strip().lower()
    return round(float(ra)) == round(float(rb))


def main():
    ap = argparse.ArgumentParser(description="Eval генератора против реф-якорей.")
    ap.add_argument("--mode", default="baseline", help="режим param_rules.generate")
    ap.add_argument("--top", type=int, default=10, help="сколько худших звуков печатать")
    ap.add_argument("--no-mask", action="store_true", help="не маскировать неактивные параметры (сырая метрика)")
    args = ap.parse_args()

    store = _load(REF_STORE)
    mp = _load(MAP_PATH)
    roles, attrs, _ = v4_specs.load_specs()
    idx = map_index(mp)

    anchors = [e for e in store["entries"] if e.get("approved") and isinstance(e.get("params"), dict)]
    if not anchors:
        raise SystemExit("Нет утверждённых якорей с params в reference_anchors.json")

    per_param_err = defaultdict(list)      # name → [|Δ| по якорям] (непрерывные, активные)
    disc_miss = defaultdict(int)           # name → число несовпадений (дискретные, активные)
    disc_active = 0                        # всего активных дискретных «ячеек» (знаменатель)
    rows = []                              # (anchor, cont_mae, worst[(name, gen, ref, |Δ|)])
    skipped = []
    act_counts = []

    for a in anchors:
        tgt = a.get("target")
        e = idx.get(tgt)
        if not e:
            skipped.append(tgt)
            continue
        role = e["role"]
        bank = e.get("bank") or roles[role]["banks"][0]
        spec = {"role": role, "bank": bank, "axis_levels": dict(e.get("axis_preset", {}))}
        gen = param_rules.generate(spec, roles, attrs, mode=args.mode)
        ref = a["params"]
        active = set(pc.PARAM_ORDER) if args.no_mask else scored_params(gen, ref)
        act_counts.append(len(active))

        diffs = []
        cont_abs = []
        for n in pc.PARAM_ORDER:
            if n not in active:
                continue
            g, r = float(gen.get(n, 0.0)), float(ref.get(n, 0.0))
            d = abs(g - r)
            if n in DISCRETE:
                disc_active += 1
                if not real_equal(n, g, r):
                    disc_miss[n] += 1
                    diffs.append((n, g, r, d, True))
            else:
                per_param_err[n].append(d)
                cont_abs.append(d)
                diffs.append((n, g, r, d, False))
        cont_mae = sum(cont_abs) / len(cont_abs) if cont_abs else 0.0
        worst = sorted(diffs, key=lambda x: x[3], reverse=True)[:3]
        rows.append((a, role, cont_mae, worst))

    n = len(rows)
    all_cont = [d for v in per_param_err.values() for d in v]
    overall = sum(all_cont) / len(all_cont) if all_cont else 0.0
    disc_total = sum(disc_miss.values())
    disc_cells = disc_active

    avg_act = sum(act_counts) / len(act_counts) if act_counts else 0
    print("=" * 78)
    print(f"EVAL генератора против реф-якорей · mode={args.mode} · якорей={n}"
          + ("" if args.no_mask else f" · маска вкл (активных ~{avg_act:.0f}/38)")
          + (f" · пропущено(нет в карте)={len(skipped)}" if skipped else ""))
    print(f"Непрерывные: MAE = {overall:.3f} (norm [0..1], ниже — лучше)")
    print(f"Дискретные (банк/окт/полутоны/форма): несовпадений {disc_total}/{disc_cells} "
          f"({100*disc_total/max(1,disc_cells):.0f}%)")
    print("=" * 78)

    print("\nХудшие ПАРАМЕТРЫ (средняя |Δ| norm по якорям, топ-12):")
    ranked = sorted(((sum(v)/len(v), k, len(v)) for k, v in per_param_err.items()), reverse=True)
    for mae, name, cnt in ranked[:12]:
        print(f"  {name:<16} {mae:.3f}")
    if disc_miss:
        print("  -- дискретные несовпадения:")
        for name, c in sorted(disc_miss.items(), key=lambda x: -x[1]):
            print(f"     {name:<16} {c}/{n}")

    print(f"\nХудшие ЗВУКИ (по непрерывному MAE, топ-{args.top}):")
    for a, role, mae, worst in sorted(rows, key=lambda x: x[2], reverse=True)[:args.top]:
        print(f"  {mae:.3f}  [{role}] {a.get('target')}")
        for name, g, r, d, is_disc in worst:
            gr, rr = pc.norm_to_real(name, g), pc.norm_to_real(name, r)
            print(f"        {name:<15} ген={pc.format_real(name, gr):<12} эталон={pc.format_real(name, rr):<12} Δ={d:.2f}")
    if skipped:
        print(f"\n⚠ нет в карте taxonomy_to_role: {skipped}")


if __name__ == "__main__":
    main()
