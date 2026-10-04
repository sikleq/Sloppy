"""Terrain Stats page (dist/terrain_stats.html): the map history 7.08 → now — every map file Valve shipped, what stood
on it and what changed — from data/map/map_history.json (scripts/gen/map_history_table.py, out of Oldgrowth).

Why (the owner 2026-10-04): the Oldgrowth table "could be added somewhere, carefully, not breaking the Terrain page
visually or technically — a sub-tab of the Terrain button, Terrain Stats, with more info". A page of its own under
Materials ▸ Terrain: summary tiles, a chart of the trees over the years (the big reworks marked, every point's value
on hover), and one row per map file — the patches that shipped it, every kind of object with what was added (green),
removed (red) and moved (yellow) since the file before, a little square of the map linking to its picture. Static
HTML + inline SVG, the hover in CSS, no script of its own.
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
OG_REPO = "https://github.com/sikleq/Oldgrowth"
OG_PAGES = "https://sikleq.github.io/Oldgrowth/versions/"
ASSET_VERSION = _site.compute_asset_version()
# (key, label, icon) — every kind of object (camp spawn boxes left out: the column was nearly always empty, the owner
# 2026-10-04)
COLUMNS = (
    ("trees", "Trees", "ui/gothic/tc_trees"),
    ("camps", "Camps", "camps/creepcamp_mid"),
    ("tier0", "Small", "camps/creepcamp_small"),
    ("tier1", "Medium", "camps/creepcamp_mid"),
    ("tier2", "Large", "camps/creepcamp_big"),
    ("tier3", "Ancient", "camps/creepcamp_ancient"),
    ("towers", "Towers", "ui/gothic/tc_towers"),
    ("outposts", "Outposts", "ui/gothic/tc_outposts"),
    ("watchers", "Watchers", "ui/gothic/tc_watchers"),
    ("lotus", "Lotus pools", "ui/gothic/tc_lotus"),
    ("wisdom", "Wisdom", "ui/gothic/tc_wisdom"),
    ("gates", "Twin Gates", "ui/gothic/tc_twingates"),
    ("bounty", "Bounty runes", "ui/gothic/tc_bounty"),
    ("power", "Power runes", "ui/gothic/tc_power"),
    ("shrines", "Shrines", "ui/gothic/tc_shrines"),
    ("roshan", "Roshan pits", "ui/gothic/tc_roshan"),
    ("tormentors", "Tormentors", "ui/gothic/tc_tormentors"),
)
MARKS = 5                     # the files that moved the most trees, labelled on the chart


def _esc(s):
    return _html.escape(str(s), quote=True)


def _key(v):
    m = _re.match(r"(\d+)\.(\d+)([a-z]?)", v)
    return int(m.group(1)), int(m.group(2)), m.group(3)


def _icon(path, size=16):
    return f'<img src="icons/{path}.png" alt="" width="{size}" height="{size}">'


def short_date(iso):
    """2026-09-15 -> 15-09-26 (the owner 2026-10-04: dd-mm-yy)."""
    return _dt.date.fromisoformat(iso).strftime("%d-%m-%y") if iso else ""


def load():
    """[map file] oldest first: {"patch", "date", "sha8", "n", "moves", "also": [patches with the same file]}."""
    with open(DATA, encoding="utf-8") as f:
        rows = _json.load(f)["patches"]
    files, by = [], {}
    for r in sorted(rows, key=lambda r: _key(r["patch"])):
        if "n" in r:
            n = dict(r["n"])
            for t, v in enumerate(n.pop("camp_tiers")):
                n[f"tier{t}"] = v
            f = {**r, "n": n, "moves": r.get("moves", {}), "also": []}
            files.append(f)
            by[r["patch"]] = f
        elif r.get("same_as") in by:
            by[r["same_as"]]["also"].append(r["patch"])
    return files


def group(files):
    """Map files with nothing different from the one before — the same counts, nothing moved (7.41c … 7.41f) — share
    the earlier file's row (the owner 2026-10-04: "versions that don't differ at all — glue them, no value changes")."""
    rows = []
    for f in files:
        if rows and not f["moves"] and f["n"] == rows[-1]["n"]:
            rows[-1] = {**rows[-1], "also": rows[-1]["also"] + [f["patch"]] + f["also"]}
        else:
            rows.append(f)
    return rows


def churn(f):
    """Trees added + removed in a map file (7.38: +1017 −1052 → 2069)."""
    t = f["moves"].get("trees", {})
    return t.get("add", 0) + t.get("rem", 0)


