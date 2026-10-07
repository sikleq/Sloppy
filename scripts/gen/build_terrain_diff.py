"""Compute per-patch terrain diffs -> data/terrain_diff_<newVer>.json.

Primary terrain-data sources:
  - Interactive map: https://tools.spectral.gg/interactive-map
  - Coords (GitHub):  leamare/dota-interactive-map
    (assets/data/<ver>/mapdata.json + root worlddata.json bounds)

For each old->new patch pair we read the two `mapdata.json` exports from
leamare/dota-interactive-map (cached under .cache/leamare/mapdata_<code>.json —
NOT committed; this is a regeneration helper, like scripts/fetch_*.py) and emit a
small, committed diff per NEW patch that the site build (builders/terrain.py)
projects onto that patch's terrain map:

  - treesOld / treesNew     : full tree coord sets (forest layout each side)
  - campsOld / campsNew      : neutral camps with tier (split old/new by slider)
  - entities                 : full old+new sets per point-entity layer
                               (towers / lotus / gates / tormentors / runes /
                               wisdom / outposts / watchers / roshan)
  - camps / towers / …       : move/relocate/demote records (kept for reference)

World coords are kept as-is; builders/terrain.py projects them with the shared crop
meta (data/terrain_map_meta.json), which lines up pixel-accurately with our
cropped map renders (verified by overlaying all trees on the map image). The crop
box is shared across every version, so the same projector places any patch's
markers correctly.

Since 2026-10-02 every map file 7.38-7.41f is our own (data/map/mapdata_<code>.json, one per distinct map file,
named by the first patch that shipped it), and the default pairs are the Terrain pages' steps
(builders/map_versions.py): every patch whose map file differs from the patch before's, old file -> new file::

    python scripts/gen/build_terrain_diff.py            # every step -> data/terrain_diff_<patch>.json
    python scripts/gen/build_terrain_diff.py 739:740    # or a single pair
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))  # scripts/gen -> scripts -> repo root
_CACHE = os.path.join(_ROOT, ".cache", "leamare")

sys.path.insert(0, _ROOT)
from builders import map_versions  # noqa: E402


def default_pairs():
    """(old_code, new_code, page) for every Terrain step. Codes have no dot; the diff is saved under the step's own
    patch (the page that reads it) — not the new file's first patch, which differs if a patch ever brings back an
    older map file."""
    return [(map_versions.code(s.old_pic), map_versions.code(s.new_pic), s.patch) for s in map_versions.steps()]


# Point-entity layers (full old+new sets → toggleable slider-split map layers).
# leamare keys (layerDefinitions.js): Outpost == npc_dota_watch_tower (2),
# Watcher == npc_dota_lantern (10) — SEPARATE layers.
_ENTITY_KEYS = {
    "towers": "npc_dota_tower",
    # before 7.38 the Lotus Pools were npc_dota_mango_tree (7.38's notes: "changed the way Healing Lotuses are
    # collected from Lotus Pools"); without the old name 7.37e -> 7.38 read "lotus pools +2"
    "lotus": ("npc_dota_lotus_pool", "npc_dota_mango_tree"),
    "wisdomRunes": "dota_item_rune_spawner_xp",   # until 7.38 replaced them with the Shrines (no map layer)
    "twinGates": "npc_dota_unit_twin_gate",
    "tormentors": "npc_dota_miniboss_spawner",
    "bounty": "dota_item_rune_spawner_bounty",
    "power": "dota_item_rune_spawner_powerup",
    "wisdom": "npc_dota_xp_fountain",       # Shrine of Wisdom
    "outposts": "npc_dota_watch_tower",
    "watchers": "npc_dota_lantern",
    "roshan": "npc_dota_roshan_spawner",
    # 2026-10-06 (owner: "все слои"), from extract_map_entities._layers
    "laneSpawns": "npc_dota_spawner",
    "heroSpawns": "info_player_start",
    "couriers": "info_courier_spawn",
    "stash": "ent_dota_neutral_item_stash",
}

# Zone layers: brush volumes as polygons (old / new sides like the spawn boxes)
_ZONE_KEYS = {"nowardZones": "trigger_no_wards", "shops": "trigger_shop", "roshanPit": "trigger_boss_attackable"}


def lane_paths(src):
    """[{"team", "lane", "points": [[x, y], …]}]: each lane creep wave's walk, from its spawner through the
    path corners (path_corner "next" chain) — absent on maps extracted before 2026-10-06."""
    corners = {p["name"]: p for p in src.get("path_corner", [])}
    out = []
    for s in src.get("npc_dota_spawner", []):
        pts, name, seen = [[s["x"], s["y"]]], s.get("first"), set()
        while name in corners and name not in seen:
            seen.add(name)
            c = corners[name]
            pts.append([c["x"], c["y"]])
            name = c.get("next")
        out.append({"team": s["team"], "lane": s["lane"], "points": pts})
    return out


def current_paths(src, steps=8):
    """[[x, y], …] per river current: its spline (cubic Bézier between nodes: node + out-tangent, next node +
    in-tangent) sampled `steps` points a segment."""
    out = []
    for cur in src.get("dota_movespeed_modifier_path", []):
        nodes, pts = cur.get("nodes", []), []
        for a, b in zip(nodes, nodes[1:]):
            p0, p3 = (a["x"], a["y"]), (b["x"], b["y"])
            p1 = (p0[0] + a["out"][0], p0[1] + a["out"][1])
            p2 = (p3[0] + b["in"][0], p3[1] + b["in"][1])
            for i in range(steps):
                t = i / steps
                u = 1 - t
                pts.append([round(u ** 3 * p0[k] + 3 * u * u * t * p1[k] + 3 * u * t * t * p2[k] + t ** 3 * p3[k])
                            for k in (0, 1)])
        if nodes:
            pts.append([nodes[-1]["x"], nodes[-1]["y"]])
        out.append(pts)
    return out


AREA_CELL = 16          # world units per cell of the field the buff zones are traced on
AREA_TOLERANCE = 10     # world units: the traced outline is simplified this much (the field is AREA_CELL / 2 exact)


def _spline_samples(cur, steps):
    """(x, y, radius) along a current's spline: the radius goes linearly from node to node."""
    nodes, rad = cur.get("nodes", []), cur.get("radius", [])
    out = []
    for i, (a, b) in enumerate(zip(nodes, nodes[1:])):
        p0, p3 = (a["x"], a["y"]), (b["x"], b["y"])
        p1 = (p0[0] + a["out"][0], p0[1] + a["out"][1])
        p2 = (p3[0] + b["in"][0], p3[1] + b["in"][1])
        ra, rb = (rad[i], rad[i + 1]) if i + 1 < len(rad) else (0, 0)
        for k in range(steps + (i == len(nodes) - 2)):
            t = k / steps
            u = 1 - t
            out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                        u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1],
                        ra + (rb - ra) * t))
    return out


