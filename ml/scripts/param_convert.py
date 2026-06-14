#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
param_convert.py — конвертация параметров VerbalSynth между РЕАЛЬНЫМИ физическими
единицами (мс, Гц, центы, полутоны, Q, %, имена банков) и нормализованными [0..1].

ЕДИНСТВЕННАЯ ИСТИНА — C++ движок. Каждая формула ниже скопирована из исходников
со ссылкой на файл:строку. Если движок меняется — синхронизировать здесь и прогнать
round-trip самотест (`python param_convert.py`).

Зачем (подход v3): Claude проектирует звук в реальных единицах (ему так естественно),
а этот модуль ДЕТЕРМИНИРОВАННО переводит их в [0..1] — теми же формулами, что синтезатор
использует обратно. Нормализованные значения идут в синтезатор и в обучающий вектор.

Источники формул:
  - Source/SynthUtils.h:9         logParam(norm,min,max) = min*(max/min)^norm   (лог-кривая)
  - Source/SynthUtils.h:19-22     octaveShift = round(norm*4)-2                 (-2..+2)
  - Source/SynthUtils.h:25-28     detuneInCents = (norm-0.5)*100                (±50 ц)
  - Source/AdsrEnvelope.cpp:16-19 attack logTime(0.0005,5), decay (0.001,5), release (0.005,10)
  - Source/SynthVoice.cpp:56      semis = round((osc2_semitones-0.5)*48)        (±24)
  - Source/SynthVoice.cpp:57      detCents = (osc2_detune-0.5)*100              (±50 ц)
  - Source/SynthVoice.cpp:124-125 lp/hp cutoff = logParam(norm,20,18000)        (Гц)
  - Source/SynthVoice.cpp:128     fenvAmt = (fenv_amount-0.5)*2                 (-1..+1)
  - Source/SynthVoice.cpp:149     semiShift = lfoVal*lfo1_to_pitch*2            (до ±2 полутона)
  - Source/SynthVoice.cpp:176     lpCut *= 2^(lfoVal*lfo1_to_filter*2)          (до ±2 окт)
  - Source/SynthVoice.cpp:179     lpCut *= 2^(fenvVal*fenvAmt*4)               (до ±4 окт свип)
  - Source/SynthFilter.cpp:39,66  q = 0.5 + resonance*9.5                       (Q 0.5..10)
  - Source/LfoGenerator.cpp:14-20 формы: sine/triangle/saw/square (морф 0..1)
  - Banks (рантайм): build/.../Wavetables/*.wav → Basic,Organ,Acoustic,Vocal,Metallic,Digital
                     osc_table snap {0,.2,.4,.6,.8,1.0}; индекс = round(norm*(N-1))

Зависимостей нет (stdlib).
"""

import math

# ── Имена дискретных наборов (порядок = индекс в движке) ──────────────────────
# Рантайм грузит WAV из папки Wavetables, отсортированные по имени (префиксы "1 ".."6 ").
BANK_NAMES = ["Basic", "Organ", "Acoustic", "Vocal", "Metallic", "Digital"]
# osc_table snap-точки соответствуют этим банкам:
BANK_NORMS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

# LFO формы (LfoGenerator.cpp морфит между ними; snap-точки из param_reference)
LFO_SHAPE_NAMES = ["sine", "triangle", "saw", "square"]
LFO_SHAPE_NORMS = [0.0, 0.33, 0.67, 1.0]

# osc_octave: 5 ступеней (-2..+2), SynthUtils.h:19-22 round(norm*4)-2
OCTAVE_NORMS = [0.0, 0.25, 0.5, 0.75, 1.0]


# ── Базовые лог/лин преобразования (зеркало SynthUtils::logParam) ─────────────
def log_to_norm(real, mn, mx):
    """real → norm для логарифмической кривой real = mn*(mx/mn)^norm."""
    real = min(max(real, mn), mx)
    return math.log(real / mn) / math.log(mx / mn)


def norm_to_log(norm, mn, mx):
    """norm → real (лог). Зеркало SynthUtils.h:9."""
    norm = min(max(norm, 0.0), 1.0)
    return mn * (mx / mn) ** norm


def lin_to_norm(real, mn, mx):
    real = min(max(real, mn), mx)
    return (real - mn) / (mx - mn)


def norm_to_lin(norm, mn, mx):
    norm = min(max(norm, 0.0), 1.0)
    return mn + norm * (mx - mn)


def _nearest_index(value, choices):
    return min(range(len(choices)), key=lambda i: abs(choices[i] - value))


# ── Спека параметров в реальных единицах ──────────────────────────────────────
# Для каждого параметра: тип конвертации + аргументы.
# Типы:
#   "log"     : лог-кривая, args (real_min, real_max, unit)
#   "linpct"  : линейный 0..1 движка, показываем как % 0..100
#   "q"       : резонанс, real = 0.5 + norm*9.5  (Q 0.5..10)
#   "octave"  : дискретные октавы -2..+2
#   "detune"  : центы ±50, real = (norm-0.5)*100
#   "semis"   : полутоны ±24, real = round((norm-0.5)*48)
#   "fenvamt" : свип в октавах ±4, real = (norm-0.5)*2*4 = (norm-0.5)*8
#   "modsemi" : глубина → центы 0..200 (lfo*_to_pitch), real = norm*2*100 = norm*200
#   "modoct"  : глубина → октавы 0..2 (lfo1_to_filter), real = norm*2
#   "bank"    : имя банка (дискр.)
#   "lfoshape": имя формы (дискр.)
#   "morphpct": позиция wavetable 0..1, показываем как % 0..100
#
# unit — человекочитаемая единица (для промпта/валидатора/ревью).

PARAM_SPEC = {
    "osc1_table":      ("bank",     {"unit": "bank"}),
    "osc1_position":   ("morphpct", {"unit": "%"}),
    "osc1_octave":     ("octave",   {"unit": "oct"}),
    "osc2_table":      ("bank",     {"unit": "bank"}),
    "osc2_position":   ("morphpct", {"unit": "%"}),
    "osc2_detune":     ("detune",   {"unit": "cents"}),
    "osc2_semitones":  ("semis",    {"unit": "st"}),
    "mix_osc1":        ("linpct",   {"unit": "%"}),
    "mix_osc2":        ("linpct",   {"unit": "%"}),
    "mix_noise":       ("linpct",   {"unit": "%"}),
    "lp_cutoff":       ("log",      {"min": 20.0, "max": 18000.0, "unit": "Hz"}),
    "lp_resonance":    ("q",        {"unit": "Q"}),
    "hp_cutoff":       ("log",      {"min": 20.0, "max": 18000.0, "unit": "Hz"}),
    "hp_resonance":    ("q",        {"unit": "Q"}),
    "filter_keytrack": ("linpct",   {"unit": "%"}),
    "amp_attack":      ("log",      {"min": 0.0005, "max": 5.0, "unit": "s"}),
    "amp_decay":       ("log",      {"min": 0.001,  "max": 5.0, "unit": "s"}),
    "amp_sustain":     ("linpct",   {"unit": "%"}),
    "amp_release":     ("log",      {"min": 0.005,  "max": 10.0, "unit": "s"}),
    "fenv_attack":     ("log",      {"min": 0.0005, "max": 5.0, "unit": "s"}),
    "fenv_decay":      ("log",      {"min": 0.001,  "max": 5.0, "unit": "s"}),
    "fenv_sustain":    ("linpct",   {"unit": "%"}),
    "fenv_release":    ("log",      {"min": 0.005,  "max": 10.0, "unit": "s"}),
    "fenv_amount":     ("fenvamt",  {"unit": "oct"}),
    "fenv_to_wt":      ("linpct",   {"unit": "%"}),
    "lfo1_rate":       ("log",      {"min": 0.01, "max": 20.0, "unit": "Hz"}),
    "lfo1_shape":      ("lfoshape", {"unit": "shape"}),
    "lfo1_to_pitch":   ("modsemi",  {"unit": "cents"}),
    "lfo1_to_filter":  ("modoct",   {"unit": "oct"}),
    "lfo2_rate":       ("log",      {"min": 0.01, "max": 20.0, "unit": "Hz"}),
    "lfo2_shape":      ("lfoshape", {"unit": "shape"}),
    "lfo2_to_wt":      ("linpct",   {"unit": "%"}),
    "lfo2_to_amp":     ("linpct",   {"unit": "%"}),
    "drive_amount":    ("linpct",   {"unit": "%"}),
    "drive_tone":      ("linpct",   {"unit": "%"}),
    "reverb_time":     ("linpct",   {"unit": "%"}),
    "reverb_damp":     ("linpct",   {"unit": "%"}),
    "reverb_mix":      ("linpct",   {"unit": "%"}),
}

# Строгий порядок (= индексы выходного вектора, SynthParameters.h:75-87)
PARAM_ORDER = list(PARAM_SPEC.keys())


# ── norm → real ───────────────────────────────────────────────────────────────
def norm_to_real(name, norm):
    """Нормализованное [0..1] → реальное значение в единицах параметра."""
    kind, a = PARAM_SPEC[name]
    if kind == "log":
        return norm_to_log(norm, a["min"], a["max"])
    if kind == "linpct" or kind == "morphpct":
        return norm_to_lin(norm, 0.0, 1.0) * 100.0  # проценты
    if kind == "q":
        return 0.5 + min(max(norm, 0.0), 1.0) * 9.5
    if kind == "octave":
        return int(round(min(max(norm, 0.0), 1.0) * 4)) - 2
    if kind == "detune":
        return (min(max(norm, 0.0), 1.0) - 0.5) * 100.0
    if kind == "semis":
        return int(round((min(max(norm, 0.0), 1.0) - 0.5) * 48))
    if kind == "fenvamt":
        return (min(max(norm, 0.0), 1.0) - 0.5) * 8.0  # ±4 окт
    if kind == "modsemi":
        return min(max(norm, 0.0), 1.0) * 200.0  # центы 0..200
    if kind == "modoct":
        return min(max(norm, 0.0), 1.0) * 2.0   # октавы 0..2
    if kind == "bank":
        return BANK_NAMES[_nearest_index(norm, BANK_NORMS)]
    if kind == "lfoshape":
        return LFO_SHAPE_NAMES[_nearest_index(norm, LFO_SHAPE_NORMS)]
    raise ValueError(f"unknown kind {kind} for {name}")


# ── real → norm ───────────────────────────────────────────────────────────────
def real_to_norm(name, real):
    """Реальное значение в единицах параметра → нормализованное [0..1]."""
    kind, a = PARAM_SPEC[name]
    if kind == "log":
        return log_to_norm(float(real), a["min"], a["max"])
    if kind == "linpct" or kind == "morphpct":
        return min(max(float(real) / 100.0, 0.0), 1.0)
    if kind == "q":
        return min(max((float(real) - 0.5) / 9.5, 0.0), 1.0)
    if kind == "octave":
        oct_ = int(round(float(real)))
        oct_ = min(max(oct_, -2), 2)
        return (oct_ + 2) / 4.0
    if kind == "detune":
        return min(max(float(real) / 100.0 + 0.5, 0.0), 1.0)
    if kind == "semis":
        st = int(round(float(real)))
        st = min(max(st, -24), 24)
        return min(max(st / 48.0 + 0.5, 0.0), 1.0)
    if kind == "fenvamt":
        return min(max(float(real) / 8.0 + 0.5, 0.0), 1.0)
    if kind == "modsemi":
        return min(max(float(real) / 200.0, 0.0), 1.0)
    if kind == "modoct":
        return min(max(float(real) / 2.0, 0.0), 1.0)
    if kind == "bank":
        if isinstance(real, str):
            idx = _match_name(real, BANK_NAMES)
            return BANK_NORMS[idx]
        return BANK_NORMS[_nearest_index(float(real), BANK_NORMS)]
    if kind == "lfoshape":
        if isinstance(real, str):
            idx = _match_name(real, LFO_SHAPE_NAMES)
            return LFO_SHAPE_NORMS[idx]
        return LFO_SHAPE_NORMS[_nearest_index(float(real), LFO_SHAPE_NORMS)]
    raise ValueError(f"unknown kind {kind} for {name}")


def _match_name(value, names):
    """Имя банка/формы → индекс (без регистра, по подстроке для гибкости)."""
    v = str(value).strip().lower()
    lower = [n.lower() for n in names]
    if v in lower:
        return lower.index(v)
    for i, n in enumerate(lower):       # частичное совпадение (напр. "Basic (sine)")
        if n in v or v in n:
            return i
    raise ValueError(f"не распознано имя '{value}', допустимо: {names}")


# ── Конвертация целого патча ──────────────────────────────────────────────────
def patch_real_to_norm(real_params: dict):
    """{name: real} → {name: norm} (все 38 в строгом порядке). Пропуски → дефолт 0.5-эквивалент."""
    out = {}
    for name in PARAM_ORDER:
        if name in real_params and real_params[name] is not None:
            out[name] = round(real_to_norm(name, real_params[name]), 6)
        else:
            out[name] = 0.5  # нейтральный дефолт, валидатор пометит
    return out


def patch_norm_to_real(norm_params: dict):
    """{name: norm} → {name: real} (для ревью глазами / отчётов)."""
    return {name: norm_to_real(name, norm_params.get(name, 0.5)) for name in PARAM_ORDER}


def norm_vector(norm_params: dict):
    """{name: norm} → список из 38 чисел в строгом порядке (обучающий вектор)."""
    return [norm_params[name] for name in PARAM_ORDER]


def unit_of(name):
    return PARAM_SPEC[name][1]["unit"]


def format_real(name, real):
    """Человекочитаемое реальное значение с единицей (для промпта/ревью/флагов).
       Времена в секундах → мс если <1с; частоты в Гц; и т.д."""
    kind = PARAM_SPEC[name][0]
    unit = unit_of(name)
    if isinstance(real, str):
        return real  # имя банка/формы
    if kind == "log" and unit == "s":
        ms = real * 1000.0
        return f"{ms:.0f} мс" if ms < 1000 else f"{real:.2f} с"
    if unit == "Hz":
        return f"{real:.2f} Гц" if real < 100 else f"{real:.0f} Гц"
    if unit == "%":
        return f"{real:.0f}%"
    if unit == "Q":
        return f"Q{real:.1f}"
    if unit == "cents":
        return f"{real:+.0f} ц"
    if unit == "st":
        return f"{int(real):+d} пт"
    if unit == "oct":
        return f"{real:+.1f} окт" if kind in ("fenvamt",) else f"{real:.1f} окт" if kind == "modoct" else f"{int(real):+d} окт"
    return f"{real:g} {unit}"


# ── Round-trip самотест ───────────────────────────────────────────────────────
def _self_test():
    import sys
    failures = []

    # 1. norm → real → norm на сетке для непрерывных; точные точки для дискретных.
    grid = [i / 20.0 for i in range(21)]  # 0.0..1.0 шаг 0.05
    discrete = {"osc1_table", "osc2_table", "lfo1_shape", "lfo2_shape",
                "osc1_octave", "osc2_semitones"}
    for name in PARAM_ORDER:
        kind = PARAM_SPEC[name][0]
        for n in grid:
            real = norm_to_real(name, n)
            back = real_to_norm(name, real)
            if name in discrete:
                # для дискретных проверяем, что повторная конвертация стабильна (идемпотентна)
                real2 = norm_to_real(name, back)
                if str(real) != str(real2):
                    failures.append(f"{name}: дискретная нестабильность n={n} {real}!={real2}")
            else:
                if abs(back - min(max(n, 0.0), 1.0)) > 1e-4:
                    failures.append(f"{name}: round-trip n={n:.3f} → real={real:.5g} → {back:.5f}")

    # 2. Контрольные точки против известных значений движка.
    checks = [
        ("lp_cutoff", 0.5, 600.0, 60.0),       # logParam(0.5,20,18000) ≈ 600 Гц
        ("lp_cutoff", 0.0, 20.0, 0.1),
        ("lp_cutoff", 1.0, 18000.0, 1.0),
        ("amp_attack", 0.0, 0.0005, 1e-6),     # 0.5 мс
        ("amp_attack", 1.0, 5.0, 1e-3),
        ("amp_decay", 1.0, 5.0, 1e-3),
        ("amp_release", 1.0, 10.0, 1e-3),
        ("lfo1_rate", 1.0, 20.0, 1e-2),
        ("lp_resonance", 0.0, 0.5, 1e-6),      # q = 0.5
        ("lp_resonance", 1.0, 10.0, 1e-6),     # q = 10
        ("osc2_detune", 0.5, 0.0, 1e-6),       # 0 центов
        ("osc2_detune", 0.0, -50.0, 1e-6),
        ("fenv_amount", 0.5, 0.0, 1e-6),       # нейтрально
        ("fenv_amount", 1.0, 4.0, 1e-6),       # +4 окт
        ("lfo1_to_pitch", 1.0, 200.0, 1e-6),   # ±200 ц при глубине 1
        ("lfo1_to_filter", 1.0, 2.0, 1e-6),    # ±2 окт
        ("mix_osc1", 1.0, 100.0, 1e-6),        # 100 %
        ("amp_sustain", 0.8, 80.0, 1e-6),
    ]
    for name, n, expect, tol in checks:
        got = norm_to_real(name, n)
        if abs(got - expect) > tol:
            failures.append(f"{name}: norm_to_real({n}) = {got:.6g}, ожидалось {expect} (±{tol})")

    # 3. Известные точки real → norm (обратное).
    rev = [
        ("lp_cutoff", 600.0, 0.5, 1e-3),
        ("amp_attack", 0.0005, 0.0, 1e-4),
        ("lp_resonance", 10.0, 1.0, 1e-6),
        ("osc2_semitones", 12, 0.75, 1e-6),    # +12 → 0.75
        ("osc2_semitones", -12, 0.25, 1e-6),
        ("osc1_octave", 0, 0.5, 1e-6),
        ("osc1_octave", -2, 0.0, 1e-6),
        ("osc1_octave", 2, 1.0, 1e-6),
        ("osc1_table", "Acoustic", 0.4, 1e-6),
        ("lfo1_shape", "sine", 0.0, 1e-6),
        ("lfo1_shape", "square", 1.0, 1e-6),
    ]
    for name, real, expect, tol in rev:
        got = real_to_norm(name, real)
        if abs(got - expect) > tol:
            failures.append(f"{name}: real_to_norm({real}) = {got:.6g}, ожидалось {expect} (±{tol})")

    print("=" * 64)
    if failures:
        print(f"❌ ПРОВАЛЕНО проверок: {len(failures)}")
        for f in failures:
            print("   -", f)
        sys.exit(1)
    print(f"✅ Round-trip + контрольные точки пройдены ({len(PARAM_ORDER)} параметров).")
    # Демонстрация на примере (как Claude увидит реальные значения)
    demo_norm = {"lp_cutoff": 0.5, "amp_attack": 0.6, "lfo1_rate": 0.82,
                 "lp_resonance": 0.8, "osc1_table": 0.4, "osc2_semitones": 0.75}
    print("\nПример norm → real:")
    for k, v in demo_norm.items():
        r = norm_to_real(k, v)
        u = PARAM_SPEC[k][1]["unit"]
        rs = f"{r:.4g}" if isinstance(r, float) else str(r)
        print(f"   {k:<16} {v} → {rs} {u}")
    print("=" * 64)


if __name__ == "__main__":
    _self_test()
