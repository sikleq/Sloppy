"""The Creeps table calls every creep what the game calls it (owner 2026-10-25: "Satyr Tormenter in one place, Satyr
Hellcaller in another"; "Mud Golem Splinter > Shard Golem"; then all 26 older names: "измени, как в игре")."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from builders import creeps  # noqa: E402
from builders.creeps import CREEP_DISPLAY_NAMES  # noqa: E402


def test_satyr_and_shard_golem_use_the_game_names():
    assert CREEP_DISPLAY_NAMES["npc_dota_neutral_satyr_hellcaller"] == "Satyr Tormenter"
    assert CREEP_DISPLAY_NAMES["npc_dota_neutral_mud_golem_split"] == "Shard Golem"


def test_every_creep_has_the_game_name():
    differ = {npc: (ours, creeps.game_unit_name(npc)) for npc, ours in CREEP_DISPLAY_NAMES.items()
              if creeps.game_unit_name(npc) and ours != creeps.game_unit_name(npc)}
    assert not differ, differ
