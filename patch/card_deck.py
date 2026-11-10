"""An old -> new card as a deck (owner 2026-11-09, tried on 7.38 first): the new card across the block, the old one lying
under it, shown only by two pixel steps at its bottom right edge; a click puts the old card on top in the same place,
another click brings the new one back (src/js/card-deck.js, the look in patch-ability-change.css). No arrow, no old card
beside it. Items' old -> new panes stay as they are ("предметы не учитываем").

Each card carries its patch on a tab over its top right corner — this page's on the new one, the patch before on the old
(owner 2026-11-09: "когда карточка меняется, непонятно, где новая, а где старая").

A card with a value table: its text on the left, the values a card of their own beside it, as a one-sided card's
(value_tables.tables_beside_single_cards; owner 2026-11-09: "много пустого места … описание отдельно, карточка значений
рядом"). The two move together, a table inside a folded text too.

Every patch page (owner 2026-11-09, after the try on 7.38: "на все патчи"); a set of page stems would limit it.
"""
import html as _html
import re

from .deck_extra import enrich
from .html_util import div_end
from .deck_values import mark_new_values, rows_before, rows_of_named
from .meta import _prev_patch_version

DECK_PAGES = None

_CARD_RE = re.compile(r'<div class="ability-change unified-panes(?P<cls>[^"]*)"')
_PANE_RE = re.compile(r'<div class="ability-change-pane ability-change-(?P<side>old|new)(?P<cls>[^"]*)"(?P<rest>[^>]*)>')
_BLOCK_START_RE = re.compile(r'<div class="ability-(?:change-)?block[ "]')
_ICON_SLUG_RE = re.compile(r'<img[^>]*class="ability-icon-img"[^>]*data-slug="([a-z0-9_]+)"'
                           r'|<div class="ability-icon-wrap[^"]*"><img[^>]*abilities/([a-z0-9_]+)\.(?:webp|png)')


_OLD_ICON_RE = re.compile(r'<img(?=[^>]*class="ability-icon-old-underlay")[^>]*>')


def _block_slug(html, card_start):
    """The ability of the block a card stands in, by its icon: only that block's (a search back over the page took
    another hero's — 7.40 Lone Druid's Spirit Bear read Lion's values, its icon wrap holds an old icon first)."""
    starts = [m.start() for m in _BLOCK_START_RE.finditer(html, max(0, card_start - 40000), card_start)]
    if not starts:
        return None
    m = _ICON_SLUG_RE.search(html, starts[-1], card_start)
    return (m.group(1) or m.group(2)) if m else None


def _renamed_block(html, card_start):
    """The card's block is titled "Old → New": another ability replaced the old one."""
    starts = [m.start() for m in _BLOCK_START_RE.finditer(html, max(0, card_start - 40000), card_start)]
    return bool(starts) and 'class="ability-title-old"' in html[starts[-1]:card_start]


def _old_slug(html, card_start, new):
    """The old side's ability: the old icon under the new one when the ability changed (7.40 Gift Bearer -> Spirit Bear),
    None when that icon names no ability (the innate's blank), else the same one."""
    starts = [m.start() for m in _BLOCK_START_RE.finditer(html, max(0, card_start - 40000), card_start)]
    m = _OLD_ICON_RE.search(html, starts[-1], card_start) if starts else None
    if not m:
        return new
    own = re.search(r"abilities/([a-z0-9_]+)\.(?:webp|png)", m.group(0))
    return own.group(1) if own else None
_VT = '<div class="value-table"'


def _div_end(s, start):
    """The index just past the </div> closing the <div opening at `start`; a card that never closes is an error."""
    return div_end(s, start, strict=True)


def _tab(version, side, other):
    """The card's patch, a button that brings the other card up (by keyboard too — code review 2026-11-09)."""
    return (f'<button type="button" class="deck-tab deck-tab-{side}" aria-label="{_html.escape(version)}: show '
            f'{_html.escape(other)}">{_html.escape(version)}</button>')


_ROW_OPEN = '<div class="ability-change-row'
_SUB_RE = re.compile(r'<span class="ac-sub">.*?</b></span>', re.S)


