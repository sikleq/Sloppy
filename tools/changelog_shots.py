"""Screenshots for the site changelog (icons/changelog/*.webp).

Serves nothing itself: point it at a running copy of dist/ (default http://localhost:8799,
`python -m http.server 8799` from dist/). Each shot = a page + either a CSS selector for
one block (optionally the block that contains some text) or the top of the page.

    python tools/changelog_shots.py            # all shots
    python tools/changelog_shots.py tormentor  # shots whose file name contains "tormentor"
"""
import io
import pathlib
import re
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "changelog"
BASE = "http://localhost:8799/"
MAX_H = 760            # tall blocks are cut to a readable preview
WIDTH = 1280

# (file, page, selector or None for the page top, text the block must contain)
SHOTS = [
    ("2026-09-24_tormentor.webp", "patches/7.38.html", ".entity-block", r"^Tormentor"),
    ("2026-09-24_lifesteal.webp", "patches/7.38.html", ".entity-block", r"^Lifesteal"),
    ("2026-09-24_abyssal.webp", "patches/7.38.html", ".entity-block", r"^Abyssal Blade"),
    ("2026-09-23_roshan.webp", "units/roshan.html", None, None),
    ("2026-09-22_unit_changes.webp", "unit_changes.html", None, None),
    ("2026-09-17_hero_changes.webp", "hero_changes.html", None, None),
]


def _save(png_bytes, name):
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    if img.height > MAX_H:
        img = img.crop((0, 0, img.width, MAX_H))
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / name, "WEBP", quality=82, method=6)
    print(f"  {name}: {img.width}x{img.height}")


def main(only=None):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": 900})
        for name, url, sel, text in SHOTS:
            if only and only not in name:
                continue
            page.goto(BASE + url, wait_until="networkidle")
            if sel is None:
                _save(page.screenshot(), name)
                continue
            block = page.locator(sel, has=page.locator(".entity-name", has_text=re.compile(text))).first
            block.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            _save(block.screenshot(), name)
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
