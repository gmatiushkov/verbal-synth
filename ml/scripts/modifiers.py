#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
modifiers.py — ФАЗА 2: модификаторы ПАРАМЕТРОВ (PIVOT_RETRIEVAL.md §2, фаза 2).

retrieval выбирает идентичность (прототип), а этот модуль детерминированно ДВИГАЕТ непрерывные
параметры под модификаторы запроса («теплее/ярче/короче/ниже/агрессивнее/просторнее»). Сдвиги —
в РЕАЛЬНЫХ единицах (множитель/прибавка) с клипом через param_convert; меняются ТОЛЬКО затронутые
параметры, ядро архетипа (банк, форма WT, осцилляторы) не трогается.

Это отвечает на «ИЗМЕНИТЬ звук», чего retrieval не умеет (он лишь ВЫБИРАЕТ прототип). Поэтому
«тёплый бас» и «яркий бас» теперь дают разный срез фильтра на одной и той же базе.

    from modifiers import apply_modifiers
    new_params, applied = apply_modifiers(proto_params, "яркий короткий бас")
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import param_convert as pc

# Спецификации: (имя, cue-подстроки, [операции]). Операция = (параметр, вид, значение) в РЕАЛЬНЫХ
# единицах. Виды: mul (×), add (+), atleast (поднять не ниже), atmost (опустить не выше).
# Cue-листы держим узкими, чтобы не путать с идентичностью; порядок — для читаемости.
MODIFIERS = [
    ("ярче",        ["ярк", "светл", "звонк", "bright", "блестящ", "искрист", "звенящ"],
     [("lp_cutoff", "mul", 1.9)]),
    ("пронзительно", ["пронзительн", "режущ", "остр ", "piercing", "визглив", "сверлящ"],
     [("lp_cutoff", "mul", 3.0), ("lp_resonance", "add", 1.5)]),
    ("темнее",      ["тёмн", "темн", "глух", "тускл", "приглуш", "муфл", "mellow", "матов"],
     [("lp_cutoff", "mul", 0.45)]),
    ("теплее",      ["тёпл", "тепл", "warm", "ламп", "округл", "бархат"],
     [("lp_cutoff", "mul", 0.7)]),
    ("ниже",        ["ниже", "пониж", "октав вниз", "octave down", "глубж"],
     [("osc1_octave", "add", -1)]),
    ("выше",        ["выше", "повыш", "октав вверх", "octave up"],
     [("osc1_octave", "add", 1)]),
    ("короче",      ["коротк", "отрывист", "стаккато", "staccato", "щелчк", "перкуссивн", "punch",
                     "тычк", "сухо и коротк", "tight"],
     [("amp_decay", "mul", 0.4), ("amp_release", "mul", 0.3), ("amp_sustain", "mul", 0.5)]),
    ("длиннее",     ["длинн", "протяжн", "тянущ", "бесконечн", "педаль", "затяжн", "longer", "долг звуч"],
     [("amp_release", "mul", 2.6), ("amp_decay", "mul", 1.5), ("amp_sustain", "atleast", 70)]),
    ("мягкая атака", ["нараст", "плавн", "медленн атак", "swell", "наплыв", "fade in"],
     [("amp_attack", "mul", 5.0)]),
    ("резкая атака", ["щип", "пощип", "plucky", "цепк", "резкая атак", "острая атак", "быстр атак"],
     [("amp_attack", "mul", 0.3)]),
    ("агрессивнее", ["агрессивн", "грязн", "жёстк", "жёстч", "жестч", "перегруж", "перегруз", "distort",
                     "dirty", "рычащ", "злой", "напорист"],
     [("drive_amount", "add", 30)]),
    ("чище",        ["чище", "чист тон", "чистый звук", "гладк", "clean", "smooth", "нежн"],
     [("drive_amount", "mul", 0.3)]),
    ("просторнее",  ["простор", "в зал", "hall", "реверб", "эхо", "ambient", "объёмн", "далёк", "космич"],
     [("reverb_mix", "add", 25), ("reverb_time", "add", 15)]),
    ("сухо",        ["сух", "dry", "без реверб", "вблизи", "intimate", "близк звуч"],
     [("reverb_mix", "mul", 0.25)]),
]


def detect_modifiers(text):
    """Список сработавших модификаторов: [(имя, ops), ...]."""
    low = text.lower()
    return [(name, ops) for name, cues, ops in MODIFIERS if any(c in low for c in cues)]


# одно-словные cue-стеммы (для вырезания слов-модификаторов из запроса retrieval)
_WORD_CUES = [c for _, cues, _ in MODIFIERS for c in cues if " " not in c]


def strip_modifier_words(text):
    """Убирает из запроса СЛОВА-модификаторы → остаётся идентичность-residual для retrieval
    (чтобы «тёмный бас» искался как «бас», а не уводился прилагательным). Пусто → исходный текст."""
    kept = []
    for w in text.split():
        wl = w.lower().strip('.,!?;:()«»"\'')
        if not any(c in wl for c in _WORD_CUES):
            kept.append(w)
    return " ".join(kept).strip() or text


def _apply_op(params, param, kind, val):
    if param not in params:
        return
    real = pc.norm_to_real(param, params[param])
    if kind == "mul":
        real *= val
    elif kind == "add":
        real += val
    elif kind == "atleast":
        real = max(real, val)
    elif kind == "atmost":
        real = min(real, val)
    params[param] = round(pc.real_to_norm(param, real), 6)   # real_to_norm клипует в допустимый диапазон


def apply_modifiers(params, text):
    """Возвращает (копия params с применёнными модификаторами, список имён применённых)."""
    out = dict(params)
    applied = []
    for name, ops in detect_modifiers(text):
        for (p, k, v) in ops:
            _apply_op(out, p, k, v)
        applied.append(name)
    return out, applied
