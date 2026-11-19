"""The Item Potency page (Materials → Mechanics, owner 2026-11-19): every value the game flags, from the newest
patch's items.txt; the abilities that set attacks' potency from data/rules/item_potency_abilities.json."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "builders"))


def test_the_page_lists_the_flagged_items_and_the_sources():
    import item_potency
    html = item_potency.render_html()
    assert "Desolator" in html and "<b>-6</b>" in html and ">-1.2<" in html          # its illusion value at 20%
    assert "Swashbuckle" in html and "Slashes: 60%" in html and "Pangolier" in html
    assert "Illusion Rune" in html and "Manta Style" in html
    assert 'subtabs_active' not in html and "Item Potency" in html
    # owner 2026-11-19 "item potency улучшить намного": the rules, the usual illusion potencies, the gone items, Curio
    for title in ("How Item Potency adds up", "Attacks with their own Item Potency", "Bonuses and penalties",
                  "Illusions", "Dormant Curio"):
        assert f'<h3 class="ipot-title">{title}</h3>' in html
    assert ">-2.1<" in html and ">-2.4<" in html                      # Desolator −6 at Manta 35% and Rune 40%
    assert 'class="ipot-gone"' in html and "(not in the game)" in html
