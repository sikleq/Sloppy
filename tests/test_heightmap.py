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
    assert [label for *_x, label in heightmap.BANDS][:3] == ["River 0", "Low 128", "High 256"]


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
    """One overlay picture + one 16-bit grid per map file with a gridnav (heightmap.py all), in the site's frame."""
    codes = [n[len("gridnav_"):-len(".gnv.gz")] for n in os.listdir(os.path.join(_ROOT, "data", "map"))
             if n.startswith("gridnav_")]
    assert codes
    for code in codes:
        ver = f"{code[0]}.{code[1:]}"
        assert os.path.exists(os.path.join(_ROOT, "icons", "maps", f"heights_{ver}.png")), ver
        assert os.path.exists(os.path.join(_ROOT, "data", "map", f"heights_{code}.png")), code
    pytest.importorskip("PIL")
    from PIL import Image
    g = Image.open(os.path.join(_ROOT, "data", "map", f"heights_{codes[-1]}.png"))
    assert g.size == (heightmap.FRAME_W, heightmap.FRAME_H)


def test_terrain_page_gets_the_heights_layer_button_and_key():
    import builders.terrain as terrain
    top, _fs = terrain._controls_html(layers=True, heights=True)
    assert 'data-layer="heights"' in top and "tc_heights.png" in top
    assert 'data-layer="heights"' not in terrain._controls_html(layers=True)[0]
    html = terrain._compare_html("7.40c", "7.41", markers_svg='<svg class="tc-markers tm-layer tm-layer-heights tm-old">')
    assert 'class="tc-heights-key"' in html and "River 0" in html and "--c:rgb(52, 132, 218)" in html
    assert "tc-heights-key" not in terrain._compare_html("7.40c", "7.41", markers_svg="<svg></svg>")
