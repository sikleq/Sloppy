"""Build item_potency.html — the "Item Potency" page (Materials → Mechanics), as AoE Increase (owner 2026-11-19).

Nothing guessed — all from the newest patch's game files and the code research of 7.42 (data/rules/
item_potency_abilities.json):
  * How it adds up: the rules with an example each;
  * Items: every value flagged ``apply_effectiveness "1"`` — the game's own tooltip sentence, the value in bold, and the
    same value at the usual potencies of illusions (20% default, Manta 35%, Illusion Rune 40%); items no one can get in
    this patch dimmed;
  * Sources: the abilities and items that set the potency of attacks — own potency, added to it, illusions;
  * Dormant Curio: the values flagged ``apply_curio_bonus`` and the same × 1.3.

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
from patch.item_ability_text import _items  # noqa: E402
from patch.item_marks import _flagged, _rows  # noqa: E402
from patch.images import abil_img  # noqa: E402
from patch.loc_history import tooltip  # noqa: E402
from heroes_stats import _display_name, _latest_href, _load_display_names, _versions  # noqa: E402

_esc = lambda s: _html.escape(str(s), quote=True)
RULES = _HERE / "data" / "rules" / "item_potency_abilities.json"
ITEM_CDN = "icons/items/"
ILLUSIONS = (("Illusions", 20), ("Manta", 35), ("Illusion Rune", 40))     # the usual potencies of an illusion
CURIO = 1.3
_BOLD = _re.compile(r"<b>([-+]?\d+(?:\.\d+)?)(%?)</b>")


def _root(src):
    return src[3:] if src.startswith("../") else src


def _scaled(text, factor):
    """The sentence's bold numbers × factor, "-4% / -8%"; '—' when it has none."""
    nums = _BOLD.findall(text)
    return " / ".join(f"{round(float(v) * factor, 2):g}{p}" for v, p in nums) if nums else "—"


def _flagged_items(version, flag):
    out = []
    for key, blk in _items(version).items():
        if not (isinstance(blk, dict) and key.startswith("item_") and not key.startswith("item_recipe")):
            continue
        keys = _flagged(blk, flag)
        if keys:
            slug = key[len("item_"):]
            name = tooltip(f"DOTA_Tooltip_Ability_{key}", version) or slug.replace("_", " ").title()
            out.append((name, key, slug, _rows(slug, version, blk, keys)))
    return sorted(out, key=lambda r: r[0].lower())


def _hero_of(ability, version, names):
    heroes = _json.loads((_HERE / "data" / "stats" / version / "heroes.json").read_text(encoding="utf-8"))
    for npc, blk in heroes.items():
        if isinstance(blk, dict) and ability in {v for k, v in blk.items()
                                                 if k.startswith("Ability") and isinstance(v, str)}:
            return _display_name(npc, names)
    return ""


