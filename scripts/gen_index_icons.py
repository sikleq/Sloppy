"""One-off: regenerate index gothic pixel icons.
  - icon_terrain.png  : flat isometric stone platform (Diablo-2 Sanctuary tile),
                        checkered top + carved sides + jagged underside.
  - icon_telegram.png : paper-plane (Support sub-panel).
  - icon_donation.png : coin stack with a heart (Support sub-panel).
All 32x32 RGBA, gothic-gold palette (CSS warms them toward #e3c46a).

Run from anywhere::  python scripts/gen_index_icons.py
Outputs straight into icons/ui/gothic/.
"""
import os
from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUT_DIR = os.path.join(_ROOT, "icons", "ui", "gothic")

S = 32


def newimg():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def px(img, x, y, c):
    if 0 <= x < S and 0 <= y < S and len(c) == 3:
        c = c + (255,)
    if 0 <= x < S and 0 <= y < S:
        img.putpixel((int(x), int(y)), c)


# ---- palette (stone-gold) ----
OUT = (38, 28, 16)        # dark outline
TOP_L = (208, 184, 120)   # light floor stone
TOP_D = (176, 150, 92)    # dark floor stone (checker)
TOP_RIM = (233, 210, 150)  # top edge highlight
SIDE_R = (140, 116, 68)   # lit right face
SIDE_L = (104, 84, 48)    # shadow left face
TEETH = (70, 56, 32)      # jagged underside


def fill_poly(img, pts, color):
    """Scanline-fill a convex polygon (integer pixel centres)."""
    ys = [p[1] for p in pts]
    y0, y1 = int(min(ys)), int(max(ys))
    for y in range(y0, y1 + 1):
        xs = []
        n = len(pts)
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay <= y < by) or (by <= y < ay):
                t = (y - ay) / (by - ay)
                xs.append(ax + t * (bx - ax))
        if len(xs) >= 2:
            xa, xb = min(xs), max(xs)
            for x in range(int(round(xa)), int(round(xb)) + 1):
                px(img, x, y, color)


def terrain():
    img = newimg()
    # iso top diamond
    T, R, B, L = (16, 5), (29, 12), (16, 19), (3, 12)
    # side faces (thickness 7)
    H = 7
    Lp, Bp, Rp = (3, 12 + H), (16, 19 + H), (29, 12 + H)
    # --- side faces first (so top overlaps their upper edge) ---
    fill_poly(img, [L, B, Bp, Lp], SIDE_L)       # left/front-left
    fill_poly(img, [B, R, Rp, Bp], SIDE_R)       # right/front-right
    # --- top face ---
    fill_poly(img, [T, R, B, L], TOP_L)
    # checker on the top face (iso cells)
    cx, cy, hw, hh = 16, 12, 13, 7
    for y in range(5, 20):
        for x in range(3, 30):
            if img.getpixel((x, y))[3] == 0:
                continue
            if img.getpixel((x, y))[:3] != TOP_L:
                continue
            u = (x - cx) / hw + (y - cy) / hh
            v = (x - cx) / hw - (y - cy) / hh
            cell = int((u + 2) * 2.0) + int((v + 2) * 2.0)
            if cell % 2 == 0:
                px(img, x, y, TOP_D)
    # top rim highlight (upper two edges of the diamond)
    def edge(a, b, color):
        steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) or 1
        for i in range(steps + 1):
            t = i / steps
            px(img, round(a[0] + t * (b[0] - a[0])),
               round(a[1] + t * (b[1] - a[1])), color)
    edge(L, T, TOP_RIM)
    edge(T, R, TOP_RIM)
    # outline the silhouette (top two edges + side verticals + base)
    edge(L, T, TOP_RIM)
    for a, b in [(L, Lp), (Lp, Bp), (Bp, Rp), (Rp, R)]:
        edge(a, b, OUT)
    edge(L, B, (120, 100, 60))   # inner crease
    edge(B, R, (120, 100, 60))
    edge(B, Bp, OUT)             # front vertical crease
    # jagged underside teeth (stalactite look) hanging from the base edges
    base = [(5, 18), (8, 20), (11, 19), (14, 21), (16, 20),
            (19, 22), (22, 20), (25, 21), (27, 19)]
    for (bx, by) in base:
        depth = 2 + (bx % 3)
        for d in range(depth):
            px(img, bx, by + d, TEETH)
        px(img, bx, by + depth, OUT)
    return img


