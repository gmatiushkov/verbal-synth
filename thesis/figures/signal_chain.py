"""
Рис. 3.2 — Сигнальная цепь синтезатора (на голос + общий тракт).
Генерация схемы кодом (matplotlib). Запуск:  python signal_chain.py
Вывод: img/signal_chain.png

Примечание по инструментарию: договорённость — блок-схемы на Graphviz, но `dot` пока не установлен,
поэтому первая проба сделана на matplotlib (уже доступен). При установке Graphviz перенесём на .dot.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.join(os.path.dirname(__file__), "img")
os.makedirs(OUT, exist_ok=True)

# Цвета (нейтральные, печать на белом)
BOX_FILL = "#eef2f7"
BOX_EDGE = "#33475b"
SRC_FILL = "#e3ecf7"
FX_FILL = "#f3eee3"
TEXT = "#0f1b26"

fig, ax = plt.subplots(figsize=(6.6, 12.2))
ax.set_xlim(0, 10)
ax.set_ylim(-3.0, 10.5)
ax.axis("off")

BW, BH = 3.2, 0.78  # ширина/высота блока


def box(x, y, text, fill=BOX_FILL):
    """Прямоугольник со скруглением, центр в (x, y)."""
    p = FancyBboxPatch(
        (x - BW / 2, y - BH / 2), BW, BH,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=1.4, edgecolor=BOX_EDGE, facecolor=fill,
    )
    ax.add_patch(p)
    ax.text(x, y, text, ha="center", va="center", fontsize=10.5, color=TEXT)
    return (x, y)


def arrow(p1, p2):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle="-|>", mutation_scale=14,
        linewidth=1.3, color=BOX_EDGE, shrinkA=2, shrinkB=2,
    ))


xc = 5.0  # центральная вертикаль

# --- Источники (вверху, в ряд) ---
s1 = box(2.0, 9.7, "Осциллятор 1\n(таблица волн)", SRC_FILL)
s2 = box(5.0, 9.7, "Осциллятор 2\n(таблица волн)", SRC_FILL)
s3 = box(8.0, 9.7, "Генератор шума", SRC_FILL)

mix = box(xc, 8.3, "Микшер\n(смешивание источников)")
lp = box(xc, 7.0, "Фильтр НЧ\n(приглушает высокие)")
hp = box(xc, 5.8, "Фильтр ВЧ\n(приглушает низкие)")
amp = box(xc, 4.6, "Громкость\n(огибающая во времени)")

ssum = box(xc, 3.1, "Сумма голосов\n(многоголосие)")
drive = box(xc, 1.9, "Насыщение", FX_FILL)
rev = box(xc, 0.7, "Реверберация\n(эффект пространства)", FX_FILL)
mst = box(xc, -0.5, "Мастер-громкость")
out = box(xc, -1.9, "Выход (звук)")

# --- Стрелки ---
for s in (s1, s2, s3):
    arrow((s[0], s[1] - BH / 2), (mix[0], mix[1] + BH / 2))
for a, b in [(mix, lp), (lp, hp), (hp, amp), (amp, ssum),
             (ssum, drive), (drive, rev), (rev, mst), (mst, out)]:
    arrow((a[0], a[1] - BH / 2), (b[0], b[1] + BH / 2))

# --- Поясняющие скобки-подписи слева ---
ax.text(0.15, 6.8, "на каждый\nголос", ha="left", va="center",
        fontsize=9.5, color="#5a6b7a", rotation=90)
ax.text(0.15, 0.7, "общий\nтракт", ha="left", va="center",
        fontsize=9.5, color="#5a6b7a", rotation=90)

ax.set_title("Рис. 3.2 — Сигнальная цепь синтезатора", fontsize=12.5, color=TEXT, pad=12)

fig.tight_layout()
path = os.path.join(OUT, "signal_chain.png")
fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
print("saved:", path)
