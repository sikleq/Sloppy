"""Build item_potency.html — the "Item Potency" page (Materials → Mechanics), as AoE Increase (owner 2026-11-19).

Little text, colour for meaning (owner 2026-11-19: "мешанина … не читается из-за обилия текста и отсутствия цветовых
индикаторов"):
  * rules as cards — a short title, the formula in the site's formula look, an example before → after;
  * items: one row per scaled value — ability, the value's name (the game's tooltip sentence in its hover), the value
    for a hero (100%) and the same at the usual potencies of illusions (20% default, Manta 35%, Illusion Rune 40%);
    items no one can get in this patch dimmed;
  * sources: what sets the potency of attacks, the potency as a chip — green above 100% / a bonus, red below / a
    penalty;
Dormant Curio is a mechanic of its own (owner 2026-11-21: "вынести на свою страницу"): builders/dormant_curio.py.
Data: the newest patch's items.txt flags (apply_effectiveness / apply_curio_bonus) and the code research of 7.42
(data/rules/item_potency_abilities.json). Nothing guessed.

    python builders/item_potency.py
"""
from __future__ import annotations

import html as _html
import json as _json
import re as _re
import sys as _sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_HERE))
_sys.path.insert(0, str(_HERE / "builders"))

import patch.site_common as _site  # noqa: E402
from patch.formula_rows import _fmt_formula  # noqa: E402
from patch.item_ability_text import _clean, _fill, _items, _values  # noqa: E402
from patch.item_marks import _flagged, _sentences  # noqa: E402
from patch.images import abil_img  # noqa: E402
from patch.loc_history import tooltip  # noqa: E402
from patch.rosters import items_in_game, items_removed  # noqa: E402
import mr_table as _mt  # noqa: E402
from heroes_stats import _display_name, _latest_href, _load_display_names, _versions  # noqa: E402

_esc = lambda s: _html.escape(str(s), quote=True)
RULES = _HERE / "data" / "rules" / "item_potency_abilities.json"
ITEM_CDN = "icons/items/"
ILLUSIONS = (("Illusion", 20), ("Manta", 35), ("Rune", 40))     # the usual potencies of an illusion
# the site's "Removed" switch, as Neutral Stats' (builders/creeps.py; owner 2026-11-21: "Show removed кнопка не похожа на
# те, что у нас на сайте с подобным функционалом")
# in the site's filter card, as Neutral Stats' toolbar (design review 2026-11-21)
REMOVED_BUTTON = ('<div class="cal-toggle-bar inbox-bar ipot-tools"><div class="toolbar-panel">'
                  '<button type="button" class="hs-attack-filter ipot-show-gone" '
                  'aria-pressed="false"><span>Removed</span></button></div></div>')


def _root(src):
    return src[3:] if src.startswith("../") else src


def _num(v):
    try:
        return float(str(v).split("/")[0])
    except ValueError:
        return None


def _fmt(x):
    return f"{round(x, 2):g}"


def _label(key, ability):
    """"cold_slow_melee" → "Slow (melee)" — the value's own name, its ability's words dropped."""
    words = key.split("_")
    side = [w for w in words if w in ("melee", "ranged")]
    words = [w for w in words if w not in ("melee", "ranged")]
    # only the ability's first word: "cold_slow" / "cold_attack_slow" are the move and the attack slow (Eye of Skadi)
    first = (ability.lower().split() or [""])[0]
    if len(words) > 1 and words[0] == first:
        words = words[1:]
    text = " ".join(words).capitalize() or key
    return f"{text} ({side[0]})" if side else text


