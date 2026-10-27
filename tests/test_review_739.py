"""Owner's review of 7.39 (2026-10-27), each rule in the generator / the renderers so the next patch gets it too."""
import pytest

import tools.generate_patch_code_v2 as g
from patch import ability_kv, elements
from patch.cards_aghs import _AGHS_REWORK_RE


@pytest.mark.parametrize("text", [
    "Wyrm's Wrath: Instead of reducing Healing, Health Regen, Lifesteal, and Spell Lifesteal by 14/21/28/35%, now reduces "
    "Health Restoration by 14/21/28/35%",
    "Aghanim's Scepter instead of reducing Healing, Health Regen, Lifesteal, and Spell Lifesteal by 10% per stack, now "
    "reduces Health Restoration by 10% per stack",
    "Hobble 40% Healing, Health Regen, Lifesteal and Spell Lifesteal reductions replaced with a new 40% Health "
    "Restoration reduction stat",
])
def test_a_renamed_heal_mechanic_with_the_same_numbers_is_misc(text):
    assert g._guess_tag(text) == "MISC"


def test_a_renamed_heal_mechanic_with_new_numbers_stays_a_change():
    assert g._guess_tag("Instead of increasing Healing, Health Regen, Lifesteal, and Spell Lifesteal by 50%, now "
                        "increases Health Restoration by 30/40/50/60%") == "REWORK"


@pytest.mark.parametrize("text", [
    "Added an auto-cast. Right-click the ability to make Bristleback automatically cast it whenever it's possible",
    "Astral Spirit no longer automatically rejoins Elder Titan on collision with him. Now requires the duration to run "
    "out or the Return ability to be cast",
])
def test_control_conveniences_are_qol(text):
    assert g._guess_tag(text) == "QoL"


def test_a_card_summary_does_not_repeat_its_header():
    """The header says what the ability levels with ("Passive – shares level with Duel"); the summary is the canonical
    "Innate reworked." / "Ability reworked." (owner 2026-10-27, Outfight Them! 7.39 said "levels up with Duel" twice)."""
    import ast
    import glob
    import os
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = []
    for path in glob.glob(os.path.join(root, "content", "p*.py")):
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "ability_change":
                s = next((k.value.value for k in n.keywords if k.arg == "summary" and isinstance(k.value, ast.Constant)), "")
                if re.search(r"\b(?:levels? up with|scales with|shares level)\b", s or "", re.I):
                    bad.append(f"{os.path.basename(path)}:{n.lineno} {s}")
    assert not bad, bad


def test_now_granted_by_aghanims_hides_under_its_card(monkeypatch):
    """7.39 Fan of Knives: "Now granted by Aghanim's Scepter" + the card "Added Aghanim's Scepter." said it twice."""
    from patch import cards_aghs
    from patch.state import _State
    flags = {("phantom_assassin_fan_of_knives", "7.39"): "scepter", ("phantom_assassin_fan_of_knives", "7.38c"): "shard"}
    monkeypatch.setattr(cards_aghs, "_granted_flag", lambda s, v: flags.get((s, v)))
    monkeypatch.setattr(_State, "current_ability_slug", "phantom_assassin_fan_of_knives")
    monkeypatch.setattr(_State, "current_patch_version", "7.39")
    assert cards_aghs._granted_now_covered("Now granted by Aghanim's Scepter")
    assert not cards_aghs._granted_now_covered("Now granted by Aghanim's Shard")     # the files say Scepter
    flags[("phantom_assassin_fan_of_knives", "7.38c")] = "scepter"                  # nothing moved: the row stays
    assert not cards_aghs._granted_now_covered("Now granted by Aghanim's Scepter")


def test_losing_the_blink_overshoot_penalty_is_a_buff():
    # a click past max range used to blink 75% of it (owner 2026-10-27)
    assert g._guess_tag("Blink no longer has an overshoot range") == "BUFF"


def test_aghanims_upgrade_reworked_makes_a_card_too():
    assert _AGHS_REWORK_RE.match("Aghanim's Shard upgrade reworked: Removes the 20 stack limit")   # Batrider 7.39
    assert _AGHS_REWORK_RE.match("Aghanim's Scepter reworked: Silences when the target is alone")


def test_an_innate_with_nothing_to_cast_is_passive():
    assert ability_kv._kind("DOTA_ABILITY_BEHAVIOR_NOT_LEARNABLE", innate=True) == "Passive"
    assert ability_kv._kind("DOTA_ABILITY_BEHAVIOR_NOT_LEARNABLE") == ""
    assert ability_kv._kind("DOTA_ABILITY_BEHAVIOR_NO_TARGET", innate=True) == "Active"


def test_a_facet_card_takes_the_kind_of_the_ability_it_changes(monkeypatch):
    blocks = {"disruptor_electromagnetic_repulsion": {"Innate": "1", "AbilityBehavior": "DOTA_ABILITY_BEHAVIOR_NOT_LEARNABLE",
                                                      "AbilityValues": {"x": {"special_bonus_facet_disruptor_conduit": "1"}}},
              "disruptor_thunder_strike": {"AbilityBehavior": "DOTA_ABILITY_BEHAVIOR_UNIT_TARGET"}}
    monkeypatch.setattr(ability_kv, "_hero_blocks", lambda v: blocks)
    assert ability_kv.facet_ability("disruptor_conduit", "7.39") == "disruptor_electromagnetic_repulsion"
    head, _ = elements._facet_pane(["Increases the max level of Electromagnetic Repulsion to 4."], "disruptor_conduit",
                                   "7.39")
    assert '<b class="iab-kind">Passive</b>' in head
    # the text's own kind wins
    head, _ = elements._facet_pane(["Active. Pushes enemies away."], "disruptor_conduit", "7.39")
    assert '<b class="iab-kind">Active</b>' in head and "Passive" not in head
