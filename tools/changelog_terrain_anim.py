"""Animated changelog shots of the Terrain page: one map layer's changes on several maps (the owner 2026-10-03: "an
animation of examples with the trees on, in different modes and on different maps"; then "add screenshot animations
of the other layers").

For each patch the layer's "Changed in the map file" chip is pressed (it turns the layer on and outlines the
changes); the trees go through every mode — everything, then only what moved, what was removed and what was added —
the other layers show everything. Each frame is the map (.tc-stage) under a caption.
-> icons/changelog/2026-10-03_terrain_<layer>_anim.webp (the trees: _trees_modes.webp), animated, looped.
Needs dist/ served at http://localhost:8799 like tools/changelog_shots.py.

    python tools/changelog_terrain_anim.py            # every layer
    python tools/changelog_terrain_anim.py camps      # one
"""
import io
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "icons" / "changelog"
BASE = "http://localhost:8799/"
MOVED, REMOVED, ADDED = (255, 210, 63), (255, 77, 77), (93, 255, 138)
# (label, swatch colour or None, kinds shown)
ALL = (("all changes", None, ("moved", "removed", "added")),)
MODES = ALL + (("moved", MOVED, ("moved",)),
               ("removed", REMOVED, ("removed",)),
               ("added", ADDED, ("added",)))
# chip key -> (caption, patches whose Terrain page has the chip, modes, file name)
LAYERS = {
    "trees": ("Trees", ("7.38", "7.39", "7.40", "7.41"), MODES, "2026-10-03_terrain_trees_modes.webp"),
    # the other layers show in the slider sweeps (tools/changelog_terrain_sweep.py, the owner 2026-10-04: no two
    # news with the same layer animation); add one back here as ("Camps", patches, ALL, file) if a news needs it
}
# what the outline colours mean, per layer ("all changes" frames)
LEGEND = {"nowards": (("wards allowed", REMOVED), ("no wards", ADDED))}
DEFAULT_LEGEND = (("moved", MOVED), ("removed", REMOVED), ("added", ADDED))
SIDE = 720            # px of the map in a frame
HEAD = 40
FRAME_MS = 1300
BG, GOLD, TEXT = (14, 12, 9), (227, 196, 106), (230, 222, 205)
FONT = ROOT / "src" / "fonts" / "radiance-semibold.otf"


def caption(img, patch, layer, label, colour, legend=DEFAULT_LEGEND):
    """The map under "<patch>  <layer>: <mode>"; "all changes" spells out the outline colours."""
    frame = Image.new("RGB", (SIDE, SIDE + HEAD), BG)
    frame.paste(img, (0, HEAD))
    d = ImageDraw.Draw(frame)
    big, small = ImageFont.truetype(str(FONT), 22), ImageFont.truetype(str(FONT), 18)
    d.text((12, 8), patch, font=big, fill=GOLD)
    x = 12 + d.textlength(patch, font=big) + 18
    d.text((x, 11), layer + ":", font=small, fill=TEXT)
    x += d.textlength(layer + ":", font=small) + 10
    for word, c in (((label, colour),) if colour else legend):
        d.rectangle([x, 14, x + 13, 27], outline=c, width=2)
        x += 21
        d.text((x, 11), word, font=small, fill=c)
        x += d.textlength(word, font=small) + 16
    return frame


def frames(page, key):
    layer, patches, modes, _name = LAYERS[key]
    out = []
    for patch in patches:
        page.goto(f"{BASE}terrain_{patch.replace('.', '')}.html", wait_until="load")
        page.wait_for_timeout(1200)
        page.locator(f'.terrain-facts .tf-chip-btn[data-hl="{key}"]').first.click()
        for label, colour, kinds in modes:
            page.evaluate("""kinds => {
                const root = document.querySelector('.terrain-compare');
                ['moved', 'removed', 'added'].forEach(k => root.classList.toggle('hl-hide-' + k, !kinds.includes(k)));
            }""", list(kinds))
            page.wait_for_timeout(250)
            png = page.locator(".tc-stage").screenshot()
            img = Image.open(io.BytesIO(png)).convert("RGB").resize((SIDE, SIDE), Image.LANCZOS)
            out.append(caption(img, patch, layer, label, colour, LEGEND.get(key, DEFAULT_LEGEND)))
    return out


def main(only):
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1400, "height": 1000}, device_scale_factor=1.5)
        for key, (_layer, _patches, _modes, name) in LAYERS.items():
            if only and key not in only:
                continue
            fs = frames(page, key)
            out = OUT_DIR / name
            fs[0].save(out, "WEBP", save_all=True, append_images=fs[1:], duration=FRAME_MS, loop=0, quality=74,
                       method=6)
            print(out.name, len(fs), "frames", round(out.stat().st_size / 1024), "KB")
        b.close()


if __name__ == "__main__":
    main(sys.argv[1:])
