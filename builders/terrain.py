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
import glob as _glob
import html as _html
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


def _esc(s):
    return _html.escape(str(s), quote=True)


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

    old_t = tier_counts(diff.get("campsOld", []))
    new_t = tier_counts(diff.get("campsNew", []))
    counts = {
        "treesOld": len(diff.get("treesOld", [])),
        "treesNew": len(diff.get("treesNew", [])),
        "campsOld": old_t, "campsNew": new_t,
        # every other kind of object, (old, new) — the "On the map" tiles under trees and camps
        "entities": {key: (len(ed.get("old", [])), len(ed.get("new", []))) for key, ed in entities.items() if ed},
    }
    return (ward_svgs + trees_old + trees_new + camps_old + camps_new
            + "".join(ent_svgs) + sb_svg + _highlights_svg(diff, proj), counts)


def _latest_href():
    """Latest patch page href for the Changelogs nav tab (from site_meta.json)."""
    from patch.meta import latest_patch_filename as _lpf
    _fallback = _lpf()
    meta_path = _os.path.join(_HERE, "data", "site_meta.json")
    try:
        meta = _json.loads(open(meta_path, encoding="utf-8").read())
        return meta.get("latest_patch_filename", _fallback)
    except Exception:
        return _fallback


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
    return [i for i in out if i]


# Chip -> the key of its red rings on the map (scripts.js toggles .tm-hl-<key>); spawn boxes have none — the
# Spawn Boxes layer already marks a changed box (the owner 2026-10-02).
_HL_KEY = {"trees": "trees", "camps": "camps", "camp tiers": "camptiers", "no-ward cells": "nowards",
           **{name: key for key, name in _MOVED_NAMES.items()}}
_HL_RING = {"trees": 6, "camps": 22, "camptiers": 26}      # ring radius, viewBox units (entities: 19)
# the outline's colour says what happened there (the owner 2026-10-03, on 7.41d's "+23" no-ward cells drawn red:
# "it should be green, since they were added") — like the chip's own +green / −red numbers
_HL_RED = "#ff4d4d"       # removed: only on the old map
_HL_GREEN = "#5dff8a"     # added: only on the new map
_HL_YELLOW = "#ffd23f"    # changed in place: moved a little (its two rings would overlap), re-tiered
_HL_COLOUR = {"removed": _HL_RED, "added": _HL_GREEN, "changed": _HL_YELLOW}


def _changed_points(diff):
    """{highlight key: {"removed" / "added" / "changed": [(x, y) world]}} — every place a chip's change touches:
    what's only on the old map (removed), only on the new one (added), the re-tiered camps (changed); for the ward
    cells, those that turned wardable (no-ward ground removed) and those that turned no-ward (added)."""
    def split(old, new):
        a, b = {tuple(p) for p in old}, {tuple(p) for p in new}
        return {"removed": sorted(a - b), "added": sorted(b - a)}
    out = {"trees": split(diff.get("treesOld", []), diff.get("treesNew", [])),
           "camps": split([(c["x"], c["y"]) for c in diff.get("campsOld", [])],
                          [(c["x"], c["y"]) for c in diff.get("campsNew", [])]),
           "camptiers": {"changed": [(o["x"], o["y"]) for o, _c in _retiered_pairs(diff.get("campsOld", []),
                                                                                  diff.get("campsNew", []))]}}
    for key in _MOVED_NAMES:
        ed = diff.get("entities", {}).get(key)
        if ed:
            out[key] = split(ed.get("old", []), ed.get("new", []))
    w = diff.get("wards") or {}
    out["nowards"] = {"removed": [tuple(p) for p in w.get("toWardable", [])],
                      "added": [tuple(p) for p in w.get("toNoWard", [])]}
    return {k: v for k, v in out.items() if any(v.values())}


