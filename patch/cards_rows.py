"""A card side's text rows: a leading ability as its icon, rows saying the same of several abilities merged, an
Aghanim's row's stripe, the closing "?" glued to its word, and a long side folded (owner 2026-10-30)."""
import html as _html
import re
from .html_util import strip_tags

from .state import _State


def _bold_numbers_html(text):
    from .cards_item_abilities import _bold_numbers_html as bold
    return bold(text)


_LEAD_ROW_RE = re.compile(r"^([A-Z][\w'.\- ]{2,40}?):\s")


def _lead_ability_chip(text):
    """(chips, rest) of a card row's text. A row that opens with one of the hero's abilities ("Quas: When Invoker
    reaches level 6 …", 7.38 Quas Focus): the ability's icon in place of its name, the text right after it — "[Wex] …";
    the icon grows on hover with the name above it, as in every facet row (owner 2026-10-30: a colon, then a dash, then
    "убрать тире всё-таки"). A name that is no ability of the hero's with an icon stays a word: no chips, the text as it was."""
    from .elements import _hero_ability_slug
    from .images import ABIL_CDN, _LOCAL_ABIL_ICONS
    from .mech_abilities import ability_chip
    m = _LEAD_ROW_RE.match(text) if _State.current_hero else None
    if not m or m.group(1) in ("Active", "Passive", "Toggle", "Aura", "Ultimate"):
        return (), text
    slug = _hero_ability_slug(_State.current_hero, m.group(1))
    if slug not in _LOCAL_ABIL_ICONS and _State.current_patch_version:   # a name its slug doesn't spell (Unicycle)
        from .ability_kv import hero_abilities
        known = hero_abilities(_State.current_hero, _State.current_patch_version).get(m.group(1).lower())
        slug = known[0] if known else slug
    if slug not in _LOCAL_ABIL_ICONS:
        return (), text
    return (ability_chip(m.group(1), f"{ABIL_CDN}{slug}.png"),), text[m.end():]


class _CardRow(tuple):
    """(chips, text, aghs) of a card's text row before it is html: rows saying one thing of several abilities merge."""


# A row about an Aghanim's upgrade — "Can be upgraded with Aghanim's Shard. …", "Aghanim's Scepter grants 1 additional
# current level …", "Now Aghanim's Scepter grants Cataclysm …" (7.38 Invoker's facets) — gets the upgrade's stripe and
# glyph, as every other Aghanim's row in a card (owner 2026-10-30: "не подсвечено аганимной подложкой")
_ROW_AGHS_RE = re.compile(r"^(?:[A-Z][\w'.\- ]{2,40}?:\s+)?(?:Can be upgraded with |With |Now )?Aghanim's (Scepter|Shard)\b")


def _card_row(chips, text):
    m = _ROW_AGHS_RE.match(strip_tags(text).lstrip())
    return _CardRow((tuple(chips), text, m.group(1).lower() if m else ""))


# a card row's own % badges after its "from A to B" go onto B: its colour, a dotted line and the % on hover, as every
# changed number in a card (owner 2026-11-06, 7.38 Fleshfeast "+67%, +133% … разве стоит указывать там рядом, а не в
# самих значениях 25/35/... с пунктирной линией, как везде?", Undulation)
_ROW_BADGES_RE = re.compile(r'\s*<span class="badge-group[^"]*" data-overall="(\w+)">.*?</span></span>', re.S)
_ROW_FROM_TO_RE = re.compile(r"\bfrom ((?:<b[^>]*>)?[+\-]?\d[\d./%s]*(?:</b>)?) to ((?:<b[^>]*>)?[+\-]?\d[\d./%s]*?(?:</b>)?)"
                             r"(?=[\s.,;]|$)")


def _badges_into_number(text):
    badges = _ROW_BADGES_RE.search(text)
    if not badges:
        return text
    body = text[:badges.start()] + text[badges.end():]
    pairs = list(_ROW_FROM_TO_RE.finditer(body))
    if len(pairs) != 1:                         # none, or two changes in one row: whose badges — they stay
        return text
    from .number_tips import _number_tip
    m, kind = pairs[0], badges.group(1)
    new = m.group(2)
    tipped = _number_tip(strip_tags(m.group(1)), new, kind)
    if not tipped:
        return text
    return (body[:m.start(2)] + f'<span class="iab-hl iab-hl-{kind} iab-hl-num">{tipped}</span>' + body[m.end(2):])


# ... and so does a label "Aghanim's Shard: …" (7.39 Invoker's Ice Wall cards, found 2026-11-06)
_AGHS_SAID_RE = re.compile(r"^\s*(?:Can be upgraded with Aghanim's (?:Scepter|Shard)\.|Aghanim's (?:Scepter|Shard):)\s*")
_CHIP_NAME_RE = re.compile(r'data-tooltip="([^"]+)"')


_BASIC = 3                   # the hero's first abilities in its files: Quas, Wex, Exort; Q, W, E


