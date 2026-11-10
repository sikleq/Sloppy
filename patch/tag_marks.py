"""Pages with the rows' tags as small tiles (body.tag-marks, patch/page.py TAG_MARK_PAGES, src/css/patch-tag-marks.css):
what the page needs written into it when it is saved."""
import re

# a row's data-tag words, the kind first: NEW carries "buff new", DEL "del nerf" (the filters' aliases)
_TERRAIN_ROW_RE = re.compile(r'<li\b([^>]*)><span class="badge tnum(?: tnum-(buff|nerf))?">(\d+)</span>'
                             r'<span class="row-text">(?=(.*?)</li>)', re.S)
# what is the map's ground, not an object on it: removing it is no "removed object"
# (not "water": 7.40 "The watchers … near the small water camps … have been removed" are objects)
_GROUND_RE = re.compile(r'\b(?:trees?|cliffs?|ramps?|walls?|paths?|terrain|ground|bushes|grass)\b', re.I)
_REMOVED_RE = re.compile(r'\b(?:removed|deleted)\b', re.I)


def terrain_tone(attrs, pct_tone, text):
    """The diamond's colour: a row with a % in its colour (7.40 "Watcher night vision range decreased from 800 to 450"
    red), an object taken off the map red (7.38 "Corner outposts have been removed"; trees and cliffs are no objects),
    else gold (owner 2026-11-07: "красим только те ромбики, где удалённые объекты … а также то, что получает
    численные изменения")."""
    if pct_tone:
        return pct_tone
    tag = re.search(r'\bdata-tag="([^"]*)"', attrs)
    plain = re.sub(r'<span class="tshots".*', '', text, flags=re.S)
    plain = re.sub(r'<span class="info-pop">.*?</span>', '', plain, flags=re.S)
    plain = re.sub(r'<[^>]+>', ' ', plain)
    if tag and "del" in tag.group(1).split() and _REMOVED_RE.search(plain) and not _GROUND_RE.search(plain):
        return "nerf"
    return ""


def terrain_rows_tagged(html):
    """A terrain row shows no tag: a small diamond stands in the tag's place, no number (owner 2026-10-03: "the rows
    are just numbered instead of tag chips"; 2026-11-07: "убери теги", then "буквально такие же [ромбики], как ты
    показывал, только золотые. Без цифр" — the coloured row diamonds of the 06.11 mock), gold or its row's colour
    (terrain_tone). The map's number stays for a screen reader; the row's data-tag stays, so the filters find it."""
    def one(m):
        attrs, pct_tone, n, text = m.group(1), m.group(2), m.group(3), m.group(4)
        if 'terrain-row' not in attrs:
            return m.group(0)
        tone = terrain_tone(attrs, pct_tone, text)
        cls = f"tnum-dia tnum-{tone}" if tone else "tnum-dia"
        return f'<li{attrs}><span class="{cls}" role="img" aria-label="{n} on the map"></span><span class="row-text">'
    return _TERRAIN_ROW_RE.sub(one, html)
