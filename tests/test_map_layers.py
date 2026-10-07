"""Map layers of 2026-10-06 (owner: "все слои"): lane creep paths, river currents, shop / no-ward / Roshan pit zones,
spawn points — read from the map files (scripts/gen/extract_map_entities.py), diffed per Terrain step
(scripts/gen/build_terrain_diff.py), drawn on the Terrain pages (builders/terrain.py)."""
import glob
import json
import math
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


def test_the_lanes_button_explains_its_colours():
    """The owner 2026-10-06: "что значат красная/зелёные линии?"."""
    html = "".join(part for part in terrain._controls_html() if isinstance(part, str))
    btn = html[html.index('data-layer="lanes"'):]
    title = btn[btn.index('title="') + 7:]
    title = title[:title.index('"')]
    assert "green solid" in title and "red dashed" in title and "Ancient" in title


def test_each_waves_path_runs_into_the_enemy_base_to_its_ancient():
    """Why red dashed lines stand alone in the Radiant base: a Dire wave's path goes on past the Radiant barracks (where
    the Radiant waves spawn) to the Radiant Ancient."""
    src = json.load(open(os.path.join(ROOT, "data", "map", "mapdata_740c.json"), encoding="utf-8"))["data"]
    forts = {("good" if f["x"] < 0 else "bad"): (f["x"], f["y"]) for f in src["npc_dota_fort"]}
    for p in btd.lane_paths(src):
        enemy = forts["bad" if p["team"] == "good" else "good"]
        x, y = p["points"][-1]
        assert abs(x - enemy[0]) < 600 and abs(y - enemy[1]) < 600, p["team"] + p["lane"]


def test_a_lane_chip_marks_only_the_stretches_that_changed_in_their_sides_colour():
    """The owner 2026-10-06 (whole changed paths in yellow): "слишком много желтых линий… не понимаю, какая к чему
    относится". 7.41 moved 9 corners of 4 paths: Dire bot 3, Dire top 1, Radiant bot 1, Radiant top 4."""
    import math

    def length(run):
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(run, run[1:]))
    diff = terrain._load_diff("7.41")
    stretches = terrain._lane_stretches(diff)
    assert len(stretches) == 4
    # Dire top / Radiant bot: one corner moved 200 units ALONG the line — only the dropped detour is marked, not the lane
    short = [s for s in stretches if not s[2]]
    assert len(short) == 2 and all(len(s[1]) == 1 and length(s[1][0]) < 400 for s in short)
    svg = terrain._highlights_svg(diff, terrain._projector(terrain._load_map_meta()))
    new = svg[svg.index("tm-hl tm-hl-lanes tm-new"):]
    new = new[:new.index("</svg>")]
    assert f'stroke="{terrain._LANE_COLOUR["good"]}"' in new and f'stroke="{terrain._LANE_COLOUR["bad"]}"' in new
    n_old, n_new = sum(len(s[1]) for s in stretches), sum(len(s[2]) for s in stretches)
    assert new.count("<polyline") == n_old + 2 * n_new                # ghosts, then glow + the side's line


def test_a_path_that_stays_on_its_line_is_not_marked():
    a = [[0, 0], [1000, 0], [1000, 1000]]
    assert terrain._moved_runs(a, [[0, 0], [600, 0], [1000, 0], [1000, 1000]]) == []      # an extra corner on the line
    (run,) = terrain._moved_runs([[0, 0], [500, 300], [1000, 0]], [[0, 0], [1000, 0]])     # a corner pulled 300 aside
    assert run[0][1] <= 60 and max(p[1] for p in run) == 300


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
    # shops: each fountain's shop is 3 hulls, the two secret shops one each (an octagon and a 12-gon)
    assert len(d["dota_movespeed_modifier_path"]) == 5 and len(d["trigger_shop"]) == 8


