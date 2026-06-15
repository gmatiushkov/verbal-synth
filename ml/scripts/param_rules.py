#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
param_rules.py — ДЕТЕРМИНИРОВАННЫЙ генератор параметров v5 (Шаг 3 DATASET_v5_PLAN.md).

generate(spec, roles, attrs) → {param: norm}  (все 38, без LLM)
  spec = {"role": str, "bank": str, "axis_levels": {ось: уровень}}

Послойная архитектура (каждый слой калибруется eval-петлёй eval_anchors.py против реф-якорей):
  v1 baseline   — = v4_specs.resolve_skeleton + дисциплина сэмплера (filter_axes). АБСОЛЮТНОЕ
                  применение осей (real.update). Это та точка, от которой меряем прогресс.
  [3a] далее    — относительное применение осей (param_bounds + кламп/бленд вместо перезаписи);
  [3b]          — пол слышимости + связанные правила (sustain/decay, бас→октава, резонанс↔motion);
  [3c]          — джиттер (seed) для вариативности датасета.

Флаг mode у generate() выбирает слой: "baseline" (сейчас) | "rules" (по мере готовности 3a+).
"""

import param_convert as pc
import v4_specs

ALWAYS_OK = {"register", "character"}     # эти оси разрешены любой роли (универсальны)

# Роли, чья ИДЕНТИЧНОСТЬ — затухание: sustain обязан быть ~0 (нота гаснет сама).
# Ось body даёт «длину» через decay/release, поэтому sustain из body.long/sustained/drone (75/80/100)
# здесь паразит и клобберит роль → клампим. Длинный хвост остаётся в release. (Фикс #1 из eval.)
DECAY_ROLES = {"kick", "snare_clap", "hihat", "tom", "cymbal", "gong", "bell", "mallet", "pluck", "acid_bass"}

# Per-role жёсткие границы в РЕАЛЬНЫХ единицах (кламп после применения осей). Растёт по мере калибровки.
PARAM_BOUNDS = {
    # role: { param: (min, max) }
}

# 3e КАЛИБРОВКА БАЗЫ от 28 утверждённых реф-якорей (ml/data/reference): значения СТРУКТУРНЫХ
# параметров, которые НЕ задаются осями выбранных пресетов (позиция/слой osc2/шум/банк-микс).
# Для таких параметров base = эталон — корректная привязка (ось их не трогает, а др. комбинация
# осей унаследует базу). Выведено eval-анализом (медиана по якорям роли). roles.json НЕ трогаем —
# это v5-слой генератора поверх resolve_skeleton. Главный паттерн: юзер почти везде слоит osc2.
CALIB_BASE = {
    "brass":       {"osc1_position": 62, "osc2_position": 30, "mix_osc2": 60, "osc2_detune": 0, "mix_noise": 11},
    "cymbal":      {"osc1_position": 20, "mix_osc1": 86},
    "drone":       {"osc2_position": 52, "mix_osc2": 59},
    "epiano":      {"osc2_position": 11, "mix_osc2": 70},
    "flute":       {"osc1_position": 8, "mix_osc1": 65, "mix_osc2": 45},
    "glass_pad":   {"osc2_position": 28, "mix_osc2": 62, "osc2_detune": 12},
    "gong":        {"osc1_position": 0, "mix_osc2": 81, "osc2_semitones": 12, "mix_noise": 27},
    "hihat":       {"osc1_position": 75, "mix_osc1": 91, "mix_osc2": 26, "osc2_detune": 10},
    "kick":        {"mix_osc1": 80, "mix_osc2": 22, "osc2_semitones": 12},
    "mallet":      {"mix_osc2": 67},
    "noise_texture": {"osc1_position": 80, "mix_osc2": 16, "mix_noise": 91},
    "pluck":       {"osc1_position": 67, "mix_osc2": 52},
    "pure_tone":   {"mix_osc1": 80, "mix_osc2": 19},
    "reed":        {"mix_osc2": 66, "mix_noise": 14},
    "riser_fx":    {"osc1_position": 85, "mix_osc2": 67, "osc2_detune": 18, "mix_noise": 86},
    "saw_bass":    {"osc1_position": 69, "mix_osc2": 55, "osc2_semitones": -12},
    "saw_lead":    {"osc1_position": 71, "osc2_position": 69},
    "snare_clap":  {"osc1_position": 14, "mix_osc2": 13},
    "sub_bass":    {"mix_osc1": 100},
    "tom":         {"mix_osc2": 65},
    "square_lead": {"osc1_position": 54, "mix_osc2": 68, "osc2_detune": 11, "mix_noise": 9},
}


def _apply_calibration(real, spec, roles, attrs):
    """3e: подставить откалиброванные от якорей СТРУКТУРНЫЕ значения базы, НО только для тех
    параметров, которые НЕ задаёт активная ось этого спека (ось — thickness/texture/vowel — выигрывает)."""
    calib = CALIB_BASE.get(spec["role"])
    if not calib:
        return real
    clean, _ = filter_axes(spec.get("axis_levels", {}), roles[spec["role"]])
    axis_touched = set()
    for ax, lvl in clean.items():
        axis_touched |= set(attrs["axes"].get(ax, {}).get("levels", {}).get(lvl, {}).keys())
    for p, v in calib.items():
        if p not in axis_touched:
            real[p] = v
    if float(real.get("mix_osc2", 0) or 0) > 0:   # активировали слой osc2 — банк osc2 = банк спека
        real["osc2_table"] = spec["bank"]
    return real


def _clamp_rules(real, role_name):
    """Слой 3a: относительные ограничения/связки поверх каркаса (resolve_skeleton)."""
    # (1) затухающие роли — sustain ~0 (убрать паразитный sustain из body=long/sustained/drone)
    if role_name in DECAY_ROLES:
        real["amp_sustain"] = min(float(real.get("amp_sustain", 0) or 0), 2.0)
    # (2) per-role param_bounds
    for p, (lo, hi) in PARAM_BOUNDS.get(role_name, {}).items():
        if p in real:
            real[p] = max(lo, min(hi, float(real[p])))
    return real


def filter_axes(axis_levels, role):
    """Дисциплина сэмплера: оставить только оси из role.vary_axes (+register/character).
    Возвращает (clean, dropped)."""
    allowed = set(role.get("vary_axes", [])) | ALWAYS_OK
    clean, dropped = {}, {}
    for ax, lvl in (axis_levels or {}).items():
        (clean if ax in allowed else dropped)[ax] = lvl
    return clean, dropped


def generate(spec, roles, attrs, mode="baseline"):
    """spec → {param: norm} (38). mode='baseline' = текущее поведение (для измерения старта)."""
    role = roles[spec["role"]]
    clean, _dropped = filter_axes(spec.get("axis_levels", {}), role)
    spec2 = dict(spec, axis_levels=clean)

    # v1: каркас в реальных единицах (neutral ⊕ role.base ⊕ якоря осей абсолютно)
    real, _locked, _character, _osc2 = v4_specs.resolve_skeleton(spec2, roles, attrs)

    if mode == "rules":
        real = _apply_calibration(real, spec, roles, attrs)   # 3e: структурная база от якорей
        real = _clamp_rules(real, spec["role"])               # 3a: клампы/связки
    elif mode != "baseline":
        raise NotImplementedError(f"mode={mode} ещё не реализован")

    return pc.patch_real_to_norm(real)
