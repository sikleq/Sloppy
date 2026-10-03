"""2048-px copies of the Terrain map pictures: icons/maps/map_<ver>.webp -> icons/maps/map_<ver>_2k.webp.

A Terrain page opens on the small copy (~0.85 MB instead of ~4.2 MB per picture, two pictures a page) and loads the
4096 picture only once a picture pixel would be drawn bigger than a screen pixel: a big retina screen, the lens,
fullscreen zoom (src/scripts.js fitSrc; the owner 2026-10-03: "on weak computers it may lag").

    python scripts/gen/map_small.py          # every picture whose copy is missing or older
"""
import glob
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAPS = os.path.join(ROOT, "icons", "maps")
SIZE = 2048
QUALITY = 82
SUFFIX = "_2k"


def small_name(path):
    """icons/maps/map_7.41.webp -> icons/maps/map_7.41_2k.webp."""
    stem, ext = os.path.splitext(path)
    return f"{stem}{SUFFIX}{ext}"


def pictures(maps=MAPS):
    """The full map pictures (not the copies)."""
    return sorted(p for p in glob.glob(os.path.join(maps, "map_*.webp"))
                  if not os.path.splitext(p)[0].endswith(SUFFIX))


def make(path, size=SIZE):
    """Write the small copy of one picture; returns its path."""
    out = small_name(path)
    with Image.open(path) as im:
        im.convert("RGB").resize((size, size), Image.LANCZOS).save(out, "WEBP", quality=QUALITY, method=6)
    return out


def main():
    made = 0
    for path in pictures():
        out = small_name(path)
        if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(path):
            continue
        make(path)
        made += 1
        print(f"{os.path.basename(out)}: {os.path.getsize(out) / 1e6:.2f} MB "
              f"(full {os.path.getsize(path) / 1e6:.2f} MB)")
    print(f"{made} made")


if __name__ == "__main__":
    main()
