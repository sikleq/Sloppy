"""Shared renderer for the Dynamics matrix pages (heroes_dyn / items_dyn).

A matrix table: ROWS = every entity (icon + name, alphabetical), COLUMNS = every
patch (version + release date), each CELL = that entity's patch-dynamics
"dyn-cell" for that patch (the same diamond-pill widget used on patch pages).

`save_dyn_matrix(...)` is entity-agnostic — `build_heroes_dyn.py` calls it with
the hero config, `build_items_dyn.py` with the item config. Everything below
(super-category row, group dividers, sticky identity column, fit-to-width, the
spacer gutter column, the Remove chips + search toolbar) is identical for both;
only the roster, icon directory, column noun, eid prefix and the back-arrow
`from` token differ.

The coloured pills + tooltips are built client-side by scripts.js (dynBuildMatrix),
which reuses the exact dyn-cell rendering of the patch pages — so this builder
only emits the table skeleton: marked data cells (entity changed that patch) and
static empty diamonds (everything else). The same `.heroes-dyn-table` class is
reused for BOTH pages so the shared CSS + JS apply unchanged.

Data: `_dynamics.json` (written by build_patch.py) —
  - `patches`  : ordered newest-first list of {version, filename, date}
  - `entities` : per-entity tag tallies, keyed "<kind>|<slug>"
  - `heroes` / `items` : full alphabetical roster [{name, icon, key}]
"""
import html as _html
import json as _json
import os as _os
import re as _re

import site_common as _site

_HERE = _os.path.dirname(_os.path.abspath(__file__))


def _esc(s):
    return _html.escape(str(s), quote=True)


def _base_version(ver):
    """Strip a trailing letter suffix: 7.41c → 7.41, 7.39e → 7.39, 7.08 → 7.08."""
    return _re.sub(r"[a-z]+$", "", ver)


def _latest_href():
    """Latest patch page href for the Changelogs nav tab (from site_meta.json)."""
    meta_path = _os.path.join(_HERE, "data", "site_meta.json")
    try:
        meta = _json.loads(open(meta_path, encoding="utf-8").read())
        return meta.get("latest_patch_filename", "patches/7.41c.html")
    except Exception:
        return "patches/7.41c.html"


def _load_manifest():
    with open(_os.path.join(_HERE, "_dynamics.json"), encoding="utf-8") as f:
        return _json.load(f)


def _roster(manifest, roster_key, kind):
    """Full alphabetical roster as [{name, icon, key}]. Prefer the explicit
    roster build_patch.py writes (manifest[roster_key]); fall back to deriving it
    from the entities of this kind if an older _dynamics.json is in place."""
    roster = manifest.get(roster_key)
    if roster:
        return sorted(roster, key=lambda h: h["name"].lower())
    derived = []
    for key, rec in manifest.get("entities", {}).items():
        if rec.get("kind") != kind:
            continue
        name = rec.get("name", key.split("|", 1)[-1])
        icon = rec.get("icon", name.lower().replace(" ", "_")
                        .replace("'", "").replace("-", ""))
        derived.append({"name": name, "icon": icon, "key": key})
    return sorted(derived, key=lambda h: h["name"].lower())


