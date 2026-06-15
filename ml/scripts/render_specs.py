#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_specs.py — ДЕТЕРМИНИРОВАННЫЙ рендер спек в патчи (прото-генератор для Шага 1b/2/3).

Берёт спеки (роль + банк + уровни осей) и БЕЗ участия LLM собирает патч:
neutral ⊕ role.base ⊕ якоря осей (через v4_specs.resolve_skeleton) → norm (param_convert) →
плоский пресет синта. Это «база + сэмплер-дисциплина» БЕЗ слоя музыкальных правил (Шаг 3):
относительной яркости/пола слышимости и конфликт-клампов здесь ещё НЕТ.

Дисциплина сэмплера (фикс №4 DATASET_v5_PLAN.md §4): оси, которых нет в role.vary_axes
(кроме register/character), ОТБРАСЫВАЮТСЯ — чтобы ось не ломала идентичность роли
(напр. body=long на piano). Что отброшено — печатается.

Источники спек:
  --taxonomy            всю карту config/v5/taxonomy_to_role.json (140 целей → кандидат-эталон).
                        Имя = «<префикс><тег-категории> <цель>», пишет чек-лист REFERENCE_AUDIT.md.
  --store <store.json>  берём role/bank/axis_levels из entries.
  --specs <sampler.json> берём data["specs"].

Выгрузка: плоский {param: norm} в папку Patches синта (по умолчанию Release).

Запуск (Шаг 2 — кандидат-эталоны по всей таксономии):
  python ml/scripts/render_specs.py --taxonomy --clean
Запуск (A/B тест-батча v4 с исправленными базами):
  python ml/scripts/render_specs.py --store ml/data/test_batch/v4/patches_v4_test.json --clean
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path

import param_convert as pc
import v4_specs

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DEFAULT_OUT = REPO / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"
MAP_PATH = ROOT / "config" / "v5" / "taxonomy_to_role.json"
AUDIT_DOC = ROOT / "config" / "v5" / "REFERENCE_AUDIT.md"

ALWAYS_OK = {"register", "character"}     # эти оси разрешены любой роли
WATCH = ["osc1_position", "osc2_position", "lp_cutoff", "amp_attack",
         "amp_sustain", "amp_release", "amp_decay"]   # что печатаем для сверки
CAT_TAG = {"acoustic_emulation": "ac", "synth_roles": "sy", "texture_atmos": "tx",
           "percussive_fx": "fx", "drums": "dr"}
_ILLEGAL = re.compile(r'[<>:"\\/|?*]')


def safe_name(s):
    """Имя цели → безопасное имя файла (Windows): убрать недопустимые символы, схлопнуть пробелы."""
    return " ".join(_ILLEGAL.sub("-", s).split()).strip(" .")


def load_specs(args, roles):
    if args.taxonomy:
        data = json.loads(io.open(MAP_PATH, encoding="utf-8-sig").read())
        specs = []
        for cat_id, entries in data["mapping"].items():
            tag = CAT_TAG.get(cat_id, "xx")
            for e in entries:
                role = e["role"]
                bank = e.get("bank") or roles[role]["banks"][0]
                specs.append({"spec_id": f"{tag} {safe_name(e['target'])}",
                              "role": role, "bank": bank,
                              "axis_levels": dict(e.get("axis_preset", {})),
                              "_cat": cat_id, "_target": e["target"],
                              "_reference": e.get("reference", "none")})
        return specs
    if args.store:
        store = json.loads(io.open(args.store, encoding="utf-8-sig").read())
        return [{"spec_id": e.get("spec_id") or e.get("id"),
                 "role": e["role"], "bank": e["bank"],
                 "axis_levels": dict(e.get("axis_levels", {}))} for e in store["entries"]]
    if args.specs:
        data = json.loads(io.open(args.specs, encoding="utf-8-sig").read())
        return data["specs"]
    raise SystemExit("укажи --taxonomy, --store или --specs")


def filter_axes(spec, role):
    """Отбросить оси вне role.vary_axes (кроме register/character). Вернуть (clean_levels, dropped)."""
    allowed = set(role.get("vary_axes", [])) | ALWAYS_OK
    clean, dropped = {}, {}
    for ax, lvl in spec.get("axis_levels", {}).items():
        if ax in allowed:
            clean[ax] = lvl
        else:
            dropped[ax] = lvl
    return clean, dropped


