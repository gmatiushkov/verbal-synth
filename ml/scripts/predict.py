"""
Инференс: текст → 38 параметров синта (гибридная голова).

Печатает JSON {param_name: value} — формат PresetManager (плоский патч).
Непрерывные параметры — из регрессии (со снапом к сетке у дискретных-по-шагу,
напр. osc2_semitones), дискретные (банки/октава/форма LFO) — argmax классификатора.

    python predict.py "тёплый бас с лёгким перегрузом"
    echo "яркий колокольчик" | python predict.py
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).parent))
import param_convert as pc
from model import SynthPredictor, ENCODER_NAME, CATEGORICALS, CONT_NAMES, CAT_NAMES

MODELS = Path(__file__).resolve().parents[2] / "ml" / "models"

_enc = None
_model = None
_meta = None


def _load():
    global _enc, _model, _meta
    if _model is not None:
        return
    _meta = json.loads((MODELS / "meta.json").read_text(encoding="utf-8"))
    from sentence_transformers import SentenceTransformer
    _enc = SentenceTransformer(_meta.get("encoder", ENCODER_NAME))
    _model = SynthPredictor()
    _model.load_state_dict(torch.load(MODELS / "synth_predictor.pt", map_location="cpu"))
    _model.eval()


def predict(text, snap=True):
    _load()
    emb = _enc.encode([text], normalize_embeddings=True, convert_to_numpy=True)
    with torch.no_grad():
        cont, cats = _model(torch.tensor(emb))
    vals = {n: float(cont[0, i]) for i, n in enumerate(CONT_NAMES)}
    for n in CAT_NAMES:
        vals[n] = CATEGORICALS[n][int(cats[n][0].argmax())]
    out = {}
    for name in pc.PARAM_ORDER:
        v = min(max(vals[name], 0.0), 1.0)
        if snap and name not in CATEGORICALS:     # дискретные уже на сетке
            v = round(pc.real_to_norm(name, pc.norm_to_real(name, v)), 6)
        out[name] = v
    return out


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]).strip()
    if not text and not sys.stdin.isatty():
        text = sys.stdin.readline().strip()
    if not text:
        print(json.dumps({"error": "no text"}))
        sys.exit(1)
    print(json.dumps(predict(text), ensure_ascii=False))
