"""Where a patch's map changed most, by kind, outside the areas its other notes already picture (owner 2026-10-28:
7.38 "Touched up the map in general. Slightly adjusted neutral camps, trees, and cliffs" — "a picture under each
word: neutral camps, trees, cliffs, and the other changes apart", not one whole map).

    python scripts/gen/terrain_hotspots.py 7.38          # prints the spots of each kind, for data/terrain_spots.json

Kinds: camps / trees (the map diff's changed points) and cliffs — 32-unit samples whose height LEVEL changed
(data/map/heights_<code>.png, levels as heightmap.BANDS) on ground at or above the low ground, so a stream cut into
low ground (river level 0) is not a cliff. Changes are binned in BIN-unit squares; a bin with at least MIN_<kind>
changes is a hotspot; touching hotspots merge into one spot (their centre, r from their extent). A change inside any
other picture of the patch (an entry with r under the whole-map size) is left out: that picture shows it already.
"""
import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

BIN = 1024
MIN = {"camps": 1, "trees": 12, "cliffs": 40}
R_MIN, R_MAX = 700, 1500
WHOLE_MAP_R = 7000
FRAME_X0, FRAME_Y0, FRAME_W, FRAME_H, STEP = -10240, -10752, 640, 656, 32
LOW_GROUND, LEVELS = 64, (64, 192, 320, 448, 576, 704)


def _level(h):
    return sum(h >= t for t in LEVELS)


def _levels(code):
    """{(i, j): height level} of a map file's ground samples (no ground left out)."""
    from PIL import Image
    px = Image.open(os.path.join(_ROOT, "data", "map", f"heights_{code}.png")).load()
    return {(i, j): _level(px[i, j] - 1024) for j in range(FRAME_H) for i in range(FRAME_W) if px[i, j]}


def _edges(lv):
    """The samples on a cliff: a neighbour (right / down) on another level, neither of them river (a stream's bank
    is not a cliff — the stream notes picture those)."""
    out = set()
    for (i, j), v in lv.items():
        for n in ((i + 1, j), (i, j + 1)):
            w = lv.get(n)
            if w is not None and w != v and v > 0 and w > 0:
                out.add((i, j))
    return out


def _xy(i, j):
    return FRAME_X0 + i * STEP + STEP / 2, FRAME_Y0 + (FRAME_H - 1 - j) * STEP + STEP / 2


def cliff_changes(old_code, new_code):
    """(removed, added): [(x, y)] of the cliff samples only the old map has and only the new map has — one sample of
    slack (a cliff redrawn in place is not a change)."""
    a, b = _edges(_levels(old_code)), _edges(_levels(new_code))

    def near(p, s):
        return any((p[0] + di, p[1] + dj) in s for di in (-1, 0, 1) for dj in (-1, 0, 1))
    return ([_xy(*p) for p in a if not near(p, b)], [_xy(*p) for p in b if not near(p, a)])


def height_changes(old_code, new_code):
    """[(x, y)] of every changed cliff sample, removed and added (hotspots)."""
    removed, added = cliff_changes(old_code, new_code)
    return removed + added


def _covered(x, y, entries):
    for e in entries:
        r = e.get("r", 700)
        if r >= WHOLE_MAP_R:
            continue
        for s in e["spots"]:
            if abs(x - s[0]) <= r and abs(y - s[1]) <= r:
                return True
    return False


def hotspots(points, minimum):
    """[(cx, cy, r, n)] of the merged busy bins."""
    bins = {}
    for x, y in points:
        bins.setdefault((math.floor(x / BIN), math.floor(y / BIN)), []).append((x, y))
    busy = {k for k, v in bins.items() if len(v) >= minimum}
    out, seen = [], set()
    for k in sorted(busy):
        if k in seen:
            continue
        group, todo = [], [k]
        while todo:
            c = todo.pop()
            if c in seen or c not in busy:
                continue
            seen.add(c)
            group.append(c)
            todo += [(c[0] + dx, c[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
        pts = [p for c in group for p in bins[c]]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        r = max(R_MIN, min(R_MAX, max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 300))
        out.append((round(cx), round(cy), round(r), len(pts)))
    return sorted(out, key=lambda s: -s[3])


def main(patch):
    from patch import map_versions as mv
    from patch import terrain_index
    import builders.terrain as terrain
    step = {s.patch: s for s in mv.steps()}[patch]
    diff = terrain_index._load_diff(patch)
    groups = terrain._changed_points(diff)
    with open(os.path.join(_ROOT, "data", "terrain_spots.json"), encoding="utf-8") as f:
        entries = [e for e in json.load(f).get(patch, []) if not e.get("part")]

    def flat(g):
        return [tuple(p) for p in g.get("removed", []) + g.get("added", [])] + \
               [tuple(m[1]) for m in g.get("moved", [])]
    kinds = {"camps": flat(groups.get("camps", {})), "trees": flat(groups.get("trees", {})),
             "cliffs": height_changes(step.before.replace(".", ""), patch.replace(".", ""))}
    for kind, pts in kinds.items():
        left = [p for p in pts if not _covered(p[0], p[1], entries)]
        print(kind, len(pts), "changes,", len(left), "not pictured yet")
        for s in hotspots(left, MIN[kind]):
            print("  ", s)


if __name__ == "__main__":
    main(sys.argv[1])
