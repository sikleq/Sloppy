"""Micro-screenshots for the terrain notes of a patch: for each spot in data/terrain_spots.json, the same square of
the old and the new map side by side, the changes inside outlined like the Terrain page's chips — removed red on the
old map, added green on the new one, moved yellow on both, changed spawn boxes red / green.

Why (the owner 2026-10-03): the terrain rows were "all under one tag, mush"; "maybe micro-screenshots, tree
positions — we know now which tree went where". A row of a patch page / Terrain page whose text starts with a spot's
"match" shows its pictures (patch/elements.py terrain_shots_html, builders/terrain.py).

Reads the full renders (C:\\Users\\sikle\\tools\\maprender\\sfm\\final\\map_<sha8>_sfm_full.png, 2 units / px — set
SFM_FINAL to move them), so it runs on the owner's PC; the pictures it writes are committed:

    python scripts/gen/terrain_shots.py            # every patch in data/terrain_spots.json
    python scripts/gen/terrain_shots.py 7.41       # one
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)
from builders import map_versions as mv  # noqa: E402
import builders.terrain as terrain  # noqa: E402
from render_map import world_rect  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
FINAL = os.environ.get("SFM_FINAL", r"C:\Users\sikle\tools\maprender\sfm\final")
OUT = os.path.join(_ROOT, "icons", "terrain")
SPOTS = os.path.join(_ROOT, "data", "terrain_spots.json")
UPP = 2.0                 # game units per pixel of the full renders
HALF = 240                # px per side of one half (shown at 120 css px: crisp on hi-dpi)
GAP = 4
COLOUR = {"removed": (255, 77, 77), "added": (93, 255, 138), "moved": (255, 210, 63)}
SIZE = {"trees": 64, "camps": 170, "camptiers": 190}     # half size of an outline, game units (entities: 150)
CIRCLE = 150


def spot_list():
    with open(SPOTS, encoding="utf-8") as f:
        return {p: v for p, v in json.load(f).items() if not p.startswith("_")}


def shot_name(patch, i):
    """icons/terrain/<code>_<i>.webp — the i-th picture of a patch's spots, in file order."""
    return f"{mv.code(patch)}_{i}.webp"


def _sha8(ver, maps):
    return maps[ver]["sha1"][:8]


def _crop(full, rect, cx, cy, r):
    x0, _x1, _yb, yt = rect
    box = (round((cx - r - x0) / UPP), round((yt - (cy + r)) / UPP), round((cx + r - x0) / UPP), round((yt - (cy - r)) / UPP))
    return full.crop(box).resize((HALF, HALF), Image.LANCZOS)


def _outlines(img, cx, cy, r, groups, side):
    """Draw one side's outlines: old side = removed + moved (where it stood), new side = added + moved (where it
    stands); trees and camps as squares, the round entity markers as circles."""
    d = ImageDraw.Draw(img)
    k = HALF / (2 * r)

    def px(x, y):
        return (x - (cx - r)) * k, ((cy + r) - y) * k
    for key, g in groups.items():
        if key == "nowards":
            continue
        spots = {"moved": [m[0] if side == "old" else m[1] for m in g.get("moved", [])],
                 "removed": g.get("removed", []) if side == "old" else [],
                 "added": g.get("added", []) if side == "new" else []}
        for kind, pts in spots.items():
            for x, y in pts:
                if abs(x - cx) > r + 300 or abs(y - cy) > r + 300:
                    continue
                X, Y = px(x, y)
                if key in SIZE:
                    s = SIZE[key] * k
                    d.rectangle([X - s, Y - s, X + s, Y + s], outline=COLOUR[kind], width=2)
                else:
                    s = CIRCLE * k
                    d.ellipse([X - s, Y - s, X + s, Y + s], outline=COLOUR[kind], width=2)


def _boxes(img, cx, cy, r, diff, side):
    """Changed camp spawn boxes: the old box red on the old side, the new box green on the new side."""
    d = ImageDraw.Draw(img)
    k = HALF / (2 * r)
    old = {terrain._box_key(b) for b in diff.get("spawnboxesOld", [])}
    new = {terrain._box_key(b) for b in diff.get("spawnboxesNew", [])}
    boxes = diff.get("spawnboxesOld" if side == "old" else "spawnboxesNew", [])
    other = new if side == "old" else old
    for b in boxes:
        if terrain._box_key(b) in other:
            continue
        pts = [((p["x"] - (cx - r)) * k, ((cy + r) - p["y"]) * k) for p in b]
        if all(-HALF < x < 2 * HALF and -HALF < y < 2 * HALF for x, y in pts):
            d.line(pts + pts[:1], fill=COLOUR["removed" if side == "old" else "added"], width=2)


def _label(img, text, font):
    d = ImageDraw.Draw(img, "RGBA")
    w = d.textlength(text, font=font)
    d.rounded_rectangle([5, 5, 5 + w + 12, 25], radius=3, fill=(20, 16, 9, 205), outline=(227, 196, 106, 150))
    d.text((11, 7), text, font=font, fill=(244, 230, 191, 255))


def make(patch, entries, maps, steps):
    step = steps[patch]
    diff = terrain._load_diff(patch)
    groups = terrain._changed_points(diff)
    rect = world_rect()
    fulls = {v: Image.open(os.path.join(FINAL, f"map_{_sha8(v, maps)}_sfm_full.png")).convert("RGB")
             for v in (step.old_pic, step.new_pic)}
    font = ImageFont.truetype(os.path.join(_ROOT, "src", "fonts", "radiance-semibold.otf"), 14)
    os.makedirs(OUT, exist_ok=True)
    i = 0
    for e in entries:
        r = e.get("r", 700)
        for cx, cy in e["spots"]:
            halves = []
            for side, ver, label in (("old", step.old_pic, step.before), ("new", step.new_pic, patch)):
                img = _crop(fulls[ver], rect, cx, cy, r)
                _boxes(img, cx, cy, r, diff, side)
                _outlines(img, cx, cy, r, groups, side)
                _label(img, label, font)
                halves.append(img)
            sheet = Image.new("RGB", (2 * HALF + GAP, HALF), (8, 11, 6))
            sheet.paste(halves[0], (0, 0))
            sheet.paste(halves[1], (HALF + GAP, 0))
            sheet.save(os.path.join(OUT, shot_name(patch, i)), "WEBP", quality=82, method=6)
            i += 1
    print(patch, i, "pictures")


def main(only):
    with open(os.path.join(_ROOT, "data", "map", "patch_maps.json"), encoding="utf-8") as f:
        maps = json.load(f)["patches"]
    steps = {s.patch: s for s in mv.steps()}
    for patch, entries in spot_list().items():
        if not only or patch in only:
            make(patch, entries, maps, steps)


if __name__ == "__main__":
    main(sys.argv[1:])
