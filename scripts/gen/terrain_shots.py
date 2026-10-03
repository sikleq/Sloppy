"""Micro-screenshots for the terrain notes of a patch: for each spot in data/terrain_spots.json, the same square of
the old and the new map side by side, the changes inside outlined like the Terrain page's chips — removed red on the
old map, added green on the new one, moved yellow on both, changed spawn boxes red / green.

Why (the owner 2026-10-03): the terrain rows were "all under one tag, mush"; "maybe micro-screenshots, tree
positions — we know now which tree went where". A row of a patch page / Terrain page whose text starts with a spot's
"match" ends with a "Show" button that opens its pictures (patch/elements.py terrain_shots_html, builders/terrain.py).

Only the note's own objects are outlined (the owner 2026-10-03: "a camps note shows only the camps, not the trees and
everything else"): `show_keys` takes the first object word of the note (camp, tree, watcher, tower / tier N, lotus,
twin gates, tormentor, bounty rune, Roshan pit, wisdom shrine, outpost); a note with none (a cliff, a ramp, a stream)
gets no outlines. A spot's "show" list in terrain_spots.json overrides it (a ramp "behind the Tier 2" is not about
the tower). Each picture comes twice: <code>_<i>.webp (240-px halves, the row) and <code>_<i>_lg.webp (600-px
halves, opened by a click on the row's picture).

Reads the full renders (C:\\Users\\sikle\\tools\\maprender\\sfm\\final\\map_<sha8>_sfm_full.png, 2 units / px — set
SFM_FINAL to move them), so it runs on the owner's PC; the pictures it writes are committed:

    python scripts/gen/terrain_shots.py            # every patch in data/terrain_spots.json
    python scripts/gen/terrain_shots.py 7.41       # one
"""
import json
import math
import os
import re
import sys

try:                      # CI has no Pillow; show_keys / spot_keys are tested there without it
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)
from builders import map_versions as mv  # noqa: E402
import builders.terrain as terrain  # noqa: E402

if Image:
    Image.MAX_IMAGE_PIXELS = None
FINAL = os.environ.get("SFM_FINAL", r"C:\Users\sikle\tools\maprender\sfm\final")
OUT = os.path.join(_ROOT, "icons", "terrain")
SPOTS = os.path.join(_ROOT, "data", "terrain_spots.json")
UPP = 2.0                 # game units per pixel of the full renders
# (half px, file suffix, gap, line width, label font px): the row picture (shown at 240 css px a half) and the large
# one a click opens. The owner 2026-10-03: "the pictures should be bigger and the camera a bit further out" —
# every spot's square is ZOOM_OUT times wider than its r says, and a minimap shows where it is.
SIZES = ((360, "", 6, 3, 20), (720, "_lg", 10, 5, 32))
ZOOM_OUT = 1.4
MINIMAP = 0.32                # minimap side, share of a half
COLOUR = {"removed": (255, 77, 77), "added": (93, 255, 138), "moved": (255, 210, 63)}
MARK = (240, 240, 240)       # "here": an unchanged camp a note is about (evolutions, pull timers)
# camp tier icons for "tiers" (the owner 2026-10-03: "a demoted camp's pictures get the camp icons, before / after")
TIER_ICON = {t: os.path.join(_ROOT, "icons", "camps", f"creepcamp_{t}.png") for t in ("small", "mid", "big", "ancient")}
CELL = 64                    # gridnav cell, game units
SIZE = {"trees": 64, "camps": 170, "camptiers": 190}     # half size of an outline, game units (entities: 150)
CIRCLE = 150
CAMP_KEYS = ("camps", "camptiers", "boxes")              # "boxes" = changed spawn boxes

# the note's subject = its FIRST object word; ground words (cliff, ramp, stream…) name no object
_SUBJECTS = (
    (r"\bcamps?\b|\bspawn ?box", CAMP_KEYS),
    (r"\btrees?\b|\bjuke paths?\b", ("trees",)),
    (r"\bwatchers?\b", ("watchers",)),
    (r"\btowers?\b|\btier [1-4]\b", ("towers",)),
    (r"\blotus", ("lotus",)),
    (r"\btwin gates?\b", ("twinGates",)),
    (r"\btormentors?\b", ("tormentors",)),
    (r"\bbounty runes?\b", ("bounty",)),
    (r"\broshan pits?\b", ("roshan",)),
    (r"\bwisdom shrines?\b", ("wisdom",)),
    (r"\boutposts?\b", ("outposts",)),
    # the ground itself as the subject: no outlines, the two pictures show it ("The ramp … Roshan Pit", "The cliff
    # above the … camp", "the entrance to the bridge by the Lotus pools")
    (r"\b(?:cliffs?|ramps?|streams?|paths?|entrances?|areas?|rim|bridge|high ground|low ground)\b", ()),
)


