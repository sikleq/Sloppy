"""The Sloppy site's own icon for "the power runes as a whole" -> icons/runes/power.png (32 px, a patch row's chip)
and icons/ui/gothic/tc_power.png (48 px, the Terrain page's Power layer button, owner 2026-10-28).

The game has no such icon (its HUD power-rune timer icon is the Water rune, owner 2026-10-28), so ours is built from
the game's own power-rune minimap icons (the Terrain page's tc_rune_0..6, which icons/runes/<key>.png copy), in their
style — natural colours, the game's dark outline, light from the top left.

The concept the owner chose (2026-10-28, of three: a bunch of runes / a crystal in seven rune colours / seven gems in
a ring): a bunch of three runes' own icons — Regeneration (green) behind on the left, Haste (red) behind on the right,
Double Damage (blue) bigger in front, so the three colours still read at 19 px (the .ability-chip size).

    python scripts/gen/gen_power_rune_icon.py            # both (gen_terrain_layer_icons.py tc_power runs it too)
    python scripts/gen/gen_power_rune_icon.py --sheet    # + .cache/_preview_power_rune.png: it beside the 7 runes
"""
import os
import sys

from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_GOTHIC = os.path.join(_ROOT, "icons", "ui", "gothic")
N = 32
# the seven power runes, in the order the Terrain page cycles them (gen_terrain_layer_icons.RUNE_ORDER: tc_rune_<i>)
POWER = ["doubledamage", "arcane", "haste", "illusion", "invisibility", "regeneration", "shield"]
# (rune, its size, its top-left corner) on the 32-px canvas, back to front
BUNCH = (("regeneration", 20, (0, 1)), ("haste", 20, (12, 1)), ("doubledamage", 22, (5, 10)))
# where it goes: (file, its size)
OUTPUTS = ((os.path.join(_ROOT, "icons", "runes", "power.png"), N), (os.path.join(_GOTHIC, "tc_power.png"), 48))


def rune(key, size=N):
    """A rune's game icon (48 px, its outline included) shrunk to fit ``size`` (its proportions kept, centred),
    its edge kept hard."""
    src = Image.open(os.path.join(_GOTHIC, f"tc_rune_{POWER.index(key)}.png")).convert("RGBA")
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


def power_icon(n=N):
    """The three runes stacked back to front on an ``n``-px canvas (the 32-px layout scaled, each rune drawn at its
    own size there, not blown up); each keeps its own dark outline, so the front one stands apart."""
    k = n / N
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    for key, size, (x, y) in BUNCH:
        im.alpha_composite(rune(key, round(size * k)), (round(x * k), round(y * k)))
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
    for path, n in OUTPUTS:
        power_icon(n).save(path)
        print("wrote", os.path.relpath(path, _ROOT))
    if "--sheet" in args:
        print("sheet ->", os.path.relpath(sheet(os.path.join(_ROOT, ".cache", "_preview_power_rune.png"),
                                                power_icon()), _ROOT))


if __name__ == "__main__":
    main(sys.argv[1:])
