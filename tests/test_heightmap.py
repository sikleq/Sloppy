"""maps/dota.vhcg — the map's height grid (scripts/gen/heightmap.py) and the Terrain page's Heights layer.
The owner 2026-10-05: "decode dota.vhcg and make a height layer; we don't go to leamare any more"."""
import os
import struct
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
import heightmap  # noqa: E402

NONE = -16384.0


def _vhcg(cells, blocks, w=3, h=2, s=5, cell=128.0, x0=-10752.0, y0=-109440.0):
    """A tiny dota.vhcg: `cells` = [(a, b, flag)] row-major, `blocks` = one s x s list per flagged cell."""
    head = b"vhcg" + struct.pack("<5I", 1, int(cell), w, h, s) + struct.pack("<3f", cell, x0, y0)
    head += b"\0" * (128 - len(head))
    body = b"".join(struct.pack("<ffB", *c) for c in cells)
    det = b"".join(struct.pack(f"<{s * s}f", *[v for row in blk for v in row]) for blk in blocks)
    return head + body + det


def test_header_records_and_detail_blocks_in_row_major_order():
    ramp = [[0, 32, 64, 96, 128] for _ in range(5)]              # rises west -> east
    step = [[256] * 5, [256] * 5, [128] * 5, [128] * 5, [128] * 5]   # rows run south -> north: [r][q]
    cells = [(128, NONE, 0), (NONE, NONE, 1), (512, NONE, 0),
             (NONE, NONE, 1), (0, 16, 0), (NONE, NONE, 0)]
    head, recs, blocks = heightmap.parse(_vhcg(cells, [ramp, step]))
    assert (head["w"], head["h"], head["s"], head["cell"], head["x0"], head["y0"]) == (3, 2, 5, 128, -10752, -109440)
    idx = heightmap.block_index(recs)
    at = lambda x, y: heightmap.height_at(head, recs, blocks, idx, x, y)
    x0, y0 = -10752, -109440
    assert at(x0 + 10, y0 + 10) == 128                           # flat cell (0, 0)
    assert at(x0 + 128 + 5, y0 + 5) == 0 and at(x0 + 128 + 100, y0 + 5) == 96   # the ramp: first block, by x
    assert at(x0 + 10, y0 + 128 + 5) == 256 and at(x0 + 10, y0 + 128 + 100) == 128   # second block: by y, [r][q]
    assert at(x0 + 128 + 10, y0 + 128 + 10) == 0                 # the river bed (b = its water, 16 above)
    assert at(x0 + 256 + 10, y0 + 128 + 10) is None              # -16384 = no ground
    assert at(x0 - 1, y0) is None                                # outside the grid


def test_a_file_whose_detail_does_not_fit_its_flags_is_refused():
    raw = _vhcg([(NONE, NONE, 1)] + [(0, NONE, 0)] * 5, [])
    with pytest.raises(ValueError):
        heightmap.parse(raw)
    with pytest.raises(ValueError):
        heightmap.parse(b"xxxx" + raw[4:])


def test_bands_follow_the_game_levels():
    assert [heightmap.band(v) for v in (0, 16, 128, 144, 256, 384, 512, 640, 768, 1100)] == [0, 0, 1, 1, 2, 3, 4, 5, 6, 6]
    # the key shows the numbers only (the owner 2026-10-05: "instead of River 0, Base 512 keep only the values")
    assert [label for *_x, label in heightmap.BANDS] == ["0", "128", "256", "384", "512", "640", "768+"]


def test_overlay_fills_bands_and_draws_the_step_on_the_upper_side():
    pytest.importorskip("PIL")
    rows = [[0, 0, 256, 256], [0, 0, 256, 256], [None, 128, 128, 128]]
    im = heightmap.overlay_image(rows)
    assert im.getpixel((0, 0)) == heightmap.BANDS[0][1] + (heightmap.FILL_A,)          # river, inside its band
    edge = tuple(int(c * 0.55) for c in heightmap.BANDS[2][1]) + (heightmap.EDGE_A,)
    assert im.getpixel((2, 0)) == edge                                                    # high ground next to river
    assert im.getpixel((1, 2)) == edge[:0] + tuple(int(c * 0.55) for c in heightmap.BANDS[1][1]) + (heightmap.EDGE_A,)
    assert im.getpixel((0, 2))[3] == 0                                                    # no ground: clear
    assert im.getpixel((3, 0)) == heightmap.BANDS[2][1] + (heightmap.FILL_A,)
    g = heightmap.grid_image(rows)
    assert g.getpixel((2, 0)) == 256 + 1024 and g.getpixel((0, 2)) == 0


