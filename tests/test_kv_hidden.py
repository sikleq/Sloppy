"""tools/kv_hidden.py: the hidden-change check misses no change the page does not write, and keeps the noise out.
Owner 2026-11-21: "пойми, почему ты эти изменения не нашёл, улучши себя" — the 7.41 check (kv_review part 3 only)
missed Viper Strike's cast range (an ability with no row), Kinetic Fence's mana and Guardian Angel's dispel (next to a
word row), Giant's Maul and Tormentor (items and units were not compared) and Liquipedia's undocumented list."""
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.kv_hidden import entity_block, lp_lines, uncovered  # noqa: E402


def test_a_change_the_block_does_not_write_is_found():
    # 7.41 Viper: the block has no Viper Strike row at all; Disruptor's Kinetic Fence: a word row, no mana number
    viper = 'W(hero_header("Viper"))\n    W(li("Agility gain increased from 2.7 to 2.9", b(2.7, 2.9)))'
    assert uncovered({"AbilityCastRange": ("700 800 900", "750")}, viper) == {"AbilityCastRange": ("700 800 900", "750")}
    fence = 'W(li("Formation Delay increased from 0.4s to 1s", b(0.4, 1)))'
    assert "AbilityManaCost" in uncovered({"AbilityManaCost": ("50", "70")}, fence)
    # a flag has no number: always a candidate (7.41 Guardian Angel can no longer be dispelled)
    assert uncovered({"SpellDispellableType": ("SPELL_DISPELLABLE_YES", "SPELL_DISPELLABLE_NO")}, "x")


def test_what_the_page_writes_is_not_a_candidate():
    block = ('W(li("Base Damage increased by 3", bstat_h(…)))\n'
             'W(li("No longer provides +7 Intelligence", t("DEL")))\n'
             'W(li("Cast Range increased from 150 to 175", b(150, 175)))')
    assert not uncovered({"AttackDamageMin": ("22", "25")}, block)             # the step of one number
    assert not uncovered({"bonus_int": ("7", "0")}, block)                      # a value gone to 0
    assert not uncovered({"AbilityCastRange.value": ("150", "175")}, block)     # the new numbers


def test_the_noise_is_left_out():
    talents = {"special_bonus_unique_brewmaster_2"}
    assert not uncovered({
        "duration.special_bonus_facet_x_y": ("+1", None),                          # an aspect's key (7.41)
        "enemy_slow": ("-20 -25 -30 -35", "-20 -25 -30"),                          # a level no one reaches
        "AbilityBehavior": ("DOTA_ABILITY_BEHAVIOR_PASSIVE", "DOTA_ABILITY_BEHAVIOR_PASSIVE | "
                                                             "DOTA_ABILITY_BEHAVIOR_HIDDEN"),  # a UI flag
        "pierce_units": (None, "0"),                                               # a new key of 0
        "radius_treant": ("0", None),                                              # a key of 0 removed
        "duration.special_bonus_unique_brewmaster_7": ("+1.5", None),              # a talent the tree lacks
        "Ability13": ("special_bonus_a", "special_bonus_b"),                       # a slot swap: its row
        "damage.apply_curio_bonus": (None, "1"),
    }, "W(li(\"x\"))", talents)
    # a behaviour flag a word row states (7.41e Zeus "Toggling on/off no longer breaks invisibility …")
    zeus = 'W(li("Toggling on/off no longer breaks invisibility and can be done while silenced", t("MISC")))'
    assert not uncovered({"AbilityBehavior": ("TOGGLE", "TOGGLE | IGNORE_SILENCE | IGNORE_INVISIBLE")}, zeus)
    assert uncovered({"AbilityBehavior": ("TOGGLE", "TOGGLE | IGNORE_SILENCE")}, "W(li(\"x\"))")
    shard = 'W(li("No longer upgraded with Aghanim\'s Shard", t("DEL")))'
    assert not uncovered({"shard_bonus_damage.special_bonus_shard": ("125", None)}, shard)


def test_a_summon_is_found_in_its_heros_block():
    blocks = {"beastmaster": 'W(ability("Summon Razorback"))\n W(li("Boar\'s armor increased by 1", …))'}
    assert "Razorback" in entity_block(blocks, "Razorback")
    assert not uncovered({"ArmorPhysical": ("0", "1")}, entity_block(blocks, "Razorback"))


def test_liquipedias_undocumented_lines_are_read(tmp_path):
    text = ("{{VersionTableStart}}\n{{VersionTableElement|7.41|\n* Increased base damage.\n"
            "* {{cf|U}} {{A|Morphling|Morph}}\n** The {{Symbol|Target|Unit}} target's primary attribute is now "
            "{{H|Morphling}}'s.\n* {{undocumented}} {{cf|changed}} shop category from A to B.\n}}\n"
            "{{VersionTableElement|7.40|\n* {{cf|U}} older\n}}")
    with gzip.open(tmp_path / "Morphling_Changelogs.txt.gz", "wt", encoding="utf-8") as f:
        f.write(text)
    got = lp_lines("7.41", tmp_path)
    assert got == [("Morphling", "[U] Morph / The target's primary attribute is now Morphling's.")]
