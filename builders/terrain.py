"""Build terrain_<code>.html — one terrain comparison page per patch (Materials tab).

A before/after **swipe slider** over the map file a patch shipped against the
one the patch before it ran, plus that patch's own "Terrain Changes" list and
what moved in the map file. Every patch whose map file changed is a page
(patch/map_versions.py: 7.38b … 7.41f), letter patches included; the header
picker and the subpatch arrows step through them. Each page has the FULL marker
toolbar (Trees / Camps / point-entities) from its committed
``data/terrain/terrain_diff_<patch>.json``.

Maps live in ``icons/maps/`` as ``map_<ver>.webp``, one per distinct map file,
named by the first patch that shipped it — our own Source Filmmaker renders
(scripts/gen/stitch_sfm.py, docs/terrain.md) on ONE shared world box so every
pair is pixel-aligned and the swipe handle lines up exactly. The same shared
crop meta (``data/terrain_map_meta.json``) projects every patch's markers.

The slider itself is driven by ``scripts.js`` (terrainCompareInit): the NEW
image is clipped with ``clip-path: inset(...)`` to ``--pos`` and a draggable
gold handle sets ``--pos`` (pointer + keyboard + click-to-position).

**Terrain change list — source of truth:** every patch's "Terrain Changes"
section in ``content/p*.py`` (``plain_header("Terrain Changes", terrain_link=…)``),
parsed at build time; a patch whose notes list none says so.

``python build_site.py`` runs it (``save_terrain_html``).
"""
import difflib as _difflib
import functools as _functools
import glob as _glob
import json as _json
import math as _math
import os as _os
import re as _re
import sys as _sys

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _HERE)

import patch.site_common as _site
import patch.map_versions as _map_versions
# which patches get a page and what moved on the map: data, in patch/terrain_index.py (the header needs it too)
from patch.terrain_index import (_MOVED_NAMES, _SAME_CAMP, _box_key, _box_key_xy, _current_shapes,
                                 _moved_items, _retiered_pairs, _terrain_filename, page_patches)
ASSET_VERSION = _site.compute_asset_version()


def _newest_map_img():
    """The newest map picture we hold (icons/maps/map_<ver>.webp) — the fallback's blurred backdrop, so a new
    patch never needs a version written here."""
    maps_dir = _os.path.join(_os.path.dirname(_site.DIST_DIR), "icons", "maps")
    vers = [m.group(1) for f in _os.listdir(maps_dir)
            if (m := _re.fullmatch(r"map_(\d+\.\d+[a-z]*)\.webp", f))]
    return f"icons/maps/map_{max(vers, key=_map_versions.ver_key)}.webp"

# Map markers are toggleable layers (off by default; the toolbar buttons reveal
# them): Trees + Camps + the 10 point-entity layers, each split old/new by the
# slider. Move records (Lotus/Tormentor/Twin Gate moves) stay in the diff for
# reference but aren't drawn — you SEE those by sweeping the slider under the lens.
SHOW_MARKERS = True

# SVG marker overlay is drawn in this square viewBox; world coords project into
# it via the shared crop meta (data/terrain_map_meta.json). 1280 == the cropped
# map's native pixel size, so trees land exactly on the forest.
MAP_VB = 1280


_esc = _site.esc


def _load_map_meta():
    """Projection meta written by scripts/gen/build_terrain_maps.py — the map's world
    boundaries + the crop box used for our map images. Without it the
    markers can't be placed accurately."""
    path = _os.path.join(_HERE, "data", "terrain_map_meta.json")
    try:
        with open(path, encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return None


def _projector(meta):
    """world (x,y) -> (px,py) in the MAP_VB viewBox, using the exact
    projection of the stitched map pictures: world -> full-map pixel
    (MAP_W) -> stitched-canvas px (/canvasScale) -> minus the crop origin ->
    normalised over the crop size -> viewBox. This is what makes the markers
    sit exactly on the rendered map."""
    xb = meta["xBounds"]
    yb = meta["yBounds"]
    mw, mh = meta["mapW"], meta["mapH"]
    sc = meta["canvasScale"]
    cr = meta["crop"]

    def proj(x, y):
        # world -> full-map pixel. Our stitched tile canvas is y-DOWN (tile row 0
        # at the top), so y uses reverseLerp directly — NOT worldToLatLon's
        # `map_h - …` form (that yields OpenLayers y-up and flips the map, which
        # put Dire at the bottom). x is unflipped.
        mpx = (x - xb[0]) / (xb[1] - xb[0]) * mw
        mpy = (y - yb[0]) / (yb[1] - yb[0]) * mh
        # -> stitched-canvas px -> crop-relative -> viewBox
        cx = mpx / sc - cr["x"]
        cy = mpy / sc - cr["y"]
        return round(cx / cr["w"] * MAP_VB, 1), round(cy / cr["h"] * MAP_VB, 1)
    return proj


_CAMP_ICON = {0: "creepcamp_small", 1: "creepcamp_mid",
              2: "creepcamp_big", 3: "creepcamp_ancient"}
_TREE_SIDE = 6.4    # tree square side, viewBox units
_CAMP_SIDE = 30     # camp icon size, viewBox units
_ENT_ICON = 26      # entity marker icon size, viewBox units
_ENT_DISC = 17      # marker disc radius, viewBox units
_MARKER_GOLD = "#e3c46a"

# Toggleable point-entity layers, in toolbar order. Each: (key in
# terrain_diff_<ver>.json["entities"], full label/tooltip, icon slug, type colour). The
# icon (icons/ui/gothic/tc_<key>.png, baked in the type colour by
# scripts/gen/gen_terrain_layer_icons.py) is the toolbar button; on the MAP it sits
# in a light-gold ring over a faint disc of the same colour. Colour must match
# the generator's COLORS. Watchers == the capturable lookout structures (the old
# "Outpost"); Roshan == the two pits.
_ENTITY_LAYERS = [
    ("towers",     "Towers",         "tc_towers",      "#4a90e2"),
    ("lotus",      "Lotus Pools",    "tc_lotus",       "#ff7ab5"),
    ("twinGates",  "Twin Gates",     "tc_twingates",   "#7ec8ff"),
    ("tormentors", "Tormentors",     "tc_tormentors",  "#ff6a4a"),
    ("bounty",     "Bounty Runes",   "tc_bounty",      "#f4c63a"),
    ("power",      "Power Up Runes", "tc_power",       "#5fd06a"),
    ("wisdom",     "Wisdom Shrines", "tc_wisdom",      "#9b7fc7"),
    ("outposts",   "Outposts",       "tc_outposts",    "#ff9a3c"),
    ("watchers",   "Watchers",       "tc_watchers",    "#56d6d0"),
    ("roshan",     "Roshan",         "tc_roshan",      "#d24a5a"),
]


def _markers_svg(diff, pair_id="default"):
    """Build the SVG overlays. Returns (svg_html, counts). Three layers, all the
    SAME colour for trees:
      • .tc-trees-old — the 7.40 tree layout, clipped to the OLD side of the
        slider; .tc-trees-new — the 7.41 layout, clipped to the NEW side. So
        sweeping the handle reveals how the forest moved (no add/remove colours).
      • .tc-camps-svg — every 7.41 camp as its tier icon; changed ones ringed.
    Hidden until the top-bar buttons flip .show-trees / .show-camps."""
    meta = _load_map_meta()
    if not diff or not meta:
        return "", {}
    proj = _projector(meta)

    def squares(coords):
        out = []
        for x, y in coords:
            px, py = proj(x, y)
            out.append(f'<rect x="{round(px - _TREE_SIDE / 2, 1)}" '
                       f'y="{round(py - _TREE_SIDE / 2, 1)}" '
                       f'width="{_TREE_SIDE}" height="{_TREE_SIDE}"/>')
        return "".join(out)

    def tree_layer(cls, coords):
        return (f'<svg class="tc-markers tm-layer tm-layer-trees {cls}" '
                f'viewBox="0 0 {MAP_VB} {MAP_VB}" preserveAspectRatio="none" '
                f'aria-hidden="true">'
                f'<g class="tm-trees-g">{squares(coords)}</g></svg>')

    trees_old = tree_layer("tc-trees-old", diff.get("treesOld", []))
    trees_new = tree_layer("tc-trees-new", diff.get("treesNew", []))

    cz = _CAMP_SIDE

    def tier_counts(camps):
        t = {0: 0, 1: 0, 2: 0, 3: 0}
        for c in camps:
            t[c.get("tier", 1)] = t.get(c.get("tier", 1), 0) + 1
        return t

    def camp_layer(cls, camps):
        cells = []
        for c in camps:
            px, py = proj(c["x"], c["y"])
            icon = _CAMP_ICON.get(c.get("tier", 1), "creepcamp_mid")
            cells.append(
                f'<image href="icons/camps/{icon}.png" '
                f'x="{round(px - cz / 2, 1)}" y="{round(py - cz / 2, 1)}" '
                f'width="{cz}" height="{cz}"/>')
        return (f'<svg class="tc-markers tm-layer tm-layer-camps {cls}" '
                f'viewBox="0 0 {MAP_VB} {MAP_VB}" preserveAspectRatio="none" '
                f'aria-hidden="true">'
                f'{"".join(cells)}</svg>')

    # Two layouts split by the slider (old camps on the old side, new on the
    # new side) so you see what a camp became + where it moved. No "changed"
    # ring — the side-by-side tier icon tells the story.
    camps_old = camp_layer("tc-camps-old", diff.get("campsOld", []))
    camps_new = camp_layer("tc-camps-new", diff.get("campsNew", []))

    # ---- point-entity layers (towers / lotus / gates / … ) — each marker is the
    # type's pixel icon sitting in a light-gold ring over a faint disc of the
    # type colour. Full old+new sets, split by the slider. ----
    def marker_g(coords, icon, color):
        z, r = _ENT_ICON, _ENT_DISC
        cells = []
        for x, y in coords:
            px, py = proj(x, y)
            cells.append(
                # clean dark backing (so the busy map doesn't show through and
                # read as "muddy"), a faint colour tint over it for identity, then
                # the gold ring + the light icon on top.
                f'<circle cx="{px}" cy="{py}" r="{r}" fill="#0d100b" '
                f'fill-opacity="0.66"/>'
                f'<circle cx="{px}" cy="{py}" r="{r}" fill="{color}" '
                f'fill-opacity="0.34" stroke="{_MARKER_GOLD}" stroke-width="2"/>'
                f'<image href="icons/ui/gothic/{icon}.png" '
                f'x="{round(px - z / 2, 1)}" y="{round(py - z / 2, 1)}" '
                f'width="{z}" height="{z}"/>')
        return f'<g class="tm-ent-g">{"".join(cells)}</g>'

    def ent_layer(key, side, coords, icon, color):
        return (f'<svg class="tc-markers tm-layer tm-layer-{key} tm-{side}" '
                f'viewBox="0 0 {MAP_VB} {MAP_VB}" preserveAspectRatio="none" '
                f'aria-hidden="true">{marker_g(coords, icon, color)}</svg>')

    entities = diff.get("entities", {})
    ent_svgs = []
    for key, _label, icon, color in _ENTITY_LAYERS:
        ed = entities.get(key)
        if not ed:
            continue
        ent_svgs.append(ent_layer(key, "old", ed.get("old", []), icon, color))
        ent_svgs.append(ent_layer(key, "new", ed.get("new", []), icon, color))

    # ---- spawnboxes — 4-point world-coord polygons ----
    # Both old and new boxes shown simultaneously (no slider clip).
    # Old = red dashed, New = teal solid. This matches how spectral.gg
    # renders them and avoids all clipping artifacts on rectangle strokes.
    def _box_poly(points, cls):
        pts_str = " ".join(
            f"{proj(p['x'], p['y'])[0]:.1f},{proj(p['x'], p['y'])[1]:.1f}"
            for p in points)
        return f'<polygon class="tc-spawnbox {cls}" points="{pts_str}"/>'

    # A box that didn't change is drawn once (plain teal). A changed one stands
    # out (the owner 2026-10-02: 7.39d's bigger Triangle Ancient boxes didn't
    # show — the old dashed box hid inside the new one, a few px apart): the new
    # box thick with a stronger fill, the old one thick dashed red on top.
    old_boxes = diff.get("spawnboxesOld", [])
    new_boxes = diff.get("spawnboxesNew", [])
    old_keys = {_box_key(b) for b in old_boxes}
    new_keys = {_box_key(b) for b in new_boxes}
    boxes_same = "".join(_box_poly(b, "tc-sb-new tc-sb-same")
                         for b in new_boxes if _box_key(b) in old_keys)
    boxes_new = "".join(_box_poly(b, "tc-sb-new tc-sb-changed")
                        for b in new_boxes if _box_key(b) not in old_keys)
    boxes_old = "".join(_box_poly(b, "tc-sb-old tc-sb-changed")
                        for b in old_boxes if _box_key(b) not in new_keys)

    sb_svg = (
        f'<svg class="tc-markers tm-layer tm-layer-spawnboxes" '
        f'viewBox="0 0 {MAP_VB} {MAP_VB}" preserveAspectRatio="none" '
        f'aria-hidden="true">{boxes_same}{boxes_new}{boxes_old}</svg>'
    )

    # ---- no-ward ground: the gridnav picture of each side (scripts/gen/gridnav.py
    # overlay — one pixel per 64-unit cell over x -10240..10240, y -10752..10240),
    # old/new split by the slider like the other layers ----
    wards = diff.get("wards") or {}
    ward_svgs = ""
    if wards.get("old") and wards.get("new"):
        gx0, gy0 = proj(-10240, 10240)                 # north-west corner of the grid
        gx1, gy1 = proj(10240, -10752)                 # south-east
        for side in ("old", "new"):
            ward_svgs += (
                f'<svg class="tc-markers tm-layer tm-layer-nowards tm-{side}" viewBox="0 0 {MAP_VB} {MAP_VB}" '
                f'preserveAspectRatio="none" aria-hidden="true"><image href="icons/maps/nowards_{wards[side]}.png" '
                f'x="{gx0}" y="{gy0}" width="{round(gx1 - gx0, 1)}" height="{round(gy1 - gy0, 1)}" '
                f'preserveAspectRatio="none"/></svg>')

    # ---- heights: the map's own height grid (maps/dota.vhcg, scripts/gen/heightmap.py — the owner 2026-10-05:
    # "decode dota.vhcg and make a height layer", for a ward tool later), same frame as the no-ward picture, one value
    # per 32 units, under every other layer ----
    # one picture per height (the owner 2026-10-05: "click 0, 128 … to turn those layers on and off"):
    # .hband-off-<k> on .terrain-compare hides band k (scripts.js initHeightBands)
    height_svgs = ""
    hb = _heights_bands(diff)
    if hb:
        gx0, gy0 = proj(-10240, 10240)
        gx1, gy1 = proj(10240, -10752)
        for side in ("old", "new"):
            ver, bands = hb[side]
            images = "".join(
                f'<image class="tm-hband tm-hband-{k}" href="icons/maps/heights_{ver}_{k}.png" x="{gx0}" y="{gy0}" '
                f'width="{round(gx1 - gx0, 1)}" height="{round(gy1 - gy0, 1)}" preserveAspectRatio="none"/>'
                for k in bands)
            height_svgs += (f'<svg class="tc-markers tm-layer tm-layer-heights tm-{side}" viewBox="0 0 {MAP_VB} '
                            f'{MAP_VB}" preserveAspectRatio="none" aria-hidden="true">{images}</svg>')

    extra_svgs = _line_zone_svgs(diff, proj)

    old_t = tier_counts(diff.get("campsOld", []))
    new_t = tier_counts(diff.get("campsNew", []))
    counts = {
        "treesOld": len(diff.get("treesOld", [])),
        "treesNew": len(diff.get("treesNew", [])),
        "campsOld": old_t, "campsNew": new_t,
        # every other kind of object, (old, new) — the "On the map" tiles under trees and camps
        "entities": {key: (len(ed.get("old", [])), len(ed.get("new", []))) for key, ed in entities.items() if ed},
    }
    return (height_svgs + ward_svgs + trees_old + trees_new + camps_old + camps_new
            + "".join(ent_svgs) + sb_svg + extra_svgs + _highlights_svg(diff, proj), counts)


# Line and zone layers (2026-10-06, the owner: "все слои"), from the map file's own entities
# (scripts/gen/extract_map_entities._layers → build_terrain_diff: "lanes", "currents", "zones", entities).
# Vision entities are not drawn on this site.
_LANE_COLOUR = {"good": "#7ed060", "bad": "#ff6a54"}
_CURRENT_COLOUR = "#54aaec"
_SHOP_COLOUR = "#e3c46a"
_SHOP_NAME = {"0": "Home shop", "1": "Side shop", "2": "Secret shop"}


_CURRENT_ARROW_EVERY = 1100     # world units between the flow arrows along a current
_CURRENT_ARROW = 5.5            # half-size of a flow arrow, viewBox units


def _ring_path(rings, proj):
    """Closed rings as one SVG path (fill-rule even-odd: an island in the stream stays dry)."""
    out = []
    for ring in rings:
        if len(ring) > 2:
            p = [proj(x, y) for x, y in ring]
            out.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in p) + "Z")
    return "".join(out)


