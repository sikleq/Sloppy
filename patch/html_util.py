"""The small things every page transform does with markup, in one place (code audit 2026-11-10: the end of a <div>
was found by four copies that already differed on broken markup, tags were stripped by one regex written 67 times).

Imports nothing of the project: any module may use it.
"""
import re

TAG_RE = re.compile(r"<[^>]+>")
_DIV_RE = re.compile(r"<div\b|</div>")


def strip_tags(html):
    """The text with every tag taken out, nothing else touched (spaces, entities stay)."""
    return TAG_RE.sub("", html)


def plain(html):
    """The text a reader sees: tags out, runs of spaces as one, no space at the ends."""
    return re.sub(r"\s+", " ", TAG_RE.sub("", html)).strip()


def div_end(html, start, strict=False):
    """The index just past the </div> that closes the <div opening at `start`. Markup that never closes it: the end of
    the text, or ValueError with `strict` (a card cut at a wrong place must not pass for a card)."""
    depth = 0
    for m in _DIV_RE.finditer(html, start):
        depth += 1 if m.group() == "<div" else -1
        if depth == 0:
            return m.end()
    if strict:
        raise ValueError("unclosed <div>")
    return len(html)
