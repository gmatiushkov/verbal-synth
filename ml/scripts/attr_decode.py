#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
attr_decode.py — ДЕКОДЕР параметров обратно в перцептивные атрибуты.

Нужен для метрики: и регрессионная модель (38 чисел), и будущая классификационная меряются
одинаково — переводим выход в атрибуты (банк/регистр/яркость/тело) и сравниваем с ожиданием
золотого набора. Атрибуты определяются ближайшим уровнем оси (якоря из config/v4/attributes.json),
банк/регистр — напрямую из дискретных параметров.

p — плоский патч {имя_параметра: norm[0..1]} (как из predict.predict / пресета синта).
"""

import io
import json
from pathlib import Path

import param_convert as pc

ROOT = Path(__file__).resolve().parents[1]
ATTRS_PATH = ROOT / "config" / "v4" / "attributes.json"

# Порядок уровней для ОРДИНАЛЬНЫХ осей (для метрики «в пределах 1 уровня»).
REGISTER_ORDER = ["sub", "low", "mid", "high", "very_high"]
BRIGHTNESS_ORDER = ["dark", "warm", "neutral", "bright", "piercing"]
BODY_ORDER = ["staccato", "pluck", "sustained", "long", "drone"]
_OCT2REG = {-2: "sub", -1: "low", 0: "mid", 1: "high", 2: "very_high"}

_attrs = None


def _load():
    global _attrs
    if _attrs is None:
        _attrs = json.loads(io.open(ATTRS_PATH, encoding="utf-8-sig").read())
    return _attrs


def _nearest(p, axis_params, levels):
    """Ближайший уровень оси по евклиду в norm-пространстве заданных параметров."""
    best, bd = None, float("inf")
    for lv, anch in levels.items():
        d = 0.0
        cnt = 0
        for prm in axis_params:
            if prm in anch and prm in p:
                tn = pc.real_to_norm(prm, anch[prm])
                d += (float(p[prm]) - tn) ** 2
                cnt += 1
        if cnt and d < bd:
            bd, best = d, lv
    return best


def decode_bank(p):
    return pc.norm_to_real("osc1_table", p["osc1_table"])


def decode_register(p):
    o = max(-2, min(2, round(pc.norm_to_real("osc1_octave", p["osc1_octave"]))))
    return _OCT2REG[o]


def decode_brightness(p):
    return _nearest(p, ["lp_cutoff"], _load()["axes"]["brightness"]["levels"])


def decode_body(p):
    return _nearest(p, ["amp_decay", "amp_sustain", "amp_release"], _load()["axes"]["body"]["levels"])


DECODERS = {"bank": decode_bank, "register": decode_register,
            "brightness": decode_brightness, "body": decode_body}
ORDINAL = {"register": REGISTER_ORDER, "brightness": BRIGHTNESS_ORDER, "body": BODY_ORDER}


def decode_all(p):
    return {a: f(p) for a, f in DECODERS.items()}


def ordinal_dist(attr, a, b):
    """|разница индексов| для ординальной оси; None для номинальной (банк)."""
    order = ORDINAL.get(attr)
    if not order or a not in order or b not in order:
        return None
    return abs(order.index(a) - order.index(b))
