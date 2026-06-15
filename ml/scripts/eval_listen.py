"""
Прослушка обученной модели.

Прогоняет набор СВОБОДНЫХ фраз (которых нет в датасете дословно) через
predict.py и выгружает результат как патчи [VAL]_*.json в Release/Patches —
загрузи их в синте и послушай, осмысленно ли звучит генерация.

    python eval_listen.py
    python eval_listen.py --out "C:\\путь\\к\\Patches"
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from predict import predict

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "build" / "VerbalSynth_artefacts" / "Release" / "Patches"

# Тестовые фразы — разные категории/регистры/характеры.
PROMPTS = [
    "тёплый аналоговый бас с лёгким перегрузом",
    "яркий хрустальный колокольчик с длинным эхом",
    "космический эмбиент-пэд, медленно дышит",
    "острый резкий пилообразный лид для транса",
    "глубокий суб-бас для трэпа",
    "нежное электропиано с мягкой атакой",
    "агрессивный расстроенный reese-бас, грязный",
    "стеклянный пэд с медленным движением тембра",
    "короткий сухой деревянный плак",
    "тревожный диссонансный хоррор-дрон",
    "звонкий синт-кик для хауса",
    "флейта с придыханием, воздушная",
]


def slug(s):
    s = re.sub(r"[^a-zа-яё0-9]+", "_", s.lower()).strip("_")
    return s[:40]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--prefix", default="[VAL]_")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for p in PROMPTS:
        params = predict(p)
        fn = out / f"{args.prefix}{slug(p)}.json"
        fn.write_text(json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  → {fn.name}")
    print(f"\n{len(PROMPTS)} патчей выгружено в {out}")


if __name__ == "__main__":
    main()
