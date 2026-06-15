#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe_encoder.py — ЛИНЕЙНЫЙ ПРОБИНГ энкодера (диагностика «виноват ли MiniLM?»).

Вопрос: разделяет ли замороженный энкодер описания по НУЖНЫМ признакам (роль/банк/регистр/
яркость/тело/…)? Берём эмбеддинги описаний датасета + известные метки (роль/оси из манифеста)
и учим ОДИН линейный слой эмб->признак (сплит ПО ПАТЧАМ). Высокая val-точность ⇒ семантика
ЛИНЕЙНО доступна в эмбеддинге (энкодер ок, проблема ниже по стеку). Низкая ⇒ энкодер/метки.

Сравниваем с majority-baseline (частота самого частого класса) — иначе точность не интерпретируема.

Запуск:  python ml/scripts/probe_encoder.py
         python ml/scripts/probe_encoder.py --encoder intfloat/multilingual-e5-base   # сравнить энкодер
"""

import argparse
import io
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "v5" / "dataset.jsonl"
MANIFEST = ROOT / "data" / "v5" / "manifest.json"
DEFAULT_ENCODER = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Признаки для пробинга: роль/банк всегда есть; оси — где присутствуют в axis_levels патча.
AXES = ["register", "brightness", "attack", "body", "texture", "movement", "space",
        "filter_motion", "thickness", "vowel"]


def load():
    specs = json.loads(io.open(MANIFEST, encoding="utf-8").read())["specs"]
    by_sp = {f"{s['category']}|{s['target']}|{s['variant']}": s for s in specs}
    rows = []
    with io.open(DATASET, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            s = by_sp.get(r["source_patch"])
            if not s:
                continue
            rows.append((r["source_patch"], r["text"], r["role"], s["bank"], s.get("axis_levels", {})))
    return rows


def encode(texts, name, cache):
    if cache.exists():
        d = np.load(cache, allow_pickle=True)
        if str(d["name"]) == name and int(d["n"]) == len(texts):
            return d["emb"].astype(np.float32)
    from sentence_transformers import SentenceTransformer
    print(f"  кодирую {len(texts)} описаний энкодером {name} ...")
    enc = SentenceTransformer(name)
    emb = enc.encode(texts, batch_size=64, convert_to_numpy=True,
                     normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
    np.savez(cache, emb=emb, name=np.array(name), n=np.array(len(texts)))
    return emb


def probe(emb, labels, tr, va, epochs=400):
    """Линейный классификатор эмб->метка. Возвращает (val_acc, baseline, n_classes)."""
    classes = sorted({labels[i] for i in (tr + va) if labels[i] is not None})
    cidx = {c: i for i, c in enumerate(classes)}
    y = np.array([cidx.get(l, -1) for l in labels], dtype=np.int64)
    Xtr, Xva = torch.tensor(emb[tr]), torch.tensor(emb[va])
    ytr, yva = torch.tensor(y[tr]), torch.tensor(y[va])
    clf = nn.Linear(emb.shape[1], len(classes))
    opt = torch.optim.Adam(clf.parameters(), lr=0.05, weight_decay=1e-3)
    lossf = nn.CrossEntropyLoss()
    for _ in range(epochs):
        opt.zero_grad()
        lossf(clf(Xtr), ytr).backward()
        opt.step()
    with torch.no_grad():
        acc = (clf(Xva).argmax(1) == yva).float().mean().item()
    base = Counter(y[va].tolist()).most_common(1)[0][1] / len(va)
    return acc, base, len(classes)


def main():
    ap = argparse.ArgumentParser(description="Линейный пробинг энкодера на признаки звука.")
    ap.add_argument("--encoder", default=DEFAULT_ENCODER)
    ap.add_argument("--val-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rows = load()
    texts = [r[1] for r in rows]
    print(f"Строк: {len(texts)} · патчей: {len({r[0] for r in rows})} · энкодер: {args.encoder}")

    safe = args.encoder.replace("/", "_")
    emb = encode(texts, args.encoder, ROOT / "models" / f"_probe_emb_{safe}.npz")

    # сплит по патчам (анти-течь)
    patches = sorted({r[0] for r in rows})
    rng = np.random.default_rng(args.seed)
    rng.shuffle(patches)
    n_val = max(1, int(round(args.val_frac * len(patches))))
    val_p = set(patches[:n_val])
    tr = [i for i, r in enumerate(rows) if r[0] not in val_p]
    va = [i for i, r in enumerate(rows) if r[0] in val_p]

    print(f"Сплит: train {len(tr)} / val {len(va)} строк ({len(patches)-n_val}/{n_val} патчей)\n")
    print(f"{'признак':<14} {'классов':>7} {'val acc':>8} {'baseline':>9} {'прирост':>8}  вывод")
    print("-" * 72)

    def report(name, labels_idx):
        labels = [rows[i][labels_idx] if isinstance(labels_idx, int) else labels_idx(rows[i])
                  for i in range(len(rows))]
        # отфильтровать None (ось отсутствует у патча)
        keep = [i for i in range(len(rows)) if labels[i] is not None]
        kset = set(keep)
        tri = [i for i in tr if i in kset]
        vai = [i for i in va if i in kset]
        if len(vai) < 10 or len(set(labels[i] for i in tri)) < 2:
            print(f"{name:<14} (мало данных: val={len(vai)})")
            return
        lab = [labels[i] for i in range(len(rows))]
        acc, base, k = probe(emb, lab, tri, vai)
        gain = acc - base
        verdict = "энкодер ОК" if gain > 0.25 else ("слабо" if gain > 0.1 else "НЕ разделяет")
        print(f"{name:<14} {k:>7} {acc:>8.2f} {base:>9.2f} {gain:>+8.2f}  {verdict}")

    report("role", 2)
    report("bank(osc1)", 3)
    for ax in AXES:
        report(ax, (lambda a: (lambda r: r[4].get(a)))(ax))


if __name__ == "__main__":
    main()