def in_heros_order(rows):
    """Rows of several of the hero's abilities: first the hero's basic ability with its Aghanim's rows (owner
    2026-11-06, 7.38 Invoker's facets: "Active: Wex/Exort/Quas ставить в начале списка"), then the abilities the side
    improves, then its Aghanim's Scepter rows, then its Shard rows, each part in the order of the hero's abilities — so
    three facets side by side say the same thing on one line ("как ты аспекта эти 3 рядом расположил"). The rows before
    the first icon stay first; a row without an icon goes with the one above it."""
    if not (_State.current_hero and _State.current_patch_version) or not all(isinstance(r, _CardRow) for r in rows):
        return rows
    from .ability_kv import hero_abilities
    order = list(hero_abilities(_State.current_hero, _State.current_patch_version))
    keys, key = [], (-1, -1)
    for r in rows:
        m = _CHIP_NAME_RE.search(r[0][0]) if r[0] else None
        if m:
            name = _html.unescape(m.group(1)).lower()
            at = order.index(name) if name in order else len(order)
            part = 0 if at < _BASIC else {"": 1, "scepter": 2, "shard": 3}[r[2]]
            key = (part, at)
        keys.append(key)
    if len({k for k in keys if k[0] >= 0}) < 2:
        return rows
    return [r for _k, _i, r in sorted(zip(keys, range(len(rows)), rows), key=lambda x: x[:2])]


def _merge_same_rows(rows):
    """Neighbouring rows of different abilities that say the same — "[Funhouse Mirror] – Made exclusive to Carny Classics
    Facet" three times (7.38 Dark Carnival Barker) — become one row with the icons side by side (owner 2026-10-30:
    "объединять, как мы делали со способностями, и просто поставить рядом 3 иконки")."""
    out = []
    for r in rows:
        prev = out[-1] if out else None
        if (isinstance(r, _CardRow) and isinstance(prev, _CardRow) and r[0] and prev[0]
                and (r[1], r[2]) == (prev[1], prev[2])):
            out[-1] = _CardRow((prev[0] + r[0], r[1], r[2]))
        else:
            out.append(r)
    return out


def _row_html(row):
    """The icons straight before the text, no dash (owner 2026-10-30: "убрать тире всё-таки после иконок"); an
    Aghanim's row's glyph at the END of the text, as on every list row ("иконки аганима/шарда поставить по правилам в
    конце строки"), and the text lined up with the plain rows' (.acr-aghs)."""
    chips, text, aghs = row
    lead = f'<span class="acr-lead-chips">{"".join(chips)}</span>' if chips else ""
    cls = f" aghanim-{aghs} acr-aghs" if aghs else ""
    marker = f'<span class="aghanim-marker {aghs}"></span>' if aghs else ""
    if aghs:
        # "Can be upgraded with Aghanim's Scepter." says what the stripe and the glyph say (owner 2026-11-06: "да")
        cut = _AGHS_SAID_RE.sub("", text, count=1)
        text = cut[:1].upper() + cut[1:] if cut != text else text
    from .mech_abilities import ability_list_chips, rune_name_chips
    text = ability_list_chips(text, _State.current_hero, _State.current_patch_version)
    text = _badges_into_number(text)
    # the runes' icons before the last word glues to its "?": "any Power Rune?" kept its name (7.38 Runic Infusion)
    return f'<div class="ability-change-row{cls}">{lead}{_bold_numbers_html(_glue_tail(rune_name_chips(text), marker))}</div>'


# the row's closing cluster — its Aghanim's glyph, then its "?" (an inline_note) — and the word before it never part on
# a wrap: a bare "?" on a line of its own is not allowed (owner 2026-10-30, 7.38 Mind of Tornarus' E.M.P. row); as
# iab_attach_tail does for an item's ability and page rows for their glyph
_TAIL_TIPS_RE = re.compile(r"\s*((?:<!--INLINETIP-->)?<!--TIP-->.*<!--/TIP-->(?:<!--/INLINETIP-->)?)\s*$", re.S)


def _glue_tail(text, marker=""):
    m = _TAIL_TIPS_RE.search(text)
    tips = m.group(1) if m else ""
    if tips and re.sub(r"<!--TIP-->.*?<!--/TIP-->|<!--/?INLINETIP-->", "", tips, flags=re.S).strip():
        tips = ""                               # words between two tips: only the last tip's word could glue
    body = text[:m.start()] if tips else text.rstrip()
    if not (tips or marker or _TAIL_CHIPS_RE.search(body)):
        return text
    # icons closing the text ("upon activating any [rune]") go with the word before them: a line never starts with a
    # bare icon or a (?) (owner 2026-11-06, 7.38 Runic Infusion)
    chips = _TAIL_CHIPS_RE.search(body)
    lead, chips = (body[:chips.start()], chips.group(0)) if chips else (body, "")
    w = re.search(r"(\S+)$", lead)
    if w and "<" not in w.group(1) and ">" not in w.group(1):
        return lead[:w.start()] + f'<span class="li-tail">{w.group(1)}{chips}{marker}{tips}</span>'
    return body + f'<span class="li-tail">{marker}{tips}</span>'


