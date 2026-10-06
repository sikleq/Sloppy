"""Build terrain_<code>.html — one terrain comparison page per patch (Materials tab).

A before/after **swipe slider** over the map file a patch shipped against the
one the patch before it ran, plus that patch's own "Terrain Changes" list and
what moved in the map file. Every patch whose map file changed is a page
(builders/map_versions.py: 7.38b … 7.41f), letter patches included; the header
picker and the subpatch arrows step through them. Each page has the FULL marker
toolbar (Trees / Camps / point-entities) from its committed
``data/terrain_diff_<patch>.json``.

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
import ast as _ast
import functools as _functools
import glob as _glob
import json as _json
import os as _os
import sys as _sys

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _HERE)

import builders.site_common as _site
import builders.map_versions as _map_versions
ASSET_VERSION = _site.compute_asset_version()

OLD_VER = "7.40"
NEW_VER = "7.41"
OLD_MAP = f"icons/maps/map_{OLD_VER}.webp"
NEW_MAP = f"icons/maps/map_{NEW_VER}.webp"

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


def _load_diff(patch):
    """The committed per-patch terrain diff (data/terrain_diff_<patch>.json,
    written by scripts/gen/build_terrain_diff.py). Returns None if absent so the page
    still builds (maps only, no markers) for a patch without a diff."""
    path = _os.path.join(_HERE, "data", f"terrain_diff_{patch}.json")
    try:
        with open(path, encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return None


def _load_map_meta():
    """Projection meta written by scripts/gen/build_terrain_maps.py — the leamare
    map boundaries + the crop box used for our map images. Without it the
    markers can't be placed accurately."""
    path = _os.path.join(_HERE, "data", "terrain_map_meta.json")
    try:
        with open(path, encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return None


def _projector(meta):
    """world (x,y) -> (px,py) in the MAP_VB viewBox, using the EXACT leamare
    projection (src/js/conversion.js worldToLatLon): world -> full-map pixel
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


def _box_key(box):
    """A camp spawn box as a hashable set of its corners (order-free)."""
    return frozenset((p["x"], p["y"]) for p in box)


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
        if currents:
            body = "".join(f'<polyline points="{pts(c)}" fill="none" stroke="{_CURRENT_COLOUR}" stroke-opacity="0.45" '
                           f'stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>'
                           f'<polyline points="{pts(c)}" fill="none" stroke="#d6efff" stroke-width="1.6" '
                           f'stroke-dasharray="4 6"/>' for c in currents if len(c) > 1)
            out.append(layer("currents", side, body))
        shops = (zones.get("shops") or {}).get(side) or []
        stash = (ents.get("stash") or {}).get(side) or []
        if shops or stash:
            body = "".join(f'<polygon points="{pts(z)}" fill="{_SHOP_COLOUR}" fill-opacity="0.16" '
                           f'stroke="{_SHOP_COLOUR}" stroke-width="1.6"/>' for z in shops)
            body += dots(stash, 6, "#5fd06a")
            out.append(layer("shops", side, body))
        heroes = (ents.get("heroSpawns") or {}).get(side) or []
        couriers = (ents.get("couriers") or {}).get(side) or []
        if heroes or couriers:
            out.append(layer("spawns", side, dots(heroes, 5, "#d24a5a") + dots(couriers, 3.2, "#7ec8ff")))
        nw = (zones.get("nowardZones") or {}).get(side) or []
        if nw:
            out.append(layer("nowards", side, "".join(
                f'<polygon points="{pts(z)}" fill="none" stroke="#eb50ff" stroke-width="1.8" stroke-dasharray="6 4"/>'
                for z in nw)))
        pit = (zones.get("roshanPit") or {}).get(side) or []
        if pit:
            out.append(layer("roshan", side, "".join(
                f'<polygon points="{pts(z)}" fill="#d24a5a" fill-opacity="0.14" stroke="#d24a5a" stroke-width="1.6"/>'
                for z in pit)))
    return "".join(out)


_latest_href = _site.latest_patch_href


# ---- terrain change list -----------------------------------------------------
# SOURCE OF TRUTH: the "Terrain Changes" sections in content/p*.py. Rather than
# duplicate them (and risk drift), we PARSE them straight out of the content files
# at build time — one list per patch that has a terrain section.
#
# ONE PAGE PER PATCH (2026-10-02, the owner: "the difference between the letter
# patches has to be shown too, not just two major versions"): every patch whose
# map file differs from the patch before's is a step (builders/map_versions.py)
# with its own page terrain_<code>.html comparing the two map files — its own
# pictures, markers, counts and its own notes. A patch with terrain notes but no
# step still gets a page, with a "comparison not available yet" fallback in place
# of the slider. Patches that shipped the very same map file (7.40b, 7.41b) get
# none; the next step's page names them.
# Marker overlays + tree/camp counts come from the committed per-step diff
# (data/terrain_diff_<patch>.json, scripts/gen/build_terrain_diff.py). The shared
# crop meta projects every patch's markers identically.


def _ver_key(v):
    """Sort key for version strings: '7.40' < '7.40b' < '7.41'."""
    import re
    def _part(s):
        m = re.match(r'^(\d+)([a-z]*)$', s)
        return (int(m.group(1)), m.group(2)) if m else (0, s)
    return tuple(_part(x) for x in v.split("."))


def _call_name(node):
    return node.func.id if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name) else None


def _str_arg(node):
    """A plain string literal ("a" "b" implicit concatenation is one constant)."""
    return node.value if isinstance(node, _ast.Constant) and isinstance(node.value, str) else None


def _row_tag(text, badge):
    """t("X") -> X; b(old, new[, l=True]) -> BUFF/NERF by the row's direction."""
    name = _call_name(badge)
    if name == "t" and badge.args:
        return _str_arg(badge.args[0]) or "MISC"
    if name in ("b", "bf"):
        lower_better = any(k.arg == "l" and isinstance(k.value, _ast.Constant) and k.value.value
                           for k in badge.keywords)
        low = text.lower()
        good = lower_better if ("decreased" in low or "reduced" in low) else not lower_better
        return "BUFF" if good else "NERF"
    return "MISC"


def _statements(body):
    """A function body's statements in order, nested if/for/with bodies included."""
    for st in body:
        yield st
        for field in ("body", "orelse"):
            if isinstance(st, (_ast.If, _ast.For, _ast.While, _ast.With)) and getattr(st, field, None):
                yield from _statements(getattr(st, field))


def _notes_in(source):
    """{patch: rows} of one content file (see _terrain_notes_by_patch)."""
    raw = {}
    for st in _ast.parse(source).body:
        if isinstance(st, _ast.FunctionDef):
            for k, v in _notes_in_body(st.body).items():
                raw.setdefault(k, []).extend(v)
    return raw


def _notes_in_body(body):
    raw, patch, in_block, sub = {}, None, False, None
    for st in _statements(body):
        call = st.value if isinstance(st, _ast.Expr) else None
        name = _call_name(call)
        if name == "write_head" and call.args:
            patch = _str_arg(call.args[0])
            continue
        if name != "W" or not call.args:
            continue
        inner = call.args[0]
        iname = _call_name(inner)
        if iname == "plain_header":
            title = _str_arg(inner.args[0]) if inner.args else None
            in_block = any(k.arg == "terrain_link" for k in inner.keywords)
            sub = None if title == "Terrain Changes" else title
        elif not in_block or iname in ("ul_open", "ul_close"):
            continue
        elif iname == "subgroup" and inner.args:
            sub = _str_arg(inner.args[0])
        elif iname == "li" and inner.args and _str_arg(inner.args[0]) and patch:
            text = _str_arg(inner.args[0])
            badge = inner.args[1] if len(inner.args) > 1 else next(
                (k.value for k in inner.keywords if k.arg == "badge"), None)
            extra = next((k.value for k in inner.keywords if k.arg == "extra"), None)
            note = (_str_arg(extra.args[0]) if _call_name(extra) == "inline_note" and extra.args else None)
            raw.setdefault(patch, []).append((text, _row_tag(text, badge), sub, note))
        else:
            in_block = False                   # any other block (an item, a unit, a section) ends it
    return raw


def _terrain_notes_by_patch():
    """Every patch's map notes from content/*.py: the rows of each block whose
    ``plain_header(..., terrain_link=...)`` links it to the map — "Terrain
    Changes" (7.39+), 7.38's "Wandering Waters" / "Other Terrain Changes",
    7.38c's "Dire Safe Lane Jungle" / "Top Roshan Pit" / "Bottom Lane" (the
    owner 2026-10-02: 7.38b's and 7.38c's map notes were missing). A block
    titled other than "Terrain Changes" is its own subgroup.

    Read as Python (ast), not by regex: a row's inline note (7.41's "Result:"
    lines under the Watcher row) comes along and the page shows it as on the
    patch page. Returns ``{patch: [(text, TAG, subgroup, note), ...]}``.
    """
    import glob as _glob
    raw = {}
    for p in sorted(_glob.glob(_os.path.join(_HERE, "content", "*.py"))):
        try:
            with open(p, encoding="utf-8") as f:
                found = _notes_in(f.read())
        except (OSError, SyntaxError):
            continue
        for k, v in found.items():
            raw.setdefault(k, []).extend(v)
    return raw


# What moved in the map file, per point-entity layer of the diff (plural nouns).
_MOVED_NAMES = {"towers": "towers", "lotus": "lotus pools", "twinGates": "twin gates",
                "tormentors": "Tormentors", "bounty": "bounty runes", "power": "power runes",
                "wisdom": "wisdom shrines", "wisdomRunes": "wisdom runes", "outposts": "outposts",
                "watchers": "watchers", "roshan": "Roshan pits"}


_SAME_CAMP = 1000          # units: a camp this close on both sides is the same camp, moved


def _retiered_pairs(old, new, radius=_SAME_CAMP):
    """Camps whose tier changed, as (old camp, new camp): each new camp paired with
    the old camp nearest to it when they are each other's nearest and within
    `radius`. By position, not by trigger name — 7.38 renumbered the camps (by
    name, camps "moved" 12000 units and "changed tier"), and a camp demoted AND
    moved (7.40's triangle camps) is still found, which an exact-position match
    missed (7.40 read 2 of its 4 demotions)."""
    def d2(a, b):
        return (a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2
    out = []
    for c in new:
        if not old:
            break
        o = min(old, key=lambda o: d2(o, c))
        back = min(new, key=lambda x: d2(o, x))
        if back is c and d2(o, c) <= radius ** 2 and o.get("tier") != c.get("tier"):
            out.append((o, c))
    return out


def _retiered(old, new, radius=_SAME_CAMP):
    return len(_retiered_pairs(old, new, radius))


def _moved_items(diff):
    """What changed between the step's two map files, read off its diff, as
    (name, kind, n, removed, total): kind "delta" when the count changed (n
    added, `removed` removed), "moved" when it kept its count (n of `total`
    moved), "changed" for camp tiers and resized/moved spawn boxes (7.39d:
    "Increased spawnboxes of Triangle Ancient camps"). [] when nothing changed."""
    if not diff:
        return []

    def delta(old, new, name):
        a, b = {tuple(p) for p in old}, {tuple(p) for p in new}
        added, removed = len(b - a), len(a - b)
        if not added and not removed:
            return None
        if len(old) == len(new):
            return (name, "moved", added, 0, len(new))
        return (name, "delta", added, removed, len(new))

    camps_new = diff.get("campsNew", [])
    out = [delta(diff.get("treesOld", []), diff.get("treesNew", []), "trees")]
    out.append(delta([(c["x"], c["y"]) for c in diff.get("campsOld", [])],
                     [(c["x"], c["y"]) for c in camps_new], "camps"))
    retiered = _retiered(diff.get("campsOld", []), camps_new)
    if retiered:
        out.append(("camp tiers", "changed", retiered, 0, len(camps_new)))
    old_boxes = {_box_key(b) for b in diff.get("spawnboxesOld", [])}
    new_boxes = {_box_key(b) for b in diff.get("spawnboxesNew", [])}
    if len(old_boxes) == len(new_boxes) and new_boxes - old_boxes:
        out.append(("camp spawn boxes", "changed", len(new_boxes - old_boxes), 0, len(new_boxes)))
    elif old_boxes != new_boxes:
        out.append(("camp spawn boxes", "delta", len(new_boxes - old_boxes), len(old_boxes - new_boxes),
                    len(new_boxes)))
    for key, name in _MOVED_NAMES.items():
        ed = diff.get("entities", {}).get(key)
        if ed:
            out.append(delta(ed.get("old", []), ed.get("new", []), name))
    w = diff.get("wards") or {}
    if w.get("lost") or w.get("gained"):
        # gridnav cells (64 units) where a ward can't stand: "lost" = became no-ward, so +lost −gained
        out.append(("no-ward cells", "delta", w.get("lost", 0), w.get("gained", 0), w.get("cells", 0)))
    out += _layer_changes(diff)
    return [i for i in out if i]


def _layer_changes(diff):
    """The 2026-10-06 layers as chips: lane paths changed (n of the 6 lanes), currents, the zones, spawn points —
    a patch's notes say nothing about some of them (7.39, 7.39b lane paths)."""
    out = []
    lanes = diff.get("lanes") or {}
    old = {(p["team"], p["lane"]): p["points"] for p in lanes.get("old", [])}
    new = {(p["team"], p["lane"]): p["points"] for p in lanes.get("new", [])}
    if old and new:
        n = sum(1 for k, v in new.items() if old.get(k) != v)
        if n:
            out.append(("lane paths", "changed", n, 0, len(new)))
    cur = diff.get("currents") or {}
    co, cn = cur.get("old") or [], cur.get("new") or []
    if co != cn:
        if len(co) == len(cn):
            out.append(("river currents", "changed", sum(1 for a, b in zip(co, cn) if a != b), 0, len(cn)))
        else:                                      # 7.38: the streams (and their currents) are new
            out.append(("river currents", "delta", len(cn), len(co), len(cn)))
    for key, name in (("shops", "shop zones"), ("roshanPit", "Roshan pit zones"), ("nowardZones", "no-ward zones")):
        z = (diff.get("zones") or {}).get(key) or {}
        a, b = {_box_key_xy(p) for p in z.get("old", [])}, {_box_key_xy(p) for p in z.get("new", [])}
        if a != b:
            out.append((name, "changed", len(b - a), 0, len(b)) if len(a) == len(b)
                       else (name, "delta", len(b - a), len(a - b), len(b)))
    ents = diff.get("entities") or {}
    for key, name in (("laneSpawns", "lane creep spawns"), ("heroSpawns", "hero spawns")):
        ed = ents.get(key) or {}
        if ed.get("old") and ed.get("new"):
            a, b = {tuple(p) for p in ed["old"]}, {tuple(p) for p in ed["new"]}
            if a != b:
                out.append((name, "moved", len(b - a), 0, len(b)))
    return out


def _box_key_xy(points):
    return frozenset(tuple(p) for p in points)


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
    return "".join(out)


def _hl_kinds(diff):
    """The kinds of change this step's outlines hold, in switch order (moved, removed, added)."""
    have = set()
    for g in _changed_points(diff).values():
        have |= {k for k, v in g.items() if v}
    return [k for k in _HL_KINDS if k in have]


def _moved_summary(diff):
    """_moved_items as text — e.g. ["trees +38 −27", "camps moved: 2", "camp tiers
    changed: 4"] (the Oldgrowth table says the same)."""
    def text(name, kind, n, removed, _total):
        return {"delta": f"{name} +{n} −{removed}", "moved": f"{name} moved: {n}"}.get(kind, f"{name} {kind}: {n}")
    return [text(*i) for i in _moved_items(diff)]


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
        layer_parts.append(layer_btn("lanes", "Lane creep paths", "tc_lanes"))
        layer_parts.append(layer_btn("currents", "River currents", "tc_currents"))
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
        body.append(f'<div class="tc-fsp-title">Heights</div><div class="tf-hbands">{_heights_buttons()}</div>')
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
    change list and in the fullscreen panel alike; scripts.js initHeightBands keeps both copies in step."""
    return "".join(f'<button type="button" class="tf-hband" data-hband="{k}" aria-pressed="true" '
                   f'aria-label="Height {_esc(label)}"><i class="tf-hband-sw" style="--c:rgb{rgb}"></i>'
                   f'{_esc(label)}</button>' for k, (_top, rgb, label) in enumerate(_height_bands()))


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
        out.append(f'<div class="tf-head">Heights</div>\n<div class="tf-hbands">{_heights_buttons()}</div>\n')
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


def _quiet(steps, notes, diffs):
    """Steps whose notes list nothing and whose map file moved nothing — no page.
    Their pictures differ from the patch before only by render noise (checked
    2026-10-02 with scripts/gen/map_picture_diff.py: no change bigger than the
    wind in the trees), so there is nothing to compare. The newest step keeps its
    page all the same (the owner 2026-10-03: without it "one could think the patch
    doesn't exist" — 7.41f, the current map)."""
    newest = max(steps, key=_ver_key) if steps else None
    return {p for p in steps if p != newest and not notes.get(p) and not _moved_summary(diffs.get(p))}


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




def _terrain_filename(ver, patches=None):
    """terrain_<ver_slug>.html for every version."""
    return f"terrain_{ver.replace('.', '')}.html"


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
        f'  <img class="tc-fallback-img" src="{NEW_MAP}?v={ASSET_VERSION}" '
        'alt="" draggable="false" loading="lazy">\n'
        '  <div class="tc-fallback-veil"></div>\n'
        '  <div class="tc-fallback-msg">\n'
        f'    <span class="tc-fallback-title">Map comparison for {ver}</span>\n'
        '    <span class="tc-fallback-sub">isn’t available yet</span>\n'
        '    <span class="tc-fallback-note">The change list is on the right.</span>\n'
        '  </div>\n'
        '</div>\n'
    )


def _pages(steps, notes):
    """Every Terrain page, newest first: each step (a patch with its own map file)
    and each patch with terrain notes."""
    return sorted(set(steps) | set(notes), key=_ver_key, reverse=True)


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
    # no line under the slider (the owner 2026-10-03: remove "Inspired by Leamare and devilesk" — every picture and
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


def page_patches():
    """The patches that get a Terrain page, newest first (Terrain Stats links its rows to them), with what
    save_terrain_html needs to build them: (patches, notes, steps, diffs)."""
    notes = _terrain_notes_by_patch()
    steps = {s.patch: s for s in _map_versions.steps()}
    diffs = {p: _load_diff(p) for p in steps}
    quiet = _quiet(steps, notes, diffs)
    return (_pages([p for p in steps if p not in quiet], notes) or ["7.41"]), notes, steps, diffs


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