def test_a_zone_is_its_hulls_real_footprint():
    """2026-10-07: the 7.41 secret shop is an octagon of radius 640 — its bounding box reached 905 units out, and a hero
    standing in the drawn corner could not buy. Three dump formats carry a hull's vertices."""
    import struct
    pts = [(640 * math.cos(math.radians(22.5 + 45 * i)), 640 * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
    raw = b"".join(struct.pack("<3f", x, y, 0.0) for x, y in pts).hex()
    for dump in (f"m_Vertices = #[ 00 01 02 ]\nm_VertexPositions = \n#[\n{raw}\n]",     # 7.35c+: positions apart
                 f"m_Vertices = \n#[\n{raw}\n]",                                         # older .vphys_c
                 "m_Vertices = \n[\n" + "".join(f"[ {x:.4f}, {y:.4f}, 0.0 ],\n" for x, y in pts) + "]"):  # oldest
        (hull,) = ext.hull_vertices(dump)
        assert len(ext.convex(hull)) == 8
    e = {"origin": [1000.0, 2000.0, 0.0], "angles": [0.0, 90.0, 0.0], "model": "maps/dota/entities/shop.vmdl"}
    (shape,) = ext._zone_shapes(e, {"maps/dota/entities/shop.vmdl": ((-640, -640), (640, 640))},
                                {"maps/dota/entities/shop.vmdl": [ext.convex(pts)]})
    assert len(shape) == 8
    assert max(math.hypot(p["x"] - 1000, p["y"] - 2000) for p in shape) <= 641          # not the box's 905
    (box,) = ext._zone_shapes(e, {"maps/dota/entities/shop.vmdl": ((-640, -640), (640, 640))}, {})
    assert len(box) == 4                                                                # no vertices read: the box


def test_a_zone_chip_counts_zones_not_their_hulls():
    """A fountain's shop is 3 hulls: one of them moving is 1 shop changed of 2, not 1 of 4 polygons."""
    sq = [[[0, 0], [1, 0], [1, 1]], [[5, 5], [6, 5], [6, 6]], [[9, 9], [10, 9], [10, 10]]]
    moved = [sq[0], sq[1], [[9, 9], [11, 9], [11, 11]]]
    diff = {"zones": {"shops": {"old": sq + [[[50, 50], [51, 50], [51, 51]]], "oldVolume": [0, 0, 0, 1],
                               "new": moved + [[[50, 50], [51, 50], [51, 51]]], "newVolume": [0, 0, 0, 1]}}}
    assert [c for c in terrain._layer_changes(diff) if c[0] == "shop zones"] == [("shop zones", "changed", 1, 0, 2)]


def test_touching_hulls_are_outlined_as_one_shape():
    """The owner 2026-10-07: the Dire fountain shop looked "из 2 частей" — 2 entities, 2 hulls each (a pentagon and a
    rectangle side by side, a 32-unit strip inside them); drawn now as one outline."""
    pytest.importorskip("contourpy")
    pentagon = [[5824, 6208], [6720, 5312], [6720, 7104], [5824, 7104]]
    rect = [[6720, 5312], [7808, 5312], [7808, 7104], [6720, 7104]]
    strip = [[5824, 7072], [7808, 7072], [7808, 7104], [5824, 7104]]
    (ring,) = btd.zone_outlines([pentagon, rect, strip])
    assert all(5820 <= x <= 7812 and 5308 <= y <= 7108 for x, y in ring)
    assert not any(6700 < x < 6740 and 5400 < y < 7000 for x, y in ring)            # no corner on the inner edge
    lone = [[0, 0], [100, 0], [100, 100]]
    assert btd.zone_outlines([lone, [[900, 900], [1000, 900], [1000, 1000]]])[0] == lone   # a lone hull: exact


def test_the_741_shops_layer_outlines_each_shop_once():
    svg = terrain._line_zone_svgs(terrain._load_diff("7.41"), terrain._projector(terrain._load_map_meta()))
    new = svg[svg.index("tm-layer-shops tm-new"):]
    new = new[:new.index("</svg>")]
    stroke = new[new.index('fill="none" stroke='):]
    assert stroke.count("<polygon") == 4                                            # 2 fountain shops + 2 secret


def test_the_741_secret_shop_and_roshan_pits_are_polygons():
    with open(os.path.join(ROOT, "data", "map", "mapdata_741f.json"), encoding="utf-8") as f:
        d = json.load(f)["data"]
    assert sorted(len(z["points"]) for z in d["trigger_shop"] if z["shopType"] == "2") == [8, 12]
    assert [len(z["points"]) for z in d["trigger_boss_attackable"]] == [7, 7]
    assert all(len(c["points"]) == 4 for c in d["trigger_multiple"])                     # camp boxes are rectangles


def test_7_38c_shows_its_top_lane_path_change():
    """7.38c "The Top Lane creep paths have been slightly adjusted": both top lanes changed in the map file."""
    chips = [c for c in terrain._moved_items(terrain._load_diff("7.38c")) if c[0] == "lane paths"]
    assert chips == [("lane paths", "changed", 2, 0, 6)]


def test_new_layers_are_drawn_per_side():
    svg, _counts = terrain._markers_svg(terrain._load_diff("7.41"))
    for key in ("lanes", "currents", "shops", "spawns"):
        assert f"tm-layer-{key} tm-old" in svg and f"tm-layer-{key} tm-new" in svg, key
