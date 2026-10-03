"""No line under the Terrain slider. Until 2026-10-03 it read "Inspired by Leamare and devilesk"; the owner then
asked to remove it from the site — every map picture and object list is our own, and the Oldgrowth README already
credits them."""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
import builders.map_versions as mv  # noqa: E402
import builders.terrain as terrain  # noqa: E402


def test_no_page_has_a_line_under_the_slider():
    steps = {s.patch: s for s in mv.steps()}
    html = terrain._build_terrain_page("7.41c", list(steps), {}, steps["7.41c"], terrain._load_diff("7.41c"), "")
    assert "tc-source" not in html and "Inspired" not in html and "devilesk" not in html
    css = open(os.path.join(_ROOT, "styles.css"), encoding="utf-8").read()
    assert ".tc-source" not in css
