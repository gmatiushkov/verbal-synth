#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
retrieval.py — ЯДРО retrieval-MVP (PIVOT_RETRIEVAL.md §2 фаза 1, §4).

Запрос пользователя → энкодер → косинус к ОПИСАНИЯМ прототипов из library.json → top-k прототип.
Идентичность не генерируется, а ВЫБИРАЕТСЯ из ручной библиотеки; параметры берём как есть.

Ключевые решения:
  • Мульти-фразовый матчинг: у прототипа НЕ один склеенный документ, а список фраз
    ([target] + descriptors). Сходство прототипа = МАКСИМУМ косинуса по его фразам.
    Это и есть «много формулировок на прототип» (§4) и устойчивость к разбавлению:
    «acid bass» матчит фразу «кислотный бас», не теряясь среди прочих descriptors.
  • Параметры читаются ИЗ library.json НА ЛЕТУ (свежая загрузка на каждый процесс).
    Кэшируются только ЭМБЕДДИНГИ семантики (descriptors), они меняются редко — кэш
    инвалидируется по хэшу контента+энкодера. Правка params тюнером кэш НЕ трогает.
  • Кандидаты — только прототипы с непустыми params (нечего отдавать без них).

Используется predict.py (инференс для синта) и eval_retrieval.py (метрика identity).

    from retrieval import Retriever
    r = Retriever()
    hits = r.search("кислотный бас", k=3)   # [{num,name,target,score,phrase}, ...]
