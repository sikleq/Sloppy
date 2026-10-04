"""Terrain Stats page (dist/terrain_stats.html): the map history 7.08 → now — every map file Valve shipped, what stood
on it and what moved — from data/map/map_history.json (scripts/gen/map_history_table.py, out of Oldgrowth).

Why (the owner 2026-10-04): the Oldgrowth table "could be added somewhere, carefully, not breaking the Terrain page
visually or technically — a sub-tab of the Terrain button, Terrain Stats, with more info". A page of its own under
Materials ▸ Terrain: summary tiles, a chart of the trees over the years with the big reworks marked, and one row per
map file (the patches that shipped it, its objects with their change from the file before, what moved, links to its
Terrain page and picture). Static HTML + inline SVG, no script of its own.
"""
import datetime as _dt
import html as _html
import json as _json
import os as _os
import re as _re
import sys as _sys

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _HERE not in _sys.path:
    _sys.path.insert(0, _HERE)

import builders.site_common as _site  # noqa: E402
import builders.terrain as _terrain  # noqa: E402

DATA = _os.path.join(_HERE, "data", "map", "map_history.json")
OG_PAGES = "https://sikleq.github.io/Oldgrowth/versions/"
ASSET_VERSION = _site.compute_asset_version()
# (key, label, icon) — the counts that changed over the years (towers are always 22, power runes always 2)
COLUMNS = (
    ("trees", "Trees", "ui/gothic/tc_trees"),
    ("camps", "Camps", "camps/creepcamp_mid"),
    ("tier0", "Small", "camps/creepcamp_small"),
    ("tier1", "Medium", "camps/creepcamp_mid"),
    ("tier2", "Large", "camps/creepcamp_big"),
    ("tier3", "Ancient", "camps/creepcamp_ancient"),
    ("outposts", "Outposts", "ui/gothic/tc_outposts"),
    ("watchers", "Watchers", "ui/gothic/tc_watchers"),
    ("lotus", "Lotus pools", "ui/gothic/tc_lotus"),
    ("wisdom", "Wisdom", "ui/gothic/tc_wisdom"),
    ("gates", "Twin Gates", "ui/gothic/tc_twingates"),
    ("bounty", "Bounty runes", "ui/gothic/tc_bounty"),
    ("shrines", "Shrines", None),
    ("roshan", "Roshan pits", "ui/gothic/tc_roshan"),
    ("tormentors", "Tormentors", "ui/gothic/tc_tormentors"),
)
_CHURN_RE = _re.compile(r"trees \+(\d+) [−-](\d+)")


def _esc(s):
    return _html.escape(str(s), quote=True)


def _key(v):
    m = _re.match(r"(\d+)\.(\d+)([a-z]?)", v)
    return int(m.group(1)), int(m.group(2)), m.group(3)


def load():
    """[map file] oldest first: {"patch", "date", "sha8", "changes", "n", "also": [patches with the same file]}."""
    with open(DATA, encoding="utf-8") as f:
        rows = _json.load(f)["patches"]
    files, by = [], {}
    for r in sorted(rows, key=lambda r: _key(r["patch"])):
        if "n" in r:
            n = dict(r["n"])
            for t, v in enumerate(n.pop("camp_tiers")):
                n[f"tier{t}"] = v
            f = {**r, "n": n, "also": []}
            files.append(f)
            by[r["patch"]] = f
        elif r.get("same_as") in by:
            by[r["same_as"]]["also"].append(r["patch"])
    return files


def _ranges(patches):
    """'7.22b, 7.22c, 7.22d' -> '7.22b–7.22d': runs of consecutive letters of one patch number."""
    out, run = [], []

    def flush():
        if run:
            out.append(run[0] if len(run) == 1 else f"{run[0]}–{run[-1]}")
    for p in patches:
        base, letter = _re.match(r"(\d+\.\d+)([a-z]?)", p).groups()
        if run:
            pb, pl = _re.match(r"(\d+\.\d+)([a-z]?)", run[-1]).groups()
            if pb == base and pl and letter and ord(letter) == ord(pl) + 1:
                run.append(p)
                continue
        flush()
        run = [p]
    flush()
    return ", ".join(out)


