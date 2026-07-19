"""Shared site chrome for the Sloppy static site.

Used by both build_patch.py (patch changelogs + calendar + main hub) and
build_creeps.py (the neutral-creeps table side-project). Owns the single
source of truth for:
  - the top-nav tab list (so adding a tab is a one-file change)
  - the asset-version cache-bust hash (styles.css + scripts.js)

Keeping these here means the two builders stay decoupled — neither has to
import the other — while the header stays identical across every page.
"""
import hashlib as _hashlib
import os as _os

# builders/site_common.py lives one directory below the project root.
_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
DIST_DIR = _os.path.join(_HERE, "dist")


def favicon_links(prefix=""):
    """Render the shared favicon <link> block. `prefix` is "" for root pages
    and "../" for files under /patches/ so paths resolve correctly."""
    return (
        f'<link rel="icon" type="image/svg+xml" href="{prefix}icons/favicon/favicon.svg">\n'
        f'<link rel="icon" type="image/png" sizes="16x16" href="{prefix}icons/favicon/favicon-16x16.png">\n'
        f'<link rel="icon" type="image/png" sizes="32x32" href="{prefix}icons/favicon/favicon-32x32.png">\n'
        f'<link rel="icon" type="image/png" sizes="96x96" href="{prefix}icons/favicon/favicon-96x96.png">\n'
        f'<link rel="shortcut icon" href="{prefix}icons/favicon/favicon.ico">\n'
        f'<link rel="apple-touch-icon" sizes="180x180" href="{prefix}icons/favicon/apple-touch-icon.png">\n'
        f'<link rel="manifest" href="{prefix}icons/favicon/site.webmanifest">\n'
    )


def compute_asset_version():
    """Short SHA1 of shared CSS and JavaScript assets."""
    with open(_os.path.join(_HERE, "styles.css"), encoding="utf-8") as _f:
        css = _f.read()
    with open(_os.path.join(_HERE, "src", "scripts.js"), encoding="utf-8") as _f:
        js = _f.read()
    battle_path = _os.path.join(_HERE, "src", "hero_lab_battle.js")
    if _os.path.exists(battle_path):
        with open(battle_path, encoding="utf-8") as _f:
            battle = _f.read()
    else:
        battle = ""
    hcl_path = _os.path.join(_HERE, "src", "hero_changelog.js")
    if _os.path.exists(hcl_path):
        with open(hcl_path, encoding="utf-8") as _f:
            hcl = _f.read()
    else:
        hcl = ""
    return _hashlib.sha1((css + js + battle + hcl).encode("utf-8")).hexdigest()[:10]


def get_latest_version():
    """Return the latest patch version string (e.g. '7.41c') from site_meta.json,
    written by build_patch.py. Empty string if the meta hasn't been written yet."""
    import json as _json
    meta_path = _os.path.join(_HERE, "data", "site_meta.json")
    try:
        with open(meta_path, encoding="utf-8") as _f:
            return _json.loads(_f.read()).get("latest_patch_version", "")
    except Exception:
        return ""


# Header tabs in the centre of the site nav. Tuple: (key, label, root_href).
# `changelogs` (label: Patch Reader) is special — its href is the latest patch
# page, passed in per-call (it isn't a fixed root file). "Main" lives in the
# brand link on the left, so it's not duplicated here.
NAV_TABS = [
    ("main",       "Main",         "index.html"),
    ("changelogs", "Changelogs",   None),
    ("calendar",   "Calendar",     "calendar.html"),
    ("materials",  "Materials",    "neutral_stats.html"),
]


# Materials sub-tabs — a thin bar BELOW the main header (so the header stays
# compact). GROUPED to mirror the index inventory tiles: each group is a
# trigger (links to its primary page) that reveals a hover dropdown of its
# sub-pages. Terrain has no children → a plain link. Single source of truth.
#   (group_key, group_label, group_href, [ (child_key, child_label, child_href|None), ... ])
# child_href=None ⇒ an unbuilt "soon" placeholder (Summons / Lane Creeps).
MATERIALS_GROUPS = [
    ("creeps_grp", "Creeps", "neutral_stats.html", [
        # Neutral Abilities nests UNDER Neutral Stats (4th tuple element = its
        # own sub-pages, rendered indented inside the dropdown).
        ("creeps",    "Neutral Stats",     "neutral_stats.html", [
            ("abilities", "Neutral Abilities", "neutral_abilities.html"),
        ]),
        ("summons",   "Summons",           None),
        ("lane",      "Lane Creeps",       None),
    ]),
    ("items_grp", "Items", "mana_items.html", [
        ("mana_items", "Mana Items",    "mana_items.html"),
        ("items_dyn",  "Item Dynamics", "items_dyn.html"),
    ]),
    ("heroes_grp", "Heroes", "heroes_stats.html", [
        ("heroes_stats", "Hero Stats",    "heroes_stats.html"),
        ("hero_lab",     "Hero Lab",      "hero_lab.html"),
        ("aoe_increase", "AoE Increase",  "aoe_increase.html"),
        ("heroes_dyn",   "Hero Dynamics", "heroes_dyn.html"),
        ("hero_changelog", "Hero Changelog", "hero_changelog.html"),
    ]),
    ("terrain", "Terrain", "terrain_741.html", None),
]


