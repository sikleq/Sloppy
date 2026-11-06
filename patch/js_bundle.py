"""The site's script is written in parts, src/js/*.js, and glued here in a fixed order. Each part stays a block of its own (owner
2026-11-04). No modules and no bundler: gluing keeps the order the code runs in, and a part can share nothing with another except
the few top-level functions it already shared.

Each kind of page loads its own file, dist/src/scripts-<kind>.js: the common parts plus what its pages use (2026-11-05, a patch page
needed under half of the script). Which pages use a part is read from its guard, the element it looks for: PART_MARKERS, and
tests/test_js_pages.py checks every built page against them. A part with no marker is common. dist/src/scripts.js stays whole, for
a page cached from before this. A new part used by only some pages: its marker here and its name in JS_PAGES.
"""
from pathlib import Path

JS_DIR = Path(__file__).resolve().parent.parent / "src" / "js"

# The order is the order of execution. It matters: abilities trees (patch-page) before changes-filters, the mana heatmap's
# listener (mana-items) before its toggle (mana-items-heatmap).
JS_PARTS = (
    "nav-subnav", "back-arrow", "patch-reanchor", "back-to-top", "version-dropdown", "patch-page", "patch-dynamics", "talent-tree", "dyn-lens", "creeps-table", "unit-abilities-upgrades",
    "creeps-changelog", "creeps-scroll-size", "creeps-pinned", "tooltips", "nav-height", "mana-items",
    "terrain-stats-rows", "mana-items-filters", "hero-stats", "changes-filters", "changes-item-slots", "changes-index",
    "hero-lab", "hero-stats-divider", "mana-items-heatmap", "index-wall", "index-tiles", "formula-calculator", "terrain",
    "terrain-lightbox", "info-pop-placement", "aoe-increase", "dyn-offscreen", "creeps-scroll-guard", "search-layout",
    "search-fab", "colorblind",
)

# What only some pages use, by the words its guard needs in the page's HTML (a regular expression).
PART_MARKERS = {
    "creeps-table": r"creeps-table|creep-copy",
    "creeps-changelog": r"<td[^>]*data-(?:hist|name)=",
    "creeps-pinned": r"creeps-table",
    "unit-abilities-upgrades": r"unit-abilities-table",
    "dyn-lens": r"heroes-dyn-table",
    "dyn-offscreen": r"heroes-dyn-table",
    "mana-items": r"mr-table|mr-hide-active",
    "mana-items-filters": r"mr-table",
    "mana-items-heatmap": r"mr-table",
    "hero-stats": r"hs-view-mode",
    "hero-stats-divider": r"(?<![-\w])hs-table",
    "terrain-stats-rows": r"ts-table",
    "aoe-increase": r"aoe-table",
    "changes-filters": r"ec-scope-btn|ec-ab-btn",
    "changes-item-slots": r"ec-islots",
    "changes-index": r"data-ec-search",
    "index-wall": r"inv-signatures",
    "index-tiles": r"inv-book|inv-cell-",
    "hero-lab": r"hero-lab-data",
}

# The kinds of page and their parts beyond the common ones. hero-lab reads innateDpm of hero-stats and ecShopMarkup of changes-item-slots.
JS_PAGES = {
    "base": (),
    "entity": ("changes-filters", "changes-item-slots"),
    "changes": ("changes-filters", "changes-item-slots", "changes-index", "index-wall"),
    "table": ("creeps-table", "creeps-changelog", "creeps-pinned", "unit-abilities-upgrades", "dyn-lens", "dyn-offscreen", "mana-items",
              "mana-items-filters", "mana-items-heatmap", "hero-stats", "hero-stats-divider", "terrain-stats-rows", "aoe-increase"),
    "lab": ("hero-stats", "changes-item-slots", "hero-lab"),
    "home": ("index-wall", "index-tiles"),
}


def parts_of(kind):
    """The parts of a kind of page, in the order of JS_PARTS."""
    own = JS_PAGES[kind]
    return tuple(name for name in JS_PARTS if name not in PART_MARKERS or name in own)


def read_js(kind=None) -> str:
    """The script as the browser gets it, before minifying: a kind of page's, or the whole one."""
    return "".join((JS_DIR / f"{name}.js").read_text(encoding="utf-8") for name in (parts_of(kind) if kind else JS_PARTS))
