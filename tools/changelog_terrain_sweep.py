"""Animated changelog / post shots of the Terrain page: the slider sweeps from the old map to the new one and back,
with one layer or a set of chips on (the owner 2026-10-04: "animations where the slider moves from the old to the
new map, showing the trees layer on one patch, how objects were moved, no-ward ground, …").

Each scene opens a Terrain page, presses its chips / layer buttons, sets the slider the way scripts.js apply() does
(the split layers' clip-path + the handle's left) and shoots the map (.tc-stage), cropped to a part of it.
-> icons/changelog/2026-10-04_sweep_<scene>.webp (animated, looped). Needs dist/ served at http://localhost:8799.

    python tools/changelog_terrain_sweep.py            # every scene and still
    python tools/changelog_terrain_sweep.py trees      # one (a scene key or a STILLS file name)
"""
import io
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "icons" / "changelog"
BASE = "http://localhost:8799/"
FONT = ROOT / "src" / "fonts" / "radiance-semibold.otf"
BG, GOLD, TEXT = (14, 12, 9), (227, 196, 106), (230, 222, 205)
SIDE, HEAD = 720, 40
# scene -> (page patch, caption, clicks, crop as fractions of the map (x0, y0, x1, y1))
SCENES = {
    "trees": ("7.40", "Trees", ['.terrain-facts .tf-chip-btn[data-hl="trees"]'], (0.0, 0.0, 0.55, 0.55)),
    "objects": ("7.41", "Camps, towers, watchers, Twin Gates, Lotus Pools",
                [f'.terrain-facts .tf-chip-btn[data-hl="{k}"]' for k in
                 ("camps", "towers", "watchers", "twinGates", "lotus", "tormentors")], (0.0, 0.0, 1.0, 1.0)),
    "nowards": ("7.38", "No-ward ground", ['.terrain-facts .tf-chip-btn[data-hl="nowards"]'], (0.0, 0.0, 0.6, 0.6)),
    "all_layers": ("7.41", "All layers", ['.tc-layer-btn[data-layer="all"]'], (0.25, 0.25, 0.75, 0.75)),
}
# still close-ups: name -> (page patch, clicks, crop, slider position (100 = all old)), shot at triple scale
STILLS = {
    "2026-10-04_terrain_dashes.webp": ("7.40", ['.terrain-facts .tf-chip-btn[data-hl="trees"]'],
                                       (0.05, 0.085, 0.16, 0.195), 100),
}
STILL_SCALE = 8                        # device pixels per CSS pixel: the outlines are vector, they stay sharp
HOLD, SWEEP = 8, 22                    # frames resting on a map, frames of one sweep
HOLD_MS, SWEEP_MS = 110, 60

APPLY = """p => {
    const root = document.querySelector('.terrain-compare');
    const nw = 'inset(0 0 0 ' + p + '%)', od = 'inset(0 ' + (100 - p) + '% 0 0)';
    root.querySelectorAll('.tc-new-layer, .tm-new, .tc-trees-new, .tc-camps-new, .tc-lens-new')
        .forEach(el => { el.style.clipPath = nw; });
    root.querySelectorAll('.tm-old, .tc-trees-old, .tc-camps-old').forEach(el => { el.style.clipPath = od; });
    const h = root.querySelector('.tc-handle');
    if (h) h.style.left = p + '%';
}"""


def caption(img, patch, label):
    frame = Image.new("RGB", (SIDE, SIDE + HEAD), BG)
    frame.paste(img, (0, HEAD))
    d = ImageDraw.Draw(frame)
    big, small = ImageFont.truetype(str(FONT), 22), ImageFont.truetype(str(FONT), 18)
    d.text((12, 8), patch, font=big, fill=GOLD)
    d.text((12 + d.textlength(patch, font=big) + 18, 11), label, font=small, fill=TEXT)
    return frame


def scene(page, key):
    patch, label, clicks, crop = SCENES[key]
    page.goto(f"{BASE}terrain_{patch.replace('.', '')}.html", wait_until="load")
    page.wait_for_timeout(1500)
    for sel in clicks:
        loc = page.locator(sel)
        if loc.count():
            loc.first.click()
            page.wait_for_timeout(150)
    page.wait_for_timeout(800)
    stage = page.locator(".tc-stage")
    positions = ([100] * HOLD + [100 - 100 * (i + 1) / SWEEP for i in range(SWEEP)] + [0] * HOLD
                 + [100 * (i + 1) / SWEEP for i in range(SWEEP)])
    frames, durations, last = [], [], None
    for p in positions:
        if p != last:
            page.evaluate(APPLY, p)
            page.wait_for_timeout(40)
            im = Image.open(io.BytesIO(stage.screenshot())).convert("RGB")
            w, h = im.size
            box = (round(crop[0] * w), round(crop[1] * h), round(crop[2] * w), round(crop[3] * h))
            shot = caption(im.crop(box).resize((SIDE, SIDE), Image.LANCZOS), patch, label)
            last = p
        frames.append(shot)
        durations.append(HOLD_MS if p in (0, 100) else SWEEP_MS)
    return frames, durations


def still(b, name):
    """A sharp close-up of part of the map (e.g. the old side's dashed tree outlines)."""
    patch, clicks, crop, pos = STILLS[name]
    page = b.new_page(viewport={"width": 1400, "height": 1000}, device_scale_factor=STILL_SCALE)
    page.goto(f"{BASE}terrain_{patch.replace('.', '')}.html", wait_until="load")
    page.wait_for_timeout(2500)
    for sel in clicks:
        page.locator(sel).first.click()
        page.wait_for_timeout(200)
    page.evaluate(APPLY, pos)
    page.wait_for_timeout(1500)
    im = Image.open(io.BytesIO(page.locator(".tc-stage").screenshot())).convert("RGB")
    w, h = im.size
    im = im.crop((round(crop[0] * w), round(crop[1] * h), round(crop[2] * w), round(crop[3] * h)))
    im.thumbnail((900, 900), Image.LANCZOS)
    im.save(OUT_DIR / name, "WEBP", quality=86)
    page.close()
    print(name, im.size)


def main(only):
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for name in STILLS:
            if not only or name in only:
                still(b, name)
        page = b.new_page(viewport={"width": 1400, "height": 1000}, device_scale_factor=1.5)
        for key in SCENES:
            if only and key not in only:
                continue
            frames, durations = scene(page, key)
            out = OUT_DIR / f"2026-10-04_sweep_{key}.webp"
            frames[0].save(out, "WEBP", save_all=True, append_images=frames[1:], duration=durations, loop=0,
                           quality=72, method=6)
            print(out.name, len(frames), "frames", round(out.stat().st_size / 1024), "KB")
        b.close()


if __name__ == "__main__":
    main(sys.argv[1:])
