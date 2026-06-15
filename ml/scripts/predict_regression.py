"""
[АРХИВ] Прежний инференс: текст → 38 параметров через ГИБРИДНУЮ РЕГРЕССИЮ (v3→v5).

Отменён пивотом на retrieval (PIVOT_RETRIEVAL.md §6): прямая регрессия 38 чисел схлопывалась
к среднему. Оставлено для справки / возможного возврата к фазе-2 модификаторов. Боевой
инференс теперь в predict.py (retrieval). Требует обученной головы ml/models/synth_predictor.pt.

    python predict_regression.py "тёплый бас с лёгким перегрузом"
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).parent))
import param_convert as pc
from model import SynthPredictor, reconstruct, ENCODER_NAME, CATEGORICALS

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
        cont, cats, axes = _model(torch.tensor(emb))
        vec = reconstruct(cont, cats, axes)[0]            # полный вектор 38 в PARAM_ORDER
    out = {}
    for i, name in enumerate(pc.PARAM_ORDER):
        v = min(max(float(vec[i]), 0.0), 1.0)
        if snap and name not in CATEGORICALS:             # категории уже на сетке; оси — на якорях
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
