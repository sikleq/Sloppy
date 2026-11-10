"""A row that adds new levels to many values at once, as one table (owner 2026-11-08, 7.38 Invoker "Added values for
levels 9 and 10": the [?] list of 21 "Cold Snap: Duration (Quas) 6.2/6.6s" lines was "массивный"; variant B chosen):
the text opens a table — ability (icon, once per group) | value | the orb or skill it grows with | every level, the
new levels gold."""

from .badges import _formula_id_counter
from .elements import li
from .images import abil_img


def _ability_cell(slug, name, span):
    return (f'<th class="lv-ab" rowspan="{span}"><span class="lv-ab-in"><img src="{abil_img(slug)}" alt="" '
            f'loading="lazy"><span>{name}</span></span></th>')


def level_values_table(rows, new_from, fid):
    """rows = [(ability slug, ability name, value label, scaling slug or None, "v1 v2 … vN", unit)]."""
    count = max(len(r[4].split()) for r in rows)
    has_scale = any(r[3] for r in rows)
    head = ("<th>Ability</th><th>Value</th>" + ("<th></th>" if has_scale else "")
            + "".join(f'<th{" class=lv-new" if n >= new_from else ""}>{n}</th>' for n in range(1, count + 1)))
    body, i = [], 0
    while i < len(rows):
        span = next((j for j in range(i, len(rows)) if rows[j][0] != rows[i][0]), len(rows)) - i
        for k, (slug, name, label, scale, values, unit) in enumerate(rows[i:i + span]):
            cells = "".join(f'<td{" class=lv-new" if n >= new_from else ""}>{v}</td>'
                            for n, v in enumerate(values.split(), 1))
            scale_td = (f'<td class="lv-scale"><img src="{abil_img(scale)}" alt="" title="{scale.split("_")[-1].title()}">'
                        f'</td>' if scale else '<td class="lv-scale"></td>') if has_scale else ""
            label_html = f'{label} ({unit})' if unit else label
            body.append(f'<tr{" class=lv-first" if k == 0 else ""}>'
                        + (_ability_cell(slug, name, span) if k == 0 else "")
                        + f'<td class="lv-label">{label_html}</td>{scale_td}{cells}</tr>')
        i += span
    return (f'<table class="formula-table lv-values" id="{fid}" hidden>'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>')


def li_level_values(lead, trigger, rows, new_from, tag):
    """`lead` + `trigger` (the dotted words that open the table): "Added values for " + "levels 9 and 10"."""
    _formula_id_counter[0] += 1
    fid = f"f{_formula_id_counter[0]}"
    text = f'{lead}<span class="formula-trigger" data-formula="{fid}">{trigger}</span>'
    return li(text, tag, extra=level_values_table(rows, new_from, fid))
