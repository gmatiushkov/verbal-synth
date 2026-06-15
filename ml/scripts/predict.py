"""
Инференс для синта: текст → 38 нормализованных параметров (RETRIEVAL-MVP, PIVOT_RETRIEVAL.md §2).

Не генерируем патч, а ВЫБИРАЕМ ближайший эталон из library.json и отдаём его параметры КАК ЕСТЬ.
Печатает одну строку JSON {param_name: value} в порядке PARAM_ORDER — формат PresetManager
(см. MainComponent::parsePatchJson). Диагностика идёт в stderr, чтобы не мешать парсингу stdout.

Параметры читаются из library.json НА ЛЕТУ (свежий процесс на каждый клик Generate) — правки
тюнинга подхватываются без перестройки чего-либо. Кэшируются только эмбеддинги описаний.

    python predict.py "тёплый бас с лёгким перегрузом"
    echo "яркий колокольчик" | python predict.py
    python predict.py -k 5 "кислотный бас"      # top-5 в stderr (отладка), top-1 в stdout
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import param_convert as pc
from retrieval import Retriever, DEFAULT_ENCODER

try:
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def predict(text, encoder=DEFAULT_ENCODER, approved_only=False, k=1):
    """Возвращает (patch_dict_38, hits). patch_dict — params top-1 в порядке PARAM_ORDER."""
    r = Retriever(encoder_name=encoder, approved_only=approved_only)
    hits = r.search(text, k=max(k, 1))
    if not hits:
        return None, []
    params = r.params_of(hits[0]["num"])
    out = {}
    for name in pc.PARAM_ORDER:                            # стабильный порядок + клип на всякий
        v = float(params.get(name, 0.0))
        out[name] = min(max(v, 0.0), 1.0)
    return out, hits


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Retrieval-инференс: текст → параметры прототипа.")
    ap.add_argument("text", nargs="*", help="запрос (или подаётся в stdin)")
    ap.add_argument("--encoder", default=DEFAULT_ENCODER)
    ap.add_argument("--approved-only", action="store_true", help="только утверждённые прототипы")
    ap.add_argument("-k", "--topk", type=int, default=1, help="сколько кандидатов показать в stderr")
    args = ap.parse_args()

    text = " ".join(args.text).strip()
    if not text and not sys.stdin.isatty():
        text = sys.stdin.readline().strip()
    if not text:
        print(json.dumps({"error": "no text"}))
        sys.exit(1)

    patch, hits = predict(text, encoder=args.encoder, approved_only=args.approved_only, k=args.topk)
    if patch is None:
        print(json.dumps({"error": "no candidates in library"}))
        sys.exit(2)

    # Диагностика — в stderr (stdout парсит синт).
    top = hits[0]
    print(f"[retrieval] «{text}» → #{top['num']} {top['target']} "
          f"(score {top['score']}, {'approved' if top['approved'] else 'draft'})", file=sys.stderr)
    for h in hits[1:]:
        print(f"            · #{h['num']} {h['target']} ({h['score']}) ← {h['phrase']}", file=sys.stderr)

    print(json.dumps(patch, ensure_ascii=False))
