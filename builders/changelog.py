"""Site changelog page (dist/changelog.html) from data/changelog.json.

Short notes on what changed on the SITE (not Dota patches): newest first, grouped by
date, each entry with a category chip, 1-4 points, an optional link to the changed
page and optional screenshots (icons/changelog/*.webp, tools/changelog_shots.py) beside the notes.
Left rail = month / date navigation; category chips filter the entries.
"""
import datetime as _dt
import html as _html
import json as _json
import os as _os
import sys as _sys

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _HERE not in _sys.path:
    _sys.path.insert(0, _HERE)

import builders.site_common as _site  # noqa: E402

DATA = _os.path.join(_HERE, "data", "changelog.json")
CATEGORIES = ["Patch Reader", "Materials", "Hero Lab", "Dynamics", "Site"]


def _esc(s):
    return _html.escape(str(s), quote=True)


def _slug(s):
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-")


def _latest_href():
    ver = _site.get_latest_version()
    return f"patches/{ver}.html" if ver else "calendar.html"


def load_entries(path=DATA):
    with open(path, encoding="utf-8") as f:
        entries = _json.load(f)["entries"]
    for e in entries:
        _dt.date.fromisoformat(e["date"])                  # fail fast on a bad date
        if e["category"] not in CATEGORIES:
            raise ValueError(f"changelog: unknown category {e['category']!r} ({e['title']})")
    return sorted(entries, key=lambda e: e["date"], reverse=True)


def _entry_html(e):
    items = "".join(f"<li>{_esc(x)}</li>" for x in e.get("items", []))
    link = (f'<a class="clog-open" href="{_esc(e["link"])}">Open page &rarr;</a>'
            if e.get("link") else "")
    shots = "".join(
        f'<a class="clog-shot" href="{_esc(p)}" target="_blank" rel="noopener">'
        f'<img src="{_esc(p)}" alt="{_esc(e["title"])}" loading="lazy"></a>'
        for p in e.get("shots", []) if _os.path.exists(_os.path.join(_HERE, p)))
    cls = "clog-entry has-shots" if shots else "clog-entry"
    return (f'<article class="{cls}" data-cat="{_slug(e["category"])}"><div class="clog-text">'
            f'<div class="clog-entry-head"><span class="clog-cat clog-cat-{_slug(e["category"])}">'
            f'{_esc(e["category"])}</span><h3 class="clog-title">{_esc(e["title"])}</h3></div>'
            f'<ul class="clog-items">{items}</ul>{link}</div>'
            + (f'<div class="clog-shots">{shots}</div>' if shots else '') + '</article>')


def render(entries):
    by_date = {}
    for e in entries:
        by_date.setdefault(e["date"], []).append(e)
    days, rail, month_seen = [], [], None
    for date, group in by_date.items():
        d = _dt.date.fromisoformat(date)
        month = d.strftime("%B %Y")
        if month != month_seen:
            rail.append(f'<div class="clog-rail-month">{month}</div>')
            month_seen = month
        cats = " ".join(sorted({_slug(e["category"]) for e in group}))
        rail.append(f'<a class="clog-rail-day" href="#d-{date}" data-cats="{cats}">'
                    f'{d.strftime("%b")} {d.day}<span>{len(group)}</span></a>')
        days.append(f'<section class="clog-day" id="d-{date}" data-cats="{cats}">'
                    f'<h2 class="clog-date">{d.strftime("%b")} {d.day}, {d.year}</h2>'
                    + "".join(_entry_html(e) for e in group) + '</section>')
    chips = '<button class="clog-chip active" data-cat="">All</button>' + "".join(
        f'<button class="clog-chip" data-cat="{_slug(c)}">{_esc(c)}</button>' for c in CATEGORIES)
    return (f'<div class="clog-layout"><nav class="clog-rail" aria-label="Dates">{"".join(rail)}</nav>'
            f'<div class="clog-main"><div class="clog-chips" role="toolbar" aria-label="Category">{chips}</div>'
            f'{"".join(days)}</div></div>')


def build():
    entries = load_entries()
    asset_v = _site.compute_asset_version()
    nav = _site.render_top_nav("changelog", _latest_href())
    page = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>SIKLE | Changelog</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={asset_v}">\n'
        '</head>\n<body class="clog-page">\n'
        f'{nav}\n'
        f'<div class="container clog-container">{render(entries)}</div>\n'
        f'<script defer src="src/scripts.js?v={asset_v}"></script>\n'
        '</body>\n</html>\n')
    _os.makedirs(_site.DIST_DIR, exist_ok=True)
    with open(_os.path.join(_site.DIST_DIR, "changelog.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print(f"  -> dist/changelog.html: {len(entries)} entries")


if __name__ == "__main__":
    build()
