"""Which patches get a Terrain page and what changed on each — the map notes of content/*.py (read as Python) and
the committed map diffs (data/terrain/terrain_diff_<patch>.json). Data only, no HTML: builders/terrain.py draws the
pages from it, and the site header (patch/site_common.py) asks it for the newest page — that used to be a lazy
import of builders/terrain.py from the header, a cycle (audit 2026-10-26 #6).
"""
import ast as _ast
import glob as _glob
import json as _json
import os as _os

from patch import map_versions as _map_versions

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))


def _load_diff(patch):
    """The committed per-patch terrain diff (data/terrain/terrain_diff_<patch>.json,
    written by scripts/gen/build_terrain_diff.py). Returns None if absent so the page
    still builds (maps only, no markers) for a patch without a diff."""
    path = _os.path.join(_HERE, "data", "terrain", f"terrain_diff_{patch}.json")
    try:
        with open(path, encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return None


def _box_key(box):
    """A camp spawn box as a hashable set of its corners (order-free)."""
    return frozenset((p["x"], p["y"]) for p in box)


def _ver_key(v):
    """Sort key for version strings: '7.40' < '7.40b' < '7.41'."""
    import re
    def _part(s):
        m = re.match(r'^(\d+)([a-z]*)$', s)
        return (int(m.group(1)), m.group(2)) if m else (0, s)
    return tuple(_part(x) for x in v.split("."))


def _call_name(node):
    return node.func.id if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name) else None


def _str_arg(node):
    """A plain string literal ("a" "b" implicit concatenation is one constant)."""
    return node.value if isinstance(node, _ast.Constant) and isinstance(node.value, str) else None


def _row_tag(text, badge):
    """t("X") -> X; b(old, new[, l=True]) -> BUFF/NERF by the row's direction."""
    name = _call_name(badge)
    if name == "t" and badge.args:
        return _str_arg(badge.args[0]) or "MISC"
    if name in ("b", "bf"):
        lower_better = any(k.arg == "l" and isinstance(k.value, _ast.Constant) and k.value.value
                           for k in badge.keywords)
        low = text.lower()
        good = lower_better if ("decreased" in low or "reduced" in low) else not lower_better
        return "BUFF" if good else "NERF"
    return "MISC"


def _statements(body):
    """A function body's statements in order, nested if/for/with bodies included."""
    for st in body:
        yield st
        for field in ("body", "orelse"):
            if isinstance(st, (_ast.If, _ast.For, _ast.While, _ast.With)) and getattr(st, field, None):
                yield from _statements(getattr(st, field))


def _notes_in(source):
    """{patch: rows} of one content file (see _terrain_notes_by_patch)."""
    raw = {}
    for st in _ast.parse(source).body:
        if isinstance(st, _ast.FunctionDef):
            for k, v in _notes_in_body(st.body).items():
                raw.setdefault(k, []).extend(v)
    return raw


def _notes_in_body(body):
    raw, patch, in_block, sub = {}, None, False, None
    for st in _statements(body):
        call = st.value if isinstance(st, _ast.Expr) else None
        name = _call_name(call)
        if name == "write_head" and call.args:
            patch = _str_arg(call.args[0])
            continue
        if name != "W" or not call.args:
            continue
        inner = call.args[0]
        iname = _call_name(inner)
        if iname == "plain_header":
            title = _str_arg(inner.args[0]) if inner.args else None
            in_block = any(k.arg == "terrain_link" for k in inner.keywords)
            sub = None if title == "Terrain Changes" else title
        elif not in_block or iname in ("ul_open", "ul_close"):
            continue
        elif iname == "subgroup" and inner.args:
            sub = _str_arg(inner.args[0])
        elif iname == "li" and inner.args and _str_arg(inner.args[0]) and patch:
            text = _str_arg(inner.args[0])
            badge = inner.args[1] if len(inner.args) > 1 else next(
                (k.value for k in inner.keywords if k.arg == "badge"), None)
            extra = next((k.value for k in inner.keywords if k.arg == "extra"), None)
            note = (_str_arg(extra.args[0]) if _call_name(extra) == "inline_note" and extra.args else None)
            raw.setdefault(patch, []).append((text, _row_tag(text, badge), sub, note))
        else:
            in_block = False                   # any other block (an item, a unit, a section) ends it
    return raw


