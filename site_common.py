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


def compute_asset_version():
    """Short SHA1 of styles.css + scripts.js combined content. Appended as
    ?v=<hash> to asset URLs so browsers re-fetch only when either changes."""
    css = open(_os.path.join(_HERE, "styles.css"), encoding="utf-8").read()
    js = open(_os.path.join(_HERE, "scripts.js"), encoding="utf-8").read()
    return _hashlib.sha1((css + js).encode("utf-8")).hexdigest()[:10]


# Single source of truth for the nav tabs. Tuple: (key, label, root_href).
# `changelogs` is special — its href is the latest patch page, passed in
# per-call (it isn't a fixed root file).
NAV_TABS = [
    ("main",       "Main",         "index.html"),
    ("changelogs", "Changelogs",   None),
    ("calendar",   "Calendar",     "calendar.html"),
    ("creeps",     "Tables",       "creeps.html"),
]


def render_top_nav(active, latest_href, *, patch_context=False, picker_html=None):
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
    """
    prefix = "../" if patch_context else ""
    tabs = []
    for key, label, root_href in NAV_TABS:
        cls = " active" if active == key else ""
        target = latest_href if key == "changelogs" else (prefix + root_href)
        tabs.append(f'<a class="nav-tab{cls}" href="{target}">{label}</a>')
    if picker_html:
        right_side = picker_html
    else:
        # Flat tabs (calendar, creeps, main, any future page) reserve the
        # nav-context height via the unified .nav-context-flat modifier.
        right_side = (
            f'\n    <div class="nav-context nav-context-flat '
            f'nav-context-{active}"></div>'
        )
    return f'''<nav class="top-nav">
  <div class="nav-inner">
    <div class="nav-tabs">
      {"".join(tabs)}
    </div>{right_side}
  </div>
</nav>
'''
