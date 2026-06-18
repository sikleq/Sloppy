"""Build terrain.html — per-patch terrain comparison (Materials tab).

A before/after **swipe slider** over each patch's old→new map renders, plus that
patch's "Terrain Changes" list. The patch picker (heading) switches panes.
Today two pairs ship: 7.41 (7.40→7.41) and 7.40 (7.39→7.40), each with the FULL
marker toolbar (Trees / Camps / point-entities) from its committed
``data/terrain_diff_<ver>.json``. See ``_MAP_PAIRS``.

Maps live in ``icons/maps/`` as ``map_<ver>.webp`` — all stitched from the
spectral courier tile server and cropped to ONE shared content box
(``scripts/gen/build_terrain_maps.py 7.39 7.40 7.41``) so every pair is pixel-aligned
and the swipe handle lines up exactly. The same shared crop meta
(``data/terrain_map_meta.json``) projects every patch's markers onto its own map.

The slider itself is driven by ``scripts.js`` (terrainCompareInit): the NEW
image is clipped with ``clip-path: inset(...)`` to ``--pos`` and a draggable
gold handle sets ``--pos`` (pointer + keyboard + click-to-position).

**Terrain change list — source of truth:** the 7.41 "Terrain Changes" section
in ``build_patch.py`` (search ``plain_header("Terrain Changes")``, ~line 13190).
Keep this list in sync when the live patch terrain section changes; it is a
small static list that only moves once per patch.

Run anytime (no manifest dependency). CI runs it after build_patch.py so the
nav's latest-patch href is fresh::

    python build_patch.py
    python build_terrain.py
"""
import html as _html
import json as _json
import os as _os
import sys as _sys

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _HERE)

import builders.site_common as _site
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


def _markers_svg(diff):
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

    old_t = tier_counts(diff.get("campsOld", []))
    new_t = tier_counts(diff.get("campsNew", []))
    counts = {
        "treesOld": len(diff.get("treesOld", [])),
        "treesNew": len(diff.get("treesNew", [])),
        "campsOld": old_t, "campsNew": new_t,
    }
    return (trees_old + trees_new + camps_old + camps_new
            + "".join(ent_svgs), counts)


def _latest_href():
    """Latest patch page href for the Changelogs nav tab (from site_meta.json)."""
    meta_path = _os.path.join(_HERE, "data", "site_meta.json")
    try:
        meta = _json.loads(open(meta_path, encoding="utf-8").read())
        return meta.get("latest_patch_filename", "patches/7.41c.html")
    except Exception:
        return "patches/7.41c.html"


# ---- terrain change list -----------------------------------------------------
# SOURCE OF TRUTH: the "Terrain Changes" sections in build_patch.py. Rather than
# duplicate them (and risk drift), we PARSE them straight out of build_patch.py
# at build time — one list per patch that has a terrain section. Today that's
# 7.41 (the moves that line up with our 7.40->7.41 map diff) and 7.40 (the big
# stream/Wisdom-Shrine/bridge rework). The patch picker shows every patch found.
#
# Patches we hold a matched OLD->NEW map pair for (so the swipe slider works);
# any other patch with terrain changes still lists its changes but shows a
# "comparison not available yet" fallback in place of the slider.
_MAP_PAIRS = {
    "7.41": ("7.40", "7.41"),   # icons/maps/map_7.40.webp + map_7.41.webp
    "7.40": ("7.39", "7.40"),   # icons/maps/map_7.39.webp + map_7.40.webp
}
# Marker overlays + tree/camp counts come from a committed per-patch diff
# (data/terrain_diff_<patch>.json). Any patch with one gets the full layer toolbar
# (Trees / Camps / point-entities); patches without a diff show the slider + Zoom
# only. The shared crop meta projects every patch's markers identically.