def _split_values(inner):
    """(text, values) when the pane's value tables can all leave it, else (inner, None): one table outside any fold, or
    several each under its own ability's name ("Burning Army: …", "Bone and Arrow: …"), which heads it in the values card
    (owner 2026-11-09, 7.40 Clinkz: "почему тут не в 2 карточки?")."""
    starts = [m.start() for m in re.finditer(re.escape(_VT), inner)]
    # a table inside a folded text leaves it too (Sonnet 2026-11-09, 7.41 Marci Special Delivery: the new side's values
    # stayed under its fade while the old side's stood on the right)
    if not starts:
        return inner, None
    parts = []
    for i in starts:
        row = inner.rfind(_ROW_OPEN, 0, i)
        sub = _SUB_RE.search(inner, row, i) if row >= 0 else None
        if len(starts) > 1 and not sub:
            return inner, None              # tables of several things, not one named each: they stay by their text
        parts.append((i, _div_end(inner, i), sub.group(0) if sub and len(starts) > 1 else ""))
    text, pos, values = [], 0, []
    for i, j, sub in parts:
        text.append(inner[pos:i])
        values.append((f'<div class="deck-vals-head">{sub}</div>' if sub else "") + inner[i:j])
        pos = j
    text.append(inner[pos:])
    text = "".join(text).replace('<div class="ability-change-row"></div>', "")   # a row that held only the table
    return text, "".join(values)


def _pane(m, inner, versions):
    side = m.group("side")
    hid = " deck-hid" if side == "old" else ""
    tab = _tab(versions[side], side, versions["new" if side == "old" else "old"])
    text, table = _split_values(inner)
    if table is None:
        return (f'<div class="ability-change-pane ability-change-{side}{m.group("cls")}{hid}"{m.group("rest")}>'
                + tab + inner + "</div>")
    return (f'<div class="ability-change-pane ability-change-{side}{m.group("cls")}{hid} has-vals"{m.group("rest")}>'
            + f'<div class="deck-card">{tab}{text}</div>'
            + f'<div class="deck-vals vt-side">{table}</div></div>')


def _deck(card, versions, rows=(), slug=None, other=False):
    """One card's markup (up to the next card) as a deck. None if it is not two-sided. `rows`: the change rows above it,
    which name the values that changed (deck_values); `slug`: the ability of its block, whose values name the text's
    numbers (deck_extra); `other`: the old side is another ability (its block's title "Old → New")."""
    panes = list(_PANE_RE.finditer(card))
    if {p.group("side") for p in panes} != {"old", "new"}:
        return None
    head = _CARD_RE.match(card)
    spans, pos = [], head.end()
    for m in panes:
        if m.start() < pos:                 # a pane inside a pane: none such, kept as it is
            continue
        end = _div_end(card, m.start())
        spans.append((m, pos, end))
        pos = end
    # the header's values and the text's numbers into the values card, each side by its own patch's files (deck_extra)
    slugs = slug if isinstance(slug, dict) else {"new": slug, "old": slug}
    inner = {m.group("side"): enrich(card[m.end():end - len("</div>")], slugs[m.group("side")],
                                     versions[m.group("side")])
             for m, _, end in spans}
    out = [f'<div class="ability-change unified-panes{head.group("cls")} is-deck"']
    for m, start, end in spans:
        side_inner = inner[m.group("side")]
        if m.group("side") == "new":
            # another ability on the old side (7.37 Tidebringer -> Admiral's Rum): nothing to compare its values with
            # (owner 2026-11-10: "неправильно сравнивать перезарядки … это разные способности"); a change row that
            # names a value still lights it
            same = slugs["old"] == slugs["new"] and not other
            side_inner = _tidy_lit(mark_new_values(side_inner, inner.get("old", "") if same else "", rows))
        out.append(card[start:m.start()])
        out.append(_pane(m, side_inner, versions))
    out.append(card[spans[-1][2]:])
    return "".join(out)


_VT_SIDE = '<div class="vt-side">'


def _tidy_lit(inner):
    """The values card once more after its numbers are lit: lighting writes a header's number anew ("Cooldown 60"
    lost its "s", Sonnet proofread 2026-11-10)."""
    from .deck_text import without_tables
    from .html_util import strip_tags
    from .value_tidy import tidy
    return tidy(inner, strip_tags(without_tables(inner)))


