"""Архитектура головы text→patch (Фаза 3 → реворк v5) — ГИБРИД + ОСИ-КЛАССИФИКАЦИЯ.

Реворк (golden-эвал показал: непрерывная регрессия яркости/тела схлопывается к среднему —
«очень яркий»→neutral, «длинный дрон»→pluck). Поэтому ПЕРЦЕПТИВНО-САЛИЕНТНЫЕ оси переводим
в КЛАССИФИКАЦИЮ по уровням, а параметры этих осей СНАПИМ к якорям уровня (config/v4/attributes.json
= те же значения, что кладёт param_rules). Модель «решается» на piercing/drone вместо мутной середины.

Три типа выходов:
  • КАТЕГОРИИ (как было): osc1_table/osc2_table/osc1_octave/lfo1_shape/lfo2_shape — argmax по сетке.
  • ОСИ (новое): brightness/attack/body/texture — argmax уровня → параметры оси из якоря уровня.
  • РЕГРЕССИЯ: всё остальное (позиции/миксы/osc2/фильтры/fenv/lfo-rate/reverb) — sigmoid.

bank/октава уже работали классификацией (golden: банк 100%, регистр 82%); яркость/тело — главная цель.

Единый источник правды — импортируется train.py / predict.py / eval_golden.py.
"""
import io
import json
import sys
from pathlib import Path

import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).parent))
import param_convert as pc

ENCODER_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
INPUT_DIM = 384
TRUNK = (256, 128, 64)
OUTPUT_DIM = 38

ATTRS_PATH = Path(__file__).resolve().parents[1] / "config" / "v4" / "attributes.json"

# Дискретные «сеточные» параметры → классификация (grid = норм-значения классов).
CATEGORICALS = {
    "osc1_table":  pc.BANK_NORMS,
    "osc2_table":  pc.BANK_NORMS,
    "osc1_octave": pc.OCTAVE_NORMS,
    "lfo1_shape":  pc.LFO_SHAPE_NORMS,
    "lfo2_shape":  pc.LFO_SHAPE_NORMS,
}

# Перцептивные ОСИ → классификация по уровням; параметры оси берутся из якоря уровня (norm).
AXIS_AXES = ["brightness", "attack", "body", "texture"]


def _build_axis_heads():
    attrs = json.loads(io.open(ATTRS_PATH, encoding="utf-8-sig").read())
    heads = {}
    for ax in AXIS_AXES:
        spec = attrs["axes"][ax]
        levels = list(spec["levels"].keys())
        anchor_norm = {}
        for lv, anch in spec["levels"].items():
            anchor_norm[lv] = {p: float(pc.real_to_norm(p, v)) for p, v in anch.items()
                               if p in pc.PARAM_SPEC}
        params = sorted({p for a in anchor_norm.values() for p in a})
        heads[ax] = {"levels": levels, "anchor_norm": anchor_norm, "params": params}
    return heads


AXIS_HEADS = _build_axis_heads()
AXIS_PARAMS = sorted({p for h in AXIS_HEADS.values() for p in h["params"]})

# Регрессия — всё, что не категория и не управляется осью.
CONT_NAMES = [n for n in pc.PARAM_ORDER if n not in CATEGORICALS and n not in AXIS_PARAMS]
CONT_IDX = [pc.PARAM_ORDER.index(n) for n in CONT_NAMES]
CAT_NAMES = [n for n in pc.PARAM_ORDER if n in CATEGORICALS]
CAT_IDX = [pc.PARAM_ORDER.index(n) for n in CAT_NAMES]
AXIS_NAMES = list(AXIS_HEADS.keys())


class SynthPredictor(nn.Module):
    """Эмбеддинг (384) → ствол → {регрессия, категории-softmax, оси-softmax}."""

    def __init__(self, input_dim=INPUT_DIM, trunk=TRUNK, dropout=0.15):
        super().__init__()
        layers = []
        prev = input_dim
        for h in trunk:
            layers += [nn.Linear(prev, h), nn.LayerNorm(h), nn.GELU(), nn.Dropout(dropout)]
            prev = h
        self.trunk = nn.Sequential(*layers)
        self.reg = nn.Linear(prev, len(CONT_NAMES))
        self.cls = nn.ModuleDict({n: nn.Linear(prev, len(CATEGORICALS[n])) for n in CAT_NAMES})
        self.axis = nn.ModuleDict({a: nn.Linear(prev, len(AXIS_HEADS[a]["levels"])) for a in AXIS_NAMES})

    def forward(self, x):
        h = self.trunk(x)
        cont = torch.sigmoid(self.reg(h))
        cats = {n: head(h) for n, head in self.cls.items()}
        axes = {a: head(h) for a, head in self.axis.items()}
        return cont, cats, axes


def reconstruct(cont, cats, axes):
    """(регрессия, лог.категорий, лог.осей) → полный вектор 38 [0..1] в PARAM_ORDER."""
    B = cont.shape[0]
    out = torch.zeros((B, OUTPUT_DIM), dtype=cont.dtype, device=cont.device)
    for i, n in enumerate(CONT_NAMES):
        out[:, CONT_IDX[i]] = cont[:, i]
    for n in CAT_NAMES:
        grid = torch.tensor(CATEGORICALS[n], dtype=cont.dtype, device=cont.device)
        out[:, pc.PARAM_ORDER.index(n)] = grid[cats[n].argmax(dim=1)]
    for a in AXIS_NAMES:
        levels = AXIS_HEADS[a]["levels"]
        anc = AXIS_HEADS[a]["anchor_norm"]
        idx = axes[a].argmax(dim=1)
        for li, lv in enumerate(levels):
            mask = idx == li
            if not bool(mask.any()):
                continue
            for prm, val in anc[lv].items():
                out[mask, pc.PARAM_ORDER.index(prm)] = val
    return out


def axis_label_idx(axis, norm_patch):
    """Индекс ближайшего уровня оси для патча {имя:norm} (евклид по параметрам оси в norm)."""
    h = AXIS_HEADS[axis]
    best, bd = 0, float("inf")
    for li, lv in enumerate(h["levels"]):
        anc = h["anchor_norm"][lv]
        d = sum((float(norm_patch[p]) - v) ** 2 for p, v in anc.items() if p in norm_patch)
        if d < bd:
            bd, best = d, li
    return best
