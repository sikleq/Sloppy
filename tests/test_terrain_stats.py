"""Terrain Stats — the map history under Materials ▸ Terrain (the owner 2026-10-04: "add the Oldgrowth table
somewhere, carefully, not breaking the Terrain page visually or technically — a sub-tab of the Terrain button,
Terrain Stats, with more info")."""
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
    assert by["7.22"]["also"][:2] == ["7.22b", "7.22c"] and ts._ranges(by["7.22"]["also"]) == "7.22b–7.22f"
    assert ts._ranges(["7.10"]) == "7.10" and ts._ranges(["7.12", "7.13", "7.13b", "7.14"]) == "7.12, 7.13, 7.13b, 7.14"
    assert ts._ranges(["7.20b", "7.20c", "7.20d"]) == "7.20b–7.20d"
    assert by["7.41"]["n"]["watchers"] == 10 and by["7.41"]["n"]["outposts"] == 2      # lanterns, not outposts
    assert [by["7.41"]["n"][f"tier{t}"] for t in range(4)] == [6, 14, 6, 2]
    assert ts.churn(by["7.38"]["changes"]) == 2069 and ts.churn("no object moved") == 0


def test_the_page_has_tiles_a_chart_and_the_table_under_terrain():
    files = ts.load()
    table = ts.table_html(files, {"7.41", "7.40"})
    assert table.count("<tr>") == 66                                  # the head + 65 map files
    assert table.index(">7.41f<") < table.index(">7.08<")              # newest first
    assert '<a href="terrain_741.html">7.41</a>' in table and '<a href="terrain_739.html">' not in table
    assert 'class="ts-delta ts-up">+20<' in table                      # 7.41: trees 2456 -> 2476
    assert "Towers" not in table                                       # always 22: no column
    chart = ts.chart_svg(files)
    assert chart.count('class="ts-mark"') == 5 and ">7.33 ±3416<" in chart
    groups = {g[0]: g for g in site.MATERIALS_GROUPS}
    assert [c[0] for c in groups["terrain_grp"][3]] == ["terrain", "terrain_stats"]
    nav = site.render_materials_subnav("terrain_stats")
    assert 'href="terrain_stats.html">Terrain Stats</a>' in nav


def test_terrain_pages_never_delete_the_stats_page():
    src = open(os.path.join(_ROOT, "builders", "terrain.py"), encoding="utf-8").read()
    assert '"terrain_[0-9]*.html"' in src and '"terrain_*.html"' not in src
    assert not [f for f in glob.glob(os.path.join(_ROOT, "dist", "terrain_[0-9]*.html")) if "stats" in f]
    css = open(os.path.join(_ROOT, "styles.css"), encoding="utf-8").read()
    block = css.split("/* ---- Terrain Stats", 1)[1].split("a.ts-pic:hover", 1)[0]
    for line in block.splitlines():                                   # every rule scoped to the page or its parts
        if line.startswith(".") and "{" in line:
            assert line.startswith((".terrain-stats-page", ".ts-chart", ".ts-table")), line