def _facet_of(html, card_start):
    """The facet a card stands under ("Glacial Guard" -> "glacial_guard"), None when its block is no facet's."""
    starts = [m.start() for m in _BLOCK_START_RE.finditer(html, max(0, card_start - 40000), card_start)]
    if not starts or "facet-block" not in html[starts[-1]:starts[-1] + 80]:
        return None
    m = re.search(r'<h4 class="ability-title">([^<]+)</h4>', html[starts[-1]:card_start])
    return re.sub(r"[^a-z0-9]+", "_", _html.unescape(m.group(1)).lower()).strip("_") if m else None


def _solo(card, version, slug, rows, facet=None):
    """A one-sided card ("New ability.", "New facet", "Added Aghanim's Scepter.") as a deck's new side: its text where
    it stands, under its block on the left, its values a card of their own on the right — the header's values and the
    text's numbers among them, the values a change row names lit (owner 2026-11-10, 7.41 Ready to Roll: "вот такие
    карточки делаем, как и всё остальное … не по правую часть с линией до карточки, а как и раньше слева")."""
    from .value_tables import _unfold
    end = _div_end(card, 0)
    own, tail = card[:end], card[end:]
    pane = _PANE_RE.search(own)
    if not pane:
        return None
    p_end = _div_end(own, pane.start())
    inner = own[pane.end():p_end - len("</div>")]
    rest = own[p_end:-len("</div>")]
    # a table value_tables already set beside the text goes back in: the values card is made of all of them
    side = rest.find(_VT_SIDE)
    if side >= 0:
        table = rest[side + len(_VT_SIDE):_div_end(rest, side) - len("</div>")]
        rest = rest[:side] + rest[_div_end(rest, side):]
        body = inner.rfind("</div>")
        inner = inner[:body] + f'<div class="ability-change-row">{table}</div>' + inner[body:]
    inner = _tidy_lit(mark_new_values(enrich(inner, slug, version, facet), "", rows))
    text, values = _split_values(inner)
    if values is None:
        return None
    head = _CARD_RE.match(own)
    cls = head.group("cls") if "has-vt-side" in head.group("cls") else head.group("cls") + " has-vt-side"
    # its text was folded for the weight of the table it held (cards_rows._side_weight): short now, open
    return (_unfold(f'<div class="ability-change unified-panes{cls}"' + own[head.end():pane.end()] + text + "</div>")
            + rest + f'{_VT_SIDE}{values}</div></div>' + tail)


_AGHS_LI_RE = re.compile(r'<li data-tag="[^"]*" class="(aghanim-(scepter|shard)[^"]*)">(.*?)</li>', re.S)
_LEAD_RE = re.compile(r"^(?:Now upgraded with|Can be upgraded with|Added) Aghanim's (?:Scepter|Shard)\.?\s*", re.I)
_WORDS_RE = re.compile(r"[a-z][a-z']{3,}")
_TIP_RE = re.compile(r'<span class="info-tip"[^>]*>\?<span class="info-pop">.*?</span></span>', re.S)
# a row that tells what an upgrade does, not how a number of it changed
_DESCRIBES_RE = re.compile(r"^(?:Now upgraded with|Can be upgraded with|Upgradable by) Aghanim's (?:Scepter|Shard)\b", re.I)
RETOLD = 0.6                      # a sentence whose words stand in the card this much is the card's own


def _sentences(text):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if x.strip()]


def _told(sentence, card_words):
    words = set(_WORDS_RE.findall(sentence.lower()))
    return bool(words) and len(words & card_words) / len(words) >= RETOLD


def _bold_numbers(text):
    return re.sub(r"(?<![\w.])([+\-]?\d+(?:[./]\d+)*(?:%|s\b)?)", r'<b class="iab-num">\1</b>', text)


def _block_card(html, row_at):
    """(the new pane's start, the block's end) of the card in the block a row stands in, above the row or under it;
    None when the block has none."""
    start = html.rfind('<div class="ability-block', 0, row_at)
    nxt = html.find('<div class="ability-block', row_at)
    nxt = len(html) if nxt < 0 else nxt
    card = html.find('<div class="ability-change unified-panes', max(start, 0), nxt)
    new_at = html.find("ability-change-pane ability-change-new", card, nxt) if card >= 0 else -1
    return (new_at, nxt) if new_at >= 0 else None


