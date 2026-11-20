"""The Neutral Abilities table reads what each ability does from the game files (owner 2026-11-20: "мы разве
автоматически из патчей и файлов не должны подтягивать"). A new creep's ability with no Property fails here, not on
the page later (7.42: Odobenus Blight's row was dashes only)."""
import json
import pathlib

from builders.creeps_abilities import ABIL_MANUAL, abil_props
from builders.creeps_auto_props import auto_effects

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_property_from_the_keys_and_the_description():
    assert auto_effects({"av_armor_reduction": "2 3 4 5", "av_armor_reduction_duration": "4.0"}) == ["Armor reduction 2/3/4/5"]
    assert auto_effects({"av_stun_duration": "2", "av_impact_radius": "175"}) == ["Stun in an area"]
    assert auto_effects({"av_movespeed_slow": "15 17 19 21", "av_radius": "1200"}) == ["Slow 15/17/19/21%"]
    assert auto_effects({"av_slow": "0", "av_radius": "150"},
                        "The Radigull lays eggs, damaging and silencing nearby enemies.") == ["Silence in an area"]
    assert auto_effects({}, "Grants the unit a warm glow, of some kind.") == ["Grants the unit a warm glow"]


def test_no_row_of_the_table_has_an_empty_property():
    import re
    import pytest
    page = ROOT / "dist" / "neutral_abilities.html"
    if not page.exists():
        pytest.skip("the site is not built")
    empty = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page.read_text(encoding="utf-8"), re.S):
        cells = [re.sub(r"<[^>]+>|\s+", " ", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) > 15 and cells[2] and cells[15] in ("", "—"):
            empty.append(cells[2])
    assert not empty, empty


def test_every_neutral_ability_of_the_patch_says_what_it_does():
    cur = json.loads((ROOT / "data" / "stats" / "7.42" / "npc_abilities.json").read_text(encoding="utf-8"))
    for slug in ("odobenus_blight", "mud_golem_hurl_big_boulder", "eimermole_miners_slam", "ogre_seal_flop",
                 "radigull_eggstremism", "eimermole_miners_aura", "ogre_seal_pup_disapproval_aura"):
        assert abil_props(slug, cur)["effect"], slug
        assert "effect" not in ABIL_MANUAL.get(slug, {}), slug          # from the files, not typed by hand
    assert abil_props("mud_golem_hurl_big_boulder", cur)["duration"] == "2"     # the stun, not av_duration 1.0
