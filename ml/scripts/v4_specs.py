#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4_specs.py — загрузчик/валидатор/резолвер спек для пайплайна датасета v4 (A6-Claude).

Звук v4 = РОЛЬ-якорь (config/v4/roles.json) + уровни ОСЕЙ (config/v4/attributes.json),
слова — в config/v4/lexicon.json. Этот модуль:
  • грузит три артефакта (utf-8-sig, терпим к BOM);
  • валидирует их взаимную согласованность против param_convert (имена/банки/конвертируемость);
  • РЕЗОЛВИТ спеку → детерминированный КАРКАС патча в реальных единицах
    (neutral_defaults ⊕ role.base ⊕ якоря выбранных осей) + множество ЗАЛОЧЕННЫХ
    параметров (банк/октава/позиция-Vocal), которые сэмплер фиксирует, а пост-обработчик
    генерации принудительно возвращает к этим значениям (гибридный режим: Claude доводит
    непрерывные параметры и пишет описания, но НЕ может увести определяющие параметры —
    это чинит «размазывание» банка/октавы, давшее потолок v3);
  • собирает ПАЛИТРУ лексикона для спеки (роль + уровни осей + характер) для промпта.

Зависит от param_convert (имена/диапазоны/конвертация — зеркало C++).
"""

import io
import json
from pathlib import Path

import param_convert as pc

ROOT = Path(__file__).resolve().parents[1]            # .../ml
V4 = ROOT / "config" / "v4"
ROLES_PATH = V4 / "roles.json"
ATTRS_PATH = V4 / "attributes.json"
LEX_PATH = V4 / "lexicon.json"


# ── загрузка ──────────────────────────────────────────────────────────────────
def _load(path):
    with io.open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def load_specs():
    """Возвращает (roles, attrs, lexicon) — словари из трёх артефактов v4."""
    roles = _load(ROLES_PATH)["roles"]
    attrs = _load(ATTRS_PATH)
    lex = _load(LEX_PATH)
    return roles, attrs, lex


# ── валидация согласованности ───────────────────────────────────────────────────
def validate(roles, attrs, lex):
    """Сквозная проверка. Возвращает список строк-проблем (пустой = ок)."""
    issues = []
    axes = attrs["axes"]
    axiskeys = set(axes.keys())

    def conv_ok(name, val):
        if name.endswith("_shape"):
            return val in pc.LFO_SHAPE_NAMES
        if name in ("osc1_table", "osc2_table"):
            return val in pc.BANK_NAMES
        try:
            pc.real_to_norm(name, val)
            return True
        except Exception:
            return False

    # роли
    for rn, r in roles.items():
        for k, v in r.get("base", {}).items():
            if k not in pc.PARAM_SPEC:
                issues.append(f"{rn}: base — неизвестный параметр {k}")
            elif not conv_ok(k, v):
                issues.append(f"{rn}: base.{k}={v} не конвертируется")
        for b in r.get("banks", []):
            if b not in pc.BANK_NAMES:
                issues.append(f"{rn}: неизвестный банк {b}")
        if not r.get("banks"):
            issues.append(f"{rn}: нет банков")
        for ax in r.get("vary_axes", []):
            if ax not in axiskeys:
                issues.append(f"{rn}: vary_axes — неизвестная ось {ax}")
        for ax, lvls in r.get("typical", {}).items():
            if ax not in axes:
                issues.append(f"{rn}: typical — неизвестная ось {ax}")
                continue
            for lv in lvls:
                if lv not in axes[ax]["levels"]:
                    issues.append(f"{rn}: typical {ax}.{lv} — нет такого уровня")
        for lv in r.get("register_range", []):
            if lv not in axes["register"]["levels"]:
                issues.append(f"{rn}: register_range — неизвестный уровень {lv}")

    # оси
    for an, a in axes.items():
        for ln, lv in a.get("levels", {}).items():
            for k, v in lv.items():
                if k not in pc.PARAM_SPEC:
                    issues.append(f"ось {an}.{ln}: неизвестный параметр {k}")
                elif not conv_ok(k, v):
                    issues.append(f"ось {an}.{ln}.{k}={v} не конвертируется")

    # лексикон
    lroles = set(lex["roles"].keys())
    for rn in roles:
        if rn not in lroles:
            issues.append(f"lexicon: у роли {rn} нет ключевых слов")
    alk = set(lex["axis_levels"].keys())
    for an, a in axes.items():
        for ln in a.get("levels", {}):
            if f"{an}.{ln}" not in alk:
                issues.append(f"lexicon: нет axis_levels[{an}.{ln}]")

    # neutral_defaults + position_semantics
    for k, v in attrs.get("neutral_defaults", {}).items():
        if k == "note":
            continue
        if k not in pc.PARAM_SPEC:
            issues.append(f"neutral_defaults: неизвестный параметр {k}")
        elif not conv_ok(k, v):
            issues.append(f"neutral_defaults.{k}={v} не конвертируется")
    for b in attrs.get("position_semantics", {}):
        if b != "note" and b not in pc.BANK_NAMES:
            issues.append(f"position_semantics: неизвестный банк {b}")

    return issues


# ── резолв спеки → каркас + locks ───────────────────────────────────────────────
# Спека (от сэмплера):
#   { "spec_id": str, "role": str, "bank": str,
#     "axis_levels": { ось: уровень, ... }   # может включать "register" и "character" }

def resolve_skeleton(spec, roles, attrs):
    """Спека → (real_params, locked, character, osc2_active).

    real_params — каркас в реальных единицах (neutral ⊕ base ⊕ якоря осей, + банк/позиция).
    locked      — {имя: значение} параметров, которые НЕЛЬЗЯ менять Claude (банк/октава/
                  для Vocal — позиция). Пост-обработчик генерации форсит их обратно.
    character   — уровень оси character или None (качественная директива, без жёстких якорей).
    osc2_active — включён ли второй осциллятор (mix_osc2 > 0).
    """
    role = roles[spec["role"]]
    bank = spec["bank"]
    real = {}

    # 1) нейтральные дефолты (фолбэк там, где спека молчит)
    for k, v in attrs.get("neutral_defaults", {}).items():
        if k != "note":
            real[k] = v
    # 2) база роли (идентичность)
    real.update(role.get("base", {}))
    # 3) якоря выбранных осей (кроме качественной character)
    character = None
    for ax, lvl in spec.get("axis_levels", {}).items():
        if ax == "character":
            character = lvl
            continue
        anchors = attrs["axes"][ax]["levels"].get(lvl, {})
        real.update(anchors)

    # 4) банк осцилляторов
    real["osc1_table"] = bank
    osc2_active = float(real.get("mix_osc2", 0) or 0) > 0
    real["osc2_table"] = bank  # держим тот же банк (при выкл. osc2 безвреден, вектор чище)

    # 5) множество локов
    locked = {
        "osc1_table": bank,
        "osc2_table": bank,
        "osc1_octave": int(real.get("osc1_octave", 0)),
    }
    if bank == "Vocal":
        # для Vocal позиция = ГЛАСНАЯ (форманта), задаётся осью vowel → залочена
        if "osc1_position" in real:
            locked["osc1_position"] = real["osc1_position"]
        if "osc2_position" in real:
            locked["osc2_position"] = real["osc2_position"]

    return real, locked, character, osc2_active


def enforce_locks(returned_real, locked):
    """Принудительно вернуть залоченные параметры к значениям спеки (поверх ответа Claude).
    Возвращает (clean_real, overrides) — overrides: какие параметры пришлось переписать."""
    out = dict(returned_real)
    overrides = {}
    for k, v in locked.items():
        cur = out.get(k)
        # сравнение банка/формы — по имени; чисел — по округлению
        changed = True
        if isinstance(v, str):
            changed = (str(cur).strip().lower() != v.strip().lower())
        elif cur is not None:
            try:
                changed = abs(float(cur) - float(v)) > 1e-6
            except (TypeError, ValueError):
                changed = True
        if changed:
            overrides[k] = (cur, v)
        out[k] = v
    return out, overrides


# ── палитра лексикона для спеки ──────────────────────────────────────────────────
def lexicon_palette(spec, lex):
    """Слова/фразы, релевантные спеке → для подсказки описаний (роль + уровни осей + характер)."""
    pal = {}
    role_words = lex["roles"].get(spec["role"])
    if role_words:
        pal[f"role:{spec['role']}"] = role_words
    for ax, lvl in spec.get("axis_levels", {}).items():
        key = f"{ax}.{lvl}"
        words = lex["axis_levels"].get(key)
        if words:
            pal[key] = words
    return pal


# ── самотест/валидация из CLI ────────────────────────────────────────────────────
def _main():
    roles, attrs, lex = load_specs()
    issues = validate(roles, attrs, lex)
    print(f"роли: {len(roles)} | оси: {len(attrs['axes'])} | "
          f"лексикон-ролей: {len(lex['roles'])} | axis_levels: {len(lex['axis_levels'])}")
    if issues:
        print(f"ПРОБЛЕМЫ ({len(issues)}):")
        for s in issues:
            print("  -", s)
        raise SystemExit(1)
    print("ISSUES: нет")

    # демо резолва на одной спеке
    demo = {"spec_id": "demo_organ_0", "role": "organ", "bank": "Organ",
            "axis_levels": {"register": "mid", "brightness": "warm",
                            "movement": "leslie", "space": "hall", "character": "epic"}}
    real, locked, char, osc2 = resolve_skeleton(demo, roles, attrs)
    print("\nДЕМО резолв (organ / mid / warm / leslie / hall / epic):")
    print("  locked:", locked)
    print("  character:", char, "| osc2_active:", osc2)
    norm = pc.patch_real_to_norm(real)
    print("  каркас конвертируется в 38 norm:", len(norm) == len(pc.PARAM_ORDER))
    print("  палитра ключей:", list(lexicon_palette(demo, lex).keys()))


if __name__ == "__main__":
    _main()
