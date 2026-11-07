"""Notes under and beside rows: note_box (a stat's value now and the patch that last changed it), bug_note, subnote
(a list folded under a row), section_intro. Cut out of elements.py (2026-11-07)."""

import re

from .elements import _pop_list, info_tip
from .state import _State


# The owner's bug silhouette (icons/ui/bug.png, background cut to alpha, 2026-10-22), drawn as a CSS mask so it
# takes the box's colour; the hand-drawn pixel bugs read poorly at this size.
_BUG_SVG = '<span class="bug-ico" aria-hidden="true"></span>'


def bug_note(text):
    """A game bug next to a row: the [?] box with a bug instead of "?", never merged with the row's [?] tips."""
    return (f'<!--INLINETIP--><span class="info-tip bug-tip" tabindex="0" aria-label="Bug">{_BUG_SVG}'
            f'<span class="info-pop"><span class="info-pop-h">Bug</span>{_pop_list(text)}</span></span><!--/INLINETIP-->')


_BULLET_SPLIT = re.compile(r'(?:^|<br>)+\s*\*\s+', re.I)


def subnote(text):
    parts = _BULLET_SPLIT.split(text)
    intro_raw = parts[0] if parts else ''
    items = [p.strip() for p in parts[1:] if p.strip()]
    if len(items) >= 3:
        intro = re.sub(r'<br>+\s*$', '', intro_raw).rstrip(' :').strip()
        items_html = ''.join(f'<li>{it}</li>' for it in items)
        summary = (intro if intro else 'Show list') + \
                  f' <span class="subnote-count">({len(items)})</span>'
        return ('<ul class="subnotes"><li>'
                f'<details class="subnote-collapse">'
                f'<summary>{summary}</summary>'
                f'<ul class="subnote-items">{items_html}</ul>'
                '</details></li></ul>')
    return f'<ul class="subnotes"><li>{text}</li></ul>'


def section_intro(text):
    return f'<p class="section-intro">{text}</p>'


def _days_ago(version):
    if not version:
        return None
    from .meta import RELEASE_HISTORY
    date_str = None
    for row in RELEASE_HISTORY:
        if row.get('version') == version:
            date_str = row.get('date')
            break
    if not date_str:
        return None
    from datetime import datetime, date
    try:
        d = datetime.strptime(date_str, "%d.%m.%Y").date()
    except Exception:
        return None
    return (date.today() - d).days


def _patch_link(version):
    if not version:
        return ''
    return f'<span class="patch-ref"><b>{version}</b></span>'


def _format_age(days):
    if days is None:
        return None
    if days < 365:
        return f"{days} days ago"
    years = days // 365
    months = (days % 365) // 30
    yr = f"{years} year{'s' if years != 1 else ''}"
    if months == 0:
        return f"{yr} ago"
    mo = f"{months} month{'s' if months != 1 else ''}"
    return f"{yr} {mo} ago"


def _fmt_val(v):
    if v is None:
        return "?"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def note_box(text=None, *, hero=None, item=None, unit=None, field=None, before_patch=None,
             prev_val=None, prev_patch=None, new_val=None, extra_note=None):
    from .stats import stat_h, stat_i, stat_u, prev_change_patch_h, prev_change_patch_i, prev_change_patch_u
    cur = _State.current_patch_version
    if prev_val is None and (hero or item or unit):
        if hero:
            prev_val = stat_h(hero, field, before_patch)
            prev_patch = prev_change_patch_h(hero, field, before_patch) or before_patch
            if new_val is None and cur:
                new_val = stat_h(hero, field, cur)
        elif item:
            prev_val = stat_i(item, field, before_patch)
            prev_patch = prev_change_patch_i(item, field, before_patch) or before_patch
            if new_val is None and cur:
                new_val = stat_i(item, field, cur)
        else:
            prev_val = stat_u(unit, field, before_patch)
            prev_patch = prev_change_patch_u(unit, field, before_patch) or before_patch
            if new_val is None and cur:
                new_val = stat_u(unit, field, cur)
    show_val = new_val if new_val is not None else prev_val
    if show_val is not None and prev_patch is not None:
        if isinstance(prev_patch, str) and prev_patch.startswith("<"):
            ver = prev_patch[1:]
            tail = (f'Unchanged across all tracked patches '
                    f'(since {_patch_link(ver)}) — first recorded change')
        else:
            ago_phrase = _format_age(_days_ago(prev_patch))
            ago_str = f' <span class="days-ago">({ago_phrase})</span>' if ago_phrase else ''
            tail = f'Before this patch it was changed in {_patch_link(prev_patch)}{ago_str}'
        body = f"Now it's <b>{_fmt_val(show_val)}</b>. {tail}"
        if extra_note:
            body += f'<br>{extra_note}'
        return f'<!--INLINETIP-->{info_tip(body)}<!--/INLINETIP-->'
    note = text or ""
    if extra_note:
        note = f'{note}<br>{extra_note}' if note else extra_note
    return f'<!--INLINETIP-->{info_tip(note, header="Note:")}<!--/INLINETIP-->'
