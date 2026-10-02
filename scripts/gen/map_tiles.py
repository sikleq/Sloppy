"""Zoom tiles of a full map render: the Terrain page's fullscreen zoom loads them over the 4096 picture once a picture
pixel would be drawn bigger than a screen pixel (the owner 2026-10-02: "is this quality normal when zoomed?").

The 4096 site picture is the full render (2 units/px, 9999 x 10425) squeezed into a square; the tiles are the same
square at 8192, cut 16 x 16 into 512-px webp — twice as sharp, ~10 MB a map. They live in Oldgrowth
(tiles/<ver>/<row>_<col>.webp, served by its GitHub Pages; the owner chose that over growing Sloppy).

    python scripts/gen/map_tiles.py FULL.png OUT_DIR
"""
import argparse
import os

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
SIZE = 8192
GRID = 16                 # tiles per side -> 512 px each
QUALITY = 78


def tiles(full, size=SIZE, grid=GRID):
    """[(row, col, tile image)] of the full render squeezed into a size x size square."""
    sq = full.convert("RGB").resize((size, size), Image.LANCZOS)
    t = size // grid
    return [(r, c, sq.crop((c * t, r * t, (c + 1) * t, (r + 1) * t))) for r in range(grid) for c in range(grid)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("full")
    ap.add_argument("out_dir")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    total = 0
    for r, c, im in tiles(Image.open(args.full)):
        path = os.path.join(args.out_dir, f"{r}_{c}.webp")
        im.save(path, "WEBP", quality=QUALITY, method=6)
        total += os.path.getsize(path)
    print(f"{GRID * GRID} tiles, {total / 1e6:.1f} MB -> {args.out_dir}")


if __name__ == "__main__":
    main()
