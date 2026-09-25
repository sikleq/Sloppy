"""Small control icons in the gothic-gold pixel style (Pixel Art Studio skill): attack type
(melee sword / ranged bow) and the talent tree. Drawn at their true on-screen size and shipped
at 2x (nearest) so they stay crisp on hi-DPI; the page shows them with image-rendering: pixelated.

    python tools/pixel_icons/small.py            # -> tools/pixel_icons/out/*.png + preview_small.png
    python tools/pixel_icons/small.py --install  # also copy to icons/ui/gothic/
"""
import os
import shutil
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import O, G0, G1, G2, G3, G4, G5, G6, G7, P0, P1, OUT, GOTHIC, Sprite  # noqa: E402,F401

SHIP_SCALE = 2


def melee():
    """Sword, point to the top-right: lit upper edge, shaded lower edge, crossguard, grip, pommel."""
    s = Sprite(12, 12)
    for i in range(6):                                   # blade (5,6) -> (10,1)
        s.px(5 + i, 6 - i, G7)
        s.px(6 + i, 6 - i, G4)
    s.px(10, 1, G7)
    s.px(11, 1, None)
    s.px(3, 6, G6)                                       # crossguard, across the blade
    s.px(4, 7, G4)
    s.px(5, 8, G2)
    s.px(3, 8, G2)                                       # grip
    s.px(2, 9, G1)
    s.px(1, 10, G5)                                      # pommel
    s.outline(O)
    return s


def ranged():
    """Bow bulging toward the target (right), bone string on the left, arrow nocked and pointing right."""
    s = Sprite(12, 12)
    s.layer("bow")
    s.use(layer="bow")
    arc = {1: 4, 2: 5, 3: 6, 4: 7, 5: 7, 6: 7, 7: 7, 8: 6, 9: 5, 10: 4}
    shade = {1: G7, 2: G7, 3: G6, 4: G6, 5: G5, 6: G4, 7: G3, 8: G3, 9: G2, 10: G2}
    for y, x in arc.items():
        s.px(x, y, shade[y])
    for y in range(2, 10):                               # string
        s.px(3, y, P0)
    s.outline(O)
    s.layer("arrow")
    s.use(layer="arrow")
    for x in range(2, 10):                               # shaft
        s.px(x, 6, G5)
    s.px(10, 6, G7)                                      # head
    s.px(9, 5, G6)
    s.px(9, 7, G3)
    s.px(1, 5, P1)                                       # fletching
    s.px(1, 7, P0)
    s.outline(O)
    return s


def talents():
    """Talent tree: trunk with two branches and a crown, each ending in a gold node."""
    s = Sprite(13, 13)
    s.layer("tree")
    s.use(layer="tree")
    for y in range(4, 11):                               # trunk
        s.px(6, y, G3)
    s.px(5, 11, G2)
    s.px(6, 11, G2)
    s.px(7, 11, G1)
    for i in range(3):                                   # branches
        s.px(5 - i, 8 - i, G4)
        s.px(7 + i, 8 - i, G2)
    s.outline(O)
    s.layer("nodes")
    s.use(layer="nodes")
    for cx, cy in ((2, 4), (10, 4), (6, 2)):             # 3x3 diamonds, lit top-left
        s.px(cx, cy - 1, G7)
        s.px(cx - 1, cy, G7)
        s.px(cx, cy, G6)
        s.px(cx + 1, cy, G4)
        s.px(cx, cy + 1, G3)
    s.outline(O)
    return s


ICONS = {"atk_melee": melee, "atk_ranged": ranged, "icon_talents": talents}


def main():
    os.makedirs(OUT, exist_ok=True)
    shots = []
    for name, fn in ICONS.items():
        s = fn()
        s.flatten()
        raw = os.path.join(OUT, f"_{name}_1x.png")
        s.save_png(raw)
        im = Image.open(raw).convert("RGBA")
        im.resize((im.width * SHIP_SCALE, im.height * SHIP_SCALE), Image.NEAREST).save(os.path.join(OUT, f"{name}.png"))
        shots.append(im)
        print(f"  {name}: {im.width}x{im.height} -> x{SHIP_SCALE}")
    sc, pad = 16, 12
    sheet = Image.new("RGBA", (sum(i.width * sc + pad for i in shots) + pad, 13 * sc + 2 * pad), (21, 18, 14, 255))
    x = pad
    for im in shots:
        sheet.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.NEAREST), (x, pad))
        x += im.width * sc + pad
    sheet.save(os.path.join(OUT, "preview_small.png"))
    one = Image.new("RGBA", (80, 24), (34, 27, 19, 255))   # true size, as on the page
    for i, im in enumerate(shots):
        one.alpha_composite(im, (6 + i * 24, 6))
    one.resize((one.width * 4, one.height * 4), Image.NEAREST).save(os.path.join(OUT, "preview_small_1x.png"))
    if "--install" in sys.argv:
        for name in ICONS:
            shutil.copy(os.path.join(OUT, f"{name}.png"), os.path.join(GOTHIC, f"{name}.png"))
        print("  installed into icons/ui/gothic/")


if __name__ == "__main__":
    main()
