"""The map's gridnav and the No-ward ground layer (the owner 2026-10-02: "a layer of every place where wards can't be
placed"; "check how Valve fixed it")."""
import gzip
import os
import struct
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
sys.path.insert(0, _ROOT)
import gridnav  # noqa: E402
import builders.map_versions as mv  # noqa: E402
import builders.terrain as terrain  # noqa: E402


def _gnv(cells, w=4, h=2):
    head = struct.pack("<IfffIIii", gridnav.MAGIC, 64.0, 32.0, 32.0, w, h, -2, -1)
    return head + bytes(cells)


def test_the_header_and_the_cells_are_read():
    head, cells = gridnav.parse(_gnv([1, 17, 16, 20, 0, 1, 25, 13]))
    assert head == {"cell": 64.0, "w": 4, "h": 2, "x0": -128.0, "y0": -64.0} and len(cells) == 8
    with pytest.raises(ValueError):
        gridnav.parse(b"\0" * 40)


def test_a_ward_stands_on_walkable_ground_without_the_no_ward_flag():
    assert [gridnav.kind(v) for v in (1, 13, 17, 25, 16, 0, 4, 20)] == [
        "ward", "ward", "zone", "zone", "blocked", "blocked", "blocked", "void"]
    assert gridnav.ward_changes(bytes([1, 1, 17, 16]), bytes([17, 1, 1, 16])) == (1, 1)


def test_the_changed_cells_are_their_world_centres():
    """The chips outline these on the map: the centre of each cell that turned no-ward (green), and of each that
    turned wardable (red)."""
    head, _ = gridnav.parse(_gnv([0] * 8))
    old, new = bytes([1, 1, 17, 16, 1, 1, 1, 1]), bytes([17, 1, 1, 16, 1, 1, 1, 0])
    assert gridnav.changed_cells(head, old, new) == ([[-96, -32], [96, 32]], [[32, -32]])
    assert (len(_wards("7.41d")["toNoWard"]), len(_wards("7.41d")["toWardable"])) == (23, 0)
    assert (len(_wards("7.41c")["toNoWard"]), len(_wards("7.41c")["toWardable"])) == (0, 149)


def test_every_pictured_map_file_has_its_grid_and_its_layer_picture():
    pics = mv.load_pictures()
    for ver in pics:
        assert os.path.exists(os.path.join(_ROOT, "data", "map", f"gridnav_{mv.code(ver)}.gnv.gz")), ver
        assert os.path.exists(os.path.join(_ROOT, "icons", "maps", f"nowards_{ver}.png")), ver


def _wards(patch):
    return terrain._load_diff(patch)["wards"]


def test_what_the_grids_say_about_valves_ward_fixes():
    """7.39b "Fixed some locations that were incorrectly blocked for warding": not one cell changed — it was no map
    change. 7.39d "Fixed a ward spot in Radiant safe lane hard camp": cells there turned no-ward. 7.41c opened 149
    cells by the Twin Gates and Tormentors that no note mentions."""
    assert (_wards("7.39b")["lost"], _wards("7.39b")["gained"]) == (0, 0)
    assert (_wards("7.39d")["lost"], _wards("7.39d")["gained"]) == (10, 0)
    assert (_wards("7.41c")["lost"], _wards("7.41c")["gained"]) == (0, 149)


def test_the_layer_shows_each_sides_grid_and_starts_off():
    """Off on every page, a ward-only one (7.41c) too — the owner 2026-10-02: "forgot to turn it off by default"."""
    diff = terrain._load_diff("7.41c")
    svg, _counts = terrain._markers_svg(diff, "741c")
    assert 'tm-layer-nowards tm-old' in svg and 'href="icons/maps/nowards_7.41a.png"' in svg
    assert 'tm-layer-nowards tm-new' in svg and 'href="icons/maps/nowards_7.41c.png"' in svg
    assert 'data-layer="nowards"' in terrain._controls_html(layers=True)[0]
    steps = {s.patch: s for s in mv.steps()}
    html = terrain._build_terrain_page("7.41c", list(steps), {}, steps["7.41c"], diff, "")
    assert "data-layers-on" not in html and "show-nowards" not in html


def test_the_overlay_is_one_pixel_per_cell_north_up(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    src = tmp_path / "t.gnv.gz"
    with gzip.open(src, "wb") as f:
        f.write(_gnv([17, 1, 1, 1, 1, 1, 1, 20]))           # row 0 (south): a zone at x 0; row 1: void at x 3
    out = tmp_path / "t.png"
    gridnav.overlay(str(src), str(out))
    im = Image.open(out)
    assert im.size == (4, 2)
    assert im.getpixel((0, 1)) == gridnav.ZONE and im.getpixel((3, 0)) == gridnav.VOID and im.getpixel((1, 1))[3] == 0
