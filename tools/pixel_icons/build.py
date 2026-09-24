"""Index-tile icons for the tiles that have no hover animation (Pixel Art Studio skill).

Style = the site's gothic-gold set (icons/ui/gothic/*): 32x32, transparent, one warm gold ramp,
1px #311e12 outline, light from the top-left, flat clusters, no dithering (study card
~/.claude/skills/pixel-art-studio/references/learned/006-sloppy-gothic-gold-icons.md).
Every part that overlaps another sits on its own layer so it gets its own outline.

    python tools/pixel_icons/build.py          # -> tools/pixel_icons/out/*.png + preview.png
    python tools/pixel_icons/build.py --install # also copy to icons/ui/gothic/
"""
import os
import shutil
import sys

SKILL = os.path.expanduser("~/.claude/skills/pixel-art-studio/scripts")
sys.path.insert(0, SKILL)
from pixelstudio import Sprite  # noqa: E402
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
GOTHIC = os.path.join(HERE, "..", "..", "icons", "ui", "gothic")

O = "#311e12"                                          # outline / internal separations
G0, G1, G2, G3 = "#674919", "#7d5b23", "#826924", "#997c2c"
G4, G5, G6, G7 = "#a49438", "#b3a240", "#c2b048", "#d6c46e"
P0, P1 = "#b09a64", "#d6c286"                           # parchment / bone


def new():
    return Sprite(32, 32)


def part(s, name):
    s.layer(name)
    s.use(layer=name)


def cols(s, x0, x1, y0, y1, bands):
    """Cylinder shading: split x0..x1 into vertical bands (left = lit), paint only over opaque px."""
    w = x1 - x0 + 1
    for i, c in enumerate(bands):
        a = x0 + (w * i) // len(bands)
        b = x0 + (w * (i + 1)) // len(bands) - 1
        if b >= a:
            s.rect(a, y0, b, y1, c, only="opaque")


def rows(s, x0, x1, y0, bands):
    """Horizontal shading rows from y0 down (top = lit)."""
    for i, c in enumerate(bands):
        s.rect(x0, y0 + i, x1, y0 + i, c, only="opaque")


def shade_ring(s, cx, cy, lit, mid, dark):
    """Light from the top-left: recolour every opaque px of the current layer by its angle."""
    for y in range(32):
        for x in range(32):
            if s.get(x, y) is None:
                continue
            d = (x - cx) + (y - cy)                      # < 0 = toward the top-left
            s.px(x, y, lit if d < -3 else dark if d > 3 else mid)


# Each icon is one solid, chunky mass (like the animated set: beetle, chest, book), shaded as
# a volume (lit left/top planes, dark right/bottom planes). Parts that a future hover
# animation would move sit on their own layer (noted in each title).

# ------------------------------------------------ heroes: knight helm (anim: plume sways)
def heroes():
    s = new()
    part(s, "plume")
    s.polygon([(13, 7), (14, 3), (18, 1), (23, 1), (28, 3), (30, 7), (29, 9), (26, 7), (22, 5), (17, 6)], G4)
    s.line(16, 2, 24, 2, G7)
    s.line(15, 3, 25, 3, G6)
    s.line(26, 4, 28, 6, G6)
    s.line(18, 5, 27, 7, G2)
    s.outline(O)
    part(s, "helm")
    s.ellipse(5, 5, 26, 24, G3)
    s.rect(5, 14, 26, 27, G3)
    cols(s, 5, 26, 5, 27, [G5, G6, G6, G4, G3, G3, G3, G2, G1, G1])
    s.rect(9, 7, 11, 10, G7, only="opaque")              # dome glint
    s.rect(15, 5, 16, 13, G7)                             # crest ridge
    s.line(16, 5, 16, 13, G5)
    s.rect(7, 14, 24, 15, O)                              # visor slit
    s.line(7, 16, 24, 16, G6)                             # lit lower lip of the slit
    for x in (10, 13, 18, 21):                            # breathing holes
        s.rect(x, 19, x + 1, 19, O)
        s.rect(x, 22, x + 1, 22, O)
    s.rect(4, 26, 27, 29, G2)                             # rim
    rows(s, 4, 27, 26, [G6, G4, G2, G0])
    s.outline(O)
    return s