def _flow_arrows(line, proj):
    """Chevrons along a current's centre line, pointing downstream (the nodes run downstream: from the stream's
    beginning near a base — 7.38 "starting near the T3 towers … down to the T1 towers"); the bonus is downstream only
    ("going upstream inflicts no penalty")."""
    out, walked, nxt = [], 0.0, _CURRENT_ARROW_EVERY / 2
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        seg = _math.hypot(bx - ax, by - ay)
        while seg and walked + seg >= nxt:
            t = (nxt - walked) / seg
            (px, py), (qx, qy) = proj(ax + (bx - ax) * t, ay + (by - ay) * t), proj(bx, by)
            d = _math.hypot(qx - px, qy - py) or 1.0
            ux, uy = (qx - px) / d, (qy - py) / d          # downstream, in viewBox units
            s = _CURRENT_ARROW
            out.append(f'<polyline points="{px - s * ux + s * uy:.1f},{py - s * uy - s * ux:.1f} {px:.1f},{py:.1f} '
                       f'{px - s * ux - s * uy:.1f},{py - s * uy + s * ux:.1f}"/>')
            nxt += _CURRENT_ARROW_EVERY
        walked += seg
    return "".join(out)


_CURRENT_ZONE = {150: ("#3f9cf0", 0.5), 100: ("#8fd0ff", 0.3)}     # max bonus speed -> fill, its opacity


def _current_svg(lines, areas, proj):
    """The river currents (the owner 2026-10-06: "точно покажи места, где юнит получает скорость от течения, т.е там,
    где действует бафф, а не просто линию течения"): each current's buff zone — its spline swept by each node's
    radius, traced by scripts/gen/build_terrain_diff.current_areas; on the renders it lies on the stream's water bank
    to bank — filled by its max bonus (7.38–7.40c: strong +150 deeper, moderate +100 paler; 7.41 made them all +150),
    one opacity per group so two zones that overlap are not darker, outlined, with arrows downstream."""
    body = ""
    for bonus, (colour, opacity) in _CURRENT_ZONE.items():
        fill = "".join(f'<path d="{_ring_path(a["rings"], proj)}" fill-rule="evenodd"/>'
                       for a in areas if a["rings"] and a["max"] == bonus)
        if fill:
            body += (f'<g class="tc-current-zone tc-current-{bonus}" fill="{colour}" opacity="{opacity}">'
                     f'{fill}</g>')
    edge = "".join(f'<path d="{_ring_path(a["rings"], proj)}"/>' for a in areas if a["rings"])
    arrows = "".join(_flow_arrows(line, proj) for line in lines if len(line) > 1)
    if edge:
        body += f'<g fill="none" stroke="#9fd6ff" stroke-width="1.2" stroke-opacity="0.85">{edge}</g>'
    if arrows:
        body += (f'<g class="tc-current-flow" fill="none" stroke="#e6f6ff" stroke-width="1.8" '
                 f'stroke-linecap="round" stroke-linejoin="round">{arrows}</g>')
    return body


