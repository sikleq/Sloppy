"""Build item_potency.html — the "Item Potency" page (Materials → Mechanics), as AoE Increase (owner 2026-11-19).

Little text, colour for meaning (owner 2026-11-19: "мешанина … не читается из-за обилия текста и отсутствия цветовых
индикаторов"):
  * rules as cards — a short title, the formula in the site's formula look, an example before → after;
  * items: one row per scaled value — ability, the value's name (the game's tooltip sentence in its hover), the value
    for a hero (100%) and the same at the usual potencies of illusions (20% default, Manta 35%, Illusion Rune 40%);
    items no one can get in this patch dimmed;
  * sources: what sets the potency of attacks, the potency as a chip — green above 100% / a bonus, red below / a
    penalty;
  * Dormant Curio: the values it raises and the same × 1.3.
Data: the newest patch's items.txt flags (apply_effectiveness / apply_curio_bonus) and the code research of 7.42
(data/rules/item_potency_abilities.json). Nothing guessed.

    python builders/item_potency.py
"""
from __future__ import annotations

import html as _html
import json as _json
import re as _re
import sys as _sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_HERE))
_sys.path.insert(0, str(_HERE / "builders"))

import patch.site_common as _site  # noqa: E402
from patch.formula_rows import _fmt_formula  # noqa: E402
from patch.item_ability_text import _clean, _fill, _items, _values  # noqa: E402
from patch.item_marks import _flagged, _sentences  # noqa: E402
from patch.images import abil_img  # noqa: E402
from patch.loc_history import tooltip  # noqa: E402
from heroes_stats import _display_name, _latest_href, _load_display_names, _versions  # noqa: E402

_esc = lambda s: _html.escape(str(s), quote=True)
RULES = _HERE / "data" / "rules" / "item_potency_abilities.json"
ITEM_CDN = "icons/items/"
ILLUSIONS = (("Illusion", 20), ("Manta", 35), ("Rune", 40))     # the usual potencies of an illusion
CURIO = 1.3


def _root(src):
    return src[3:] if src.startswith("../") else src


def _num(v):
    try:
        return float(str(v).split("/")[0])
    except ValueError:
        return None


def _fmt(x):
    return f"{round(x, 2):g}"


def _label(key, ability):
    """"cold_slow_melee" → "Slow (melee)" — the value's own name, its ability's words dropped."""
    words = key.split("_")
    side = [w for w in words if w in ("melee", "ranged")]
    words = [w for w in words if w not in ("melee", "ranged")]
    # only the ability's first word: "cold_slow" / "cold_attack_slow" are the move and the attack slow (Eye of Skadi)
    first = (ability.lower().split() or [""])[0]
    if len(words) > 1 and words[0] == first:
        words = words[1:]
    text = " ".join(words).capitalize() or key
    return f"{text} ({side[0]})" if side else text


def _scaled_values(version, flag):
    """[(item name, item key, slug, [(ability, label, value, sentence)])] of every item with a value flagged so."""
    out = []
    for key, blk in _items(version).items():
        if not (isinstance(blk, dict) and key.startswith("item_") and not key.startswith("item_recipe")):
            continue
        keys = _flagged(blk, flag)
        if not keys:
            continue
        slug = key[len("item_"):]
        vals = _values(blk)
        desc = tooltip(f"DOTA_Tooltip_Ability_{key}_Description", version) or ""
        sents = _sentences(desc)
        rows = []
        for k in keys:
            hit = next(((n, s) for n, s in sents if _re.search(rf"%{k}%", s, _re.I)), ("", ""))
            text = _fill(hit[1], vals) if hit[1] else None
            ab = hit[0] or (rows[-1][0] if rows else (sents[0][0] if sents else ""))   # a value no sentence names
            rows.append((ab, _label(k, ab), vals.get(k, "?"), _clean(text) if text else ""))
        name = tooltip(f"DOTA_Tooltip_Ability_{key}", version) or slug.replace("_", " ").title()
        out.append((name, key, slug, rows))
    return sorted(out, key=lambda r: r[0].lower())


