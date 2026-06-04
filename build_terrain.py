"""Build terrain.html — the 7.40 → 7.41 terrain comparison (Materials tab).

A before/after **swipe slider** over the two map renders, plus the 7.41
"Terrain Changes" list beside/below it.

Maps live in ``icons/maps/``:
  - ``map_7.40.webp`` / ``map_7.41.webp`` — the Valve map exports cropped
    identically to the (384,384)-(1664,1664) playable box (1280×1280) so the
    two images are pixel-aligned; the swipe handle lines up exactly. Built once
    from the user's downloads (``map (1).png`` = 7.40, ``map.png`` = 7.41).

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

import site_common as _site

_HERE = _os.path.dirname(_os.path.abspath(__file__))
ASSET_VERSION = _site.compute_asset_version()

OLD_VER = "7.40"
NEW_VER = "7.41"
OLD_MAP = f"icons/maps/map_{OLD_VER}.webp"
NEW_MAP = f"icons/maps/map_{NEW_VER}.webp"

# Tree-change dots (added / removed) are the ONLY map markers — each is a
# toggleable layer (off by default; the toolbar checkboxes reveal them). The
# moved objects (Lotus/Tormentor/Twin Gate/camps/towers) are NOT marked: you
# read those off the change list and SEE them move by sweeping the slider under
# the magnifier lens. (The camp/tower/etc diff data is still computed and kept
# in terrain_diff.json for future use.)
SHOW_MARKERS = True

# SVG marker overlay is drawn in this square viewBox; world coords project into
# it via the leamare worlddata bounds (stored in terrain_diff.json). 1280 ==
# the cropped map's native pixel size, so trees land exactly on the forest.
MAP_VB = 1280


def _esc(s):
    return _html.escape(str(s), quote=True)


def _load_diff():
    """The committed 7.40->7.41 terrain diff (scripts/build_terrain_diff.py).
    Returns None if absent so the page still builds (maps only, no markers)."""
    path = _os.path.join(_HERE, "data", "terrain_diff.json")
    try:
        with open(path, encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return None


def _load_map_meta():
    """Projection meta written by scripts/build_terrain_maps.py — the leamare
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
    camps_old = camp_layer("tc-camps-old", diff.get("camps40", []))
    camps_new = camp_layer("tc-camps-new", diff.get("camps41", []))

    old_t = tier_counts(diff.get("camps40", []))
    new_t = tier_counts(diff.get("camps41", []))
    counts = {
        "treesOld": len(diff.get("treesOld", [])),
        "treesNew": len(diff.get("treesNew", [])),
        "campsOld": old_t, "campsNew": new_t,
    }
    return trees_old + trees_new + camps_old + camps_new, counts


def _latest_href():
    """Latest patch page href for the Changelogs nav tab (from site_meta.json)."""
    meta_path = _os.path.join(_HERE, "data", "site_meta.json")
    try:
        meta = _json.loads(open(meta_path, encoding="utf-8").read())
        return meta.get("latest_patch_filename", "patches/7.41c.html")
    except Exception:
        return "patches/7.41c.html"


