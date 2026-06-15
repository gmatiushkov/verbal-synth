#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_coverage.py — валидатор + отчёт покрытия для Шага 1a (DATASET_v5_PLAN.md §7).

Сверяет config/v5/taxonomy_to_role.json с:
  • config/sound_taxonomy.json  — все ли ~139 целей покрыты (без пропусков/опечаток/лишних);
  • config/v4/roles.json        — существует ли каждая указанная роль (или она в new_roles_proposed);
  • config/v4/attributes.json   — валидны ли имена осей и уровни в axis_preset;
  • build/.../Release/Patches/  — существуют ли указанные reference-файлы (предупреждение).

Печатает сводку в консоль и пишет человекочитаемый отчёт config/v5/COVERAGE_AUDIT.md
(источник истины — JSON; .md генерируется из него). Код возврата ≠0 при проблемах валидации.

Запуск:  python ml/scripts/audit_coverage.py
"""

import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# консоль Windows по умолчанию cp1251 — принудительно utf-8, чтобы кириллица/эмодзи не падали
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]                 # .../ml
REPO = ROOT.parent
MAP_PATH = ROOT / "config" / "v5" / "taxonomy_to_role.json"
TAX_PATH = ROOT / "config" / "sound_taxonomy.json"
ROLES_PATH = ROOT / "config" / "v4" / "roles.json"
ATTRS_PATH = ROOT / "config" / "v4" / "attributes.json"
PATCHES_DIR = REPO / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"
REPORT_PATH = ROOT / "config" / "v5" / "COVERAGE_AUDIT.md"


def _load(path):
    with io.open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def validate(mp, tax, roles, attrs):
    """Возвращает (issues, warnings). issues != [] → провал валидации."""
    issues, warnings = [], []

    existing_roles = set(roles["roles"].keys())
    new_roles = set(mp.get("new_roles_proposed", {}).keys())
    all_roles = existing_roles | new_roles
    axes = attrs["axes"]

    # цели таксономии vs цели маппинга
    tax_targets = set()
    for cat in tax["categories"]:
        tax_targets.update(cat["targets"])
    mapped = []
    for cat_id, entries in mp["mapping"].items():
        for e in entries:
            mapped.append(e["target"])
    mapped_set = set(mapped)

    for t in sorted(tax_targets - mapped_set):
        issues.append(f"цель таксономии НЕ покрыта маппингом: «{t}»")
    for t in sorted(mapped_set - tax_targets):
        issues.append(f"цель маппинга ОТСУТСТВУЕТ в таксономии (опечатка?): «{t}»")
    dup = [t for t, c in Counter(mapped).items() if c > 1]
    for t in sorted(dup):
        issues.append(f"цель встречается в маппинге дважды: «{t}»")

    # категории маппинга vs категории таксономии
    tax_cats = {c["id"] for c in tax["categories"]}
    for cat_id in mp["mapping"]:
        if cat_id not in tax_cats:
            issues.append(f"категория маппинга «{cat_id}» отсутствует в таксономии")

    # роли, оси, уровни, флаг new_role, reference-файлы
    patch_names = set()
    if PATCHES_DIR.exists():
        patch_names = {p.name for p in PATCHES_DIR.glob("*.json")}
    else:
        warnings.append(f"папка Patches не найдена ({PATCHES_DIR}) — проверка reference пропущена")

    for cat_id, entries in mp["mapping"].items():
        for e in entries:
            tgt = e["target"]
            role = e.get("role")
            if role not in all_roles:
                issues.append(f"[{tgt}] неизвестная роль «{role}» (нет ни в roles.json, ни в new_roles_proposed)")
            is_new = role in new_roles
            if bool(e.get("new_role")) != is_new:
                issues.append(f"[{tgt}] флаг new_role={e.get('new_role')} не совпадает с фактом (роль «{role}» {'новая' if is_new else 'существующая'})")
            for ax, lvl in e.get("axis_preset", {}).items():
                if ax not in axes:
                    issues.append(f"[{tgt}] неизвестная ось «{ax}» в axis_preset")
                elif lvl not in axes[ax]["levels"]:
                    issues.append(f"[{tgt}] неизвестный уровень «{ax}.{lvl}»")
            ref = e.get("reference", "none")
            if ref and ref != "none" and patch_names and ref not in patch_names:
                warnings.append(f"[{tgt}] reference «{ref}» не найден в Patches/")

    # все новые роли использованы?
    used_new = {e["role"] for entries in mp["mapping"].values() for e in entries if e["role"] in new_roles}
    for r in sorted(new_roles - used_new):
        warnings.append(f"предложенная новая роль «{r}» не используется ни одной целью")

    return issues, warnings


def build_report(mp, tax, roles):
    """Собирает текст markdown-отчёта."""
    existing_roles = set(roles["roles"].keys())
    new_roles = mp.get("new_roles_proposed", {})

    entries_all = [(cat_id, e) for cat_id, entries in mp["mapping"].items() for e in entries]
    total = len(entries_all)

    # доли категорий: маппинг vs план таксономии
    cat_counts = Counter(cat_id for cat_id, _ in entries_all)
    tax_share = {c["id"]: c.get("share") for c in tax["categories"]}

    # цели на роль
    role_targets = defaultdict(list)
    for cat_id, e in entries_all:
        role_targets[e["role"]].append(e["target"])

    # реф-дыры
    gaps = [(cat_id, e) for cat_id, e in entries_all if e.get("reference", "none") in (None, "none", "")]
    have_ref = total - len(gaps)

    L = []
    L.append("# Шаг 1a — Аудит покрытия (таксономия × роли)\n")
    L.append("> Сгенерировано `ml/scripts/audit_coverage.py` из `config/v5/taxonomy_to_role.json`.")
    L.append("> Источник истины — JSON; этот файл перегенерируется. См. `DATASET_v5_PLAN.md` §7 Шаг 1a.\n")

    L.append("## Сводка\n")
    L.append(f"- Целей покрыто: **{total}** (все цели `sound_taxonomy.json`).")
    L.append(f"- Ролей задействовано: **{len(role_targets)}** "
             f"(существующих {len([r for r in role_targets if r in existing_roles])}, "
             f"новых {len([r for r in role_targets if r in new_roles])}).")
    L.append(f"- Целей с готовым эталоном/кандидатом: **{have_ref}**; без референса (ТЗ на догенерацию): **{len(gaps)}**.\n")

    L.append("### Доли категорий: маппинг vs план таксономии\n")
    L.append("| Категория | Целей в маппинге | Доля факт. | Доля план |")
    L.append("|---|---|---|---|")
    for c in tax["categories"]:
        cid = c["id"]
        cnt = cat_counts.get(cid, 0)
        L.append(f"| {cid} | {cnt} | {cnt/total:.0%} | {tax_share.get(cid, '—')} |")
    L.append("")

    L.append("## Новые роли к заведению (ТЗ для roles.json)\n")
    L.append("| Роль | Банк | Целей покрывает | Эталон/калибровка | Обоснование |")
    L.append("|---|---|---|---|---|")
    for rn, r in new_roles.items():
        cnt = len(role_targets.get(rn, []))
        refs = ", ".join(r.get("reference", [])) or "—"
        L.append(f"| `{rn}` | {r.get('bank','?')} | {cnt} | {refs} | {r.get('rationale','')} |")
    L.append("")

    L.append("## Цели на роль (параметрический архетип → инструменты)\n")
    for rn in sorted(role_targets, key=lambda r: (-len(role_targets[r]), r)):
        tag = "🆕" if rn in new_roles else "  "
        tgts = role_targets[rn]
        L.append(f"- {tag} **`{rn}`** ({len(tgts)}): " + "; ".join(tgts))
    L.append("")

    L.append("## ТЗ на реф-патчи: цели без референса (для Шага 2)\n")
    L.append("Сгруппировано по роли. Эти цели нужно догенерить Claude'ом и утвердить вручную "
             "(либо подобрать из существующих [TEST]/[DIV]/[DS]/[VAL]).\n")
    gap_by_role = defaultdict(list)
    for cat_id, e in gaps:
        gap_by_role[e["role"]].append(e["target"])
    for rn in sorted(gap_by_role, key=lambda r: (-len(gap_by_role[r]), r)):
        L.append(f"- **`{rn}`** ({len(gap_by_role[rn])}): " + "; ".join(gap_by_role[rn]))
    L.append("")

    L.append("## Полная таблица маппинга\n")
    L.append("| Категория | Цель | Роль | 🆕 | Пресет осей | Референс |")
    L.append("|---|---|---|---|---|---|")
    for cat_id, e in entries_all:
        new_flag = "🆕" if e["role"] in new_roles else ""
        preset = ", ".join(f"{k}={v}" for k, v in e.get("axis_preset", {}).items())
        ref = e.get("reference", "none")
        L.append(f"| {cat_id} | {e['target']} | `{e['role']}` | {new_flag} | {preset} | {ref} |")
    L.append("")

    return "\n".join(L)


def main():
    mp = _load(MAP_PATH)
    tax = _load(TAX_PATH)
    roles = _load(ROLES_PATH)
    attrs = _load(ATTRS_PATH)

    issues, warnings = validate(mp, tax, roles, attrs)

    total = sum(len(v) for v in mp["mapping"].values())
    print(f"Целей в маппинге: {total}")
    if warnings:
        print(f"\nПРЕДУПРЕЖДЕНИЯ ({len(warnings)}):")
        for w in warnings:
            print("  ⚠", w)
    if issues:
        print(f"\nПРОБЛЕМЫ ВАЛИДАЦИИ ({len(issues)}):")
        for s in issues:
            print("  ✗", s)
        print("\nОтчёт НЕ записан — сначала почини проблемы.")
        sys.exit(1)

    report = build_report(mp, tax, roles)
    with io.open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ Валидация чистая. Отчёт → {REPORT_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
