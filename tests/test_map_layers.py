"""Map layers of 2026-10-06 (owner: "все слои"): lane creep paths, river currents, shop / no-ward / Roshan pit zones,
spawn points — read from the map files (scripts/gen/extract_map_entities.py), diffed per Terrain step
(scripts/gen/build_terrain_diff.py), drawn on the Terrain pages (builders/terrain.py)."""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "gen"))

import build_terrain_diff as btd  # noqa: E402
import extract_map_entities as ext  # noqa: E402
from builders import terrain  # noqa: E402


def test_a_three_quoted_value_spans_lines():
    text = ('====1====\nclassname "dota_movespeed_modifier_path"\norigin [ 10.0, 20.0, 0.0 ]\npathnodes """\n[\n'
            '\t[ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 0.0, 0.0, ],\n\t[ 100.0, 0.0, 0.0, -5.0, 0.0, 0.0, 0.0, 0.0, 0.0, ],\n'
            ']\n"""\nhammeruniqueid "1:2"\n')
    (e,) = ext.parse_vents(text)
    assert e["hammeruniqueid"] == "1:2"                      # the entity goes on after the block
    cur = ext._current(e)
    assert [(n["x"], n["y"]) for n in cur["nodes"]] == [(10, 20), (110, 20)]
    assert cur["nodes"][0]["out"] == [5, 0] and cur["nodes"][1]["in"] == [-5, 0]


def test_a_lane_path_follows_the_corner_chain_from_its_spawner():
    src = {"npc_dota_spawner": [{"x": 0, "y": 0, "team": "good", "lane": "top", "first": "c1"}],
           "path_corner": [{"x": 0, "y": 100, "name": "c1", "next": "c2"}, {"x": 50, "y": 200, "name": "c2", "next": "c1"},
                           {"x": 9, "y": 9, "name": "elsewhere", "next": ""}]}
    (lane,) = btd.lane_paths(src)
    assert lane["points"] == [[0, 0], [0, 100], [50, 200]]   # a loop back to c1 stops the walk


def test_a_current_is_sampled_along_its_spline_end_to_end():
    src = {"dota_movespeed_modifier_path": [{"nodes": [{"x": 0, "y": 0, "in": [0, 0], "out": [30, 0]},
                                                        {"x": 90, "y": 0, "in": [-30, 0], "out": [0, 0]}]}]}
    (pts,) = btd.current_paths(src, steps=4)
    assert pts[0] == [0, 0] and pts[-1] == [90, 0] and len(pts) == 5
    assert all(p[1] == 0 for p in pts)                       # a straight spline stays on its line


def test_published_map_data_holds_no_vision_entities():
    """Vision (fog blockers, revealers) is not published on this site: those entities live only in the private
    store next to the map files (extract_map_entities --store, ents/<sha8>.json.gz)."""
    for path in glob.glob(os.path.join(ROOT, "data", "map", "mapdata_*.json")):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        assert "fow" not in text.lower(), os.path.basename(path)


def test_the_site_maps_carry_the_new_layers():
    with open(os.path.join(ROOT, "data", "map", "mapdata_741.json"), encoding="utf-8") as f:
        d = json.load(f)["data"]
    assert len(d["npc_dota_spawner"]) == 6 and len(d["path_corner"]) == 62
    assert len(d["dota_movespeed_modifier_path"]) == 5 and len(d["trigger_shop"]) == 5


def test_7_38c_shows_its_top_lane_path_change():
    """7.38c "The Top Lane creep paths have been slightly adjusted": both top lanes changed in the map file."""
    chips = [c for c in terrain._moved_items(terrain._load_diff("7.38c")) if c[0] == "lane paths"]
    assert chips == [("lane paths", "changed", 2, 0, 6)]


def test_new_layers_are_drawn_per_side():
    svg, _counts = terrain._markers_svg(terrain._load_diff("7.41"))
    for key in ("lanes", "currents", "shops", "spawns"):
        assert f"tm-layer-{key} tm-old" in svg and f"tm-layer-{key} tm-new" in svg, key
