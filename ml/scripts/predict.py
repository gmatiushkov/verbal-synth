"""
Инференс для синта: текст → 38 нормализованных параметров.

Каскад (см. записку, L1→L4):
  L1 запрос → эмбеддинг e5 (заморожен) → L2 ОБУЧАЕМЫЙ классификатор → прототип (#N)
  L3 прототип → ручные 38 параметров из library.json → L4 детерминированные модификаторы.

Метод по умолчанию — классификатор (clf), если модель обучена (ml/models/clf); иначе retrieval
(ближайший эталон по косинусу) как fallback/baseline. Классификатор ест ПОЛНЫЙ запрос (без
вырезания слов): прилагательные обработаны в контексте при обучении, identity-split не нужен.

Печатает одну строку JSON {param_name: value} в порядке PARAM_ORDER — формат PresetManager
(см. MainComponent::parsePatchJson). Диагностика идёт в stderr, чтобы не мешать парсингу stdout.
Параметры читаются из library.json НА ЛЕТУ (свежий процесс на каждый клик) — правки тюнинга
подхватываются без перестройки.

    python predict.py "тёплый бас с лёгким перегрузом"
    echo "яркий колокольчик" | python predict.py
    python predict.py --method retrieval "кислотный бас"   # сравнить с baseline
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import clf
import param_convert as pc
from clf import Classifier
from modifiers import apply_modifiers, strip_modifier_words
from retrieval import Retriever, DEFAULT_ENCODER

try:
    # stdout ОБЯЗАТЕЛЬНО UTF-8: синт читает его как UTF-8, а --explain содержит кириллицу/«→».
    # Без этого на Windows stdout=cp1251 и печать JSON падает с UnicodeEncodeError (пустой вывод).
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


# Единицы для лога режима разработчика (реальные единицы из param_convert).
_UNITS = {"lp_cutoff": "Гц", "hp_cutoff": "Гц", "amp_attack": "с", "amp_decay": "с", "amp_release": "с",
          "amp_sustain": "%", "fenv_attack": "с", "fenv_decay": "с", "fenv_release": "с", "fenv_sustain": "%",
          "drive_amount": "%", "drive_tone": "%", "reverb_mix": "%", "reverb_time": "%", "reverb_damp": "%",
          "lp_resonance": "Q", "hp_resonance": "Q", "osc1_octave": "окт", "osc2_semitones": "пт",
          "osc2_detune": "цент", "fenv_amount": "окт", "lfo1_rate": "Гц", "lfo2_rate": "Гц"}


def _format_log(e):
    """Готовый человекочитаемый блок лога (UTF-8 → JSON → синт). Формируем в Python, чтобы
    кириллица не зависела от кодировки C++-литералов (MSVC их корёжит)."""
    L = ["=" * 60, f"ЗАПРОС: «{e['query']}»"]
    if e["identity_query"] != e["query"]:
        line = f"Идентичность (для поиска): «{e['identity_query']}»"
        if e["stripped"]:
            line += f"   (убраны: {' '.join(e['stripped'])})"
        L.append(line)
    method = "классификатор (L2)" if e.get("method") == "clf" else "retrieval (baseline)"
    L.append(f"МЕТОД: {method}")
    sc_label = "prob" if e.get("method") == "clf" else "score"
    L += ["", f"TOP-3 КАНДИДАТА ({'вероятность' if e.get('method') == 'clf' else 'косинус'}):"]
    for i, h in enumerate(e["retrieval"]):
        mark = ">>" if i == 0 else "  "
        appr = "approved" if h["approved"] else "draft"
        L.append(f"  {mark} #{h['num']}  {h['target']}   "
                 f"[role={h['role']}, bank={h['bank']}, {sc_label}={h['score']}, {appr}]")
    L += ["", "ВЫЧЛЕНЕНО (модификаторы из запроса): "
          + (", ".join(e["modifiers"]) if e["modifiers"] else "—")]
    L += ["", "ИЗМЕНЕНИЯ ПАРАМЕТРОВ ЭТАЛОНА:"]
    if not e["changes"]:
        L.append("  (без изменений — эталон отдан как есть)")
    else:
        for c in e["changes"]:
            L.append(f"  {c['param']}:  {c['before_real']} → {c['after_real']} {c['unit']}")
    L.append("")
    return "\n".join(L)


def _build_explain(text, ident, hits, before, after, applied, method="clf"):
    changes = []
    for name in pc.PARAM_ORDER:
        b, a = before.get(name), after.get(name)
        if b is None or a is None or abs(float(a) - float(b)) <= 1e-4:
            continue
        changes.append({"param": name, "unit": _UNITS.get(name, ""),
                        "before_real": round(pc.norm_to_real(name, b), 3),
                        "after_real": round(pc.norm_to_real(name, a), 3),
                        "before_norm": round(float(b), 4), "after_norm": round(float(a), 4)})
    iw = set(ident.split())
    top = hits[0]
    explain = {
        "query": text, "identity_query": ident, "method": method,
        "stripped": [w for w in text.split() if w not in iw],
        "retrieval": [{"num": h["num"], "target": h["target"], "role": h.get("role", ""),
                       "bank": h.get("bank", ""), "score": h["score"], "approved": h["approved"]} for h in hits],
        "chosen": {"num": top["num"], "target": top["target"], "role": top.get("role", ""),
                   "bank": top.get("bank", ""), "score": top["score"], "approved": top["approved"]},
        "modifiers": applied, "changes": changes,
    }
    explain["log"] = _format_log(explain)                 # готовый текст для dev-окна (UTF-8 через JSON)
    return explain


def _clf_hits(text, k):
    """Классификатор (L2): полный запрос → top-k прототипов, обогащённых данными библиотеки."""
    C = Classifier()
    ent = clf.entries_by_num()
    hits = []
    for c in C.predict(text, k=k):
        e = ent.get(c["num"], {})
        hits.append({"num": c["num"], "name": e.get("name", ""), "target": e.get("target", ""),
                     "role": e.get("role", ""), "bank": e.get("bank", ""),
                     "score": c["prob"], "phrase": "", "approved": bool(e.get("approved"))})
    return hits, ent


def predict(text, encoder=DEFAULT_ENCODER, approved_only=False, k=1, modifiers=True, method=None):
    """Возвращает (patch_dict_38, hits, applied, explain).
    method: 'clf' (обученная голова, по умолчанию если есть модель) | 'retrieval' (baseline)."""
    if method is None:
        method = "clf" if Classifier.exists() else "retrieval"

    if method == "clf":
        # классификатор видит ПОЛНЫЙ запрос (без identity-split) — прилагательные учтены в контексте
        hits, ent = _clf_hits(text, max(k, 3))
        if not hits:
            return None, [], [], None
        ident = text
        before = dict(ent[hits[0]["num"]]["params"])
    else:
        r = Retriever(encoder_name=encoder, approved_only=approved_only)
        # retrieval по идентичности: убираем слова-модификаторы, чтобы прилагательные не уводили выбор
        ident = strip_modifier_words(text) if modifiers else text
        hits = r.search(ident, k=max(k, 3))
        if not hits:
            return None, [], [], None
        before = dict(r.params_of(hits[0]["num"]))

    params, applied = (apply_modifiers(before, text) if modifiers else (before, []))
    out = {}
    for name in pc.PARAM_ORDER:                            # стабильный порядок + клип на всякий
        v = float(params.get(name, 0.0))
        out[name] = min(max(v, 0.0), 1.0)
    explain = _build_explain(text, ident, hits, before, params, applied, method=method)
    return out, hits, applied, explain


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Retrieval-инференс: текст → параметры прототипа.")
    ap.add_argument("text", nargs="*", help="запрос (или подаётся в stdin)")
    ap.add_argument("--encoder", default=DEFAULT_ENCODER)
    ap.add_argument("--approved-only", action="store_true", help="только утверждённые прототипы")
    ap.add_argument("-k", "--topk", type=int, default=3, help="сколько кандидатов показать в stderr")
    ap.add_argument("--no-modifiers", action="store_true", help="отключить модификаторы параметров (L4)")
    ap.add_argument("--method", choices=["clf", "retrieval"], default=None,
                    help="clf (обученная голова, по умолч.) | retrieval (baseline)")
    ap.add_argument("--explain", action="store_true",
                    help="печатать {params, explain} (для режима разработчика синта)")
    args = ap.parse_args()

    text = " ".join(args.text).strip()
    if not text and not sys.stdin.isatty():
        text = sys.stdin.readline().strip()
    if not text:
        print(json.dumps({"error": "no text"}))
        sys.exit(1)

    patch, hits, applied, explain = predict(text, encoder=args.encoder, approved_only=args.approved_only,
                                            k=args.topk, modifiers=not args.no_modifiers, method=args.method)
    if patch is None:
        print(json.dumps({"error": "no candidates in library"}))
        sys.exit(2)

    # Диагностика — в stderr (stdout парсит синт).
    top = hits[0]
    sc = "prob" if explain["method"] == "clf" else "score"
    if explain["identity_query"] != text:
        print(f"[identity]  «{text}» → ищем «{explain['identity_query']}»", file=sys.stderr)
    print(f"[{explain['method']}] «{text}» → #{top['num']} {top['target']} "
          f"({sc} {top['score']}, {'approved' if top['approved'] else 'draft'})", file=sys.stderr)
    for h in hits[1:]:
        print(f"            · #{h['num']} {h['target']} ({sc} {h['score']})", file=sys.stderr)
    if applied:
        print(f"[modifiers] применены: {', '.join(applied)}", file=sys.stderr)

    # stdout: для синта — плоский патч; с --explain — {params, explain} (режим разработчика).
    if args.explain:
        print(json.dumps({"params": patch, "explain": explain}, ensure_ascii=False))
    else:
        print(json.dumps(patch, ensure_ascii=False))
