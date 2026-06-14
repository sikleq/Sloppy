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

# Common Dota item abbreviations the search box should resolve (keyed by icon
# slug). The search placeholder promises "aghs" etc., so each row carries a
# data-alias with these + an auto acronym so "aghs"→Aghanim's Scepter, "bkb"→
# Black King Bar, "pa"→Phantom Assassin all work.
_ITEM_SEARCH_ALIASES = {
    "ultimate_scepter": "aghs ags scepter", "ultimate_scepter_2": "aghs blessing",
    "aghanims_shard": "shard", "black_king_bar": "bkb", "monkey_king_bar": "mkb",
    "bfury": "bf battlefury", "desolator": "deso", "assault": "ac cuirass",
    "sange_and_yasha": "sny", "kaya_and_sange": "kya", "yasha_and_kaya": "yk",
    "cyclone": "euls eul", "vladmir": "vlads vlad", "poor_mans_shield": "pms",
    "helm_of_the_dominator": "hotd", "helm_of_the_overlord": "overlord",
    "mask_of_madness": "mom", "hand_of_midas": "midas", "hurricane_pike": "pike",
    "shivas_guard": "shiva", "abyssal_blade": "abyssal", "sheepstick": "hex scythe vyse",
    "invis_sword": "shadow blade", "silver_edge": "silver", "heart": "tarrasque",
    "blade_mail": "blademail", "guardian_greaves": "greaves",
    "boots_of_bearing": "bearing", "ancient_janggo": "drum janggo endurance",
    "ethereal_blade": "eblade", "rod_of_atos": "atos", "dragon_lance": "dlance",
    "power_treads": "treads", "travel_boots": "bots", "octarine_core": "octarine",
    "aeon_disk": "aeon", "crimson_guard": "cg", "pipe": "insight",
    "diffusal_blade": "diffusal", "manta": "style", "demonicon": "book of the dead",
    "desolator_2": "stygian", "heavy_blade": "witchbane", "pogo_stick": "tumbler",
    "angels_demise": "khanda", "gungir": "gleipnir", "royale_with_cheese": "block",
}


def _search_alias(name, icon, kind):
    """Extra search keywords for a row: manual abbreviations (items) + an acronym of
    the words (Black King Bar→bkb, Phantom Assassin→pa). Possessive 's is stripped so
    'Aghanim's Scepter'→'as' not 'ass'."""
    parts = []
    if kind == "item":
        a = _ITEM_SEARCH_ALIASES.get(icon)
        if a:
            parts.append(a)
    words = _re.findall(r"[a-z0-9]+",
                        name.lower().replace("’s", "").replace("'s", ""))
    if len(words) > 1:
        parts.append("".join(w[0] for w in words))
    return " ".join(parts)


def _esc(s):
    return _html.escape(str(s), quote=True)


def _multiselect_dropdown(dd_id, label, options):
    """A single toolbar control = a button that opens a checkbox popover for
    multi-select filtering. `options` = [(value, label, checked), ...]. Each option
    checkbox carries data-<dd_id>="<value>"; a top "All" checkbox (data-dd-all) toggles
    them all at once. The menu carries data-dd="<dd_id>" too, so it can be portaled to
    <body> (escaping .creeps-scroll's contain:paint clip) and still be found by
    applyRowFilters. scripts.js `initHdDropdowns` wires open/close + the badge
    ("all"/count); `applyRowFilters` reads checked option values vs each row's
    data-<dd_id>. Used for Type (class) and Category."""
    opts = ''.join(
        f'<label class="hd-dd-opt"><input type="checkbox" '
        f'data-{_esc(dd_id)}="{_esc(v)}"{" checked" if ck else ""}>'
        f'<span>{_esc(lbl)}</span></label>'
        for v, lbl, ck in options)
    all_row = ('<label class="hd-dd-opt hd-dd-all"><input type="checkbox" data-dd-all>'
               '<span>All</span></label><div class="hd-dd-sep" aria-hidden="true"></div>')
    return (
        f'<div class="hd-dd" data-dd="{_esc(dd_id)}">'
        f'<button type="button" class="hd-dd-btn" aria-expanded="false" '
        f'aria-haspopup="true"><span class="hd-dd-label">{_esc(label)}</span>'
        f'<span class="hd-dd-badge" aria-hidden="true"></span>'
        f'<svg class="hd-dd-caret" viewBox="0 0 10 6" width="10" height="6" '
        f'aria-hidden="true"><path d="M0 0l5 6 5-6z" fill="currentColor"/></svg>'
        f'</button>'
        f'<div class="hd-dd-menu" data-dd="{_esc(dd_id)}" role="group" hidden>'
        f'{all_row}{opts}</div></div>')


def _attr_filter_buttons() -> str:
    buttons = [
        ("str", "Strength", "icons/strength.webp"),
        ("agi", "Agility", "icons/agility.webp"),
        ("int", "Intelligence", "icons/intelligence.webp"),
        ("uni", "Universal", "icons/universal.webp"),
    ]
    html = ['<span class="hs-attr-filter-group" aria-label="Primary attribute filter">']
    for key, label, icon in buttons:
        html.append(
            '<button type="button" class="hs-attr-filter" '
            f'data-attr-filter="{key}" aria-pressed="false" title="Show {label} heroes">'
            f'<img src="{icon}" alt="{label}" loading="lazy"></button>'
        )
    html.append('</span>')
    return ''.join(html)


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


