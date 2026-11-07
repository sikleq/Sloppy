"""Formula rows: formula_change (an old / new formula with its table of examples) and li_formula (a row whose value
is a formula, with its per-level table). Cut out of elements.py (2026-11-07)."""

import html as _html
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
                   unit="", lower_better=False):
    _TAG = {'NEW': ('new', 'new'), 'REWORK': ('rework', 'rework'), 'SWAP': ('swap', 'swap'),
            'BUFF': ('buff-text', 'buff'), 'NERF': ('nerf-text', 'nerf'),
            'DEL': ('del', 'del'), 'MISC': ('misc', 'misc'), 'QOL': ('qol', 'qol')}
    badge_cls, tag_id = _TAG.get(tag.upper(), (tag.lower(), tag.lower()))
    badge = f'<span class="badge {badge_cls}" data-tag="{tag_id}">{tag}</span>'
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


def li_formula(prefix, old_formula, new_formula, old_fn, new_fn, l=False,
               rework_badge=True, inline_note_text=None, label=None,
               force_rework=False, **bf_kwargs):
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
    return li(full_text, full_badge, extra=extra)