def _simplify(ring, tol):
    """Douglas–Peucker on a closed ring of [x, y]."""
    def rdp(pts):
        if len(pts) < 3:
            return pts
        (ax, ay), (bx, by) = pts[0], pts[-1]
        dx, dy = bx - ax, by - ay
        norm = (dx * dx + dy * dy) ** 0.5 or 1.0
        far, idx = -1.0, 0
        for i in range(1, len(pts) - 1):
            d = abs(dy * (pts[i][0] - ax) - dx * (pts[i][1] - ay)) / norm
            if d > far:
                far, idx = d, i
        if far <= tol:
            return [pts[0], pts[-1]]
        return rdp(pts[:idx + 1])[:-1] + rdp(pts[idx:])
    half = len(ring) // 2
    return rdp(ring[:half + 1])[:-1] + rdp(ring[half:])[:-1]


OUTLINE_CELL = 8        # world units per cell of the field a zone's outline is traced on (straight edges stay exact)


def _convex_field(gx, gy, poly):
    """Signed distance-like field of a convex polygon on a grid: max over its edges of the distance outside that edge
    (<= 0 inside). Its zero line runs exactly along straight edges."""
    import numpy as np
    # counter-clockwise (the shoelace sum of (x2 - x1)(y2 + y1) is negative), so "outside" is right of every edge
    pts = poly if sum((b[0] - a[0]) * (b[1] + a[1]) for a, b in zip(poly, poly[1:] + poly[:1])) < 0 else poly[::-1]
    out = np.full(gx.shape, -np.inf)
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
        if length:
            np.maximum(out, ((by - ay) * (gx - ax) - (bx - ax) * (gy - ay)) / length, out=out)
    return out