def churn(changes):
    """Trees added + removed in a map file (7.38: +1017 −1052 → 2069), 0 when the note says nothing."""
    m = _CHURN_RE.search(changes or "")
    return int(m.group(1)) + int(m.group(2)) if m else 0


def _tile(icon, num, name, delta=None):
    d = ""
    if delta:
        cls = "tm-add-text" if delta > 0 else "tm-rem-text"
        d = f' <span class="{cls}">{"+" if delta > 0 else "−"}{abs(delta)}</span>'
    img = f'<img src="icons/{icon}.png" alt="" width="16" height="16">' if icon else ""
    return f'<div class="tf-tile"><div class="tf-num">{img}{_esc(num)}</div><div class="tf-name">{_esc(name)}{d}</div></div>'


def tiles_html(files, n_patches):
    first, last = files[0], files[-1]
    return ('<div class="tf-tiles ts-tiles">'
            + _tile(None, n_patches, "patches")
            + _tile(None, len(files), "map files")
            + _tile(None, f"{first['patch']} → {last['patch']}", f"{first['date'][:4]} – {last['date'][:4]}")
            + _tile("ui/gothic/tc_trees", last["n"]["trees"], f"trees since {first['patch']}",
                    last["n"]["trees"] - first["n"]["trees"])
            + _tile("camps/creepcamp_mid", last["n"]["camps"], f"camps since {first['patch']}",
                    last["n"]["camps"] - first["n"]["camps"])
            + '</div>')


