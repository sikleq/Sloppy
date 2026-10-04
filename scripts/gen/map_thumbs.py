"""icons/maps/thumbs/<sha8>.webp — a tiny square of every map file for Terrain Stats (the owner 2026-10-04: instead of
the word "picture", "something shorter — a little square?"), linking to its full picture. From Oldgrowth's
versions/<patch>/map.webp (local), 56 px (shown at 28 css px):

    python scripts/gen/map_thumbs.py [path/to/Oldgrowth]
"""
import json
import os
import sys

from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OG = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("OLDGROWTH_DIR", os.path.join(os.path.expanduser("~"), "Documents", "Oldgrowth"))
OUT = os.path.join(_ROOT, "icons", "maps", "thumbs")
SIZE = 56
Image.MAX_IMAGE_PIXELS = None


def main():
    with open(os.path.join(_ROOT, "data", "map", "map_history.json"), encoding="utf-8") as f:
        rows = [r for r in json.load(f)["patches"] if "n" in r]
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for r in rows:
        dest = os.path.join(OUT, f"{r['sha8']}.webp")
        if os.path.exists(dest):
            continue
        im = Image.open(os.path.join(OG, "versions", r["patch"], "map.webp")).convert("RGB")
        im.thumbnail((SIZE, SIZE), Image.LANCZOS)
        im.save(dest, "WEBP", quality=80, method=6)
        made += 1
    print(made, "made,", len(rows), "map files ->", os.path.relpath(OUT, _ROOT))


if __name__ == "__main__":
    main()
