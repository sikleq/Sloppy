"""Terrain Stats — the map history under Materials ▸ Terrain (the owner 2026-10-04: "add the Oldgrowth table
somewhere, carefully, not breaking the Terrain page visually or technically — a sub-tab of the Terrain button,
Terrain Stats, with more info"; then: no intro, nothing centred, the "65 map files" tile links to the repository,
a better chart with faint axes and values on hover, the table full width, a Shrines icon, a little map square instead
of "picture", dd-mm-yy dates, icons on Date / Map file, what moved shown in the cells in yellow)."""
import glob
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
import builders.site_common as site  # noqa: E402
import builders.terrain_stats as ts  # noqa: E402


def test_every_map_file_is_one_row_with_the_patches_that_shipped_it():
    files = ts.load()
    assert len(files) == 65 and files[0]["patch"] == "7.08"
    by = {f["patch"]: f for f in files}
    assert by["7.22"]["also"][:2] == ["7.22b", "7.22c"]
    assert by["7.41"]["n"]["watchers"] == 10 and by["7.41"]["n"]["outposts"] == 2      # lanterns, not outposts
    assert [by["7.41"]["n"][f"tier{t}"] for t in range(4)] == [6, 14, 6, 2]
    assert ts.churn(by["7.38"]) == 2069 and by["7.41"]["moves"]["camps"] == {"moved": 7}
    assert ts.short_date("2026-09-15") == "15-09-26"


def test_cells_show_added_removed_and_moved():
    files = ts.load()
    table = ts.table_html(files, {"7.41", "7.40"})
    rows = ts.group(files)                                             # identical files glued (7.41a … 7.41f)
    assert table.count("<tr>") == len(rows) + 1 and len(rows) < 65
    assert table.index(">7.41a<") < table.index(">7.08<")              # newest first
    glued = next(r for r in rows if r["patch"] == "7.41a")
    assert glued["also"] == ["7.41b", "7.41c", "7.41d", "7.41e", "7.41f"]
    assert '7.41a<span class="ts-range"> – 7.41f</span>' in table                # a range, not a list (the owner)
    assert '7.35<span class="ts-range"> – 7.37e</span>' in table and "also " not in table
    assert ">Map version<" in table and ">Map file<" not in table
    assert "Spawn boxes" not in table and "icon_calendar" not in table and "icon_terrain" not in table
    assert '<a href="terrain_741.html">7.41</a>' in table and '<a href="terrain_739.html">' not in table
    row = table.split('<a href="terrain_741.html">7.41</a>', 1)[1].split("</tr>", 1)[0]
    assert '<span class="ts-up">+20</span>' in row and "+324" not in row          # trees: the result, not +324 −304
    assert '<span class="ts-moved">7 moved</span>' in row and '<span class="ts-moved">2 moved</span>' in row
    assert "What moved" not in table and "picture" not in table
    assert 'src="icons/maps/thumbs/' in table and 'class="ts-thumb"' in table
    assert 'icons/ui/gothic/tc_shrines.png' in table and ">28-03-26<" in table
    for f in files:                                                    # every square and icon is there
        assert os.path.exists(os.path.join(_ROOT, "icons", "maps", "thumbs", f["sha8"] + ".webp")), f["patch"]
    for _k, _label, icon in ts.COLUMNS:
        assert os.path.exists(os.path.join(_ROOT, "icons", icon + ".png")), icon


def test_tiles_chart_and_the_terrain_menu():
    files = ts.load()
    tiles = ts.tiles_html(files, 118)
    assert '<a class="tf-tile ts-tile-link" href="https://github.com/sikleq/Oldgrowth">' in tiles
    chart = ts.chart_svg(files)
    assert chart.count('class="ts-mark"') == 5 and '">7.33</text></g>' in chart and "+1838" not in chart  # versions only
    assert chart.count('class="ts-pt"') == 65 and '">7.38 · 2496</text>' in chart       # version + count on hover
    assert 'class="ts-grid ts-grid-major" x1=' in chart and 'class="ts-axis"' in chart
    groups = {g[0]: g for g in site.MATERIALS_GROUPS}
    assert [c[0] for c in groups["terrain_grp"][3]] == ["terrain", "terrain_stats"]
    assert 'href="terrain_stats.html">Terrain Stats</a>' in site.render_materials_subnav("terrain_stats")


def test_terrain_pages_never_delete_the_stats_page_and_styles_stay_scoped():
    src = open(os.path.join(_ROOT, "builders", "terrain.py"), encoding="utf-8").read()
    assert '"terrain_[0-9]*.html"' in src and '"terrain_*.html"' not in src
    assert not [f for f in glob.glob(os.path.join(_ROOT, "dist", "terrain_[0-9]*.html")) if "stats" in f]
    css = open(os.path.join(_ROOT, "styles.css"), encoding="utf-8").read()
    block = css.split("/* ---- Terrain Stats", 1)[1].split("a.ts-thumb:hover img", 1)[0]
    wrap = block.split(".terrain-stats-page .ts-wrap {", 1)[1].split("}", 1)[0]
    assert "auto" not in wrap and "max-width" not in wrap               # never centred
    for line in block.splitlines():                                   # every rule scoped to the page or its parts
        if line.startswith(".") and "{" in line:
            assert line.startswith((".terrain-stats-page", ".ts-chart", ".ts-table")), line
