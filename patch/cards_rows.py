"""A card side's text rows: a leading ability as its icon, rows saying the same of several abilities merged, an
Aghanim's row's stripe, the closing "?" glued to its word, and a long side folded (owner 2026-10-30)."""
import html as _html
import re

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
    m = _ROW_AGHS_RE.match(re.sub(r"<[^>]+>", "", text).lstrip())
    return _CardRow((tuple(chips), text, m.group(1).lower() if m else ""))


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
    from .mech_abilities import rune_name_chips
    return f'<div class="ability-change-row{cls}">{lead}{rune_name_chips(_bold_numbers_html(_glue_tail(text, marker)))}</div>'


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
    if not (tips or marker):
        return text
    w = re.search(r"(\S+)$", body)
    if w and "<" not in w.group(1) and ">" not in w.group(1):
        return body[:w.start()] + f'<span class="li-tail">{w.group(1)}{marker}{tips}</span>'
    return body + f'<span class="li-tail">{marker}{tips}</span>'


FOLD_CHARS = 600                 # a card side longer than this folds (owner 2026-10-30: "раскатай на весь сайт"; 28
                                  # sides of 569 in 7.37–7.41, 7.37 Drunken Brawler's 733 the first)
_INTRO_SHARE = 0.45               # a first row this short a part of the whole stays open as the intro


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


def fold_long_rows(rows):
    """A long card side folds: its intro row stays (the first one when it is short), the rest shows its first lines
    fading out under soft glass, a click opens it (owner 2026-10-30: "для таких длинных описаний может сделаем
    свёрнутый вид?", the glass "чтобы было видно, что оно разворачиваться может, а также возможность свернуть
    обратно"). A side with no short intro folds whole and shows more lines. src/scripts.js opens and folds it and
    redraws the card's connectors."""
    texts = [r for r in rows if isinstance(r, str)]
    total = sum(_plain_len(r) for r in texts)
    if total <= FOLD_CHARS or any("acr-fold" in r for r in texts):
        return rows
    k = [i for i, r in enumerate(rows) if isinstance(r, str)]
    # no short intro to keep open: the side stays as it is (owner 2026-10-30, 7.38 Roshan's Throw: "как будто можно и
    # не сворачивать")
    if not (len(k) > 1 and _plain_len(rows[k[0]]) <= _INTRO_SHARE * total):
        return rows
    first, last = k[1], k[-1]
    # over the faded text's bottom a strip of soft glass says it opens, and folds it back (owner 2026-10-30: "чтобы
    # было видно, что оно разворачиваться может, а также возможность свернуть обратно"; a chevron and golden pollen
    # were tried and dropped: "эффект стекла снизу, но не резкий, а плавный … чтобы не нагружало страницу")
    toggle = ('<button type="button" class="acr-fold-toggle" aria-expanded="false" aria-label="Show the whole text">'
              '</button>')
    return (rows[:first] + [f'<div class="acr-fold"><div class="acr-fold-body">{"".join(rows[first:last + 1])}</div>'
                            f'{toggle}</div>'] + rows[last + 1:])
