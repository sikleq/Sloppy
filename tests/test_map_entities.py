"""Our own map data (data/map/mapdata_<code>.json), read from the game's map files by
scripts/gen/extract_map_entities.py (owner 2026-09-30: "don't depend on third-party repos")."""
import glob
import json
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
import extract_map_entities as xm  # noqa: E402

FILES = sorted(glob.glob(os.path.join(_ROOT, "data", "map", "mapdata_*.json")))


def _load(code):
    with open(os.path.join(_ROOT, "data", "map", f"mapdata_{code}.json"), encoding="utf-8") as f:
        return json.load(f)["data"]


def test_the_lump_parser_reads_both_the_new_and_the_legacy_format():
    ents = xm.parse_vents('====0====\nclassname "ent_dota_tree"\norigin [ -852.0, 4940.4, 265.3 ]\n\n'
                          '====1====\nclassname "trigger_multiple"\norigin "2560.000000 -4096.000000 -64.0"\n'
                          'model "maps\\\\dota\\\\entities\\\\neutralcamp_good_3_2699_9825.vmdl"\n')
    assert xm._xy(ents[0]) == {"x": -852, "y": 4940} and xm._xy(ents[1]) == {"x": 2560, "y": -4096}
    assert xm._model(ents[1]) == "maps/dota/entities/neutralcamp_good_3_2699_9825.vmdl"
    # a camp box = the hull's bounds around the entity (no yaw here)
    assert xm._box(ents[1], ((-10, -20), (30, 40))) == [
        {"x": 2550, "y": -4116}, {"x": 2550, "y": -4056}, {"x": 2590, "y": -4056}, {"x": 2590, "y": -4116}]


@pytest.mark.parametrize("path", FILES, ids=[os.path.basename(f) for f in FILES])
def test_every_map_has_its_forest_buildings_and_camps(path):
    with open(path, encoding="utf-8") as f:
        md = json.load(f)
    d = md["data"]
    assert md["source"].startswith("game files: maps/")
    assert len(d["ent_dota_tree"]) > 2000 and len(d["npc_dota_tower"]) == 22 and len(d["npc_dota_fort"]) == 2
    camps = d["npc_dota_neutral_spawner"]
    assert camps and all(c["triggerName"].startswith("neutralcamp") and c["neutralType"] in "0123" for c in camps)
    assert len(d["trigger_multiple"]) == len(camps)                  # a box for every camp
    assert all(t["subType"] in ("tower1", "tower2", "tower3", "tower4") for t in d["npc_dota_tower"])


def test_the_current_map_is_the_741_terrain():
    d = _load("741")
    assert len(d["ent_dota_tree"]) == 2475
    types = [c["neutralType"] for c in d["npc_dota_neutral_spawner"]]
    assert {t: types.count(t) for t in "0123"} == {"0": 6, "1": 14, "2": 6, "3": 2}
    assert len(d["npc_dota_roshan_spawner"]) == 2 and len(d["npc_dota_miniboss_spawner"]) == 2


@pytest.mark.parametrize("code,theirs", [("741", "741"), ("737", "735"), ("732", "732"), ("722", "722")])
def test_the_forest_is_the_one_the_interactive_map_has(code, theirs):
    """Same trees as leamare's export where one is cached (.cache/leamare, not committed)."""
    path = os.path.join(_ROOT, ".cache", "leamare", f"mapdata_{theirs}.json")
    if not os.path.exists(path):
        pytest.skip("no cached leamare export")
    with open(path, encoding="utf-8") as f:
        them = {(round(t["x"]), round(t["y"])) for t in json.load(f)["data"]["ent_dota_tree"]}
    ours = {(t["x"], t["y"]) for t in _load(code)["ent_dota_tree"]}
    assert ours == them