# ------------------------------------------------ changelog: scroll + quill (anim: quill writes)
def changelog():
    s = new()
    part(s, "scroll")
    s.rect(5, 8, 23, 26, P1)
    s.rect(20, 9, 23, 26, P0)
    s.rect(3, 4, 25, 8, G3)                                # top roll (cylinder)
    rows(s, 3, 25, 4, [G7, G6, G4, G2, G1])
    s.rect(3, 25, 25, 29, G3)                              # bottom roll
    rows(s, 3, 25, 25, [G6, G5, G3, G1, G0])
    for y, x1 in ((12, 18), (16, 15), (20, 18)):
        s.rect(8, y, x1, y + 1, G2)                        # 2px text lines
    s.outline(O)
    part(s, "quill")
    s.polygon([(29, 1), (30, 3), (27, 11), (23, 17), (19, 20), (18, 18), (21, 11), (25, 4)], G7)
    s.polygon([(30, 3), (27, 11), (23, 17), (20, 19), (24, 11), (28, 5)], G5)
    s.line(28, 3, 18, 20, G3)                              # shaft
    s.px(25, 8, O)                                         # vane notch
    s.line(17, 21, 16, 22, O)                              # nib
    s.outline(O)
    return s


# ------------------------------------------------ stats: heraldic shield with three stat bars (anim: bars fill)
# (not a book — the Patches tile is already an open book)
SHIELD = [(4, 3), (9, 2), (15, 1), (16, 1), (22, 2), (27, 3), (27, 16), (25, 21), (21, 26), (16, 30),
          (15, 30), (10, 26), (6, 21), (4, 16)]
FACE = [(7, 5), (15, 4), (16, 4), (24, 5), (24, 16), (22, 20), (19, 24), (16, 27), (15, 27), (12, 24),
        (9, 20), (7, 16)]


def stats():
    s = new()
    part(s, "shield")
    s.polygon(SHIELD, G4)                                   # gold rim
    cols(s, 4, 27, 1, 30, [G6, G7, G6, G5, G4, G4, G3, G2])
    s.polygon(FACE, G0)                                     # dark enamel face
    cols(s, 7, 24, 4, 27, [G1, G1, G0, G0, G0, O])
    s.line(8, 5, 14, 4, G7)                                 # rim glint top-left
    s.outline(O)
    part(s, "bars")
    for y, x1 in ((8, 21), (13, 16), (18, 19)):             # three stat bars, different lengths
        s.rect(9, y, 22, y + 2, O)                          # empty track (dark, so the fill reads)
        s.rect(9, y, x1, y + 2, G5)
        s.rect(9, y, x1, y, G7)
        s.rect(9, y + 2, x1, y + 2, G3)
    s.outline(O)
    part(s, "boss")
    s.rect(14, 23, 17, 25, G6)                              # small boss at the tip
    s.px(14, 23, G7)
    s.px(17, 25, G2)
    s.outline(O)
    return s


# ------------------------------------------------ hero lab: alchemy flask (anim: bubbles rise)
def hero_lab():
    s = new()
    part(s, "flask")
    s.circle(15, 20, 10, G1, fill=True)                    # bulb (glass, dark)
    s.rect(12, 4, 19, 11, G1)                              # neck
    s.circle(15, 20, 10, G5, fill=True, only=G1)           # liquid ...
    s.rect(4, 9, 27, 17, G1, only=G5)                      # ... only below the surface
    cols(s, 5, 25, 18, 30, [G6, G6, G5, G5, G5, G4, G3])   # liquid volume
    for c in (G6, G5, G4, G3):
        s.rect(5, 18, 25, 18, G7, only=c)                  # bright surface line
    s.rect(11, 2, 20, 4, G3)                               # rim
    rows(s, 11, 20, 2, [G7, G4, G2])
    for x, y in ((8, 14), (8, 13), (9, 12), (9, 11), (10, 10)):   # glass highlight arc (2px)
        s.px(x, y, G6)
        s.px(x + 1, y, G4)
    s.rect(13, 5, 13, 10, G4)                              # neck glint
    for x, y in ((11, 22), (17, 25), (14, 20)):            # bubbles (2x2)
        s.rect(x, y, x + 1, y + 1, G7)
    s.outline(O)
    return s


