"""The Item Potency page (Materials → Mechanics, owner 2026-11-19): every value the game flags, from the newest
patch's items.txt; the abilities that set attacks' potency from data/rules/item_potency_abilities.json; little text,
colour for meaning ("мешанина … не читается из-за обилия текста и отсутствия цветовых индикаторов")."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "builders"))


def test_what_illusions_do_not_get_is_a_dash_not_a_share():
    # owner 2026-11-21: "basher/abyssal не работает на иллюзиях, а столбец есть" — the game's notes say which
    import pytest
    import item_potency as ip
    from patch import game_files
    if not game_files.available():
        pytest.skip("no game-files store")
    v = ip._versions()[-1]
    assert set(ip.no_illusions("item_basher", v)) == {"bash"}
    assert set(ip.no_illusions("item_maelstrom", v)) == {"chain lightning"}
    assert set(ip.no_illusions("item_devastator", v)) == {"witch blade"}          # Magic Corruption still applies
    assert set(ip.no_illusions("item_orb_of_venom", v)) == {"*"}
    assert ip.no_illusions("item_skadi", v) == {}
    rows = "".join(ip._items_rows(v, {"not_in_game": []}))
    basher = rows[rows.index('data-name="skull basher"'):]
    assert basher.split("</tr>")[0].count("ipot-no-ill") == 3                    # Illusion, Manta, Rune
    skadi = rows[rows.index('data-name="eye of skadi"'):]
    assert "ipot-no-ill" not in skadi.split("</tr>")[0]


def test_every_potency_chip_is_a_number():
    # owner 2026-11-21: Falcon Rush's chip read "equal to their damage (30/35/40/45%)" — the chip says the number, the
    # words go to the "Attacks" column
    import json
    import re
    rules = json.loads((ROOT / "data" / "rules" / "item_potency_abilities.json").read_text(encoding="utf-8"))
    for slug, text in list(rules["abilities"].items()) + list(rules.get("items", {}).items()):
        what, _, val = text.partition(": ")
        assert val and re.fullmatch(r"[+\-−]?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*%", val), (slug, text)


def test_the_items_table_reads_like_the_sites_tables():
    # design review 2026-11-21: the ability once per item, centred values, the illusions apart, the hero's value on a
    # phone, the switch in the site's filter card
    import pytest
    import item_potency as ip
    from patch import game_files
    from patch.css_bundle import read_css
    if not game_files.available():
        pytest.skip("no game-files store")
    rows = "".join(ip._items_rows(ip._versions()[-1], {"not_in_game": []}))
    skadi = "".join(r for r in ip._items_rows(ip._versions()[-1], {"not_in_game": []}) if 'data-name="eye of skadi"' in r)
    assert skadi.count('<td class="ipot-ab"') == 1 and '<td class="ipot-ab" rowspan=3>Cold Attack</td>' in skadi
    assert "ipot-ill-first" in rows
    assert ip.REMOVED_BUTTON.startswith('<div class="cal-toggle-bar inbox-bar ipot-tools"><div class="toolbar-panel">')
    css = read_css()
    assert "table.mr-table.ipot-table td { text-align: center;" in css
    # the words left, one first-column width for every table (owner 2026-11-21: all centred "не очень")
    assert "table.mr-table.ipot-table thead th.ipot-th-text { text-align: left; }" in css
    assert "thead th:first-child { width: 230px; min-width: 230px; }" in css
    # melee / ranged in one row (owner 2026-11-21: "через слеш, а не в 2 строки")
    basher = "".join(r for r in ip._items_rows(ip._versions()[-1], {"not_in_game": []}) if 'data-name="skull basher"' in r)
    assert basher.count("<tr") == 1 and "Chance (melee / ranged)" in basher and ">25 / 10<" in basher
    skadi_rows = [r for r in ip._items_rows(ip._versions()[-1], {"not_in_game": []}) if 'data-name="eye of skadi"' in r]
    assert len(skadi_rows) == 3 and ">-20 / -40<" in "".join(skadi_rows) and ">-4 / -8<" in "".join(skadi_rows)
    # on a phone the ability column is squeezed, not display:none — the group row still counts it
    assert ("table.mr-table.ipot-items td.ipot-ab, table.mr-table.ipot-items tr.col-row th:nth-child(2) {\n"
            "    width: 0; min-width: 0; max-width: 0;") in css


def test_column_lines_run_through_the_rows_under_a_spanning_cell():
    # owner 2026-11-21 (Parasma, two ability rows under one item): "линия вертикальная не до конца, уже были такие
    # проблемы" — lines go by column class, so the 2nd row's first <td> (a later column) keeps its line
    from patch.css_bundle import read_css
    css = read_css()
    assert "table.mr-table.ipot-table td:not(.ipot-name) { border-left: 1px solid" in css
    assert "td:first-child { border-left: 0" not in css.split("ipot-table", 1)[1].split("@media", 1)[0]


def test_both_pages_have_the_two_floor_header_of_hero_stats():
    # owner 2026-11-21 chose variant 1 of the header mock ("давай 1 стиль"): groups over the columns, as Hero Stats and
    # Neutral Stats; no group named as the column under it ("два раза hero"); a line under a named group
    import item_potency as ip
    from patch.css_bundle import read_css
    head = ip._table("ipot-items", ["Item", "Ability", "Value", "100%", "20%"], [], [("", 3), ("Hero", 1), ("Illusions", 1)])
    assert '<thead><tr class="cat-row"><th class="cat-head" colspan="3"></th><th class="cat-head" colspan="1">Hero</th>' in head
    assert "tbl-card" not in head
    assert ip._table("x", ["Item"], []).startswith('<table class="mr-table hs-table ipot-table x"><thead><tr class="col-row">')
    aoe = (ROOT / "builders" / "aoe_increase.py").read_text(encoding="utf-8")
    assert '<tr class="cat-row"><th class="cat-head"></th>' in aoe and ">Abilities</th>" in aoe
    css = read_css()
    assert ".tbl-card" not in css
    assert "th.cat-head:not(:empty) { box-shadow: inset 0 -1px 0 var(--line-soft); }" in css
    # AoE's script freezes widths by the column row and hands them to <col>s: a fixed table reads its first row
    js = (ROOT / "src" / "js" / "aoe-increase.js").read_text(encoding="utf-8")
    assert "table.querySelectorAll('thead tr.col-row th').forEach(th => {" in js and "createElement('colgroup')" in js


def test_one_name_cell_for_items_and_heroes():
    # owner 2026-11-21: "столбец hero сделан не так, как в item potency. достичь единого формата" and the item's icon
    # grows on hover as on Mana Items (.mr-ico)
    import item_potency as ip
    from patch.css_bundle import read_css
    cell = ip._name_cell("Skadi", "", span=3)
    assert cell.startswith('<td class="mr-name hs-name ipot-name" rowspan="3"><span class="mr-ico mr-ico-blank"></span>')
    assert '<span class="mr-name-body"><span class="mr-name-text">Skadi</span></span>' in cell
    css = read_css()
    assert ".mr-table.aoe-table td.aoe-name, table.mr-table.ipot-table td.ipot-name {" in css
    assert ".mr-ico:hover {\n  transform: scale(1.8);" in css


def test_aoe_icons_name_in_the_sites_gold_tooltip():
    # owner 2026-11-21: AoE's ability icons showed the browser's grey title — the site's tooltip, gold name, as in the
    # patch tables; and the empty cells keep no background of their own (it ate the row / column hover shade)
    from patch.css_bundle import read_css
    aoe = (ROOT / "builders" / "aoe_increase.py").read_text(encoding="utf-8")
    assert '<span class="aoe-ico-wrap abil-ico-hint" data-tooltip="{tip}">' in aoe
    assert 'title="{_esc(ab["name"])}"' not in aoe
    css = read_css()
    empty = css.split(".mr-table.aoe-table td.aoe-cell-empty {", 1)[1].split("}", 1)[0]
    assert "background" not in empty


def test_cross_hover_finds_the_column_under_a_rowspan():
    # Item Potency: the 2nd row of an item starts with a later column; the hover's column is the visual one
    js = (ROOT / "src" / "js" / "tooltips.js").read_text(encoding="utf-8")
    assert "function visualColumns(table)" in js and "c.rowSpan" in js
    assert "tr.cells[idx]" not in js


def test_the_page_lists_the_flagged_values_and_the_sources():
    import item_potency
    html = item_potency.render_html()
    for title in ("How Item Potency adds up", "Items", "Attacks with their own Item Potency", "Bonuses and penalties",
                  "Illusions"):
        assert f'<h3 class="ipot-title">{title}</h3>' in html
    assert html.count('class="ipot-rule"') == 5                         # the rules as cards, not a table of text
    assert "ipot-curio" not in html                                     # Curio has its own page (owner 2026-11-21)
    # a row per value: Desolator's armour reduction, the hero's −6 and the same at 20 / 35 / 40%
    assert ">Corruption<" in html and ">-6<" in html
    assert ">-1.2<" in html and ">-2.1<" in html and ">-2.4<" in html
    assert "data-tooltip=" in html and "ipot-prop" in html              # the game's sentence in the value's hover
    assert '<span class="ipot-chip ipot-nerf">60%</span>' in html       # Swashbuckle: below 100% red
    assert '<span class="ipot-chip ipot-buff">125%</span>' in html      # Astral Step: above 100% green
    assert '<span class="ipot-chip ipot-buff">+20%</span>' in html      # Evolved: a bonus green
    # removed items: grey, hidden till "Show removed", no words (owner 2026-11-19)
    assert 'class="ipot-gone"' in html and "not in the game" not in html
    # the site's "Removed" filter button, as Neutral Stats' (owner 2026-11-21)
    assert 'class="hs-attack-filter ipot-show-gone" aria-pressed="false"><span>Removed</span></button>' in html
    assert "Pangolier" in html and "Illusion Rune" in html


def test_dormant_curio_has_its_own_page():
    # owner 2026-11-21: "Dormant Curio вынести на свою страницу"; Curio's bonus from items.txt (30% in 7.42)
    import dormant_curio
    html = dormant_curio.render_html()
    assert "<title>s/kle - Dormant Curio</title>" in html and "With Curio +30%" in html
    assert html.count("<tr data-name=") >= 10 and 'class="ipot-rule"' in html


def test_a_name_under_a_key_with_a_grammar_mark_is_found():
    # 7.42 "DOTA_Tooltip_Ability_item_riftshadow_prism:n": the page showed "item_riftshadow_prism" (owner 2026-11-21)
    from patch.loc_history import tooltip
    assert tooltip("DOTA_Tooltip_Ability_item_riftshadow_prism", "7.42") == "Riftshadow Prism"
    import item_potency
    assert ">item_riftshadow_prism<" not in item_potency.render_html()


def test_a_selected_item_of_several_rows_is_framed_as_one():
    # owner 2026-11-19, Eye of Skadi's five rows: "при выделении строки выделяет только 1 вариант"
    from patch.css_bundle import read_css
    from patch.js_bundle import read_js
    js = read_js()
    assert "r.dataset.name === name" in js and "mr-sel-top" in js and "mr-sel-bottom" in js
    css = read_css()
    assert ".mr-table tbody tr.mr-row-selected.mr-sel-top > td:first-child" in css
    assert ".mr-table tbody tr.mr-row-selected.mr-sel-bottom > td:last-child" in css