def show_keys(text):
    """The map-object keys a note is about: those of its first object word ('Removed several trees from the …
    pull camp' -> trees only; 'The Large camp nearest to Tier 3 towers …' -> camps only); none for a ground note."""
    best = None
    for rx, keys in _SUBJECTS:
        m = re.search(rx, text, re.I)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), keys)
    return set(best[1]) if best else set()


def spot_keys(entry):
    return set(entry["show"]) if "show" in entry else show_keys(entry["match"])


def spot_list():
    with open(SPOTS, encoding="utf-8") as f:
        return {p: v for p, v in json.load(f).items() if not p.startswith("_")}


def shot_name(patch, i, suffix=""):
    """icons/terrain/<code>_<i><suffix>.webp — the i-th picture of a patch's spots, in file order."""
    return f"{mv.code(patch)}_{i}{suffix}.webp"


def _sha8(ver, maps):
    return maps[ver]["sha1"][:8]


def _crop(full, rect, cx, cy, r, half):
    x0, _x1, _yb, yt = rect
    box = (round((cx - r - x0) / UPP), round((yt - (cy + r)) / UPP), round((cx + r - x0) / UPP), round((yt - (cy - r)) / UPP))
    return full.crop(box).resize((half, half), Image.LANCZOS)


def _outlines(img, cx, cy, r, groups, side, keys, half, width):
    """Draw one side's outlines of the given keys: old side = removed + moved (where it stood), new side = added +
    moved (where it stands); trees and camps as squares, the round entity markers as circles."""
    d = ImageDraw.Draw(img)
    k = half / (2 * r)

    def px(x, y):
        return (x - (cx - r)) * k, ((cy + r) - y) * k
    for key, g in groups.items():
        if key not in keys:
            continue
        if key == "nowards":         # changed no-ward cells: turned wardable red on the old side, no-ward green on the new
            _cells(img, g.get("removed" if side == "old" else "added", []), px, k,
                   COLOUR["removed" if side == "old" else "added"], width)
            continue
        spots = {"moved": [m[0] if side == "old" else m[1] for m in g.get("moved", [])],
                 "removed": g.get("removed", []) if side == "old" else [],
                 "added": g.get("added", []) if side == "new" else []}
        for kind, pts in spots.items():
            for x, y in pts:
                if abs(x - cx) > r + 300 or abs(y - cy) > r + 300:
                    continue
                X, Y = px(x, y)
                s = (SIZE[key] if key in SIZE else CIRCLE) * k
                shape = d.rectangle if key in SIZE else d.ellipse
                shape([X - s, Y - s, X + s, Y + s], outline=COLOUR[kind], width=width)
        if side == "new":            # where the moved ones stood: a light dashed outline, on top (the owner 2026-10-03)
            ghost = ImageDraw.Draw(img, "RGBA")
            for x, y in (m[0] for m in g.get("moved", [])):
                if abs(x - cx) <= r + 300 and abs(y - cy) <= r + 300:
                    X, Y = px(x, y)
                    s = (SIZE[key] if key in SIZE else CIRCLE) * k
                    _dashed(ghost, key in SIZE, X, Y, s, COLOUR["moved"] + (200,), max(1, width - 1))


def _dashed(d, square, X, Y, s, colour, width):
    """A dashed square (or circle) of half size s round (X, Y)."""
    dash, gap = max(3.0, s / 3), max(2.0, s / 5)
    if not square:
        steps = max(8, int(2 * math.pi * s / (dash + gap)))
        for i in range(steps):
            a = 360 * i / steps
            d.arc([X - s, Y - s, X + s, Y + s], a, a + 360 * dash / (dash + gap) / steps, fill=colour, width=width)
        return
    _dashed_poly(d, [(X - s, Y - s), (X + s, Y - s), (X + s, Y + s), (X - s, Y + s)], colour, width, dash, gap)


def _cells(img, cells, px, k, colour, width):
    """Gridnav cells (south-west corners) as faintly filled, outlined squares."""
    d = ImageDraw.Draw(img, "RGBA")
    s = CELL * k
    for wx, wy in cells:
        x, y = px(wx, wy + CELL)
        if -s < x < img.width and -s < y < img.height:
            d.rectangle([x, y, x + s, y + s], fill=colour + (70,), outline=colour + (255,), width=max(1, width - 1))


_CAMPS = {}


