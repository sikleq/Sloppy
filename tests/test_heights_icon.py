"""The Terrain "Heights" button icon (scripts/gen/gen_terrain_layer_icons.py HEIGHTS_GLYPH, icons/ui/gothic/tc_heights.png).
The owner 2026-10-25: the old terraced hill "looks like a mountain" -> steps rising to the right, layers lighter higher."""
import os
import sys

import pytest

pytest.importorskip("PIL")                      # the generator imports Pillow; CI installs no imaging libraries
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
import gen_terrain_layer_icons as g  # noqa: E402

DARK_TO_LIGHT = "bgyor"                         # HEIGHTS_PAL keys, GOLD[1] .. GOLD[5]


def _column_tops():
    tops = {}
    for x in range(g.N):
        ys = [y for y, row in enumerate(g.HEIGHTS_GLYPH) if row[x] != "."]
        if ys:
            tops[x] = min(ys)
    return tops


def test_glyph_is_16_by_16_in_the_gold_ramp():
    assert len(g.HEIGHTS_GLYPH) == g.N
    assert all(len(row) == g.N for row in g.HEIGHTS_GLYPH)
    assert set("".join(g.HEIGHTS_GLYPH)) <= set(".") | set(g.HEIGHTS_PAL)


def test_steps_rise_to_the_right_not_a_hill():
    tops = _column_tops()
    xs = sorted(tops)
    assert all(tops[a] >= tops[b] for a, b in zip(xs, xs[1:])), "a column is higher than the one to its right"
    assert len(set(tops.values())) >= 3, "fewer than three steps"
    assert tops[xs[-1]] < tops[xs[0]]


def test_higher_layers_are_lighter():
    shades = [max(DARK_TO_LIGHT.index(c) for c in row if c != ".")
              for row in g.HEIGHTS_GLYPH if row.strip(".")]
    assert shades == sorted(shades, reverse=True), "a lower row is lighter than the one above"


def test_png_matches_the_generator():
    from PIL import Image, ImageChops
    png = Image.open(os.path.join(_ROOT, "icons", "ui", "gothic", "tc_heights.png")).convert("RGBA")
    assert ImageChops.difference(png, g.heights_icon()).getbbox() is None, "run gen_terrain_layer_icons.py tc_heights"
