"""Owner 2026-09-28: the 7.38 "List of Neutral Enchantments" is one table — a row per enchantment (still its
own entity: patch squares, its Changes page), a value per tier it can be rolled at, no repeated
"Available at Tiers 1, 2, 3, and 4"."""
import re

from patch import elements as el
from patch.state import _State


def test_enchant_row_puts_each_value_under_its_tier():
    saved = (_State.current_entity_key, _State.current_patch_version, _State.block_open)
    try:
        _State.current_patch_version, _State.block_open = "7.38", False
        html = el.enchant_row("Greedy", [("GPM", ["+75", "+100"], False), ("Mana", ["+200", "+250"], False),
                                         ("Attack Damage", ["-30", "-60"], True)], [2, 3])
        assert 'id="dyn-enchant-greedy"' in html and "is-new" in html and 'data-tag="new"' in html
        gpm = re.search(r'<span class="ench-stat">GPM</span>((?:<span class="ench-v[^"]*">[^<]*</span>){5})', html).group(1)
        cells = re.findall(r'<span class="ench-v([^"]*)">([^<]*)</span>', gpm)
        assert cells == [(" ench-off", ""), ("", "+75"), ("", "+100"), (" ench-off", ""), (" ench-off", "")]
        assert '<span class="ench-stat ench-neg">Attack Damage</span>' in html
        assert "Available at" not in html
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.block_open = saved


def test_a_zero_and_a_single_value():
    saved = (_State.current_entity_key, _State.current_patch_version, _State.block_open)
    try:
        _State.current_patch_version, _State.block_open = "7.38", False
        html = el.enchant_row("Alert", [("Bonus Night Vision", ["+0", "+150", "+225", "+300"], False)], [1, 2, 3, 4])
        assert '<span class="ench-v ench-zero">—</span>' in html          # no such bonus at tier 1
        html = el.enchant_row("Keen-eyed", [("Maximum Mana", ["-15%"], True)], [2, 3])
        assert html.count('<span class="ench-v ench-neg">-15%</span>') == 2   # the same at every tier it has
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.block_open = saved