# ------------------------------------------------ aoe: rune rings (anim: rings pulse outward)
def aoe():
    s = new()
    part(s, "outer")
    s.circle(15, 15, 14, G4, fill=True)
    s.circle(15, 15, 11, None, fill=True)
    shade_ring(s, 15, 15, G7, G4, G2)
    for x, y in ((14, 1), (14, 27), (1, 14), (27, 14)):    # rune studs
        s.rect(x, y, x + 2, y + 2, G6)
    s.outline(O)
    part(s, "inner")
    s.circle(15, 15, 8, G4, fill=True)
    s.circle(15, 15, 5, None, fill=True)
    shade_ring(s, 15, 15, G6, G4, G1)
    s.outline(O)
    part(s, "core")
    s.circle(15, 15, 3, G6, fill=True)
    s.rect(14, 13, 15, 14, G7)
    s.rect(16, 16, 17, 17, G3, only="opaque")
    s.outline(O)
    return s


# ------------------------------------------------ changes: hourglass (anim: sand runs / flips)
def changes():
    s = new()
    part(s, "glass")
    s.polygon([(9, 5), (22, 5), (22, 9), (17, 15), (17, 16), (22, 22), (22, 26), (9, 26),
               (9, 22), (14, 16), (14, 15), (9, 9)], G0)
    s.polygon([(11, 9), (20, 9), (16, 14), (15, 14)], G6)            # sand left above
    s.line(11, 9, 20, 9, G7)
    s.polygon([(15, 19), (16, 19), (21, 24), (21, 25), (10, 25), (10, 24)], G6)  # pile below
    s.line(13, 22, 11, 24, G7)
    s.rect(15, 15, 16, 21, G7)                                     # 2px stream
    s.line(10, 6, 10, 8, G3)                                       # glass glint
    s.outline(O)
    part(s, "frame")
    s.rect(3, 1, 28, 4, G3)
    rows(s, 3, 28, 1, [G7, G5, G3, G1])
    s.rect(3, 27, 28, 30, G3)
    rows(s, 3, 28, 27, [G6, G4, G2, G0])
    s.rect(5, 5, 7, 26, G4)
    cols(s, 5, 7, 5, 26, [G6, G4, G2])
    s.rect(24, 5, 26, 26, G3)
    cols(s, 24, 26, 5, 26, [G4, G2, G1])
    s.outline(O)
    return s


# ------------------------------------------------ summons: skull on a rune dais (anim: skull rises, eyes glow)
def summons():
    s = new()
    part(s, "dais")
    s.ellipse(1, 21, 30, 30, G1)                            # dais side (its thickness)
    s.ellipse(1, 20, 30, 28, G4)                            # top face
    s.ellipse(4, 21, 27, 27, G6, fill=False)                # rune ring on top
    s.line(5, 21, 12, 20, G7)
    for x, y in ((2, 24), (29, 24), (15, 20), (15, 28)):
        s.px(x, y, G7)
    s.outline(O)
    part(s, "skull")
    s.circle(15, 10, 9, P1, fill=True)
    s.rect(9, 14, 22, 18, P1)
    s.rect(10, 19, 21, 23, P1)
    s.rect(21, 4, 24, 23, P0, only=P1)                      # shaded right side
    s.rect(17, 19, 21, 23, P0, only=P1)
    s.rect(8, 9, 12, 13, O)                                 # chunky eye sockets
    s.rect(18, 9, 22, 13, O)
    s.px(9, 10, G1)
    s.px(19, 10, G1)
    s.polygon([(15, 15), (16, 15), (17, 17), (14, 17)], O)  # nose
    s.line(11, 20, 20, 20, O)                               # teeth
    for x in (12, 14, 17, 19):
        s.px(x, 21, O)
    s.rect(9, 3, 11, 4, G7)                                 # cranium glint
    s.outline(O)
    return s