def zone_outlines(polys):
    """The outline of a zone kind's polygons as ONE shape where its hulls touch or overlap (the owner 2026-10-07: the
    Dire fountain shop "будто с пропуском и в целом зона построена из 2 частей" — it is 2 entities of 2 hulls each,
    one a 32-unit strip inside the other): union of the convex hulls, traced at the zero of min(field) on an
    OUTLINE_CELL grid per cluster of overlapping polygons → rings [[[x, y], …], …]. Needs numpy + contourpy (the
    owner's PC; the site build only reads the result)."""
    import numpy as np
    from contourpy import contour_generator
    polys = [[tuple(p) for p in poly] for poly in polys if len(poly) >= 3]
    boxes = [(min(p[0] for p in q), min(p[1] for p in q), max(p[0] for p in q), max(p[1] for p in q)) for q in polys]
    group = list(range(len(polys)))

    def root(i):
        while group[i] != i:
            group[i] = group[group[i]]
            i = group[i]
        return i
    for i, a in enumerate(boxes):                      # clusters of polygons whose boxes touch
        for j in range(i):
            b = boxes[j]
            if a[0] <= b[2] + 1 and b[0] <= a[2] + 1 and a[1] <= b[3] + 1 and b[1] <= a[3] + 1:
                group[root(i)] = root(j)
    rings = []
    for g in sorted({root(i) for i in range(len(polys))}):
        members = [polys[i] for i in range(len(polys)) if root(i) == g]
        if len(members) == 1:                          # a lone hull is its own outline, corners exact
            rings.append([list(p) for p in members[0]])
            continue
        x0 = min(boxes[i][0] for i in range(len(polys)) if root(i) == g) - 3 * OUTLINE_CELL
        y0 = min(boxes[i][1] for i in range(len(polys)) if root(i) == g) - 3 * OUTLINE_CELL
        x1 = max(boxes[i][2] for i in range(len(polys)) if root(i) == g) + 3 * OUTLINE_CELL
        y1 = max(boxes[i][3] for i in range(len(polys)) if root(i) == g) + 3 * OUTLINE_CELL
        xs, ys = np.arange(x0, x1 + 1, OUTLINE_CELL, dtype=float), np.arange(y0, y1 + 1, OUTLINE_CELL, dtype=float)
        gx, gy = np.meshgrid(xs, ys)
        field = np.min([_convex_field(gx, gy, q) for q in members], axis=0)
        for line in contour_generator(xs, ys, field).lines(0.0):
            ring = [[int(round(x)), int(round(y))] for x, y in line]
            if ring and ring[0] == ring[-1]:
                ring = ring[:-1]
            if len(ring) > 2:
                rings.append(_simplify(ring, 2))
    return rings


STRONG, MODERATE = 150, 100     # max bonus movement speed of a strong / moderate current (7.38)
ALL_STRONG_FROM = 41            # 7.41: "All sections of currents now give a max movement speed bonus of 150"


def current_max_bonus(cur, code):
    """A current's max bonus movement speed. The map files mark each node strong (2) or moderate (1) — every current of
    7.38-7.41f is one strength end to end (tests/test_map_layers.py) — and still do since 7.41, where the notes made
    them all 150."""
    if code.startswith("7") and int(code[1:3]) >= ALL_STRONG_FROM:          # "741f" -> 41; 6.83 maps had none
        return STRONG
    return STRONG if 2 in (cur.get("types") or []) else MODERATE


