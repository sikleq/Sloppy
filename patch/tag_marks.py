"""Pages with the rows' tags as small tiles (body.tag-marks, patch/page.py TAG_MARK_PAGES, src/css/patch-tag-marks.css):
what the page needs written into it when it is saved."""
import re

from .badges import t

# a row's data-tag words, the kind first: NEW carries "buff new", DEL "del nerf" (the filters' aliases)
_KINDS = ("new", "rework", "swap", "del", "qol", "misc")
_NAMES = {"new": "NEW", "rework": "REWORK", "swap": "SWAP", "del": "DEL", "qol": "QoL", "misc": "MISC",
          "buff": "BUFF", "nerf": "NERF"}
_TERRAIN_ROW_RE = re.compile(r'<li\b([^>]*)><span class="badge tnum[^"]*">(\d+)</span><span class="row-text">')


def row_kinds(data_tag):
    """The tags a row shows from its data-tag: its kinds (NEW, DEL, ...), else BUFF / NERF."""
    words = (data_tag or "").split()
    kinds = [w for w in words if w in _KINDS]
    return kinds or [w for w in words if w in ("buff", "nerf")][:1]


def terrain_rows_tagged(html):
    """A terrain row's number chip in the tag's place (owner 2026-10-03) gives that place back to the tag, now a tile;
    the number goes (owner 2026-11-06: "отказываемся от нумерации в подобных случаях")."""
    def one(m):
        attrs = m.group(1)
        tag = re.search(r'\bdata-tag="([^"]*)"', attrs)
        kinds = row_kinds(tag.group(1)) if tag and 'terrain-row' in attrs else []
        if not kinds:
            return m.group(0)
        return f'<li{attrs}>{t(_NAMES[kinds[0]])}<span class="row-text">'
    return _TERRAIN_ROW_RE.sub(one, html)
