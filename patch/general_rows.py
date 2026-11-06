"""A hero's General list on the saved page: the row of a new main attribute is its first row (owner 2026-11-06: "Если
герой меняет атрибут … всегда ставим вверху списка general"). The generator puts it first in content
(tools/patchgen/post_hero.py); the stats card's damage rows are drawn in its place when the page is saved
(cards_hero_stats.render_hs_card), above it — so the page moves it up again."""
import re

_UL_RE = re.compile(r'(<ul class="changes"[^>]*>)(.*?)(</ul>)', re.S)
_ATTR_MARK = 'row-text">Main attribute changed from <b class="attr-chip'


def attr_row_first(html):
    from .page import _split_top_li

    def one(m):
        if _ATTR_MARK not in m.group(2):
            return m.group(0)
        body = m.group(2)
        _prefix, items, _suffix = _split_top_li(body)
        at = next((k for k, li in enumerate(items) if _ATTR_MARK in li), None)
        if not at:                                  # none of its own (a nested list's) or already first
            return m.group(0)
        row = items[at]
        rest = body.replace(row, "", 1)
        first = rest.index(items[0])                # everything else stays as it was, the row goes before the first
        return m.group(1) + rest[:first] + row + rest[first:] + m.group(3)
    return _UL_RE.sub(one, html)
