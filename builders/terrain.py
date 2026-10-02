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

    boxes_old = "".join(_box_poly(box, "tc-sb-old")
                        for box in diff.get("spawnboxesOld", []))
    boxes_new = "".join(_box_poly(box, "tc-sb-new")
                        for box in diff.get("spawnboxesNew", []))

    sb_svg = (
        f'<svg class="tc-markers tm-layer tm-layer-spawnboxes" '
        f'viewBox="0 0 {MAP_VB} {MAP_VB}" preserveAspectRatio="none" '
        f'aria-hidden="true">{boxes_old}{boxes_new}</svg>'
    )

    old_t = tier_counts(diff.get("campsOld", []))
    new_t = tier_counts(diff.get("campsNew", []))
    counts = {
        "treesOld": len(diff.get("treesOld", [])),
        "treesNew": len(diff.get("treesNew", [])),
        "campsOld": old_t, "campsNew": new_t,
    }
    return (trees_old + trees_new + camps_old + camps_new
            + "".join(ent_svgs) + sb_svg, counts)


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


def _terrain_notes_by_patch():
    """Parse every ``plain_header("Terrain Changes")`` block from content/*.py
    (and 7.38's "Wandering Waters" / "Other Terrain Changes").

    Returns ``{patch: [(text, TAG, subgroup), ...]}`` — each patch's own notes
    (its page shows only them; subgroup may be None).
    """
    import re, glob as _glob
    here = _HERE
    content_files = sorted(_glob.glob(_os.path.join(here, "content", "*.py")))
    if not content_files:
        content_files = [_os.path.join(here, "build_patch.py")]
    src_parts = []
    for p in content_files:
        try:
            src_parts.append(open(p, encoding="utf-8").read())
        except OSError:
            pass
    if not src_parts:
        return {}
    src = "\n".join(src_parts)
    heads = [(m.start(), m.group(1))
             for m in re.finditer(r'write_head\("([^"]+)"', src)]

    def patch_for(off):
        prev = [h for h in heads if h[0] < off]
        return prev[-1][1] if prev else "?"

    # raw: {patch_ver: [(text, tag, subgroup), ...]}
    # 7.38 put its map notes under "Wandering Waters" (the new streams) and "Other
    # Terrain Changes"; those blocks count too, each under its own title.
    raw = {}
    for hm in re.finditer(r'plain_header\("((?:Other )?Terrain Changes|Wandering Waters)"', src):
        i = hm.start()
        # Find end of terrain section: next plain_header, section(), or write_footer
        end_m = re.search(r'(?:plain_header|section|write_footer)\(', src[i + 1:])
        j = (i + 1 + end_m.start()) if end_m else len(src)
        block = src[i:j]
        rows = []
        cur_subgroup = None if hm.group(1) == "Terrain Changes" else hm.group(1)
        for line in block.split("\n"):
            sg = re.search(r'subgroup\("([^"]+)"\)', line)
            if sg:
                cur_subgroup = sg.group(1)
                continue
            li_m = re.search(r'W\(li\(\s*"([^"]*)"', line)
            if not li_m:
                continue
            text = li_m.group(1)
            rest = line[li_m.end():li_m.end() + 300]
            tm = re.search(r't\("(\w+)"\)', rest)
            if tm:
                tag = tm.group(1)
            elif re.match(r"\s*,\s*b\(", rest):
                lower_better = "l=True" in rest
                low = text.lower()
                good = lower_better if ("decreased" in low or "reduced" in low) else not lower_better
                tag = "BUFF" if good else "NERF"
            else:
                tag = "MISC"
            rows.append((text, tag, cur_subgroup))
        if rows:
            raw.setdefault(patch_for(i), []).extend(rows)
    return raw


# What moved in the map file, per point-entity layer of the diff (plural nouns).
_MOVED_NAMES = {"towers": "towers", "lotus": "lotus pools", "twinGates": "twin gates",
                "tormentors": "Tormentors", "bounty": "bounty runes", "power": "power runes",
                "wisdom": "wisdom shrines", "wisdomRunes": "wisdom runes", "outposts": "outposts",
                "watchers": "watchers", "roshan": "Roshan pits"}


