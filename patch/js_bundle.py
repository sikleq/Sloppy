"""The site's one script is written in parts, src/js/*.js, and glued here in a fixed order into dist/src/scripts.js. The page
gets one file as before; each part stays a block of its own (owner 2026-11-04). No modules and no bundler: gluing keeps the
order the code runs in, and a part can share nothing with another except the few top-level functions it already shared."""
from pathlib import Path

JS_DIR = Path(__file__).resolve().parent.parent / "src" / "js"

# The order is the order of execution. It matters: abilities trees (patch-page) before changes-filters, the mana heatmap's
# listener (mana-items) before its toggle (mana-items-heatmap).
JS_PARTS = (
    "nav-subnav", "back-arrow", "patch-page", "talent-tree", "dyn-lens", "creeps-table", "unit-abilities-upgrades",
    "creeps-changelog", "creeps-scroll-size", "creeps-pinned", "tooltips", "nav-height", "mana-items",
    "terrain-stats-rows", "mana-items-filters", "hero-stats", "changes-filters", "changes-item-slots", "changes-index",
    "hero-lab", "hero-stats-divider", "mana-items-heatmap", "index-wall", "index-tiles", "formula-calculator", "terrain",
    "terrain-lightbox", "info-pop-placement", "aoe-increase", "dyn-offscreen", "creeps-scroll-guard", "search-layout",
    "search-fab", "colorblind",
)


def read_js() -> str:
    """The whole script as the browser gets it, before minifying."""
    return "".join((JS_DIR / f"{name}.js").read_text(encoding="utf-8") for name in JS_PARTS)
