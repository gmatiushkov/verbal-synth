#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
modifiers.py — ФАЗА 2: модификаторы ПАРАМЕТРОВ (PIVOT_RETRIEVAL.md §2, фаза 2).

Классификатор (L2) выбирает идентичность (прототип), а этот модуль детерминированно ДВИГАЕТ
непрерывные параметры под модификаторы запроса («теплее/ярче/короче/ниже/агрессивнее/просторнее»).
Меняются ТОЛЬКО затронутые параметры; ядро архетипа (банк, форма WT, осцилляторы) не трогается.

НЕЛИНЕЙНЫЙ сдвиг (op «edge»): двигаем параметр к нужному КРАЮ на фиксированную долю ОСТАВШЕГОСЯ
нормализованного диапазона:  new = cur + f·(1−cur)  при f>0 (к максимуму),  new = cur·(1+f) при f<0.
Почему не множитель/прибавка в физических единицах: нормализованная шкала движка для времён, частот
и rate — ЛОГАРИФМИЧЕСКАЯ (real = min·(max/min)^norm), т.е. перцептивная. Равная доля в norm = равный
перцептивный шаг при ЛЮБОМ исходном значении и авто-насыщение у границ. Линейный ×5 у дна давал
неслышимое (атака колокольчика 1→4 мс); edge +0.5 даёт ~70 мс — реальный наплыв. Дискретные параметры
(октава) по-прежнему сдвигаются на ступень в реальных единицах (op «add»).

Усилители масштабируют долю сдвига: «очень/слишком ярче» двигает сильнее, «чуть/слегка» — мягче.

    from modifiers import apply_modifiers
    new_params, applied = apply_modifiers(proto_params, "очень яркий короткий бас")
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import param_convert as pc

# Спецификации: (имя, cue-подстроки, [операции]). Операция = (параметр, вид, значение).
# Виды:
#   edge — сдвиг к краю в НОРМАЛИЗОВАННОМ пространстве на долю остатка (f>0 → к max, f<0 → к min);
#          |f|<1, перцептивно-равномерно, само-насыщается. Это основной вид для непрерывных.
#   add/mul/atleast/atmost — в РЕАЛЬНЫХ единицах (для дискретной октавы и т.п.).
# Cue-листы держим узкими, чтобы не путать с идентичностью; порядок — для читаемости.
MODIFIERS = [
    ("ярче",        ["ярк", "ярч", "светл", "звонк", "звонч", "bright", "блестящ", "искрист", "звенящ"],
     [("lp_cutoff", "edge", +0.38)]),
    ("пронзительно", ["пронзительн", "режущ", "остр ", "piercing", "визглив", "сверлящ"],
     [("lp_cutoff", "edge", +0.60), ("lp_resonance", "edge", +0.35)]),
    ("темнее",      ["тёмн", "темн", "глух", "глуш", "тускл", "приглуш", "муфл", "mellow", "матов"],
     [("lp_cutoff", "edge", -0.45)]),
    ("теплее",      ["тёпл", "тепл", "warm", "ламп", "округл", "бархат", "мягк", "мягч"],
     [("lp_cutoff", "edge", -0.28)]),
    ("ниже",        ["ниже", "пониж", "октав вниз", "octave down", "глубж"],
     [("osc1_octave", "add", -1)]),
    ("выше",        ["выше", "повыш", "октав вверх", "octave up"],
     [("osc1_octave", "add", 1)]),
    ("короче",      ["коротк", "короч", "отрывист", "стаккато", "staccato", "щелчк", "перкуссивн", "punch",
                     "тычк", "сухо и коротк", "tight"],
     [("amp_decay", "edge", -0.55), ("amp_release", "edge", -0.60), ("amp_sustain", "edge", -0.40)]),
    ("длиннее",     ["длинн", "протяжн", "тянущ", "бесконечн", "педаль", "затяжн", "longer", "долг звуч"],
     [("amp_release", "edge", +0.55), ("amp_decay", "edge", +0.40), ("amp_sustain", "edge", +0.45)]),
    ("мягкая атака", ["нараст", "плавн", "медленн атак", "swell", "наплыв", "fade in", "вплыв"],
     [("amp_attack", "edge", +0.50)]),
    ("резкая атака", ["щип", "пощип", "plucky", "цепк", "резк", "острая атак", "быстр атак"],
     [("amp_attack", "edge", -0.70)]),
    ("агрессивнее", ["агрессивн", "грязн", "жёстк", "жёстч", "жестч", "перегруж", "перегруз", "distort",
                     "dirty", "рычащ", "злой", "напорист"],
     [("drive_amount", "edge", +0.50)]),
    ("чище",        ["чище", "чист тон", "чистый звук", "гладк", "clean", "smooth", "нежн",
                     "без перегруз", "без драйв", "без искаж"],
     [("drive_amount", "edge", -0.65)]),
    ("просторнее",  ["простор", "в зал", "hall", "реверб", "эхо", "ambient", "объёмн", "далёк", "космич"],
     [("reverb_mix", "edge", +0.45), ("reverb_time", "edge", +0.30)]),
    ("сухо",        ["сух", "dry", "без реверб", "вблизи", "intimate", "близк звуч"],
     [("reverb_mix", "edge", -0.70)]),
]