def write_audit_doc(records, path):
    """Чек-лист прослушки кандидат-эталонов (Шаг 2), сгруппированный по категории→роли."""
    by_cat = {}
    for r in records:
        by_cat.setdefault(r["_cat"], {}).setdefault(r["role"], []).append(r)

    L = []
    L.append("# Шаг 2 — Чек-лист прослушки кандидат-эталонов\n")
    L.append("> Сгенерировано `ml/scripts/render_specs.py --taxonomy`. Источник — `taxonomy_to_role.json`.")
    L.append("> Каждый патч `«<префикс>...»` выгружен в Patches. Прослушай, отметь вердикт:")
    L.append("> `[x]` — годен как эталон · `[~]` — почти, нужна правка базы/правил · `[ ]` — мимо (в Шаг 3).")
    L.append("> Колонка «эталон-кандидат» — заводской/golden патч на ту же цель: если он лучше — берём ЕГО.\n")
    L.append(f"- Всего целей: **{len(records)}**.")
    have_ref = sum(1 for r in records if r["_reference"] not in (None, "none", ""))
    L.append(f"- С заводским/golden эталоном для сверки: **{have_ref}**; чисто синтез-кандидат: **{len(records)-have_ref}**.\n")

    for cat_id in CAT_TAG:
        if cat_id not in by_cat:
            continue
        L.append(f"## {cat_id}\n")
        for role in sorted(by_cat[cat_id]):
            L.append(f"### `{role}`\n")
            L.append("| ✓ | Цель | Банк | Что слышно (real) | Дропнуто | Эталон-кандидат |")
            L.append("|---|---|---|---|---|---|")
            for r in by_cat[cat_id][role]:
                ref = r["_reference"] if r["_reference"] not in (None, "none", "") else "—"
                drop = ", ".join(f"{k}={v}" for k, v in r["dropped"].items()) or "—"
                L.append(f"| [ ] | {r['_target']} | {r['bank']} | {r['watch']} | {drop} | {ref} |")
            L.append("")
    with io.open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description="Детерминированный рендер спек → пресеты синта.")
    ap.add_argument("--taxonomy", action="store_true",
                    help="рендерить кандидат-эталон по всей карте taxonomy_to_role.json")
    ap.add_argument("--store", help="store JSON (берём role/bank/axis_levels из entries)")
    ap.add_argument("--specs", help="JSON сэмплера ({specs:[...]})")
    ap.add_argument("--out", default=None, help="папка Patches (деф. Release)")
    ap.add_argument("--prefix", default=None, help="префикс имени (деф. 'v5ref ' для --taxonomy, иначе 'v5b ')")
    ap.add_argument("--clean", action="store_true", help="снести ранее выгруженные с этим префиксом")
    ap.add_argument("--dry-run", action="store_true", help="не писать файлы, только печать")
    args = ap.parse_args()

    if args.prefix is None:
        args.prefix = "v5ref " if args.taxonomy else "v5b "

    roles, attrs, _ = v4_specs.load_specs()
    specs = load_specs(args, roles)

    out = Path(args.out) if args.out else DEFAULT_OUT
    if not args.dry_run:
        if not out.exists():
            raise SystemExit(f"Папка не найдена: {out} — укажи --out")
        if args.clean:
            for f in out.glob(f"{args.prefix}*.json"):
                f.unlink()

    written = 0
    records = []
    for spec in specs:
        role = roles[spec["role"]]
        clean, dropped = filter_axes(spec, role)
        spec2 = dict(spec, axis_levels=clean)
        real, locked, character, osc2_active = v4_specs.resolve_skeleton(spec2, roles, attrs)
        norm = pc.patch_real_to_norm(real)

        drop_s = (" | drop: " + ", ".join(f"{k}={v}" for k, v in dropped.items())) if dropped else ""
        watch_s = " ".join(f"{k.split('_', 1)[-1]}={pc.format_real(k, real[k])}"
                           for k in WATCH if k in real)
        print(f"  {spec['spec_id']:<34} {spec['role']}/{spec['bank']}  {watch_s}{drop_s}")

        if not args.dry_run:
            path = out / f"{args.prefix}{spec['spec_id']}.json"
            with io.open(path, "w", encoding="utf-8") as f:
                json.dump(norm, f, ensure_ascii=False)
            written += 1

        if args.taxonomy:
            records.append({"role": spec["role"], "bank": spec["bank"], "watch": watch_s,
                            "dropped": dropped, "_cat": spec["_cat"],
                            "_target": spec["_target"], "_reference": spec["_reference"]})

    if args.taxonomy and not args.dry_run:
        write_audit_doc(records, AUDIT_DOC)
        print(f"\nЧек-лист → {AUDIT_DOC.relative_to(REPO)}")
    if not args.dry_run:
        print(f"Выгружено {written} пресетов → {out}  (префикс «{args.prefix}»)")
    else:
        print(f"\n(dry-run) спек: {len(specs)}")


if __name__ == "__main__":
    main()
