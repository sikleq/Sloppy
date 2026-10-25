"""The Creeps table calls a creep what the game and the patch pages call it (owner 2026-10-25: "Satyr Tormenter in one
place, Satyr Hellcaller in another"; "Mud Golem Splinter > Shard Golem")."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from builders.creeps import CREEP_DISPLAY_NAMES  # noqa: E402


def test_satyr_and_shard_golem_use_the_game_names():
    assert CREEP_DISPLAY_NAMES["npc_dota_neutral_satyr_hellcaller"] == "Satyr Tormenter"
    assert CREEP_DISPLAY_NAMES["npc_dota_neutral_mud_golem_split"] == "Shard Golem"
    assert "Satyr Hellcaller" not in CREEP_DISPLAY_NAMES.values()
    assert "Mud Golem Splinter" not in CREEP_DISPLAY_NAMES.values()