def current_areas(src, code, steps=24):
    """Where each river current acts (the owner 2026-10-06: "точно покажи места, где юнит получает скорость от
    течения"): the union of the circles of its spline's radius (each node's radius, linear between nodes), traced as
    outline rings [[[x, y], …], …] (an island in the stream is a ring of its own; draw them even-odd) — with its max
    bonus speed: [{"max": 150, "rings": …}, …]. Needs numpy + contourpy (the owner's PC; the site build only reads
    the result)."""
    import numpy as np
    from contourpy import contour_generator
    out = []
    for cur in src.get("dota_movespeed_modifier_path", []):
        s = np.array(_spline_samples(cur, steps), dtype=float)
        if not len(s) or not s[:, 2].any():
            out.append({"max": current_max_bonus(cur, code), "rings": []})
            continue
        pad = s[:, 2].max() + 2 * AREA_CELL
        xs = np.arange(s[:, 0].min() - pad, s[:, 0].max() + pad, AREA_CELL)
        ys = np.arange(s[:, 1].min() - pad, s[:, 1].max() + pad, AREA_CELL)
        gx, gy = np.meshgrid(xs, ys)
        field = np.full(gx.shape, -1e9)
        for x, y, r in s:                       # inside where some circle reaches: max(r - distance) > 0
            np.maximum(field, r - np.hypot(gx - x, gy - y), out=field)
        rings = []
        for line in contour_generator(xs, ys, field).lines(0.0):
            ring = [[int(round(x)), int(round(y))] for x, y in line]
            if len(ring) > 3:
                rings.append(_simplify(ring[:-1] if ring[0] == ring[-1] else ring, AREA_TOLERANCE))
        out.append({"max": current_max_bonus(cur, code), "rings": rings})
    return out


def _dotted(code):
    """'740' -> '7.40' (insert the dot after the major '7')."""
    return code if "." in code else f"{code[0]}.{code[1:]}"


_OWN = os.path.join(_ROOT, "data", "map")


