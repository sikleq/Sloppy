"""gen_camp_icons.py — the camp-type glyphs at the sizes the site shows them:

    icons/camps/creepcamp_<type>_<size>.png   the game's camp-type glyph (icons/camps/creepcamp_<type>.png, 32 px) as a
                                              crisp file of that size: the same drawing, empty margins cut, every pixel
                                              snapped to the original's own colours, hard edge (the 32 px file shown
                                              smaller blurs, owner 2026-11-19)
    ...@2x.png                                each doubled pixel for pixel, for sharp screens

A camp's creeps are shown as their game portraits (patch/camps.py camp_kind, owner 2026-11-20); the faces and count
plates drawn here on 2026-11-19 were dropped then.

    python scripts/gen/gen_camp_icons.py
Pillow only; the output is the same on every run.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CAMPS = ROOT / "icons" / "camps"

# the type glyph for each size it is shown at (a 32 px file squeezed by the browser blurs): 16 - Neutral Creeps table,
# Terrain buttons / chips / tiles; 20 - entity-change cards; 22 - camp tables. The Terrain map markers keep the 32 px
# file: they scale with the map.
TYPE_SIZES = (16, 20, 22)
TYPES = ("small", "mid", "big", "ancient")


def save(img, path):
    """the 1x file and its pixel-doubled @2x twin"""
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(path.with_name(path.stem + "@2x.png"), optimize=True)


def _palette(im, n=10):
    opaque = Image.new("RGB", im.size)
    opaque.paste(im.convert("RGB"), (0, 0), im.getchannel("A").point(lambda v: 255 if v > 200 else 0))
    pal = opaque.quantize(n, method=Image.Quantize.MEDIANCUT).getpalette()[: n * 3]
    return [tuple(pal[i:i + 3]) for i in range(0, len(pal), 3)]


def type_icon(src, size):
    """the game glyph at `size` px: margins cut, shrunk, each pixel snapped to the source's colours, no soft edge"""
    pal = _palette(src)
    part = src.crop(src.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox())
    side = max(part.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(part, ((side - part.width) // 2, (side - part.height) // 2))
    small = sq.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y in range(size):
        for x in range(size):
            r, g, b, a = small.getpixel((x, y))
            if a >= 110:
                best = min(pal, key=lambda p: (p[0] - r) ** 2 + (p[1] - g) ** 2 + (p[2] - b) ** 2)
                out.putpixel((x, y), best + (255,))
    return out


def main():
    for t in TYPES:
        src = Image.open(CAMPS / f"creepcamp_{t}.png").convert("RGBA")
        for size in TYPE_SIZES:
            save(type_icon(src, size), CAMPS / f"creepcamp_{t}_{size}.png")
    print(f"camp glyphs: {len(TYPES)} types x {len(TYPE_SIZES)} sizes")


if __name__ == "__main__":
    main()