def get_materials_label(active_key):
    """Return the visible label for a Materials page key."""
    def _walk(nodes):
        for node in nodes:
            if node[0] == active_key:
                return node[1]
            if len(node) > 3 and node[3]:
                found = _walk(node[3])
                if found:
                    return found
        return None

    for gkey, glabel, _ghref, children in MATERIALS_GROUPS:
        if gkey == active_key:
            return glabel
        if children:
            found = _walk(children)
            if found:
                return found
    return ""


def render_top_nav(active, latest_href, *, patch_context=False, picker_html=None,
                   subtabs_active=None, subnav_in_header=True, centre_tabs=True):
    """Render the shared top nav.

    active        — one of the NAV_TABS keys ('main'/'changelogs'/...).
    latest_href   — href for the Changelogs tab (the latest patch page),
                    already relative-correct for the calling page.
    patch_context — True when rendered inside the patches/ folder; root
                    files (index/calendar/creeps) get a ../ prefix.
    picker_html   — optional right-side HTML (version dropdown + arrows +
                    release-info) for patch pages. When None, a flat
                    placeholder reserves the SAME height so the header
                    doesn't jump between tabs.
    subtabs_active — when set (one of MATERIALS_SUBTABS keys), the Materials
                    sub-tabs render INSIDE the header (right side) instead of
                    a separate strip below it.
    """
    prefix = "../" if patch_context else ""
    # Header now carries a brand block (helmet logo + pixel-font title) instead
    # of inline nav tabs. The full nav list lives on the main hub page.
    if active == "main":
        brand = (
            f'<span class="nav-brand">'
            f'<img class="nav-brand-logo" src="{prefix}icons/logo_knight.png" '
            f'alt="" loading="eager">'
            f'<span class="nav-brand-text">'
            f'<span class="nav-brand-sikle">sikle</span> | dota.vpk'
            f'</span>'
            f'</span>'
        )
    else:
        brand = (
            f'<a class="nav-brand" href="{prefix}index.html" aria-label="Home">'
            f'<img class="nav-brand-logo" src="{prefix}icons/logo_knight.png" '
            f'alt="" loading="eager">'
            f'<span class="nav-brand-text">'
            f'<span class="nav-brand-sikle">sikle</span> | dota.vpk'
            f'</span>'
            f'</a>'
        )
    # Centre tabs: Patch Reader (→ latest patch) | Calendar | Materials. Shown
    # on every page so navigation is one click from anywhere.
    def _tab_href(key, href):
        if key == "changelogs":
            return latest_href
        return prefix + href
    centre = ''.join(
        f'<a class="nav-tab{" active" if active == key else ""}" '
        f'href="{_tab_href(key, href)}">{label}</a>'
        for key, label, href in NAV_TABS)
    # On the index hub the centre tabs are omitted — they'd just duplicate the
    # inventory-tile grid below. Other pages keep them. Keep an EMPTY centre
    # element so the 3-column grid (1fr/auto/1fr) still puts the version block
    # in the RIGHT column (without it, only 2 children remain and the version
    # slides into the middle column).
    centre_html = (f'<div class="nav-tabs">{centre}</div>' if centre_tabs
                   else '<div class="nav-tabs" aria-hidden="true"></div>')

    if picker_html:
        right_side = picker_html
    else:
        # Non-patch pages: show the latest patch version as a NON-clickable
        # display, except Materials pages which show the current table/page
        # label there instead.
        materials_label = (get_materials_label(subtabs_active)
                           if active == "materials" and subtabs_active else "")
        if active == "main":
            ver_html = (
                '<span class="version-beta-wrap" role="button" tabindex="0"'
                ' aria-label="What\'s new" aria-expanded="false">'
                '<span class="version version-static version-beta"><span class="version-beta-text">NEW</span></span>'
                '</span>'
            )
        elif materials_label:
            ver_html = (f'<span class="version version-static version-materials">'
                        f'{materials_label}</span>')
        elif active == "calendar":
            ver_html = ''
        else:
            latest_ver = get_latest_version()
            ver_html = (f'<span class="version version-static">{latest_ver}</span>'
                        if latest_ver else '')
        right_side = (
            f'<div class="nav-context nav-context-flat '
            f'nav-context-{active}">{ver_html}</div>'
        )
    header = f'''<nav class="top-nav">
  <div class="nav-inner">
    {brand}
    {centre_html}
    {right_side}
  </div>
</nav>
'''
    # On Materials pages, hang a thin sub-tab bar BELOW the header (NOT inside
    # it — that would make the header tall). Flat row of three pills.
    #   subnav_in_header=True  (Mana Items): the bar sits right under the nav
    #     and scrolls away with the page.
    #   subnav_in_header=False (Neutral Creeps / Abilities): the caller places
    #     the bar INSIDE the inner scroll box itself (via render_materials_subnav)
    #     so it scrolls away with the table — the page barely scrolls there.
    if subtabs_active is not None and subnav_in_header:
        header += render_materials_subnav(subtabs_active, prefix)
    return header