def _terrain_changes_by_patch():
    """Parse every ``plain_header("Terrain Changes")`` block out of
    build_patch.py → ``{version: [(text, TAG), ...]}`` in newest-first source
    order. Each block is a single ``ul_open()…ul_close()`` of ``W(li("text",
    …))`` rows; we read the row text + its tag (``t("TAG")`` or a ``b(...)``
    badge inferred BUFF/NERF). Falls back to an empty dict if the source can't
    be read so the page still builds."""
    import re, glob as _glob
    here = _HERE
    # Scan content/*.py (modular build) then fall back to build_patch.py (legacy).
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

    out = {}
    for hm in re.finditer(r'plain_header\("Terrain Changes"', src):
        i = hm.start()
        j = src.index("ul_close()", i)
        block = src[i:j]
        rows = []
        for seg in block.split("W(li(")[1:]:
            m = re.match(r'\s*"([^"]*)"', seg)
            if not m:
                continue
            text = m.group(1)
            rest = seg[m.end():m.end() + 300]
            tm = re.search(r't\("(\w+)"\)', rest)
            if tm:
                tag = tm.group(1)
            elif re.match(r"\s*,\s*b\(", rest):
                # Numeric badge → BUFF/NERF by direction, honouring l=True
                # (lower-is-better: cheaper mana cost = buff).
                lower_better = "l=True" in rest
                low = text.lower()
                if "decreased" in low or "reduced" in low:
                    good = lower_better
                else:                       # increased / default
                    good = not lower_better
                tag = "BUFF" if good else "NERF"
            else:
                tag = "MISC"
            rows.append((text, tag))
        if rows:
            # Collapse a patch letter (7.41c) to its base (7.41) — the terrain
            # block lives under the base patch's write_head.
            out.setdefault(patch_for(i), rows)
    return out


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


def _changes_html(changes):
    rows = sorted(
        enumerate(changes),
        key=lambda it: (_TAG_RANK.get(it[1][1], 9), it[0]),
    )
    return "\n".join(_change_li(text, tag) for _i, (text, tag) in rows)


def _controls_html(layers=True):
    """The control bar ABOVE the map (not overlaid, so it never covers the now
    edge-to-edge map): the Zoom mode button + every overlay-layer toggle (Trees,
    Camps, and the eight point-entity layers). Icon-only square buttons with
    tooltips + a colour dot matching each layer's map markers, wrapping as the
    width allows.

    layers=False  — only the Zoom button (no layer toggles). Used for map pairs
                    that ship no terrain_diff_<ver>.json (no marker data), so the
                    toggles would be dead buttons."""
    def layer_btn(key, label, icon, icon_dir="ui/gothic"):
        return (f'<button type="button" class="tc-btn tc-btn-icon tc-layer-btn" '
                f'data-layer="{key}" aria-pressed="false" '
                f'title="{_esc(label)}" aria-label="{_esc(label)}">'
                f'<img src="icons/{icon_dir}/{icon}.png" alt="" '
                f'width="16" height="16"></button>')
    parts = [
        # No long tooltip — the "Zoom" label already says what it is.
        '<button type="button" class="tc-btn tc-btn-zoom" aria-pressed="false">'
        '<img src="icons/ui/gothic/icon_loupe.png" alt="" width="15" height="15">'
        'Zoom</button>',
    ]
    if layers:
        parts.append('<span class="tc-sep" aria-hidden="true"></span>')
        parts.append(layer_btn("trees", "Trees", "tc_trees"))
        parts.append(layer_btn("camps", "Neutral Camps", "creepcamp_mid", icon_dir="camps"))
        for key, label, icon, _color in _ENTITY_LAYERS:
            parts.append(layer_btn(key, label, icon))
    return ('    <div class="tc-controls-bar">\n      '
            + "".join(parts) + '\n    </div>\n')