def _camps(ver):
    """Camp spawner spots of one map picture (data/map/mapdata_<code>.json)."""
    if ver not in _CAMPS:
        with open(os.path.join(_ROOT, "data", "map", f"mapdata_{mv.code(ver)}.json"), encoding="utf-8") as f:
            _CAMPS[ver] = [(c["x"], c["y"]) for c in json.load(f)["data"]["npc_dota_neutral_spawner"]]
    return _CAMPS[ver]


def _marks(img, cx, cy, r, ver, points, half, width):
    """The camps a note is about, outlined white where each map picture has them (a camp may stand elsewhere on the
    old map): the nearest camp to each mark within 1500 units."""
    d = ImageDraw.Draw(img)
    k = half / (2 * r)
    ys = []
    for mx, my in points:
        camp = min(_camps(ver), key=lambda c: (c[0] - mx) ** 2 + (c[1] - my) ** 2)
        if (camp[0] - mx) ** 2 + (camp[1] - my) ** 2 > 1500 ** 2 or abs(camp[0] - cx) > r or abs(camp[1] - cy) > r:
            continue
        X, Y = (camp[0] - (cx - r)) * k, ((cy + r) - camp[1]) * k
        s = SIZE["camps"] * k
        d.rectangle([X - s - 1, Y - s - 1, X + s + 1, Y + s + 1], outline=(0, 0, 0), width=width + 2)
        d.rectangle([X - s, Y - s, X + s, Y + s], outline=MARK, width=width)
        ys.append(Y)
    return ys                                # where the marked camps sit: the tier plate keeps away from them


