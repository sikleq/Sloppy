"""Animated changelog shot: the Terrain page's tree changes in each mode on several maps, for comparison (the owner
2026-10-03: "an animation of examples with the trees on, in different modes and on different maps").

For each patch the trees chip is pressed and the kind switches show everything, then only what moved, what was removed
and what was added; each frame is the map (.tc-stage) under a caption. -> icons/changelog/<name>.webp (animated, looped).
Needs dist/ served at http://localhost:8799 like tools/changelog_shots.py.

    python tools/changelog_terrain_anim.py
"""
import io
import pathlib

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "changelog" / "2026-10-03_terrain_trees_modes.webp"
BASE = "http://localhost:8799/"
PATCHES = ("7.38", "7.39", "7.40", "7.41")
# (label, swatch colour or None, kinds shown)
MODES = (("all changes", None, ("moved", "removed", "added")),
         ("moved", (255, 210, 63), ("moved",)),
         ("removed", (255, 77, 77), ("removed",)),
         ("added", (93, 255, 138), ("added",)))
SIDE = 720            # px of the map in a frame
HEAD = 40
FRAME_MS = 1300
BG, GOLD, TEXT = (14, 12, 9), (227, 196, 106), (230, 222, 205)
FONT = ROOT / "src" / "fonts" / "radiance-semibold.otf"


def caption(img, patch, label, colour):
    frame = Image.new("RGB", (SIDE, SIDE + HEAD), BG)
    frame.paste(img, (0, HEAD))
    d = ImageDraw.Draw(frame)
    big, small = ImageFont.truetype(str(FONT), 22), ImageFont.truetype(str(FONT), 18)
    d.text((12, 8), patch, font=big, fill=GOLD)
    x = 12 + d.textlength(patch, font=big) + 18
    d.text((x, 11), "Trees:", font=small, fill=TEXT)
    x += d.textlength("Trees:", font=small) + 10
    if colour:
        d.rectangle([x, 14, x + 13, 27], outline=colour, width=2)
        x += 21
    d.text((x, 11), label, font=small, fill=colour or TEXT)
    return frame


def frames():
    out = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1400, "height": 1000}, device_scale_factor=1.5)
        for patch in PATCHES:
            page.goto(f"{BASE}terrain_{patch.replace('.', '')}.html", wait_until="load")
            page.wait_for_timeout(1200)
            page.locator('.terrain-facts .tf-chip-btn[data-hl="trees"]').first.click()
            for label, colour, kinds in MODES:
                page.evaluate("""kinds => {
                    const root = document.querySelector('.terrain-compare');
                    ['moved', 'removed', 'added'].forEach(k => root.classList.toggle('hl-hide-' + k, !kinds.includes(k)));
                }""", list(kinds))
                page.wait_for_timeout(250)
                png = page.locator(".tc-stage").screenshot()
                img = Image.open(io.BytesIO(png)).convert("RGB").resize((SIDE, SIDE), Image.LANCZOS)
                out.append(caption(img, patch, label, colour))
        b.close()
    return out


def main():
    fs = frames()
    fs[0].save(OUT, "WEBP", save_all=True, append_images=fs[1:], duration=FRAME_MS, loop=0, quality=74, method=6)
    print(OUT.name, len(fs), "frames", round(OUT.stat().st_size / 1024), "KB")


if __name__ == "__main__":
    main()
