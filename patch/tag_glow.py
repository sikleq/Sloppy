"""Shared by the gold (patch/hidden_change.py) and the red (patch/valve_error.py) tag marks: find a row's note in its
[?], cut it out without breaking the markup, and put a glow class and a hover text on the row's tag.

A row's [?] is '<span class="info-tip" tabindex="0">?<span class="info-pop">…</span></span>'; its parts are bare text,
'<span class="pop-part">…</span>' or '<span class="pop-li"><span class="pop-t">…</span></span>', a "Note:" head
('<span class="info-pop-h">Note:</span>') before the text. Spans are matched by nesting, not by regex.
"""
import html as _html
import re

_SPAN = re.compile(r"<span\b[^>]*>|</span>")
_TAG = re.compile(r'<span (?=[^>]*\bclass="[^"]*\bbadge\b)(?=[^>]*\bdata-tag=")([^>]*)>')
# a map row's tag is its diamond (patch/tag_marks.py; 7.42 "Dire base shop moved …")
_DIAMOND = re.compile(r'<span ((?=[^>]*\bclass="tnum-dia\b)[^>]*)>')


def span_end(html, start):
    """The index just after the </span> closing the span that opens at `start`."""
    depth = 0
    for m in _SPAN.finditer(html, start):
        depth += -1 if m.group(0) == "</span>" else 1
        if depth == 0:
            return m.end()
    return len(html)


def _text(fragment):
    return _html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def cut_note(li, marker, keep=None):
    """(li without the note, the note's text) — the note is the [?] part holding `marker` (a regex); its [?] goes
    when nothing else is left in it. (li, None) when no [?] holds it. `keep(note)` → words to leave in the note's
    place ('' or None: nothing)."""
    for tip in [m.start() for m in re.finditer(r'<span class="info-tip"', li)]:
        end = span_end(li, tip)
        pop = li.find('<span class="info-pop">', tip, end)
        if pop < 0:
            continue
        inner_a, inner_b = pop + len('<span class="info-pop">'), span_end(li, pop) - len("</span>")
        inner = li[inner_a:inner_b]
        hit = re.search(marker, inner)
        if not hit:
            continue
        # the part that holds it: a pop-part / pop-li around it, or the whole pop
        a, b = 0, len(inner)
        for m in re.finditer(r'<span class="pop-(?:part|li)">', inner):
            e = span_end(inner, m.start())
            if m.start() < hit.start() < e:
                a, b = m.start(), e
        note = _text(re.sub(r'<span class="info-pop-h">Note:</span>', "", inner[a:b]))
        left = keep(note) if keep else ""
        if left:
            return li[:inner_a] + inner[:a] + _html.escape(left, quote=False) + inner[b:] + li[inner_b:], note
        rest = inner[:a] + inner[b:]
        rest = re.sub(r'<span class="pop-(?:part|li)">\s*</span>', "", rest)
        if not _text(rest):
            return li[:tip] + li[end:], note
        return li[:inner_a] + rest + li[inner_b:], note
    return li, None


def mark_tag(li, cls, tip):
    """The row's tag (the first span.badge with a data-tag — not a % badge) gets `cls`, a hover `tip` and focus (a
    phone's tap, the keyboard); a tag already marked keeps its hover and gets this one after it."""
    m = _TAG.search(li) or _DIAMOND.search(li)
    if not m:
        return li
    attrs = m.group(1)
    old = re.search(r'data-tooltip="([^"]*)"', attrs)
    text = _html.escape(tip, quote=True)
    if old:
        attrs = attrs.replace(old.group(0), f'data-tooltip="{old.group(1)}<br>{text}"', 1)
    else:
        attrs = f'data-tooltip="{text}" tabindex="0" ' + attrs
    attrs = re.sub(r'class="', f'class="{"" if "tb-tip-target" in attrs else "tb-tip-target "}{cls} ', attrs, count=1)
    return li[:m.start()] + f"<span {attrs}>" + li[m.end():]


def has_tag(li):
    """A row with a tag to glow on: no tag (a % badge only), no mark — its [?] keeps the note."""
    return bool(_TAG.search(li) or _DIAMOND.search(li))


def each_row(html, marker, fix):
    """`fix(li)` on every <li> whose text holds `marker` (a regex), the rest of the page untouched."""
    out, pos = [], 0
    for i in [m.start() for m in re.finditer(marker, html)]:
        a, b = max(html.rfind("<li ", 0, i), html.rfind("<li>", 0, i)), html.find("</li>", i)
        if a < pos or b < 0:
            continue
        out += [html[pos:a], fix(html[a:b + 5])]
        pos = b + 5
    return "".join(out) + html[pos:]