def _moved_summary(diff):
    """What moved between the step's two map files, read off its diff — e.g.
    ["trees +38 −27", "camps moved: 2", "towers moved: 1"]; [] when nothing did.
    A layer whose count changed reads "+added −removed", one that kept its count
    "moved: n" (the Oldgrowth table says the same)."""
    if not diff:
        return []

    def delta(old, new, name):
        a, b = {tuple(p) for p in old}, {tuple(p) for p in new}
        added, removed = len(b - a), len(a - b)
        if not added and not removed:
            return None
        if len(old) == len(new):
            return f"{name} moved: {added}"
        return f"{name} +{added} −{removed}"

    out = [delta(diff.get("treesOld", []), diff.get("treesNew", []), "trees")]
    out.append(delta([(c["x"], c["y"]) for c in diff.get("campsOld", [])],
                     [(c["x"], c["y"]) for c in diff.get("campsNew", [])], "camps"))
    old_tier = {(c["x"], c["y"]): c.get("tier") for c in diff.get("campsOld", [])}
    retiered = sum(1 for c in diff.get("campsNew", [])
                   if (c["x"], c["y"]) in old_tier and old_tier[(c["x"], c["y"])] != c.get("tier"))
    if retiered:
        out.append(f"camp tiers changed: {retiered}")
    for key, name in _MOVED_NAMES.items():
        ed = diff.get("entities", {}).get(key)
        if ed:
            out.append(delta(ed.get("old", []), ed.get("new", []), name))
    return [s for s in out if s]


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


def _change_li(text, tag):
    _cls, tid, overall = _TAG_CLS[tag]
    # data-tag carries the primary tag plus its filter-overall (NEW→buff,
    # DEL→nerf) so a future filter surfaces them correctly; dedupe so BUFF/NERF
    # (whose tid already equals the overall) don't repeat.
    tags = [tid]
    if 'data-overall="buff"' in overall and "buff" not in tags:
        tags.append("buff")
    elif 'data-overall="nerf"' in overall and "nerf" not in tags:
        tags.append("nerf")
    return (f'<li data-tag="{" ".join(tags)}">{_badge(tag)}'
            f'<span class="row-text">{text}</span></li>')