def _tiers(img, chain, half, camp_ys=()):
    """A camp tier chain at the top-right of a picture half — 'mid' or 'mid → big → ancient' — on a dark plate;
    at the bottom-right when a marked camp sits in the upper part of the picture."""
    if not chain:
        return
    s = 32 if half < 400 else 64          # the 32-px minimap icons at 1x / 2x, unblurred: their bars stay readable
    gap = s // 3
    arrow = s // 2
    w = len(chain) * s + (len(chain) - 1) * (arrow + 2 * gap) + 2 * gap
    m = max(4, half // 40)
    x0, y0 = half - w - m, m                 # top-right: the version label holds the top-left
    if any(y < half * 0.45 for y in camp_ys):
        y0 = half - s - 2 * gap - m
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([x0, y0, x0 + w, y0 + s + 2 * gap], radius=4, fill=(20, 16, 9, 215),
                        outline=(227, 196, 106, 150))
    x = x0 + gap
    for i, tier in enumerate(chain):
        icon = Image.open(TIER_ICON[tier]).convert("RGBA").resize((s, s), Image.NEAREST)
        img.paste(icon, (x, y0 + gap), icon)
        x += s
        if i < len(chain) - 1:
            cy = y0 + gap + s // 2
            d.line([x + gap, cy, x + gap + arrow, cy], fill=(227, 196, 106, 230), width=max(2, s // 12))
            d.polygon([(x + gap + arrow + 2, cy), (x + gap + arrow - s // 6, cy - s // 6),
                       (x + gap + arrow - s // 6, cy + s // 6)], fill=(227, 196, 106, 230))
            x += arrow + 2 * gap


def _boxes(img, cx, cy, r, diff, side, half, width):
    """Changed camp spawn boxes: the old box red on the old side, the new box green on the new side — and on the new
    side the old box again, red dashed and faint, so a box that moved a little shows its shift (the owner 2026-10-03:
    "a camp that moves moves its spawn boxes too — it doesn't show that they moved")."""
    d = ImageDraw.Draw(img, "RGBA")
    k = half / (2 * r)
    old = {terrain._box_key(b) for b in diff.get("spawnboxesOld", [])}
    new = {terrain._box_key(b) for b in diff.get("spawnboxesNew", [])}

    def corners(b):
        pts = [((p["x"] - (cx - r)) * k, ((cy + r) - p["y"]) * k) for p in b]
        return pts if all(-half < x < 2 * half and -half < y < 2 * half for x, y in pts) else None
    boxes = diff.get("spawnboxesOld" if side == "old" else "spawnboxesNew", [])
    other = new if side == "old" else old
    for b in boxes:
        pts = None if terrain._box_key(b) in other else corners(b)
        if pts:
            d.line(pts + pts[:1], fill=COLOUR["removed" if side == "old" else "added"], width=width)
    if side == "new":                # on top, so a box moved by a few pixels still shows its old edge
        for b in diff.get("spawnboxesOld", []):
            pts = None if terrain._box_key(b) in new else corners(b)
            if pts:
                _dashed_poly(d, pts, COLOUR["removed"] + (220,), max(1, width - 1), max(4.0, half / 45),
                             max(3.0, half / 70))


def _dashed_poly(d, pts, colour, width, dash, gap):
    """A closed polygon drawn dashed."""
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        length, t = math.hypot(bx - ax, by - ay), 0.0
        while length and t < length:
            e = min(t + dash, length)
            d.line([ax + (bx - ax) * t / length, ay + (by - ay) * t / length,
                    ax + (bx - ax) * e / length, ay + (by - ay) * e / length], fill=colour, width=width)
            t += dash + gap


_MINI = {}


def _minimap(img, full, rect, cx, cy, r, half):
    """The whole map, small, in the bottom-left corner of the old half, the pictured square framed on it (the owner
    2026-10-03: "when you show where something is, add a minimap with a mark, otherwise it's unclear")."""
    x0, x1, yb, yt = rect
    side = round(half * MINIMAP)
    key = (id(full), side)
    if key not in _MINI:
        _MINI[key] = full.resize((side, round(side * (yt - yb) / (x1 - x0))), Image.LANCZOS)
    mini = _MINI[key].copy()
    mw, mh = mini.size
    d = ImageDraw.Draw(mini)
    fx, fy = mw / (x1 - x0), mh / (yt - yb)
    left, right = (cx - r - x0) * fx, (cx + r - x0) * fx
    top, bottom = (yt - (cy + r)) * fy, (yt - (cy - r)) * fy
    grow = max(0, 7 - (right - left)) / 2              # a tiny square still shows as a frame
    left, right, top, bottom = left - grow, right + grow, top - grow, bottom + grow
    d.rectangle([left - 1, top - 1, right + 1, bottom + 1], outline=(0, 0, 0), width=2)
    d.rectangle([left, top, right, bottom], outline=(255, 210, 63), width=max(2, side // 60))
    m = max(4, half // 40)
    pos = (m, half - mh - m)
    plate = ImageDraw.Draw(img, "RGBA")
    plate.rectangle([pos[0] - 2, pos[1] - 2, pos[0] + mw + 1, pos[1] + mh + 1], fill=(20, 16, 9, 230),
                    outline=(227, 196, 106, 170))
    img.paste(mini, pos)


def _label(img, text, font):
    d = ImageDraw.Draw(img, "RGBA")
    w = d.textlength(text, font=font)
    h = font.size
    pad = max(5, h // 3)
    d.rounded_rectangle([pad, pad, pad + w + 2 * pad, pad + h + pad], radius=3, fill=(20, 16, 9, 205),
                        outline=(227, 196, 106, 150))
    d.text((2 * pad, pad + 2), text, font=font, fill=(244, 230, 191, 255))


def _sheet(fulls, rect, step, patch, diff, groups, cx, cy, r, entry, size):
    half, _suffix, gap, width, font_px = size
    keys = spot_keys(entry)
    font = ImageFont.truetype(os.path.join(_ROOT, "src", "fonts", "radiance-semibold.otf"), font_px)
    halves = []
    for side, ver, label in (("old", step.old_pic, step.before), ("new", step.new_pic, patch)):
        img = _crop(fulls[ver], rect, cx, cy, r, half)
        if "boxes" in keys:
            _boxes(img, cx, cy, r, diff, side, half, width)
        _outlines(img, cx, cy, r, groups, side, keys, half, width)
        ys = _marks(img, cx, cy, r, ver, entry.get("mark", []), half, width)
        _tiers(img, entry.get("tiers", {}).get(side), half, ys)
        if side == "old":
            _minimap(img, fulls[ver], rect, cx, cy, r, half)
        _label(img, label, font)
        halves.append(img)
    sheet = Image.new("RGB", (2 * half + gap, half), (8, 11, 6))
    sheet.paste(halves[0], (0, 0))
    sheet.paste(halves[1], (half + gap, 0))
    return sheet


def make(patch, entries, maps, steps):
    from render_map import world_rect
    step = steps[patch]
    diff = terrain._load_diff(patch)
    groups = terrain._changed_points(diff)
    rect = world_rect()
    fulls = {v: Image.open(os.path.join(FINAL, f"map_{_sha8(v, maps)}_sfm_full.png")).convert("RGB")
             for v in (step.old_pic, step.new_pic)}
    os.makedirs(OUT, exist_ok=True)
    i = 0
    for e in entries:
        r = round(e.get("r", 700) * ZOOM_OUT)
        for cx, cy in e["spots"]:
            for size in SIZES:
                sheet = _sheet(fulls, rect, step, patch, diff, groups, cx, cy, r, e, size)
                sheet.save(os.path.join(OUT, shot_name(patch, i, size[1])), "WEBP", quality=82 if not size[1] else 78,
                           method=6)
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
