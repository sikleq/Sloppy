"""Formula rows: formula_change (an old / new formula with its table of examples) and li_formula (a row whose value
is a formula, with its per-level table). Cut out of elements.py (2026-11-07)."""

import html as _html
import math
import re

from .elements import inline_note, li


def _fmt_formula(expr):
    expr = expr.replace('*', '×')
    return re.sub(
        r'[A-Za-z_]\w*|\d+(?:\.\d+)?',
        lambda m: (f'<span class="f-var">{m.group(0)}</span>'
                   if m.group(0)[0].isalpha() or m.group(0)[0] == '_'
                   else f'<span class="f-num">{m.group(0)}</span>'),
        expr)


def _eval_formula(expr, env):
    return eval(expr.replace('^', '**'), {"__builtins__": {}}, dict(env))


def _num_fmt(x):
    return f'{round(float(x), 1):g}'


def _formula_pct_badge(o, n, lower=False):
    from .badges import gradient_class
    if o == 0 or n == o:
        inner = '<span class="badge neutral">0%</span>'
    else:
        raw = (n - o) / o * 100
        is_buff = (n < o) if lower else (n > o)
        disp = ('+' if n > o else '-') + f'{round(abs(raw), 1):g}%'
        inner = f'<span class="badge {gradient_class(abs(raw), is_buff)}">{disp}</span>'
    return f'<span class="badge-group">{inner}</span>'


def formula_change(name, old, new, *, tag="REWORK", vary=None, fixed=None,
                   unit="", lower_better=False, inputs=None, chart=None):
    _TAG = {'NEW': ('new', 'new'), 'REWORK': ('rework', 'rework'), 'SWAP': ('swap', 'swap'),
            'BUFF': ('buff-text', 'buff'), 'NERF': ('nerf-text', 'nerf'),
            'DEL': ('del', 'del'), 'MISC': ('misc', 'misc'), 'QOL': ('qol', 'qol')}
    badge_cls, tag_id = _TAG.get(tag.upper(), (tag.lower(), tag.lower()))
    badge = f'<span class="badge {badge_cls}" data-tag="{tag_id}">{tag}</span>'
    if inputs:
        return _formula_live(name, old, new, badge, tag_id, inputs, chart, unit, lower_better)
    has_ex = bool(vary)
    has_input = bool(vary and fixed)
    input_html = ''
    data_attrs = ''
    if has_input:
        var_name, label, values = vary
        in_var = next(iter(fixed))
        in_def = fixed[in_var]
        def_disp = f'{in_def:,}' if isinstance(in_def, int) else f'{in_def:g}'
        input_html = (
            '<div class="formula-input-row">'
            f'<span class="formula-input-label">Set <span class="fx-vname">{in_var}</span>:</span>'
            '<input type="number" class="formula-input" min="0" inputmode="numeric" '
            f'placeholder="By default: {def_disp}"></div>')
        data_attrs = (
            f' data-fx-old="{_html.escape(old, quote=True)}"'
            f' data-fx-new="{_html.escape(new, quote=True)}"'
            f' data-fx-invar="{in_var}" data-fx-default="{in_def}"'
            f' data-fx-varyvar="{var_name}" data-fx-lower="{1 if lower_better else 0}"')

    def _ex_table(this_is_old):
        if not has_ex:
            return ''
        var_name, label, values = vary
        th_pct = '' if this_is_old else '<th class="fx-pct-h">Δ%</th>'
        head = f'<thead><tr><th>{label}</th><th>{unit}</th>{th_pct}</tr></thead>'
        body = ''
        for v in values:
            env = dict(fixed or {})
            env[var_name] = v
            oval = _eval_formula(old, env)
            nval = _eval_formula(new, env)
            if this_is_old:
                body += (f'<tr data-h="{v}"><td class="fx-k">{v}</td>'
                         f'<td class="fx-gold">{_num_fmt(oval)}</td></tr>')
            else:
                body += (f'<tr data-h="{v}"><td class="fx-k">{v}</td>'
                         f'<td class="fx-gold">{_num_fmt(nval)}</td>'
                         f'<td class="fx-pct">{_formula_pct_badge(oval, nval, lower_better)}</td></tr>')
        return f'<table class="formula-ex">{head}<tbody>{body}</tbody></table>'

    def _pane(expr, cls, is_old):
        return (f'<div class="formula-pane formula-pane-{cls}">'
                f'<code class="formula-expr">{_fmt_formula(expr)}</code>'
                f'{_ex_table(is_old)}</div>')

    return (f'<div class="formula-change" data-tag="{tag_id}"{data_attrs}>'
            f'<div class="formula-change-title">{badge}'
            f'<span class="formula-change-name">{name}</span></div>'
            f'{input_html}'
            f'<div class="formula-change-panes">'
            f'{_pane(old, "old", True)}'
            f'<span class="ability-change-arrow">→</span>'
            f'{_pane(new, "new", False)}'
            f'</div></div>')


