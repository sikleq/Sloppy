"""An ability whose numbers now grow with something else: "Scaling reworked" (owner 2026-11-06: "придумай" — 7.38 Tormentor's
abilities went from "per death" to "per minute of game time"). The card: the game's description on both sides and each value
as its formula with a level table on that formula's own axis (deaths, game time, hero level).

    scaling_rework("Reflect", "../icons/abilities/miniboss_reflect.png", old_desc, new_desc,
                   [("Damage percentage", "90 + (20 per death)", "50 + (2 per minute of game time)")])

The generator writes this call (tools/patchgen/post_items.py) for a row "X rescaled from A + (B per death) to C + (D per
minute of game time)"; the rule is "the formula's variable changed", not the unit."""
import re

from .badges import scale_pill
from .cards_ability_change import ability_change

_FORMULA_RE = re.compile(r"^\s*(?P<a>-?\d+(?:\.\d+)?)%?\s*\+\s*\(?\s*(?P<b>-?\d+(?:\.\d+)?)%?\s+per\s+(?P<var>[^)]+?)\s*\)?\s*$")

# each variable's axis: which values the table shows and how a column reads
_AXES = {
    "death": dict(levels=list(range(0, 7)), level_fmt=lambda D: f"{D}", axis_label="deaths", jump_at=None),
    "minute": dict(levels=list(range(15, 61, 5)), level_fmt=lambda M: f"{M}:00", axis_label="time", jump_at=None),
    "level": dict(),
}


def variable(formula):
    """"20 per minute of game time" -> "minute"; "200 per death" -> "death"; None when it is no "A + B per X" formula."""
    m = _FORMULA_RE.match(formula or "")
    if not m:
        return None
    word = m.group("var").lower().split()[0].rstrip("s")
    return word if word in _AXES else m.group("var").lower()


def _pill(formula, pct):
    m = _FORMULA_RE.match(formula)
    a, b, var = float(m.group("a")), float(m.group("b")), variable(formula)
    unit = "%" if pct else ""
    said = m.group("var").split(" of ")[0]                       # "minute of game time" -> "per minute"
    text = f"{m.group('a')}{unit} + {m.group('b')}{unit} per {said}"
    return scale_pill(text, lambda x: a + b * x, value_fmt="{:g}" + unit, **_AXES.get(var, {}))


def scaling_rework(name, icon_url, old_desc, new_desc, stats):
    """The old -> new card. stats: [(label, old formula, new formula)]; a label saying "percentage" or "%" is a percent."""
    sides = {"old": [], "new": []}
    tables = {"old": [], "new": []}
    for label, old, new in stats:
        pct = bool(re.search(r"percent|%", label, re.I))
        for side, formula in (("old", old), ("new", new)):
            trigger, table = _pill(formula, pct)
            sides[side].append(f"{label}: {trigger}.")
            tables[side].append(table)

    def desc(text, formulas):
        # what the side grows with goes to its header, "Passive – scales with game time" (owner 2026-11-06)
        said = {_SCALES_WITH.get(variable(f)) for f in formulas} - {None}
        text = text.rstrip()
        text += "" if text.endswith((".", "!")) else "."
        return text + (f" Scales with {said.pop()}." if len(said) == 1 else "")
    return ability_change(
        old=dict(name=name, icon_url=icon_url, desc=[desc(old_desc, [s[1] for s in stats]), " ".join(sides["old"])],
                 tables=tables["old"]),
        new=dict(name=name, icon_url=icon_url, desc=[desc(new_desc, [s[2] for s in stats]), " ".join(sides["new"])],
                 tables=tables["new"]),
        summary="Scaling reworked", tag="rework")


_SCALES_WITH = {"minute": "game time", "death": "its deaths", "level": "level"}
