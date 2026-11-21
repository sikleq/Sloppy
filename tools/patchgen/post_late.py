"""A pass run late: an ability's per-level % formula (the innate, facet and General passes are in post_innates,
post_facets, post_notes since 2026-11-21)."""
import re

from .data import ABILS

_LEVEL_OF_RE = re.compile(
    r'^(?P<ind>\s*)W\(li\("(?P<pre>[^"]*?) rescaled from \(\+(?P<a>\d+(?:\.\d+)?) with every (?P<n>\d+) hero levels\) '
    r'to \(\+(?P<b>\d+(?:\.\d+)?) with every level of (?P<abil>[^)"]+)\)", t\("[A-Za-z]+"\)\)\)\s*$')


_PCT_LEVEL_PILL_RE = re.compile(r'^\s*(_pill\d+) = scale_pill\("(?P<last>\d+(?:\.\d+)?)% \+ (?P<per>\d+(?:\.\d+)?)% per level"')
_PCT_LEVEL_ROW_RE = re.compile(
    r'^(?P<ind>\s*)W\(li\("(?P<pre>[^"]*?) rescaled from (?P<a>\d+(?:\.\d+)?)% per hero level to (?P<vals>(?:\d+(?:\.\d+)?%?/)+)" '
    r'\+ _pill\d+\[0\] \+ "", t\("[A-Za-z]+"\)(?:, extra=inline_note\("(?P<note>[^"]*)"\) \+ _pill\d+\[1\])?\)\)\s*$')
_ANY_SLUG_RE = re.compile(r'^\s*W\(ability\("[^"]+", slug="([^"]+)"')


def _pct_level_formula(pill, row, slug, version):
    """"… rescaled from 2% per hero level to 4/8/12/16% + 1% per level" (7.38 Precision Aura) -> a formula table by hero
    level, as the rule above (owner 2026-11-02): the levels come from the ability it depends on, or its own."""
    from patch.ability_kv import _hero_blocks
    p, m = _PCT_LEVEL_PILL_RE.match(pill), _PCT_LEVEL_ROW_RE.match(row)
    if not (p and m):
        return None
    vals = [v.rstrip("%") for v in m.group("vals").split("/") if v] + [p.group("last")]
    blocks = _hero_blocks(version) if version else {}
    parent = str((blocks.get(slug) or {}).get("DependentOnAbility", ""))
    ult = "ULTIMATE" in str((blocks.get(parent) or blocks.get(slug) or {}).get("AbilityType", "")).upper() or bool(parent)
    if ult:
        at, levels = "6, 12 and 18", "[1, 5, 6, 11, 12, 17, 18, 25, 30]"
        idx = "0 if L < 6 else min(3, (L - 6) // 6 + 1)"
    else:
        at, levels = "1, 3, 5 and 7", "[1, 3, 5, 7, 10, 20, 30]"
        idx = "min(3, (L - 1) // 2)"
    who = f"{parent} taken at hero levels {at}" if parent else f"Taken at hero levels {at}"
    note = f'{m.group("note")}. {who}' if m.group("note") else who
    ind = m.group("ind")
    return (f'{ind}W(li_formula("{m.group("pre")} rescaled", "{m.group("a")}% per hero level", '
            f'"{"/".join(vals)}% + {p.group("per")}% per level",\n'
            f'{ind}             lambda L: {m.group("a")} * L, lambda L: [{", ".join(vals)}][{idx}] + {p.group("per")} * L,\n'
            f'{ind}             levels={levels}, tag_levels=range(1, 31), label="Hero level", value_fmt="{{:g}}%",\n'
            f'{ind}             inline_note_text="{note}"))')


def _postprocess_ability_level_formula(lines, version):
    """"Radius increase rescaled from (+50 with every 10 hero levels) to (+40 with every level of Echo Slam)" -> a
    formula table by hero level with its BUFF / NERF, not a REWORK row (owner 2026-10-27, 7.39 Aftershock). The
    ability's levels: an ultimate at 6 / 12 / 18, a basic ability at 1 / 3 / 5 / 7 (as soon as it can be taken)."""
    from patch.ability_kv import _hero_blocks
    by_name = {name.lower(): slug for name, slug in ABILS.values()}
    out, slug_here = [], ""
    for line in lines:
        s = _ANY_SLUG_RE.match(line)
        slug_here = s.group(1) if s else slug_here
        formula = _pct_level_formula(out[-1], line, slug_here, version) if out else None
        if formula:
            out[-1] = formula
            continue
        m = _LEVEL_OF_RE.match(line)
        if not m:
            out.append(line)
            continue
        slug = by_name.get(m.group("abil").strip().lower())
        block = _hero_blocks(version).get(slug) if slug and version else None
        ult = "ULTIMATE" in str((block or {}).get("AbilityType", "")).upper()
        a, n, b, abil = m.group("a"), m.group("n"), m.group("b"), m.group("abil").strip()
        if ult:
            new_fn, levels, at = f"lambda L: {b} * (0 if L < 6 else min(3, (L - 6) // 6 + 1))", "[1, 6, 10, 12, 18, 20, 30]", "6, 12 and 18"
        else:
            new_fn, levels, at = f"lambda L: {b} * min(4, (L + 1) // 2)", "[1, 3, 5, 7, 10, 20, 30]", "1, 3, 5 and 7"
        ind = m.group("ind")
        out.append(f'{ind}W(li_formula("{m.group("pre")} rescaled", "+{a} with every {n} hero levels", '
                   f'"+{b} with every level of {abil}",\n{ind}             lambda L: {a} * (L // {n}), {new_fn},\n'
                   f'{ind}             levels={levels}, label="Hero level", value_fmt="+{{:g}}",\n'
                   f'{ind}             inline_note_text="{abil} taken at hero levels {at}"))')
    return out