# ---- Live formula (inputs= + chart=): a field for every variable, the OLD and NEW result, a chart of both curves ----
# The chart's geometry is mirrored in src/js/formula-calculator.js (FX_* there): change both together.
FX_W, FX_H = 480, 190
FX_PAD_L, FX_PAD_R, FX_PAD_T, FX_PAD_B = 44, 14, 22, 40


def _fx_gap_pieces(xs, po, pn):
    """The stretches where one curve stays above the other, split where they cross:
    [(sign, [(x, old, new), …])], sign = +1 where new > old, -1 where new < old."""
    pieces = []
    for i in range(len(xs) - 1):
        x0, x1, o0, o1, n0, n1 = xs[i], xs[i + 1], po[i], po[i + 1], pn[i], pn[i + 1]
        d0, d1 = n0 - o0, n1 - o1
        segs = [((x0, o0, n0), (x1, o1, n1))]
        if d0 * d1 < 0:                     # they cross inside: split at the crossing
            t = d0 / (d0 - d1)
            xc, yc = x0 + t * (x1 - x0), o0 + t * (o1 - o0)
            segs = [((x0, o0, n0), (xc, yc, yc)), ((xc, yc, yc), (x1, o1, n1))]
        for a, b in segs:
            mid = (a[2] - a[1]) + (b[2] - b[1])
            sign = (mid > 0) - (mid < 0)
            if not sign:
                continue
            if pieces and pieces[-1][0] == sign and pieces[-1][1][-1] == a:
                pieces[-1][1].append(b)
            else:
                pieces.append((sign, [a, b]))
    return pieces


def _fx_nice(lo, hi, n=4):
    """Round y-axis bounds and step (1 / 2 / 2.5 / 5 x 10^k) giving about n gaps."""
    if hi <= lo:
        hi = lo + 1
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    return math.floor(lo / step) * step, math.ceil(hi / step) * step, step


def _fx_xticks(lo, hi):
    if hi - lo <= 10:
        return list(range(lo, hi + 1))
    every = 5 if hi - lo <= 60 else 10
    return [lo] + [v for v in range(lo + 1, hi + 1) if v % every == 0]


