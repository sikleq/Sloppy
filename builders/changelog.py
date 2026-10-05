"""Site changelog page (dist/changelog.html) from data/changelog.json.

Short notes on what changed on the SITE (not Dota patches): newest first, grouped by
date, each entry with a category chip, 1-4 points, an optional link to the changed
page and optional screenshots (icons/changelog/*.webp, tools/changelog_shots.py) beside the notes.
Left rail (fixed, centred on the left edge, faint until hovered) = the FEATURE titles by month
(small changes are not listed there); fixes ("fix": true) get a pixel-beetle marker;
category chips filter the entries.
"""
import datetime as _dt
import json as _json
import os as _os
import re as _re
import sys as _sys

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _HERE not in _sys.path:
    _sys.path.insert(0, _HERE)

import builders.site_common as _site  # noqa: E402

DATA = _os.path.join(_HERE, "data", "changelog.json")
# what a change is about (the owner 2026-10-03: "not Materials but Terrain, not Materials but Heroes")
CATEGORIES = ["Patch Reader", "Terrain", "Heroes", "Items", "Units", "Tables", "Hero Lab", "Dynamics", "Site"]
FIRST_SHOWN = 5          # features shown before "Show more" (the owner 2026-10-04: "only the last 5 news")


_esc = _site.esc


# hero names in the notes become the hero's small picture (the owner 2026-10-03: "where there are hero names, put
# their small icons instead") — "Mirana's Shard" -> [Mirana] Shard; short forms the notes use map to the full name
_HERO_ALIASES = {"Treant": "Treant Protector"}
_HERO_RE = None


def _hero_re():
    global _HERO_RE
    if _HERO_RE is None:
        from patch.images import HERO_SLUG
        names = sorted(set(HERO_SLUG) | set(_HERO_ALIASES), key=len, reverse=True)
        _HERO_RE = (_re.compile(r"(?<![\w'’-])(" + "|".join(map(_re.escape, names)) + r")(?:'s|’s)?(?![\w-])"),
                    HERO_SLUG)
    return _HERO_RE


# a button / filter / icon a note adds is shown as its picture, not named (the owner 2026-10-03: "if we add a
# button, a filter or an icon, put that icon there instead of text when there is no screenshot") — in the text as
# [[icons/ui/gothic/tc_all.png|All layers]]
_UI_ICON_RE = _re.compile(r"\[\[([\w./-]+\.(?:png|svg|webp))\|([^\]]+)\]\]")


def _rich(text):
    """The note's text, escaped: its [[icon|name]] marks as the icon, its hero names as their portraits."""
    out, pos = [], 0
    for m in _UI_ICON_RE.finditer(text):
        out.append(_heroes(text[pos:m.start()]))
        out.append(f'<img class="clog-ui" src="{_esc(m.group(1))}" alt="{_esc(m.group(2))}" width="16" height="16" '
                   f'loading="lazy" decoding="async">')
        pos = m.end()
    out.append(_heroes(text[pos:]))
    return "".join(out)


def _plain(text):
    """The text with each [[icon|name]] as its name (the rail, anchors, alt texts)."""
    return _UI_ICON_RE.sub(lambda m: m.group(2), text)


def _heroes(text):
    """Escaped text with every hero name as the hero's small picture (alt = the name)."""
    rx, slugs = _hero_re()
    out, pos = [], 0
    for m in rx.finditer(text):
        name = _HERO_ALIASES.get(m.group(1), m.group(1))
        out.append(_esc(text[pos:m.start()]))
        out.append(f'<img class="clog-hero" src="icons/heroes/{slugs[name]}.png" alt="{_esc(name)}" width="28" '
                   f'height="16" loading="lazy" decoding="async">')
        pos = m.end()
    out.append(_esc(text[pos:]))
    return "".join(out)


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
        if not e.get("minor") and not e.get("items"):
            raise ValueError(f"changelog: a feature entry needs items ({e['title']})")
        if e["category"] not in CATEGORIES:
            raise ValueError(f"changelog: unknown category {e['category']!r} ({e['title']})")
    return sorted(entries, key=lambda e: e["date"], reverse=True)