def chart_svg(files, w=1000, h=230, marks=5):
    """Trees on the map over the years: a step line, one dot per map file, the files that moved the most trees
    labelled ("7.38 ±2069"), a year scale below."""
    pad_l, pad_r, pad_t, pad_b = 46, 16, 26, 26
    dates = [_dt.date.fromisoformat(f["date"]) for f in files]
    t0, t1 = dates[0].toordinal(), dates[-1].toordinal()
    ys = [f["n"]["trees"] for f in files]
    lo, hi = (min(ys) // 100) * 100 - 50, (max(ys) // 100 + 1) * 100 + 50

    def X(d):
        return round(pad_l + (d.toordinal() - t0) / max(1, t1 - t0) * (w - pad_l - pad_r), 1)

    def Y(v):
        return round(pad_t + (hi - v) / (hi - lo) * (h - pad_t - pad_b), 1)
    parts = []
    for v in range((lo // 200 + 1) * 200, hi, 200):                      # grid
        parts.append(f'<line class="ts-grid" x1="{pad_l}" x2="{w - pad_r}" y1="{Y(v)}" y2="{Y(v)}"/>'
                     f'<text class="ts-ylab" x="{pad_l - 6}" y="{Y(v) + 4}">{v}</text>')
    for year in range(dates[0].year + 1, dates[-1].year + 1):           # year scale
        x = X(_dt.date(year, 1, 1))
        parts.append(f'<line class="ts-tick" x1="{x}" x2="{x}" y1="{h - pad_b}" y2="{h - pad_b + 4}"/>'
                     f'<text class="ts-xlab" x="{x}" y="{h - 6}">{year}</text>')
    d = [f"M{X(dates[0])} {Y(ys[0])}"]
    for i in range(1, len(files)):
        d.append(f"H{X(dates[i])}V{Y(ys[i])}")
    d.append(f"H{w - pad_r}")
    parts.append(f'<path class="ts-line" d="{"".join(d)}"/>')
    top = sorted(range(len(files)), key=lambda i: churn(files[i]["changes"]), reverse=True)[:marks]
    for i, (f, dt) in enumerate(zip(files, dates)):
        big = i in top and churn(f["changes"])
        parts.append(f'<circle class="ts-dot{" ts-dot-big" if big else ""}" cx="{X(dt)}" cy="{Y(ys[i])}" '
                     f'r="{4 if big else 2.4}"/>')
        if big:
            parts.append(f'<text class="ts-mark" x="{X(dt)}" y="{Y(ys[i]) - 10}">{_esc(f["patch"])} '
                         f'±{churn(f["changes"])}</text>')
    return (f'<svg class="ts-chart" viewBox="0 0 {w} {h}" role="img" aria-label="Trees on the map, '
            f'{files[0]["patch"]} to {files[-1]["patch"]}">{"".join(parts)}</svg>')


def _cell(n, prev, key):
    v = n[key]
    if prev is None or prev[key] == v:
        return f'<td>{v}</td>'
    diff = v - prev[key]
    cls = "ts-up" if diff > 0 else "ts-down"
    return f'<td class="ts-changed">{v}<span class="ts-delta {cls}">{"+" if diff > 0 else "−"}{abs(diff)}</span></td>'


def table_html(files, pages):
    head = ("<th class=\"ts-file\">Map file</th><th>Date</th>"
            + "".join(f'<th>{f"<img src=\"icons/{icon}.png\" alt=\"\" width=\"16\" height=\"16\">" if icon else ""}'
                      f'<span>{_esc(label)}</span></th>' for _k, label, icon in COLUMNS)
            + "<th class=\"ts-moved\">What moved since the file before</th><th>Map</th>")
    rows, prev = [], None
    for f in files:
        ver = f["patch"]
        link = (f'<a href="{_terrain._terrain_filename(ver)}">{_esc(ver)}</a>' if ver in pages else _esc(ver))
        also = f'<span class="ts-also">also {_esc(_ranges(f["also"]))}</span>' if f["also"] else ""
        cells = "".join(_cell(f["n"], prev, k) for k, _l, _i in COLUMNS)
        rows.append(f'<tr><td class="ts-file">{link}{also}</td><td class="ts-date">{_esc(f["date"])}</td>{cells}'
                    f'<td class="ts-moved">{_esc(f["changes"])}</td>'
                    f'<td><a class="ts-pic" href="{OG_PAGES}{_esc(ver)}/map.webp">picture</a></td></tr>')
        prev = f["n"]
    return ('<div class="ts-table-wrap"><table class="ts-table"><thead><tr>' + head + '</tr></thead><tbody>'
            + "".join(reversed(rows)) + '</tbody></table></div>')


def build():
    files = load()
    with open(DATA, encoding="utf-8") as f:
        n_patches = len(_json.load(f)["patches"])
    pages = set(_terrain.page_patches()[0])
    nav = _site.render_top_nav("materials", _terrain._latest_href(), patch_context=False,
                               subtabs_active="terrain_stats", subnav_in_header=False)
    subnav = _site.render_materials_subnav("terrain_stats")
    page = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>SIKLE | Terrain Stats</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25'
        '&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={ASSET_VERSION}">\n'
        '</head>\n<body>\n'
        f'{nav}\n'
        '<div class="container creeps-page terrain-stats-page">\n<div class="creeps-scroll">\n'
        f'{subnav}'
        '<div class="ts-wrap">\n'
        '<p class="ts-intro">Every map file Valve shipped since 7.08, letter patches included: what stood on it and '
        'what moved. Rendered and counted from the game\'s own files; the pictures and data are open in '
        '<a href="https://github.com/sikleq/Oldgrowth">Oldgrowth</a>.</p>\n'
        f'{tiles_html(files, n_patches)}\n'
        '<div class="tf-head">Trees on the map</div>\n'
        f'{chart_svg(files)}\n'
        '<div class="tf-head">Every map file</div>\n'
        f'{table_html(files, pages)}\n'
        '</div>\n</div>\n</div>\n'
        f'<script defer src="src/scripts.js?v={ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n')
    _os.makedirs(_site.DIST_DIR, exist_ok=True)
    out = _os.path.join(_site.DIST_DIR, "terrain_stats.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"  -> dist/terrain_stats.html: {len(files)} map files, {len(page):,} bytes")


if __name__ == "__main__":
    build()