def test_every_terrain_map_file_has_its_heights():
    """One picture per height + one 16-bit grid per map file with a gridnav (heightmap.py all), in the site's frame.
    Since 2026-10-05 the heights are separate pictures, so the page can switch them one by one."""
    codes = [n[len("gridnav_"):-len(".gnv.gz")] for n in os.listdir(os.path.join(_ROOT, "data", "map"))
             if n.startswith("gridnav_")]
    assert codes
    for code in codes:
        ver = f"{code[0]}.{code[1:]}"
        bands = [k for k in range(len(heightmap.BANDS))
                 if os.path.exists(os.path.join(_ROOT, "icons", "maps", f"heights_{ver}_{k}.png"))]
        assert {0, 1, 2} <= set(bands), (ver, bands)              # river, low and high ground on every map
        assert not os.path.exists(os.path.join(_ROOT, "icons", "maps", f"heights_{ver}.png")), ver   # the old one
        assert os.path.exists(os.path.join(_ROOT, "data", "map", f"heights_{code}.png")), code
    pytest.importorskip("PIL")
    from PIL import Image
    g = Image.open(os.path.join(_ROOT, "data", "map", f"heights_{codes[-1]}.png"))
    assert g.size == (heightmap.FRAME_W, heightmap.FRAME_H)


def test_terrain_page_gets_the_heights_layer_button_and_switches():
    """The key moved off the map into the panels (the owner 2026-10-05): under the change list and in the fullscreen
    panel, one switch per height (numbers only), each showing / hiding its own picture."""
    import builders.terrain as terrain
    top, fs = terrain._controls_html(layers=True, heights=True)
    assert 'data-layer="heights"' in top and "tc_heights.png" in top
    assert 'data-layer="heights"' not in terrain._controls_html(layers=True)[0]
    assert '<div class="tc-fsp-title">Heights</div><div class="tf-hbands tc-fsp-chips">' in fs
    btns = terrain._heights_buttons()
    # chips like "Changed in the map file" (the owner 2026-10-08): swatch in the icon's place, the number bold
    assert btns.count('class="tf-chip tf-hband"') == 7 and 'data-hband="0"' in btns and "</i><b>768+</b></button>" in btns
    assert "River" not in btns and "Base" not in btns and "--c:rgb(52, 132, 218)" in btns
    assert "tc-heights-key" not in terrain._compare_html("7.40c", "7.41", markers_svg='<svg class="tm-layer-heights">')
    diff = terrain._load_diff("7.41")
    hb = terrain._heights_bands(diff)
    assert hb["old"][0] == "7.40c" and hb["new"][0] == "7.41" and 0 in hb["new"][1]
    svg, _counts = terrain._markers_svg(diff)
    assert 'class="tm-hband tm-hband-0" href="icons/maps/heights_7.41_0.png"' in svg
    facts = terrain._facts_html({}, "7.41", diff)
    assert '<div class="tf-head">Heights</div>' in facts and 'data-hband="6"' in facts


def test_fullscreen_chips_are_icon_and_number_with_the_word_kept_for_the_tooltip():
    """The owner 2026-10-05: in fullscreen "icon + 7/28, i.e. without the text 'moved', and a small chip"."""
    import builders.terrain as terrain
    chip = terrain._chip("camps", "moved", 7, 0, 28)
    assert '<b>7/28</b> <span class="tf-chip-word">moved</span>' in chip and 'data-tooltip="Camps: 7/28 moved"' in chip
    css = open(os.path.join(_ROOT, "styles.css"), encoding="utf-8").read()
    assert ".tc-fsp-chips .tf-chip-word { display: none; }" in css
    js = open(os.path.join(_ROOT, "src", "scripts.js"), encoding="utf-8").read()
    assert ".tc-fsp-chips .tf-chip[data-tooltip]" in js and "function initHeightBands()" in js


def test_the_control_bar_keeps_one_row_with_the_heights_button():
    """16 layer toggles + Zoom + Full wrapped at a 6px gap once Heights was added (the owner 2026-10-05: "the new
    filter doesn't fit in one line"); a 2px minimum fits a 1280-px window's 685-px bar (628 px of buttons)."""
    css = open(os.path.join(_ROOT, "styles.css"), encoding="utf-8").read()
    bar = css.replace("\r\n", "\n").split("\n.tc-controls-bar {", 1)[1].split("}", 1)[0]   # the bar's own rule
    assert "gap: 2px;" in bar and "justify-content: space-between;" in bar