def _ellipse(img, cx, cy, rx, ry, fill, rim=None):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1.0:
                px(img, x, y, fill)
            elif d <= 1.45 and rim:
                px(img, x, y, rim)


def telegram():
    """A slightly crooked / wrinkled gold envelope (mail)."""
    img = newimg()
    GOLD = (226, 200, 112)
    GOLD_D = (188, 160, 92)     # body shade
    FLAP = (170, 142, 80)       # flap (shadowed)
    CREASE = (150, 122, 66)
    LIGHT = (246, 230, 170)
    OUTl = (52, 38, 18)

    def edge(a, b, color):
        steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) or 1
        for i in range(steps + 1):
            t = i / steps
            px(img, round(a[0] + t * (b[0] - a[0])),
               round(a[1] + t * (b[1] - a[1])), color)

    # Body quad — corners nudged off-true so it reads hand-folded / crooked.
    TL, TR, BR, BL = (5, 8), (27, 10), (26, 26), (4, 24)
    fill_poly(img, [TL, TR, BR, BL], GOLD)
    # subtle wrinkle shading: a darker band lower-left + a crease
    fill_poly(img, [(4, 20), (15, 22), (14, 25), (4, 24)], GOLD_D)
    # Flap — V from the two top corners down to a centre point.
    C = (16, 19)
    fill_poly(img, [TL, TR, C], FLAP)
    edge(TL, C, LIGHT)
    edge(TR, C, LIGHT)
    # diagonal fold creases on the body (the "crumpled" feel)
    edge((6, 23), (15, 16), CREASE)
    edge((25, 24), (17, 17), CREASE)
    edge(C, (16, 25), CREASE)
    # a small dent on the right edge
    px(img, 26, 16, OUTl)
    px(img, 25, 17, GOLD_D)
    # outline the silhouette
    for a, b in [(TL, TR), (TR, BR), (BR, BL), (BL, TL)]:
        edge(a, b, OUTl)
    return img


def donation():
    """A wide, OPEN-top tip jar with a neat pile of coins (TIPS-jar reference).
    No lid — so the dropping coin can actually fall in through the mouth."""
    img = newimg()
    GLASS = (196, 210, 222)          # pale glass outline
    GLASS_D = (150, 166, 182)        # darker glass (mouth back / shading)
    GLASS_HI = (238, 246, 250)       # glass highlight streak
    GLASS_FILL = (150, 178, 196, 42)  # faint translucent body
    COIN = (228, 200, 106)
    COIN_D = (182, 150, 70)
    COIN_RIM = (246, 230, 156)
    OUTl = (52, 46, 40)

    def edge(a, b, color):
        steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) or 1
        for k in range(steps + 1):
            t = k / steps
            px(img, round(a[0] + t * (b[0] - a[0])),
               round(a[1] + t * (b[1] - a[1])), color)

    # ---- wide rounded jar body (open top) ----
    body = [(6, 8), (4, 13), (3, 19), (5, 25), (9, 28), (14, 29),
            (18, 29), (23, 28), (27, 25), (29, 19), (28, 13), (26, 8)]
    fill_poly(img, body, GLASS_FILL)
    # ---- coins: neat pile at the bottom (3 + 2 + 1) ----

    def coin_at(cx, cy, rx):
        _ellipse(img, cx, cy + 1, rx, 3, OUTl)        # drop shadow / outline
        _ellipse(img, cx, cy, rx, 3, COIN_D)          # body
        _ellipse(img, cx, cy - 1, rx - 1, 2, COIN)    # lit top
        for x in range(cx - rx + 1, cx + rx - 1):     # rim highlight
            px(img, x, cy - 2, COIN_RIM)
    for cx, cy, rx in [(10, 25, 4), (16, 26, 5), (22, 25, 4),
                       (13, 23, 5), (19, 23, 5), (16, 21, 5)]:
        coin_at(cx, cy, rx)
    # ---- glass walls + rounded bottom (drawn over coin edges → seen through) ----
    n = len(body)
    for i in range(n):
        a, b = body[i], body[(i + 1) % n]
        if a[1] < 9 and b[1] < 9:        # skip the open top span
            continue
        edge(a, b, GLASS)
    # ---- open mouth: a CONTIGUOUS ellipse rim that joins the walls (the old
    # 6°-sampled ring left gaps → it looked broken/disconnected at the top). ----
    import math
    cx, cy, rx, ry = 16, 7, 10, 3
    for x in range(cx - rx, cx + rx + 1):
        dx = (x - cx) / rx
        dy = ry * math.sqrt(max(0.0, 1 - dx * dx))
        px(img, x, round(cy - dy), GLASS_D)     # back rim (top, shaded)
        px(img, x, round(cy + dy), GLASS)       # front rim (bottom, lit)
    for y in range(cy - ry, cy + ry + 2):       # side columns close the ring +
        px(img, cx - rx, y, GLASS)              # connect it down into the walls
        px(img, cx + rx, y, GLASS)
    # ---- glass highlight streak (upper-left, kept below the rim so it doesn't
    # read as a stray glint) ----
    for y in range(12, 21):
        px(img, 7, y, GLASS_HI)
    return img