BUG_ICON = "icons/ui/gothic/icon_bug.png"


def _bug_html(e):
    """Fixes of something that was wrong ("fix": true) carry a small pixel beetle beside the chip.
    The cell is there even without a beetle, so every title starts on the same vertical line."""
    bug = (f'<img class="clog-bug" src="{BUG_ICON}" width="13" height="13" alt="Fix" '
           'title="Fix: something was wrong and now works">') if e.get("fix") else ""
    return f'<span class="clog-bugcell">{bug}</span>'


def _cat_html(e):
    return f'<span class="clog-catcell"><span class="clog-cat clog-cat-{_slug(e["category"])}">{_esc(e["category"])}</span></span>'


def _entry_html(e, minor=""):
    """One feature; `minor` = the day's small changes, under its items (the day's last feature carries them — the
    owner 2026-10-03: "move it up to the topic, not a separate news item behind a line")."""
    items = "".join(f"<li>{_rich(x)}</li>" for x in e.get("items", []))
    title = (f'<a class="clog-title-link" href="{_esc(e["link"])}">{_rich(e["title"])}</a>'
             if e.get("link") else _rich(e["title"]))
    shots = _shots_html(e)
    cls = "clog-entry has-shots" if shots else "clog-entry"
    return (f'<article class="{cls}" id="{_entry_id(e)}" data-cat="{_slug(e["category"])}"><div class="clog-text">'
            f'<div class="clog-entry-head">{_cat_html(e)}{_bug_html(e)}<h3 class="clog-title">{title}</h3></div>'
            f'<ul class="clog-items">{items}</ul>{minor}</div>{shots}</article>')


def _entry_id(e):
    return f'e-{e["date"]}-{_slug(_plain(e["title"]))}'


def _shots_html(e):
    """One screenshot = a plain image; 2+ = a carousel: one slide at a time, arrows,
    dots and an "n / N" counter (scripts.js "SITE CHANGELOG")."""
    paths = [p for p in e.get("shots", []) if _os.path.exists(_os.path.join(_HERE, p))]
    if not paths:
        return ""
    slides = "".join(
        f'<a class="clog-shot{" is-active" if i == 0 else ""}" href="{_esc(p)}" data-zoom>'
        f'<img src="{_esc(p)}" alt="{_esc(_plain(e["title"]))} — {i + 1}" loading="lazy"></a>'
        for i, p in enumerate(paths))
    if len(paths) == 1:
        return f'<div class="clog-shots">{slides}</div>'
    dots = "".join(f'<button class="clog-dot{" is-active" if i == 0 else ""}" data-i="{i}" '
                   f'aria-label="Screenshot {i + 1}"></button>' for i in range(len(paths)))
    return (f'<div class="clog-shots clog-carousel" data-n="{len(paths)}">'
            f'<div class="clog-slides">{slides}</div>'
            '<div class="clog-car-bar">'
            '<button class="clog-car-btn is-prev" data-step="-1" aria-label="Previous screenshot"></button>'
            f'<span class="clog-car-mid"><span class="clog-dots">{dots}</span>'
            f'<span class="clog-car-count">1 / {len(paths)}</span></span>'
            '<button class="clog-car-btn is-next" data-step="1" aria-label="Next screenshot"></button>'
            '</div></div>')


MINOR_OPEN_MAX = 3            # a day's small changes: up to 3 shown as a list, more fold under a toggle