def _fx_chart_body(old, new, env, var, label, lo, hi, unit='', lower=False):
    """The SVG inside of the chart for these inputs (the JS draws the same on every change)."""
    xs = list(range(lo, hi + 1))
    po = [_eval_formula(old, {**env, var: x}) for x in xs]
    pn = [_eval_formula(new, {**env, var: x}) for x in xs]
    y0, y1, step = _fx_nice(min(po + pn), max(po + pn))
    pw, ph = FX_W - FX_PAD_L - FX_PAD_R, FX_H - FX_PAD_T - FX_PAD_B
    sx = lambda x: FX_PAD_L + (x - lo) / (hi - lo) * pw
    sy = lambda y: FX_PAD_T + (y1 - y) / (y1 - y0) * ph
    parts = []
    y = y0
    while y <= y1 + step / 2:
        yy = round(sy(y), 1)
        parts.append(f'<line class="fx-grid" x1="{FX_PAD_L}" x2="{FX_W - FX_PAD_R}" y1="{yy}" y2="{yy}"/>'
                     f'<text class="fx-tick fx-tick-y" x="{FX_PAD_L - 6}" y="{yy}">{_num_fmt(y)}</text>')
        y += step
    base = FX_H - FX_PAD_B
    for x in _fx_xticks(lo, hi):
        xx = round(sx(x), 1)
        parts.append(f'<line class="fx-grid" x1="{xx}" x2="{xx}" y1="{FX_PAD_T}" y2="{base}"/>'
                     f'<text class="fx-tick fx-tick-x" x="{xx}" y="{base + 14}">{x}</text>')
    parts.append(f'<text class="fx-axis" x="{FX_PAD_L + pw / 2:g}" y="{FX_H - 4}">{_html.escape(label)}</text>')
    if unit:
        parts.append(f'<text class="fx-axis fx-axis-y" x="{FX_PAD_L - 6}" y="{FX_PAD_T - 10}">{_html.escape(unit)}</text>')
    p = lambda x, y: f'{round(sx(x), 1):g},{round(sy(y), 1):g}'
    for sign, seg in _fx_gap_pieces(xs, po, pn):     # the gap between the curves: green better, red worse
        better = (sign < 0) if lower else (sign > 0)
        ring = [p(x, n) for x, _o, n in seg] + [p(x, o) for x, o, _n in reversed(seg)]
        parts.append(f'<polygon class="fx-gap {"fx-gain" if better else "fx-loss"}" points="{" ".join(ring)}"/>')
    parts.append(f'<polyline class="fx-line fx-line-old" points="{" ".join(p(x, v) for x, v in zip(xs, po))}"/>')
    parts.append(f'<polyline class="fx-line fx-line-new" points="{" ".join(p(x, v) for x, v in zip(xs, pn))}"/>')
    cur = env.get(var)
    if cur is not None and lo <= cur <= hi:
        parts.append(_fx_marker(sx(cur), sy(_eval_formula(old, env)), sy(_eval_formula(new, env)),
                                _eval_formula(old, env), _eval_formula(new, env), base))
    return ''.join(parts)


def _fx_marker(cx, yo, yn, o, n, base):
    """The ruler at the entered value, a dot on each curve and its number beside it (on the left near the right edge);
    the upper number sits above its dot, the lower one below, so the two never overlap."""
    cx = round(cx, 1)
    right = cx < FX_W - FX_PAD_R - 70
    tx, anchor = (cx + 7, 'start') if right else (cx - 7, 'end')
    new_up = yn <= yo
    lab = lambda cls, y, v, up: (f'<text class="fx-mark fx-mark-{cls}" x="{tx}" y="{round(y + (-6 if up else 12), 1):g}" '
                                 f'text-anchor="{anchor}">{_num_fmt(v)}</text>')
    return (f'<line class="fx-ruler" x1="{cx}" x2="{cx}" y1="{FX_PAD_T}" y2="{base}"/>'
            f'<rect class="fx-dot fx-dot-old" x="{cx - 3:g}" y="{round(yo, 1) - 3:g}" width="6" height="6"/>'
            f'<rect class="fx-dot fx-dot-new" x="{cx - 3:g}" y="{round(yn, 1) - 3:g}" width="6" height="6"/>'
            + lab('old', yo, o, not new_up) + lab('new', yn, n, new_up))


