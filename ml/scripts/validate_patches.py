#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_patches.py — валидация и экспорт патчей VerbalSynth (подход v2).

Делает:
  1. Кламп всех значений в [0,1].
  2. Снап дискретных параметров (osc_table / osc_octave / lfo_shape) к ближайшему
     значению из snap-набора param_reference.json.
  3. Проверки качества (флаги, не правки): анти-тишина, анти-клиппинг,
     противоречия (вибрато заявлено, но LFO→pitch=0 и т.п.).
  4. Экспорт каждого патча в плоский JSON {name: value} для загрузки синтезатором
     (формат PresetManager) → можно прослушать.
  5. (опц.) Разворачивание в dataset.jsonl: одна строка на описание,
     params как вектор из 38 чисел в порядке индексов.

Зависимостей нет (только stdlib).

Примеры:
  python validate_patches.py --in ml/data/test_batch/patches_test.json
  python validate_patches.py --in ml/data/patches_raw.json --jsonl ml/data/dataset.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

ROOT      = Path(__file__).resolve().parents[1]
CONFIG    = ROOT / "config"
DATA      = ROOT / "data"
PARAM_REF = CONFIG / "param_reference.json"


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def nearest(value, choices):
    return min(choices, key=lambda c: abs(c - value))


def build_param_meta(param_ref):
    """Возвращает (ordered_names, name->param, snap_sets)."""
    params = sorted(param_ref["params"], key=lambda p: p["i"])
    names = [p["name"] for p in params]
    by_name = {p["name"]: p for p in params}
    return names, by_name, param_ref["snap"]


def clamp_snap(patch_params, names, by_name, snap_sets):
    """Возвращает (clean_dict, changed_count). Чинит кламп+снап, заполняет пропуски 0.5."""
    clean = {}
    changed = 0
    for name in names:
        raw = patch_params.get(name, None)
        if raw is None:
            clean[name] = 0.5
            changed += 1
            continue
        try:
            v = float(raw)
        except (TypeError, ValueError):
            v = 0.5
            changed += 1
        cv = min(1.0, max(0.0, v))
        if cv != v:
            changed += 1
        meta = by_name[name]
        if meta.get("kind") == "discrete" and "snap" in meta:
            sv = nearest(cv, snap_sets[meta["snap"]])
            if abs(sv - cv) > 1e-9:
                changed += 1
            cv = sv
        clean[name] = round(cv, 6)
    return clean, changed


def quality_flags(p):
    """Список строк-предупреждений по правилам param_reference.validation_rules."""
    flags = []
    g = p.get
    mix_sum = g("mix_osc1", 0) + g("mix_osc2", 0) + g("mix_noise", 0)
    if mix_sum <= 0.2:
        flags.append(f"анти-тишина: сумма миксов {mix_sum:.2f} ≤ 0.2")
    if g("amp_sustain", 0) < 0.05 and g("amp_decay", 0) < 0.1 and g("amp_release", 0) < 0.1:
        flags.append("анти-тишина: очень короткая огибающая (sustain/decay/release малы)")
    if mix_sum > 1.7 and g("drive_amount", 0) > 0.6:
        flags.append(f"возможный клип: миксы {mix_sum:.2f} + drive {g('drive_amount',0):.2f}")
    return flags


def consistency_flags(entry, p):
    """Описания обещают движение/вибрато, но модуляция выключена."""
    flags = []
    text = " ".join(d.get("text", "") for d in entry.get("descriptions", [])).lower()
    vib = any(w in text for w in ("вибрато", "вибрир", "колышет", "колыш"))
    if vib and p.get("lfo1_to_pitch", 0) < 0.01 and p.get("lfo1_to_filter", 0) < 0.01 \
            and p.get("lfo2_to_wt", 0) < 0.01:
        flags.append("описание обещает вибрато/движение, но LFO-модуляция ≈0")
    return flags


def sanitize_filename(name: str) -> str:
    keep = "-_.() "
    s = "".join(c if (c.isalnum() or c in keep) else "_" for c in name)
    return s.strip().replace(" ", "_")[:60] or "patch"