def _table(cls, head, rows, title):
    th = "".join(f"<th>{h}</th>" for h in head)
    return (f'<h3 class="ipot-title">{title}</h3>'
            f'<table class="mr-table hs-table ipot-table {cls}"><thead><tr class="col-row">{th}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def _name_cell(name, icon, owner="", span=1, wide=True):
    w, h = (44, 32) if wide else (32, 32)
    rs = f' rowspan="{span}"' if span > 1 else ''
    who = f'<span class="ipot-owner">{_esc(owner)}</span>' if owner else ''
    img = f'<img src="{icon}" alt="" loading="lazy" width="{w}" height="{h}">' if icon else ''
    return f'<td class="ipot-name"{rs}>{img}<span class="ipot-nm">{_esc(name)}{who}</span></td>'


def _items_rows(version, rules):
    gone = set(rules.get("not_in_game", []))
    rows = []
    for name, key, slug, lines in _flagged_items(version, "apply_effectiveness"):
        for k, (ab, text) in enumerate(lines):
            cls = ' class="ipot-gone"' if key in gone else ''
            head = _name_cell(name + (" (not in the game)" if key in gone else ""), f"{ITEM_CDN}{slug}.png",
                              span=len(lines)) if k == 0 else ''
            ill = "".join(f'<td class="ipot-ill">{_scaled(text, p / 100)}</td>' for _, p in ILLUSIONS)
            rows.append(f'<tr{cls} data-name="{_esc(name.lower())}">{head}'
                        f'<td class="ipot-text">{f"<b>{_esc(ab)}:</b> " if ab else ""}{text}</td>{ill}</tr>')
    return rows


def _sources_rows(version, rules, names, group):
    rows = []
    for slug in rules["groups"][group]:
        text = rules["abilities"].get(slug) or rules.get("items", {}).get(slug, "")
        if slug.startswith("item_"):
            title = tooltip(f"DOTA_Tooltip_Ability_{slug}", version) or slug
            cell = _name_cell(title, f"{ITEM_CDN}{slug[len('item_'):]}.png")
        else:
            title = tooltip(f"DOTA_Tooltip_ability_{slug}", version) or slug
            cell = _name_cell(title, _root(abil_img(slug)), _hero_of(slug, version, names), wide=False)
        rows.append(f'<tr data-name="{_esc(title.lower())}">{cell}<td class="ipot-text">{_esc(text)}</td></tr>')
    if group == "illusions":
        for title, text in rules.get("other", {}).items():
            rows.append(f'<tr>{_name_cell(title, "")}<td class="ipot-text">{_esc(text)}</td></tr>')
    return rows


def _curio_rows(version):
    rows = []
    for name, key, slug, lines in _flagged_items(version, "apply_curio_bonus"):
        for k, (ab, text) in enumerate(lines):
            head = _name_cell(name, f"{ITEM_CDN}{slug}.png", span=len(lines)) if k == 0 else ''
            # only a value above 0 gets the bonus (server.dll 6983)
            nums = [(v, p) for v, p in _BOLD.findall(text)]
            up = " / ".join(f"{round(float(v) * CURIO, 2):g}{p}" if float(v) > 0 else f"{v}{p}" for v, p in nums)
            rows.append(f'<tr data-name="{_esc(name.lower())}">{head}'
                        f'<td class="ipot-text">{f"<b>{_esc(ab)}:</b> " if ab else ""}{text}</td>'
                        f'<td class="ipot-ill">{up or "—"}</td></tr>')
    return rows


def render_html() -> str:
    version = _versions()[-1]
    rules = _json.loads(RULES.read_text(encoding="utf-8"))
    names = _load_display_names()
    how = [f'<tr><td class="ipot-name"><span class="ipot-nm">{_esc(a)}</span></td><td class="ipot-text">{_esc(b)}</td>'
           f'<td class="ipot-text ipot-ex">{_esc(c)}</td></tr>' for a, b, c in rules["rules"]]
    body = (
        _table("ipot-rules", ["", "How it works", "Example"], how, "How Item Potency adds up")
        + _table("ipot-items", ["Item", "Scaled by Item Potency"] + [f"{n} ({p}%)" for n, p in ILLUSIONS],
                 _items_rows(version, rules), "Items")
        + _table("ipot-sources", ["Ability", "Item Potency of its attacks"],
                 _sources_rows(version, rules, names, "own"), "Attacks with their own Item Potency")
        + _table("ipot-sources", ["Ability", "Added to the attacker's Item Potency"],
                 _sources_rows(version, rules, names, "added"), "Bonuses and penalties")
        + _table("ipot-sources", ["Source", "Item Potency of the illusion"],
                 _sources_rows(version, rules, names, "illusions"), "Illusions")
        + _table("ipot-curio", ["Item", "Improved by Dormant Curio", f"With Dormant Curio (×{CURIO:g})"],
                 _curio_rows(version), "Dormant Curio")
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