def _small_moves(removed, added, reach):
    """Pairs of a removed and an added spot (projected) that are each other's nearest and closer than `reach` — one
    object moved a little. Returns (removed left, added left, the paired spots)."""
    def d2(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
    paired_r, paired_a = set(), set()
    for i, r in enumerate(removed):
        if not added:
            break
        j = min(range(len(added)), key=lambda k: d2(r, added[k]))
        back = min(range(len(removed)), key=lambda k: d2(removed[k], added[j]))
        if back == i and j not in paired_a and d2(r, added[j]) < reach ** 2:
            paired_r.add(i)
            paired_a.add(j)
    return ([p for i, p in enumerate(removed) if i not in paired_r],
            [p for j, p in enumerate(added) if j not in paired_a],
            [removed[i] for i in sorted(paired_r)] + [added[j] for j in sorted(paired_a)])


_HL_STROKE = 2.4          # outline width, viewBox units
_CELL = 64                # gridnav cell, game units


def _ring_union(mask, centres, r, colour=_HL_RED):
    """Rings that overlap merged into ONE outline (the owner 2026-10-03: a slightly moved object showed "two
    frames" — its old and new spot each ringed): every ring widened by half the stroke, minus every ring narrowed by
    half the stroke (an SVG mask `mask`, an id unique on the page), leaves only the outer contour of the union."""
    if not centres:
        return ""
    h = _HL_STROKE / 2
    outer = "".join(f'<circle cx="{x}" cy="{y}" r="{round(r + h, 2)}"/>' for x, y in centres)
    inner = "".join(f'<circle cx="{x}" cy="{y}" r="{round(r - h, 2)}"/>' for x, y in centres)
    return (f'<mask id="{mask}" maskUnits="userSpaceOnUse" x="0" y="0" width="{MAP_VB}" height="{MAP_VB}">'
            f'<rect width="{MAP_VB}" height="{MAP_VB}" fill="#fff"/><g fill="#000">{inner}</g></mask>'
            f'<g fill="{colour}" mask="url(#{mask})">{outer}</g>')


def _cell_outline(cells, proj, colour=_HL_RED):
    """The outline of a set of changed ward cells: only the sides no other changed cell shares, so neighbouring
    cells read as one patch, not a grid of squares."""
    if not cells:
        return ""
    have = {(round(x), round(y)) for x, y in cells}
    h = _CELL // 2
    segs = []
    for x, y in have:
        for (dx, dy), (ax, ay, bx, by) in (((0, _CELL), (-h, h, h, h)), ((0, -_CELL), (-h, -h, h, -h)),
                                           ((-_CELL, 0), (-h, -h, -h, h)), ((_CELL, 0), (h, -h, h, h))):
            if (x + dx, y + dy) not in have:
                (px, py), (qx, qy) = proj(x + ax, y + ay), proj(x + bx, y + by)
                segs.append(f"M{px} {py}L{qx} {qy}")
    return (f'<path d="{"".join(sorted(segs))}" fill="none" stroke="{colour}" stroke-width="{_HL_STROKE}" '
            f'stroke-linecap="square"/>')


def _highlights_svg(diff, proj):
    """One SVG per chip, hidden until its chip is pressed: outlines round the changed places on the OLD side of the
    slider (the owner: "outlined on the old version") — red where something is removed, green where something is
    added, yellow where it changed in place (moved so little its two rings would overlap, or re-tiered). Overlapping
    rings and neighbouring ward cells merge into one outline."""
    out = []
    for key, groups in _changed_points(diff).items():
        if key == "nowards":
            body = "".join(_cell_outline(groups.get(g, []), proj, _HL_COLOUR[g]) for g in ("removed", "added"))
        else:
            r = _HL_RING.get(key, 19)
            removed, added, moved = _small_moves([proj(x, y) for x, y in groups.get("removed", [])],
                                                 [proj(x, y) for x, y in groups.get("added", [])], 2 * r)
            spots = {"removed": removed, "added": added,
                     "changed": [proj(x, y) for x, y in groups.get("changed", [])] + moved}
            body = "".join(_ring_union(f"tm-hl-mask-{key}-{g}", spots[g], r, _HL_COLOUR[g])
                           for g in ("removed", "added", "changed"))
        out.append(f'<svg class="tc-markers tm-hl tm-hl-{key} tm-old" viewBox="0 0 {MAP_VB} {MAP_VB}" '
                   f'preserveAspectRatio="none" aria-hidden="true">{body}</svg>')
    return "".join(out)


def _moved_summary(diff):
    """_moved_items as text — e.g. ["trees +38 −27", "camps moved: 2", "camp tiers
    changed: 4"] (the Oldgrowth table says the same)."""
    def text(name, kind, n, removed, _total):
        return {"delta": f"{name} +{n} −{removed}", "moved": f"{name} moved: {n}"}.get(kind, f"{name} {kind}: {n}")
    return [text(*i) for i in _moved_items(diff)]


# Canonical tag order (same as the site convention): NEW → REWORK → BUFF →
# NERF → DEL → QoL → MISC. QoL gets its own rank before MISC so QoL rows group
# together instead of interleaving with MISC. Stable within a rank.
_TAG_RANK = {"NEW": 1, "REWORK": 2, "BUFF": 3, "NERF": 4, "DEL": 5,
             "QoL": 6, "MISC": 7}
_TAG_CLS = {
    "NEW": ("new", "new", ' data-overall="buff"'),
    "REWORK": ("rework", "rework", ""),
    "BUFF": ("buff-text", "buff", ' data-overall="buff"'),
    "NERF": ("nerf-text", "nerf", ' data-overall="nerf"'),
    "DEL": ("del", "del", ' data-overall="nerf"'),
    "MISC": ("misc", "misc", ""),
    "QoL": ("qol", "qol", ""),
}


def _badge(tag):
    cls, tid, _extra = _TAG_CLS[tag]
    return f'<span class="badge {cls}" data-tag="{tid}">{tag}</span>'


def _change_li(text, tag, note=None):
    _cls, tid, overall = _TAG_CLS[tag]
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
    return (f'<li data-tag="{" ".join(tags)}">{_badge(tag)}'
            f'<span class="row-text">{text}</span></li>')


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
            sorted_rows = sorted(sg_rows,
                                 key=lambda it: (_TAG_RANK.get(it[2], 9), it[0]))
            parts.extend(_change_li(text, tag, note) for _, text, tag, note in sorted_rows)
    return "\n".join(parts)


def _controls_html(layers=True):
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
        for key, label, icon, _color in _ENTITY_LAYERS:
            layer_parts.append(layer_btn(key, label, icon))

    # Top bar: Zoom + Fullscreen + layer toggles
    top_parts = [
        '<button type="button" class="tc-btn tc-btn-zoom" aria-pressed="false">'
        '<img src="icons/ui/gothic/icon_loupe.png" alt="" width="15" height="15">'
        'Zoom</button>',
        f'<button type="button" class="tc-btn tc-btn-fs" aria-pressed="false" '
        f'aria-label="Fullscreen" title="Fullscreen">'
        # "Full", not "Fullscreen": the owner 2026-10-02 — every toggle on one line
        f'{_FS_ENTER_ICON}Full</button>',
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
    fs_hints = (
        '<span class="tc-sep" aria-hidden="true"></span>'
        f'<span class="tc-fs-hint">{_RMB_ICON}Drag</span>'
        f'<span class="tc-fs-hint">{_MMB_ICON}Zoom</span>'
    )
    # Bottom fullscreen bar: Exit + same layer toggles (no Zoom) + hints
    fs_parts = [
        f'<button type="button" class="tc-btn tc-btn-fs-exit" aria-pressed="false" '
        f'aria-label="Exit fullscreen" title="Exit fullscreen (Esc)">'
        f'{_FS_EXIT_ICON}Exit</button>',
    ] + (layer_parts if layers else []) + [fs_hints]

    top_html = ('    <div class="tc-controls-bar">\n      '
                 + "".join(top_parts) + '\n    </div>\n')
    fs_html = ('    <div class="tc-fs-bar">\n      '
               + "".join(fs_parts) + '\n    </div>\n')
    return top_html, fs_html


def _compare_html(old_ver, new_ver, markers_svg="", old_pic=None, new_pic=None):
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
    top_bar, fs_bar = _controls_html(layers=bool(markers_svg))
    tiled = _tiled_pictures()
    tiles = "".join(f' data-tiles-{side}="{_TILES_BASE}{v}/"'
                    for side, v in (("old", old_pic or old_ver), ("new", new_pic or new_ver)) if v in tiled)
    return (
        f'<div class="terrain-compare" data-pos="50" data-zoom="1.9" data-lens="184"{tiles}>\n'
        f'{top_bar}'
        '  <div class="tc-fs-canvas">\n'
        '    <div class="tc-stage">\n'
        f'      <img class="tc-img tc-old" src="{old_map}?v={ASSET_VERSION}" '
        f'width="4096" height="4096" alt="Dota 2 map terrain in patch {old_ver}" '
        f'draggable="false" loading="eager" fetchpriority="high">\n'
        '      <div class="tc-new-layer">\n'
        f'        <img class="tc-img tc-new" src="{new_map}?v={ASSET_VERSION}" '
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
        f'        <img class="tc-lens-img tc-lens-old" src="{old_map}?v={ASSET_VERSION}" alt="" draggable="false">\n'
        f'        <img class="tc-lens-img tc-lens-new" src="{new_map}?v={ASSET_VERSION}" alt="" draggable="false">\n'
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
              "no-ward cells": "ui/gothic/tc_nowards"}


_CHANGED_WORD = {"camp tiers": "re-tiered", "camp spawn boxes": "resized"}


def _chip(name, kind, n, removed, total):
    """One kind of object in the changes: its layer icon and the change — "+added −removed", or "n/of all moved"
    (the owner 2026-10-02: "icon: change" instead of "Added / removed: No-ward cells +2"; "Bounty runes 1 moved
    (1/2)"). The name stays in the icon's alt text."""
    icon = _ITEM_ICON.get(name)
    label = _esc(name[:1].upper() + name[1:])
    img = (f'<img src="icons/{icon}.png" alt="{label}" width="16" height="16">' if icon
           else f'<span class="tf-chip-name">{label}</span>')
    if kind == "delta":
        value = f'{_signed(n)}{_signed(-removed)}'.strip()
    else:
        value = f'<b>{n}/{total}</b> {_CHANGED_WORD.get(name, kind)}'
    key = _HL_KEY.get(name)
    if key:
        # pressed: the changed places outlined on the old side of the map (scripts.js initChangeHighlights)
        return (f'<button type="button" class="tf-chip tf-chip-btn" data-hl="{key}" aria-pressed="false">'
                f'{img}{value}</button>')
    return f'<span class="tf-chip">{img}{value}</span>'


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
        chips = [_chip(*i) for i in _moved_items(diff)]
        out.append('<div class="tf-head">Changed in the map file</div>\n'
                   + (f'<div class="tf-chips">{"".join(chips)}</div>\n' if chips
                      else '<div class="tf-none">Nothing</div>\n'))
    return f'<div class="terrain-facts">\n{"".join(out)}</div>\n' if out else ""


def _quiet(steps, notes, diffs):
    """Steps whose notes list nothing and whose map file moved nothing — no page.
    Their pictures differ from the patch before only by render noise (checked
    2026-10-02 with scripts/gen/map_picture_diff.py: no change bigger than the
    wind in the trees), so there is nothing to compare."""
    return {p for p in steps if not notes.get(p) and not _moved_summary(diffs.get(p))}


_INSPIRED_BY = (("Leamare", "https://github.com/leamare/dota-interactive-map"),
                ("devilesk", "https://github.com/devilesk/dota-interactive-map"))


def _own_pictures():
    """Versions whose map picture we rendered ourselves (data/map/renders.json)."""
    try:
        with open(_os.path.join(_HERE, "data", "map", "renders.json"), encoding="utf-8") as f:
            return set(_json.load(f)["pictures"])
    except (OSError, ValueError, KeyError):
        return set()


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


def _own_entities(ver):
    """True when the version's map entities are read from the game files by us (data/map/mapdata_<code>.json)."""
    return _os.path.exists(_os.path.join(_HERE, "data", "map", f"mapdata_{ver.replace('.', '')}.json"))


def _source_html(old_ver=None, new_ver=None):
    """Credit under the slider, kept to the minimum (the owner 2026-10-01): inspired by Leamare's and devilesk's
    interactive maps; a version whose picture or objects are still Leamare's is named, so the line never claims
    more than is true."""
    def link(name, url):
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>'
    names = " and ".join(link(n, u) for n, u in _INSPIRED_BY)
    vers = [v for v in (old_ver, new_ver) if v]
    pics = _own_pictures()
    borrowed = [v for v in vers if v not in pics or not _own_entities(v)]
    note = f" {', '.join(borrowed)}: Leamare’s map for now." if borrowed else ""
    return f'<p class="tc-source">Inspired by {names}.{note}</p>\n'


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
    if step:
        map_inner = _compare_html(step.before, ver, markers, step.old_pic, step.new_pic)
        credit = _source_html(step.old_pic, step.new_pic)
    else:
        map_inner = _fallback_html(ver)
        credit = _source_html()

    counts_html = _facts_html(counts, step, diff)
    rows = notes.get(ver)
    # an empty list stays (the subpatch arrows hang off it); a patch whose notes say nothing about the map says
    # nothing here either — the facts below speak for it (the owner 2026-10-03: drop "Patch notes / No terrain
    # changes", "we won't write anything if there were no changes")
    list_html = _changes_html([(ver, rows)], skip_first_head=True) if rows else ""
    first_ver = ver

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>SIKLE | Terrain</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
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
        f'{credit}'
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

    notes = _terrain_notes_by_patch()
    steps = {s.patch: s for s in _map_versions.steps()}
    diffs = {p: _load_diff(p) for p in steps}
    quiet = _quiet(steps, notes, diffs)
    patches = _pages([p for p in steps if p not in quiet], notes) or ["7.41"]
    _os.makedirs(_site.DIST_DIR, exist_ok=True)
    for stale in _glob.glob(_os.path.join(_site.DIST_DIR, "terrain_*.html")):
        _os.remove(stale)                     # a page that went quiet must not linger in dist/
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