def _line_zone_svgs(diff, proj):
    """Lane creep paths (Radiant solid, Dire dashed: the two walk the same lane), river currents, shop zones with
    the neutral item stashes, hero / courier spawn points; no-ward zones join the No-ward layer, the Roshan pit
    the Roshan layer. Each old / new, split by the slider like the other layers."""
    def pts(points):
        return " ".join(f"{proj(x, y)[0]:.1f},{proj(x, y)[1]:.1f}" for x, y in points)

    def layer(key, side, body):
        return (f'<svg class="tc-markers tm-layer tm-layer-{key} tm-{side}" viewBox="0 0 {MAP_VB} {MAP_VB}" '
                f'preserveAspectRatio="none" aria-hidden="true">{body}</svg>')

    def dots(coords, r, fill, stroke=_MARKER_GOLD):
        return "".join(f'<circle cx="{proj(x, y)[0]}" cy="{proj(x, y)[1]}" r="{r}" fill="{fill}" stroke="{stroke}" '
                       f'stroke-width="1.6"/>' for x, y in coords)

    out = []
    ents = diff.get("entities") or {}
    zones = diff.get("zones") or {}

    def zone_svg(kind, fill, fill_opacity, stroke, dash, width=1.6):
        """A zone kind's hulls filled (one opacity for the group: overlapping hulls are not darker) and outlined
        ONCE round the shape they make together (build_terrain_diff.zone_outlines; the owner 2026-10-07 saw the
        Dire fountain shop's inner hull lines as a zone "из 2 частей"). A diff without outlines: each hull outlined."""
        z = zones.get(kind) or {}
        hulls, rings = z.get(side) or [], z.get(side + "Outline")
        body = ""
        if fill:
            body += (f'<g fill="{fill}" opacity="{fill_opacity}">'
                     + "".join(f'<polygon points="{pts(h)}"/>' for h in hulls) + "</g>")
        edge = rings if rings is not None else hulls
        return body + (f'<g fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"{dash}>'
                       + "".join(f'<polygon points="{pts(r)}"/>' for r in edge if len(r) > 2) + "</g>")

    for side in ("old", "new"):
        lanes = (diff.get("lanes") or {}).get(side) or []
        if lanes:
            dash = {"good": "", "bad": ' stroke-dasharray="7 5"'}
            body = "".join(
                f'<polyline class="tc-lane tc-lane-{p["team"]}" points="{pts(p["points"])}" fill="none" '
                f'stroke="{_LANE_COLOUR[p["team"]]}" stroke-width="2.6" stroke-linejoin="round"{dash[p["team"]]}/>'
                for p in lanes)
            body += dots([p["points"][0] for p in lanes], 5, "#0d100b")          # where each wave starts
            out.append(layer("lanes", side, body))
        currents = (diff.get("currents") or {}).get(side) or []
        areas = (diff.get("currentAreas") or {}).get(side) or []
        if currents or areas:
            out.append(layer("currents", side, _current_svg(currents, areas, proj)))
        shops = (zones.get("shops") or {}).get(side) or []
        stash = (ents.get("stash") or {}).get(side) or []
        if shops or stash:
            body = zone_svg("shops", _SHOP_COLOUR, 0.16, _SHOP_COLOUR, "")
            body += dots(stash, 6, "#5fd06a")
            out.append(layer("shops", side, body))
        heroes = (ents.get("heroSpawns") or {}).get(side) or []
        couriers = (ents.get("couriers") or {}).get(side) or []
        if heroes or couriers:
            out.append(layer("spawns", side, dots(heroes, 5, "#d24a5a") + dots(couriers, 3.2, "#7ec8ff")))
        if (zones.get("nowardZones") or {}).get(side):
            out.append(layer("nowards", side, zone_svg("nowardZones", None, 0, "#eb50ff", ' stroke-dasharray="6 4"',
                                                       width=1.8)))
        if (zones.get("roshanPit") or {}).get(side):
            out.append(layer("roshan", side, zone_svg("roshanPit", "#d24a5a", 0.14, "#d24a5a", "")))
    return "".join(out)


_latest_href = _site.latest_patch_href


# ---- terrain change list -----------------------------------------------------
# SOURCE OF TRUTH: the "Terrain Changes" sections in content/p*.py. Rather than
# duplicate them (and risk drift), we PARSE them straight out of the content files
# at build time — one list per patch that has a terrain section.
#
# ONE PAGE PER PATCH (2026-10-02, the owner: "the difference between the letter
# patches has to be shown too, not just two major versions"): every patch whose
# map file differs from the patch before's is a step (patch/map_versions.py)
# with its own page terrain_<code>.html comparing the two map files — its own
# pictures, markers, counts and its own notes. A patch with terrain notes but no
# step still gets a page, with a "comparison not available yet" fallback in place
# of the slider. Patches that shipped the very same map file (7.40b, 7.41b) get
# none; the next step's page names them.
# Marker overlays + tree/camp counts come from the committed per-step diff
# (data/terrain/terrain_diff_<patch>.json, scripts/gen/build_terrain_diff.py). The shared
# crop meta projects every patch's markers identically.


# Chip -> the key of its outlines on the map (scripts.js toggles .tm-hl-<key>); spawn boxes have none — the
# Spawn Boxes layer already marks a changed box (the owner 2026-10-02).
_HL_KEY = {"trees": "trees", "camps": "camps", "camp tiers": "camptiers", "no-ward cells": "nowards",
           **{name: key for key, name in _MOVED_NAMES.items()}}
# The map layer each chip's outlines belong to: pressing the chip turns it on, and the outlines show only while it
# is on (the owner 2026-10-03: "taking the Trees filter in the bar into account"). Wisdom runes have no layer.
_HL_LAYER = {"trees": "trees", "camps": "camps", "camptiers": "camps", "nowards": "nowards",
             **{key: key for key, _label, _icon, _colour in _ENTITY_LAYERS}}
# The outline follows the object's own marker (the owner 2026-10-03: "a square outline, like the tree itself"):
# squares round trees and camp icons, circles round the round entity markers — (shape, half size in viewBox units)
# trees: the tree's own square (the owner 2026-10-04: "outline the square itself in the colour of its change, only
# dashed" — not a contour round it); camps and the rest keep a ring round them
_HL_SHAPE = {"trees": ("rect", _TREE_SIDE / 2), "camps": ("rect", _CAMP_SIDE / 2 + 3),
             "camptiers": ("rect", _CAMP_SIDE / 2 + 3)}
_HL_PER_SQUARE = {"trees"}
_HL_ENT_SHAPE = ("circle", _ENT_DISC + 3)
# outline width, viewBox units (others: 2.4). Trees 1.6 -> 0.7 (the owner 2026-10-05 on the per-square outlines:
# "too thick, dashed or not — 2–2.5 times thinner, on the outer edge")
_HL_STROKE = {"trees": 0.7}
# Colour = what happened (the owner 2026-10-03, on 7.41d's "+23" no-ward cells drawn red: "it should be green,
# since they were added"), like the chip's own +green / −red: removed on the old map, added on the new one, moved
# on both — where it stood and where it stands (the owner: "a moved tree outlined yellow on the old map, and in its
# new spot, yellow too, when you slide to the new map")
_HL_RED = "#ff4d4d"
_HL_GREEN = "#5dff8a"
_HL_YELLOW = "#ffd23f"
_HL_COLOUR = {"moved": _HL_YELLOW, "removed": _HL_RED, "added": _HL_GREEN}
_HL_KINDS = ("moved", "removed", "added")
# a removed and an added spot this close (game units), each other's nearest, are one object moved
# (7.41 moved the Tormentors ~1700 units and the Twin Gates ~1240: one of each per side, so a long reach is safe)
_MOVE_REACH = {"trees": 200, "camps": _SAME_CAMP, "tormentors": 2500, "twinGates": 2000}
_MOVE_REACH_ENT = 1500
_CELL = 64                            # gridnav cell, game units
_CELL_FILL = 0.55                     # changed ward cells: filled like the magenta layer, red / green