def _hero_of(ability, version, names):
    heroes = _json.loads((_HERE / "data" / "stats" / version / "heroes.json").read_text(encoding="utf-8"))
    for npc, blk in heroes.items():
        if isinstance(blk, dict) and ability in {v for k, v in blk.items()
                                                 if k.startswith("Ability") and isinstance(v, str)}:
            return _display_name(npc, names)
    return ""


def _section(title, table):
    return f'<section class="ipot-sec"><h3 class="ipot-title">{title}</h3>{table}</section>'


def _table(cls, head, rows):
    th = "".join(f"<th>{h}</th>" for h in head)
    return (f'<table class="mr-table hs-table ipot-table {cls}"><thead><tr class="col-row">{th}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def _name_cell(name, icon, owner="", span=1, wide=True):
    w, h = (44, 32) if wide else (32, 32)
    rs = f' rowspan="{span}"' if span > 1 else ''
    who = f'<span class="ipot-owner">{_esc(owner)}</span>' if owner else ''
    img = f'<img src="{icon}" alt="" loading="lazy" width="{w}" height="{h}">' if icon else ''
    return f'<td class="ipot-name"{rs}><span class="ipot-nm-wrap">{img}<span class="ipot-nm">{_esc(name)}{who}</span></span></td>'


def _chip(text):
    """"60%" / "+20%" / "125%" / "−25%" → a chip in the colour of what it does to items: above 100% or a bonus green,
    below or a penalty red, other text plain."""
    m = _re.search(r"([+\-−]?)(\d+(?:\.\d+)?)%", text)
    tone = ""
    if m:
        sign, v = m.group(1), float(m.group(2))
        tone = ("buff" if sign == "+" else "nerf" if sign in "-−" and sign else
                "buff" if v > 100 else "nerf" if v < 100 else "")
    return f'<span class="ipot-chip{f" ipot-{tone}" if tone else ""}">{_esc(text)}</span>'


def _rules_cards(rules):
    cards = []
    for title, formula, (a, b, what) in rules["rules"]:
        ex = (f'<span class="ipot-ex-old">{_esc(a)}</span> → <span class="ipot-ex-new">{_esc(b)}</span>'
              f'<span class="ipot-ex-what">{_esc(what)}</span>')
        cards.append(f'<div class="ipot-rule"><div class="ipot-rule-h">{_esc(title)}</div>'
                     f'<code class="formula-expr">{_fmt_formula(formula)}</code><div class="ipot-rule-ex">{ex}</div></div>')
    return f'<div class="ipot-rules">{"".join(cards)}</div>'


def _items_rows(version, rules):
    gone = set(rules.get("not_in_game", []))
    rows = []
    for name, key, slug, vals in _scaled_values(version, "apply_effectiveness"):
        for k, (ab, label, value, sentence) in enumerate(vals):
            cls = ' class="ipot-gone"' if key in gone else ''
            head = _name_cell(name, f"{ITEM_CDN}{slug}.png", "not in the game" if key in gone else "",
                              span=len(vals)) if k == 0 else ''
            hint = f' data-tooltip="{_esc(sentence)}"' if sentence else ''
            prop = f'<span class="{"iab-hint abil-ico-hint " if sentence else ""}ipot-prop"{hint}>{_esc(label)}</span>'
            v = _num(value)
            ill = "".join(f'<td class="ipot-v ipot-v-ill">{_fmt(v * p / 100) if v is not None else "—"}</td>'
                          for _, p in ILLUSIONS)
            rows.append(f'<tr{cls} data-name="{_esc(name.lower())}">{head}<td class="ipot-ab">{_esc(ab)}</td>'
                        f'<td class="ipot-text">{prop}</td><td class="ipot-v ipot-v-hero">{_esc(value)}</td>{ill}</tr>')
    return rows


def _sources_rows(version, rules, names, group):
    rows = []
    for slug in rules["groups"][group]:
        text = rules["abilities"].get(slug) or rules.get("items", {}).get(slug, "")
        what, _, val = text.partition(": ")
        if slug.startswith("item_"):
            title = tooltip(f"DOTA_Tooltip_Ability_{slug}", version) or slug
            cell = _name_cell(title, f"{ITEM_CDN}{slug[len('item_'):]}.png")
        else:
            title = tooltip(f"DOTA_Tooltip_ability_{slug}", version) or slug
            cell = _name_cell(title, _root(abil_img(slug)), _hero_of(slug, version, names), wide=False)
        rows.append(f'<tr data-name="{_esc(title.lower())}">{cell}<td class="ipot-text">{_esc(what)}</td>'
                    f'<td class="ipot-v">{_chip(val or what)}</td></tr>')
    if group == "illusions":
        for title, text in rules.get("other", {}).items():
            what, _, val = text.partition(": ")
            rows.append(f'<tr>{_name_cell(title, "")}<td class="ipot-text">{_esc(what if val else "")}</td>'
                        f'<td class="ipot-v">{_chip(val or what)}</td></tr>')
    return rows


def _curio_rows(version):
    rows = []
    for name, key, slug, vals in _scaled_values(version, "apply_curio_bonus"):
        for k, (ab, label, value, sentence) in enumerate(vals):
            head = _name_cell(name, f"{ITEM_CDN}{slug}.png", span=len(vals)) if k == 0 else ''
            hint = f' data-tooltip="{_esc(sentence)}"' if sentence else ''
            prop = f'<span class="{"iab-hint abil-ico-hint " if sentence else ""}ipot-prop"{hint}>{_esc(label)}</span>'
            v = _num(value)
            up = _fmt(v * CURIO) if v is not None and v > 0 else (value if v is not None else "—")   # above 0 only
            rows.append(f'<tr data-name="{_esc(name.lower())}">{head}<td class="ipot-ab">{_esc(ab)}</td>'
                        f'<td class="ipot-text">{prop}</td><td class="ipot-v ipot-v-hero">{_esc(value)}</td>'
                        f'<td class="ipot-v ipot-v-up">{up}</td></tr>')
    return rows


def render_html() -> str:
    version = _versions()[-1]
    rules = _json.loads(RULES.read_text(encoding="utf-8"))
    names = _load_display_names()
    head_items = ["Item", "Ability", "Value", "Hero"] + [f"{n} {p}%" for n, p in ILLUSIONS]
    body = (
        _section("How Item Potency adds up", _rules_cards(rules))
        + _section("Items", _table("ipot-items", head_items, _items_rows(version, rules)))
        + _section("Attacks with their own Item Potency", _table(
            "ipot-sources", ["Ability", "Attacks", "Item Potency"], _sources_rows(version, rules, names, "own")))
        + _section("Bonuses and penalties", _table(
            "ipot-sources", ["Source", "Attacks", "Item Potency"], _sources_rows(version, rules, names, "added")))
        + _section("Illusions", _table(
            "ipot-sources", ["Source", "Illusions", "Item Potency"], _sources_rows(version, rules, names, "illusions")))
        + _section("Dormant Curio", _table(
            "ipot-curio", ["Item", "Ability", "Value", "Now", f"With Curio ×{CURIO:g}"], _curio_rows(version)))
    )
    nav = _site.render_top_nav('materials', _latest_href(), patch_context=False, subtabs_active='item_potency',
                               subnav_in_header=False)
    subnav = _site.render_materials_subnav('item_potency')
    asset_version = _site.compute_asset_version()
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<title>s/kle - Item Potency</title>\n'
        + _site.head_common() +
        f'<link rel="stylesheet" href="styles.css?v={asset_version}">\n'
        '</head>\n<body>\n'
        f'{nav}\n'
        '<div class="container creeps-page">\n'
        '<div class="sticky-frame hs-sticky-frame"></div>\n'
        '<div class="creeps-scroll">\n'
        f'{subnav}<div class="ipot-page">{body}</div>\n'
        '</div>\n</div>\n'
        f'<script defer src="src/scripts-table.js?v={asset_version}"></script>\n'
        '</body>\n</html>\n'
    )


def main() -> int:
    html = render_html()
    if html.count('<tr data-name=') < 10:            # a page with no rows is a broken build, not "0 results"
        raise RuntimeError("item_potency.html: fewer than 10 rows — the game files did not load")
    out = _HERE / "dist" / "item_potency.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"  -> dist/item_potency.html: {len(html):,} bytes ({html.count('<tr data-name=')} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
