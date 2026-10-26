"""The Terrain "Lane creep paths" / "River currents" button icons (the owner 2026-10-26): ready 48-px pictures in
icons/ref/ (gen_terrain_layer_icons.py READY_ICONS), copied as they are to icons/ui/gothic/tc_lanes.png / tc_currents.png."""
import os
import sys

import pytest

pytest.importorskip("PIL")                      # the generator imports Pillow; CI installs no imaging libraries
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
import gen_terrain_layer_icons as g  # noqa: E402

if not all(os.path.exists(os.path.join(g._REF, f)) for f in g.READY_ICONS.values()):
    pytest.skip("icons/ref/ is kept locally only (.gitignore)", allow_module_level=True)


@pytest.mark.parametrize("name", ["tc_lanes", "tc_currents"])
def test_generator_takes_the_ready_picture(name):
    assert name in g.READY_ICONS and name not in g.NEW_LAYER_GLYPHS
    im = g.ready_icon(name)
    assert im.size == (g.ICON_RES, g.ICON_RES) and im.mode == "RGBA"


@pytest.mark.parametrize("name", ["tc_lanes", "tc_currents"])
def test_button_icon_is_the_ready_picture(name):
    built = g.Image.open(os.path.join(g._OUT, f"{name}.png")).convert("RGBA")
    assert built.tobytes() == g.ready_icon(name).tobytes(), f"{name}.png is not icons/ref/{g.READY_ICONS[name]}"
