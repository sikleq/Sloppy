"""Build dormant_curio.html — the "Dormant Curio" page (Materials → Mechanics). It was a folded list at the foot of
Item Potency; the owner 2026-11-21: "Dormant Curio вынести на свою страницу" — a mechanic of its own: the values an item
flags "apply_curio_bonus" grow by Curio's own "item_potency" (30% in 7.42), values above 0 only (server.dll 6983).

    python builders/dormant_curio.py
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_HERE))
_sys.path.insert(0, str(_HERE / "builders"))

from item_potency import (ITEM_CDN, _esc, _fmt, _name_cell, _num, _rules_cards, _scaled_values,  # noqa: E402
                          _section, _table, page_shell)
from heroes_stats import _versions  # noqa: E402
from patch.item_marks import _curio_pct  # noqa: E402


def _rows(version, pct):
    rows = []
    for name, _key, slug, vals in _scaled_values(version, "apply_curio_bonus"):
        for k, (ab, label, value, sentence) in enumerate(vals):
            head = _name_cell(name, f"{ITEM_CDN}{slug}.png", span=len(vals)) if k == 0 else ''
            hint = f' data-tooltip="{_esc(sentence)}"' if sentence else ''
            prop = f'<span class="{"iab-hint abil-ico-hint " if sentence else ""}ipot-prop"{hint}>{_esc(label)}</span>'
            v = _num(value)
            up = _fmt(v * (100 + pct) / 100) if v is not None and v > 0 else (value if v is not None else "—")
            rows.append(f'<tr data-name="{_esc(name.lower())}">{head}<td class="ipot-ab">{_esc(ab)}</td>'
                        f'<td class="ipot-text">{prop}</td><td class="ipot-v ipot-v-hero">{_esc(value)}</td>'
                        f'<td class="ipot-v ipot-v-up">{up}</td></tr>')
    return rows


def render_html() -> str:
    version = _versions()[-1]
    pct = _curio_pct(version)
    if pct is None:
        raise RuntimeError(f"dormant_curio.html: no item_potency of Dormant Curio in {version}'s items.txt")
    mult = (100 + pct) / 100
    rule = {"rules": [["A value Dormant Curio improves", f"Value * {mult:g}", ["40", _fmt(40 * mult), "values above 0 only"]]]}
    body = (_section("How Dormant Curio adds up", _rules_cards(rule))
            + _section("Items", _table("ipot-curio", ["Item", "Ability", "Value", "Now", f"With Curio +{pct:g}%"],
                                       _rows(version, pct), [("", 3), ("Value", 2)])))
    return page_shell("dormant_curio", "Dormant Curio", body)


def main() -> int:
    html = render_html()
    if html.count('<tr data-name=') < 10:            # a page with no rows is a broken build, not "0 results"
        raise RuntimeError("dormant_curio.html: fewer than 10 rows — the game files did not load")
    out = _HERE / "dist" / "dormant_curio.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"  -> dist/dormant_curio.html: {len(html):,} bytes ({html.count('<tr data-name=')} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
