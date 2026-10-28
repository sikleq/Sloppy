"""Proofread of 7.37e (2026-10-28), each rule in the generator so the next patch gets it too."""
import pytest

import tools.generate_patch_code_v2 as g


@pytest.mark.parametrize("text, tag", [
    ("Natural Order: Enemies that leave the AoE now lose 1 stack per second instead of all stacks instantly", "BUFF"),
    ("Now also applies to units under Lycan's control. Bonus is still based on Lycan's level", "BUFF"),
    ("Chain Frost: If the affected hero dies and buys back, Chain Frost will no longer follow that hero", "DEL"),
    ("Presence of the Dark Lord: Now Bonus Armor Reduction buff is removed when Shadow Fiend dies", "NERF"),
    ("Rolling Thunder: Turn Rate bonus changed from flat +110 to +40% (results in +48)", "NERF"),
    ("Nature's Call: Treant gold bounty rescaled from 18-24 on all levels to 16/24/32/40", "NERF"),
    ("Imps no longer explode if killed by enemy heroes", "DEL"),
    ("Eidolon gold bounty increased from 14-20 to 17-20", "NERF"),
    ("Stroke of Fate: Improved behavior when casting at maximum cast range", "QoL"),   # owner 2026-10-28
])
def test_7_37e_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


@pytest.mark.parametrize("text", [
    "Aghanim's Scepter charge restoration time increased from 60s to 70/65/60s",
    "Outgoing Spell Damage reflected increased from 20% to 21%",
])
def test_own_waits_and_self_damage_are_lower_is_better(text):
    assert "l=True" in g._emit_badge(text)


def test_an_old_min_max_range_is_compared_by_its_middle():
    """Owner 2026-10-28: "Treant gold bounty rescaled from 18-24 on all levels to 16/24/32/40" — a % per level against
    the middle of 18-24, not a bare tag; the enemy's gold, so lower is better."""
    text = "Nature's Call: Treant gold bounty rescaled from 18-24 on all levels to 16/24/32/40"
    assert g._emit_badge(text, hero_side=True) == "b(21, [16, 24, 32, 40], l=True)"
    assert g._emit_badge("Eidolon gold bounty increased from 14-20 to 17-20", hero_side=True) == "br(14, 20, 17, 20, l=True)"


def test_an_enemy_damage_reflection_stays_higher_is_better():
    assert "l=True" not in g._emit_badge("Damage reflected increased from 10% to 12%")