def _formula_live(name, old, new, badge, tag_id, inputs, chart, unit, lower_better):
    names = list(inputs)
    env = dict(inputs)
    fields = ''
    for v in names:
        d = inputs[v]
        disp = f'{d:,}' if isinstance(d, int) else f'{d:g}'
        rng = (f' min="{chart[2]}" max="{chart[3]}" step="1"' if chart and v == chart[0] else ' min="0"')
        fields += (f'<label class="formula-input-cell">'
                   f'<span class="formula-input-label">Set <span class="fx-vname">{v}</span>:</span>'
                   f'<input type="number" class="formula-input" data-var="{v}" data-default="{d}"{rng} '
                   f'inputmode="decimal" placeholder="By default: {disp}"></label>')
    o, n = _eval_formula(old, env), _eval_formula(new, env)
    unit_html = f' <span class="fx-unit">{unit}</span>' if unit else ''

    def _pane(expr, cls, val, pct):
        return (f'<div class="formula-pane formula-pane-{cls}">'
                f'<code class="formula-expr">{_fmt_formula(expr)}</code>'
                f'<div class="fx-result"><span class="fx-val fx-val-{cls}">{_num_fmt(val)}</span>{unit_html}{pct}</div>'
                f'</div>')

    chart_html = ''
    attrs = (f' data-fx-old="{_html.escape(old, quote=True)}" data-fx-new="{_html.escape(new, quote=True)}"'
             f' data-fx-vars="{",".join(names)}" data-fx-lower="{1 if lower_better else 0}"')
    if chart:
        var, label, lo, hi = chart
        if var not in inputs:
            raise ValueError(f'formula_change chart variable {var!r} has no input')
        attrs += (f' data-fx-chart="{var}" data-fx-lo="{lo}" data-fx-hi="{hi}"'
                  f' data-fx-label="{_html.escape(label, quote=True)}" data-fx-unit="{_html.escape(unit, quote=True)}"')
        chart_html = (f'<div class="fx-chart"><svg class="fx-svg" viewBox="0 0 {FX_W} {FX_H}" '
                      f'preserveAspectRatio="xMidYMid meet">'
                      f'{_fx_chart_body(old, new, env, var, label, lo, hi, unit, lower_better)}</svg></div>')
    return (f'<div class="formula-change formula-live" data-tag="{tag_id}"{attrs}>'
            f'<div class="formula-change-title">{badge}'
            f'<span class="formula-change-name">{name}</span></div>'
            f'<div class="formula-input-row">{fields}</div>'
            f'<div class="formula-change-panes">'
            f'{_pane(old, "old", o, "")}'
            f'<span class="ability-change-arrow">→</span>'
            f'{_pane(new, "new", n, _formula_pct_badge(o, n, lower_better))}'
            f'</div>{chart_html}</div>')


def li_formula(prefix, old_formula, new_formula, old_fn, new_fn, l=False,
               rework_badge=True, inline_note_text=None, label=None,
               force_rework=False, extra_html=None, after_html=None, **bf_kwargs):
    """extra_html: a box that goes before the table (note_box of a wrongly stated "from", 7.42 Tormentor Reflect);
    after_html: one under it (formula_approx, Valve's approximation of the 7.42 experience per level)."""
    from .badges import bf
    if label:
        bf_kwargs.setdefault('axis_label', label)
        bf_kwargs.setdefault('jump_at', None)
    bf_kwargs.setdefault('extra_formulas', (old_formula,))   # old -> new steps: union of breakpoints
    trigger, badge, table = bf(old_fn, new_fn, new_formula, l=l, **bf_kwargs)
    if force_rework:
        badge = '<span class="badge-group"></span>'
    full_text = (f'{prefix} from <span class="formula-old">{old_formula}</span> '
                 f'to {trigger}')
    overall_match = re.search(r'data-overall="(buff|nerf)"', badge)
    force_match = re.search(r'data-force-left="(buff|nerf)"', badge)
    kind = (force_match.group(1) if force_match
            else overall_match.group(1) if overall_match
            else None)
    if kind and not force_rework:
        cls = "buff-text" if kind == "buff" else "nerf-text"
        label = "BUFF" if kind == "buff" else "NERF"
        full_badge = (f'<span class="badge {cls}" data-tag="{kind}" '
                      f'data-overall="{kind}">{label}</span>' + badge)
    elif bf_kwargs.get('effective_unchanged'):
        full_badge = ('<span class="badge misc" data-tag="misc">MISC</span>'
                      + badge)
    elif rework_badge:
        full_badge = ('<span class="badge rework" data-tag="rework">REWORK</span>'
                      + badge)
    else:
        full_badge = badge
    extra = table
    if inline_note_text:
        extra = inline_note(inline_note_text) + extra
    if extra_html:
        extra = extra_html + extra
    if after_html:
        extra = extra + after_html
    return li(full_text, full_badge, extra=extra)
