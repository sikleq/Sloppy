"""Tests for generate_patch_code_v2 tag heuristics and l=True logic."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from generate_patch_code_v2 import _guess_tag, LOWER_IS_BUFF, _NOT_LOWER_IS_BUFF


# ── _guess_tag: canonical phrase → expected tag ────────────────────────────

@pytest.mark.parametrize("text, expected", [
    # NEW
    ("Added to Captains Mode", "NEW"),
    ("Can now be disassembled", "NEW"),
    ("Now also grants 10% evasion", "NEW"),
    ("Added a new passive component", "NEW"),
    # DEL
    ("Removed from Captains Mode", "DEL"),
    ("No longer provides bonus damage", "DEL"),
    ("No longer applied by illusions", "DEL"),
    ("Can no longer target magic immune units", "DEL"),
    # REWORK
    ("Replaced with a new ability", "REWORK"),
    ("Reworked", "REWORK"),
    ("Rescaled from 10/20/30 to 15/25", "REWORK"),
    ("No longer levels with Duel", "REWORK"),
    ("Changed from a passive to an active", "REWORK"),
    # BUFF — direction keyword without from/to
    ("Damage increased", "BUFF"),
    ("Armor raised", "BUFF"),
    ("Range improved", "BUFF"),
    # NERF — direction keyword without from/to
    ("Damage decreased", "NERF"),
    ("Duration reduced", "NERF"),
    ("Range lowered", "NERF"),
    # MISC
    ("Fixed tooltip description", "QoL"),
    ("Fixed a bug where stun lasted too long", "MISC"),
    ("Unchanged", "MISC"),
    # TAG_OVERRIDES
    ("Now shares cooldown with Blink Dagger", "MISC"),
    ("Respawn time increased from 25 to 30", "NERF"),
    ("Respawn time decreased from 30 to 25", "BUFF"),
    ("Now requires Blade of Alacrity instead of Band of Elvenskin", "REWORK"),
    # "No longer has a penalty" → BUFF (not DEL)
    ("No longer has a movement speed penalty", "BUFF"),
    ("No longer has an attack speed debuff slow", "BUFF"),
    # from/to present → None (let b() decide)
    ("Damage increased from 100 to 120", None),
    ("Cooldown decreased from 30 to 25", None),
])
def test_guess_tag(text, expected):
    assert _guess_tag(text) == expected


# ── LOWER_IS_BUFF: keywords that flip direction ───────────────────────────

@pytest.mark.parametrize("text, should_match", [
    # Should match (l=True)
    ("Cooldown increased from 10 to 12", True),
    ("Mana Cost decreased from 100 to 80", True),
    ("Gold Cost increased from 900 to 1000", True),
    ("Base Attack Time decreased from 1.7 to 1.6", True),
    ("Cast Point increased from 0.3 to 0.4", True),
    ("Channel Time decreased from 3 to 2.5", True),
    ("Recharge Time increased from 60 to 70", True),
    ("Incoming Damage increased from 10% to 15%", True),
    ("Damage Taken increased from 5% to 8%", True),
    ("Damage Vulnerability increased from 10% to 15%", True),
    ("Building Damage Penalty decreased from 50% to 40%", True),
    ("Penalty increased from 5 to 10", True),
    ("Recipe cost decreased from 1000 to 800", True),
    ("Respawn Time increased from 25 to 30", True),
    ("Activation Time decreased from 0.5 to 0.3", True),
    ("Restore Time increased from 3 to 4", True),
    # Should NOT match (normal direction)
    ("Damage increased from 100 to 120", False),
    ("Duration increased from 4 to 5", False),
    ("Heal increased from 200 to 250", False),
    ("Bonus Agility increased from 10 to 15", False),
    ("Attack Speed increased from 30 to 40", False),
])
def test_lower_is_buff(text, should_match):
    match = bool(LOWER_IS_BUFF.search(text))
    not_excluded = not bool(_NOT_LOWER_IS_BUFF.search(text))
    result = match and not_excluded
    assert result == should_match, f"LOWER_IS_BUFF for '{text}': got {result}, expected {should_match}"


# ── _NOT_LOWER_IS_BUFF: exclusions ───────────────────────────────────────

@pytest.mark.parametrize("text", [
    "Cooldown Reduction increased from 10% to 15%",
    "Cooldown Advance increased from 2 to 3",
    "Mana Cost Reduction increased from 10% to 15%",
    "Penalty Reduction increased from 5% to 10%",
])
def test_not_lower_is_buff_exclusions(text):
    assert LOWER_IS_BUFF.search(text), f"Should match LOWER_IS_BUFF base: {text}"
    assert _NOT_LOWER_IS_BUFF.search(text), f"Should be excluded by _NOT_LOWER_IS_BUFF: {text}"
