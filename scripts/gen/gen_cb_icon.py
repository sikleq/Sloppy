"""The colour-blind switch icon -> icons/ui/gothic/icon_cb_off.png / icon_cb_on.png (48 px, 16-px glyph ×3).

An eye (after pixelarticons' "eye", MIT) in the site's gold ramp, its iris split into the BUFF / NERF pair in use:
green / red (off) or blue / orange (on, the colour-blind mode — scripts/gen/gen_colorblind_css.py). The header
switch shows the one that matches the mode (builders/site_common.py CB_TOGGLE). Dark outline, hard-edged like the
terrain layer icons (gen_terrain_layer_icons.py).

    python scripts/gen/gen_cb_icon.py
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_colorblind_css as cb  # noqa: E402
from gen_terrain_layer_icons import GOLD, ICON_RES, N, _outline  # noqa: E402

_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "icons", "ui", "gothic")
# '#' lid edge, 'l' white of the eye, 'G' / 'R' the iris halves (buff / nerf), 'k' pupil, '*' its glint
EYE_GLYPH = [
    "................",
    "................",
    "................",
    "................",
    "......####......",
    "....##llll##....",
    "...#llGGRRll#...",
    "..#llGG*kRRll#..",
    "..#llGGkkRRll#..",
    "...#llGGRRll#...",
    "....##llll##....",
    "......####......",
    "................",
    "................",
    "................",
    "................",
]
BUFF, NERF = (93, 177, 78), (209, 75, 75)         # scripts.js DYN_TAG_RGB buff / nerf


def _safe(rgb):
    m = cb.COLOUR.search("rgb(%d, %d, %d)" % rgb)
    return tuple(int(x) for x in cb.remap(m)[4:-1].split(","))


def eye_icon(buff, nerf):
    pal = {"#": GOLD[3], "l": GOLD[5], "G": buff, "R": nerf, "k": (20, 17, 14), "*": (255, 255, 255)}
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    for y, row in enumerate(EYE_GLYPH):
        for x, ch in enumerate(row):
            if ch in pal:
                im.putpixel((x, y), pal[ch] + (255,))
    return _outline(im).resize((ICON_RES, ICON_RES), Image.NEAREST)


def main():
    eye_icon(BUFF, NERF).save(os.path.join(_OUT, "icon_cb_off.png"))
    eye_icon(_safe(BUFF), _safe(NERF)).save(os.path.join(_OUT, "icon_cb_on.png"))
    print("icon_cb_off.png, icon_cb_on.png")


if __name__ == "__main__":
    main()
