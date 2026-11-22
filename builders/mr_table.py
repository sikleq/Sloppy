"""One part for every Materials table (owner 2026-11-22: "единые правила на всех таблицах", Neutral Stats the reference).

Pages build their heads and name cells here, not each in its own way, so a table looks the same everywhere:
- head names always centred (CSS), the name column sortable with the site's sort mark;
- the two-floor head of Hero Stats: `tr.cat-row` of group heads over `tr.col-row`; a column with no group spans both
  floors (`th.th-tall`, rowspan 2), its name in the middle;
- one name cell for hero and item: `td.mr-name.hs-name` + `img.mr-ico` + `.mr-name-body > .mr-name-text`.
Rules in words: docs/agent-rules/ui-style.md, "Таблицы — единые правила".
"""
from __future__ import annotations

import re
from html import escape
from pathlib import Path


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


def table(cls: str, head: str, rows: list[str], attrs: str = "") -> str:
    return f'<table class="mr-table hs-table {cls}"{attrs}>{head}<tbody>{"".join(rows)}</tbody></table>'


def icon(src: str | None, *, width: int, height: int, cls: str = "") -> str:
    """The name cell's picture; no file, no picture — a broken image showed its file name (design review 2026-11-19)."""
    if not src:
        return '<span class="mr-ico mr-ico-blank"></span>'
    extra = f" {cls}" if cls else ""
    return f'<img class="mr-ico{extra}" src="{src}" alt="" loading="lazy" width="{width}" height="{height}">'


def slugify(name: str) -> str:
    """The file name of a hero's or a unit's own page, from its name (as patch.elements._slugify)."""
    s = name.lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# every name in a table leads to its own page (owner 2026-11-22: "во всех таблицах сделать ссылки-переходы").
# The pages are named by the display name ("Battle Fury" -> items/battle-fury.html, not the key "bfury") and written by
# builders/entity_changes.py, which build_site.py runs before the tables; a name with no page (an item new in a patch
# not annotated yet) stays plain text rather than a dead link.
_DIST = Path(__file__).resolve().parent.parent / "dist"


def _href(folder: str, name: str, prefix: str) -> str | None:
    rel = f"{folder}/{slugify(name)}.html"
    return f"{prefix}{rel}" if (_DIST / rel).exists() else None


def hero_href(name: str, prefix: str = "") -> str | None:
    return _href("heroes", name, prefix)


def item_href(name: str, prefix: str = "", key: str | None = None) -> str | None:
    """`name` — the item's display name ("Eye of Skadi"); `key` — its items.txt key ("item_robe"), for the few pages
    named by the key (Robe of the Magi -> items/robe.html, Mantle of Intelligence -> items/mantle.html)."""
    return _href("items", name, prefix) or (_href("items", key.removeprefix("item_"), prefix) if key else None)


def name_text(name: str, href: str | None = None, cls: str = "mr-name-text") -> str:
    """The name, a link to its page when `href` is given (`a.ec-name-link`, as Hero Stats)."""
    if href:
        return f'<a class="{cls} ec-name-link" href="{_esc(href)}">{_esc(name)}</a>'
    return f'<span class="{cls}">{_esc(name)}</span>'


def name_cell(name: str, img: str, *, cls: str = "", span: int = 1, sort_key: str | None = None,
              after: str = "", href: str | None = None, attrs: str = "") -> str:
    """The name cell of every table: picture, then the name (and `after`, e.g. the owner of an item's ability). Its
    icon grows on hover (`.mr-ico:hover`); `span` > 1 for an item of several rows — they sort and select together.
    `href`: the name links to its own page."""
    extra = f" {cls}" if cls else ""
    rs = f' rowspan="{span}"' if span > 1 else ""
    key = _esc(sort_key if sort_key is not None else name.lower())
    return (f'<td class="mr-name hs-name{extra}"{rs}{attrs} data-sort="{key}">{img}<span class="mr-name-body">'
            f'{name_text(name, href)}{after}</span></td>')
