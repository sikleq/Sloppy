"""Talent swap rows marked by what happened to each talent (owner 2026-10-21, Batrider 7.41).

"Level 10 Talent: A replaced with B" reads as one swap, but A and B each have their own fate:
  - A left the tree             -> red (the DEL colour)
  - B is a brand-new talent     -> gold; the row stays SWAP (as NEW it scored as a buff)
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

# an optional facet prefix: "Facet: " or the facet's own name ("Old Blood: Level 10 Talent ...", Bloodseeker 7.39)
SWAP_RE = re.compile(r"^(?:[A-Z][\w' -]{1,30}: )?Level (10|15|20|25)(?: Talent)?:? (.+?) replaced with (.+?)\.?$")
# numbers incl. per-level lists ("+20/40", Viper 7.41 Nethertoxin) and their unit
_NUM_RE = re.compile(r"[+\-−]?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*\s*(?:%|s\b|x\b)?")
_cache = {}


def key(talent):
    """The talent without its numbers: "+1s Smoldering Resin Duration" -> "smoldering resin duration"."""
    words = re.sub(r"\s+", " ", _NUM_RE.sub(" ", talent)).strip(" :.").lower().split(" ")
    # singular / plural are one talent: "+1 Acorn Shot Bounce" -> "+2 Acorn Shot Bounces" (Hoodwink 7.41)
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words)


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


# Fates the patch text can't show (the other half of the move isn't in the notes), checked in the game files
# (dota2-ida-researcher, 2026-10-21): (version, hero, "old" / "new", key(talent)) -> (fate, note)
_KNOWN = {
    ("7.38", "Shadow Demon", "new", key("+150 Demonic Purge Damage")):
        ("moved", "+150 Demonic Purge Damage was already in the tree before this patch (Level 20)"),
    ("7.40", "Chen", "new", key("+75 Penitence Damage")):
        ("moved", "+75 Penitence Damage was already in the tree before this patch (Level 10, Penitence deals 175 damage)"),
    ("7.41", "Keeper of the Light", "new", key("+90 Blinding Light Damage")):
        ("moved", "+90 Blinding Light Damage was already in the tree before this patch (Level 15, since 7.40)"),
    ("7.41", "Keeper of the Light", "old", key("+10% Spirit Form Movement Speed Bonus")):
        ("moved", "+10% Spirit Form Movement Speed Bonus moved to Level 15 as +30% Spirit Form Bright Speed Bonus"),
    ("7.41", "Ogre Magi", "old", key("+35 Bloodlust Attack Speed")):
        ("moved", "+35 Bloodlust Attack Speed moved to Level 15 as +20 (+35 on self) Bloodlust Attack Speed"),
    ("7.41", "Rubick", "old", key("+165 Telekinesis Landing Damage")):
        ("moved", "+165 Telekinesis Landing Damage moved to Level 20 (Telekinesis Landing deals 325 damage)"),
}


def mark(text, hero):
    """(old_fate, new_fate, note) for a talent swap row, or None when the row isn't one.
    Fates: "gone" / "moved" for the old talent, "fresh" / "moved" for the new one."""
    m = SWAP_RE.match(text)
    path = _content_file()
    if not m or not hero or not path:
        return None
    level, old, new = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
    if key(old) == key(new):
        # the same talent in another form ("+50% Spark Wraith Damage" -> "+200 Spark Wraith Damage", Arc Warden 7.41)
        return ("same", "same", "")
    others = [r for r in _swaps_by_hero(path).get(hero, []) if r != (level, old, new)]
    # another row of the hero, the same level too: a talent can swap sides of one level (Wraith King 7.38)
    came = next(((lv, o) for lv, o, _ in others if key(o) == key(new)), None)
    went = next(((lv, n) for lv, _, n in others if key(n) == key(old)), None)
    notes = []
    if came:
        where = "the other side of this level" if came[0] == level else f"Level {came[0]}"
        notes.append(f"{new} moved from {where}, where it was {came[1]}")
    if went:
        where = "the other side of this level" if went[0] == level else f"Level {went[0]}"
        notes.append(f"{old} moved to {where} as {went[1]}")
    old_fate, new_fate = "moved" if went else "gone", "moved" if came else "fresh"
    from .state import _State
    ver = _State.current_patch_version
    for side, talent in (("old", old), ("new", new)):
        known = _KNOWN.get((ver, hero, side, key(talent)))
        if known:
            if side == "old":
                old_fate = known[0]
            else:
                new_fate = known[0]
            notes.append(known[1])
    return (old_fate, new_fate, ". ".join(notes))