# ---- terrain change list -----------------------------------------------------
# SOURCE OF TRUTH: build_patch.py 7.41 "Terrain Changes" section (search
# write_head("7.41") then plain_header("Terrain Changes"), ~line 6416). These
# are the changes introduced IN 7.41 (the 7.40 map rework is a DIFFERENT, much
# larger list — do not use it here). They line up with the leamare 7.40->7.41
# data diff: tormentor/lotus/twin-gate moves, camp demotions+moves, tower
# nudges, tree removals. (text, TAG); sorted by canonical tag order on render.
# TODO(terrain): when the patch picker lands, make this per-patch instead of a
# single hardcoded list (see docs/terrain.md).
_TERRAIN_CHANGES = [
    ("Tormentor spawns have been positioned closer towards Lotus Pools", "MISC"),
    ("Tormentor spawn areas have been reduced to low ground relative to the lane's level", "MISC"),
    ("Lotus Pools have been moved slightly closer to their respective offlane tower", "MISC"),
    ("Twin Gates slightly moved away from the stairs towards the map border", "MISC"),
    ("The watcher between the safe lane tier 1 tower and the tormentor has been repositioned", "MISC"),
    ("Ancient neutral camps near stream ends demoted to medium camps and moved slightly towards bases", "NERF"),
    ("Medium neutral camp near offlane defender's gate has been demoted to a small neutral camp", "NERF"),
    ("The tier 1 safe lane towers have been moved slightly away from their pull camps and where the creeps meet", "BUFF"),
    ("Radiant safe lane small camp has been slightly moved north away from the lane", "MISC"),
    ("Radiant safe lane hard camp's spawn box has been moved towards the offlane to remove a bad ward location", "MISC"),
    ("Radiant offlane tier 2 tower has been adjusted slightly to the left, such that creeps do not path on both sides of the tower", "BUFF"),
    ("The ramp leading from the Radiant tier 1 tower to the stream has been decreased in width and moved away from the tower", "NERF"),
    ("The medium flooded camp near the safe lane tier 2 towers moved closer to the middle of the stream (substantially more for Dire than for Radiant)", "MISC"),
    ("The medium flooded camp near the safe lane tier 2 towers can now only evolve once into a hard camp, rather than into an Ancient Camp", "NERF"),
    ("The medium flooded camp near the bounty runes can now evolve twice into an Ancient Camp", "REWORK"),
    ("Removed several trees from Dire Safelane easy pull camp and Radiant Safelane hard pull camp", "MISC"),
]

# Canonical tag order (same as the site convention): NEW → REWORK → BUFF →
# NERF → DEL → MISC/QoL. Stable within a rank.
_TAG_RANK = {"NEW": 1, "REWORK": 2, "BUFF": 3, "NERF": 4, "DEL": 5,
             "MISC": 6, "QoL": 6}
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


def _changes_html():
    rows = sorted(
        enumerate(_TERRAIN_CHANGES),
        key=lambda it: (_TAG_RANK.get(it[1][1], 9), it[0]),
    )
    return "\n".join(_change_li(text, tag) for _i, (text, tag) in rows)


def _topbar_html():
    """The control strip overlaid on the map's top edge (non-playable space):
    the Zoom / Trees / Camps toggle buttons, with the NEW version label pinned
    to the right. (The OLD label sits in the bottom-left map corner instead.)"""
    def btn(cls, icon, label, title):
        return (f'        <button type="button" class="tc-btn {cls}" '
                f'aria-pressed="false" title="{_esc(title)}">'
                f'<img src="{icon}" alt="" width="15" height="15">{label}</button>\n')
    return (
        '    <div class="tc-topbar">\n'
        '      <span class="tc-controls">\n'
        + btn("tc-btn-zoom", "icons/ui/gothic/icon_loupe.png", "Zoom",
              "Magnifier: hover to zoom, click to pin a spot, then sweep the "
              "handle to compare it across versions")
        + btn("tc-btn-trees", "icons/ui/gothic/icon_tree.png", "Trees",
              "Show the tree layout — 7.40 on the old side, 7.41 on the new "
              "side; sweep the handle to see the forest move")
        + btn("tc-btn-camps", "icons/camps/creepcamp_mid.png", "Camps",
              "Show neutral camps by tier (small / medium / large / ancient); "
              "camps whose tier changed are ringed")
        + '      </span>\n'
        f'      <span class="tc-ver tc-ver-new">{NEW_VER}</span>\n'
        '    </div>\n'
    )


