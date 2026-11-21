"""The Item Potency page (Materials → Mechanics, owner 2026-11-19): every value the game flags, from the newest
patch's items.txt; the abilities that set attacks' potency from data/rules/item_potency_abilities.json; little text,
colour for meaning ("мешанина … не читается из-за обилия текста и отсутствия цветовых индикаторов")."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "builders"))


def test_the_page_lists_the_flagged_values_and_the_sources():
    import item_potency
    html = item_potency.render_html()
    for title in ("How Item Potency adds up", "Items", "Attacks with their own Item Potency", "Bonuses and penalties",
                  "Illusions", "Dormant Curio"):
        assert f'<h3 class="ipot-title">{title}</h3>' in html
    assert html.count('class="ipot-rule"') == 6                         # the rules as cards, not a table of text
    # a row per value: Desolator's armour reduction, the hero's −6 and the same at 20 / 35 / 40%
    assert ">Corruption<" in html and ">-6<" in html
    assert ">-1.2<" in html and ">-2.1<" in html and ">-2.4<" in html
    assert "data-tooltip=" in html and "ipot-prop" in html              # the game's sentence in the value's hover
    assert '<span class="ipot-chip ipot-nerf">60%</span>' in html       # Swashbuckle: below 100% red
    assert '<span class="ipot-chip ipot-buff">125%</span>' in html      # Astral Step: above 100% green
    assert '<span class="ipot-chip ipot-buff">+20%</span>' in html      # Evolved: a bonus green
    # removed items: grey, hidden till "Show removed", no words (owner 2026-11-19)
    assert 'class="ipot-gone"' in html and "not in the game" not in html and 'class="ipot-show-gone"' in html
    assert "Pangolier" in html and "Illusion Rune" in html


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