def retold_rows(html):
    """An Aghanim's row of a block with a card that says it again (7.37 Ghostship: "Now upgraded with Aghanim's Scepter.
    Creates a fleet of 2 ships …" over the Scepter card saying the same, its "projectile radius: 100" and "speed: 1400"
    only in the row): the row is hidden — its tag kept for the filters — and what only it says goes into the card's part,
    so the values card has all of it (owner 2026-11-10: "строка дублирует то, что в карточке изменений, но только не до
    конца"). A row telling an upgrade the card has no part for ("Can be upgraded with Aghanim's Shard. Increases damage
    by 10, radius by 175 …" under 7.37 Immolation) becomes the card's part (owner 2026-11-10: "не нужно внутри левой
    карточки вставить?" -> yes). The card may stand above the row or under it."""
    from .html_util import plain
    edits = []                                   # (at, text to insert); applied from the end
    for m in _AGHS_LI_RE.finditer(html):
        if "iab-covered" in m.group(1):
            continue
        got = _block_card(html, m.start())
        if not got:
            continue
        new_at, nxt = got
        kind = m.group(2)
        part = html.find(f'<div class="ability-change-row aghanim-{kind}', new_at, nxt)
        # its [?] goes with it, whole; the rest as text (the "?" of the tip stood as a stray character)
        tip = _TIP_RE.search(m.group(3))
        raw = plain(re.sub(r'<span class="badge[^"]*"[^>]*>.*?</span>', "", _TIP_RE.sub("", m.group(3))))
        text = _LEAD_RE.sub("", raw)
        if not text:
            continue
        tip = tip.group(0) if tip else ""
        if part < 0:
            body = html.find('<div class="ability-change-body">', new_at, nxt)
            if body < 0 or not _DESCRIBES_RE.match(raw):
                continue
            edits.append((m.start(1), "iab-covered covered-card "))
            edits.append((_div_end(html, body) - len("</div>"),
                          f'<div class="ability-change-row aghanim-{kind}"><span class="aghanim-marker {kind}"></span>'
                          + _bold_numbers(_html.escape(text, quote=False)) + tip + "</div>"))
            continue
        card_words = set(_WORDS_RE.findall(plain(html[new_at:nxt]).lower()))
        said = _sentences(text)
        # a retelling: half the row's words or more stand in the card (7.37 Ghostship: two sentences of five are the
        # card's, the three short ones the row's own)
        words = set(_WORDS_RE.findall(text.lower()))
        if not said or not words or len(words & card_words) * 2 < len(words):
            continue
        extra = " ".join(x for x in said if not _told(x, card_words))
        edits.append((m.start(1), "iab-covered covered-card "))
        if extra:
            edits.append((_div_end(html, part) - len("</div>"),
                          " " + _bold_numbers(_html.escape(extra, quote=False)) + tip))
    for at, text in sorted(edits, key=lambda e: e[0], reverse=True):
        html = html[:at] + text + html[at:]
    return html


def deck_cards(html, stem):
    """Mark every two-sided ability card of the page as a deck, its old pane hidden under the new one; a one-sided
    card gets the deck's values card beside it (_solo)."""
    if DECK_PAGES is not None and stem not in DECK_PAGES:
        return html
    versions = {"new": stem, "old": _prev_patch_version(stem) or "before"}
    html = retold_rows(html)
    out, pos = [], 0
    for m in _CARD_RE.finditer(html):
        if m.start() < pos:
            continue
        nxt = _CARD_RE.search(html, m.start() + 1)
        end = nxt.start() if nxt else len(html)
        card = html[m.start():end]
        if "is-single-new" in m.group("cls"):
            solo = _solo(card, stem, _block_slug(html, m.start()),
                         rows_before(html, m.start()) + rows_of_named(html, m.start(), card),
                         _facet_of(html, m.start()))
            if solo is not None:
                out.append(html[pos:m.start()])
                out.append(solo)
                pos = end
            continue
        new = _block_slug(html, m.start())
        deck = _deck(card, versions, rows_before(html, m.start()) + rows_of_named(html, m.start(), card),
                     {"new": new, "old": _old_slug(html, m.start(), new)}, _renamed_block(html, m.start()))
        if deck is None:
            continue
        out.append(html[pos:m.start()])
        out.append(deck)
        pos = end
    out.append(html[pos:])
    return "".join(out)