def _compare_html(old_ver, new_ver, markers_svg=""):
    """The before/after swipe stage + magnifier lens for an old→new map pair.

    Layers: top control bar | OLD map (base) | .tc-new-layer (NEW map, clipped
    to --pos) | tree/camp SVG (above maps, NOT slider-clipped) | drag handle |
    .tc-lens. The lens holds its own old/new map copies (scaled by data-zoom,
    positioned by scripts.js) reusing the SAME --pos clip; scripts.js also
    clones the marker SVG into it. Divider moves ONLY via the handle; in Loupe
    mode a plain click on the map pins/unpins the lens.

    markers_svg is non-empty when the patch ships a terrain_diff_<ver>.json; when
    empty, the layer-toggle buttons are dropped (Zoom stays)."""
    old_map = f"icons/maps/map_{old_ver}.webp"
    new_map = f"icons/maps/map_{new_ver}.webp"
    return (
        '<div class="terrain-compare" data-pos="50" data-zoom="1.9" data-lens="184">\n'
        f'{_controls_html(layers=bool(markers_svg))}'
        '  <div class="tc-stage">\n'
        f'    <img class="tc-img tc-old" src="{old_map}?v={ASSET_VERSION}" '
        f'width="1536" height="1536" alt="Dota 2 map terrain in patch {old_ver}" '
        f'draggable="false" loading="eager" fetchpriority="high">\n'
        '    <div class="tc-new-layer">\n'
        f'      <img class="tc-img tc-new" src="{new_map}?v={ASSET_VERSION}" '
        f'width="1536" height="1536" alt="Dota 2 map terrain in patch {new_ver}" '
        f'draggable="false" loading="eager">\n'
        '    </div>\n'
        f'    {markers_svg}\n'
        f'    <span class="tc-ver tc-ver-new">NEW &nbsp;{new_ver} →</span>\n'
        f'    <span class="tc-ver tc-ver-old">← {old_ver}&nbsp; OLD</span>\n'
        '    <div class="tc-handle" role="slider" tabindex="0" '
        f'aria-label="Reveal {old_ver} versus {new_ver} terrain" '
        'aria-valuemin="0" aria-valuemax="100" aria-valuenow="50">\n'
        '      <span class="tc-line" aria-hidden="true"></span>\n'
        '      <span class="tc-grip" aria-hidden="true">'
        '<span class="tc-chev tc-chev-l"></span>'
        '<span class="tc-chev tc-chev-r"></span></span>\n'
        '    </div>\n'
        '    <div class="tc-lens" aria-hidden="true">\n'
        f'      <img class="tc-lens-img tc-lens-old" src="{old_map}?v={ASSET_VERSION}" alt="" draggable="false">\n'
        f'      <img class="tc-lens-img tc-lens-new" src="{new_map}?v={ASSET_VERSION}" alt="" draggable="false">\n'
        '      <span class="tc-lens-rim" aria-hidden="true"></span>\n'
        '    </div>\n'
        '  </div>\n'
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


def _source_html():
    """Data-source credit shown under the slider — the map renders come from one
    leamare repo, the entity coordinates (tree/camp diff) from another."""
    def link(repo):
        return (f'<a href="https://github.com/leamare/{repo}" target="_blank" '
                f'rel="noopener noreferrer">leamare/{repo}</a>')
    return (
        '<p class="tc-source">Map renders from '
        f'{link("dota-interactive-map")}; entity coordinates from '
        f'{link("dota-map-coordinates")}.</p>\n'
    )


def _picker_html(patches, default):
    """Gold dropdown (calendar year-picker structure, gold `.tc-picker` skin)
    listing every patch that has terrain changes — newest first. It sits in the
    change-list heading AS the version (e.g. "[7.41 ▾] Terrain Changes");
    switching it swaps the visible map pane + change list (scripts.js
    initTerrainPicker)."""
    opts = []
    for ver in patches:
        sel = " is-selected" if ver == default else ""
        asel = "true" if ver == default else "false"
        opts.append(
            f'<li class="cal-year-opt{sel}" role="option" '
            f'data-patch="{ver}" aria-selected="{asel}">{ver}</li>')
    return (
        '<div class="cal-year-picker tc-picker">'
        '<button type="button" class="cal-year-current" '
        'aria-haspopup="listbox" aria-expanded="false">'
        f'<span class="cal-year-current-val">{default}</span>'
        '<span class="cal-year-caret" aria-hidden="true">▾</span>'
        '</button>'
        '<ul class="cal-year-menu" role="listbox" hidden>'
        + "".join(opts) +
        '</ul>'
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


def save_terrain_html():
    nav = _site.render_top_nav('materials', _latest_href(),
                               patch_context=False, subtabs_active='terrain',
                               subnav_in_header=False)
    subnav = _site.render_materials_subnav('terrain')

    by_patch = _terrain_changes_by_patch()
    # Sort newest-first by version tuple so default is always the latest patch.
    def _ver_key(v):
        parts = v.split(".")
        return tuple(int(x) if x.isdigit() else x for x in parts)
    patches = sorted(by_patch.keys(), key=_ver_key, reverse=True)
    if not patches:                       # parser failed → degrade gracefully
        patches = sorted(_MAP_PAIRS, key=_ver_key, reverse=True) or ["7.41"]
        by_patch = {p: [] for p in patches}
    default = patches[0]

    # ---- per-patch marker overlays + tree/camp counts: every patch that ships a
    # committed terrain_diff_<ver>.json gets the full layer toolbar; the shared
    # crop meta projects each patch's markers onto its own map identically. ----
    markers_by_patch, counts_by_patch = {}, {}
    if SHOW_MARKERS:
        for ver in _MAP_PAIRS:
            diff = _load_diff(ver)
            if diff:
                markers_by_patch[ver], counts_by_patch[ver] = _markers_svg(diff)

    # ---- map panes (one per patch): the swipe slider where we have a map pair,
    # the "not available yet" fallback otherwise. ----
    map_panes = []
    for ver in patches:
        hidden = "" if ver == default else " hidden"
        if ver in _MAP_PAIRS:
            ov, nv = _MAP_PAIRS[ver]
            inner = _compare_html(ov, nv, markers_by_patch.get(ver, ""))
        else:
            inner = _fallback_html(ver)
        map_panes.append(
            f'<div class="terrain-map-pane" data-patch="{ver}"{hidden}>\n'
            f'{inner}</div>\n')

    # ---- change-list panes (one per patch): list + counts (counts only for the
    # patch whose map diff we have). The single heading (with the patch picker)
    # sits above all panes. ----
    list_panes = []
    for ver in patches:
        hidden = "" if ver == default else " hidden"
        counts_html = _counts_html(counts_by_patch.get(ver, {}))
        list_panes.append(
            f'<div class="terrain-list-pane" data-patch="{ver}"{hidden}>\n'
            f'<ul class="changes terrain-list">\n{_changes_html(by_patch[ver])}\n</ul>\n'
            f'{counts_html}'
            '</div>\n')
    # Heading = the picker AS the version + "Terrain Changes" label. (A <div>,
    # not <h2> — it holds interactive controls, which can't live inside a heading.)
    list_head = (
        '<div class="terrain-list-head">'
        f'{_picker_html(patches, default)}'
        '<span class="terrain-list-head-label">Terrain Changes</span>'
        '</div>\n')

    page = (
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
        '<p class="mr-blurb inbox-bar">Drag the <strong>handle</strong> to wipe between '
        'the old and new map. Turn on '
        '<img class="tc-inline-loupe" src="icons/ui/gothic/icon_loupe.png" alt="" '
        'width="16" height="16"><strong>Zoom</strong> (above the map) to magnify on hover — '
        '<strong>click</strong> pins a spot so you can sweep the handle and compare it '
        'across versions. The toggle buttons above the map overlay objects — '
        '<strong>Trees</strong>, <strong>Camps</strong>, towers, runes, lotus pools, '
        'gates, tormentors, shrines, outposts, watchers and Roshan — each split old/new by the slider, so '
        'sweeping shows what moved. Pick a <strong>patch</strong> from the heading on the '
        'right.</p>\n'
        '<div class="terrain-wrap">\n'
        '<div class="terrain-compare-col">\n'
        f'{"".join(map_panes)}'
        f'{_source_html()}'
        '</div>\n'
        '<div class="terrain-list-box">\n'
        f'{list_head}'
        f'{"".join(list_panes)}'
        '</div>\n'
        '</div>\n'
        '</div>\n'   # close .creeps-scroll
        '</div>\n'   # close .creeps-page
        f'<script src="src/scripts.js?v={ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n'
    )
    _os.makedirs(_site.DIST_DIR, exist_ok=True)
    out = _os.path.join(_site.DIST_DIR, "terrain.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    total = sum(len(v) for v in by_patch.values())
    print(f"  -> dist/terrain.html: {len(page):,} bytes "
          f"({len(patches)} patches, {total} terrain changes; "
          f"default {default})")


if __name__ == "__main__":
    save_terrain_html()
