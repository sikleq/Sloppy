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
    ("Aghanim's Scepter no longer reduces cooldown by 25s", "DEL"),
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
    # ── classes found by the 2026-09-18 datafeed proofread ──
    # removed own restriction / self-penalty → BUFF
    ("Toggling is no longer disabled by silence", "BUFF"),
    ("Can no longer be disabled by Silence", "BUFF"),
    ("Now can be toggled while silenced", "BUFF"),
    ("Raptor Dance: Can no longer be interrupted by casting Grappling Claw", "BUFF"),
    ("Activation no longer interrupts movement", "BUFF"),
    ("Land sub-ability no longer cancels channeling or interrupts movement", "BUFF"),
    ("Now can be cast without cancelling Charge of Darkness", "BUFF"),
    ("No longer has reduced movement slow against creeps", "BUFF"),
    ("No longer has illusion vision penalty", "BUFF"),
    ("No longer freezes Reincarnation cooldown while Wraith Delay is active", "BUFF"),
    ("Atrophy Aura: No longer loses cleave on death", "BUFF"),
    ("Duration is no longer decreased on Largo from his own abilities", "BUFF"),
    ("Gaining max stacks requirement for the speedup buff is removed", "BUFF"),
    # own buff / debuff becomes undispellable → BUFF; becomes dispellable / disjointable → NERF
    ("Buff is no longer dispellable", "BUFF"),
    ("Break debuff is no longer dispellable", "BUFF"),
    ("Fate's Edict that was cast on Oracle or his ally is now dispellable by enemies", "NERF"),
    ("Draw Forth initial projectile is now disjointable", "NERF"),
    # new restriction / limit / delay → NERF
    ("Now only affects enemy heroes", "NERF"),
    ("Now only available with Aghanim's Scepter", "NERF"),
    ("Now affects only attacks made on enemy heroes", "NERF"),
    ("Now has a 0.3s cast point", "NERF"),
    ("Falcon Rush: Now has an 825 break distance", "NERF"),
    ("Spellover now has a 0.1s internal cooldown", "NERF"),
    ("Effect now ends if Spirit Breaker is more than 900 units away from the target", "NERF"),
    ("Zombies summoned by the facet effect now die when Undying dies", "NERF"),
    ("The active effect may only trigger up to a maximum of 500 stacks", "NERF"),
    ("Movement is now cancelled if Magnus is interrupted", "NERF"),
    ("Now disabled by roots", "NERF"),
    ("Health regen reduction does not affect enemies in fountain", "NERF"),
    # removed capability → DEL
    ("Certain spells that are toggleable are no longer stealable", "DEL"),
    ("No longer benefits from mana cost reduction effects", "DEL"),
    ("Clones can no longer copy Bottle", "DEL"),
    ("No longer has an alt-cast", "DEL"),
    ("Defense Matrix: No longer blinks Tinker if he is rooted or leashed", "DEL"),
    # structural → REWORK
    ("Now a Universal melee hero instead of a creep", "REWORK"),
    ("Now an Agility Hero", "REWORK"),
    ("Now Spectre's ultimate ability", "REWORK"),
    ("Ability is now Innate to Spirit Bear", "REWORK"),
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
    ("Disable range decreased from 400 to 325", True),
    ("Enemy hero disable range decreased from 325 to 300", True),
    ("Damage interval improved from 1s to 0.5s", True),
    ("Attack Interval increased from 1.15s to 1.2s", True),
    ("Flight time decreased from 1.25s to 1.1s", True),
    ("Keen Eye disable duration on taking damage increased from 3s to 6s", True),
    ("Stun duration from falling off the cut tree decreased from 4s to 3s", True),
    ("Relentless slow resistance loss per enemy hero in range decreased from 20% to 10%", True),
    ("Intelligence reduction decreased from 8% to 5%", True),
    ("Creep penalty decreased from 50% to 35%", True),
    ("Max Mana Penalty increased from 10% to 10/12/14%", True),
    ("Voodoo Restoration: Mana per second rescaled from 8/12/16/20 to 9/12/15/18", True),
    ("Health Cost increased from 10% to 12%", True),
    ("Reverberate damage threshold increased from 180 to 220", True),
    # Should NOT match (normal direction)
    ("Slow per cooldown decreased from 7/8/9/10% to 4/5/6/7%", False),
    ("Level 10 Talent Time Dilation DPS Per Cooldown decreased from +9 to +6", False),
    ("Max Slow increased from 35/40/45/50% to 50%", False),
    ("Magic Resistance bonus decreased from +20% to +18%", False),
    ("Ether Blast magic damage vulnerability decreased from 40% to 30%", True),
    ("Relentless enemy search radius increased from 300 to 600", False),
    ("Dominate target unit's max health minimum increased from 1800 to 1900", False),
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
