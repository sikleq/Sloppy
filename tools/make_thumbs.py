"""Small WebP copies of the hero / item / ability icons for the patch & Changes pages.

The pages show these icons at 80x45 (hero), 62x45 (item) and 45x45 (ability), but the
source PNGs are 256x144 / 88x64 / 128x128 — 7.41 alone pulled ~25 MB of PNG, and decoding
them while scrolling cost frames (perf probe: p95 33 ms, 16.8 ms with images hidden).
The thumbnails are 2x the display size (sharp on HiDPI) and live in icons/_t/<dir>/<name>.webp;
patch/page.py points the pages at them when a thumbnail exists (falls back to the PNG).

Run after adding / updating icons (re-creates only missing or outdated thumbnails):
    python tools/make_thumbs.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
# folder -> target width (2x the rendered width in styles.css)
TARGETS = {"heroes": 160, "items": 124, "abilities": 96}


def main():
    made = skipped = 0
    for folder, width in TARGETS.items():
        src_dir, dst_dir = ROOT / "icons" / folder, ROOT / "icons" / "_t" / folder
        dst_dir.mkdir(parents=True, exist_ok=True)
        for src in sorted(src_dir.glob("*.png")):
            dst = dst_dir / (src.stem + ".webp")
            if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
                skipped += 1
                continue
            try:
                im = Image.open(src)
                im.load()
            except (OSError, ValueError):          # not a raster PNG (e.g. an SVG saved as .png)
                skipped += 1
                continue
            with im:
                im = im.convert("RGBA")
                if im.width > width:
                    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
                im.save(dst, "WEBP", quality=88, method=6)
            made += 1
    print(f"thumbnails: {made} made, {skipped} up to date")


if __name__ == "__main__":
    main()
