"""Архитектура головы text→patch (Фаза 3) — ГИБРИДНАЯ.

Регрессия для непрерывных параметров + классификация для дискретных
(банки / октава OSC1 / формы LFO). Регрессия по дискретной цели давала
«среднее» (reese-бас уезжал на Acoustic вместо Basic, бас не опускался по
октаве). Классификация предсказывает МОДАЛЬНЫЙ класс — устойчиво к шуму
разнообразия в данных.

Единый источник правды — импортируется train.py / predict.py / export_onnx.py.
"""
import sys
from pathlib import Path

import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).parent))
import param_convert as pc

# Энкодер: МУЛЬТИЯЗЫЧНЫЙ (описания на русском!), выход 384-dim, заморожен.
ENCODER_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
INPUT_DIM = 384
TRUNK = (256, 128, 64)
OUTPUT_DIM = 38   # = SynthPatch::kNumParams (SynthParameters.h)

# Дискретные параметры → классификация. grid = норм-значения классов.
CATEGORICALS = {
    "osc1_table":  pc.BANK_NORMS,        # 6 банков
    "osc2_table":  pc.BANK_NORMS,        # 6
    "osc1_octave": pc.OCTAVE_NORMS,      # 5 ступеней (-2..+2)
    "lfo1_shape":  pc.LFO_SHAPE_NORMS,   # 4 формы
    "lfo2_shape":  pc.LFO_SHAPE_NORMS,   # 4
}
# Непрерывные / категориальные имена в порядке PARAM_ORDER (= индексы вектора).
CONT_NAMES = [n for n in pc.PARAM_ORDER if n not in CATEGORICALS]
CONT_IDX = [pc.PARAM_ORDER.index(n) for n in CONT_NAMES]
CAT_NAMES = [n for n in pc.PARAM_ORDER if n in CATEGORICALS]
CAT_IDX = [pc.PARAM_ORDER.index(n) for n in CAT_NAMES]


class SynthPredictor(nn.Module):
    """Эмбеддинг (384) → общий ствол → {регрессия непрерывных, softmax дискретных}."""

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

    def forward(self, x):
        h = self.trunk(x)
        cont = torch.sigmoid(self.reg(h))            # [B, n_cont] в [0..1]
        cats = {n: head(h) for n, head in self.cls.items()}   # логиты по классам
        return cont, cats


def reconstruct(cont, cats):
    """(регрессия, логиты) → полный вектор 38 параметров [0..1] в PARAM_ORDER."""
    out = torch.zeros((cont.shape[0], OUTPUT_DIM), dtype=cont.dtype, device=cont.device)
    for i, n in enumerate(CONT_NAMES):
        out[:, CONT_IDX[i]] = cont[:, i]
    for n in CAT_NAMES:
        grid = torch.tensor(CATEGORICALS[n], dtype=cont.dtype, device=cont.device)
        out[:, pc.PARAM_ORDER.index(n)] = grid[cats[n].argmax(dim=1)]
    return out