"""

import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]                 # .../ml
LIB = ROOT / "data" / "library" / "library.json"
QUERIES = ROOT / "data" / "library" / "queries.json"       # синонимы-формулировки (gen_queries.py), опц.
CACHE_DIR = ROOT / "models"

# e5-base выбран A/B-замером на golden (strict 92.5% vs MiniLM 81.1%, top-3 100%) — PIVOT_RETRIEVAL.md §5.
# e5 требует асимметричных префиксов query:/passage: (см. ENCODER_PREFIXES) — учтено.
DEFAULT_ENCODER = "intfloat/multilingual-e5-base"

# Вес матча по СИНОНИМАМ (gen_queries.py) относительно точных target/descriptors (вес 1.0).
# 0 = синонимы (gen_queries.py) ВЫКЛЮЧЕНЫ. Замер показал: с e5 они избыточны — strict на golden
# одинаков при 0 и 0.9 (92.5%), а на жаргонных запросах (tb303/хувер/вобл/сингинг-боул) выбор тоже
# не меняется (e5 уже кроет это через target+descriptors). Вес 1.0 даже РОНЯЛ strict до 84.9% (шум).
# Инфраструктура весов + queries.json сохранены: пригодятся для более слабого/быстрого энкодера.
DEFAULT_SYN_WEIGHT = 0.0

# Префиксы для e5/bge-стиля энкодеров (asymmetric). Для MiniLM-paraphrase — пусто.
# Подбираются в A/B (PIVOT_RETRIEVAL.md §5); ключ — имя энкодера (substring).
ENCODER_PREFIXES = {
    "e5": ("query: ", "passage: "),
    "bge-m3": ("", ""),               # bge-m3 без префиксов
    "bge": ("query: ", ""),
}


def load_library(path=LIB):
    return json.loads(io.open(path, encoding="utf-8-sig").read())


def entry_phrases(entry, extra=None):
    """Фразы прототипа для матчинга = имя цели + descriptors + синонимы (extra), без дублей."""
    phrases, seen = [], set()
    for p in [entry.get("target", "")] + list(entry.get("descriptors", [])) + list(extra or []):
        p = (p or "").strip()
        key = p.lower()
        if p and key not in seen:
            seen.add(key)
            phrases.append(p)
    return phrases


def _prefixes(encoder_name):
    for k, (q, d) in ENCODER_PREFIXES.items():
        if k in encoder_name:
            return q, d
    return "", ""


class Retriever:
    """Поиск ближайшего прототипа по описаниям. Эмбеддинги фраз кэшируются на диск."""

    def __init__(self, encoder_name=DEFAULT_ENCODER, approved_only=False, lib_path=LIB,
                 syn_weight=DEFAULT_SYN_WEIGHT):
        self.encoder_name = encoder_name
        self.lib = load_library(lib_path)
        self.q_prefix, self.d_prefix = _prefixes(encoder_name)
        self.syn_weight = syn_weight                       # вес матча по синонимам (<1 → точные фразы важнее)

        # Синонимы-формулировки (gen_queries.py) — опционально, по num прототипа.
        # syn_weight<=0 полностью отключает синонимы (только target+descriptors).
        self.queries = {}
        if QUERIES.exists() and syn_weight > 0:
            self.queries = json.loads(io.open(QUERIES, encoding="utf-8-sig").read()).get("entries", {})

        # Кандидаты: только с непустыми params (иначе нечего отдавать синту).
        self.entries = [e for e in self.lib["entries"]
                        if e.get("params") and (e.get("approved") or not approved_only)]

        # Плоский список фраз + владелец + ВЕС (target/descriptors=1.0, синонимы=syn_weight).
        self.phrases, self.owner, weights = [], [], []
        for ei, e in enumerate(self.entries):
            base = entry_phrases(e)                         # target + descriptors
            base_keys = {p.lower() for p in base}
            syns = [s for s in entry_phrases({"descriptors": self.queries.get(str(e["num"]), [])})
                    if s.lower() not in base_keys]          # синонимы без дублей с base
            for ph in base:
                self.phrases.append(ph); self.owner.append(ei); weights.append(1.0)
            for ph in syns:
                self.phrases.append(ph); self.owner.append(ei); weights.append(self.syn_weight)
        self.owner = np.asarray(self.owner, dtype=np.int64)
        self.weights = np.asarray(weights, dtype=np.float32)

        self._enc = None                                    # ленивый энкодер (запросы/сборка кэша)
        self.emb = self._load_or_encode()                  # (n_phrases, dim), L2-норм.

    # ── кэш эмбеддингов фраз ──────────────────────────────────────────────
    def _cache_path(self):
        safe = self.encoder_name.replace("/", "_")
        return CACHE_DIR / f"retrieval_{safe}.npz"

    def _content_hash(self):
        h = hashlib.sha256()
        h.update(self.encoder_name.encode("utf-8"))
        h.update(self.d_prefix.encode("utf-8"))
        for ph in self.phrases:
            h.update(ph.encode("utf-8"))
            h.update(b"\x00")
        return h.hexdigest()

    def _load_or_encode(self):
        ch = self._content_hash()
        cache = self._cache_path()
        if cache.exists():
            d = np.load(cache, allow_pickle=True)
            if str(d.get("hash")) == ch:
                return d["emb"].astype(np.float32)
        emb = self._encode([self.d_prefix + p for p in self.phrases])
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.savez(cache, emb=emb, hash=np.array(ch), name=np.array(self.encoder_name))
        return emb

    def _encode(self, texts):
        from sentence_transformers import SentenceTransformer
        if self._enc is None:
            self._enc = SentenceTransformer(self.encoder_name)
        return self._enc.encode(texts, batch_size=64, convert_to_numpy=True,
                                normalize_embeddings=True, show_progress_bar=False).astype(np.float32)

    # ── поиск ─────────────────────────────────────────────────────────────
    def search(self, text, k=3):
        """top-k прототипов: max-pool косинуса по фразам каждого прототипа."""
        if not self.entries:
            return []
        q = self._encode([self.q_prefix + text.strip()])[0]   # (dim,) L2-норм.
        sims = (self.emb @ q) * self.weights                   # косинус × вес фразы (синонимы <1)
        # Свести фразы к прототипам максимумом.
        n = len(self.entries)
        best = np.full(n, -1.0, dtype=np.float32)
        best_ph = np.zeros(n, dtype=np.int64)
        for i, oi in enumerate(self.owner):
            if sims[i] > best[oi]:
                best[oi] = sims[i]
                best_ph[oi] = i
        order = np.argsort(-best)[:k]
        out = []
        for ei in order:
            e = self.entries[int(ei)]
            out.append({
                "num": e["num"],
                "name": e["name"],
                "target": e.get("target", ""),
                "score": round(float(best[ei]), 4),
                "phrase": self.phrases[int(best_ph[ei])],
                "approved": bool(e.get("approved")),
            })
        return out

    def params_of(self, num):
        for e in self.entries:
            if e["num"] == num:
                return e["params"]
        return None
