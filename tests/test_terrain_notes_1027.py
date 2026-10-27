"""Terrain note pictures (owner 2026-10-27): the new side shows where removed trees stood (7.38b "Removed several trees
around camps" had a new side with nothing on it), and two rows with the same words in two sections of a patch (7.38c
"Several additional tree and visual adjustments have been made to this area") each take their own spot."""
import pytest

from patch import elements
from patch.state import reset_page_state


def test_same_worded_rows_take_their_own_spots(monkeypatch):
    rows = [("Several additional tree", ["738c_5.webp"], "tree"), ("Several additional tree", ["738c_9.webp"], "tree")]
    monkeypatch.setattr(elements, "_terrain_spot_index", lambda: {"7.38c": rows})
    reset_page_state()
    text = "Several additional tree and visual adjustments have been made to this area"
    assert "738c_5.webp" in elements.terrain_note("7.38c", text)[1]
    assert "738c_9.webp" in elements.terrain_note("7.38c", text)[1]
    reset_page_state()                                          # the next page counts from the first again
    assert "738c_5.webp" in elements.terrain_note("7.38c", text)[1]


def test_a_second_row_without_a_spot_of_its_own_gets_none(monkeypatch):
    rows = [("Several additional tree", ["738c_5.webp"], "tree")]
    monkeypatch.setattr(elements, "_terrain_spot_index", lambda: {"7.38c": rows})
    reset_page_state()
    text = "Several additional tree and visual adjustments have been made to this area"
    assert elements.terrain_note("7.38c", text)[1]
    assert elements.terrain_note("7.38c", text) == ("", "")      # Bottom Lane's: all its trees are in other pictures


def _red(img, xy):
    r, g, _ = img.getpixel(xy)
    return r > 150 and g < 120


def _green(img, xy):
    r, g, _ = img.getpixel(xy)
    return g > 40 and r < 30


def test_a_tree_note_shows_the_trees_layer_and_the_removed_tree_only_on_the_old_side():
    """7.38b "Removed several trees around camps" (owner 2026-10-27): "just show the trees layer, both pictures, and
    outline the removed trees red dashed on the left" — no mark on the right, the gap in the layer says it."""
    pytest.importorskip("PIL")
    from PIL import Image
    import scripts.gen.terrain_shots as ts
    groups = {"trees": {"removed": [(0, 0)], "added": [], "moved": []}}
    layer = {"old": [(0, 0), (300, 0)], "new": [(300, 0)]}           # the tree at (0, 0) is gone in the new map
    sides = {}
    for side in ("old", "new"):
        sides[side] = Image.new("RGB", (360, 360))
        ts._tree_layer(sides[side], 0, 0, 500, layer[side], 360)
        ts._outlines(sides[side], 0, 0, 500, groups, side, {"trees"}, 360, 3)
    assert _green(sides["old"], (180, 180)) and not _green(sides["new"], (180, 180))
    assert _green(sides["new"], (180 + 108, 180))                   # the tree that stays: on both sides
    assert any(_red(sides["old"], (x, 180 - 23)) for x in range(160, 200))
    raw = sides["new"].tobytes()
    assert not any(raw[i] > 150 and raw[i + 1] < 120 for i in range(0, len(raw), 3))   # nothing red on the right