# ------------------------------------------------ lane creeps: crossed swords (anim: clash + glint)
def _sword(s, flip):
    X = (lambda x: 31 - x) if flip else (lambda x: x)
    for i in range(0, 15):                                 # 4px blade: lit edge -> ridge -> shade
        s.px(X(2 + i), 2 + i, G7)
        s.px(X(3 + i), 2 + i, G6)
        s.px(X(4 + i), 2 + i, G4)
        s.px(X(5 + i), 2 + i, G2)
    for i in range(-2, 3):                                 # chunky crossguard (short: the two never touch)
        s.px(X(19 + i), 19 - i, G5)
        s.px(X(20 + i), 19 - i, G3)
        s.px(X(20 + i), 20 - i, G2)
        s.px(X(21 + i), 20 - i, G1)
    for i in range(0, 4):                                  # grip
        s.px(X(21 + i), 21 + i, G2)
        s.px(X(22 + i), 21 + i, G0)
    s.rect(min(X(25), X(28)), 25, max(X(25), X(28)), 28, G4)   # pommel
    s.px(X(25), 25, G7)
    s.px(X(26), 25, G6)
    s.px(X(28), 28, G1)


def lane_creeps():
    s = new()
    part(s, "a")
    _sword(s, False)
    s.outline(O)
    part(s, "b")
    _sword(s, True)
    s.outline(O)
    return s


# ------------------------------------------------ ko-fi: mug + heart (anim: hearts rise as steam)
def kofi():
    s = new()
    part(s, "saucer")
    s.ellipse(1, 26, 30, 30, G2)
    s.rect(3, 26, 28, 26, G5, only="opaque")
    s.outline(O)
    part(s, "mug")
    s.circle(22, 19, 6, G3, fill=True)                      # thick handle ring
    s.circle(22, 19, 3, None, fill=True)
    s.rect(4, 11, 20, 27, G3)
    cols(s, 4, 20, 11, 27, [G5, G6, G6, G4, G4, G3, G2, G1])
    s.rect(4, 11, 20, 11, G7)                               # rim
    s.rect(5, 12, 19, 13, G0)                               # coffee
    s.rect(6, 12, 9, 12, G1)
    s.outline(O)
    part(s, "heart")
    s.polygon([(10, 2), (13, 2), (14, 3), (15, 2), (18, 2), (19, 3), (19, 6), (14, 10), (9, 6), (9, 3)], G6)
    s.rect(10, 3, 12, 4, G7, only="opaque")
    s.polygon([(16, 4), (19, 3), (19, 6), (15, 9)], G4)
    s.outline(O)
    return s


ICONS = {
    "icon_helm": heroes, "icon_changelog": changelog, "icon_ledger": stats,
    "icon_flask": hero_lab, "icon_aoe": aoe, "icon_hourglass": changes,
    "icon_summons": summons, "icon_swords": lane_creeps, "icon_kofi": kofi,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    tiles = []
    for name, fn in ICONS.items():
        s = fn()
        s.flatten()
        path = os.path.join(OUT, f"{name}.png")
        s.save_png(path)
        tiles.append((name, Image.open(path).convert("RGBA")))
        n = len([c for c in Image.open(path).convert("RGBA").getcolors(4096) if c[1][3] > 0])
        print(f"  {name}: {n} colours")
    # contact sheet on the site's dark background, x8
    sc, pad = 8, 16
    sheet = Image.new("RGBA", (len(tiles) * (32 * sc + pad) + pad, 32 * sc + 2 * pad), (20, 22, 28, 255))
    for i, (_, im) in enumerate(tiles):
        big = im.resize((32 * sc, 32 * sc), Image.NEAREST)
        sheet.alpha_composite(big, (pad + i * (32 * sc + pad), pad))
    sheet.save(os.path.join(OUT, "preview.png"))
    one = Image.new("RGBA", (len(tiles) * 40 + 8, 48), (20, 22, 28, 255))   # 1x arm's-length check
    for i, (_, im) in enumerate(tiles):
        one.alpha_composite(im, (8 + i * 40, 8))
    one.resize((one.width * 2, one.height * 2), Image.NEAREST).save(os.path.join(OUT, "preview_1x.png"))
    if "--install" in sys.argv:
        for name, _ in tiles:
            shutil.copy(os.path.join(OUT, f"{name}.png"), os.path.join(GOTHIC, f"{name}.png"))
        print("  installed into icons/ui/gothic/")


if __name__ == "__main__":
    main()