def save_dyn_matrix(*, kind, roster_key, out_file, page_title, subtab, noun,
                    icon_dir, from_token, search_ph, blurb,
                    current_toggle=False, class_filter=False, price_filter=False):
    """Render a Dynamics matrix page. See module docstring for the params.

    current_toggle — add an "In game" switch (left of Buff/nerf only) that hides
                     rows whose roster entry has current=False (removed/obsolete).
                     Default ON. Needs roster entries to carry `current`.
    class_filter   — add a Show group (right of Remove) with Items / Neutral Items
                     / Enchantments toggles. Needs roster entries to carry `class`.
    Both are no-ops on pages whose roster lacks those fields (heroes_dyn)."""
    manifest = _load_manifest()
    # Columns: every patch, OLDEST on the left → NEWEST on the right (so the
    # latest patch is the rightmost column; scripts.js keeps it flush right).
    patches = list(reversed(manifest.get("patches", [])))
    entities = manifest.get("entities", {})
    rows_data = _roster(manifest, roster_key, kind)

    nav = _site.render_top_nav('materials', _latest_href(),
                               patch_context=False, subtabs_active=subtab,
                               subnav_in_header=False)
    subnav = _site.render_materials_subnav(subtab)

    # ---- super-category row: base version spanning its lettered variants ----
    # Patches are oldest→newest, so variants of one base (7.41, 7.41a, 7.41b,
    # 7.41c) are consecutive. A base with >1 patch gets a spanning header
    # labelled with the bare version; a base with a single patch gets an empty
    # cell. scripts.js dynLayoutMatrix recomputes the colspans to the VISIBLE
    # columns after the fit-to-width hide.
    groups = []                      # [(base, [patch, ...]), ...] in column order
    for p in patches:
        b = _base_version(p["version"])
        if groups and groups[-1][0] == b:
            groups[-1][1].append(p)
        else:
            groups.append((b, [p]))
    # First patch version of each base group EXCEPT the first → full-height
    # vertical divider on its left (separates super-categories).
    gsep_vers = {ps[0]["version"] for gi, (base, ps) in enumerate(groups) if gi > 0}
    supercat_cells = [
        # sits over the frozen identity column (sticky, empty, carries the divider)
        '<th class="cat-head hd-hero-cat sticky-col" aria-hidden="true"></th>'
    ]
    for base, ps in groups:
        if len(ps) > 1:
            supercat_cells.append(
                f'<th class="cat-head hd-supercat" colspan="{len(ps)}" '
                f'data-base="{_esc(base)}">{_esc(base)}</th>')
        else:
            supercat_cells.append(
                f'<th class="cat-head hd-supercat hd-supercat-solo" '
                f'data-base="{_esc(base)}" aria-hidden="true"></th>')
    # Trailing spacer column (fills the right hover-pop gutter).
    supercat_cells.append('<th class="cat-head hd-spacer" aria-hidden="true"></th>')
    supercat_html = "".join(supercat_cells)

    # ---- column row: <noun> | <version> per patch (release date on hover) ----
    head_cells = [f'<th class="hd-hero sortable sticky-col" data-col="name" '
                  f'data-idx="0">{_esc(noun)}<span class="sort-ind"></span></th>']
    for p in patches:
        sep = ' hd-gsep' if p["version"] in gsep_vers else ''
        head_cells.append(
            f'<th class="hd-patch{sep}" tabindex="0" '
            f'data-base="{_esc(_base_version(p["version"]))}" '
            f'data-tooltip="{_esc(p["date"])}">{_esc(p["version"])}</th>')
    head_cells.append('<th class="hd-spacer" aria-hidden="true"></th>')
    head_html = "".join(head_cells)

    # Chronological column index (patches is oldest-first) for lifespan blanking.
    ver_index = {p["version"]: i for i, p in enumerate(patches)}

    # ---- body: one row per entity ----
    rows = []
    for h in rows_data:
        key = h["key"]
        slug = key.split("|", 1)[-1]
        eid = f"dyn-{kind}-{slug}"
        per_patch = (entities.get(key, {}) or {}).get("patches", {})
        # Lifespan window (items_dyn only; absent on heroes_dyn → spans everything):
        # blank columns BEFORE the item entered the game, and AFTER it was removed.
        added = h.get("added")
        removed = h.get("removed")
        a_idx = ver_index.get(added, 0) if added else 0
        r_idx = ver_index.get(removed) if removed else None
        img = (f'<img src="{_esc(icon_dir)}/{_esc(h["icon"])}.png" '
               f'alt="{_esc(h["name"])}" loading="lazy">')
        cells = [
            f'<td class="hd-hero sticky-col" data-col="name" '
            f'data-sort="{_esc(h["name"])}">'
            f'<span class="hd-hero-inner">{img}'
            f'<span class="hd-hero-name">{_esc(h["name"])}</span></span></td>'
        ]
        for i, p in enumerate(patches):
            ver = p["version"]
            sep = ' hd-gsep' if ver in gsep_vers else ''
            counts = per_patch.get(ver)
            absent = (added and i < a_idx) or (r_idx is not None and i > r_idx)
            if counts:
                # Touched this patch → JS fills a coloured pill (always wins, even
                # if the lifespan math would blank it — a touch means it existed).
                cells.append(
                    f'<td class="hd-cell{sep}" data-ver="{_esc(ver)}" '
                    f'data-hkey="{_esc(key)}" data-eid="{_esc(eid)}"></td>')
            elif absent:
                # Outside the item's lifespan (not added yet / already removed) →
                # faint "n/a" dot, NOT the empty-slot square.
                cells.append(f'<td class="hd-cell hd-absent{sep}"></td>')
            else:
                # Existed but untouched → static empty diamond (CSS ::after).
                cells.append(f'<td class="hd-cell hd-empty{sep}"></td>')
        cells.append('<td class="hd-cell hd-empty hd-spacer"></td>')
        # Row metadata for the items_dyn filters (absent on heroes_dyn).
        tr_attr = ""
        if "class" in h:
            tr_attr += f' data-class="{_esc(h["class"])}"'
        if "current" in h:
            tr_attr += f' data-current="{1 if h["current"] else 0}"'
        if h.get("price"):
            tr_attr += f' data-price="{int(h["price"])}"'
        rows.append(f'<tr{tr_attr}>{"".join(cells)}</tr>')

    # Toggles — styled like the Neutral Creeps / Unit Abilities switches.
    def _switch(sw_id, label, title, checked):
        ck = ' checked' if checked else ''
        return (f'<label class="ua-upgrades-toggle" title="{_esc(title)}">'
                f'<span class="ua-upgrades-label">{label}</span>'
                f'<input type="checkbox" id="{sw_id}" class="ua-switch-input"{ck}>'
                f'<span class="ua-switch" aria-hidden="true"></span></label>')
    # "Remove" tag chips — click a tag to drop it from the diamonds.
    _TAG_CHIPS = [
        ('buff', 'buff-text', 'BUFF'), ('nerf', 'nerf-text', 'NERF'),
        ('new', 'new', 'NEW'), ('del', 'del', 'DEL'),
        ('rework', 'rework', 'REWORK'), ('misc', 'misc', 'MISC'),
        ('qol', 'qol', 'QoL'),
    ]
    tag_chips = ''.join(
        f'<button type="button" class="badge {cls} hd-tag" data-tag="{tag}">{label}</button>'
        for tag, cls, label in _TAG_CHIPS)
    remove_block = (
        '<span class="hd-remove-group" '
        'title="Click a tag to drop it from the diamonds (hover still shows it)">'
        '<strong>Remove</strong>' + tag_chips + '</span>')
    search_block = (
        '<span class="search-box hd-search">'
        '<input type="text" id="hd-hero-search" autocomplete="off" spellcheck="false" '
        f'placeholder="{_esc(search_ph)}">'
        '</span>')
    # Optional items_dyn controls. "Show deleted" switch (sits left of Buff/nerf
    # only): OFF by default → items removed from the game are hidden; ON reveals
    # them (their post-removal columns are blanked anyway).
    current_block = _switch(
        'hd-show-deleted', 'Show deleted',
        'Show items that were removed from the game (hidden by default)', False
    ) if current_toggle else ''
    # Class filter group (sits right of Remove): toggle item classes on/off.
    # Default: only regular Items on; Neutral Items + Enchantments start OFF.
    if class_filter:
        _CLASS_CHIPS = [('regular', 'Items', True), ('neutral', 'Neutral Items', False),
                        ('enchant', 'Enchantments', False)]
        class_chips = ''.join(
            f'<button type="button" class="hd-class-chip" data-class="{c}" '
            f'aria-pressed="{"true" if on else "false"}">{lbl}</button>'
            for c, lbl, on in _CLASS_CHIPS)
        class_block = (
            '<span class="hd-class-group" title="Show or hide item classes">'
            '<strong>Show</strong>' + class_chips + '</span>')
    else:
        class_block = ''
    # Price-range filter (copied from mana_items): two bound inputs + a clear-X
    # sharing one border. Items priced 0 (neutrals/enchants) are exempt — see JS.
    if price_filter:
        price_block = (
            '<span class="view-group hd-price-group"><strong>Price</strong>'
            '<span class="mr-price-range">'
            '<input type="number" class="mr-price-input" id="hd-price-min" '
            'placeholder="from" min="0" step="50" inputmode="numeric">'
            '<span class="mr-price-sep" aria-hidden="true">–</span>'
            '<input type="number" class="mr-price-input" id="hd-price-max" '
            'placeholder="to" min="0" step="50" inputmode="numeric">'
            '<button type="button" class="mr-price-clear" id="hd-price-clear" '
            'aria-label="Clear price range" title="Clear price range" hidden>'
            '<svg viewBox="0 0 12 12" width="10" height="10" aria-hidden="true">'
            '<path d="M2 2 L10 10 M10 2 L2 10" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" fill="none"/>'
            '</svg></button></span></span>')
    else:
        price_block = ''
    # All controls live inside ONE bordered surface (.hd-tb-inner) — a single
    # unified panel rather than a row of separate floating pills. The switches +
    # filter groups go borderless inside it (CSS), separated by thin dividers;
    # the tag/class chips keep their own (universal) design.
    toolbar = (
        '<div class="cal-toggle-bar inbox-bar hd-toolbar"><div class="hd-tb-inner">'
        + _switch('hd-hide-old', 'Hide old',
                  'Show only the most recent patches that fit the width '
                  '(latest at the right edge); off shows every patch', True)
        + current_block
        + _switch('hd-bn-only', 'Buff/nerf only',
                  'Fill cells with buff/nerf colours only — NEW counts as buff, '
                  'DEL as nerf (hover still shows every tag)', False)
        + remove_block
        + class_block
        + price_block
        + search_block
        + '</div></div>\n')

    page = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        f'<title>SIKLE | {_esc(page_title)}</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={_site.compute_asset_version()}">\n'
        '</head>\n'
        # data-dyn-path: where scripts.js fetches the manifest (root page → direct).
        # data-dyn-from: the ?from= token the matrix puts on dyn-cell links so the
        # destination patch page's back-arrow returns HERE.
        f'<body data-dyn-path="_dynamics.json" data-dyn-from="{_esc(from_token)}">\n'
        f'{nav}\n'
        '<div class="container creeps-page hd-page">\n'
        '<div class="sticky-frame" aria-hidden="true"></div>\n'
        '<div class="sticky-frame-top" aria-hidden="true"></div>\n'
        '<div class="creeps-scroll">\n'
        f'{subnav}'
        f'<p class="mr-blurb inbox-bar">{blurb}</p>\n'
        f'{toolbar}'
        # Column visibility + fit-to-width is set by scripts.js dynLayoutMatrix().
        # items pages get an extra hook class so item-shaped icons (88×64) aren't
        # cropped by the hero 16:9 icon box.
        f'<table class="creeps-table heroes-dyn-table'
        f'{" items-dyn-table" if kind == "item" else ""}">\n'
        f'<thead><tr class="cat-row">{supercat_html}</tr>'
        f'<tr class="col-row">{head_html}</tr></thead>\n'
        f'<tbody>\n{chr(10).join(rows)}\n</tbody>\n'
        '</table>\n</div>\n</div>\n'
        f'<script src="scripts.js?v={_site.compute_asset_version()}"></script>\n'
        '</body>\n</html>\n'
    )
    out = _os.path.join(_HERE, out_file)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"  -> {out_file}: {len(page):,} bytes "
          f"({len(rows_data)} {kind}s x {len(patches)} patches)")