def _terrain_notes_by_patch():
    """Every patch's map notes from content/*.py: the rows of each block whose
    ``plain_header(..., terrain_link=...)`` links it to the map — "Terrain
    Changes" (7.39+), 7.38's "Wandering Waters" / "Other Terrain Changes",
    7.38c's "Dire Safe Lane Jungle" / "Top Roshan Pit" / "Bottom Lane" (the
    owner 2026-10-02: 7.38b's and 7.38c's map notes were missing). A block
    titled other than "Terrain Changes" is its own subgroup.

    Read as Python (ast), not by regex: a row's inline note (7.41's "Result:"
    lines under the Watcher row) comes along and the page shows it as on the
    patch page. Returns ``{patch: [(text, TAG, subgroup, note), ...]}``.
    """
    raw = {}
    for p in sorted(_glob.glob(_os.path.join(_HERE, "content", "*.py"))):
        try:
            with open(p, encoding="utf-8") as f:
                found = _notes_in(f.read())
        except (OSError, SyntaxError):
            continue
        for k, v in found.items():
            raw.setdefault(k, []).extend(v)
    return raw


# What moved in the map file, per point-entity layer of the diff (plural nouns).
_MOVED_NAMES = {"towers": "towers", "lotus": "lotus pools", "twinGates": "twin gates",
                "tormentors": "Tormentors", "bounty": "bounty runes", "power": "power runes",
                "wisdom": "wisdom shrines", "wisdomRunes": "wisdom runes", "outposts": "outposts",
                "watchers": "watchers", "roshan": "Roshan pits"}


_SAME_CAMP = 1000          # units: a camp this close on both sides is the same camp, moved