def _scaled_values(version, flag, with_removed=False):
    """[(item name, item key, slug, [(ability, label, value, sentence)])] of every item with a value flagged so."""
    out = []
    # not the never-added / cycled-out ones items.txt keeps (owner 2026-11-22); `with_removed` adds the removed ones
    in_game = items_in_game(version) | (items_removed(version) if with_removed else frozenset())
    for key, blk in _items(version).items():
        if not (isinstance(blk, dict) and key.startswith("item_") and not key.startswith("item_recipe")):
            continue
        if key not in in_game:
            continue
        keys = _flagged(blk, flag)
        if not keys:
            continue
        slug = key[len("item_"):]
        vals = _values(blk)
        desc = tooltip(f"DOTA_Tooltip_Ability_{key}_Description", version) or ""
        sents = _sentences(desc)
        rows = []
        for k in keys:
            hit = next(((n, s) for n, s in sents if _re.search(rf"%{k}%", s, _re.I)), ("", ""))
            text = _fill(hit[1], vals) if hit[1] else None
            ab = hit[0] or (rows[-1][0] if rows else (sents[0][0] if sents else ""))   # a value no sentence names
            rows.append((ab, _label(k, ab), vals.get(k, "?"), _clean(text) if text else ""))
        name = tooltip(f"DOTA_Tooltip_Ability_{key}", version) or slug.replace("_", " ").title()
        out.append((name, key, slug, rows))
    return sorted(out, key=lambda r: r[0].lower())


def _hero_of(ability, version, names):
    heroes = _json.loads((_HERE / "data" / "stats" / version / "heroes.json").read_text(encoding="utf-8"))
    for npc, blk in heroes.items():
        if isinstance(blk, dict) and ability in {v for k, v in blk.items()
                                                 if k.startswith("Ability") and isinstance(v, str)}:
            return _display_name(npc, names)
    # an ability outside the hero's slots (Ringmaster's souvenir Funhouse Mirror, owner 2026-11-22: "ведёт к
    # Ringmaster, это его способность"): the hero its name starts with
    for npc in heroes:
        if ability.startswith(npc.removeprefix("npc_dota_hero_") + "_"):
            return _display_name(npc, names)
    return ""


def _section(title, table):
    return f'<section class="ipot-sec"><h3 class="ipot-title">{title}</h3>{table}</section>'


_TEXT_HEADS = {"Ability", "Value", "Attacks", "Illusions"}      # word columns: their heads left, as their cells


def _th(h, i, extra=(), tall=False):
    """The first column — the item's or the ability's name — sorts by name, with the site's sort mark, as AoE Increase's
    Hero (owner 2026-11-22: "в одной вкладке нажимаются и сортируются … в другой нет"); the others do not: one column
    holds values of different kinds (chance, armor, mana)."""
    cls = ("ipot-th-text" if h in _TEXT_HEADS and i else "", "ipot-th-ab" if h == "Ability" and i else "", *extra)
    return _mt.th(h, cls=cls, sortable=i == 0, tall=tall)


def _table(cls, head, rows, groups=()):
    """`groups`: (label, columns) for a row of groups over the columns — the two-floor header of Hero Stats and Neutral
    Stats (owner 2026-11-21 chose variant 1 of the header mock: one system for the site's tables). A column with no
    group ("" label) takes both floors, its name in the middle ("hero можно в центр ячейке поставить"); the first
    column of "Illusions" starts the illusions' 2px line, in both floors. Built by the shared builders/mr_table.py."""
    if not groups:
        return _mt.table(f"ipot-table {cls}", _mt.thead([_th(h, i) for i, h in enumerate(head)]), rows)
    top, low, i = [], [], 0
    for label, n in groups:
        ill = ("ipot-ill-first",) if label == "Illusions" else ()
        if not label:
            top += [_th(head[k], k, tall=True) for k in range(i, i + n)]
        else:
            top.append(_mt.group_th(label, n, cls=ill))
            low += [_th(head[k], k, ill if k == i else ()) for k in range(i, i + n)]
        i += n
    return _mt.table(f"ipot-table {cls}", _mt.thead(top, low), rows)


