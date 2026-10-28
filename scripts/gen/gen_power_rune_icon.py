"""The Sloppy site's own icon for "the power runes as a whole" -> icons/runes/power.png (32 px).

The game has no such icon (its HUD power-rune timer icon is the Water rune, owner 2026-10-28), so ours is built from
the game's own power-rune minimap icons (icons/runes/<key>.png, copies of the Terrain page's tc_rune_0..6), in their
style — natural colours, the game's dark outline, light from the top left.

The concept the owner chose (2026-10-28, of three: a bunch of runes / a crystal in seven rune colours / seven gems in
a ring): a bunch of three runes' own icons — Regeneration (green) behind on the left, Haste (red) behind on the right,
Double Damage (blue) bigger in front, so the three colours still read at 19 px (the .ability-chip size).

    python scripts/gen/gen_power_rune_icon.py            # icons/runes/power.png
    python scripts/gen/gen_power_rune_icon.py --sheet    # + .cache/_preview_power_rune.png: it beside the 7 runes
"""
import os
import sys

from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_RUNES = os.path.join(_ROOT, "icons", "runes")
N = 32
# the seven power runes, in the order the Terrain page cycles them (gen_terrain_layer_icons.RUNE_ORDER)
POWER = ["doubledamage", "arcane", "haste", "illusion", "invisibility", "regeneration", "shield"]
# (rune, its size, its top-left corner), back to front
BUNCH = (("regeneration", 20, (0, 1)), ("haste", 20, (12, 1)), ("doubledamage", 22, (5, 10)))


def rune(key, size=N):
    """A rune's game icon (48 px, its outline included) shrunk to fit ``size`` (its proportions kept, centred),
    its edge kept hard."""
    src = Image.open(os.path.join(_RUNES, f"{key}.png")).convert("RGBA")
    src = src.crop(src.getbbox())
    s = size / max(src.size)
    src = src.resize((max(1, round(src.width * s)), max(1, round(src.height * s))), Image.LANCZOS)
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    im.alpha_composite(src, ((size - src.width) // 2, (size - src.height) // 2))
    px = im.load()
    for y in range(size):
        for x in range(size):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)
    return im


def power_icon():
    """The three runes stacked back to front; each keeps its own dark outline, so the front one stands apart."""
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    for key, size, pos in BUNCH:
        im.alpha_composite(rune(key, size), pos)
    return im


def sheet(path, icon):
    """The icon beside the seven runes, each at 19 px (chip), 32 px and 64 px, on the chip's dark ground."""
    icons = [icon] + [rune(k) for k in POWER]
    sizes = (19, 32, 64)
    cell = 80
    out = Image.new("RGBA", (len(icons) * cell, len(sizes) * cell), (26, 22, 19, 255))
    for i, im in enumerate(icons):
        for j, s in enumerate(sizes):
            small = im.resize((s, s), Image.NEAREST if s % N == 0 else Image.LANCZOS)
            out.alpha_composite(small, (i * cell + (cell - s) // 2, j * cell + (cell - s) // 2))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path)
    return path


def main(args):
    im = power_icon()
    im.save(os.path.join(_RUNES, "power.png"))
    print("wrote icons/runes/power.png")
    if "--sheet" in args:
        print("sheet ->", os.path.relpath(sheet(os.path.join(_ROOT, ".cache", "_preview_power_rune.png"), im), _ROOT))


if __name__ == "__main__":
    main(sys.argv[1:])
