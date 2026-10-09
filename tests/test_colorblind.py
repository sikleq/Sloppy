"""Colour-blind mode (owner 2026-10-09): under html.cb-mode every tag (BUFF, NERF, NEW, REWORK, SWAP, QoL, DEL, MISC)
gets its own colour, apart for deutan / protan eyes too; every page with the header carries the switch."""
import itertools
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "gen"))

import gen_colorblind_css as cb  # noqa: E402
from builders import site_common  # noqa: E402

# Machado, Oliveira & Fernandes 2009, severity 1.0, on linear RGB
_SIM = {
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
}


def _css():
    with open(cb.CSS, encoding="utf-8") as f:
        return f.read()


def _js():
    with open(os.path.join(ROOT, "src", "scripts.js"), encoding="utf-8") as f:
        return f.read()


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lab(rgb):
    r, g, b = (_lin(c) for c in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116   # noqa: E731
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def _seen(rgb, m):
    lr = [_lin(c) for c in rgb]
    out = [max(0.0, min(1.0, sum(m[i][j] * lr[j] for j in range(3)))) for i in range(3)]
    return tuple(255 * (12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055) for v in out)


def _min_de(pal, m):
    return min(sum((p - q) ** 2 for p, q in zip(_lab(_seen(a, m)), _lab(_seen(b, m)))) ** 0.5
               for a, b in itertools.combinations(pal.values(), 2))


def test_block_is_up_to_date():
    """A new tag rule without its twin fails here: run python scripts/gen/gen_colorblind_css.py."""
    text = _css()
    assert cb.build(text)[0] == text
    assert text.index(cb.END) < text.index(cb.PHONES)          # the phone block stays last


def test_tag_colours_stay_apart_for_colour_blind_eyes():
    """Every pair of tag colours at least MIN_DE apart (CIE Lab) as deutan / protan eyes see them; the site's own
    set merges (BUFF / REWORK would be 1 with only buff / nerf swapped, SWAP / MISC is 6 today)."""
    for eye, m in _SIM.items():
        assert _min_de(cb.CB_TAGS, m) >= cb.MIN_DE, eye
    assert _min_de(cb.BASE, _SIM["deutan"]) < 10


def test_recolour_keeps_text_lightness_and_moves_tints():
    m = cb.COLOUR.search("#87a3bf")                                   # QoL badge text
    text = cb._hls(cb._rgb(cb.COLOUR.search(cb.recolour(m, "qol", text=True)))[0])
    assert abs(text[1] - cb._hls((0x87, 0xa3, 0xbf))[1]) < 0.01      # readable: same lightness
    tint = cb.recolour(cb.COLOUR.search("rgba(121, 192, 255, 0.20)"), "qol")
    assert tint.endswith("0.30)")                                     # a stronger tint
    assert cb.recolour(cb.COLOUR.search("rgba(0, 0, 0, 0.5)"), "buff") == "rgba(0, 0, 0, 0.5)"   # shadows stay


def test_every_tag_has_twins():
    text = _css()
    for sel in ("badge.buff1", "badge.buff10", "badge.nerf5", "badge.buff-text", "badge.nerf-text", "badge.new",
                "badge.rework", "badge.swap", "badge.qol", "badge.del", 'data-tag*="qol"', "ec-score.pos"):
        assert f"html.cb-mode .{sel}" in text or f'html.cb-mode ul.changes li.li-notext[{sel}]' in text, sel
    assert "html.cb-mode ul.changes li.li-notext::before" in text      # the text-less NERF default


def test_only_tags_and_dynamics_cells_change():
    """Owner: «только для тегов/cells» — the rest of the site keeps its colours."""
    block = _css().split(cb.BEGIN, 1)[1].split(cb.END, 1)[0]
    rules = [line.split("{", 1)[0] for line in block.splitlines() if line.strip()]
    assert rules and all(cb.tag_of(s.replace("html.cb-mode ", "")) for s in rules)
    for sel in (".tm-", ".clog-cat-", ".hl-bar-hp", ".atk-basic", ".cat-filter-btn"):
        assert sel not in block, sel


def test_dynamics_cells_use_the_same_colours():
    js = _js()

    def rgb(name):
        block = js[js.index(f"const {name} = {{"):]
        block = block[:block.index("};")]
        return {t: tuple(int(x) for x in v) for t, *v in re.findall(r"(\w+):\s*\[(\d+), (\d+), (\d+)\]", block)}
    assert rgb("DYN_TAG_RGB_CB") == cb.CB_TAGS
    assert rgb("DYN_TAG_RGB") == cb.BASE


def test_header_has_switch_and_early_script():
    nav = site_common.render_top_nav("main", "patches/7.41.html")
    assert 'class="cb-toggle"' in nav
    assert nav.index(site_common.CB_EARLY_SCRIPT) < nav.index('class="cb-toggle"')
    assert "localStorage.getItem('cbMode')" in site_common.CB_EARLY_SCRIPT


def test_switch_is_wired_in_scripts():
    js = _js()
    assert "initCbMode" in js and "'cb-mode-changed'" in js
    assert "localStorage.setItem('cbMode'" in js