# Отрицание ПРЯМО перед cue подавляет модификатор («не яркий» больше не делает ярче).
# Также «не очень/слишком X» (отрицание + усилитель + cue). Узко, чтобы «не» не глушило
# модификатор через слово («не яркий КОРОТКИЙ бас» → «короче» обязан сработать).
_NEG = {"не", "без", "ни", "нет"}

# Усилители/ослабители: масштабируют долю edge-сдвига. «очень ярче» >> «ярче» >> «чуть ярче».
_AMP = {"очень": 1.7, "слишком": 1.7, "сильно": 1.6, "супер": 1.8, "чрезмерно": 1.9,
        "максимально": 2.0, "крайне": 1.8, "ультра": 1.9}
_DAMP = {"чуть": 0.45, "слегка": 0.45, "немного": 0.55, "еле": 0.40, "чуточку": 0.40,
         "капельку": 0.45, "слабо": 0.55}
_EDGE_CAP = 0.9                                            # доля сдвига не ближе 90% к краю


def _negated(words, idx):
    """Отрицание непосредственно перед words[idx] (или через усилитель: «не очень X»)."""
    if idx - 1 >= 0 and words[idx - 1] in _NEG:
        return True
    if idx - 2 >= 0 and words[idx - 1] in _AMP and words[idx - 2] in _NEG:
        return True
    return False


def _scale(words, idx):
    """Множитель силы сдвига по усилителю/ослабителю прямо перед cue (1.0 если нет)."""
    if idx - 1 >= 0:
        w = words[idx - 1]
        if w in _AMP:
            return _AMP[w]
        if w in _DAMP:
            return _DAMP[w]
    return 1.0


def detect_modifiers(text):
    """[(имя, ops, scale), ...]. Отрицание перед cue подавляет; усилитель — масштабирует силу."""
    low = text.lower()
    words = [w.strip('.,!?;:()«»"\'') for w in low.split()]
    out = []
    for name, cues, ops in MODIFIERS:
        for c in cues:
            if " " in c:                                   # многословный cue — простое вхождение
                if c in low:
                    out.append((name, ops, 1.0)); break
            else:                                          # одно-словный cue — токенно, с отрицанием/усилением
                idxs = [i for i, w in enumerate(words) if c in w]
                if idxs and not _negated(words, idxs[0]):
                    out.append((name, ops, _scale(words, idxs[0]))); break
    return out


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
    if kind == "edge":
        # нелинейный сдвиг в НОРМАЛИЗОВАННОМ (перцептивном) пространстве к краю на долю остатка
        cur = min(max(float(params[param]), 0.0), 1.0)
        f = max(-_EDGE_CAP, min(_EDGE_CAP, float(val)))
        new = cur + f * (1.0 - cur) if f >= 0 else cur * (1.0 + f)
        params[param] = round(min(max(new, 0.0), 1.0), 6)
        return
    # операции в реальных единицах (дискретная октава и пр.)
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
    for name, ops, scale in detect_modifiers(text):
        for (p, k, v) in ops:
            _apply_op(out, p, k, (v * scale) if k == "edge" else v)
        applied.append(name)
    return out, applied
