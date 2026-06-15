#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v5_sampler.py — ТАКСОНОМИЧЕСКИЙ сэмплер спек для датасета v5 (DATASET_v5_PLAN.md §4/§7 Шаг 4).

Отличие от v4_sampler (тот раскладывал уровни осей по РОЛЯМ round-robin): здесь сэмплер идёт
по ЦЕЛЯМ таксономии (config/v5/taxonomy_to_role.json, 140 целей, доли категорий) — широта живёт
на уровне целей. Для каждой цели:
  • вариант 0 — КАНОНИЧНЫЙ пресет осей цели (axis_preset из карты) → узнаваемый эталонный экземпляр;
  • варианты 1..K-1 — то же, но меняем ОДНУ ось из role.vary_axes (кроме register — он часть
    идентичности цели) round-robin'ом → «разные прочтения той же цели» (параметрическое разнообразие).

Выход — список СПЕК (target, category, role, bank, axis_levels, descriptors, variant). Параметры
из них делает param_rules.generate (детерминированно, без LLM); описания — отдельный дешёвый этап.

Распределение объёма:
  --per-target K   каждая цель = K вариантов (ровное покрытие; total = 140*K)
  --total N        N патчей, разнесены по категориям по доле share (sound_taxonomy), затем ровно
                   по целям категории (каждая цель ≥1)

Запуск:  python ml/scripts/v5_sampler.py --per-target 4 --report
         python ml/scripts/v5_sampler.py --total 600 --out ml/data/v5/specs.json
