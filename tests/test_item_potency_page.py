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
    assert 'class="ipot-gone"' in html and "not in the game" in html
    assert "Pangolier" in html and "Illusion Rune" in html
