#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clf.py — ЯДРО L2-классификатора «запрос → прототип» (ВКР-грейд ML-компонент).

Архитектура каскада (см. записку, L1→L4):
  L1  запрос → эмбеддинг (e5-base, ПРЕДОБУЧЕН и ЗАМОРОЖЕН — feature-extractor)
  L2  эмбеддинг → ОБУЧАЕМАЯ голова (MLP) → один из 140 прототипов     ← это и есть ML
  L3  прототип → ручные 38 параметров (library.json)
  L4  параметры → детерминированные модификаторы (modifiers.py)

Почему голова, а не сырой косинус (retrieval): классификатор учит ГРАНИЦЫ решений на сотнях
формулировок (queries.json), а не ищет ближайшего соседа в неадаптированном пространстве e5.
Это чинит провалы вида «барабан → аккордеон», где сырая близость шумит на голых существительных.

Датасет: queries.json (gen_queries.py) — ~30 формулировок на прототип, метка = #N по построению.
Сплит стратифицирован по прототипу (каждый класс есть в train). Честный held-out — РУЧНОЙ golden.

Здесь: загрузка пар, стратифицированный сплит, e5-энкодер с кэшем, модель Head, save/load,
класс Classifier для инференса (predict.py). Обучение/эвал — в train_clf.py.
"""

import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from retrieval import DEFAULT_ENCODER, LIB, QUERIES, _prefixes, load_library

ROOT = Path(__file__).resolve().parents[1]                 # .../ml
MODEL_DIR = ROOT / "models" / "clf"
SPLIT_PATH = ROOT / "data" / "library" / "clf_split.json"  # фиксированный воспроизводимый сплит
EMB_CACHE_DIR = MODEL_DIR / "emb_cache"                    # кэш эмбеддингов по сплитам (emb_<tag>.npz)


# ── данные ──────────────────────────────────────────────────────────────────
def load_label_maps(lib_path=LIB):
    """Прототипы с непустыми params → отображения num↔index и num→role/target."""
    lib = load_library(lib_path)
    entries = [e for e in lib["entries"] if e.get("params")]
    nums = sorted(e["num"] for e in entries)
    by_num = {e["num"]: e for e in entries}
    num2idx = {n: i for i, n in enumerate(nums)}
    role_by_num = {n: by_num[n].get("role", "") for n in nums}
    target_by_num = {n: by_num[n].get("target", "") for n in nums}
    return nums, num2idx, role_by_num, target_by_num


def entries_by_num(lib_path=LIB):
    """num → полная запись прототипа (с params) для построения hits/params в инференсе."""
    lib = load_library(lib_path)
    return {e["num"]: e for e in lib["entries"] if e.get("params")}


def load_pairs(per=None, queries_path=QUERIES, valid_nums=None):
    """queries.json → [(query, num), ...] только для прототипов с params (valid_nums)."""
    qdata = json.loads(io.open(queries_path, encoding="utf-8-sig").read())["entries"]
    pairs = []
    for snum, qs in qdata.items():
        num = int(snum)
        if valid_nums is not None and num not in valid_nums:
            continue
        use = qs[:per] if per else qs
        for q in use:
            q = (q or "").strip()
            if q:
                pairs.append((q, num))
    return pairs


def stratified_split(pairs, seed=42, fracs=(0.70, 0.15, 0.15)):
    """Сплит по прототипу: каждый класс пропорционально делится на train/val/test.
    Так train видит ВСЕ 140 классов, а test/val — независимые формулировки (обобщение на фразинг)."""
    rng = np.random.default_rng(seed)
    by_num = {}
    for q, n in pairs:
        by_num.setdefault(n, []).append(q)
    train, val, test = [], [], []
    for n, qs in by_num.items():
        qs = list(qs)
        rng.shuffle(qs)
        k = len(qs)
        n_tr = max(1, int(round(k * fracs[0])))
        n_va = max(1, int(round(k * fracs[1]))) if k >= 3 else 0
        n_tr = min(n_tr, k)
        n_va = min(n_va, k - n_tr)
        train += [(q, n) for q in qs[:n_tr]]
        val += [(q, n) for q in qs[n_tr:n_tr + n_va]]
        test += [(q, n) for q in qs[n_tr + n_va:]]
    return train, val, test


def build_and_save_split(per=None, seed=42, fracs=(0.70, 0.15, 0.15)):
    nums, _, _, _ = load_label_maps()
    pairs = load_pairs(per=per, valid_nums=set(nums))
    train, val, test = stratified_split(pairs, seed=seed, fracs=fracs)
    SPLIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    obj = {"seed": seed, "fracs": list(fracs), "per": per,
           "counts": {"train": len(train), "val": len(val), "test": len(test)},
           "train": [[q, n] for q, n in train], "val": [[q, n] for q, n in val],
           "test": [[q, n] for q, n in test]}
    io.open(SPLIT_PATH, "w", encoding="utf-8").write(json.dumps(obj, ensure_ascii=False, indent=1))
    return train, val, test


def load_split():
    if not SPLIT_PATH.exists():
        return build_and_save_split()
    o = json.loads(io.open(SPLIT_PATH, encoding="utf-8-sig").read())
    f = lambda k: [(q, int(n)) for q, n in o[k]]
    return f("train"), f("val"), f("test")


# ── энкодер e5 (L1, заморожен) ────────────────────────────────────────────────
_ENC_CACHE = {}


def get_encoder(name=DEFAULT_ENCODER):
    if name not in _ENC_CACHE:
        from sentence_transformers import SentenceTransformer
        _ENC_CACHE[name] = SentenceTransformer(name)
    return _ENC_CACHE[name]


def embed(texts, encoder_name=DEFAULT_ENCODER, batch_size=64):
    """Тексты → L2-нормированные эмбеддинги e5 с query-префиксом (как в retrieval/инференсе)."""
    qpref, _ = _prefixes(encoder_name)
    enc = get_encoder(encoder_name)
    return enc.encode([qpref + t.strip() for t in texts], batch_size=batch_size,
                      convert_to_numpy=True, normalize_embeddings=True,
                      show_progress_bar=False).astype(np.float32)


def embed_cached(texts, encoder_name=DEFAULT_ENCODER, tag="default"):
    """Как embed, но кэширует на диск по хэшу (encoder + упорядоченный список текстов).
    tag разводит сплиты по разным файлам (train/val/test не перетирают друг друга)."""
    h = hashlib.sha256(encoder_name.encode("utf-8"))
    for t in texts:
        h.update(t.encode("utf-8")); h.update(b"\x00")
    key = h.hexdigest()
    path = EMB_CACHE_DIR / f"emb_{tag}.npz"
    if path.exists():
        d = np.load(path, allow_pickle=True)
        if str(d.get("hash")) == key:
            return d["emb"].astype(np.float32)
    emb = embed(texts, encoder_name)
    EMB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(path, emb=emb, hash=np.array(key))
    return emb


# ── модель (L2) ───────────────────────────────────────────────────────────────
def make_head(dim, n_classes, hidden=384, dropout=0.4):
    import torch.nn as nn
    return nn.Sequential(
        nn.Linear(dim, hidden), nn.ReLU(), nn.Dropout(dropout),
        nn.Linear(hidden, n_classes),
    )


def save_model(model, nums, role_by_num, target_by_num, encoder_name, dim, hidden, meta=None):
    import torch
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), MODEL_DIR / "head.pt")
    obj = {"encoder": encoder_name, "dim": dim, "hidden": hidden, "nums": nums,
           "role_by_num": {str(n): role_by_num[n] for n in nums},
           "target_by_num": {str(n): target_by_num[n] for n in nums},
           "meta": meta or {}}
    io.open(MODEL_DIR / "meta.json", "w", encoding="utf-8").write(
        json.dumps(obj, ensure_ascii=False, indent=1))


# ── инференс ──────────────────────────────────────────────────────────────────
class Classifier:
    """Загружает обученную голову + e5; predict(text) → top-k прототипов (num/role/prob)."""

    def __init__(self, model_dir=MODEL_DIR):
        import torch
        meta = json.loads(io.open(Path(model_dir) / "meta.json", encoding="utf-8-sig").read())
        self.encoder_name = meta["encoder"]
        self.nums = meta["nums"]
        self.role_by_num = {int(k): v for k, v in meta["role_by_num"].items()}
        self.target_by_num = {int(k): v for k, v in meta["target_by_num"].items()}
        self.model = make_head(meta["dim"], len(self.nums), hidden=meta["hidden"], dropout=0.0)
        self.model.load_state_dict(torch.load(Path(model_dir) / "head.pt", map_location="cpu"))
        self.model.eval()
        self._torch = torch

    @staticmethod
    def exists(model_dir=MODEL_DIR):
        return (Path(model_dir) / "head.pt").exists() and (Path(model_dir) / "meta.json").exists()

    def predict(self, text, k=3):
        torch = self._torch
        emb = embed([text], self.encoder_name)            # (1, dim) L2-норм
        with torch.no_grad():
            logits = self.model(torch.from_numpy(emb))[0]
            probs = torch.softmax(logits, dim=-1).numpy()
        order = np.argsort(-probs)[:k]
        return [{"num": self.nums[int(i)], "role": self.role_by_num[self.nums[int(i)]],
                 "target": self.target_by_num[self.nums[int(i)]],
                 "prob": round(float(probs[int(i)]), 4)} for i in order]
