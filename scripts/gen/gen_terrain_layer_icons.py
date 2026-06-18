"""Generate the terrain-page layer icons -> icons/ui/gothic/tc_<name>.png (ICON_RES).

Each icon is a smooth adaptation of the GAME map icon in icons/ref/, fit + tinted
to its layer's type colour (or kept NATURAL for bounty + the power runes) with a
soft dark outline. The same PNG is the toolbar button AND the map marker
(builders/terrain.py wraps the map one in a gold ring over a dark/colour disc).

Refs (icons/ref/): towers.svg, roashan.svg, tormentor_png.png,
Bounty_Rune_mapicon_dota2_gameasset.png, watcher_lantern.png, and
lotus_pool_sheet / twin_gate_sheet / outpost_sheet (cells cut from the
minimap_sheet). Power = 7 runes in runes/ (cycled by scripts.js). Wisdom has no
game icon → drawn custom (wisdom_icon: a dense purple inner ring + glow).

SVGs are rasterised with ImageMagick (`magick`). Run::
    python scripts/gen/gen_terrain_layer_icons.py
"""
import os
import shutil
import subprocess
from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUT = os.path.join(_ROOT, "icons", "ui", "gothic")
_REF = os.path.join(_ROOT, "icons", "ref")
N = 16
OUTLINE = (20, 17, 14, 255)

# Per-layer base colour (used for the icon fill AND the map marker's faint disc).
COLORS = {
    "tc_towers":     (74, 144, 226),    # blue
    "tc_lotus":      (255, 122, 181),   # pink
    "tc_twingates":  (126, 200, 255),   # bluish (голубоватый)
    "tc_tormentors": (255, 106, 74),    # red
    "tc_bounty":     (244, 198, 58),    # gold
    "tc_power":      (95, 208, 106),    # green
    "tc_wisdom":     (155, 127, 199),   # dull purple (тускло фиолетовый)
    "tc_outposts":   (255, 154, 60),    # orange
    "tc_watchers":   (86, 214, 208),    # cyan (vision)
    "tc_roshan":     (210, 74, 90),     # crimson
}

# Layers backed by a game icon in icons/ref/.
REFS = {
    "tc_towers":     "towers.svg",
    "tc_roshan":     "roashan.svg",
    "tc_tormentors": "tormentor_png.png",
    "tc_lotus":      "lotus_pool_sheet.png",     # from minimap_sheet (r9,c5)
    "tc_twingates":  "twin_gate_sheet.png",      # from minimap_sheet (r9,c4)
    "tc_outposts":   "outpost_sheet.png",        # from minimap_sheet (r2,c0)
    "tc_bounty":     "Bounty_Rune_mapicon_dota2_gameasset.png",  # natural (see NATURAL)
    "tc_watchers":   "watcher_lantern.png",
    # tc_power is special — its icon cycles through the 7 power runes (see the
    # RUNE_ORDER block below), so it's NOT generated via this REFS table.
}

# The 7 power runes (icons/ref/runes/, downloaded from liquipedia). Kept in their
# NATURAL colours (so they're distinguishable) — build_terrain wraps each marker
# in the faint-GREEN power disc; scripts.js cycles tc_rune_0..6 every 3s on the
# map. tc_power.png (button default + initial marker) = the regeneration rune.
RUNE_ORDER = ["amplify_damage", "arcane", "haste", "illusion",
              "invisibility", "regeneration", "shield"]

# Fallback glyphs for layers without a game icon yet ('#' fill, 'o' shade).
# Wisdom Shrine has no game minimap icon → drawn custom (see wisdom_icon).
FALLBACK = {}


def _shades(rgb):
    base = rgb + (255,)
    dark = tuple(int(c * 0.5) for c in rgb) + (255,)
    return {"#": base, "o": dark, "*": base}


def _outline(im):
    w, h = im.size
    src = im.load()
    out = im.copy()
    dst = out.load()
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]
    for y in range(h):
        for x in range(w):
            if src[x, y][3] != 0:
                continue
            if any(0 <= x + dx < w and 0 <= y + dy < h and src[x + dx, y + dy][3] != 0
                   for dx, dy in nb):
                dst[x, y] = OUTLINE
    return out


def _load_ref(fname):
    path = os.path.join(_REF, fname)
    if fname.lower().endswith(".svg"):
        magick = shutil.which("magick") or shutil.which("convert")
        if not magick:
            raise RuntimeError("ImageMagick (magick) needed to rasterise " + fname)
        tmp = path + ".raster.png"
        subprocess.run([magick, "-background", "none", "-density", "300",
                        path, "-resize", "128x128", tmp], check=True)
        im = Image.open(tmp).convert("RGBA")
        os.remove(tmp)
        return im
    return Image.open(path).convert("RGBA")


# Output at 2x (32px) so the game icons keep their FORM (the 16px hard-pixel
# downscale destroyed the tower's arrow-top, Roshan's fangs, the bounty ring).
# These are displayed small + smooth (NOT pixelated) so they read like the real
# minimap icons.
ICON_RES = 48
PAD = 3