def _changes_html(subpatches, skip_first_head=False):
    """Render change list for one major-version bucket.

    subpatches: [(sub_ver, [(text, tag, subgroup), ...]), ...]  oldest-first.
    Rows are 3-tuples (text, tag, subgroup) where subgroup may be None.
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
            groups.setdefault(sg, []).append((i, text, tag))
        for sg, sg_rows in groups.items():
            if sg:
                parts.append(f'<li class="terrain-subgroup-head">{sg}</li>')
            sorted_rows = sorted(sg_rows,
                                 key=lambda it: (_TAG_RANK.get(it[2], 9), it[0]))
            parts.extend(_change_li(text, tag) for _, text, tag in sorted_rows)
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
        for key, label, icon, _color in _ENTITY_LAYERS:
            layer_parts.append(layer_btn(key, label, icon))

    # Top bar: Zoom + Fullscreen + layer toggles
    top_parts = [
        '<button type="button" class="tc-btn tc-btn-zoom" aria-pressed="false">'
        '<img src="icons/ui/gothic/icon_loupe.png" alt="" width="15" height="15">'
        'Zoom</button>',
        f'<button type="button" class="tc-btn tc-btn-fs" aria-pressed="false" '
        f'aria-label="Fullscreen" title="Fullscreen">'
        f'{_FS_ENTER_ICON}Fullscreen</button>',
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


def _counts_html(counts):
    """Two lines under the change list: tree count old→new (net delta), and the
    neutral-camp roster by tier with the change vs the old patch."""
    if not counts:
        return ""
    o = counts.get("treesOld", 0)
    n = counts.get("treesNew", 0)
    d = n - o
    tree_delta_cls = "tm-add-text" if d >= 0 else "tm-rem-text"

    old_t = counts.get("campsOld", {})
    new_t = counts.get("campsNew", {})

    def camp_part(tier, label):
        cur = new_t.get(tier, new_t.get(str(tier), 0))
        delta = cur - old_t.get(tier, old_t.get(str(tier), 0))
        if delta:
            cls = "tm-add-text" if delta > 0 else "tm-rem-text"
            return f'{cur} {label} (<span class="{cls}">{delta:+d}</span>)'
        return f'{cur} {label}'

    camps_str = ", ".join([
        camp_part(3, "ancients"), camp_part(2, "large"),
        camp_part(1, "medium"), camp_part(0, "small"),
    ])
    return (
        '<p class="terrain-counts"><b>Trees:</b> '
        f'{n} (<span class="{tree_delta_cls}">{d:+d}</span>)</p>\n'
        f'<p class="terrain-counts"><b>Neutral camps:</b> {camps_str}</p>\n'
    )


def _map_file_html(step, diff, quiet_after=()):
    """Under the counts: what moved in the map file since the patch before (read
    off the diff, so a patch Valve's notes say nothing about still shows its
    changes), and the patches after it that changed nothing on the map (they get
    no page — the owner 2026-10-02: "if nothing changed, there's nothing to
    compare")."""
    out = ""
    if step is not None:
        moved = _moved_summary(diff)
        out = ('<p class="terrain-counts terrain-moved"><b>Moved in the map file:</b> '
               f'{_esc(", ".join(moved)) if moved else "nothing"}</p>\n')
    if quiet_after:
        run = quiet_after[0] if len(quiet_after) == 1 else f"{quiet_after[0]} – {quiet_after[-1]}"
        out += (f'<p class="terrain-counts terrain-quiet">{_esc(run)} changed nothing on the '
                'map.</p>\n')
    return out


def _quiet(steps, notes, diffs):
    """Steps whose notes list nothing and whose map file moved nothing — no page.
    Their pictures differ from the patch before only by render noise (checked
    2026-10-02 with scripts/gen/map_picture_diff.py: no change bigger than the
    wind in the trees), so there is nothing to compare."""
    return {p for p in steps if not notes.get(p) and not _moved_summary(diffs.get(p))}


def _quiet_runs(pages, patch_maps, quiet):
    """{page: [the patches right after it that changed nothing on the map]} — the
    quiet steps and the patches that shipped the very same map file, up to the
    next page (or the first patch that changed something we hold no page for)."""
    order = list(patch_maps)
    out = {}
    for ver in pages:
        if ver not in patch_maps:
            continue
        run = []
        for i in range(order.index(ver) + 1, len(order)):
            p = order[i]
            same = patch_maps[p] == patch_maps[order[i - 1]]
            if p in pages or not (same or p in quiet):
                break
            run.append(p)
        out[ver] = run
    return out


def _no_notes_html():
    """The change list of a patch whose notes list no terrain changes."""
    return ('<li class="terrain-no-notes"><span class="row-text">The patch notes list no terrain '
            'changes.</span></li>')


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


def _build_terrain_page(ver, patches, notes, step, diff, subnav, quiet_after=()):
    """Build one terrain HTML page: patch ``ver``'s map file against the patch
    before's (``step``, None when there's no pair → fallback), its own notes
    (``notes`` = {patch: rows}), what moved (``diff``) and the patches after it
    that changed nothing (``quiet_after``)."""
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

    counts_html = _counts_html(counts) + _map_file_html(step, diff, quiet_after)
    rows = notes.get(ver)
    list_html = _changes_html([(ver, rows)], skip_first_head=True) if rows else _no_notes_html()
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
    runs = _quiet_runs(patches, _map_versions.load_patch_maps(), quiet)

    _os.makedirs(_site.DIST_DIR, exist_ok=True)
    for stale in _glob.glob(_os.path.join(_site.DIST_DIR, "terrain_*.html")):
        _os.remove(stale)                     # a page that went quiet must not linger in dist/
    total = sum(len(rows) for rows in notes.values())
    for ver in patches:
        page = _build_terrain_page(ver, patches, notes, steps.get(ver), diffs.get(ver), subnav,
                                   runs.get(ver, ()))
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
