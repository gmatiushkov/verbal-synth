#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_info.py — «ЗВУКОВОЙ БРИФ» прототипа для тюнинга на слух.

Собирает в одном месте всё, что известно про то, КАК патч должен звучать (помимо имени):
  • Замысел по осям (axis_preset из taxonomy_to_role.json) — целевое звучание.
  • Дескрипторы (народные признаки звука).
  • Как этот звук ищут пользователи (примеры формулировок из queries.json).
  • Что параметры дают СЕЙЧАС (декод attributes из params) — видно расхождение с замыслом.
  • concept (для сгенерированных) + reference-якорь (эталон для сравнения на слух).

    python ml/scripts/patch_info.py 16          # по номеру
    python ml/scripts/patch_info.py гобой        # по подстроке имени
    python ml/scripts/patch_info.py 45-49        # диапазон номеров
"""

import io
import json
import sys
from pathlib import Path

import attr_decode as ad

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "data" / "library" / "library.json"
TAX = ROOT / "config" / "v5" / "taxonomy_to_role.json"
QRS = ROOT / "data" / "library" / "queries.json"


def _load(p, default=None):
    if not Path(p).exists():
        return default
    return json.loads(io.open(p, encoding="utf-8-sig").read())


def tax_by_target():
    m = _load(TAX, {"mapping": {}})["mapping"]
    out = {}
    for items in m.values():
        for e in items:
            out[e["target"]] = e
    return out


def pick(lib, token):
    """num / диапазон 'a-b' / подстрока имени → список записей."""
    es = lib["entries"]
    token = token.strip()
    if token.isdigit():
        return [e for e in es if e["num"] == int(token)]
    if "-" in token and all(x.isdigit() for x in token.split("-", 1)):
        a, b = (int(x) for x in token.split("-", 1))
        return [e for e in es if a <= e["num"] <= b]
    low = token.lower()
    return [e for e in es if low in e["name"].lower() or low in e.get("target", "").lower()]


def brief(e, tax, qmap):
    t = tax.get(e["target"], {})
    ap = t.get("axis_preset", {})
    cur = ad.decode_all(e["params"]) if e.get("params") else {}
    qs = qmap.get(str(e["num"]), [])
    flag = "approved" if e.get("approved") else "черновик"

    print("=" * 70)
    print(f"#{e['num']:>3}  {e['target']}   [{e.get('source','?')}, {flag}]")
    print(f"     роль: {e.get('role','')}  |  банк: {e.get('bank','')}")
    if e.get("concept"):
        print(f"     concept (генерации): {e['concept']}")
    print("-" * 70)
    print("ЗАМЫСЕЛ по осям (как ДОЛЖНО звучать):")
    print("     " + ("  ".join(f"{k}={v}" for k, v in ap.items()) if ap else "— нет в таксономии"))
    print("СЕЙЧАС из параметров (для сверки):")
    print("     " + "  ".join(f"{k}={v}" for k, v in cur.items() if v))
    # подсветим расхождения замысел↔текущее по общим осям
    diverge = [k for k in ("register", "brightness", "body") if ap.get(k) and cur.get(k) and ap[k] != cur[k]]
    if diverge:
        print("     ⚠ расхождение: " + ", ".join(f"{k}: замысел {ap[k]} ≠ сейчас {cur[k]}" for k in diverge))
    print("-" * 70)
    print(f"ДЕСКРИПТОРЫ: {', '.join(e.get('descriptors', [])) or '—'}")
    ref = t.get("reference")
    if ref and str(ref).lower() not in ("none", "null", ""):
        print(f"ЭТАЛОН-ЯКОРЬ (сравнить на слух): {ref}")
    if qs:
        print(f"КАК ИЩУТ ЮЗЕРЫ ({len(qs)} формулировок, примеры):")
        print("     " + " · ".join(qs[:12]))
    print()


def main():
    if len(sys.argv) < 2:
        sys.exit("Укажи номер/диапазон/подстроку: python ml/scripts/patch_info.py 16")
    token = " ".join(sys.argv[1:])
    lib = _load(LIB)
    tax = tax_by_target()
    qmap = (_load(QRS, {}) or {}).get("entries", {})
    hits = pick(lib, token)
    if not hits:
        sys.exit(f"Ничего не найдено по «{token}».")
    for e in hits[:30]:
        brief(e, tax, qmap)
    if len(hits) > 30:
        print(f"… показано 30 из {len(hits)} (уточни запрос).")


if __name__ == "__main__":
    main()