def _name_cell(name, icon, owner="", span=1, wide=True, href=None):
    w, h = (44, 32) if wide else (32, 32)
    who = f'<span class="ipot-owner">{_esc(owner)}</span>' if owner else ''
    img = _mt.icon(icon if icon and (_HERE / icon).exists() else None, width=w, height=h,
                   cls="" if wide else "ipot-ico-sq")
    # the cell of AoE Increase's hero and Hero Stats' (owner 2026-11-21: "достичь единого формата в обеих вкладках")
    return _mt.name_cell(name, img, cls="ipot-name", span=span, after=who, href=href)


def _chip(text):
    """"60%" / "+20%" / "125%" / "−25%" → a chip in the colour of what it does to items: above 100% or a bonus green,
    below or a penalty red, other text plain."""
    m = _re.search(r"([+\-−]?)(\d+(?:\.\d+)?)%", text)
    tone = ""
    if m:
        sign, v = m.group(1), float(m.group(2))
        tone = ("buff" if sign == "+" else "nerf" if sign in "-−" and sign else
                "buff" if v > 100 else "nerf" if v < 100 else "")
    return f'<span class="ipot-chip{f" ipot-{tone}" if tone else ""}">{_esc(text)}</span>'


def _rules_cards(rules, extra=""):
    """`extra`: one more card at the row's end (Item Potency's "Removed" switch, owner 2026-11-21: "кнопку removed может
    куда-то сюда" — the empty room right of the rule cards)."""
    cards = []
    for title, formula, (a, b, what) in rules["rules"]:
        ex = (f'<span class="ipot-ex-old">{_esc(a)}</span> → <span class="ipot-ex-new">{_esc(b)}</span>'
              f'<span class="ipot-ex-what">{_esc(what)}</span>')
        cards.append(f'<div class="ipot-rule"><div class="ipot-rule-h">{_esc(title)}</div>'
                     f'<code class="formula-expr">{_fmt_formula(formula)}</code><div class="ipot-rule-ex">{ex}</div></div>')
    return f'<div class="ipot-rules">{"".join(cards)}{extra}</div>'


# the game's own notes on an item that its effect does not come from illusions (owner 2026-11-21: "basher/abyssal не
# работает на иллюзиях, а столбец есть … надо учитывать"): "Does not grant Bash to Clones, Illusions…", "Chain Lightning
# does not trigger off of attacks from illusions", "Illusions do not apply Witch Blade, but can apply Magic Corruption",
# "Does not trigger on attacks from illusions" (the whole item)
_NO_ILL = (
    _re.compile(r"does not grant (?P<ab>[A-Z][\w' ]+?) to [^.]*\billusions", _re.I),
    _re.compile(r"^(?P<ab>[A-Z][\w' ]+?) does not (?:trigger|proc|work)[^.]*\billusions", _re.I),
    _re.compile(r"^Illusions do not (?:apply|trigger|proc) (?P<ab>[A-Z][\w' ]+?)(?:,|\.|$)", _re.I),
    _re.compile(r"^Does not (?:trigger|proc|work)[^.]*\b(?:from|for|on) (?:attacks from )?illusions", _re.I),
)


def no_illusions(key, version):
    """{ability name (lower) or "*" for the whole item: the game's note} — what illusions of the holder do not get."""
    out = {}
    for i in range(8):
        note = tooltip(f"DOTA_Tooltip_ability_{key}_Note{i}", version) or tooltip(
            f"DOTA_Tooltip_Ability_{key}_Note{i}", version)
        if not note:
            continue
        for rx in _NO_ILL:
            m = rx.search(note.strip())
            if m:
                ab = m.groupdict().get("ab")
                out[ab.strip().lower() if ab else "*"] = note.strip()
                break
    return out


_SIDE = _re.compile(r"^(?P<base>.+?) \((?P<side>melee|ranged)\)$")