def _retiered_pairs(old, new, radius=_SAME_CAMP):
    """Camps whose tier changed, as (old camp, new camp): each new camp paired with
    the old camp nearest to it when they are each other's nearest and within
    `radius`. By position, not by trigger name — 7.38 renumbered the camps (by
    name, camps "moved" 12000 units and "changed tier"), and a camp demoted AND
    moved (7.40's triangle camps) is still found, which an exact-position match
    missed (7.40 read 2 of its 4 demotions)."""
    def d2(a, b):
        return (a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2
    out = []
    for c in new:
        if not old:
            break
        o = min(old, key=lambda o: d2(o, c))
        back = min(new, key=lambda x: d2(o, x))
        if back is c and d2(o, c) <= radius ** 2 and o.get("tier") != c.get("tier"):
            out.append((o, c))
    return out


def _retiered(old, new, radius=_SAME_CAMP):
    return len(_retiered_pairs(old, new, radius))


def _moved_items(diff):
    """What changed between the step's two map files, read off its diff, as
    (name, kind, n, removed, total): kind "delta" when the count changed (n
    added, `removed` removed), "moved" when it kept its count (n of `total`
    moved), "changed" for camp tiers and resized/moved spawn boxes (7.39d:
    "Increased spawnboxes of Triangle Ancient camps"). [] when nothing changed."""
    if not diff:
        return []

    def delta(old, new, name):
        a, b = {tuple(p) for p in old}, {tuple(p) for p in new}
        added, removed = len(b - a), len(a - b)
        if not added and not removed:
            return None
        if len(old) == len(new):
            return (name, "moved", added, 0, len(new))
        return (name, "delta", added, removed, len(new))

    camps_new = diff.get("campsNew", [])
    out = [delta(diff.get("treesOld", []), diff.get("treesNew", []), "trees")]
    out.append(delta([(c["x"], c["y"]) for c in diff.get("campsOld", [])],
                     [(c["x"], c["y"]) for c in camps_new], "camps"))
    retiered = _retiered(diff.get("campsOld", []), camps_new)
    if retiered:
        out.append(("camp tiers", "changed", retiered, 0, len(camps_new)))
    old_boxes = {_box_key(b) for b in diff.get("spawnboxesOld", [])}
    new_boxes = {_box_key(b) for b in diff.get("spawnboxesNew", [])}
    if len(old_boxes) == len(new_boxes) and new_boxes - old_boxes:
        out.append(("camp spawn boxes", "changed", len(new_boxes - old_boxes), 0, len(new_boxes)))
    elif old_boxes != new_boxes:
        out.append(("camp spawn boxes", "delta", len(new_boxes - old_boxes), len(old_boxes - new_boxes),
                    len(new_boxes)))
    for key, name in _MOVED_NAMES.items():
        ed = diff.get("entities", {}).get(key)
        if ed:
            out.append(delta(ed.get("old", []), ed.get("new", []), name))
    w = diff.get("wards") or {}
    if w.get("lost") or w.get("gained"):
        # gridnav cells (64 units) where a ward can't stand: "lost" = became no-ward, so +lost −gained
        out.append(("no-ward cells", "delta", w.get("lost", 0), w.get("gained", 0), w.get("cells", 0)))
    out += _layer_changes(diff)
    return [i for i in out if i]


def _layer_changes(diff):
    """The 2026-10-06 layers as chips: lane paths changed (n of the 6 lanes), currents, the zones, spawn points —
    a patch's notes say nothing about some of them (7.39, 7.39b lane paths)."""
    out = []
    lanes = diff.get("lanes") or {}
    old = {(p["team"], p["lane"]): p["points"] for p in lanes.get("old", [])}
    new = {(p["team"], p["lane"]): p["points"] for p in lanes.get("new", [])}
    if old and new:
        n = sum(1 for k, v in new.items() if old.get(k) != v)
        if n:
            out.append(("lane paths", "changed", n, 0, len(new)))
    co, cn = _current_shapes(diff, "old"), _current_shapes(diff, "new")
    if co != cn:
        if len(co) == len(cn):
            out.append(("river currents", "changed", sum(1 for a, b in zip(co, cn) if a != b), 0, len(cn)))
        else:                                      # 7.38: the streams (and their currents) are new
            out.append(("river currents", "delta", len(cn), len(co), len(cn)))
    for key, name in (("shops", "shop zones"), ("roshanPit", "Roshan pit zones"), ("nowardZones", "no-ward zones")):
        z = (diff.get("zones") or {}).get(key) or {}
        a, b = _zone_volumes(z, "old"), _zone_volumes(z, "new")
        if set(a.values()) != set(b.values()):
            # counted by zone, not by hull (2026-10-07: "1/8 shop zones" for 4 shops — a fountain's shop is 3 hulls)
            sa, sb = set(a.values()), set(b.values())
            out.append((name, "changed", len(sb - sa), 0, len(sb)) if len(sa) == len(sb)
                       else (name, "delta", len(sb - sa), len(sa - sb), len(sb)))
    ents = diff.get("entities") or {}
    for key, name in (("laneSpawns", "lane creep spawns"), ("heroSpawns", "hero spawns")):
        ed = ents.get(key) or {}
        if ed.get("old") and ed.get("new"):
            a, b = {tuple(p) for p in ed["old"]}, {tuple(p) for p in ed["new"]}
            if a != b:
                out.append((name, "moved", len(b - a), 0, len(b)))
    return out


def _box_key_xy(points):
    return frozenset(tuple(p) for p in points)


def _zone_volumes(zone, side):
    """{volume: frozenset of its hulls' point sets} of one side of a zone kind — a zone is one entity, maybe several
    hulls (no volume numbers in a diff: each polygon its own zone)."""
    polys, vols = zone.get(side) or [], zone.get(side + "Volume") or []
    out = {}
    for i, p in enumerate(polys):
        out.setdefault(vols[i] if i < len(vols) else ("p", i), set()).add(_box_key_xy(p))
    return {k: frozenset(v) for k, v in out.items()}


def _current_shapes(diff, side):
    """Each current of one side as what the map file changes: its buff zone's rings (a centre line if a diff has no
    zones). The max bonus is left out — 7.41 changed it in the notes, not in the map file."""
    areas = (diff.get("currentAreas") or {}).get(side)
    if areas is not None:
        return [a["rings"] for a in areas]
    return [[line] for line in (diff.get("currents") or {}).get(side) or []]


def _moved_summary(diff):
    """_moved_items as text — e.g. ["trees +38 −27", "camps moved: 2", "camp tiers
    changed: 4"] (the Oldgrowth table says the same)."""
    def text(name, kind, n, removed, _total):
        return {"delta": f"{name} +{n} −{removed}", "moved": f"{name} moved: {n}"}.get(kind, f"{name} {kind}: {n}")
    return [text(*i) for i in _moved_items(diff)]


def _quiet(steps, notes, diffs):
    """Steps whose notes list nothing and whose map file moved nothing — no page.
    Their pictures differ from the patch before only by render noise (checked
    2026-10-02 with scripts/gen/map_picture_diff.py: no change bigger than the
    wind in the trees), so there is nothing to compare. The newest step keeps its
    page all the same (the owner 2026-10-03: without it "one could think the patch
    doesn't exist" — 7.41f, the current map)."""
    newest = max(steps, key=_ver_key) if steps else None
    return {p for p in steps if p != newest and not notes.get(p) and not _moved_summary(diffs.get(p))}


def _terrain_filename(ver, patches=None):
    """terrain_<ver_slug>.html for every version."""
    return f"terrain_{ver.replace('.', '')}.html"


def _pages(steps, notes):
    """Every Terrain page, newest first: each step (a patch with its own map file)
    and each patch with terrain notes."""
    return sorted(set(steps) | set(notes), key=_ver_key, reverse=True)


def page_patches():
    """The patches that get a Terrain page, newest first (Terrain Stats links its rows to them), with what
    save_terrain_html needs to build them: (patches, notes, steps, diffs)."""
    notes = _terrain_notes_by_patch()
    steps = {s.patch: s for s in _map_versions.steps()}
    diffs = {p: _load_diff(p) for p in steps}
    quiet = _quiet(steps, notes, diffs)
    newest = max(_map_versions.load_patch_maps(), key=_map_versions.ver_key)
    return (_pages([p for p in steps if p not in quiet], notes) or [newest]), notes, steps, diffs


def latest_page_file():
    """terrain_<newest page>.html — where the Terrain tab and the index tile point."""
    return _terrain_filename(page_patches()[0][0])