def from_ref(fname, color, tint=True):
    """Trim the game icon, FILL the ICON_RES canvas (upscaling small sources like
    the 32px rune mapicons), recolour, sharpen, then add a thin dark outline. The
    fill + unsharp keep the icons crisp instead of muddy at marker size. ``tint``
    recolours to the type colour; ``tint=False`` keeps natural colours (runes)."""
    from PIL import ImageFilter
    im = _load_ref(fname)
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    # fill the canvas, preserving aspect (UPSCALE small sources too)
    target = ICON_RES - 2 * PAD
    w, h = im.size
    s = target / max(w, h)
    im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    out = Image.new("RGBA", (ICON_RES, ICON_RES), (0, 0, 0, 0))
    ox = (ICON_RES - im.width) // 2
    oy = (ICON_RES - im.height) // 2
    src = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = src[x, y]
            if a == 0:
                continue
            if tint:
                # Tint white-silhouette game icons (towers/roshan/…) to the type
                # colour, keeping the ref's light/shade. No lightening — the dark
                # marker backing already gives contrast, so a saturated colour
                # reads while staying true to the icon.
                lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                f = (0.52 + 0.6 * lum) * 1.12
                out.putpixel((ox + x, oy + y),
                             (min(255, int(color[0] * f)),
                              min(255, int(color[1] * f)),
                              min(255, int(color[2] * f)), a))
            else:
                out.putpixel((ox + x, oy + y), (r, g, b, a))   # natural colours
    # crisp up the (often upscaled) icon so it survives the shrink to marker size
    out = out.filter(ImageFilter.UnsharpMask(radius=1.4, percent=130, threshold=2))
    # thin dark outline (dilate the alpha, fill dark, icon on top)
    dil = out.split()[3].filter(ImageFilter.MaxFilter(3))
    ol = Image.new("RGBA", out.size, (20, 17, 14, 255))
    ol.putalpha(dil)
    return Image.alpha_composite(ol, out)


def from_glyph(rows, color):
    """Hand-drawn fallback glyph (16px), upscaled 2x so it shares ICON_RES."""
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    pal = _shades(color)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            c = pal.get(ch)
            if c:
                im.putpixel((x, y), c)
    return _outline(im).resize((ICON_RES, ICON_RES), Image.NEAREST)


def wisdom_icon(color):
    """Wisdom Shrine has no in-game minimap icon, so we draw one: a DENSE bright
    purple inner ring (where the shrine's capture glow starts) with that glow
    radiating inward. Drawn at 4x + downscaled for smooth anti-aliasing."""
    from PIL import ImageDraw
    S = ICON_RES * 4
    cx = cy = S / 2
    ring_r = S * 0.32
    ring_w = S * 0.12
    bright = tuple(min(255, int(c * 1.45) + 30) for c in color)   # dense purple
    glow = color
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    for y in range(S):
        for x in range(S):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if abs(d - ring_r) <= ring_w / 2:
                px[x, y] = bright + (255,)                 # the dense ring
            elif d < ring_r - ring_w / 2:
                t = d / (ring_r - ring_w / 2)              # 0 centre … 1 ring
                px[x, y] = glow + (int(150 * t * t),)      # inward glow
    img = img.resize((ICON_RES, ICON_RES), Image.LANCZOS)
    # thin dark outline so the ring reads on the marker disc
    from PIL import ImageFilter
    dil = img.split()[3].filter(ImageFilter.MaxFilter(3))
    ol = Image.new("RGBA", img.size, (20, 17, 14, 255))
    ol.putalpha(dil)
    return Image.alpha_composite(ol, img)


# Icons kept in their NATURAL colours (the game icon is already the right colour
# + reads on the dark marker backing) instead of tinted to the type colour.
NATURAL = {"tc_bounty"}

cells = []
for name, color in COLORS.items():
    if name == "tc_power":
        continue                     # generated from the rune set below
    if name == "tc_wisdom":
        im = wisdom_icon(color)      # custom (no game icon)
    elif name in REFS:
        im = from_ref(REFS[name], color, tint=(name not in NATURAL))
    else:
        im = from_glyph(FALLBACK[name], color)
    im.save(os.path.join(_OUT, f"{name}.png"))
    cells.append((name, im))
    print("wrote", name)

# ---- 7 power runes (natural colours) → tc_rune_0..6.png; tc_power.png defaults
# to the regeneration rune (green, matches the layer). scripts.js cycles them. ----
for i, nm in enumerate(RUNE_ORDER):
    im = from_ref(f"runes/{nm}.png", (255, 255, 255), tint=False)
    im.save(os.path.join(_OUT, f"tc_rune_{i}.png"))
    cells.append((f"tc_rune_{i}", im))
    print("wrote", f"tc_rune_{i} ({nm})")
Image.open(os.path.join(_OUT, "tc_rune_5.png")).save(os.path.join(_OUT, "tc_power.png"))
print("wrote tc_power (= regeneration default)")

# montage on mid-grey so the dark outline reads
cols = 5
rows_n = (len(cells) + cols - 1) // cols
mont = Image.new("RGBA", (cols * ICON_RES * 3, rows_n * ICON_RES * 3), (70, 78, 64, 255))
for i, (name, im) in enumerate(cells):
    big = im.resize((ICON_RES * 3, ICON_RES * 3), Image.NEAREST)
    mont.alpha_composite(big, ((i % cols) * ICON_RES * 3, (i // cols) * ICON_RES * 3))
mont.save(os.path.join(_ROOT, "_preview_tc_icons.png"))
print("montage -> _preview_tc_icons.png")
