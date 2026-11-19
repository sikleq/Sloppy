"""Terrain Changes: the rows for what the map file changed and no row of Valve's says (owner 2026-11-19, 7.42: "Terrain
Changes нет большинства показанных изменений" — the Terrain page's chips showed couriers, streams, no-ward ground the
patch page never named). The facts come from data/terrain/terrain_diff_<version>.json (scripts/gen/build_terrain_diff.py)."""
import json
import math
import os
import re

from .post_stats import _py_str

_DIFF = os.path.join(os.path.dirname(__file__), "..", "..", "data", "terrain", "terrain_diff_{}.json")
_NOTE = "Not in the patch notes: found in the game files"
_TERRAIN_HEAD_RE = re.compile(r'^\s*W\(plain_header\("Terrain Changes"')
_BLOCK_RE = re.compile(r'^\s*W\((?:plain_header|section)\(|^\s*# =====')
_ROW_TEXT_RE = re.compile(r'\bli\("((?:[^"\\]|\\.)*)"')


def _side(x, y):
    return "Dire" if x + y > 0 else "Radiant"


def _span(values):
    lo, hi = min(values), max(values)
    return f"{lo}" if lo == hi else f"{lo}–{hi}"


def _moves(old, new):
    """{side: [distances]} of points that moved, paired in the file's order."""
    out = {}
    for a, b in zip(old, new):
        d = round(math.dist(a, b))
        if d >= 16:                                   # below that: the file's rounding, not a move
            out.setdefault(_side(*b), []).append(d)
    return out


def _sides_text(moves):
    return ", ".join(f"{side} {_span(ds)} units" for side, ds in sorted(moves.items()))


def map_file_rows(diff):
    """[(regex of the words a note would use, row text)] of the map file's changes a reader should know: spawn points, couriers,
    the stash, stream currents, no-ward ground."""
    e, rows = diff.get("entities", {}), []
    hero = _moves(e.get("heroSpawns", {}).get("old", []), e.get("heroSpawns", {}).get("new", []))
    # the words a note would use, as whole words ("ward" is not in "toward")
    if hero:
        rows.append((r"\bhero spawn points?\b", f"Hero spawn points moved: {_sides_text(hero)}"))
    cour = _moves(e.get("couriers", {}).get("old", []), e.get("couriers", {}).get("new", []))
    if cour:
        rows.append((r"\bcouriers?\b", f"Courier spawn points moved: {_sides_text(cour)}"))
    stash = _moves(e.get("stash", {}).get("old", []), e.get("stash", {}).get("new", []))
    for side, ds in sorted(stash.items()):
        rows.append((r"\bstash\b", f"{side} stash moved {_span(ds)} units"))
    cur = diff.get("currentAreas", {})
    n0, n1 = len(cur.get("old", [])), len(cur.get("new", []))
    if n0 != n1:
        more = "more" if n1 > n0 else "fewer"
        rows.append((r"\bcurrents?\b", f"Streams have {abs(n1 - n0)} {more} sections with a current ({n1} instead of {n0})"))
    wards = diff.get("wards", {})
    lost, gained = int(wards.get("lost") or 0), int(wards.get("gained") or 0)
    if lost or gained:
        rows.append((r"\bno-ward\b|\bwards?\b|\bwardable\b",
                     f"No-ward ground changed: {lost} cells became no-ward, {gained} became wardable"))
    return rows


def _postprocess_map_file_rows(lines, version=None):
    """After Valve's Terrain Changes rows: one row for every kind of change the map file has and no row names (its
    keyword nowhere in the block), REWORK with the "?" that says it is ours. In the block's last list (its
    "Miscellaneous"), or a list of its own."""
    path = _DIFF.format(version) if version else None
    if not path or not os.path.exists(path):
        return lines
    with open(path, encoding="utf-8") as f:
        diff = json.load(f)
    start = next((k for k, ln in enumerate(lines) if _TERRAIN_HEAD_RE.match(ln)), None)
    if start is None:
        return lines
    end = next((k for k in range(start + 1, len(lines)) if _BLOCK_RE.match(lines[k])), len(lines))
    said = " ".join(m.group(1).lower() for ln in lines[start:end] for m in [_ROW_TEXT_RE.search(ln)] if m)
    new = [text for key, text in map_file_rows(diff) if not re.search(key, said)]
    if not new:
        return lines
    ind = re.match(r"^(\s*)", lines[start]).group(1)
    rows = [f'{ind}W(li({_py_str(t)}, t("REWORK"), extra=inline_note("{_NOTE}")))' for t in new]
    close = next((k for k in range(end - 1, start, -1) if lines[k].strip() == "W(ul_close())"), None)
    if close is None:
        return lines[:end] + [f"{ind}W(ul_open())", *rows, f"{ind}W(ul_close())"] + lines[end:]
    return lines[:close] + rows + lines[close:]
