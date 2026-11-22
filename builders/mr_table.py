"""One part for every Materials table (owner 2026-11-22: "единые правила на всех таблицах", Neutral Stats the reference).

Pages build their heads and name cells here, not each in its own way, so a table looks the same everywhere:
- head names always centred (CSS), the name column sortable with the site's sort mark;
- the two-floor head of Hero Stats: `tr.cat-row` of group heads over `tr.col-row`; a column with no group spans both
  floors (`th.th-tall`, rowspan 2), its name in the middle;
- one name cell for hero and item: `td.mr-name.hs-name` + `img.mr-ico` + `.mr-name-body > .mr-name-text`.
Rules in words: docs/agent-rules/ui-style.md, "Таблицы — единые правила".
"""
from __future__ import annotations

from html import escape


def _esc(s) -> str:
    return escape(str(s), quote=True)


def th(label: str, *, cls=(), sortable: bool = False, tall: bool = False, attrs: str = "") -> str:
    """A head cell. `sortable` adds the site's sort mark (the name column sorts on every table); `tall` makes it
    span both floors of a two-floor head."""
    classes = [c for c in (*cls, "sortable" if sortable else "", "th-tall" if tall else "") if c]
    cls_attr = f' class="{" ".join(classes)}"' if classes else ""
    span = ' rowspan="2"' if tall else ""
    inner = f'<span class="th-label">{label}</span><span class="sort-ind"></span>' if sortable else label
    return f"<th{cls_attr}{span}{attrs}>{inner}</th>"


def group_th(label: str, colspan: int, *, cls=()) -> str:
    """A group head over its columns, upper floor."""
    return f'<th class="{" ".join(("cat-head", *cls))}" colspan="{colspan}">{label}</th>'


def thead(top: list[str], low: list[str] | None = None) -> str:
    """One floor (`low` is None: `top` are the column heads) or two (`top` = groups and tall heads, `low` = the
    columns under the groups)."""
    if low is None:
        return f'<thead><tr class="col-row">{"".join(top)}</tr></thead>'
    return f'<thead><tr class="cat-row">{"".join(top)}</tr><tr class="col-row">{"".join(low)}</tr></thead>'


def table(cls: str, head: str, rows: list[str]) -> str:
    return f'<table class="mr-table hs-table {cls}">{head}<tbody>{"".join(rows)}</tbody></table>'


def icon(src: str | None, *, width: int, height: int, cls: str = "") -> str:
    """The name cell's picture; no file, no picture — a broken image showed its file name (design review 2026-11-19)."""
    if not src:
        return '<span class="mr-ico mr-ico-blank"></span>'
    extra = f" {cls}" if cls else ""
    return f'<img class="mr-ico{extra}" src="{src}" alt="" loading="lazy" width="{width}" height="{height}">'


def name_cell(name: str, img: str, *, cls: str = "", span: int = 1, sort_key: str | None = None,
              after: str = "") -> str:
    """The name cell of every table: picture, then the name (and `after`, e.g. the owner of an item's ability). Its
    icon grows on hover (`.mr-ico:hover`); `span` > 1 for an item of several rows — they sort and select together."""
    extra = f" {cls}" if cls else ""
    rs = f' rowspan="{span}"' if span > 1 else ""
    key = _esc(sort_key if sort_key is not None else name.lower())
    return (f'<td class="mr-name hs-name{extra}"{rs} data-sort="{key}">{img}<span class="mr-name-body">'
            f'<span class="mr-name-text">{_esc(name)}</span>{after}</span></td>')
