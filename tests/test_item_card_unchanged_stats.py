"""Owner 2026-09-27: a "before -> after" item card lists ALL the item's stats — the unchanged ones
come from the game's items.txt of both patches (data/rules/item_stat_lines.json)."""
import re

from patch import elements as el
from patch.state import _State


def _rows(name, version, old, new):
    _State.current_entity_key, _State.current_entity_display = f"item|{name.lower()}", name
    _State.current_patch_version = version
    return el._unchanged_stat_rows(old, new)


def test_mage_slayer_738_shows_magic_resistance_and_mana_regen_on_both_sides():
    rows = _rows("Mage Slayer", "7.38", [("NERF", "+45 Attack Speed"), ("DEL", "+10 Intelligence")],
                 [("", "+30 Attack Speed"), ("NEW", "+5 Health Regen"), ("NEW", "+8 Damage")])
    assert ("", "+20% Magic Resistance") in rows and ("", "+2 Mana Regen") in rows
    assert not any("Attack Speed" in r[1] or "Damage" in r[1] for r in rows)   # named rows aren't repeated


def test_bloodstone_738_right_pane_shows_the_stats_of_this_patch():
    # the only change is a removed stat: the right pane still lists the item's current stats (dimmed)
    _rows("Bloodstone", "7.38", [], [])
    html = el.properties_change(old=[("DEL", "+75 AoE radius increase")], new=[])
    assert "old-only" not in html and 'class="properties-pane pane-new"' in html
    new = html.split("pane-new")[1]
    assert "+450 Health" in new and "property-same" in new


def test_a_row_repeated_on_both_sides_untagged_is_dimmed():
    # Abyssal Blade 7.38: "+35 Damage" -> "+35 Damage" is unchanged, like the stats added from items.txt
    _rows("Abyssal Blade", "7.38", [], [])
    html = el.properties_change(old=[("", "+35 Damage"), ("BUFF", "+10 Strength")],
                                new=[("", "+35 Damage"), ("", "+26 Strength")])
    for pane in html.split("properties-arrow"):
        assert re.search(r'property-text property-same"[^>]*>\+35 Damage<', pane)
        assert pane.find("Strength") < pane.find("+35 Damage")        # changed pairs first


def test_an_active_number_is_not_a_stat_line():
    # Dagon's nuke damage / Ethereal Blade's projectile speed must never show as "+400 Damage"
    rows = _rows("Ethereal Blade", "7.40", [], [])
    assert not any("Projectile" in r[1] for r in rows)
