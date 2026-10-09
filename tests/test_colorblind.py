"""Colour-blind mode (owner 2026-10-09): every green / red rule in styles.css has its blue / orange twin under
html.cb-mode, and every page with the header carries the switch and the early script."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "gen"))

import gen_colorblind_css as cb  # noqa: E402
from builders import site_common  # noqa: E402


def _css():
    with open(cb.CSS, encoding="utf-8") as f:
        return f.read()


def test_block_is_up_to_date():
    """A new green / red rule without its twin fails here: run python scripts/gen/gen_colorblind_css.py."""
    text = _css()
    assert cb.build(text)[0] == text
    assert text.index(cb.END) < text.index(cb.PHONES)          # the phone block stays last


def test_kind_and_remap():
    assert cb.kind((95, 210, 125)) == "green"
    assert cb.kind((225, 100, 85)) == "red"
    assert cb.kind((227, 196, 106)) is None          # site gold stays
    assert cb.kind((120, 120, 120)) is None          # greys stay
    m = cb.COLOUR.search("rgba(95, 210, 125, 0.27)")
    assert cb.remap(m) == "rgba(65, 182, 240, 0.41)"  # same lightness, blue hue, brighter (saturation, alpha up)


def test_badges_have_twins():
    text = _css()
    for cls in ("buff1", "buff5", "buff10", "nerf1", "nerf5", "nerf10"):
        assert f"html.cb-mode .badge.{cls} " in text, cls


def test_only_tags_and_dynamics_cells_change():
    """Owner: «только для тегов/cells» — the rest of the site keeps its colours; DEL keeps its pink."""
    block = _css().split(cb.BEGIN, 1)[1].split(cb.END, 1)[0]
    rules = [line for line in block.splitlines() if line.strip()]
    assert rules and all(cb.INCLUDE.search(line.split("{", 1)[0]) for line in rules)
    for sel in (".badge.del", ".tm-", ".clog-cat-", ".hl-bar-hp", ".atk-basic"):
        assert sel not in block, sel


def test_dynamics_cells_have_safe_colours():
    """scripts.js DYN_TAG_RGB_CB = the badge remap of DYN_TAG_RGB."""
    import colorsys
    import re
    with open(os.path.join(ROOT, "src", "scripts.js"), encoding="utf-8") as f:
        js = f.read()

    def rgb(name, tag):
        block = js[js.index(f"const {name} = {{"):]
        return tuple(int(x) for x in re.search(tag + r":\s*\[(\d+), (\d+), (\d+)\]", block).groups())
    for tag, hue in (("buff", cb.GREEN_HUE), ("nerf", cb.RED_HUE)):
        h, _l, _s = colorsys.rgb_to_hls(*(c / 255 for c in rgb("DYN_TAG_RGB_CB", tag)))
        assert abs(h * 360 - hue) < 3, tag
        m = cb.COLOUR.search("rgb(%d, %d, %d)" % rgb("DYN_TAG_RGB", tag))
        assert cb.remap(m) == "rgb(%d, %d, %d)" % rgb("DYN_TAG_RGB_CB", tag)


def test_header_has_switch_and_early_script():
    nav = site_common.render_top_nav("main", "patches/7.41.html")
    assert 'class="cb-toggle"' in nav
    assert nav.index(site_common.CB_EARLY_SCRIPT) < nav.index('class="cb-toggle"')
    assert "localStorage.getItem('cbMode')" in site_common.CB_EARLY_SCRIPT


def test_switch_is_wired_in_scripts():
    with open(os.path.join(ROOT, "src", "scripts.js"), encoding="utf-8") as f:
        js = f.read()
    assert "initCbMode" in js and "'cb-mode-changed'" in js
    assert "localStorage.setItem('cbMode'" in js