def heart_hollow():
    """Hollow (outline-only) heart, faint red — the drifting particle. Thin 1px
    walls; the CSS starts it tiny and grows it as it flies, so it stays pixel."""
    R = (214, 96, 96, 245)
    rows = [
        ".##...##.",
        "#..#.#..#",
        "#...#...#",
        "#.......#",
        ".#.....#.",
        "..#...#..",
        "...#.#...",
        "....#....",
    ]
    w, h = len(rows[0]), len(rows)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '#':
                im.putpixel((x, y), R)
    return im


def coin():
    """Small gold coin — the donation drop particle."""
    w = 11
    im = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    COIN = (228, 200, 106, 255)
    COIN_D = (182, 150, 70, 255)
    COIN_RIM = (244, 226, 150, 255)
    OUTl = (44, 40, 36, 255)
    cx = cy = 5
    for y in range(w):
        for x in range(w):
            d = ((x - cx) / 5) ** 2 + ((y - cy) / 4.4) ** 2
            if d <= 1.0:
                im.putpixel((x, y), COIN_D if (y - cx) > 1 else COIN)
            elif d <= 1.45:
                im.putpixel((x, y), OUTl)
    # rim highlight + center mark
    for x in range(3, 8):
        im.putpixel((x, 2), COIN_RIM)
    im.putpixel((5, 5), COIN_RIM)
    return im


def back_arrow():
    """Cream-gold gothic LEFT-arrow ornament — echoes divider.png's filigree,
    sits just left of the divider to signal 'back'. ~24x11."""
    A = (255, 232, 215, 255)   # bright
    B = (230, 200, 178, 255)   # mid
    C = (199, 183, 171, 255)   # muted
    rows = [
        "........................",
        ".....A..................",
        "....AA..................",
        "...AAA.B................",
        "..AAAABBBBBBBBBBBBBB.oo..",
        ".AAAAA.B....C...C..C.....",
        "..AAAABBBBBBBBBBBBBB.oo..",
        "...AAA.B................",
        "....AA..................",
        ".....A..................",
        "........................",
    ]
    pal = {"A": A, "B": B, "C": C, "o": (230, 200, 178, 180)}
    w, h = len(rows[0]), len(rows)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                im.putpixel((x, y), pal[ch])
    return im


_32 = [("icon_terrain", terrain), ("icon_telegram", telegram),
       ("icon_donation", donation)]
_RAW = [("heart_hollow", heart_hollow), ("coin", coin),
        ("divider_arrow_left", back_arrow)]
for name, fn in _32 + _RAW:
    im = fn()
    im.save(os.path.join(_OUT_DIR, f"{name}.png"))
    print("wrote", name)

# montage preview (the new support assets)
prev = [n for n, _ in _32 + _RAW]
imgs = [Image.open(os.path.join(_OUT_DIR, f"{n}.png")).convert("RGBA") for n in prev]
PADc = 6
mh = max(i.height for i in imgs) * PADc
mont = Image.new("RGBA", (sum(i.width for i in imgs) * PADc + 20 * len(imgs), mh + 10),
                 (20, 24, 30, 255))
xoff = 6
for i in imgs:
    big = i.resize((i.width * PADc, i.height * PADc), Image.NEAREST)
    mont.alpha_composite(big, (xoff, 6))
    xoff += big.width + 14
mont.save(os.path.join(_ROOT, "_preview_support_icons.png"))
print("montage -> _preview_support_icons.png")
