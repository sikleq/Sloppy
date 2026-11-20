"""Square chip icons of the neutral enchantments, cut to their art (owner 2026-11-20, 7.42 Item Potency: "иконка нейтралки
меньше чем у других"). An enchantment's picture is a small round glyph on a wide dark field (88x64, the art ~45x40 in the
middle): in a 19 px chip it read half the size of an ability's square. icons/items/enhancement_<x>.png ->
icons/items/chip/enhancement_<x>.png, 64x64, the art's bounding square plus a little air.

    python scripts/gen/gen_enchant_chips.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "icons" / "items"
OUT = SRC / "chip"
LIGHT = 120          # a pixel brighter than this (r+g+b) is the art, the rest the dark field
SIZE = 64


def art_box(im):
    px, (w, h) = im.load(), im.size
    pts = [(x, y) for x in range(w) for y in range(h) if sum(px[x, y][:3]) > LIGHT]
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 3
    return (max(0, int(cx - half)), max(0, int(cy - half)), min(w, int(cx + half) + 1), min(h, int(cy + half) + 1))


def main():
    OUT.mkdir(exist_ok=True)
    n = 0
    for p in sorted(SRC.glob("enhancement_*.png")):
        im = Image.open(p).convert("RGBA")
        box = art_box(im)
        if not box:
            raise SystemExit(f"no art found in {p.name}")
        im.crop(box).resize((SIZE, SIZE), Image.LANCZOS).save(OUT / p.name)
        n += 1
    if not n:
        raise SystemExit("no enchantment icons in icons/items")
    print(f"{n} enchantment chips -> {OUT}")


if __name__ == "__main__":
    main()
