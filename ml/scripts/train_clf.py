#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_clf.py — обучение головы-классификатора (L2) + честный эвал + сравнение с retrieval-baseline.

  python ml/scripts/train_clf.py                 # сплит из clf_split.json (создаётся при первом запуске)
  python ml/scripts/train_clf.py --rebuild-split # пересоздать сплит из queries.json
  python ml/scripts/train_clf.py --epochs 120

Метрики (главная — role «верная семья = ок»):
  • test  — независимые формулировки тех же прототипов (обобщение на фразинг), self-labeled.
  • golden — РУЧНОЙ held-out (golden_retrieval.json): primary=точный прототип, expected=семья.
Печатает таблицу «retrieval-baseline vs классификатор» на одинаковых данных.
"""

import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import clf
from retrieval import DEFAULT_ENCODER, Retriever

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

GOLDEN = clf.ROOT / "eval" / "golden_retrieval.json"


# ── метрики ───────────────────────────────────────────────────────────────────
def score_topk(pred_nums, gold_num, role_by_num):
    """pred_nums — список top-k предсказанных num (по убыванию). Возвращает 4 флага."""
    g_role = role_by_num.get(gold_num, "")
    roles = [role_by_num.get(n, "") for n in pred_nums]
    return {"s1": pred_nums[0] == gold_num, "s3": gold_num in pred_nums,
            "r1": roles[0] == g_role, "r3": g_role in roles}

def aggregate(rows):
    n = len(rows) or 1
    k = lambda key: sum(r[key] for r in rows) / n
    return {"n": len(rows), "s1": k("s1"), "s3": k("s3"), "r1": k("r1"), "r3": k("r3")}

def fmt(tag, a):
    return (f"  {tag:<26} n={a['n']:<5} strict@1 {a['s1']:5.1%}  strict@3 {a['s3']:5.1%}   "
            f"role@1 {a['r1']:5.1%}  role@3 {a['r3']:5.1%}")


# ── предсказания обоих методов на одном наборе ─────────────────────────────────
def clf_topk(model, X, nums, k=3):
    import torch
    with torch.no_grad():
        logits = model(torch.from_numpy(X))
        order = torch.argsort(logits, dim=-1, descending=True)[:, :k].numpy()
    return [[nums[int(j)] for j in row] for row in order]

def retr_topk(retriever, texts, k=3):
    out = []
    for t in texts:
        hits = retriever.search(t, k=k)
        out.append([h["num"] for h in hits])
    return out


def load_golden(valid_nums):
    g = json.loads(io.open(GOLDEN, encoding="utf-8-sig").read())["prompts"]
    items = [(p["text"], p["primary"], set(p.get("expected") or []))
             for p in g if p.get("primary") in valid_nums]
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--encoder", default=DEFAULT_ENCODER)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--hidden", type=int, default=384)
    ap.add_argument("--dropout", type=float, default=0.4)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=1e-4)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--rebuild-split", action="store_true")
    args = ap.parse_args()

    import torch
    torch.manual_seed(args.seed)

    nums, num2idx, role_by_num, target_by_num = clf.load_label_maps()
    n_classes = len(nums)

    if args.rebuild_split or not clf.SPLIT_PATH.exists():
        train, val, test = clf.build_and_save_split(seed=args.seed)
        print(f"[split] пересоздан → {clf.SPLIT_PATH.name}")
    else:
        train, val, test = clf.load_split()
    print(f"[data] классов: {n_classes} | train {len(train)} | val {len(val)} | test {len(test)}")

    # L1: эмбеддинги (e5 заморожен), кэш по сплитам
    Xtr = clf.embed_cached([q for q, _ in train], args.encoder, tag="train")
    Xva = clf.embed_cached([q for q, _ in val], args.encoder, tag="val")
    Xte = clf.embed_cached([q for q, _ in test], args.encoder, tag="test")
    ytr = np.array([num2idx[n] for _, n in train], dtype=np.int64)
    dim = Xtr.shape[1]

    # L2: обучаем голову
    model = clf.make_head(dim, n_classes, hidden=args.hidden, dropout=args.dropout)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.wd)
    lossf = torch.nn.CrossEntropyLoss()
    Xtr_t, ytr_t = torch.from_numpy(Xtr), torch.from_numpy(ytr)

    val_nums = [n for _, n in val]
    best_val, best_state, best_ep = -1.0, None, -1
    for ep in range(args.epochs):
        model.train()
        perm = torch.randperm(len(Xtr_t))
        for i in range(0, len(perm), args.batch):
            idx = perm[i:i + args.batch]
            opt.zero_grad()
            loss = lossf(model(Xtr_t[idx]), ytr_t[idx])
            loss.backward(); opt.step()
        model.eval()
        va = aggregate([score_topk(p, g, role_by_num)
                        for p, g in zip(clf_topk(model, Xva, nums), val_nums)])
        sel = va["s1"] + 0.001 * va["r1"]                  # выбор лучшего по val strict@1 (tie: role@1)
        if sel > best_val:
            best_val, best_ep = sel, ep
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    print(f"[train] лучшая эпоха {best_ep} (val strict@1 {best_val:.3f})\n")

    # retrieval-baseline (тот же e5, без обучения) — на тех же val/test/golden
    r = Retriever(encoder_name=args.encoder)
    golden = load_golden(set(nums))

    def block(title, texts, gold_nums, X=None):
        clf_p = clf_topk(model, X, nums) if X is not None else \
            clf_topk(model, clf.embed(texts, args.encoder), nums)
        retr_p = retr_topk(r, texts)
        c = aggregate([score_topk(p, g, role_by_num) for p, g in zip(clf_p, gold_nums)])
        b = aggregate([score_topk(p, g, role_by_num) for p, g in zip(retr_p, gold_nums)])
        print(title)
        print(fmt("retrieval-baseline", b))
        print(fmt("классификатор (L2)", c))
        return c, b

    print("=" * 78)
    block("TEST (self-labeled, обобщение на фразинг):", [q for q, _ in test],
          [n for _, n in test], X=Xte)
    print()
    g_texts = [t for t, _, _ in golden]
    g_nums = [pr for _, pr, _ in golden]
    c_g, b_g = block("GOLDEN (ручной held-out, primary):", g_texts, g_nums)
    # expected@k (top-1 в приемлемой семье) — мягкая метрика для golden
    g_exp = [exp for _, _, exp in golden]
    cg = clf_topk(model, clf.embed(g_texts, args.encoder), nums)
    rg = retr_topk(r, g_texts)
    e_c = sum(p[0] in exp for p, exp in zip(cg, g_exp) if exp) / max(sum(1 for e in g_exp if e), 1)
    e_b = sum(p[0] in exp for p, exp in zip(rg, g_exp) if exp) / max(sum(1 for e in g_exp if e), 1)
    print(f"  expected@1 (top-1 в семье):  retrieval {e_b:5.1%}   классификатор {e_c:5.1%}")
    print("=" * 78)

    # худшие роли классификатора на test (куда копать)
    by_role = defaultdict(lambda: [0, 0])
    for p, (_, g) in zip(clf_topk(model, Xte, nums), test):
        ok = role_by_num.get(p[0]) == role_by_num.get(g)
        by_role[role_by_num.get(g, "")][0] += ok
        by_role[role_by_num.get(g, "")][1] += 1
    worst = sorted(by_role.items(), key=lambda x: x[1][0] / max(x[1][1], 1))[:8]
    print("\nХудшие роли классификатора (role@1 на test):")
    for role, (h, t) in worst:
        print(f"  {role:<14} {h:>3}/{t:<3} = {h/t:4.0%}")

    # сохранить модель + метрики (для записки)
    test_clf = aggregate([score_topk(p, g, role_by_num)
                          for p, g in zip(clf_topk(model, Xte, nums), [n for _, n in test])])
    meta = {"test_clf": test_clf,
            "golden": {"clf": c_g, "retrieval": b_g, "expected@1_clf": e_c, "expected@1_retr": e_b},
            "epochs": args.epochs, "best_epoch": best_ep, "hidden": args.hidden}
    clf.save_model(model, nums, role_by_num, target_by_num, args.encoder, dim, args.hidden, meta=meta)
    print(f"\n[save] модель → {clf.MODEL_DIR}")


if __name__ == "__main__":
    main()