def _melee_ranged(vals):
    """A value given for melee and for ranged heroes is one row "Chance (melee / ranged)" → "25 / 10" (owner
    2026-11-21: "через слеш, а не в 2 строки"), the melee one first; the rest as they were."""
    out, used = [], set()
    for i, (ab, label, value, sentence) in enumerate(vals):
        if i in used:
            continue
        m = _SIDE.match(label)
        if m:
            other = "ranged" if m.group("side") == "melee" else "melee"
            j = next((j for j, v in enumerate(vals) if j not in used and j != i and v[0] == ab
                      and v[1] == f"{m.group('base')} ({other})"), None)
            if j is not None:
                used.add(j)
                melee, ranged = (vals[i], vals[j]) if m.group("side") == "melee" else (vals[j], vals[i])
                out.append((ab, f"{m.group('base')} (melee / ranged)", f"{melee[2]} / {ranged[2]}",
                            melee[3] or ranged[3]))
                continue
        out.append((ab, label, value, sentence))
    return out


def _items_rows(version, rules):
    del rules                                    # the removed ones come from patch.rosters, not a hand list (2026-11-22)
    gone = items_removed(version)
    rows = []
    for name, key, slug, vals in _scaled_values(version, "apply_effectiveness", with_removed=True):
        no_ill = no_illusions(key, version)
        vals = _melee_ranged(vals)
        for k, (ab, label, value, sentence) in enumerate(vals):
            cls = ' class="ipot-gone"' if key in gone else ''
            # removed from the game: grey, hidden till "Show removed" (owner 2026-11-19: no "not in the game" words)
            head = (_name_cell(name, f"{ITEM_CDN}{slug}.png", span=len(vals), href=_mt.item_href(name, key=slug))
                    if k == 0 else '')
            hint = f' data-tooltip="{_esc(sentence)}"' if sentence else ''
            prop = f'<span class="{"iab-hint abil-ico-hint " if sentence else ""}ipot-prop"{hint}>{_esc(label)}</span>'
            sides = [_num(x) for x in str(value).split(" / ")]
            # the illusions' columns brighter as their potency grows (20 → 35 → 40%): how much of the hero's value is left
            note = no_ill.get(ab.lower()) or no_ill.get("*")
            # the first illusions' column opens the illusions' part: a stronger line before it (design review 2026-11-21)
            first = lambda i: " ipot-ill-first" if i == 0 else ""  # noqa: E731
            if note:     # illusions do not get it at all: a dash, the game's note on hover — not 20% of the value
                tip = f' data-tooltip="{_esc(note)}"'
                ill = "".join(f'<td class="ipot-v ipot-v-ill ipot-no-ill{first(i)}"><span class="abil-ico-hint"{tip}>—'
                              f'</span></td>' for i, _ in enumerate(ILLUSIONS))
            else:
                ill = "".join(f'<td class="ipot-v ipot-v-ill ipot-p{p}{first(i)}">'
                              + " / ".join(_fmt(v * p / 100) if v is not None else "—" for v in sides) + '</td>'
                              for i, (_, p) in enumerate(ILLUSIONS))
            # the ability once for its rows (Eye of Skadi's Cold Attack five times, design review 2026-11-21)
            run = 0 if k and vals[k - 1][0] == ab else next(
                (j - k for j in range(k + 1, len(vals)) if vals[j][0] != ab), len(vals) - k)
            ab_cell = (f'<td class="ipot-ab"{f" rowspan={run}" if run > 1 else ""}>{_esc(ab)}</td>' if run else "")
            rows.append(f'<tr{cls} data-name="{_esc(name.lower())}">{head}{ab_cell}'
                        f'<td class="ipot-text">{prop}</td><td class="ipot-v ipot-v-hero">{_esc(value)}</td>{ill}</tr>')
    return rows


