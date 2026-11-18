"""A game formula written as "OLD: <formula><br>NEW: <formula>" -> a live formula_change block: a field for every
variable, the old and new result, a chart of both curves (owner 2026-11-18, pilot 7.42 "Hero kill bounty rescaled")."""
import json
import re

from patch.formula_rows import _eval_formula

# W(li("<name>", t("<TAG>"), extra=inline_note("OLD: <formula><br>NEW: <formula>")))
_FX_ROW_RE = re.compile(
    r'^W\(li\("(?P<name>[^"]+)", t\("(?P<tag>\w+)"\), '
    r'extra=inline_note\("OLD: ?(?P<old>[^"<]+?)<br>NEW: ?(?P<new>[^"<]+?)"\)\)\)$')
_FX_EXPR_RE = re.compile(r'^[\w\s.+\-*/^()]+$')
_FX_IDENT_RE = re.compile(r'[A-Za-z_]\w*')
_FX_NAME_TAIL_RE = re.compile(r'\s+(?:rescaled|reworked|changed|adjusted|updated)$', re.I)

# The variables we know: (name pattern, default value, chart range or None). A formula with any other variable
# stays a note: a default we would have to guess is worse than none.
_FX_KNOWN_VARS = (
    (re.compile(r'Level$'), 15, (1, 30)),                     # a hero level: chart 1-30, the default mid-game
    (re.compile(r'^NumHeroes$'), 1, (1, 5)),                  # heroes sharing the gold: 1-5, the team size
    (re.compile(r'Networth$|^NW$'), 10000, None),            # networth-style -> 10000 (docs/formula-change.md)
    (re.compile(r'(?:Kill)?[Ss]treak'), 0, None),              # no streak by default
)


def _fx_known(var):
    return next(((d, rng) for pat, d, rng in _FX_KNOWN_VARS if pat.search(var)), None)


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


def formula_block(line):
    """The formula_change call for a row like that, or None when it is not a formula we can compute."""
    m = _FX_ROW_RE.match(line)
    if not m:
        return None
    old, new = m.group('old').strip(), m.group('new').strip()
    if not (_FX_EXPR_RE.match(old) and _FX_EXPR_RE.match(new)):
        return None
    names = list(dict.fromkeys(_FX_IDENT_RE.findall(old) + _FX_IDENT_RE.findall(new)))
    if not names or any(_fx_known(v) is None for v in names):
        return None
    inputs = {v: _fx_known(v)[0] for v in names}
    ranged = [v for v in names if _fx_known(v)[1]]
    chart = (ranged[0], _fx_words(ranged[0]), *_fx_known(ranged[0])[1]) if ranged else None
    try:
        tag = _fx_tag(old, new, inputs, chart, m.group('tag'))
    except Exception:          # not computable (a division by zero …): leave the note
        return None
    name = _FX_NAME_TAIL_RE.sub('', m.group('name'))
    args = [json.dumps(name), json.dumps(old), json.dumps(new), f'tag="{tag}"', f'inputs={json.dumps(inputs)}']
    if chart:
        args.append('chart=(' + ', '.join(json.dumps(x) for x in chart) + ')')
    unit = _fx_unit(name)
    if unit:
        args.append(f'unit="{unit}"')
    return 'W(formula_change(' + ', '.join(args) + '))'


def _postprocess_formula_rows(lines):
    """Each OLD / NEW formula row leaves its list as a block of its own; the lists left empty go."""
    from .post_general import _drop_empty_lists
    out, changed = [], False
    for line in lines:
        block = formula_block(line)
        if block is None:
            out.append(line)
            continue
        out += ['W(ul_close())', block, 'W(ul_open())']
        changed = True
    return _drop_empty_lists(out) if changed else lines