def _compare_html(markers_svg=""):
    """The before/after swipe stage + magnifier lens.

    Layers: top control bar | OLD map (base) | .tc-new-layer (NEW map, clipped
    to --pos) | tree/camp SVG (above maps, NOT slider-clipped) | drag handle |
    .tc-lens. The lens holds its own old/new map copies (scaled by data-zoom,
    positioned by scripts.js) reusing the SAME --pos clip; scripts.js also
    clones the marker SVG into it. Divider moves ONLY via the handle; in Loupe
    mode a plain click on the map pins/unpins the lens."""
    return (
        '<div class="terrain-compare" data-pos="50" data-zoom="1.9" data-lens="184">\n'
        '  <div class="tc-stage">\n'
        f'    <img class="tc-img tc-old" src="{OLD_MAP}?v={ASSET_VERSION}" '
        f'width="1536" height="1536" alt="Dota 2 map terrain in patch {OLD_VER}" '
        f'draggable="false" loading="eager" fetchpriority="high">\n'
        '    <div class="tc-new-layer">\n'
        f'      <img class="tc-img tc-new" src="{NEW_MAP}?v={ASSET_VERSION}" '
        f'width="1536" height="1536" alt="Dota 2 map terrain in patch {NEW_VER}" '
        f'draggable="false" loading="eager">\n'
        '    </div>\n'
        f'    {markers_svg}\n'
        f'{_topbar_html()}'
        f'    <span class="tc-ver tc-ver-old">{OLD_VER}</span>\n'
        '    <div class="tc-handle" role="slider" tabindex="0" '
        f'aria-label="Reveal {OLD_VER} versus {NEW_VER} terrain" '
        'aria-valuemin="0" aria-valuemax="100" aria-valuenow="50">\n'
        '      <span class="tc-line" aria-hidden="true"></span>\n'
        '      <span class="tc-grip" aria-hidden="true">'
        '<span class="tc-chev tc-chev-l"></span>'
        '<span class="tc-chev tc-chev-r"></span></span>\n'
        '    </div>\n'
        '    <div class="tc-lens" aria-hidden="true">\n'
        f'      <img class="tc-lens-img tc-lens-old" src="{OLD_MAP}?v={ASSET_VERSION}" alt="" draggable="false">\n'
        f'      <img class="tc-lens-img tc-lens-new" src="{NEW_MAP}?v={ASSET_VERSION}" alt="" draggable="false">\n'
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
    """Data-source credit shown under the slider — where the map renders and the
    entity coordinates (used for the tree diff) come from."""
    return (
        '<p class="tc-source">Map renders &amp; entity coordinates from '
        '<a href="https://github.com/leamare/dota-interactive-map" target="_blank" '
        'rel="noopener noreferrer">leamare/dota-interactive-map</a>.</p>\n'
    )


def save_terrain_html():
    nav = _site.render_top_nav('materials', _latest_href(),
                               patch_context=False, subtabs_active='terrain',
                               subnav_in_header=False)
    subnav = _site.render_materials_subnav('terrain')
    markers_svg, counts = _markers_svg(_load_diff()) if SHOW_MARKERS else ("", {})

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
        'width="16" height="16"><strong>Zoom</strong> (top bar) to magnify on hover — '
        '<strong>click</strong> pins a spot so you can sweep the handle and compare it '
        'across versions. <strong>Trees</strong> overlays the forest layout for both '
        'patches (sweep to see it shift); <strong>Camps</strong> shows the neutral camps '
        'by tier. Full change list on the right.</p>\n'
        '<div class="terrain-wrap">\n'
        '<div class="terrain-compare-col">\n'
        f'{_compare_html(markers_svg)}'
        f'{_source_html()}'
        '</div>\n'
        '<div class="terrain-list-box">\n'
        f'<h2 class="terrain-list-head">{NEW_VER} Terrain Changes</h2>\n'
        f'<ul class="changes terrain-list">\n{_changes_html()}\n</ul>\n'
        f'{_counts_html(counts)}'
        '</div>\n'
        '</div>\n'
        '</div>\n'   # close .creeps-scroll
        '</div>\n'   # close .creeps-page
        f'<script src="scripts.js?v={ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n'
    )
    out = _os.path.join(_HERE, "terrain.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"  -> terrain.html: {len(page):,} bytes "
          f"({len(_TERRAIN_CHANGES)} terrain changes, {OLD_VER}->{NEW_VER})")


if __name__ == "__main__":
    save_terrain_html()