_CHIP_HTML = r'<span class="ability-chip[^"]*"[^>]*>(?:<img[^>]*>)+</span>'
_TAIL_CHIPS_RE = re.compile(rf"(?:\s*(?:,|or|and)?\s*{_CHIP_HTML})+$")


FOLD_CHARS = 600                 # a card side longer than this folds (owner 2026-10-30: "раскатай на весь сайт"; 28
                                  # sides of 569 in 7.37–7.41, 7.37 Drunken Brawler's 733 the first)
_INTRO_SHARE = 0.45               # a first row this short a part of the whole stays open as the intro
FOLD_WHOLE_CHARS = 800           # a side with no short intro folds whole past this (Roshan's Throw 700 stays open)
# the sides are measured by height, not by characters only (owner 2026-11-07, 7.38 Arcane Curse: "надо ещё судить не
# только по кол-ву символов, а по высоте … карточка достаточно высокая"): a value table's row is ~28px against a text
# line's ~21px, and a line holds ~70 characters, so a table row weighs as 95 characters, whatever its own words
TABLE_ROW_CHARS = 95


def _without_popups(html):
    """The text a card shows: a "?" popup's words (.info-pop, hidden till hovered) left out — 7.39 Changing of the
    Guard's 420 of them folded a side of 414 visible characters."""
    out, i = [], 0
    while (k := html.find('<span class="info-pop"', i)) >= 0:
        out.append(html[i:k])
        depth, j = 0, k
        for m in re.finditer(r"<span\b|</span>", html[k:]):
            depth += 1 if m.group(0) == "<span" else -1
            if depth == 0:
                j = k + m.end()
                break
        else:
            j = len(html)
        i = j
    return "".join(out) + html[i:]


def _plain_len(html):
    return len(re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", _without_popups(html)))).strip())


_ROW_INNER_RE = re.compile(r'^<div class="ability-change-row(?: [^"]*)?">(.*)</div>$', re.S)


def _side_weight(row):
    """A card row's height in characters: its words, and the values the page turns into a table (patch/value_tables.py,
    applied later to the saved page) by their rows, TABLE_ROW_CHARS each."""
    from .value_tables import MIN_VALUES, _split
    m = _ROW_INNER_RE.match(row.strip())
    split = _split(m.group(1), MIN_VALUES) if m and "<div" not in m.group(1) else None
    if not split:
        return _plain_len(row)
    before, pairs, after = split
    return _plain_len(before) + _plain_len(after) + len(pairs) * TABLE_ROW_CHARS


def fold_long_rows(rows):
    """A long card side folds: its intro row stays (the first one when it is short), the rest shows its first lines
    fading out under soft glass, a click opens it (owner 2026-10-30: "для таких длинных описаний может сделаем
    свёрнутый вид?", the glass "чтобы было видно, что оно разворачиваться может, а также возможность свернуть
    обратно"). A side with no short intro folds whole and shows more lines. src/scripts.js opens and folds it and
    redraws the card's connectors."""
    texts = [r for r in rows if isinstance(r, str)]
    total = sum(_side_weight(r) for r in texts)
    if total <= FOLD_CHARS or any("acr-fold" in r for r in texts):
        return rows
    k = [i for i, r in enumerate(rows) if isinstance(r, str)]
    # no short intro to keep open: the side stays as it is (owner 2026-10-30, 7.38 Roshan's Throw, 700 characters: "как
    # будто можно и не сворачивать") — unless it is much longer: then it folds whole (owner 2026-11-06, 7.38 Nothl
    # Projection, 947: "генератор не определил, что такую карточку надо свернуть")
    intro = len(k) > 1 and _side_weight(rows[k[0]]) <= _INTRO_SHARE * total
    if not intro and not (len(k) > 1 and total > FOLD_WHOLE_CHARS):
        return rows
    first, last = (k[1] if intro else k[0]), k[-1]
    # over the faded text's bottom a strip of soft glass says it opens, and folds it back (owner 2026-10-30: "чтобы
    # было видно, что оно разворачиваться может, а также возможность свернуть обратно"; a chevron and golden pollen
    # were tried and dropped: "эффект стекла снизу, но не резкий, а плавный … чтобы не нагружало страницу")
    toggle = ('<button type="button" class="acr-fold-toggle" aria-expanded="false" aria-label="Show the whole text">'
              '</button>')
    whole = "" if intro else " acr-fold-whole"     # folded from the start: more of its first lines show
    return (rows[:first] + [f'<div class="acr-fold{whole}"><div class="acr-fold-body">{"".join(rows[first:last + 1])}'
                            f'</div>{toggle}</div>'] + rows[last + 1:])