def render_materials_subnav(active, prefix=""):
    """The Materials sub-tab bar (grouped: Creeps ▾ | Items ▾ | Heroes ▾ |
    Terrain) as a standalone strip — pages with an inner scroll box drop it
    inside that box. Each group is a trigger linking to its primary page with a
    hover dropdown of its children; the active child highlights both itself and
    its group trigger. `active` is one of the child/terrain keys."""
    def _find_active_label(nodes, active_key):
        for node in nodes:
            if node[0] == active_key:
                return node[1]
            if len(node) > 3 and node[3]:
                found = _find_active_label(node[3], active_key)
                if found:
                    return found
        return None

    parts = []
    for gkey, glabel, ghref, children in MATERIALS_GROUPS:
        if children is None:
            # Plain link (Terrain — no children).
            cls = "nav-subtab" + (" active" if active == gkey else "")
            parts.append(f'<a class="{cls}" href="{prefix}{ghref}">{glabel}</a>')
            continue
        # Flatten child + grandchild keys so the group highlights when any
        # descendant page is active.
        def _keys(nodes):
            ks = []
            for node in nodes:
                ks.append(node[0])
                if len(node) > 3 and node[3]:
                    ks.extend(_keys(node[3]))
            return ks
        grp_active = active in _keys(children)
        trig_cls = "nav-subtab nav-subtab-group" + (" active" if grp_active else "")

        def _item(node):
            ckey, clabel, chref = node[0], node[1], node[2]
            if chref is None:
                return (f'<span class="nav-subitem nav-subitem-soon" aria-disabled="true">'
                        f'{clabel}<span class="nav-soon-tag">soon</span></span>')
            icls = "nav-subitem" + (" active" if active == ckey else "")
            return f'<a class="{icls}" href="{prefix}{chref}">{clabel}</a>'

        items = []
        for node in children:
            grands = node[3] if len(node) > 3 and node[3] else None
            if grands:
                # Nested flyout: the node links to its own page AND opens a side
                # submenu of its sub-pages on hover (cascading menu).
                pcls = "nav-subitem nav-subitem-parent" + (
                    " active" if active == node[0] else "")
                trigger = (
                    f'<a class="{pcls}" href="{prefix}{node[2]}">{node[1]}'
                    f'<span class="nav-caret nav-caret-side" aria-hidden="true">'
                    f'▸</span></a>')
                flyout = ('<div class="nav-submenu nav-submenu-flyout">'
                          + ''.join(_item(g) for g in grands) + '</div>')
                items.append(
                    f'<div class="nav-subgroup nav-subgroup-nested">'
                    f'{trigger}{flyout}</div>')
            else:
                items.append(_item(node))
        trigger = (f'<a class="{trig_cls}" href="{prefix}{ghref}">'
                   f'<span class="nav-subtab-label">{glabel}</span>'
                   f'<span class="nav-caret" aria-hidden="true">▾</span></a>')
        menu = f'<div class="nav-submenu">{"".join(items)}</div>'
        parts.append(f'<div class="nav-subgroup">{trigger}{menu}</div>')
    return (f'<div class="materials-subnav"><div class="materials-subnav-inner">'
            f'<div class="materials-subnav-links">{"".join(parts)}</div>'
            f'</div></div>\n')
