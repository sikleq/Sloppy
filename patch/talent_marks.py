"""Talent swap rows marked by what happened to each talent (owner 2026-10-21, Batrider 7.41).

"Level 10 Talent: A replaced with B" reads as one swap, but A and B each have their own fate:
  - A left the tree             -> red (the DEL colour)
  - B is a brand-new talent     -> gold; the row stays SWAP (as NEW it scored as a buff)
  - A or B only changed level   -> plain, with a note saying where it went / came from
A talent "moved" when the same talent, numbers aside, stands on the other side of another swap row of the
same hero in the same patch (Batrider 7.41: +4s Smoldering Resin at 20 -> +1s Smoldering Resin at 10).

Every "replaced with" row stays SWAP, moved or not (owner 2026-10-22): the colours tell the fates apart. A talent
of the same ability whose bonus changed kind (flat -> %, active-only -> permanent) is a different talent, not a
move — keep such pairs out of _KNOWN (9 game-checked cases, docs/agent-rules/patch-tags.md).

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


def _changed_part(other, this):
    """What of the talent's other form differs from this one: only its numbers when the words are the same (owner
    2026-11-07: "+3% Max HP Regen while inside The Calling: moved from Level 10, where it was +1.5% Max HP Regen while
    inside The Calling" told the talent twice -> "…, was +1.5%"), else the whole other form."""
    a, b = other.split(), this.split()
    if len(a) != len(b):
        return other
    diff = [x for x, y in zip(a, b) if x != y]
    if diff and all(any(c.isdigit() for c in x) for x in diff):
        return " ".join(diff)
    return other


_FIRST_NUM = re.compile(r"[+\-−]?\d+(?:\.\d+)?")


def _hl(text, kind):
    from .elements import hl
    return hl(text, kind)


def _first(text):
    m = _FIRST_NUM.search(text)
    return abs(float(m.group().replace("−", "-"))) if m else None


def _bare(talent):
    """The talent's words without its numbers: "+3% Max HP Regen while inside The Calling" -> "Max HP Regen …"."""
    return re.sub(r"\s+", " ", _NUM_RE.sub(" ", talent)).strip(" :.")


def change_cells(before, after, lv_before, lv_after, label=None, percent=True):
    """(talent, level, value) cells of a moved talent's row in its "?" table: the level and the numbers each as
    before -> after, the after side green when the talent got better and red when worse (owner 2026-11-07: "надо как-то
    улучшить, чтобы дать понять, на сколько талант улучшился/ухудшился и куда переехал"; a line of them "всё равно
    визуально не читаемо, слишком подряд цифры идут"). A talent taken earlier is better; a bigger number is better."""
    if lv_before == lv_after:
        level = f"{lv_after}, other side"
    else:
        level = f"{lv_before} → " + _hl(str(lv_after), "buff" if lv_after < lv_before else "nerf")
    same_words = _changed_part(before, after) != before or before == after
    if label is None:
        # the numbers stay in the name only when they didn't change
        label = after if before == after or not same_words else _bare(after)
    value = '<span class="tm-same">same</span>'
    if before != after:
        was, now = (_changed_part(before, after), _changed_part(after, before)) if same_words else (before, after)
        a, b = _first(was), _first(now)
        if not same_words and label == after:
            value = "was " + before
        elif not same_words or a is None or b is None or a == b:
            # another bonus, not a bigger or smaller one: neither better nor worse
            value = f"{was} → " + _hl(now, "rework")
        else:
            value = f"{was} → " + _hl(now, "buff" if b > a else "nerf")
            if percent and a and len(_FIRST_NUM.findall(was)) == 1 and len(_FIRST_NUM.findall(now)) == 1:
                d = round((b - a) / a * 100)
                value += f' <span class="tm-pct">{"+" if d > 0 else "−"}{abs(d)}%</span>'
    return (label, level, value)


def moves_table(rows):
    """The "?" of a talent swap as a small table: a head, then a row per talent, its name, level and value apart."""
    cells = ['<span class="tm-h">Talent</span><span class="tm-h">Level</span><span class="tm-h">Value</span>']
    cells += [f'<span class="tm-n">{n}</span><span class="tm-c">{lv}</span><span class="tm-c">{v}</span>'
              for n, lv, v in rows]
    return '<span class="tal-moves">' + "".join(cells) + "</span>"


_SAME = '<span class="tm-same">same</span>'

# Fates the patch text can't show (the other half of the move isn't in the notes), checked in the game files
# (dota2-ida-researcher, 2026-10-21): (version, hero, "old" / "new", key(talent)) -> (fate, table row)
_KNOWN = {
    ("7.38", "Shadow Demon", "new", key("+150 Demonic Purge Damage")):
        ("moved", ("+150 Demonic Purge Damage", "20, already before this patch", _SAME)),
    ("7.40", "Chen", "new", key("+75 Penitence Damage")):
        ("moved", ("+75 Penitence Damage", "10, already before this patch", _SAME)),
    ("7.41", "Keeper of the Light", "new", key("+90 Blinding Light Damage")):
        ("moved", ("+90 Blinding Light Damage", "15, already since 7.40", _SAME)),
    ("7.41", "Keeper of the Light", "old", key("+10% Spirit Form Movement Speed Bonus")):
        ("moved", change_cells("+10% Movement Speed Bonus", "+30% Bright Speed Bonus", 20, 15, label="Spirit Form")),
    ("7.41", "Ogre Magi", "old", key("+35 Bloodlust Attack Speed")):
        ("moved", change_cells("+35", "+20 (+35 on self)", 20, 15, label="Bloodlust Attack Speed")),
    ("7.41", "Rubick", "old", key("+165 Telekinesis Landing Damage")):
        ("moved", change_cells("+165 bonus", "325 in all", 10, 20, label="Telekinesis Landing Damage", percent=False)),
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
    # each talent once, as before -> after (owner 2026-11-07, 7.38 Pangolier: "не читаемы, это много текста сплошняком")
    if came:
        notes.append(change_cells(came[1], new, came[0], level))
    if went:
        notes.append(change_cells(old, went[1], level, went[0]))
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
    return (old_fate, new_fate, moves_table(notes) if notes else "")
