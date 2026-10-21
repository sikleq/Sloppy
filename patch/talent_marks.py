"""Talent swap rows marked by what happened to each talent (owner 2026-10-21, Batrider 7.41).

"Level 10 Talent: A replaced with B" reads as one swap, but A and B each have their own fate:
  - A left the tree             -> red (the DEL colour)
  - B is a brand-new talent     -> gold, and the row is tagged NEW instead of SWAP
  - A or B only changed level   -> plain, with a note saying where it went / came from
A talent "moved" when the same talent, numbers aside, stands on the other side of another swap row of the
same hero in the same patch (Batrider 7.41: +4s Smoldering Resin at 20 -> +1s Smoldering Resin at 10).

The swaps of a hero are known only as a whole, so the content file is read once with the AST (hero_header()
and li() calls in source order) the first time one of its talent rows is drawn.
"""
import ast
import os
import re
import sys

SWAP_RE = re.compile(r"^(?:Facet: )?Level (10|15|20|25)(?: Talent)?:? (.+?) replaced with (.+?)\.?$")
_NUM_RE = re.compile(r"[+\-−]?\d+(?:\.\d+)?\s*(?:%|s\b)?")
_cache = {}


def key(talent):
    """The talent without its numbers: "+1s Smoldering Resin Duration" -> "smoldering resin duration"."""
    return re.sub(r"\s+", " ", _NUM_RE.sub(" ", talent)).strip(" :.").lower()


def _swaps_by_hero(path):
    """{hero: [(level, old, new), ...]} of every plain-text talent swap row in a content file."""
    if path in _cache:
        return _cache[path]
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    calls = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.args):
            continue
        a = node.args[0]
        if node.func.id in ("hero_header", "li") and isinstance(a, ast.Constant) and isinstance(a.value, str):
            calls.append((node.lineno, node.col_offset, node.func.id, a.value))
    out, hero = {}, None
    for _, _, fn, text in sorted(calls):
        if fn == "hero_header":
            hero = text
            continue
        m = SWAP_RE.match(text)
        if m and hero:
            out.setdefault(hero, []).append((int(m.group(1)), m.group(2).strip(), m.group(3).strip()))
    _cache[path] = out
    return out


def _content_file():
    f = sys._getframe(1)
    while f:
        fn = f.f_code.co_filename
        if os.sep + "content" + os.sep in fn and os.path.basename(fn).startswith("p"):
            return fn
        f = f.f_back
    return None


def mark(text, hero):
    """(old_fate, new_fate, note) for a talent swap row, or None when the row isn't one.
    Fates: "gone" / "moved" for the old talent, "fresh" / "moved" for the new one."""
    m = SWAP_RE.match(text)
    path = _content_file()
    if not m or not hero or not path:
        return None
    level, old, new = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
    swaps = _swaps_by_hero(path).get(hero, [])
    came = next(((lv, o) for lv, o, _ in swaps if lv != level and key(o) == key(new)), None)
    went = next(((lv, n) for lv, _, n in swaps if lv != level and key(n) == key(old)), None)
    notes = []
    if came:
        notes.append(f"{new} moved from Level {came[0]}, where it was {came[1]}")
    if went:
        notes.append(f"{old} moved to Level {went[0]} as {went[1]}")
    return ("moved" if went else "gone", "moved" if came else "fresh", ". ".join(notes))
