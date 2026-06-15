#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4_sampler.py — сэмплер спек для датасета v4 (бюджет покрытия).

Производит список СПЕК (роль + банк + уровни осей). КЛЮЧЕВАЯ ИДЕЯ (урок v3): потолок
дала не модель, а данные — механизм разнообразия РАЗМАЗАЛ определяющие параметры
(банк 63%, октава 48%). Здесь сэмплер ДЕТЕРМИНИРОВАННО раскладывает уровни каждой оси
round-robin'ом с фазовым сдвигом между осями → каждый перцептивно-определяющий уровень
(регистр/яркость/атака/…) получает ~равную долю патчей, а комбинации осей расходятся
(латинский-квадрат-подобный спред). Банк держим «каноничным»: основной банк роли —
большинство патчей, вторичные банки подмешиваются на ~1/3.

Уровни берём из role.typical[ось] если заданы (роле-уместные), иначе — все уровни оси.
register сэмплим из role.register_range (домен октав). character — на части патчей
(качественная окраска/настроение). Порядок уровней перетасован по seed (воспроизводимо).

Вывод: list спек + отчёт покрытия. Спеки потом резолвит v4_specs.resolve_skeleton.
"""

import argparse
import io
import json
import random
from collections import Counter
from pathlib import Path

from v4_specs import load_specs

ROOT = Path(__file__).resolve().parents[1]


def _levels_for(ax, role, attrs):
    """Роле-уместные уровни оси: typical[ax] если есть, иначе все уровни оси."""
    typ = role.get("typical", {}).get(ax)
    if typ:
        return list(typ)
    return list(attrs["axes"][ax]["levels"].keys())


def sample_role(role_name, role, attrs, n, rng):
    """n спек для одной роли через фазовый round-robin (покрытие уровней + спред комбо)."""
    banks = role["banks"]
    registers = list(role.get("register_range") or ["mid"])
    vary = [ax for ax in role.get("vary_axes", []) if ax != "register"]

    # перетасуем порядок уровней (воспроизводимо по rng) — чтобы фазы не были всегда выровнены
    reg_order = registers[:]
    rng.shuffle(reg_order)
    axis_levels_order = {}
    for ax in vary:
        lv = _levels_for(ax, role, attrs)
        rng.shuffle(lv)
        axis_levels_order[ax] = lv
    char_levels = [c for c in attrs["axes"]["character"]["levels"] if c != "neutral"]
    rng.shuffle(char_levels)

    specs = []
    for i in range(n):
        lv = {"register": reg_order[i % len(reg_order)]}
        # банк: основной — большинство; вторичные подмешиваем на каждый 3-й патч
        if len(banks) == 1:
            bank = banks[0]
        elif i % 3 == 2:
            sec = banks[1:]
            bank = sec[(i // 3) % len(sec)]
        else:
            bank = banks[0]
        # оси round-robin с фазой = индекс оси (декорреляция комбинаций)
        for ai, ax in enumerate(vary):
            order = axis_levels_order[ax]
            lv[ax] = order[(i + ai) % len(order)]
        # character на 2 из каждых 5 патчей
        if char_levels and i % 5 in (1, 3):
            lv["character"] = char_levels[(i // 5) % len(char_levels)]
        specs.append({
            "spec_id": f"{role_name}_{i:03d}",
            "role": role_name,
            "bank": bank,
            "axis_levels": lv,
        })
    return specs


def sample_all(roles, attrs, per_role=40, only_roles=None, seed=42):
    """Спеки по всем (или выбранным) ролям. per_role — патчей на роль."""
    rng = random.Random(seed)
    out = []
    names = only_roles or list(roles.keys())
    for rn in names:
        if rn not in roles:
            raise SystemExit(f"неизвестная роль: {rn}")
        # отдельный детерминированный поток на роль (стабильно при изменении набора ролей)
        rrng = random.Random(seed ^ (hash(rn) & 0xFFFFFFFF))
        out.extend(sample_role(rn, roles[rn], attrs, per_role, rrng))
    return out


def coverage_report(specs, roles, attrs):
    """Печатает покрытие уровней по осям и банкам — проверяем, что ничего не «голодает»."""
    by_axis = {}        # ось -> Counter(уровень)
    bank_c = Counter()
    role_c = Counter()
    for s in specs:
        role_c[s["role"]] += 1
        bank_c[s["bank"]] += 1
        for ax, level in s["axis_levels"].items():
            by_axis.setdefault(ax, Counter())[level] += 1
    print(f"Всего спек: {len(specs)} | ролей: {len(role_c)} | "
          f"банки: {dict(bank_c)}")
    for ax in sorted(by_axis):
        c = by_axis[ax]
        items = ", ".join(f"{k}:{v}" for k, v in sorted(c.items(), key=lambda x: -x[1]))
        print(f"  {ax:<14} ({len(c)} ур.) {items}")


def main():
    ap = argparse.ArgumentParser(description="Сэмплер спек датасета v4.")
    ap.add_argument("--per-role", type=int, default=40, help="патчей на роль (деф. 40)")
    ap.add_argument("--roles", nargs="*", help="только эти роли (деф. все)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None, help="сохранить спеки в JSON")
    ap.add_argument("--report", action="store_true", help="печать покрытия")
    args = ap.parse_args()

    roles, attrs, _ = load_specs()
    specs = sample_all(roles, attrs, per_role=args.per_role,
                       only_roles=args.roles, seed=args.seed)
    coverage_report(specs, roles, attrs)
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        with io.open(p, "w", encoding="utf-8") as f:
            json.dump({"version": "4.0", "per_role": args.per_role,
                       "seed": args.seed, "specs": specs}, f,
                      ensure_ascii=False, indent=2)
        print(f"\nСохранено {len(specs)} спек → {p}")


if __name__ == "__main__":
    main()
