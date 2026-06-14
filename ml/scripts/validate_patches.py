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

import param_convert as pc  # конвертер реальные↔[0,1] (зеркало C++)

ROOT      = Path(__file__).resolve().parents[1]
CONFIG    = ROOT / "config"
DATA      = ROOT / "data"
PARAM_REF = CONFIG / "param_reference.json"


def load_json(path: Path):
    # utf-8-sig: терпим к BOM (его добавляет, напр., PowerShell Out-File -Encoding utf8)
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def clamp_snap_norm(patch_norm):
    """Норм. параметры → очищенные норм. (кламп [0,1] + снап дискретных) через param_convert.
       Возвращает (clean_norm, changed_count). Пропуски → 0.5."""
    clean = {}
    changed = 0
    for name in pc.PARAM_ORDER:
        raw = patch_norm.get(name, None)
        if raw is None:
            clean[name] = 0.5
            changed += 1
            continue
        try:
            v = float(raw)
        except (TypeError, ValueError):
            clean[name] = 0.5
            changed += 1
            continue
        # норм → реальное → норм: кламп и снап дискретных делает сам конвертер
        snapped = round(pc.real_to_norm(name, pc.norm_to_real(name, v)), 6)
        if abs(snapped - v) > 1e-6:
            changed += 1
        clean[name] = snapped
    return clean, changed


def real_of(norm_params):
    """{name: norm} → {name: real} для флагов в человекочитаемых единицах."""
    return {n: pc.norm_to_real(n, norm_params[n]) for n in pc.PARAM_ORDER}


def quality_flags(real):
    """Предупреждения по физике звука — в РЕАЛЬНЫХ единицах (мс, Гц, Q, %)."""
    flags = []
    g = real.get
    # уровни в процентах
    mix_sum = g("mix_osc1", 0) + g("mix_osc2", 0) + g("mix_noise", 0)
    if mix_sum <= 20:
        flags.append(f"анти-тишина: сумма уровней {mix_sum:.0f}% слишком мала")
    sus = g("amp_sustain", 0)            # %
    dec_ms = g("amp_decay", 0) * 1000.0  # с→мс
    rel_ms = g("amp_release", 0) * 1000.0
    atk_ms = g("amp_attack", 0) * 1000.0
    # «щелчок»: затухающий (sustain≈0), но и decay, и release очень коротки
    if sus < 10 and dec_ms < 120 and rel_ms < 120:
        flags.append(f"возможный 'щелчок': sustain {sus:.0f}% + decay {dec_ms:.0f}мс / release {rel_ms:.0f}мс — нота едва прозвучит")
    # неестественный «тянущийся щипок»: маленький ненулевой sustain у ударного профиля (резкая атака)
    if 3 < sus < 18 and atk_ms < 20:
        flags.append(f"sustain {sus:.0f}%: для щипкового/ударного звука обычно 0% (затухает) либо высокий")
    # резонансный фильтр-свип заявлен (резонанс + ненулевой fenv_amount), но fenv_decay = щелчок
    fenv_oct = abs(g("fenv_amount", 0))          # октавы свипа (0=нейтр)
    fdec_ms = g("fenv_decay", 0) * 1000.0
    if g("lp_resonance", 0) > 4 and fenv_oct > 1.0 and fdec_ms < 120:
        flags.append(f"фильтр-свип: резонанс Q{g('lp_resonance',0):.1f} + амплитуда {fenv_oct:.1f}окт, но fenv decay {fdec_ms:.0f}мс короткий — щелчок вместо свипа")
    # клиппинг: высокие уровни + сильный drive
    if mix_sum > 170 and g("drive_amount", 0) > 60:
        flags.append(f"возможный клип: уровни {mix_sum:.0f}% + drive {g('drive_amount',0):.0f}%")
    return flags


def consistency_flags(entry, real):
    """Описания обещают движение/вибрато/атаку, но реальные параметры не соответствуют."""
    flags = []
    text = " ".join(d.get("text", "") for d in entry.get("descriptions", [])).lower()
    vib = any(w in text for w in ("вибрато", "вибрир", "колышет", "колыш"))
    pitch_cents = real.get("lfo1_to_pitch", 0)   # центы
    rate_hz = real.get("lfo1_rate", 0)           # Гц
    if vib and pitch_cents < 2 and real.get("lfo1_to_filter", 0) < 0.05 and real.get("lfo2_to_wt", 0) < 1:
        flags.append("описание обещает вибрато/движение, но модуляция ≈0")
    # вибрато заявлено с ЗАМЕТНОЙ глубиной, но LFO медленный → 'плавающий строй', а не вибрато.
    # Малая глубина (<15ц) на медленном LFO = намеренный тонкий дрейф (дыхание дрона/пэда) — не флажим.
    if vib and pitch_cents >= 15 and rate_hz < 3:
        flags.append(f"вибрато: глубина {pitch_cents:.0f}ц при lfo1_rate {rate_hz:.2f}Гц — медленно: будет 'плавающий строй', а не вибрато (вибрато ~5-6 Гц)")
    # обещана плавная/нарастающая атака, но amp_attack почти мгновенный
    atk_ms = real.get("amp_attack", 0) * 1000.0
    soft_atk = any(w in text for w in (
        "мягкая атака", "плавная атака", "медленная атака", "мягкий вход", "плавно нараста",
        "медленно нараста", "плавный наплыв", "наплыв", "разгорает", "вплыва", "вырастает из тишины"))
    if soft_atk and atk_ms < 30:
        flags.append(f"описание обещает плавную/нарастающую атаку, но amp_attack {atk_ms:.0f}мс почти мгновенный")
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
        # Вход: норм. параметры в entry["params"] (формат v3 от generate_dataset).
        # Если их нет, но есть реальные (params_real) — конвертируем их.
        norm_in = entry.get("params")
        if not norm_in and entry.get("params_real"):
            norm_in = pc.patch_real_to_norm(entry["params_real"])
        clean, changed = clamp_snap_norm(norm_in or {})
        total_changed += changed
        real = real_of(clean)
        flags = quality_flags(real) + consistency_flags(entry, real)

        v_entry = dict(entry)
        v_entry["params"] = clean                 # очищенные норм. [0..1]
        v_entry["params_real"] = pc.patch_norm_to_real(clean)  # реальные (для ревью)
        v_entry["flags"] = flags
        validated_entries.append(v_entry)

        if flags:
            flagged.append((entry.get("id", "?"), entry.get("concept", ""), flags))

        skip = args.strict and flags
        if skip:
            continue

        # экспорт плоского JSON под синтезатор — НОРМАЛИЗОВАННЫЕ значения (формат PresetManager)
        if not args.no_export:
            concept = sanitize_filename(entry.get("concept") or entry.get("id", "patch"))
            fname = f"{args.prefix}{concept}.json"
            with open(export_dir / fname, "w", encoding="utf-8") as f:
                json.dump(clean, f, ensure_ascii=False, indent=2)

        # строки датасета — вектор 38 норм. в строгом порядке
        if args.jsonl:
            vec = pc.norm_vector(clean)
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
    out_store = {"version": store.get("version", "3.0"),
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