def _pair_moves(removed, added, reach):
    """(removed left, added left, [(old spot, new spot)]): a removed and an added spot that are each other's nearest
    and closer than `reach` are one object that moved."""
    def d2(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
    pairs, used_r, used_a = [], set(), set()
    for i, r in enumerate(removed):
        if not added:
            break
        j = min(range(len(added)), key=lambda k: d2(r, added[k]))
        back = min(range(len(removed)), key=lambda k: d2(removed[k], added[j]))
        if back == i and j not in used_a and d2(r, added[j]) < reach ** 2:
            used_r.add(i)
            used_a.add(j)
            pairs.append((r, added[j]))
    return ([p for i, p in enumerate(removed) if i not in used_r],
            [p for j, p in enumerate(added) if j not in used_a], pairs)


def _changed_points(diff):
    """{highlight key: {"removed": [(x, y)], "added": [(x, y)], "moved": [((x, y) old, (x, y) new)]}} in world units
    — what's only on the old map, only on the new one, and what moved (a removed + an added spot paired by
    `_pair_moves`; a re-tiered camp counts as moved too: changed in place). Ward cells: removed = no-ward ground that
    turned wardable, added = ground that turned no-ward."""
    def split(old, new, reach):
        a, b = {tuple(p) for p in old}, {tuple(p) for p in new}
        removed, added, moved = _pair_moves(sorted(a - b), sorted(b - a), reach)
        return {"removed": removed, "added": added, "moved": moved}
    camps_old, camps_new = diff.get("campsOld", []), diff.get("campsNew", [])
    out = {"trees": split(diff.get("treesOld", []), diff.get("treesNew", []), _MOVE_REACH["trees"]),
           "camps": split([(c["x"], c["y"]) for c in camps_old], [(c["x"], c["y"]) for c in camps_new],
                          _MOVE_REACH["camps"]),
           "camptiers": {"moved": [((o["x"], o["y"]), (c["x"], c["y"]))
                                   for o, c in _retiered_pairs(camps_old, camps_new)]}}
    for key in _MOVED_NAMES:
        ed = diff.get("entities", {}).get(key)
        if ed:
            out[key] = split(ed.get("old", []), ed.get("new", []), _MOVE_REACH.get(key, _MOVE_REACH_ENT))
    w = diff.get("wards") or {}
    out["nowards"] = {"removed": [tuple(p) for p in w.get("toWardable", [])],
                      "added": [tuple(p) for p in w.get("toNoWard", [])]}
    return {k: v for k, v in out.items() if any(v.values())}


def _outline_union(mask, kind, centres, shape, colour, stroke=2.4):
    """One kind's outlines, overlapping ones merged into ONE contour (the owner 2026-10-03: a slightly moved object
    showed "two frames"): every shape widened by half the stroke, minus every shape narrowed by half the stroke (an
    SVG mask `mask`, an id unique on the page) — only the union's outer edge stays. Wrapped in .tm-hl-g-<kind> so
    the moved / removed / added switches can hide it."""
    if not centres:
        return ""
    form, s = shape
    h = stroke / 2

    def draw(grow):
        if form == "rect":
            a = round(s + grow, 2)
            return "".join(f'<rect x="{round(x - a, 1)}" y="{round(y - a, 1)}" width="{2 * a}" height="{2 * a}"/>'
                           for x, y in centres)
        return "".join(f'<circle cx="{x}" cy="{y}" r="{round(s + grow, 2)}"/>' for x, y in centres)
    return (f'<g class="tm-hl-g tm-hl-g-{kind}"><mask id="{mask}" maskUnits="userSpaceOnUse" x="0" y="0" '
            f'width="{MAP_VB}" height="{MAP_VB}"><rect width="{MAP_VB}" height="{MAP_VB}" fill="#fff"/>'
            f'<g fill="#000">{draw(-h)}</g></mask><g fill="{colour}" mask="url(#{mask})">{draw(h)}</g></g>')


def _cells_fill(kind, cells, proj, colour):
    """Changed ward cells filled half-transparent, like the magenta no-ward layer but red / green (the owner
    2026-10-03: "not an outline — filled, more transparent, like the original purple")."""
    if not cells:
        return ""
    h = _CELL // 2
    d = []
    for x, y in sorted(cells):
        (ax, ay), (bx, by) = proj(x - h, y + h), proj(x + h, y - h)
        d.append(f"M{ax} {ay}H{bx}V{by}H{ax}Z")
    return (f'<g class="tm-hl-g tm-hl-g-{kind}"><path d="{"".join(d)}" fill="{colour}" '
            f'fill-opacity="{_CELL_FILL}"/></g>')


def _union_edges(rects):
    """The outer boundary of a union of axis-aligned squares, as merged straight runs: ("h", y, x1, x2) and
    ("v", x, y1, y2). An edge keeps only the parts no other square covers; collinear pieces join into one run."""
    size = max((r[2] - r[0] for r in rects), default=1) or 1
    grid = {}
    for i, r in enumerate(rects):
        grid.setdefault((int(r[0] // size), int(r[1] // size)), []).append(i)

    def near(r):
        gx, gy = int(r[0] // size), int(r[1] // size)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                yield from grid.get((gx + dx, gy + dy), ())

    def uncovered(lo, hi, cover):
        out, cur = [], lo
        for a, b in sorted(cover):
            if b <= cur:
                continue
            if a > cur:
                out.append((cur, min(a, hi)))
            cur = max(cur, b)
            if cur >= hi:
                break
        if cur < hi:
            out.append((cur, hi))
        return [(a, b) for a, b in out if b - a > 0.05]
    runs = {}
    for i, (x1, y1, x2, y2) in enumerate(rects):
        others = [rects[j] for j in near(rects[i]) if j != i]
        for y in (y1, y2):                                  # top and bottom edges
            cover = [(max(x1, o[0]), min(x2, o[2])) for o in others if o[1] < y < o[3] and o[0] < x2 and o[2] > x1]
            runs.setdefault(("h", round(y, 1)), []).extend(uncovered(x1, x2, cover))
        for x in (x1, x2):                                  # left and right edges
            cover = [(max(y1, o[1]), min(y2, o[3])) for o in others if o[0] < x < o[2] and o[1] < y2 and o[3] > y1]
            runs.setdefault(("v", round(x, 1)), []).extend(uncovered(y1, y2, cover))
    edges = []
    for (kind, at), spans in runs.items():
        merged = []
        for a, b in sorted(spans):
            if merged and a <= merged[-1][1] + 0.05:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        edges += [(kind, at, round(a, 1), round(b, 1)) for a, b in merged]
    return edges


def _dashed_outlines(kind, centres, shape, colour, stroke, ghost=False):
    """Outlines drawn as thin, close dashes along their edges (the owner 2026-10-03: "on the old versions let
    everything be dashed"; 10-04, on the striped first try: "too thick, too few gaps — take the outline we already
    draw round a tree and just make it dashed"): squares merge into their union's outer edge (a grove gets one
    contour, as the solid outlines do), discs stay separate circles. `ghost` = where a moved object stood, on the
    new side: fainter. In .tm-hl-g-<kind>, so the moved / removed / added switches hide it."""
    if not centres:
        return ""
    form, s = shape
    if form == "rect":
        edges = _union_edges([(x - s, y - s, x + s, y + s) for x, y in centres])
        body = "".join(f'M{a} {at}H{b}' if k == "h" else f'M{at} {a}V{b}' for k, at, a, b in edges)
        marks = f'<path d="{body}"/>'
    else:
        marks = "".join(f'<circle cx="{round(x, 1)}" cy="{round(y, 1)}" r="{s}"/>' for x, y in centres)
    width, dash, gap = round(stroke * 0.85, 2), round(stroke * 1.25, 2), round(stroke * 0.9, 2)
    cls, faint = ("tm-hl-ghost", ' opacity="0.6"') if ghost else ("tm-hl-dashed", "")
    return (f'<g class="tm-hl-g tm-hl-g-{kind} {cls}" fill="none" stroke="{colour}" stroke-width="{width}" '
            f'stroke-dasharray="{dash} {gap}"{faint}>{marks}</g>')


def _square_outlines(kind, centres, half, colour, stroke, dashed, ghost=False):
    """Trees (the owner 2026-10-04, next to a red dashed contour round a grove and the row pictures' coloured squares:
    "not an outline round the square — outline the square itself in the colour of its change, only dashed"): every
    changed tree's OWN square gets its border in the change colour — dashed where it stood (old side; on the new side
    a moved tree's old spot, faint), solid where it stands now (new side). Under the dashes the same colour, faded,
    covers the tree's green border, so the gaps do not show green. In .tm-hl-g-<kind> for the switches.
    The line lies OUTSIDE the square (its inner edge on the square's edge — the owner 2026-10-05: "on the outer
    edge"), so the tree square itself stays whole."""
    if not centres:
        return ""
    width = stroke if not dashed else round(stroke * 0.85, 2)
    a = round(half + width / 2, 2)
    rects = "".join(f'<rect x="{round(x - a, 2)}" y="{round(y - a, 2)}" width="{round(2 * a, 2)}" '
                    f'height="{round(2 * a, 2)}"/>' for x, y in centres)
    if not dashed:
        return (f'<g class="tm-hl-g tm-hl-g-{kind} tm-hl-sq" fill="none" stroke="{colour}" '
                f'stroke-width="{stroke}">{rects}</g>')
    dash, gap = round(stroke * 1.25, 2), round(stroke * 0.9, 2)
    cls, faint = ("tm-hl-ghost", ' opacity="0.6"') if ghost else ("tm-hl-dashed", "")
    return (f'<g class="tm-hl-g tm-hl-g-{kind} {cls} tm-hl-sq" fill="none" stroke="{colour}"{faint}>'
            f'<g stroke-width="{width}" stroke-opacity="0.35">{rects}</g>'
            f'<g stroke-width="{width}" stroke-dasharray="{dash} {gap}">{rects}</g></g>')


def _highlights_svg(diff, proj):
    """Two SVGs per chip, hidden until the chip is pressed (and its layer is on): the old side's — removed red, moved
    yellow where it stood, all dashed — and the new side's — added green, moved yellow where it stands now, plus a
    dashed ghost where a moved one stood; each clipped to its side of the slider like the layers."""
    out = []
    for key, g in _changed_points(diff).items():
        layer = _HL_LAYER.get(key, "")
        for side in ("old", "new"):
            if key == "nowards":
                kind = "removed" if side == "old" else "added"
                body = _cells_fill(kind, g.get(kind, []), proj, _HL_COLOUR[kind])
            else:
                spots = {"moved": [m[0] if side == "old" else m[1] for m in g.get("moved", [])],
                         "removed": g.get("removed", []) if side == "old" else [],
                         "added": g.get("added", []) if side == "new" else []}
                shape, stroke = _HL_SHAPE.get(key, _HL_ENT_SHAPE), _HL_STROKE.get(key, 2.4)
                pts = {k: [proj(x, y) for x, y in spots[k]] for k in _HL_KINDS}
                if key in _HL_PER_SQUARE:               # each tree's own square in its change colour
                    half = shape[1]
                    body = "".join(_square_outlines(k, pts[k], half, _HL_COLOUR[k], stroke, dashed=side == "old")
                                   for k in _HL_KINDS)
                    if side == "new":
                        body += _square_outlines("moved", [proj(*m[0]) for m in g.get("moved", [])], half,
                                                 _HL_COLOUR["moved"], stroke, dashed=True, ghost=True)
                elif side == "old":                     # dashed = where it was
                    body = "".join(_dashed_outlines(k, pts[k], shape, _HL_COLOUR[k], stroke) for k in _HL_KINDS)
                else:                                   # solid = where it is, plus a faint dashed ghost of an old spot
                    body = "".join(_outline_union(f"tm-hl-mask-{key}-{side}-{k}", k, pts[k], shape, _HL_COLOUR[k],
                                                  stroke) for k in _HL_KINDS)
                    body += _dashed_outlines("moved", [proj(*m[0]) for m in g.get("moved", [])], shape,
                                             _HL_COLOUR["moved"], stroke, ghost=True)
            if body:
                out.append(f'<svg class="tc-markers tm-hl tm-hl-{key} tm-{side}" data-layer="{layer}" '
                           f'viewBox="0 0 {MAP_VB} {MAP_VB}" preserveAspectRatio="none" aria-hidden="true">{body}</svg>')
    return "".join(out) + _layer_highlights_svg(diff, proj)


def _hl_kinds(diff):
    """The kinds of change this step's outlines hold, in switch order (moved, removed, added)."""
    have = set()
    for g in _changed_points(diff).values():
        have |= {k for k, v in g.items() if v}
    for parts in _layer_changed(diff).values():
        have |= {k for k, v in parts.items() if v}
    return [k for k in _HL_KINDS if k in have]


# The 2026-10-06 layers' chips as buttons (the owner: "не могу нажать Changed in the map file фильтры новых слоёв"):
# chip name -> highlight key -> the layer it turns on
_LAYER_HL = {"lane paths": ("lanes", "lanes"), "river currents": ("currents", "currents"),
             "shop zones": ("shopzones", "shops"), "Roshan pit zones": ("roshanpit", "roshan"),
             "no-ward zones": ("nowardzones", "nowards"), "lane creep spawns": ("lanespawns", "lanes"),
             "hero spawns": ("herospawns", "spawns")}


def _layer_changed(diff):
    """{highlight key: {"moved": [(old, new)], "removed": [old], "added": [new]}} of the 2026-10-06 layers — a line
    or a zone as its point list, a spawn as its point."""
    if not diff:
        return {}
    out = {}
    lanes = diff.get("lanes") or {}
    lo = {(p["team"], p["lane"]): p["points"] for p in lanes.get("old", [])}
    ln = {(p["team"], p["lane"]): p["points"] for p in lanes.get("new", [])}
    out["lanes"] = {"moved": [(o, n) for _team, o, n in _lane_stretches(diff) if o or n],
                    "removed": [], "added": [v for k, v in ln.items() if k not in lo and lo]}
    co, cn = _current_shapes(diff, "old"), _current_shapes(diff, "new")
    pairs = list(zip(co, cn))
    out["currents"] = {"moved": [(a, b) for a, b in pairs if a != b], "removed": co[len(cn):], "added": cn[len(co):]}
    for key, zkey in (("shopzones", "shops"), ("roshanpit", "roshanPit"), ("nowardzones", "nowardZones")):
        z = (diff.get("zones") or {}).get(zkey) or {}
        a, b = z.get("old") or [], z.get("new") or []
        ka, kb = {_box_key_xy(p) for p in a}, {_box_key_xy(p) for p in b}
        out[key] = {"moved": [], "removed": [p for p in a if _box_key_xy(p) not in kb],
                    "added": [p for p in b if _box_key_xy(p) not in ka]}
    ents = diff.get("entities") or {}
    for key, ekey in (("lanespawns", "laneSpawns"), ("herospawns", "heroSpawns")):
        ed = ents.get(ekey) or {}
        if ed.get("old") and ed.get("new"):
            a, b = {tuple(p) for p in ed["old"]}, {tuple(p) for p in ed["new"]}
            removed, added, moved = _pair_moves(sorted(a - b), sorted(b - a), _MOVE_REACH_ENT)
            out[key] = {"moved": moved, "removed": removed, "added": added}
    return {k: v for k, v in out.items() if any(v.values())}


_LANE_MOVE_TOL = 60     # world units: a stretch of path within this of the other side's path is not marked
_LANE_STEP = 40         # world units between the samples that find where a path left the old one


def _seg_dist(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / ((dx * dx + dy * dy) or 1)
    t = max(0.0, min(1.0, t))
    return _math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def _moved_runs(path, other):
    """The runs of `path` that lie farther than _LANE_MOVE_TOL from `other` ([[x, y], …] each, the last sample within
    reach at each end so a run joins the path)."""
    samples = []
    for a, b in zip(path, path[1:]):
        n = max(1, int(_math.hypot(b[0] - a[0], b[1] - a[1]) // _LANE_STEP))
        samples += [[round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)] for i in range(n)]
    samples.append(list(path[-1]))
    far = [min(_seg_dist(q, a, b) for a, b in zip(other, other[1:])) > _LANE_MOVE_TOL for q in samples]
    runs, i = [], 0
    while i < len(samples):
        if not far[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(samples) and far[j + 1]:
            j += 1
        runs.append(samples[max(i - 1, 0):j + 2])
        i = j + 1
    return [r for r in runs if len(r) > 1]


def _lane_stretches(diff):
    """(team, old runs, new runs) of every changed lane path: only where the path really left its old line — farther
    than _LANE_MOVE_TOL. The owner 2026-10-06, the whole changed paths in yellow: "слишком много желтых линий… не
    понимаю, какая к чему относится"; then corners alone were too much: 7.41 moved a Dire top corner 200 units ALONG
    its line, which lit the whole top lane. A path whose corners changed but whose line stayed put keeps its changed
    corners' stretch (difflib on the corner lists), so its chip still shows something."""
    lanes = diff.get("lanes") or {}
    old = {(p["team"], p["lane"]): p["points"] for p in lanes.get("old", [])}
    out = []
    for p in lanes.get("new", []):
        a, b = old.get((p["team"], p["lane"])), p["points"]
        if not a or a == b or len(a) < 2 or len(b) < 2:
            continue
        runs_old, runs_new = _moved_runs(a, b), _moved_runs(b, a)
        if not runs_old and not runs_new:
            ta, tb = [tuple(q) for q in a], [tuple(q) for q in b]
            for op, i1, i2, j1, j2 in _difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
                if op != "equal":
                    runs_old.append([list(q) for q in ta[max(i1 - 1, 0):i2 + 1]])
                    runs_new.append([list(q) for q in tb[max(j1 - 1, 0):j2 + 1]])
        out.append((p["team"], runs_old, runs_new))
    return out


def _lane_highlight_svgs(diff, proj):
    """A lane path chip's outlines: each changed stretch — on the old side yellow dashed (where it ran); on the new side
    the stretch in its side's colour and style (Radiant green, Dire red dashed, as the layer draws them) over a yellow
    glow, its old run a thin yellow dashed ghost. Which side's wave it is stays readable."""
    def pts(points):
        return " ".join(f"{proj(x, y)[0]:.1f},{proj(x, y)[1]:.1f}" for x, y in points)
    stretches = _lane_stretches(diff)
    if not stretches:
        return []
    yellow = _HL_COLOUR["moved"]
    old = "".join(f'<polyline points="{pts(r)}"/>' for _t, runs, _n in stretches for r in runs)
    ghost = old
    glow = "".join(f'<polyline points="{pts(r)}"/>' for _t, _o, runs in stretches for r in runs)
    dash = {"good": "", "bad": ' stroke-dasharray="7 5"'}
    line = "".join(f'<polyline points="{pts(r)}" stroke="{_LANE_COLOUR[t]}"{dash[t]}/>'
                   for t, _o, runs in stretches for r in runs)
    common = 'fill="none" stroke-linejoin="round" stroke-linecap="round"'
    sides = {
        "old": f'<g class="tm-hl-g tm-hl-g-moved" {common} stroke="{yellow}" stroke-width="2.6" '
               f'stroke-dasharray="6 4">{old}</g>',
        "new": (f'<g class="tm-hl-g tm-hl-g-moved" {common}>'
                f'<g stroke="{yellow}" stroke-width="1.8" stroke-dasharray="5 4" opacity="0.75">{ghost}</g>'
                f'<g stroke="{yellow}" stroke-width="10" opacity="0.45">{glow}</g>'
                f'<g stroke-width="3">{line}</g></g>'),
    }
    return [f'<svg class="tc-markers tm-hl tm-hl-lanes tm-{side}" data-layer="lanes" viewBox="0 0 {MAP_VB} {MAP_VB}" '
            f'preserveAspectRatio="none" aria-hidden="true">{body}</svg>' for side, body in sides.items()]


def _layer_highlights_svg(diff, proj):
    """The changed lines, zones and spawns of the 2026-10-06 layers, in the chips' colours (old side dashed: where it
    was; new side solid, a moved line's old place a faint dashed ghost), hidden until their chip is pressed."""
    def pts(points):
        return " ".join(f"{proj(x, y)[0]:.1f},{proj(x, y)[1]:.1f}" for x, y in points)

    def group(kind, body, dashed, ghost=False):
        if not body:
            return ""
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        faint = ' opacity="0.6"' if ghost else ""
        return (f'<g class="tm-hl-g tm-hl-g-{kind}" fill="none" stroke="{_HL_COLOUR[kind]}" stroke-width="3.2" '
                f'stroke-linejoin="round"{dash}{faint}>{body}</g>')

    out = []
    for key, parts in _layer_changed(diff).items():
        if key == "lanes" and parts.get("moved"):
            out += _lane_highlight_svgs(diff, proj)
            continue
        layer = next(lay for k, lay in _LAYER_HL.values() if k == key)
        point = key in ("lanespawns", "herospawns")
        closed = key in ("shopzones", "roshanpit", "nowardzones", "currents")

        def draw(shapes):
            if point:
                return "".join(f'<circle cx="{proj(x, y)[0]}" cy="{proj(x, y)[1]}" r="{_ENT_DISC + 3}"/>'
                               for x, y in shapes)
            if key == "currents":                  # a current is its zone's rings
                shapes = [ring for rings in shapes for ring in rings]
            tag = "polygon" if closed else "polyline"
            return "".join(f'<{tag} points="{pts(s)}"/>' for s in shapes if len(s) > 1)
        for side in ("old", "new"):
            moved = [m[0] if side == "old" else m[1] for m in parts.get("moved", [])]
            body = group("moved", draw(moved), dashed=side == "old")
            if side == "old":
                body += group("removed", draw(parts.get("removed", [])), dashed=True)
            else:
                body += group("added", draw(parts.get("added", [])), dashed=False)
                body += group("moved", draw([m[0] for m in parts.get("moved", [])]), dashed=True, ghost=True)
            if body:
                out.append(f'<svg class="tc-markers tm-hl tm-hl-{key} tm-{side}" data-layer="{layer}" '
                           f'viewBox="0 0 {MAP_VB} {MAP_VB}" preserveAspectRatio="none" aria-hidden="true">{body}</svg>')
    return "".join(out)


# The list keeps Valve's order and shows no tag chips (2026-10-03); the tag still sets each row's data-tag
_TAG_CLS = {
    "NEW": ("new", "new", ' data-overall="buff"'),
    "REWORK": ("rework", "rework", ""),
    "BUFF": ("buff-text", "buff", ' data-overall="buff"'),
    "NERF": ("nerf-text", "nerf", ' data-overall="nerf"'),
    "DEL": ("del", "del", ' data-overall="nerf"'),
    "MISC": ("misc", "misc", ""),
    "QoL": ("qol", "qol", ""),
}


def _change_li(text, tag, note=None, patch=None, num=None):
    _cls, tid, overall = _TAG_CLS[tag]
    from patch.elements import terrain_note, terrain_button, terrain_num_chip
    phrase, shots = terrain_note(patch, text, prefix="")
    # data-tag carries the primary tag plus its filter-overall (NEW→buff,
    # DEL→nerf) so a future filter surfaces them correctly; dedupe so BUFF/NERF
    # (whose tid already equals the overall) don't repeat.
    tags = [tid]
    if 'data-overall="buff"' in overall and "buff" not in tags:
        tags.append("buff")
    elif 'data-overall="nerf"' in overall and "nerf" not in tags:
        tags.append("nerf")
    if note:
        # the row's inline note: the (?) popup on its last word, as on the patch page
        from patch.elements import info_tip
        head, _sp, last = text.rpartition(" ")
        text = f'{head}{_sp}<span class="li-tail">{last}{info_tip(note)}</span>'
    if phrase:                   # the words naming the note's object open its pictures (the owner 2026-10-03)
        text = terrain_button(text, phrase)
    # the chip is the row's number in its category, as on the patch page — no tag (the owner 2026-10-03)
    chip = terrain_num_chip(num) if num else '<span class="row-tag-empty"></span>'
    return (f'<li class="terrain-row" data-tag="{" ".join(tags)}">{chip}'
            f'<span class="row-text">{text}</span>{shots}</li>')


def _changes_html(subpatches, skip_first_head=False):
    """Render change list for one major-version bucket.

    subpatches: [(sub_ver, [(text, tag, subgroup[, note]), ...]), ...]  oldest-first.
    subgroup and note may be None.
    """
    parts = []
    for idx, (sub_ver, rows) in enumerate(subpatches):
        if idx > 0 or not skip_first_head:
            parts.append(f'<li class="terrain-subpatch-head">{sub_ver}</li>')
        # Group rows by subgroup, preserving order of first appearance
        from collections import OrderedDict
        groups = OrderedDict()
        for i, row in enumerate(rows):
            text, tag = row[0], row[1]
            sg = row[2] if len(row) > 2 else None
            note = row[3] if len(row) > 3 else None
            groups.setdefault(sg, []).append((i, text, tag, note))
        for sg, sg_rows in groups.items():
            if sg:
                parts.append(f'<li class="terrain-subgroup-head">{sg}</li>')
            # Valve's order, numbered from 1 in each category like the patch page (no tags since 2026-10-03), so a
            # row has the same number on both pages
            parts.extend(_change_li(text, tag, note, sub_ver, num=k)
                         for k, (_, text, tag, note) in enumerate(sg_rows, 1))
    return "\n".join(parts)


def _controls_html(layers=True, changes=("", ""), heights=False):
    """The control bar ABOVE the map (not overlaid, so it never covers the now
    edge-to-edge map): the Zoom mode button + every overlay-layer toggle (Trees,
    Camps, and the eight point-entity layers). Icon-only square buttons with
    tooltips + a colour dot matching each layer's map markers, wrapping as the
    width allows.

    layers=False  — only the Zoom button (no layer toggles). Used for map pairs
                    that ship no terrain_diff_<ver>.json (no marker data), so the
                    toggles would be dead buttons."""
    _FS_ENTER_ICON = (
        '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" '
        'aria-hidden="true" focusable="false">'
        '<path d="M1 5V1h4M13 5V1H9M1 9v4h4M13 9v4H9" '
        'stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )
    _FS_EXIT_ICON = (
        '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" '
        'aria-hidden="true" focusable="false">'
        '<path d="M5 5V1M5 5H1M9 5V1M9 5h4M5 9v4M5 9H1M9 9v4M9 9h4" '
        'stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )

    def layer_btn(key, label, icon, icon_dir="ui/gothic"):
        return (f'<button type="button" class="tc-btn tc-btn-icon tc-layer-btn" '
                f'data-layer="{key}" aria-pressed="false" '
                f'title="{_esc(label)}" aria-label="{_esc(label)}">'
                f'<img src="icons/{icon_dir}/{icon}.png" alt="" '
                f'width="16" height="16"></button>')

    layer_parts = []
    if layers:
        layer_parts.append('<span class="tc-sep" aria-hidden="true"></span>')
        # "All layers" (the owner 2026-10-02): turns every layer below on, or all off
        # when they're all on already (scripts.js); pressed while every layer is on.
        layer_parts.append(layer_btn("all", "All layers", "tc_all"))
        layer_parts.append(layer_btn("trees", "Trees", "tc_trees"))
        layer_parts.append(layer_btn("camps", "Neutral Camps", "creepcamp_mid", icon_dir="camps"))
        layer_parts.append(layer_btn("spawnboxes", "Spawn Boxes", "icon_spawnbox"))
        # every place a ward can't stand (the owner 2026-10-02), from the map's gridnav
        layer_parts.append(layer_btn("nowards", "No-ward ground", "tc_nowards"))
        if heights:   # the map's height grid (2026-10-05), only where both sides have a picture
            layer_parts.append(layer_btn("heights", "Heights", "tc_heights"))
        for key, label, icon, _color in _ENTITY_LAYERS:
            layer_parts.append(layer_btn(key, label, icon))
        # 2026-10-06 (the owner: "все слои"): straight from the map file's entities
        # the colours explained (the owner 2026-10-06 asked what the red and green lines are, and why two dashed
        # lines stand in the Radiant base: the Dire waves' path goes on past the barracks to the Ancient)
        layer_parts.append(layer_btn("lanes", "Lane creep paths: green solid — Radiant waves, red dashed — Dire "
                                     "waves (on a shared lane the green covers the red); a dot — where a wave "
                                     "spawns; each path ends at the enemy Ancient", "tc_lanes"))
        layer_parts.append(layer_btn("currents", "River currents: where the bonus movement speed acts, downstream "
                                     "(arrows); deeper blue up to +150, paler up to +100 (before 7.41)", "tc_currents"))
        layer_parts.append(layer_btn("shops", "Shops and neutral item stashes", "tc_shops"))
        layer_parts.append(layer_btn("spawns", "Hero and courier spawn points", "tc_spawns"))

    # Top bar: Zoom + Fullscreen + layer toggles
    # Icon-only, the word in the tooltip (2026-10-06): with the four map-file layers 19 toggles + "Zoom" + "Full"
    # needed 792 px of a 720-px bar — the owner wants every toggle on one line (2026-10-02, 2026-10-05)
    top_parts = [
        '<button type="button" class="tc-btn tc-btn-icon tc-btn-zoom" aria-pressed="false" '
        'aria-label="Zoom" title="Zoom">'
        '<img src="icons/ui/gothic/icon_loupe.png" alt="" width="15" height="15"></button>',
        f'<button type="button" class="tc-btn tc-btn-icon tc-btn-fs" aria-pressed="false" '
        f'aria-label="Fullscreen" title="Fullscreen">{_FS_ENTER_ICON}</button>',
    ] + layer_parts

    _RMB_ICON = (
        '<svg width="16" height="16" viewBox="-3 -1 16 16" fill="none" '
        'aria-hidden="true" focusable="false">'
        '<rect x=".7" y=".7" width="8.6" height="12.6" rx="4.3" '
        'stroke="currentColor" stroke-width="1.2"/>'
        '<line x1="5" y1=".7" x2="5" y2="6.3" stroke="currentColor" stroke-width="1.2"/>'
        '<line x1=".7" y1="6.3" x2="9.3" y2="6.3" stroke="currentColor" stroke-width="1.2"/>'
        '<rect x="5.4" y="1.8" width="2.8" height="3.5" rx="1.4" '
        'fill="currentColor" opacity="0.5"/>'
        '</svg>'
    )
    _MMB_ICON = (
        '<svg width="16" height="16" viewBox="-3 -1 16 16" fill="none" '
        'aria-hidden="true" focusable="false">'
        '<rect x=".7" y=".7" width="8.6" height="12.6" rx="4.3" '
        'stroke="currentColor" stroke-width="1.2"/>'
        '<rect x="3.5" y="2" width="3" height="3.5" rx="1.5" '
        'stroke="currentColor" stroke-width="1.2"/>'
        '</svg>'
    )
    _CHEVRON = ('<svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true" focusable="false">'
                '<path d="M9 2.5L4.5 7L9 11.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
                'stroke-linejoin="round"/></svg>')
    fs_hints = (f'<span class="tc-fs-hint">{_RMB_ICON}Drag</span>'
                f'<span class="tc-fs-hint">{_MMB_ICON}Zoom</span>')
    # Fullscreen: a panel beside the map, not a bar under it (the owner 2026-10-03: the "Changed in the map file"
    # filters belong in fullscreen too — "a separate panel, left or right, that opens and closes, everything neat"):
    # Exit + a hide/show toggle, the layer toggles in a grid, the change switches and chips (the same buttons as
    # under the list — scripts.js keeps both copies in step), the mouse hints at the foot.
    kinds, chips = changes
    fs_layers = [p for p in layer_parts if 'class="tc-sep"' not in p]
    body = []
    if fs_layers:
        body.append(f'<div class="tc-fsp-title">Layers</div><div class="tc-fsp-layers">{"".join(fs_layers)}</div>')
    if chips:
        body.append('<div class="tc-fsp-title">Changed in the map file</div>'
                    + (f'<div class="tc-fsp-kinds">{kinds}</div>' if kinds else '')
                    + f'<div class="tc-fsp-chips">{chips}</div>')
    if heights:
        body.append(f'<div class="tc-fsp-title">Heights</div><div class="tf-hbands tc-fsp-chips">{_heights_buttons()}</div>')
    body.append(f'<div class="tc-fsp-hints">{fs_hints}</div>')
    fs_html = (
        '    <div class="tc-fs-bar" role="region" aria-label="Map controls">\n'
        '      <div class="tc-fsp-head">'
        '<button type="button" class="tc-btn tc-btn-fs-exit" aria-pressed="false" '
        'aria-label="Exit fullscreen" title="Exit fullscreen (Esc)">'
        f'{_FS_EXIT_ICON}<span class="tc-fsp-label">Exit</span></button>'
        '<button type="button" class="tc-btn tc-btn-icon tc-fsp-toggle" aria-expanded="true" '
        f'aria-label="Hide the panel" title="Hide the panel">{_CHEVRON}</button></div>\n'
        f'      <div class="tc-fsp-body">{"".join(body)}</div>\n'
        '    </div>\n')
    top_html = ('    <div class="tc-controls-bar">\n      '
                 + "".join(top_parts) + '\n    </div>\n')
    return top_html, fs_html


@_functools.lru_cache(maxsize=1)
def _height_bands():
    """(upper bound, RGB, label) of the Heights layer — scripts/gen/heightmap.py BANDS, the one source the pictures
    were drawn with."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("heightmap", _os.path.join(_HERE, "scripts", "gen", "heightmap.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.BANDS


def _heights_bands(diff):
    """{"old": (ver, [band, …]), "new": …} — the map files' heights pictures (one per band, heightmap.py all), or
    None when a side has none. The versions are the no-ward pictures' (the same map files)."""
    wards = (diff or {}).get("wards") or {}
    out = {}
    for side in ("old", "new"):
        ver = wards.get(side)
        bands = [k for k in range(len(_height_bands()))
                 if ver and _os.path.exists(_os.path.join(_HERE, "icons", "maps", f"heights_{ver}_{k}.png"))]
        if not bands:
            return None
        out[side] = (ver, bands)
    return out


def _heights_buttons():
    """The heights as switches — swatch + number, each one shows / hides its band on the map (the owner 2026-10-05:
    the key "should move into the panel; then 0, 128 … can be clicked to turn those layers on and off"). Under the
    change list and in the fullscreen panel alike; scripts.js initHeightBands keeps both copies in step. They are
    chips like "Changed in the map file" (the owner 2026-10-08: "чипы и текст таким же"): the swatch stands where a
    chip's icon is, the number bold."""
    return "".join(f'<button type="button" class="tf-chip tf-hband" data-hband="{k}" aria-pressed="true" '
                   f'aria-label="Height {_esc(label)}"><i class="tf-hband-sw" style="--c:rgb{rgb}"></i>'
                   f'<b>{_esc(label)}</b></button>' for k, (_top, rgb, label) in enumerate(_height_bands()))


def _compare_html(old_ver, new_ver, markers_svg="", old_pic=None, new_pic=None, changes=("", "")):
    """The before/after swipe stage + magnifier lens for an old→new map pair.

    old_ver/new_ver label the two sides; old_pic/new_pic (default: the same) name
    the pictures — a patch that kept the map file before it (7.40b) is shown with
    the picture of the patch that first shipped that file (7.40).

    Layers: top control bar | OLD map (base) | .tc-new-layer (NEW map, clipped
    to --pos) | tree/camp SVG (above maps, NOT slider-clipped) | drag handle |
    .tc-lens. The lens holds its own old/new map copies (scaled by data-zoom,
    positioned by scripts.js) reusing the SAME --pos clip; scripts.js also
    clones the marker SVG into it. Divider moves ONLY via the handle; in Loupe
    mode a plain click on the map pins/unpins the lens.

    markers_svg is non-empty when the patch ships a terrain_diff_<ver>.json; when
    empty, the layer-toggle buttons are dropped (Zoom stays)."""
    old_map = f"icons/maps/map_{old_pic or old_ver}.webp"
    new_map = f"icons/maps/map_{new_pic or new_ver}.webp"
    old_src, new_src = _picture_attrs(old_map), _picture_attrs(new_map)
    has_heights = "tm-layer-heights" in markers_svg
    top_bar, fs_bar = _controls_html(layers=bool(markers_svg), changes=changes, heights=has_heights)
    tiled = _tiled_pictures()
    tiles = "".join(f' data-tiles-{side}="{_TILES_BASE}{v}/"'
                    for side, v in (("old", old_pic or old_ver), ("new", new_pic or new_ver)) if v in tiled)
    return (
        f'<div class="terrain-compare" data-pos="50" data-zoom="1.9" data-lens="184"{tiles}>\n'
        f'{top_bar}'
        '  <div class="tc-fs-canvas">\n'
        '    <div class="tc-stage">\n'
        f'      <img class="tc-img tc-old" src="{old_src[0]}"{old_src[1]} '
        f'width="4096" height="4096" alt="Dota 2 map terrain in patch {old_ver}" '
        f'draggable="false" loading="eager" fetchpriority="high">\n'
        '      <div class="tc-new-layer">\n'
        f'        <img class="tc-img tc-new" src="{new_src[0]}"{new_src[1]} '
        f'width="4096" height="4096" alt="Dota 2 map terrain in patch {new_ver}" '
        f'draggable="false" loading="eager">\n'
        '      </div>\n'
        f'      {markers_svg}\n'
        f'      <span class="tc-ver tc-ver-new">NEW &nbsp;{new_ver} →</span>\n'
        f'      <span class="tc-ver tc-ver-old">← {old_ver}&nbsp; OLD</span>\n'
        '      <div class="tc-handle" role="slider" tabindex="0" '
        f'aria-label="Reveal {old_ver} versus {new_ver} terrain" '
        'aria-valuemin="0" aria-valuemax="100" aria-valuenow="50">\n'
        '        <span class="tc-line" aria-hidden="true"></span>\n'
        '        <span class="tc-grip" aria-hidden="true">'
        '<span class="tc-chev tc-chev-l"></span>'
        '<span class="tc-chev tc-chev-r"></span></span>\n'
        '      </div>\n'
        '      <div class="tc-lens" aria-hidden="true">\n'
        f'        <img class="tc-lens-img tc-lens-old"{old_src[1]} alt="" draggable="false">\n'
        f'        <img class="tc-lens-img tc-lens-new"{new_src[1]} alt="" draggable="false">\n'
        '        <span class="tc-lens-rim" aria-hidden="true"></span>\n'
        '      </div>\n'
        '    </div>\n'
        '  </div>\n'
        f'{fs_bar}'
        '</div>\n'
    )


def _signed(n):
    """' +3' green / ' −3' red; '' for 0."""
    if not n:
        return ""
    return f' <span class="{"tm-add-text" if n > 0 else "tm-rem-text"}">{"+" if n > 0 else "−"}{abs(n)}</span>'


# smallest to biggest (the owner 2026-10-02: "camps from smaller to bigger, not starting with ancient")
_CAMP_TIERS = ((0, "small"), (1, "medium"), (2, "large"), (3, "ancient"))

# The icon of each kind of object in the "Changed in the map file" chips (its map layer's icon).
_ITEM_ICON = {"trees": "ui/gothic/tc_trees", "camps": "camps/creepcamp_mid", "camp tiers": "camps/creepcamp_big",
              "camp spawn boxes": "ui/gothic/icon_spawnbox", "towers": "ui/gothic/tc_towers",
              "lotus pools": "ui/gothic/tc_lotus", "twin gates": "ui/gothic/tc_twingates",
              "Tormentors": "ui/gothic/tc_tormentors", "bounty runes": "ui/gothic/tc_bounty",
              "power runes": "ui/gothic/tc_power", "wisdom shrines": "ui/gothic/tc_wisdom",
              "wisdom runes": "ui/gothic/tc_wisdom", "outposts": "ui/gothic/tc_outposts",
              "watchers": "ui/gothic/tc_watchers", "Roshan pits": "ui/gothic/tc_roshan",
              "no-ward cells": "ui/gothic/tc_nowards",
              # 2026-10-06 layers
              "lane paths": "ui/gothic/tc_lanes", "river currents": "ui/gothic/tc_currents",
              "shop zones": "ui/gothic/tc_shops", "Roshan pit zones": "ui/gothic/tc_roshan",
              "no-ward zones": "ui/gothic/tc_nowards", "lane creep spawns": "ui/gothic/tc_lanes",
              "hero spawns": "ui/gothic/tc_spawns"}


_CHANGED_WORD = {"camp tiers": "re-tiered", "camp spawn boxes": "resized"}


def _strip_tags(html):
    """Plain text of a chip's value (its tooltip)."""
    import html as _html
    import re as _re
    return _html.unescape(_re.sub(r"<[^>]+>", "", html)).strip()


def _chip(name, kind, n, removed, total):
    """One kind of object in the changes: its layer icon and the change — "+added −removed", or "n/of all moved"
    (the owner 2026-10-02: "icon: change" instead of "Added / removed: No-ward cells +2"; "Bounty runes 1 moved
    (1/2)"). The name stays in the icon's alt text."""
    icon = _ITEM_ICON.get(name)
    label = _esc(name[:1].upper() + name[1:])
    img = (f'<img src="icons/{icon}.png" alt="{label}" width="16" height="16">' if icon
           else f'<span class="tf-chip-name">{label}</span>')
    if kind == "delta":
        # the result, not both halves (the owner 2026-10-04: "not +734 −548 — write the result, +186"); the outlines on
        # the map still show what was removed and what was added
        value = _signed(n - removed).strip() or '<span class="tf-chip-zero">±0</span>'
    else:
        # the word in its own span: the fullscreen panel shows just icon + "7/28" (the owner 2026-10-05), the
        # tooltip still says what changed
        value = f'<b>{n}/{total}</b> <span class="tf-chip-word">{_CHANGED_WORD.get(name, kind)}</span>'
    tip = _esc(f"{name[:1].upper() + name[1:]}: {_strip_tags(value)}")
    key = _HL_KEY.get(name)
    if name in _LAYER_HL:                     # a 2026-10-06 layer: its own highlight key and layer
        key, layer = _LAYER_HL[name]
        return (f'<button type="button" class="tf-chip tf-chip-btn" data-hl="{key}" '
                f'data-layer="{layer}" aria-pressed="false" data-tooltip="{tip}">{img}{value}</button>')
    if key:
        # pressed: the changed places outlined on the map, its layer turned on (scripts.js initChangeHighlights)
        return (f'<button type="button" class="tf-chip tf-chip-btn" data-hl="{key}" '
                f'data-layer="{_HL_LAYER.get(key, "")}" aria-pressed="false" data-tooltip="{tip}">{img}{value}</button>')
    return f'<span class="tf-chip" data-tooltip="{tip}">{img}{value}</span>'


def _facts_html(counts, step, diff):
    """The facts under the change list, in the list's own look (the owner
    2026-10-02: four lines of text "should be laid out better"; then the tables
    "aren't harmonious — it can be better"): headings like the list's subgroup
    heads, then
      ON THE MAP — five tiles: trees and the camp tiers small → ancient, icon +
        number + name, with the change since the patch before; then, a gap
        below, one tile per other kind of object (towers, runes, Roshan …);
      CHANGED IN THE MAP FILE — one chip per kind of object, "icon: change"
        (_chip), so a patch Valve's notes say nothing about still shows what
        changed.
    Patches that changed nothing on the map get no page and no mention (the
    owner: "remove 'Unchanged in 7.41f'")."""
    out = []
    if counts:
        old_t, new_t = counts.get("campsOld", {}), counts.get("campsNew", {})

        def tile(icon, num, name, delta):
            return (f'<div class="tf-tile"><div class="tf-num"><img src="icons/{icon}.png" alt="" width="16" '
                    f'height="16">{num}</div><div class="tf-name">{name}{_signed(delta)}</div></div>')
        trees = counts.get("treesNew", 0)
        tiles = [tile("ui/gothic/tc_trees", trees, "trees", trees - counts.get("treesOld", 0))]
        for t, label in _CAMP_TIERS:
            cur = new_t.get(t, new_t.get(str(t), 0))
            tiles.append(tile(f"camps/{_CAMP_ICON[t]}", cur, label, cur - old_t.get(t, old_t.get(str(t), 0))))
        # every other kind of object under them, a gap apart (the owner 2026-10-03: "trees and camps on one row,
        # everything else on the others")
        more = []
        for key, name in _MOVED_NAMES.items():
            old_n, new_n = counts.get("entities", {}).get(key, (0, 0))
            if old_n or new_n:
                more.append(tile(_ITEM_ICON[name], new_n, _esc(name), new_n - old_n))
        out.append('<div class="tf-head">On the map</div>\n'
                   f'<div class="tf-tiles">{"".join(tiles)}</div>\n'
                   + (f'<div class="tf-tiles tf-tiles-more">{"".join(more)}</div>\n' if more else ''))
    if step is not None:
        kinds, chips = _change_controls(diff)
        kinds_html = f'<span class="tf-kinds">{kinds}</span>' if kinds else ""
        out.append(f'<div class="tf-head">Changed in the map file{kinds_html}</div>\n'
                   + (f'<div class="tf-chips">{chips}</div>\n' if chips
                      else '<div class="tf-none">Nothing</div>\n'))
    if _heights_bands(diff):
        out.append(f'<div class="tf-head">Heights</div>\n<div class="tf-chips tf-hbands">{_heights_buttons()}</div>\n')
    return f'<div class="terrain-facts">\n{"".join(out)}</div>\n' if out else ""


def _change_controls(diff):
    """(switches, chips): the moved / removed / added switches (the owner 2026-10-03: "choose what to show: moved,
    removed or added"), each in its outline colour — scripts.js hides a kind with .hl-hide-<kind> on the map — and
    the "Changed in the map file" chips. Under the list and in the fullscreen panel alike; scripts.js keeps the
    copies in step."""
    chips = "".join(_chip(*i) for i in _moved_items(diff))
    if not chips:
        return "", ""
    kinds = "".join(f'<button type="button" class="tf-kind" data-kind="{k}" aria-pressed="true">'
                    f'<i class="tf-kind-sw tf-kind-{k}"></i>{k}</button>' for k in _hl_kinds(diff))
    return kinds, chips


# Fullscreen zoom tiles (scripts/gen/map_tiles.py): 16 x 16 tiles of an 8192 picture per map file, kept in
# Oldgrowth and served by its GitHub Pages (the owner 2026-10-02 chose that over growing Sloppy). renders.json
# "tiles" lists the pictures that have them.
_TILES_BASE = "https://sikleq.github.io/Oldgrowth/tiles/"


def _tiled_pictures():
    """Picture versions with zoom tiles published (data/map/renders.json "tiles")."""
    try:
        with open(_os.path.join(_HERE, "data", "map", "renders.json"), encoding="utf-8") as f:
            return set(_json.load(f).get("tiles", []))
    except (OSError, ValueError):
        return set()


def _picture_attrs(path):
    """(first src, data attrs) of a map picture. The page opens on the 2048-px copy (scripts/gen/map_small.py,
    ~0.85 MB against ~4.2 MB) when it exists; scripts.js fitSrc swaps in data-full once a picture pixel would be
    drawn bigger than a screen pixel (the owner 2026-10-03: "on weak computers it may lag")."""
    stem, ext = _os.path.splitext(path)
    small = f"{stem}_2k{ext}"
    full = f"{path}?v={ASSET_VERSION}"
    first = f"{small}?v={ASSET_VERSION}" if _os.path.exists(_os.path.join(_HERE, small)) else full
    return first, f' data-small="{first}" data-full="{full}"'


def _picker_html(patches, current):
    """Version-picker dropdown styled as nav-context-flat nav-context-materials,
    matching the aesthetic of non-patch pages while using href links. One item
    per page = per patch, newest first (scripts.js's subpatch arrows step
    through them in this order)."""
    items = []
    for ver in patches:
        cls = "version-item current" if ver == current else "version-item"
        href = _terrain_filename(ver, patches)
        items.append(
            f'<a class="{cls}" href="{href}" role="menuitem">'
            f'<span class="vi-name">{_esc(ver)}</span>'
            f'</a>')
    label = _site.get_materials_label('terrain') or 'Terrain'
    current_label = _esc(current)
    return (
        '<div class="nav-context nav-context-flat nav-context-materials nav-context-picker nav-context-terrain">'
        f'<span class="version version-static version-materials">{label}</span>'
        '<div class="version-picker">'
        '<div class="version-dropdown">'
        '<button class="version version-materials" type="button" '
        'aria-haspopup="true" aria-expanded="false">'
        f'{current_label} <span class="version-chev">▾</span>'
        '</button>'
        '<div class="version-menu" role="menu">'
        + "".join(items) +
        '</div>'
        '</div>'
        '</div>'
        '</div>'
    )


def _fallback_html(ver):
    """Shown in place of the swipe slider for a patch we don't yet hold a matched
    OLD->NEW map pair for: the latest map we DO have, blurred, with a centered
    "not available yet" overlay. The textual change list still renders beside it
    so the page stays useful before the art lands."""
    return (
        '<div class="terrain-fallback">\n'
        f'  <img class="tc-fallback-img" src="{_newest_map_img()}?v={ASSET_VERSION}" '
        'alt="" draggable="false" loading="lazy">\n'
        '  <div class="tc-fallback-veil"></div>\n'
        '  <div class="tc-fallback-msg">\n'
        f'    <span class="tc-fallback-title">Map comparison for {ver}</span>\n'
        '    <span class="tc-fallback-sub">isn’t available yet</span>\n'
        '    <span class="tc-fallback-note">The change list is on the right.</span>\n'
        '  </div>\n'
        '</div>\n'
    )


def _build_terrain_page(ver, patches, notes, step, diff, subnav):
    """Build one terrain HTML page: patch ``ver``'s map file against the patch
    before's (``step``, None when there's no pair → fallback), its own notes
    (``notes`` = {patch: rows}) and what moved (``diff``)."""
    nav = _site.render_top_nav('materials', _latest_href(),
                               patch_context=False,
                               subtabs_active='terrain',
                               picker_html=_picker_html(patches, ver),
                               subnav_in_header=False)

    markers, counts = (_markers_svg(diff, ver.replace(".", "")) if SHOW_MARKERS and diff
                       else ("", {}))
    # no line under the slider (the owner 2026-10-03: remove the credit line — every picture and
    # object list is ours, and the Oldgrowth README credits them)
    map_inner = (_compare_html(step.before, ver, markers, step.old_pic, step.new_pic,
                               changes=_change_controls(diff) if markers else ("", "")) if step
                 else _fallback_html(ver))

    counts_html = _facts_html(counts, step, diff)
    rows = notes.get(ver)
    # an empty list stays (the subpatch arrows hang off it); a patch whose notes say nothing about the map says
    # nothing here either — the facts below speak for it (the owner 2026-10-03: drop "Patch notes / No terrain
    # changes", "we won't write anything if there were no changes")
    list_html = _changes_html([(ver, rows)], skip_first_head=True) if rows else ""
    first_ver = ver

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<title>SIKLE | Terrain</title>\n'
        + _site.head_common() +
        f'<link rel="stylesheet" href="styles.css?v={ASSET_VERSION}">\n'
        '</head>\n<body>\n'
        f'{nav}\n'
        '<div class="container creeps-page terrain-page">\n'
        '<div class="creeps-scroll">\n'
        f'{subnav}'
        '<div class="terrain-wrap">\n'
        '<div class="terrain-compare-col">\n'
        f'<div class="terrain-map-pane" data-patch="{ver}">\n'
        f'{map_inner}</div>\n'
        '</div>\n'
        '<div class="terrain-list-box">\n'
        f'<div class="terrain-list-pane" data-patch="{ver}">\n'
        f'<div class="terrain-subpatch-head terrain-subpatch-top">{_esc(first_ver)}</div>\n'
        f'<ul class="changes terrain-list">\n{list_html}\n</ul>\n'
        f'{counts_html}'
        '</div>\n'
        '</div>\n'
        '</div>\n'
        '</div>\n'
        '</div>\n'
        f'<script defer src="src/scripts.js?v={ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n'
    )


def save_terrain_html():
    subnav = _site.render_materials_subnav('terrain')

    patches, notes, steps, diffs = page_patches()
    _os.makedirs(_site.DIST_DIR, exist_ok=True)
    for stale in _glob.glob(_os.path.join(_site.DIST_DIR, "terrain_[0-9]*.html")):
        _os.remove(stale)                     # a page that went quiet must not linger in dist/ (terrain_stats stays)
    total = sum(len(rows) for rows in notes.values())
    for ver in patches:
        page = _build_terrain_page(ver, patches, notes, steps.get(ver), diffs.get(ver), subnav)
        # the :has() facts styles.css now reads as classes (patch/static_has.py)
        from patch.static_has import add_static_has_classes
        page = add_static_has_classes(page)
        fname = _terrain_filename(ver, patches)
        out = _os.path.join(_site.DIST_DIR, fname)
        with open(out, "w", encoding="utf-8") as f:
            f.write(page)
        print(f"  -> dist/{fname}: {len(page):,} bytes")
    print(f"     ({len(patches)} terrain pages, {total} total changes)")


if __name__ == "__main__":
    save_terrain_html()