def _load(code):
    """Our own map data first (data/map/mapdata_<code>.json, read from the game files by
    scripts/gen/extract_map_entities.py — same shape), else leamare's cached export."""
    own = os.path.join(_OWN, f"mapdata_{code}.json")
    path = own if os.path.exists(own) else os.path.join(_CACHE, f"mapdata_{code}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)["data"]


def _wards(old_code, new_code):
    """{"old", "new", "lost", "gained", "cells"} from data/map/gridnav_<code>.gnv.gz, or None without them."""
    import gridnav
    paths = [os.path.join(_OWN, f"gridnav_{c}.gnv.gz") for c in (old_code, new_code)]
    if not all(os.path.exists(p) for p in paths):
        return None
    (_ha, a), (hb, b) = gridnav.load(paths[0]), gridnav.load(paths[1])
    lost, gained = gridnav.ward_changes(a, b)
    to_no_ward, to_wardable = gridnav.changed_cells(hb, a, b)
    return {"old": _dotted(old_code), "new": _dotted(new_code), "lost": lost, "gained": gained,
            "cells": gridnav.no_ward_cells(b), "toNoWard": to_no_ward, "toWardable": to_wardable}


def _nearest(target, candidates):
    return min(candidates, key=lambda c: (c["x"] - target["x"]) ** 2
               + (c["y"] - target["y"]) ** 2)


_AREAS = {}


def _areas_of(src, code):
    """current_areas once per map file (each is the new side of one step and the old side of the next)."""
    if code not in _AREAS:
        _AREAS[code] = current_areas(src, code)
    return _AREAS[code]


def _diff_pair(old_code, new_code):
    A = _load(old_code)
    B = _load(new_code)

    # ---- trees: exact coordinate set difference (move records, not drawn) ----
    ta = {(t["x"], t["y"]) for t in A["ent_dota_tree"]}
    tb = {(t["x"], t["y"]) for t in B["ent_dota_tree"]}
    added_trees = sorted(tb - ta)
    removed_trees = sorted(ta - tb)

    # ---- neutral camps: match by triggerName ----
    ca = {e["triggerName"]: e for e in A["npc_dota_neutral_spawner"]}
    cb = {e["triggerName"]: e for e in B["npc_dota_neutral_spawner"]}
    camps = []
    rem = [ca[n] for n in ca if n not in cb]
    add = [cb[n] for n in cb if n not in ca]
    used_add = set()
    for a in rem:
        pool = [c for i, c in enumerate(add) if i not in used_add]
        if pool:
            b = _nearest(a, pool)
            used_add.add(add.index(b))
            camps.append({"kind": "relocated", "label": "Neutral camp relocated",
                          "x": b["x"], "y": b["y"], "ox": a["x"], "oy": a["y"]})
    for n in ca:
        if n not in cb:
            continue
        a, b = ca[n], cb[n]
        if (a["x"], a["y"]) != (b["x"], b["y"]):
            camps.append({"kind": "moved", "label": "Neutral camp moved",
                          "x": b["x"], "y": b["y"], "ox": a["x"], "oy": a["y"]})
        if a.get("neutralType") != b.get("neutralType"):
            camps.append({"kind": "demoted", "label": "Camp tier changed",
                          "x": b["x"], "y": b["y"]})

    # ---- towers: pair each NEW tower with the nearest OLD of same subType ----
    towers = []
    for e in B["npc_dota_tower"]:
        same = [t for t in A["npc_dota_tower"] if t["subType"] == e["subType"]]
        if not same:
            continue
        o = _nearest(e, same)
        if (o["x"], o["y"]) != (e["x"], e["y"]):
            towers.append({"kind": "moved", "label": "Tower repositioned",
                           "x": e["x"], "y": e["y"], "ox": o["x"], "oy": o["y"]})

    def moves(cat, label):
        out = []
        for b in B.get(cat, []):
            if not A.get(cat):
                continue
            o = _nearest(b, A[cat])
            if (o["x"], o["y"]) != (b["x"], b["y"]):
                out.append({"kind": "moved", "label": label,
                            "x": b["x"], "y": b["y"], "ox": o["x"], "oy": o["y"]})
        return out

    # ---- FULL tree sets each side (the "Trees" overlay shows the old layout on
    # the old side, new on the new side; sweep reveals the rearrangement). ----
    trees_old = sorted((t["x"], t["y"]) for t in A["ent_dota_tree"])
    trees_new = sorted((t["x"], t["y"]) for t in B["ent_dota_tree"])

    # ---- camps with tier (0=small 1=medium 2=large 3=ancient) both sides ----
    def camp_list(src):
        return [{"x": e["x"], "y": e["y"], "tier": int(e.get("neutralType", 0))}
                for e in src]
    camps_old = camp_list(A["npc_dota_neutral_spawner"])
    camps_new = camp_list(B["npc_dota_neutral_spawner"])

    def coords(src, key):
        """The first of the class names (one, or old and new names) the map has."""
        for k in (key,) if isinstance(key, str) else key:
            if src.get(k):
                return [[e["x"], e["y"]] for e in src[k]]
        return []
    entities = {name: {"old": coords(A, key), "new": coords(B, key)}
                for name, key in _ENTITY_KEYS.items()}

    # ---- spawnboxes: 4-point polygons from trigger_multiple ----
    spawnboxes_old = [[{"x": p["x"], "y": p["y"]} for p in box["points"]]
                      for box in A.get("trigger_multiple", [])]
    spawnboxes_new = [[{"x": p["x"], "y": p["y"]} for p in box["points"]]
                      for box in B.get("trigger_multiple", [])]

    return {
        "oldVer": _dotted(old_code), "newVer": _dotted(new_code),
        # where a ward can't stand (the map's gridnav, scripts/gen/gridnav.py): the layer's pictures
        # (icons/maps/nowards_<ver>.png) and how many cells turned no-ward / wardable
        "wards": _wards(old_code, new_code),
        "world": {"minX": -10464, "maxX": 10400, "minY": -10464, "maxY": 10400},
        "treesOld": [[x, y] for x, y in trees_old],
        "treesNew": [[x, y] for x, y in trees_new],
        "campsOld": camps_old,
        "campsNew": camps_new,
        "spawnboxesOld": spawnboxes_old,
        "spawnboxesNew": spawnboxes_new,
        # toggleable point-entity layers (full old+new sets, split by slider)
        "entities": entities,
        # line and zone layers (2026-10-06): lane creep paths, river currents, no-ward / shop / Roshan pit zones
        "lanes": {"old": lane_paths(A), "new": lane_paths(B)},
        "currents": {"old": current_paths(A), "new": current_paths(B)},
        "currentAreas": {"old": _areas_of(A, old_code), "new": _areas_of(B, new_code)},
        # one polygon per hull; old/newVolume = the entity each belongs to (a fountain's shop is 3 hulls)
        "zones": {name: {"old": [[[p["x"], p["y"]] for p in z["points"]] for z in A.get(key, [])],
                         "new": [[[p["x"], p["y"]] for p in z["points"]] for z in B.get(key, [])],
                         "oldVolume": [z.get("volume", i) for i, z in enumerate(A.get(key, []))],
                         "newVolume": [z.get("volume", i) for i, z in enumerate(B.get(key, []))],
                         # the drawn outline: touching / overlapping hulls as one shape, no inner lines
                         "oldOutline": zone_outlines([[[p["x"], p["y"]] for p in z["points"]] for z in A.get(key, [])]),
                         "newOutline": zone_outlines([[[p["x"], p["y"]] for p in z["points"]] for z in B.get(key, [])]),
                         **({"oldType": [z.get("shopType", "") for z in A.get(key, [])],
                             "newType": [z.get("shopType", "") for z in B.get(key, [])]} if key == "trigger_shop" else {})}
                  for name, key in _ZONE_KEYS.items()},
        # move data kept for reference (not drawn)
        "camps": camps,
        "towers": towers,
        "tormentors": moves("npc_dota_miniboss_spawner", "Tormentor relocated"),
        "twinGates": moves("npc_dota_unit_twin_gate", "Twin Gate moved"),
        "lotus": moves("npc_dota_lotus_pool", "Lotus Pool moved"),
    }


def main(pairs):
    from collections import Counter
    for pair in pairs:
        old_code, new_code = pair[:2]
        diff = _diff_pair(old_code, new_code)
        page = pair[2] if len(pair) > 2 else diff["newVer"]
        out = os.path.join(_ROOT, "data", f"terrain_diff_{page}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(diff, f, separators=(",", ":"))
        tiers = Counter(c["tier"] for c in diff["campsNew"])
        ent_summary = ", ".join(f"{k} {len(v['new'])}"
                                for k, v in diff["entities"].items())
        print(f"  -> {os.path.relpath(out, _ROOT)}: "
              f"{diff['oldVer']}->{diff['newVer']}  "
              f"trees {len(diff['treesOld'])}->{len(diff['treesNew'])} "
              f"({len(diff['treesNew']) - len(diff['treesOld']):+d}), "
              f"camps {len(diff['campsOld'])}/{len(diff['campsNew'])} "
              f"tiers={dict(tiers)}, {len(diff['towers'])} towers\n"
              f"     entities: {ent_summary}")


def _parse_args(argv):
    pairs = []
    for a in argv:
        if ":" in a:
            o, n = a.split(":", 1)
            pairs.append((o.replace(".", ""), n.replace(".", "")))
    return pairs or default_pairs()


if __name__ == "__main__":
    main(_parse_args(sys.argv[1:]))