"""

import argparse
import io
import json
import random
import sys
from collections import Counter
from pathlib import Path

import v4_specs
from v4_specs import load_specs

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]                 # .../ml
MAP_PATH = ROOT / "config" / "v5" / "taxonomy_to_role.json"
TAXONOMY = ROOT / "config" / "sound_taxonomy.json"

# Ось register — часть идентичности цели (контрабас=sub, глокеншпиль=very_high): её НЕ варьируем
# внутри цели, разброс регистров обеспечивают РАЗНЫЕ цели. Варьируем остальные vary_axes.
IDENTITY_AXES = {"register"}


def _load(p):
    return json.loads(io.open(p, encoding="utf-8-sig").read())


def flat_entries(mp):
    """[(cat_id, entry), ...] по всей карте (порядок категорий сохранён)."""
    out = []
    for cat_id, entries in mp["mapping"].items():
        for e in entries:
            out.append((cat_id, e))
    return out


def _variant_axes(entry, role, attrs, variant, rng):
    """axis_levels для конкретного варианта цели. variant 0 = канон; >0 — сдвиг одной vary-оси."""
    base = dict(entry.get("axis_preset", {}))
    if variant == 0:
        return base
    vary = [ax for ax in role.get("vary_axes", []) if ax not in IDENTITY_AXES]
    if not vary:
        return base
    order = vary[:]
    rng.shuffle(order)                                     # воспроизводимо по rng цели
    out = dict(base)
    ax = order[(variant - 1) % len(order)]
    levels = role.get("typical", {}).get(ax) or list(attrs["axes"][ax]["levels"].keys())
    cur = base.get(ax)
    choices = [lv for lv in levels if lv != cur] or levels  # форсим отличие от канона
    out[ax] = choices[((variant - 1) // len(order)) % len(choices)]
    if variant % 3 == 0:                                   # на каждом 3-м — окраска характера
        chars = [c for c in attrs["axes"]["character"]["levels"] if c != "neutral"]
        if chars:
            out["character"] = rng.choice(chars)           # из rng цели → разные цели ≠ один характер
    return out


def _bank_for(entry, role, roles):
    """Банк: оверрайд из карты (напр. Metallic для вибрафона) либо основной банк роли."""
    return entry.get("bank") or roles[role]["banks"][0]


def make_specs_for_target(cat_id, entry, roles, attrs, k, seed):
    """k спек одной цели (variant 0..k-1)."""
    role = entry["role"]
    if role not in roles:
        raise SystemExit(f"цель «{entry['target']}» → неизвестная роль {role}")
    rdef = roles[role]
    bank = _bank_for(entry, role, roles)
    rng = random.Random(seed ^ (hash(entry["target"]) & 0xFFFFFFFF))
    specs = []
    for v in range(k):
        specs.append({
            "spec_id": f"{cat_id}|{entry['target']}|{v}",
            "target": entry["target"],
            "category": cat_id,
            "role": role,
            "bank": bank,
            "axis_levels": _variant_axes(entry, rdef, attrs, v, rng),
            "descriptors": list(entry.get("descriptors", [])),
            "reference": entry.get("reference", "none"),
            "variant": v,
            "is_canonical": v == 0,
        })
    return specs


def sample(roles, attrs, mp, taxonomy, per_target=None, total=None, only_cats=None, seed=42):
    """Список спек по всей карте. per_target ИЛИ total (per_target приоритетнее, если задан)."""
    entries = flat_entries(mp)
    if only_cats:
        entries = [(c, e) for c, e in entries if c in only_cats]

    # сколько вариантов на каждую цель
    counts = {}
    if per_target is not None:
        for c, e in entries:
            counts[(c, e["target"])] = per_target
    else:
        shares = {cat["id"]: cat.get("share", 0) for cat in taxonomy["categories"]}
        by_cat = {}
        for c, e in entries:
            by_cat.setdefault(c, []).append(e)
        for c, elist in by_cat.items():
            n_cat = max(len(elist), round(total * shares.get(c, 0)))   # каждая цель ≥1
            alloc = _distribute(n_cat, len(elist))
            for e, a in zip(elist, alloc):
                counts[(c, e["target"])] = max(1, a)

    out = []
    for c, e in entries:
        k = counts.get((c, e["target"]), 0)
        if k > 0:
            out.extend(make_specs_for_target(c, e, roles, attrs, k, seed))
    return out


def _distribute(count, k):
    """count РАВНОМЕРНО на k целей; первые (count % k) получают +1 (как в generate_dataset)."""
    if k <= 0:
        return []
    base, rem = divmod(count, k)
    return [base + (1 if i < rem else 0) for i in range(k)]


def coverage_report(specs):
    cat_c, role_c, bank_c, tgt_c = Counter(), Counter(), Counter(), Counter()
    by_axis = {}
    for s in specs:
        cat_c[s["category"]] += 1
        role_c[s["role"]] += 1
        bank_c[s["bank"]] += 1
        tgt_c[s["target"]] += 1
        for ax, lv in s["axis_levels"].items():
            by_axis.setdefault(ax, Counter())[lv] += 1
    print(f"Всего спек: {len(specs)} | целей: {len(tgt_c)} | ролей: {len(role_c)}")
    print(f"  категории: {dict(cat_c)}")
    print(f"  банки:     {dict(bank_c)}")
    print(f"  ролей задействовано: {len(role_c)}/{len(role_c)}  (вар./цель: "
          f"min={min(tgt_c.values())}, max={max(tgt_c.values())})")
    for ax in sorted(by_axis):
        c = by_axis[ax]
        items = ", ".join(f"{k}:{v}" for k, v in sorted(c.items(), key=lambda x: -x[1]))
        print(f"  {ax:<14} ({len(c)} ур.) {items}")


def main():
    ap = argparse.ArgumentParser(description="Таксономический сэмплер спек датасета v5.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--per-target", type=int, help="вариантов на цель (ровное покрытие)")
    g.add_argument("--total", type=int, help="всего патчей, разнос по долям категорий")
    ap.add_argument("--cats", nargs="*", help="только эти категории")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None, help="сохранить спеки в JSON")
    ap.add_argument("--report", action="store_true", help="печать покрытия")
    args = ap.parse_args()

    if args.per_target is None and args.total is None:
        args.per_target = 4

    roles, attrs, _ = load_specs()
    mp = _load(MAP_PATH)
    taxonomy = _load(TAXONOMY)
    specs = sample(roles, attrs, mp, taxonomy, per_target=args.per_target,
                   total=args.total, only_cats=args.cats, seed=args.seed)
    coverage_report(specs)
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        with io.open(p, "w", encoding="utf-8") as f:
            json.dump({"version": "5.0", "per_target": args.per_target, "total": args.total,
                       "seed": args.seed, "count": len(specs), "specs": specs}, f,
                      ensure_ascii=False, indent=2)
        print(f"\nСохранено {len(specs)} спек -> {p}")


if __name__ == "__main__":
    main()
