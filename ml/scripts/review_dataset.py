#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_dataset.py — РЕВИЗИЯ датасета v5: выгрузить патчи в синт + свести описания к ним.

Зачем: проверить КАЧЕСТВО ДАННЫХ напрямую (а не через модель). Грузим патч в синте, слушаем,
и тут же читаем описания, которые к нему привязаны. Если params не звучат как описания —
проблема в детерм.генераторе (Шаг 3); если звучат, а модель мимо — проблема в обучении.

Читает ml/data/v5/dataset.jsonl (строка/описание) + manifest.json (axis_levels). Группирует
по source_patch (= spec_id) → пишет плоский пресет {name:norm} в Patches и строку в DATASET_REVIEW.md.

Запуск:
  python ml/scripts/review_dataset.py --clean                  # канон каждой цели (140 пресетов)
  python ml/scripts/review_dataset.py --category drums --clean # только барабаны
  python ml/scripts/review_dataset.py --role bell --all-variants
"""

import argparse
import io
import json
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

import param_convert as pc

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]                 # .../ml
REPO = ROOT.parent
DATASET = ROOT / "data" / "v5" / "dataset.jsonl"
MANIFEST = ROOT / "data" / "v5" / "manifest.json"
REVIEW_MD = ROOT / "data" / "v5" / "DATASET_REVIEW.md"
DEFAULT_OUT = REPO / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"
PREFIX = "[V5] "
_ILLEGAL = re.compile(r'[<>:"\\/|?*]')

# компактная сводка ключевых реальных параметров для корреляции звук↔params
KEY = ["osc1_table", "osc1_position", "osc1_octave", "mix_osc1", "osc2_table", "mix_osc2",
       "mix_noise", "lp_cutoff", "amp_attack", "amp_decay", "amp_sustain", "amp_release"]


def safe(s):
    return " ".join(_ILLEGAL.sub("-", s).split()).strip(" .")


def load_dataset():
    """source_patch -> {params(list38), target, role, category, variant, src, descs[]}."""
    patches = OrderedDict()
    with io.open(DATASET, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            sp = r["source_patch"]
            p = patches.get(sp)
            if p is None:
                p = {"params": r["params"], "target": r["target"], "role": r["role"],
                     "category": r["category"], "variant": r["variant"],
                     "src": r.get("params_src", "?"), "descs": []}
                patches[sp] = p
            p["descs"].append(r["text"])
    return patches


def load_axislevels():
    """(category|target|variant) -> axis_levels (из манифеста)."""
    idx = {}
    if MANIFEST.exists():
        m = json.loads(io.open(MANIFEST, encoding="utf-8").read())
        for s in m.get("specs", []):
            idx[f"{s['category']}|{s['target']}|{s['variant']}"] = s.get("axis_levels", {})
    return idx


def real_summary(params_list):
    d = dict(zip(pc.PARAM_ORDER, params_list))
    out = []
    for n in KEY:
        out.append(f"{n.split('_',1)[-1] if n.startswith('osc') else n}={pc.format_real(n, pc.norm_to_real(n, d[n]))}")
    return " · ".join(out)


def main():
    ap = argparse.ArgumentParser(description="Ревизия датасета v5: пресеты в синт + описания.")
    ap.add_argument("--out", default=None, help="папка Patches (деф. Release)")
    ap.add_argument("--category", help="только эта категория")
    ap.add_argument("--role", help="только эта роль")
    ap.add_argument("--all-variants", action="store_true", help="все варианты (деф. только канон v0)")
    ap.add_argument("--limit", type=int, default=None, help="не более N патчей")
    ap.add_argument("--clean", action="store_true", help="снести ранее выгруженные [V5] *")
    args = ap.parse_args()

    out = Path(args.out) if args.out else DEFAULT_OUT
    if not out.exists():
        raise SystemExit(f"Папка не найдена: {out}\nУкажи --out (где лежат заводские пресеты).")

    patches = load_dataset()
    axes = load_axislevels()

    sel = []
    for sp, p in patches.items():
        if not args.all_variants and p["variant"] != 0:
            continue
        if args.category and p["category"] != args.category:
            continue
        if args.role and p["role"] != args.role:
            continue
        sel.append((sp, p))
        if args.limit and len(sel) >= args.limit:
            break

    if args.clean:
        for f in out.glob(f"{PREFIX}*.json"):
            f.unlink()

    # порядок ревью: категория → цель → вариант
    sel.sort(key=lambda x: (x[1]["category"], x[1]["target"], x[1]["variant"]))

    written = 0
    by_cat = defaultdict(list)
    for sp, p in sel:
        vtag = "" if p["variant"] == 0 and not args.all_variants else f" v{p['variant']}"
        fname = f"{PREFIX}{safe(p['target'])}{vtag}"
        params = dict(zip(pc.PARAM_ORDER, p["params"]))
        with io.open(out / f"{fname}.json", "w", encoding="utf-8") as f:
            json.dump(params, f, ensure_ascii=False)
        by_cat[p["category"]].append((fname, sp, p))
        written += 1

    # ревью-документ
    lines = [f"# Ревизия датасета v5 — {written} патчей (из {len(patches)})",
             "",
             "Грузи пресет `" + PREFIX + "…` в синте, слушай — и сверяй с описаниями ниже. "
             "`src=anchor` — параметры из утверждённого тобой реф-якоря (ground-truth); "
             "`src=rules` — детерминированный генератор.",
             ""]
    for cat in ["acoustic_emulation", "synth_roles", "texture_atmos", "percussive_fx", "drums"]:
        items = by_cat.get(cat)
        if not items:
            continue
        lines.append(f"\n## {cat} ({len(items)})\n")
        for fname, sp, p in items:
            al = axes.get(sp, {})
            al_s = ", ".join(f"{k}:{v}" for k, v in al.items())
            lines.append(f"### {fname}")
            lines.append(f"- цель: **{p['target']}** · роль: `{p['role']}` · src: `{p['src']}`")
            if al_s:
                lines.append(f"- оси: {al_s}")
            lines.append(f"- параметры: {real_summary(p['params'])}")
            lines.append(f"- описания ({len(p['descs'])}): " + " · ".join(f"«{d}»" for d in p["descs"]))
            lines.append("")
    REVIEW_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Выгружено {written} пресетов «{PREFIX}…» → {out}")
    print(f"Ревью-документ: {REVIEW_MD}")
    print("В синте: открой менеджер пресетов, грузи [V5] …, слушай; описания читай в DATASET_REVIEW.md")


if __name__ == "__main__":
    main()
