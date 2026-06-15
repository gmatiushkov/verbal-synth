"""
Шаг 1 Фазы 3 — обучение ГИБРИДНОЙ головы text→patch.

Энкодер paraphrase-multilingual-MiniLM-L12-v2 (заморожен) → 384-dim →
общий ствол → регрессия непрерывных + классификация дискретных (model.py).

КЛЮЧЕВОЕ: сплит ПО source_patch, а не по строкам (6 описаний одного патча
имеют одинаковые params; сплит по строкам «протёк» бы ответ в val).

    python train.py
    python train.py --epochs 200 --val-frac 0.1 --seed 42

Артефакты в ml/models/: synth_predictor.pt, meta.json, emb_cache.npz.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader

sys.path.insert(0, str(Path(__file__).parent))
import param_convert as pc
from model import (SynthPredictor, reconstruct, ENCODER_NAME, INPUT_DIM, OUTPUT_DIM,
                   TRUNK, CATEGORICALS, CONT_NAMES, CONT_IDX, CAT_NAMES, CAT_IDX)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "ml" / "data" / "dataset.jsonl"
MODELS = ROOT / "ml" / "models"

# Порядок параметров ОБЯЗАН совпадать с SynthParameters.h (C++ paramNames()).
EXPECTED = [
    "osc1_table", "osc1_position", "osc1_octave",
    "osc2_table", "osc2_position", "osc2_detune", "osc2_semitones",
    "mix_osc1", "mix_osc2", "mix_noise",
    "lp_cutoff", "lp_resonance", "hp_cutoff", "hp_resonance", "filter_keytrack",
    "amp_attack", "amp_decay", "amp_sustain", "amp_release",
    "fenv_attack", "fenv_decay", "fenv_sustain", "fenv_release",
    "fenv_amount", "fenv_to_wt",
    "lfo1_rate", "lfo1_shape", "lfo1_to_pitch", "lfo1_to_filter",
    "lfo2_rate", "lfo2_shape", "lfo2_to_wt", "lfo2_to_amp",
    "drive_amount", "drive_tone",
    "reverb_time", "reverb_damp", "reverb_mix",
]
assert pc.PARAM_ORDER == EXPECTED, "PARAM_ORDER разошёлся с SynthParameters.h!"
assert len(EXPECTED) == OUTPUT_DIM

# Перцептивно важные непрерывные параметры — тянем сильнее в лоссе.
HIGH_W = {"amp_attack", "amp_decay", "amp_sustain", "amp_release",
          "lp_cutoff", "mix_osc1", "mix_osc2", "mix_noise",
          "reverb_mix", "drive_amount"}
CONT_SCALE = 10.0   # вес регрессии относительно классификации в общем лоссе


def load_rows(data_path=DATA):
    rows = []
    with open(data_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            p = r["params"]
            assert len(p) == OUTPUT_DIM, f"ожидалось {OUTPUT_DIM} параметров, а в строке {len(p)}"
            rows.append((r["source_patch"], r["text"], p))
    return rows


def get_embeddings(texts, cache_path):
    key = hashlib.md5((ENCODER_NAME + "␟" + "\n".join(texts)).encode("utf-8")).hexdigest()
    if cache_path.exists():
        d = np.load(cache_path, allow_pickle=False)
        if str(d["key"]) == key and d["emb"].shape[0] == len(texts):
            print(f"  кэш эмбеддингов: {cache_path.name} {tuple(d['emb'].shape)}")
            return d["emb"].astype(np.float32)
    from sentence_transformers import SentenceTransformer
    print(f"  кодирую {len(texts)} описаний энкодером {ENCODER_NAME} ...")
    enc = SentenceTransformer(ENCODER_NAME)
    emb = enc.encode(texts, batch_size=64, convert_to_numpy=True,
                     normalize_embeddings=True, show_progress_bar=True).astype(np.float32)
    np.savez(cache_path, emb=emb, key=np.array(key))
    return emb


def split_by_patch(rows, val_frac, seed):
    patches = sorted({r[0] for r in rows})
    rng = np.random.default_rng(seed)
    rng.shuffle(patches)
    n_val = max(1, int(round(val_frac * len(patches))))
    val_patches = set(patches[:n_val])
    tr = [i for i, r in enumerate(rows) if r[0] not in val_patches]
    va = [i for i, r in enumerate(rows) if r[0] in val_patches]
    return tr, va, len(patches) - n_val, n_val


def cat_targets(Y):
    """[N,38] норм → [N, len(CAT)] индексы классов (ближайший узел сетки)."""
    out = np.empty((len(Y), len(CAT_NAMES)), dtype=np.int64)
    for j, n in enumerate(CAT_NAMES):
        grid = np.asarray(CATEGORICALS[n])[None, :]
        out[:, j] = np.abs(Y[:, CAT_IDX[j]][:, None] - grid).argmin(axis=1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=160)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--data", default=str(DATA), help="путь к dataset.jsonl (деф. v3)")
    ap.add_argument("--out-dir", default=str(MODELS),
                    help="куда писать модель/meta/кэш (деф. ml/models — ЖИВАЯ v3-модель; для v5 укажи ml/models/v5)")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    rows = load_rows(Path(args.data))
    texts = [r[1] for r in rows]
    Y_all = np.asarray([r[2] for r in rows], dtype=np.float32)
    n_patches = len({r[0] for r in rows})
    print(f"Датасет: {len(rows)} строк, {n_patches} патчей")

    emb = get_embeddings(texts, out_dir / "emb_cache.npz")
    assert emb.shape[1] == INPUT_DIM, f"энкодер выдал {emb.shape[1]} вместо {INPUT_DIM}"

    tr, va, n_tr_p, n_va_p = split_by_patch(rows, args.val_frac, args.seed)
    print(f"Сплит по патчам: train {n_tr_p}п / {len(tr)} строк · val {n_va_p}п / {len(va)} строк")
    print(f"Голова: {len(CONT_NAMES)} регрессия + {len(CAT_NAMES)} классиф. {CAT_NAMES}")

    Ycont = Y_all[:, CONT_IDX]
    Ycat = cat_targets(Y_all)

    Xtr = torch.tensor(emb[tr])
    Xva = torch.tensor(emb[va])
    Yc_tr, Yc_va = torch.tensor(Ycont[tr]), torch.tensor(Ycont[va])
    Yk_tr, Yk_va = torch.tensor(Ycat[tr]), torch.tensor(Ycat[va])
    Yfull_va = torch.tensor(Y_all[va])

    # веса непрерывных параметров
    w = np.ones(len(CONT_NAMES), dtype=np.float32)
    for i, n in enumerate(CONT_NAMES):
        if n in HIGH_W:
            w[i] = 2.0
    wt = torch.tensor(w)

    loader = DataLoader(TensorDataset(Xtr, Yc_tr, Yk_tr), batch_size=args.batch_size, shuffle=True)
    model = SynthPredictor()
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    huber = nn.HuberLoss(delta=0.1, reduction="none")
    ce = nn.CrossEntropyLoss()

    base_mae = (Yfull_va - torch.tensor(Y_all[tr]).mean(0, keepdim=True)).abs().mean().item()

    def evaluate():
        model.eval()
        with torch.no_grad():
            cont, cats = model(Xva)
            cont_mae = (cont - Yc_va).abs().mean().item()
            accs = {n: (cats[n].argmax(1) == Yk_va[:, j]).float().mean().item()
                    for j, n in enumerate(CAT_NAMES)}
            full_mae = (reconstruct(cont, cats) - Yfull_va).abs().mean().item()
        return cont_mae, accs, full_mae

    best, best_state = float("inf"), None
    for ep in range(args.epochs):
        model.train()
        for xb, ycb, ykb in loader:
            cont, cats = model(xb)
            l_cont = (huber(cont, ycb) * wt).mean()
            l_cat = sum(ce(cats[n], ykb[:, j]) for j, n in enumerate(CAT_NAMES)) / len(CAT_NAMES)
            loss = CONT_SCALE * l_cont + l_cat
            opt.zero_grad()
            loss.backward()
            opt.step()
        sched.step()

        cont_mae, accs, full_mae = evaluate()
        if full_mae < best:
            best = full_mae
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        if ep % 10 == 0 or ep == args.epochs - 1:
            acc_s = " ".join(f"{n.split('_')[0]}{n[-1] if n[-1].isdigit() else ''}:{a:.2f}"
                             for n, a in accs.items())
            print(f"  эп {ep:3d}: full MAE {full_mae:.4f} (best {best:.4f}) · cont {cont_mae:.4f} · acc {acc_s}")

    model.load_state_dict(best_state)
    torch.save(best_state, out_dir / "synth_predictor.pt")

    cont_mae, accs, full_mae = evaluate()
    model.eval()
    with torch.no_grad():
        cont, cats = model(Xva)
        per = (cont - Yc_va).abs().mean(0).numpy()
    print("\nХудшие по MAE непрерывные (val):")
    for i in np.argsort(-per)[:8]:
        print(f"  {CONT_NAMES[i]:16s} MAE {per[i]:.3f}")
    print("\nТочность классификации дискретных (val):")
    for n, a in accs.items():
        print(f"  {n:16s} acc {a:.3f}")
    print(f"\nИТОГ: full MAE {best:.4f}  ·  бэйзлайн-среднее {base_mae:.4f}  ·  {time.time() - t0:.0f}с")

    meta = {
        "encoder": ENCODER_NAME,
        "input_dim": INPUT_DIM,
        "trunk": list(TRUNK),
        "output_dim": OUTPUT_DIM,
        "head": "hybrid",
        "normalize_embeddings": True,
        "param_order": pc.PARAM_ORDER,
        "cont_names": CONT_NAMES,
        "categoricals": {n: list(CATEGORICALS[n]) for n in CAT_NAMES},
        "rows": len(rows), "patches": n_patches, "val_patches": n_va_p,
        "full_mae": round(best, 5), "baseline_mae": round(base_mae, 5),
        "cat_accuracy": {n: round(a, 4) for n, a in accs.items()},
        "epochs": args.epochs, "seed": args.seed,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Сохранено: {out_dir / 'synth_predictor.pt'} + meta.json")


if __name__ == "__main__":
    main()
