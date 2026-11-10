"""The site's one stylesheet is written in parts, src/css/*.css, and glued here into dist/styles.css. The browser gets one file
as before. THE ORDER IS THE CASCADE: a part may override what stands in the parts before it, so parts are never reordered and
a rule stays in its part. To change how something looks, edit the declaration that sets it instead of adding one further
down (tools/css_dead_rules.py lists the ones that already do nothing)."""
from pathlib import Path

CSS_DIR = Path(__file__).resolve().parent.parent / "src" / "css"

CSS_PARTS = (
    "fonts", "tokens", "base", "nav", "index-book", "index-tiles", "version-nav", "calendar", "calendar-infographic", "calendar-builds",
    "patch-toolbar", "patch-dynamics", "patch-new-items", "patch-chips", "patch-entity-labels", "patch-ability-change",
    "patch-new-entity-rows", "patch-ability-block", "patch-subnotes", "patch-formula-rows", "patch-formula-tables",
    "creeps-table", "creeps-cells", "hero-dynamics", "tables-shared", "hero-lab", "hero-lab-inventory", "hero-lab-stats",
    "hero-lab-tooltip", "table-marks", "mana-items", "hero-stats", "aoe-increase", "terrain", "terrain-controls", "overrides",
    "pixel-skin", "pixel-skin-filters",
    "patch-tag-marks",          # tags as tiles in the row and on the line, over the tags' own look (trial, 2026-11-06)
    "colorblind.generated",     # written by scripts/gen/gen_colorblind_css.py, not by hand
    "phones",                   # last: every rule for phones wins over the rest
)


def read_css() -> str:
    """The whole stylesheet as the browser gets it, before minifying."""
    return "".join((CSS_DIR / f"{name}.css").read_text(encoding="utf-8") for name in CSS_PARTS)