def _tile(icon, num, name, delta=None, href=None):
    d = ""
    if delta:
        cls = "tm-add-text" if delta > 0 else "tm-rem-text"
        d = f' <span class="{cls}">{"+" if delta > 0 else "−"}{abs(delta)}</span>'
    inner = f'<div class="tf-num">{_icon(icon) if icon else ""}{_esc(num)}</div><div class="tf-name">{_esc(name)}{d}</div>'
    if href:          # a tile that is a link wears the site's dotted underline
        return f'<a class="tf-tile ts-tile-link" href="{_esc(href)}">{inner}</a>'
    return f'<div class="tf-tile">{inner}</div>'


def tiles_html(files, n_patches):
    first, last = files[0], files[-1]
    return ('<div class="tf-tiles ts-tiles">'
            + _tile(None, n_patches, "patches")
            + _tile(None, len(files), "map files", href=OG_REPO)
            + _tile(None, f"{first['patch']} → {last['patch']}", f"{first['date'][:4]} – {last['date'][:4]}")
            + _tile("ui/gothic/tc_trees", last["n"]["trees"], f"trees since {first['patch']}",
                    last["n"]["trees"] - first["n"]["trees"])
            + _tile("camps/creepcamp_mid", last["n"]["camps"], f"camps since {first['patch']}",
                    last["n"]["camps"] - first["n"]["camps"])
            + '</div>')