def main():
    ap = argparse.ArgumentParser(description="Валидация/снап/экспорт патчей VerbalSynth.")
    ap.add_argument("--in", dest="infile", default=str(DATA / "test_batch" / "patches_test.json"),
                    help="входной patches_*.json")
    ap.add_argument("--out", dest="outfile", default=None,
                    help="куда записать ВАЛИДИРОВАННЫЕ патчи (деф. *_validated.json рядом)")
    ap.add_argument("--export-dir", default=None,
                    help="папка для плоских JSON под синтезатор (деф. <in_dir>/patches_export)")
    ap.add_argument("--prefix", default="[TEST]_", help="префикс имени файла экспорта (деф. '[TEST]_')")
    ap.add_argument("--no-export", action="store_true", help="не писать плоские JSON для синта")
    ap.add_argument("--jsonl", default=None, help="развернуть валидные патчи в dataset.jsonl по этому пути")
    ap.add_argument("--strict", action="store_true",
                    help="исключать флагнутые патчи из экспорта/jsonl")
    args = ap.parse_args()

    in_path = Path(args.infile)
    if not in_path.exists():
        sys.exit(f"Файл не найден: {in_path}")
    param_ref = load_json(PARAM_REF)
    names, by_name, snap_sets = build_param_meta(param_ref)

    store = load_json(in_path)
    entries = store.get("entries", [])
    if not entries:
        sys.exit("В файле нет entries.")

    out_path = Path(args.outfile) if args.outfile else in_path.with_name(in_path.stem + "_validated.json")
    export_dir = Path(args.export_dir) if args.export_dir else in_path.parent / "patches_export"
    if not args.no_export:
        export_dir.mkdir(parents=True, exist_ok=True)

    total_changed = 0
    flagged = []
    validated_entries = []
    jsonl_rows = []

    for entry in entries:
        clean, changed = clamp_snap(entry.get("params", {}), names, by_name, snap_sets)
        total_changed += changed
        flags = quality_flags(clean) + consistency_flags(entry, clean)

        v_entry = dict(entry)
        v_entry["params"] = clean
        v_entry["flags"] = flags
        validated_entries.append(v_entry)

        if flags:
            flagged.append((entry.get("id", "?"), entry.get("concept", ""), flags))

        skip = args.strict and flags
        if skip:
            continue

        # экспорт плоского JSON под синтезатор
        if not args.no_export:
            concept = sanitize_filename(entry.get("concept") or entry.get("id", "patch"))
            fname = f"{args.prefix}{concept}.json"
            with open(export_dir / fname, "w", encoding="utf-8") as f:
                json.dump(clean, f, ensure_ascii=False, indent=2)

        # строки датасета
        if args.jsonl:
            vec = [clean[n] for n in names]
            for d in entry.get("descriptions", []):
                text = (d.get("text") or "").strip()
                if not text:
                    continue
                jsonl_rows.append({
                    "id": f"{entry.get('id','?')}_ru_{d.get('style','')}",
                    "source_patch": entry.get("id", "?"),
                    "category": entry.get("category", ""),
                    "desc_style": d.get("style", ""),
                    "lang": "ru",
                    "text": text,
                    "params": vec,
                })

    # запись валидированных
    out_store = {"version": store.get("version", "2.0"),
                 "count": len(validated_entries), "entries": validated_entries}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_store, f, ensure_ascii=False, indent=2)

    if args.jsonl:
        jp = Path(args.jsonl)
        jp.parent.mkdir(parents=True, exist_ok=True)
        with open(jp, "w", encoding="utf-8") as f:
            for row in jsonl_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # отчёт
    print("=" * 70)
    print(f"Патчей обработано: {len(entries)}")
    print(f"Исправлено значений (кламп/снап/пропуски): {total_changed}")
    print(f"С предупреждениями: {len(flagged)}")
    for pid, concept, fl in flagged:
        print(f"  ⚠ {pid} ({concept}):")
        for x in fl:
            print(f"      - {x}")
    print(f"\nВалидированные патчи → {out_path}")
    if not args.no_export:
        n_exp = len(list(export_dir.glob(f"{args.prefix}*.json")))
        print(f"Плоские JSON для синта ({n_exp}) → {export_dir}")
        print("  Для прослушивания скопируйте их в папку 'Patches' рядом с .exe синтезатора.")
    if args.jsonl:
        print(f"dataset.jsonl ({len(jsonl_rows)} строк) → {args.jsonl}")
    if args.strict and flagged:
        print("\n(--strict: флагнутые патчи исключены из экспорта/jsonl)")
    print("=" * 70)


if __name__ == "__main__":
    main()