def _minor_html(date, minors, after_features=True):
    """Small changes of one day ("minor": true) continue the day's list — no heading of their own (the owner
    2026-10-03: "don't set smaller changes apart from the main changes, just 'show N more changes' at the end"):
    up to MINOR_OPEN_MAX are listed as they are, more fold under "Show N more changes" (just "Show N changes" on a
    day without features). scripts.js keeps N to the rows the category filter leaves."""
    # Chip | beetle | text columns with faint row lines (owner 2026-09-26): the text always starts at one x.
    lis = "".join(
        f'<li data-cat="{_slug(e["category"])}">{_cat_html(e)}{_bug_html(e)}<span class="clog-minor-txt">'
        + (f'<a href="{_esc(e["link"])}">{_rich(e["title"])}</a>' if e.get("link") else _rich(e["title"]))
        + '</span></li>'
        for e in minors)
    if len(minors) <= MINOR_OPEN_MAX:
        return f'<div class="clog-minor" id="m-{date}"><ul class="clog-minor-list">{lis}</ul></div>'
    more = " more" if after_features else ""
    return (f'<details class="clog-minor" id="m-{date}"><summary class="clog-minor-more">'
            f'<span class="clog-more-show">Show <span class="clog-minor-n">{len(minors)}</span>{more} '
            f'change<span class="clog-minor-s">s</span></span>'
            f'<span class="clog-more-hide">Show fewer</span></summary>'
            f'<ul class="clog-minor-list">{lis}</ul></details>')


def _one_link_per_patch(group):
    """A day's entries link to the same page only once (owner 2026-09-26): the first entry keeps the
    link, later ones with the same link are shown as plain text. Copies, the data is not changed."""
    seen, out = set(), []
    for e in group:
        link = e.get("link")
        if link and link in seen:
            e = {k: v for k, v in e.items() if k != "link"}
        elif link:
            seen.add(link)
        out.append(e)
    return out


def render(entries):
    by_date = {}
    for e in entries:
        by_date.setdefault(e["date"], []).append(e)
    days, rail, month_seen = [], [], None
    for date, group in by_date.items():
        group = _one_link_per_patch(group)
        d = _dt.date.fromisoformat(date)
        month = d.strftime("%B %Y")
        if month != month_seen:
            rail.append(f'<div class="clog-rail-month">{month}</div>')
            month_seen = month
        cats = " ".join(sorted({_slug(e["category"]) for e in group}))
        majors = [e for e in group if not e.get("minor")]
        minors = [e for e in group if e.get("minor")]
        rail.extend(f'<a class="clog-rail-item" href="#{_entry_id(e)}" data-cat="{_slug(e["category"])}">'
                    f'{_esc(_plain(e["title"]))}</a>' for e in majors)
        # small changes are not listed in the rail — it names only the features
        minor = _minor_html(date, minors, bool(majors)) if minors else ''
        body = ("".join(_entry_html(e, minor if i == len(majors) - 1 else "") for i, e in enumerate(majors))
                if majors else minor)
        days.append(f'<section class="clog-day" id="d-{date}" data-cats="{cats}">'
                    f'<h2 class="clog-date">{d.strftime("%b")} {d.day}, {d.year}</h2>{body}</section>')
    used = {e["category"] for e in entries}
    chips = '<button class="clog-chip active" data-cat="">All</button>' + "".join(
        f'<button class="clog-chip" data-cat="{_slug(c)}">{_esc(c)}</button>' for c in CATEGORIES if c in used)
    # the newest FIRST_SHOWN features show, the rest come FIRST_SHOWN at a time under "Show more" (scripts.js
    # "SITE CHANGELOG"; without scripts everything shows and the button stays hidden)
    more = (f'<div class="clog-more-wrap"><button type="button" class="clog-chip clog-more-btn" '
            f'data-step="{FIRST_SHOWN}" hidden>Show more</button></div>')
    return (f'<div class="clog-layout"><nav class="clog-rail" aria-label="Changes">{"".join(rail)}</nav>'
            f'<div class="clog-main"><div class="clog-chips" role="toolbar" aria-label="Category">{chips}</div>'
            f'{"".join(days)}{more}</div></div>')


def build():
    entries = load_entries()
    asset_v = _site.compute_asset_version()
    nav = _site.render_top_nav("changelog", _latest_href())
    page = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<title>SIKLE | Changelog</title>\n'
        + _site.head_common() +
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
