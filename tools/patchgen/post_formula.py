"""A game formula written as old / new -> a live formula_change block: a field for every variable, the old and new
result, a chart of both curves (owner 2026-11-18, pilot 7.42 "Hero kill bounty rescaled"). Two ways Valve writes it:
one row with "OLD: <formula><br>NEW: <formula>" in its note (7.42), or the name row followed by an "OLD: <formula>"
row and a "NEW: <formula>" row (7.40 "Assist Gold Formula Reworked")."""
import json
import re

from patch.formula_rows import _eval_formula

# W(li("<name>", t("<TAG>"), extra=inline_note("OLD: <formula><br>NEW: <formula>")))
_FX_ROW_RE = re.compile(
    r'^W\(li\("(?P<name>[^"]+)", t\("(?P<tag>\w+)"\), '
    r'extra=inline_note\("OLD: ?(?P<old>[^"<]+?)<br>NEW: ?(?P<new>[^"<]+?)"\)\)\)$')
# the name row of the three-row form: W(li("<name>", t("<TAG>")))
_FX_NAME_ROW_RE = re.compile(r'^W\(li\("(?P<name>[^"]+)", t\("(?P<tag>\w+)"\)\)\)$')
# a row "OLD: <formula>" / "Old Formula: <formula>" (any tag after it)
_FX_SIDE_RE = re.compile(r'^W\(li\("(?P<side>OLD|NEW)(?: formula)?: ?(?P<expr>[^"<]+?)"[,)]', re.I)
_FX_EXPR_RE = re.compile(r'^[\w\s.+\-*/^()]+$')
_FX_IDENT_RE = re.compile(r'[A-Za-z_]\w*')
_FX_NAME_TAIL_RE = re.compile(r'\s+(?:rescaled|reworked|changed|adjusted|updated)$', re.I)

# The variables we know: (name pattern, default value, chart range or None, axis label or None). A formula with any
# other variable stays as it was: a default we would have to guess is worse than none.
_FX_KNOWN_VARS = (
    # a hero level: chart 1-30, the default level 1 (owner 2026-11-19: "по умолчанию 1 уровень и 0 фактор")
    (re.compile(r'Level$'), 1, (1, 30), None),
    (re.compile(r'^NumHeroes$'), 1, (1, 5), 'Heroes'),         # heroes sharing the gold: 1-5, the team size
    (re.compile(r'Networth$|^NW$'), 10000, None, None),        # networth-style -> 10000 (docs/formula-change.md)
    (re.compile(r'(?:Kill)?[Ss]treak'), 0, None, None),        # no streak by default
)


def _fx_known(var):
    return next(((d, rng, lab) for pat, d, rng, lab in _FX_KNOWN_VARS if pat.search(var)), None)


def _fx_words(var):
    """VictimLevel -> Victim Level (the chart's axis)."""
    return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', var)


def _fx_unit(name):
    if re.search(r'\b(?:gold|bounty)\b', name, re.I):
        return 'Gold'
    if re.search(r'\b(?:experience|xp)\b', name, re.I):
        return 'XP'
    return ''


def _fx_tag(old, new, inputs, chart, fallback):
    """BUFF when the new formula gives at least as much everywhere on the chart, NERF when at most, REWORK when the
    curves cross (7.42 bounty: less below level 12.5, more above)."""
    if not chart:
        return fallback
    var, _label, lo, hi = chart
    diffs = [_eval_formula(new, {**inputs, var: x}) - _eval_formula(old, {**inputs, var: x}) for x in range(lo, hi + 1)]
    if all(d >= 0 for d in diffs) and any(d > 0 for d in diffs):
        return 'BUFF'
    if all(d <= 0 for d in diffs) and any(d < 0 for d in diffs):
        return 'NERF'
    return 'REWORK'


def formula_call(name, tag, old, new):
    """The formula_change call for this name and old / new formulas, or None when they are not ones we can compute."""
    old, new = old.strip(), new.strip()
    if not (_FX_EXPR_RE.match(old) and _FX_EXPR_RE.match(new)):
        return None
    names = list(dict.fromkeys(_FX_IDENT_RE.findall(old) + _FX_IDENT_RE.findall(new)))
    if not names or any(_fx_known(v) is None for v in names):
        return None
    inputs = {v: _fx_known(v)[0] for v in names}
    ranged = [v for v in names if _fx_known(v)[1]]
    chart = None
    if ranged:
        _d, rng, lab = _fx_known(ranged[0])
        chart = (ranged[0], lab or _fx_words(ranged[0]), *rng)
    try:
        tag = _fx_tag(old, new, inputs, chart, tag)
    except Exception:          # not computable (a division by zero …): leave the rows
        return None
    name = _FX_NAME_TAIL_RE.sub('', name)
    args = [json.dumps(name), json.dumps(old), json.dumps(new), f'tag="{tag}"', f'inputs={json.dumps(inputs)}']
    if chart:
        args.append('chart=(' + ', '.join(json.dumps(x) for x in chart) + ')')
    unit = _fx_unit(name)
    if unit:
        args.append(f'unit="{unit}"')
    return 'W(formula_change(' + ', '.join(args) + '))'


def formula_block(line):
    """The formula_change call for a one-row "OLD: …<br>NEW: …" formula, else None."""
    m = _FX_ROW_RE.match(line)
    return formula_call(m.group('name'), m.group('tag'), m.group('old'), m.group('new')) if m else None


def _formula_triple(lines, i):
    """The formula_change call when lines[i:i+3] are the name row, an OLD row and a NEW row, else None."""
    if i + 2 >= len(lines):
        return None
    head = _FX_NAME_ROW_RE.match(lines[i].strip())
    a, b = (_FX_SIDE_RE.match(lines[j].strip()) for j in (i + 1, i + 2))
    if not (head and a and b and a.group('side').upper() == 'OLD' and b.group('side').upper() == 'NEW'):
        return None
    return formula_call(head.group('name'), head.group('tag'), a.group('expr'), b.group('expr'))


def _postprocess_formula_rows(lines):
    """Each old / new formula leaves its list as a block of its own; the lists left empty go."""
    from .post_general import _drop_empty_lists_general as _drop_empty_lists
    out, changed, i = [], False, 0
    while i < len(lines):
        block, used = formula_block(lines[i]), 1
        if block is None:
            block, used = _formula_triple(lines, i), 3
        if block is None:
            out.append(lines[i])
            i += 1
            continue
        out += ['W(ul_close())', block, 'W(ul_open())']
        changed = True
        i += used
    return _drop_empty_lists(out) if changed else lines
