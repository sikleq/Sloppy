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

_HERE = _os.path.dirname(_os.path.abspath(__file__))


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
    """Short SHA1 of styles.css + scripts.js combined content. Appended as
    ?v=<hash> to asset URLs so browsers re-fetch only when either changes."""
    css = open(_os.path.join(_HERE, "styles.css"), encoding="utf-8").read()
    js = open(_os.path.join(_HERE, "scripts.js"), encoding="utf-8").read()
    return _hashlib.sha1((css + js).encode("utf-8")).hexdigest()[:10]


def get_latest_version():
    """Return the latest patch version string (e.g. '7.41c') from site_meta.json,
    written by build_patch.py. Empty string if the meta hasn't been written yet."""
    import json as _json
    meta_path = _os.path.join(_HERE, "data", "site_meta.json")
    try:
        return _json.loads(open(meta_path, encoding="utf-8").read()).get(
            "latest_patch_version", ""
        )
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


# Materials sub-tabs — flat row rendered as a thin bar BELOW the main header
# (so the header itself stays compact). Single source of truth.
MATERIALS_SUBTABS = [
    ("creeps",     "Neutral Stats",     "neutral_stats.html"),
    ("abilities",  "Neutral Abilities", "neutral_abilities.html"),
    ("mana_items", "Mana Items",        "mana_items.html"),
    ("heroes_stats", "Hero Stats",      "heroes_stats.html"),
    ("heroes_dyn", "Hero Dynamics",     "heroes_dyn.html"),
    ("items_dyn",  "Item Dynamics",     "items_dyn.html"),
    ("terrain",    "Terrain",           "terrain.html"),
]


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
        # display, styled like the dropdown button on patch pages so the
        # right-side block looks consistent across the site.
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
    """The Materials sub-tab bar (Neutral Stats | Neutral Abilities | Mana
    Items) as a standalone strip — so pages with an inner scroll box can drop
    it inside that box rather than in the page header."""
    subpills = ''.join(
        f'<a class="nav-subtab{" active" if active == key else ""}" '
        f'href="{prefix}{href}">{label}</a>'
        for key, label, href in MATERIALS_SUBTABS)
    return (f'<div class="materials-subnav"><div class="materials-subnav-inner">'
            f'{subpills}</div></div>\n')