def chart_svg(files, w=1300, h=260):
    """Trees on the map over the years: a step line on a faint grid (a line per 100 trees and per year), one point
    per map file — its value shows on hover — and the files that moved the most trees labelled with what they
    added and removed."""
    pad_l, pad_r, pad_t, pad_b = 52, 20, 34, 28
    dates = [_dt.date.fromisoformat(f["date"]) for f in files]
    t0, t1 = dates[0].toordinal(), dates[-1].toordinal()
    ys = [f["n"]["trees"] for f in files]
    lo, hi = (min(ys) // 100) * 100 - 100, (max(ys) // 100 + 1) * 100 + 100
    right, bottom = w - pad_r, h - pad_b

    def X(d):
        return round(pad_l + (d.toordinal() - t0) / max(1, t1 - t0) * (right - pad_l), 1)

    def Y(v):
        return round(pad_t + (hi - v) / (hi - lo) * (bottom - pad_t), 1)
    parts = []
    for v in range(lo, hi + 1, 100):                                    # horizontal grid, every 100 trees
        major = v % 200 == 0
        parts.append(f'<line class="ts-grid{" ts-grid-major" if major else ""}" x1="{pad_l}" x2="{right}" '
                     f'y1="{Y(v)}" y2="{Y(v)}"/>')
        if major:
            parts.append(f'<text class="ts-ylab" x="{pad_l - 8}" y="{Y(v) + 4}">{v}</text>')
    for year in range(dates[0].year, dates[-1].year + 2):              # vertical grid, every year
        x = X(_dt.date(year, 1, 1))
        if pad_l <= x <= right:
            parts.append(f'<line class="ts-grid ts-grid-major" x1="{x}" x2="{x}" y1="{pad_t}" y2="{bottom}"/>'
                         f'<text class="ts-xlab" x="{x}" y="{h - 8}">{year}</text>')
    parts.append(f'<line class="ts-axis" x1="{pad_l}" x2="{pad_l}" y1="{pad_t}" y2="{bottom}"/>'
                 f'<line class="ts-axis" x1="{pad_l}" x2="{right}" y1="{bottom}" y2="{bottom}"/>')
    d = [f"M{X(dates[0])} {Y(ys[0])}"]
    for i in range(1, len(files)):
        d.append(f"H{X(dates[i])}V{Y(ys[i])}")
    d.append(f"H{right}")
    parts.append(f'<path class="ts-line" d="{"".join(d)}"/>')
    top = set(sorted(range(len(files)), key=lambda i: churn(files[i]), reverse=True)[:MARKS])
    labels, points = [], []
    for i, (f, dt) in enumerate(zip(files, dates)):
        x, y = X(dt), Y(ys[i])
        big = i in top and churn(f)
        if big:              # the version only, on a plate the line never cuts (the owner: no "+1838 −1578" there)
            lw = 14 + len(f["patch"]) * 7.5
            ly = y - 30 if y - 30 > 6 else y + 12
            lx = min(max(x - lw / 2, pad_l + 2), right - lw - 2)
            labels.append(f'<g class="ts-mark"><rect x="{lx}" y="{ly}" width="{lw}" height="20" rx="3"/>'
                          f'<text x="{lx + lw / 2}" y="{ly + 14}">{_esc(f["patch"])}</text></g>')
        # hover: the point grows and shows its tree count only (CSS :hover on the group; a wide invisible target)
        tip = f"{f['patch']} · {ys[i]}"          # the version and its tree count (the owner: "bring the versions back")
        tw = 14 + len(tip) * 7
        tx = min(max(x - tw / 2, pad_l + 2), right - tw - 2)
        ty = y + 14 if y - 30 < pad_t else y - 30
        points.append(f'<g class="ts-pt"><circle class="ts-hit" cx="{x}" cy="{y}" r="9"/>'
                      f'<circle class="ts-dot{" ts-dot-big" if big else ""}" cx="{x}" cy="{y}" r="{4 if big else 2.6}"/>'
                      f'<g class="ts-tip"><rect x="{tx}" y="{ty}" width="{round(tw, 1)}" height="20" rx="3"/>'
                      f'<text x="{tx + tw / 2}" y="{ty + 14}">{_esc(tip)}</text></g></g>')
    parts += labels + points                     # points last: a hovered value lies over the labels
    return (f'<svg class="ts-chart" viewBox="0 0 {w} {h}" role="img" aria-label="Trees on the map, '
            f'{files[0]["patch"]} to {files[-1]["patch"]}">{"".join(parts)}</svg>')


def _change(f, prev, key):
    """What changed in this kind of object since the file before: the result of what was added and removed ('+20',
    green up / red down, '±0' when as many went as came), '7 moved' (yellow), or the bare difference of the counts
    when the file's own list says nothing (a camp tier)."""
    m = f["moves"].get(key, {})
    out = []
    if m.get("add") or m.get("rem"):        # the result, not both halves (the owner: "not +734 −548 — +186")
        net = m.get("add", 0) - m.get("rem", 0)
        out.append(f'<span class="{"ts-up" if net > 0 else "ts-down" if net < 0 else "ts-zero"}">'
                   f'{"+" if net > 0 else "−" if net < 0 else "±"}{abs(net)}</span>')
    elif prev is not None and key in f["n"] and prev.get(key) is not None and f["n"][key] != prev[key]:
        diff = f["n"][key] - prev[key]
        out.append(f'<span class="{"ts-up" if diff > 0 else "ts-down"}">{"+" if diff > 0 else "−"}{abs(diff)}</span>')
    for kind in ("moved", "changed"):
        if m.get(kind):
            out.append(f'<span class="ts-moved">{m[kind]} {kind}</span>')
    if key == "camps" and f["moves"].get("camp_tiers", {}).get("changed"):
        out.append(f'<span class="ts-moved">{f["moves"]["camp_tiers"]["changed"]} re-tiered</span>')
    return " ".join(out)


def _cell(f, prev, key):
    v = f["n"].get(key)
    change = _change(f, prev, key)
    count = "" if v is None else str(v)
    if not change:
        return f"<td>{count}</td>"
    return f'<td class="ts-changed">{count}<span class="ts-delta">{change}</span></td>'


def table_html(files, pages):
    head = ('<th class="ts-file"><span>Map version</span></th><th><span>Date</span></th>'
            + "".join(f'<th>{_icon(icon)}<span>{_esc(label)}</span></th>' for _k, label, icon in COLUMNS)
            + '<th><span>Map</span></th>')
    rows, prev = [], None
    for f in group(files):
        ver = f["patch"]
        link = (f'<a href="{_terrain._terrain_filename(ver)}">{_esc(ver)}</a>' if ver in pages else _esc(ver))
        # the versions it covers as a range, first – last (the owner: "7.35 – 7.37e is easier than listing them")
        also = f'<span class="ts-range"> – {_esc(f["also"][-1])}</span>' if f["also"] else ""
        cells = "".join(_cell(f, prev, k) for k, _l, _i in COLUMNS)
        thumb = (f'<a class="ts-thumb" href="{OG_PAGES}{_esc(ver)}/map.webp" aria-label="The {_esc(ver)} map">'
                 f'<img src="icons/maps/thumbs/{_esc(f["sha8"])}.webp" alt="" width="28" height="28" loading="lazy" '
                 f'decoding="async"></a>')
        rows.append(f'<tr><td class="ts-file">{link}{also}</td><td class="ts-date">{short_date(f["date"])}</td>'
                    f'{cells}<td>{thumb}</td></tr>')
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
