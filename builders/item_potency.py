"""Build item_potency.html — the "Item Potency" page (Materials → Mechanics), as AoE Increase (owner 2026-11-19).

Three tables, nothing guessed:
  * items: every value the newest patch's items.txt flags ``apply_effectiveness "1"`` — the game's own tooltip
    sentence with the value in bold, and the same value on a default illusion (20% Item Potency);
  * abilities: the abilities that set the Item Potency of attacks (data/rules/item_potency_abilities.json, from the
    code of 7.42);
  * illusions: their Item Potency by creator.
How it works (value × potency / 100, sources added up) is in the owner's mechanics notes, not on the page
(page descriptions removed 2026-09-25, owner).

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
from patch.item_marks import ILLUSION_POTENCY, _flagged, _illusion_row, _rows  # noqa: E402
from patch.images import abil_img  # noqa: E402
from patch.loc_history import tooltip  # noqa: E402
from heroes_stats import _display_name, _latest_href, _load_display_names, _versions  # noqa: E402

_esc = lambda s: _html.escape(str(s), quote=True)
RULES = _HERE / "data" / "rules" / "item_potency_abilities.json"
ITEM_CDN = "icons/items/"


def _root(src):
    """An icon path written for dist/patches/ ("../icons/…") as the root page sees it."""
    return src[3:] if src.startswith("../") else src


def _item_rows(version):
    out = []
    for key, blk in _items(version).items():
        if not (isinstance(blk, dict) and key.startswith("item_") and not key.startswith("item_recipe")):
            continue
        keys = _flagged(blk, "apply_effectiveness")
        if not keys:
            continue
        slug = key[len("item_"):]
        name = tooltip(f"DOTA_Tooltip_Ability_{key}", version) or slug.replace("_", " ").title()
        lines = []
        for ab, text in _rows(slug, version, blk, keys):
            ill = _re.sub(r"<[^>]+>", "", _illusion_row(text)).replace("Illusions: ", "")
            lines.append((ab, text, ill))
        out.append((name, slug, lines))
    return sorted(out, key=lambda r: r[0].lower())


def _hero_of(ability, version, names):
    heroes = _json.loads((_HERE / "data" / "stats" / version / "heroes.json").read_text(encoding="utf-8"))
    for npc, blk in heroes.items():
        if isinstance(blk, dict) and ability in {v for k, v in blk.items()
                                                 if k.startswith("Ability") and isinstance(v, str)}:
            return _display_name(npc, names)
    return ""


def _table(cls, head, rows):
    th = "".join(f"<th>{h}</th>" for h in head)
    return (f'<table class="mr-table hs-table ipot-table {cls}"><thead><tr class="col-row">{th}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def render_html() -> str:
    version = _versions()[-1]
    rules = _json.loads(RULES.read_text(encoding="utf-8"))
    names = _load_display_names()

    items = []
    for name, slug, lines in _item_rows(version):
        # a row per sentence, the item's cell over all of them: each value beside its illusion value
        for k, (ab, text, ill) in enumerate(lines):
            head = (f'<td class="ipot-name" rowspan="{len(lines)}"><img src="{ITEM_CDN}{slug}.png" alt="" '
                    f'loading="lazy" width="44" height="32">{_esc(name)}</td>') if k == 0 else ''
            attr = f' data-name="{_esc(name.lower())}"' if k == 0 else ' class="ipot-cont"'
            items.append(f'<tr{attr}>{head}<td class="ipot-text">{f"<b>{_esc(ab)}:</b> " if ab else ""}{text}</td>'
                         f'<td class="ipot-ill">{ill or "—"}</td></tr>')

    abilities = []
    for slug, text in rules["abilities"].items():
        title = tooltip(f"DOTA_Tooltip_ability_{slug}", version) or slug
        hero = _hero_of(slug, version, names)
        abilities.append(f'<tr data-name="{_esc(title.lower())}"><td class="ipot-name">'
                         f'<img src="{_root(abil_img(slug))}" alt="" loading="lazy" width="32" height="32">'
                         f'{_esc(title)}<span class="ipot-owner">{_esc(hero)}</span></td>'
                         f'<td class="ipot-text">{_esc(text)}</td></tr>')
    for slug, text in rules.get("items", {}).items():
        title = tooltip(f"DOTA_Tooltip_Ability_{slug}", version) or slug
        abilities.append(f'<tr data-name="{_esc(title.lower())}"><td class="ipot-name">'
                         f'<img src="{ITEM_CDN}{slug[len("item_"):]}.png" alt="" loading="lazy" width="44" '
                         f'height="32">{_esc(title)}</td><td class="ipot-text">{_esc(text)}</td></tr>')
    for title, text in rules.get("other", {}).items():
        abilities.append(f'<tr><td class="ipot-name">{_esc(title)}</td><td class="ipot-text">{_esc(text)}</td></tr>')

    body = (_table("ipot-items", ["Item", "Scaled by Item Potency", f"Illusions ({ILLUSION_POTENCY}%)"], items)
            + _table("ipot-sources", ["Ability", "Item Potency of attacks"], abilities))

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
        f'{subnav}{body}\n'
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
