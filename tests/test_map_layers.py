"""Map layers of 2026-10-06 (owner: "все слои"): lane creep paths, river currents, shop / no-ward / Roshan pit zones,
spawn points — read from the map files (scripts/gen/extract_map_entities.py), diffed per Terrain step
(scripts/gen/build_terrain_diff.py), drawn on the Terrain pages (builders/terrain.py)."""
import glob
import json
import os
import sys

import pytest

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


def test_a_current_keeps_each_nodes_radius_and_strength():
    e = {"origin": [0.0, 0.0, 0.0], "pathnodes": [0.0] * 18, "pathnoderadiusscales": [192.0, 260.5],
         "pathnodemovespeedtypes": [2.0, 1.0]}
    cur = ext._current(e)
    assert cur["radius"] == [192.0, 260.5] and cur["types"] == [2, 1]


def test_a_current_is_turned_by_its_entity_yaw():
    """The two Dire currents of 7.41 stand at yaw 180°: their nodes are in the entity's frame (owner 2026-10-06:
    "Слой течений воды неправильный" — they were drawn mirrored, off the water)."""
    e = {"origin": [1000.0, 2000.0, 0.0], "angles": [0.0, 180.0, 0.0],
         "pathnodes": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 300.0, 50.0, 0.0, -10.0, 0.0, 0.0, 0.0, 0.0, 0.0]}
    cur = ext._current(e)
    assert [(n["x"], n["y"]) for n in cur["nodes"]] == [(1000, 2000), (700, 1950)]
    assert cur["nodes"][0]["out"] == [-10, 0]


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


def test_a_currents_max_bonus_follows_its_strength_until_7_41():
    """7.38: strong currents up to +150, moderate up to +100; 7.41: "All sections of currents now give a max
    movement speed bonus of 150" — the map files still mark them 1 / 2."""
    strong, moderate = {"types": [2, 2]}, {"types": [1, 1]}
    assert btd.current_max_bonus(strong, "740c") == 150 and btd.current_max_bonus(moderate, "740c") == 100
    assert btd.current_max_bonus(moderate, "741") == 150 and btd.current_max_bonus(moderate, "741f") == 150
    assert btd.current_max_bonus(moderate, "688") == 100              # a 6.88 code is not 7.88


def test_every_current_is_one_strength_end_to_end():
    """current_max_bonus reads one strength per current: true of every map file on the site."""
    for path in glob.glob(os.path.join(ROOT, "data", "map", "mapdata_*.json")):
        with open(path, encoding="utf-8") as f:
            for cur in json.load(f)["data"].get("dota_movespeed_modifier_path", []):
                assert len(set(cur["types"])) == 1 and len(cur["radius"]) == len(cur["nodes"]), path


def test_a_currents_zone_is_its_spline_swept_by_the_node_radius():
    pytest.importorskip("contourpy")
    src = {"dota_movespeed_modifier_path": [{
        "nodes": [{"x": 0, "y": 0, "in": [0, 0], "out": [300, 0]}, {"x": 900, "y": 0, "in": [-300, 0], "out": [0, 0]}],
        "radius": [100, 200], "types": [1, 1]}]}
    ((area),) = btd.current_areas(src, "740")
    (ring,) = area["rings"]
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    assert area["max"] == 100
    assert abs(min(xs) + 100) <= 16 and abs(max(xs) - 1100) <= 16           # the end circles: r 100 and r 200
    assert abs(max(ys) - 200) <= 16 and abs(min(ys) + 200) <= 16
    assert any(abs(x) <= 40 and 80 <= y <= 120 for x, y in ring)          # the zone narrows to r 100 at the start


def test_the_currents_layer_draws_buff_zones_by_strength_and_flow_arrows():
    svg = terrain._line_zone_svgs(terrain._load_diff("7.38"), terrain._projector(terrain._load_map_meta()))
    new = svg[svg.index("tm-layer-currents tm-new"):]
    new = new[:new.index("</svg>")]
    assert "tc-current-150" in new and "tc-current-100" in new and "tc-current-flow" in new
    svg = terrain._line_zone_svgs(terrain._load_diff("7.41"), terrain._projector(terrain._load_map_meta()))
    new = svg[svg.index("tm-layer-currents tm-new"):]
    new = new[:new.index("</svg>")]
    assert "tc-current-150" in new and "tc-current-100" not in new          # 7.41: all +150


def test_the_new_layer_chips_are_buttons_that_light_their_outlines():
    """The owner 2026-10-06: "не могу нажать Changed in the map file фильтры новых слоёв"."""
    diff = terrain._load_diff("7.40")
    html = "".join(terrain._chip(*c) for c in terrain._moved_items(diff) if c[0] in terrain._LAYER_HL)
    for key, layer in (("lanes", "lanes"), ("currents", "currents"), ("shopzones", "shops"), ("lanespawns", "lanes")):
        assert f'data-hl="{key}" data-layer="{layer}"' in html, key
        assert f"tm-hl tm-hl-{key} tm-new" in terrain._highlights_svg(diff, terrain._projector(terrain._load_map_meta())), key


def test_published_map_data_holds_no_vision_entities():
    """Vision (fog blockers, revealers) is never drawn on this site, so the site's map data leaves it out; the full
    entity lists, vision included, are in Oldgrowth (scripts/gen/oldgrowth_mapdata.py: entities.json.gz)."""
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