def _roster(manifest, roster_key, kind, *, preserve_order=False):
    """Full roster as [{name, icon, key}]. Prefer the explicit roster
    build_patch.py writes (manifest[roster_key]); fall back to deriving it from
    the entities of this kind if an older _dynamics.json is in place.

    preserve_order=True keeps the order from the manifest verbatim (items_dyn
    uses this to get its category-grouped default — build_patch.py already
    sorted by class → category → tier → name). Otherwise alpha-by-name."""
    roster = manifest.get(roster_key)
    if roster:
        if preserve_order:
            return list(roster)
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
                    current_toggle=False, class_filter=False, price_filter=False,
                    category_filter=False, attack_filter=False, attr_filter=False,
                    row_meta_by_slug=None, preserve_roster_order=False):
    """Render a Dynamics matrix page. See module docstring for the params.

    current_toggle — add an "In game" switch (left of Buff vs nerf) that hides
                     rows whose roster entry has current=False (removed/obsolete).
                     Default ON. Needs roster entries to carry `current`.
    class_filter   — add a Type multi-select dropdown (Items / Neutral Items /
                     Enchantments). Needs roster entries to carry `class`.
    category_filter — add a Category multi-select dropdown (Consumables / Attributes
                     / … from the game's shop layout). Needs roster `category` +
                     manifest['item_categories']. Items without a category (neutrals/
                     enchants) are exempt from it.
    All are no-ops on pages whose roster lacks those fields (heroes_dyn)."""
    manifest = _load_manifest()
    # Columns: every patch, OLDEST on the left → NEWEST on the right (so the
    # latest patch is the rightmost column; scripts.js keeps it flush right).
    patches = list(reversed(manifest.get("patches", [])))
    entities = manifest.get("entities", {})
    rows_data = _roster(manifest, roster_key, kind,
                        preserve_order=preserve_roster_order)
    row_meta_by_slug = row_meta_by_slug or {}

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
        # Anchor id mirrors _register_entity's "dyn-<entity_kind>-<slug>" using the
        # KEY's own kind, not the page kind — a roster can carry foreign-kind rows
        # (heroes_dyn includes Spirit Bear, key "creep-hero|spirit-bear", whose
        # patch-page anchor is dyn-creep-hero-spirit-bear, not dyn-hero-...).
        eid = "dyn-" + key.replace("|", "-")
        per_patch = (entities.get(key, {}) or {}).get("patches", {})
        # Lifespan window (items_dyn only; absent on heroes_dyn → spans everything):
        # blank columns BEFORE the item entered the game, and AFTER it was removed.
        added = h.get("added")
        removed = h.get("removed")
        a_idx = ver_index.get(added, 0) if added else 0
        r_idx = ver_index.get(removed) if removed else None
        img = (f'<img src="{_esc(icon_dir)}/{_esc(h["icon"])}.png" '
               f'alt="{_esc(h["name"])}" loading="lazy">')
        alias = _search_alias(h["name"], h["icon"], kind)
        alias_attr = f' data-alias="{_esc(alias)}"' if alias else ''
        cells = [
            f'<td class="hd-hero sticky-col" data-col="name" '
            f'data-sort="{_esc(h["name"])}"{alias_attr}>'
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
                # data-debut marks the item's introduction patch (ver == added):
                # its NEW rows describe "item now exists", so the Buff-vs-nerf fold
                # must NOT count them as a buff (items_dyn only; heroes have no `added`).
                debut_attr = ' data-debut="1"' if (added and ver == added) else ''
                cells.append(
                    f'<td class="hd-cell{sep}" data-ver="{_esc(ver)}" '
                    f'data-hkey="{_esc(key)}" data-eid="{_esc(eid)}"{debut_attr}></td>')
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
        row_meta = row_meta_by_slug.get(slug) or {}
        if row_meta.get("attack_type"):
            tr_attr += f' data-attack-type="{_esc(row_meta["attack_type"])}"'
        if row_meta.get("attr"):
            tr_attr += f' data-attr-type="{_esc(row_meta["attr"])}"'
        if "class" in h:
            tr_attr += f' data-class="{_esc(h["class"])}"'
        if "current" in h:
            tr_attr += f' data-current="{1 if h["current"] else 0}"'
        if h.get("category"):
            tr_attr += f' data-category="{_esc(h["category"])}"'
        if h.get("price"):
            tr_attr += f' data-price="{int(h["price"])}"'
        rows.append(f'<tr{tr_attr}>{"".join(cells)}</tr>')

    # Toggles — styled like the Neutral Creeps / Unit Abilities switches. No hover
    # title (the visible label already says what it does). `title` kept in the
    # signature for caller clarity but not rendered.
    def _switch(sw_id, label, title, checked):
        ck = ' checked' if checked else ''
        return (f'<label class="ua-upgrades-toggle">'
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
    # No "Remove" label — the coloured tag chips speak for themselves (click a tag
    # to drop it from the diamonds).
    remove_block = '<span class="hd-remove-group">' + tag_chips + '</span>'
    search_block = (
        '<span class="search-box hd-search">'
        '<input type="text" id="hd-hero-search" autocomplete="off" spellcheck="false" '
        f'placeholder="{_esc(search_ph)}">'
        '</span>')
    # Optional items_dyn controls. "Show deleted" switch (sits left of Buff vs
    # nerf): OFF by default → items removed from the game are hidden; ON reveals
    # them (their post-removal columns are blanked anyway).
    current_block = _switch(
        'hd-show-deleted', 'Deleted',
        'Show items no longer in the game — removed or cycled out of the pool '
        '(hidden by default)', False
    ) if current_toggle else ''
    attack_block = (
        '<span class="hs-attack-filter-group" aria-label="Attack type filter">'
        '<button type="button" class="hs-attack-filter" data-attack-filter="melee" '
        'aria-pressed="false" title="Show melee heroes">'
        '<span class="atk-badge" aria-hidden="true">'
        '<img src="icons/ui/atk_melee.png" alt=""></span><span>Melee</span></button>'
        '<button type="button" class="hs-attack-filter" data-attack-filter="ranged" '
        'aria-pressed="false" title="Show ranged heroes">'
        '<span class="atk-badge" aria-hidden="true">'
        '<img src="icons/ui/atk_ranged.png" alt=""></span><span>Ranged</span></button>'
        '</span>'
    ) if attack_filter else ''
    attr_block = _attr_filter_buttons() if attr_filter else ''
    # Class filter (sits right of Remove): ONE multi-select dropdown (Type) — pick
    # any combination of Items / Neutral Items / Enchantments. Default: Items only.
    if class_filter:
        class_block = _multiselect_dropdown('class', 'Type', [
            ('regular', 'Items', True),
            ('neutral', 'Neutral Items', False),
            ('enchant', 'Enchantments', False),
        ])
    else:
        class_block = ''
    # Price-range filter (copied from mana_items): two bound inputs + a clear-X
    # sharing one border, as ONE compact pill that matches the panel control height
    # (the label lives INSIDE the pill, so it no longer towers over the switches).
    # Items priced 0 (neutrals/enchants) are exempt — see JS.
    if price_filter:
        price_block = (
            '<span class="mr-price-range hd-price-range">'
            '<span class="mr-price-label" aria-hidden="true">Price</span>'
            '<input type="number" class="mr-price-input" id="hd-price-min" '
            'placeholder="min" min="0" step="50" inputmode="numeric" '
            'aria-label="Minimum price">'
            '<span class="mr-price-sep" aria-hidden="true">–</span>'
            '<input type="number" class="mr-price-input" id="hd-price-max" '
            'placeholder="max" min="0" step="50" inputmode="numeric" '
            'aria-label="Maximum price">'
            '<button type="button" class="mr-price-clear" id="hd-price-clear" '
            'aria-label="Clear price range" hidden>'
            '<svg viewBox="0 0 12 12" width="10" height="10" aria-hidden="true">'
            '<path d="M2 2 L10 10 M10 2 L2 10" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" fill="none"/>'
            '</svg></button></span>')
    else:
        price_block = ''
    # Category filter: ONE multi-select dropdown built from the game's shop tabs
    # (manifest['item_categories'], from data/shops.txt). Default: all selected (=
    # no filtering). Items without a category (neutrals/enchants) are exempt — JS.
    if category_filter:
        _cats = manifest.get('item_categories', [])
        category_block = _multiselect_dropdown(
            'category', 'Category', [(c, c, True) for c in _cats]) if _cats else ''
    else:
        category_block = ''
    # All controls live inside ONE bordered surface (.toolbar-panel, the site
    # standard) — a single unified panel rather than a row of separate floating
    # pills. The switches + filter groups go borderless inside it (CSS), separated
    # by thin dividers; the tag/class chips keep their own (universal) design.
    toolbar = (
        '<div class="cal-toggle-bar inbox-bar hd-toolbar"><div class="toolbar-panel">'
        # Type + Category filters lead the panel (per request), then the switches,
        # price, tag chips, and the full-width search on its own bottom row.
        + class_block
        + category_block
        + attack_block
        + attr_block
        + _switch('hd-hide-old', 'Hide old',
                  'Show only the most recent patches that fit the width '
                  '(latest at the right edge); off shows every patch', True)
        + current_block
        + _switch('hd-bn-only', 'Buff vs nerf',
                  'Collapse each cell to two bands — buff + NEW (green) vs nerf + '
                  'DEL (red); rework/misc/qol drop out of the colour (hover still '
                  'shows every tag)', False)
        + price_block
        + remove_block
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
        f'<script src="src/scripts.js?v={_site.compute_asset_version()}"></script>\n'
        '</body>\n</html>\n'
    )
    out = _os.path.join(_HERE, out_file)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"  -> {out_file}: {len(page):,} bytes "
          f"({len(rows_data)} {kind}s x {len(patches)} patches)")