def _sources_rows(version, rules, names, group):
    rows = []
    for slug in rules["groups"][group]:
        text = rules["abilities"].get(slug) or rules.get("items", {}).get(slug, "")
        what, _, val = text.partition(": ")
        if slug.startswith("item_"):
            title = tooltip(f"DOTA_Tooltip_Ability_{slug}", version) or slug
            cell = _name_cell(title, f"{ITEM_CDN}{slug[len('item_'):]}.png", href=_mt.item_href(title, key=slug))
        else:
            title = tooltip(f"DOTA_Tooltip_ability_{slug}", version) or slug
            owner = _hero_of(slug, version, names)       # a hero's ability leads to his page
            cell = _name_cell(title, _root(abil_img(slug)), owner, wide=False,
                              href=_mt.hero_href(owner) if owner else None)
        rows.append(f'<tr data-name="{_esc(title.lower())}">{cell}<td class="ipot-text">{_esc(what)}</td>'
                    f'<td class="ipot-v">{_chip(val or what)}</td></tr>')
    if group == "illusions":
        # a row that is no ability nor item still has its icon (owner 2026-11-22: "без иконок"): the rune's, and the
        # game's own illusion mark (its facet glyph) for every other illusion — from the rules file, beside the rows
        icons = rules.get("other_icons", {})
        for title, text in rules.get("other", {}).items():
            what, _, val = text.partition(": ")
            icon = icons.get(title, "")
            if not icon or not (_HERE / icon).exists():
                raise RuntimeError(f"item_potency.html: no icon for the Illusions row {title!r} (other_icons)")
            rows.append(f'<tr>{_name_cell(title, icon, wide=False)}<td class="ipot-text">{_esc(what if val else "")}</td>'
                        f'<td class="ipot-v">{_chip(val or what)}</td></tr>')
    return rows


def render_html() -> str:
    version = _versions()[-1]
    rules = _json.loads(RULES.read_text(encoding="utf-8"))
    names = _load_display_names()
    # under the groups the columns say only what is new: the hero's 100%, the illusion's 20%, Manta, Rune
    head_items = ["Item", "Ability", "Value", "100%"] + [f"{p}%" if n == "Illusion" else f"{n} {p}%" for n, p in ILLUSIONS]
    # the first group blank: "Item" over "Item" was said twice (owner 2026-11-21: "два раза hero" on AoE Increase)
    groups_items = [("", 3), ("Hero", 1), ("Illusions", len(ILLUSIONS))]
    body = (
        _section("How Item Potency adds up", _rules_cards(rules, REMOVED_BUTTON))
        + _section("Items", _table("ipot-items", head_items, _items_rows(version, rules), groups_items))
        + _section("Attacks with their own Item Potency", _table(
            "ipot-sources", ["Ability", "Attacks", "Item Potency"], _sources_rows(version, rules, names, "own")))
        + _section("Bonuses and penalties", _table(
            "ipot-sources", ["Source", "Attacks", "Item Potency"], _sources_rows(version, rules, names, "added")))
        + _section("Illusions", _table(
            "ipot-sources", ["Source", "Illusions", "Item Potency"], _sources_rows(version, rules, names, "illusions")))
    )
    return page_shell("item_potency", "Item Potency", body)


def page_shell(key, title, body):
    """A Materials ▸ Mechanics page around `body` (Item Potency, Dormant Curio)."""
    nav = _site.render_top_nav('materials', _latest_href(), patch_context=False, subtabs_active=key,
                               subnav_in_header=False)
    subnav = _site.render_materials_subnav(key)
    asset_version = _site.compute_asset_version()
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        f'<title>s/kle - {title}</title>\n'
        + _site.head_common() +
        f'<link rel="stylesheet" href="styles.css?v={asset_version}">\n'
        '</head>\n<body>\n'
        f'{nav}\n'
        '<div class="container creeps-page">\n'
        '<div class="sticky-frame hs-sticky-frame"></div>\n'
        '<div class="creeps-scroll">\n'
        f'{subnav}<div class="ipot-page">{body}</div>\n'
        '</div>\n</div>\n'
        f'<script defer src="src/scripts-table.js?v={asset_version}"></script>\n'
        '</body>\n</html>\n'
    )


def main() -> int:
    html = render_html()
    if html.count('<tr data-name=') < 10:            # a page with no rows is a broken build, not "0 results"
        raise RuntimeError("item_potency.html: fewer than 10 rows — the game files did not load")
    out = _HERE / "dist" / "item_potency.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"  -> dist/item_potency.html: {len(html):,} bytes ({html.count('<tr data-name=')} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
