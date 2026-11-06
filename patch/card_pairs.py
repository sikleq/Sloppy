"""Two new cards in a row stand side by side, each on its own half (owner 2026-11-06, variant D: 7.38 Chaos Knight's two
new facets left half the line empty under each). A lone one-sided card stays as wide as one side of a card, at the left
edge (variant A). Applied to the saved page (patch/page.py).

A block pairs when its only card is one-sided ("New ability.", "New facet", "Added Aghanim's …") and it has no rows of its
own showing: rows would be squeezed into half the line with their tags and badges. Trial on 7.38 first (owner: "нужно
протестить на одном патче"): PAGES lists the pages it runs on; None = every page."""
import re

from .value_tables import _div_end

PAGES = None

_BLOCK_OPEN_RE = re.compile(r'<div class="ability-block[ "]')
_CARD_OPEN_RE = re.compile(r'<div class="ability-change[ "]')
_ROWS_UL_RE = re.compile(r'<ul class="changes">(.*?)</ul>', re.S)
_LI_OPEN_RE = re.compile(r'<li\b[^>]*>')


def _pairable(block):
    """One card, one-sided, no row of the block's own that shows (a row the card covers is hidden)."""
    cards = [c for c in _CARD_OPEN_RE.finditer(block)]
    if len(cards) != 1 or "is-single-new" not in block[cards[0].start():block.index(">", cards[0].start())]:
        return False
    for ul in _ROWS_UL_RE.finditer(block):
        if any("covered-card" not in li.group(0) for li in _LI_OPEN_RE.finditer(ul.group(1))):
            return False
    return True


def _single_card(block):
    """(start, end) of the block's only card when it is one-sided, else None. Rows of its own may stand on the left."""
    cards = list(_CARD_OPEN_RE.finditer(block))
    if len(cards) != 1 or "is-single-new" not in block[cards[0].start():block.index(">", cards[0].start())]:
        return None
    return cards[0].start(), _div_end(block, cards[0].start())


def single_cards_right(html, page=None):
    """A lone one-sided card stands to the right of its block, at the block's top, with a line from its caption ("Added
    Aghanim's Scepter.", "New facet") to it (owner 2026-11-06, 7.38 Bloodrage / Marshmage Convert). The block keeps the
    left half: <div class="single-right"><div class="ability-block …">…</div><span class="sr-line"></span><card></div>;
    the line is drawn by drawSingleRightLines (src/js/patch-page.js). Blocks already in a pair are left alone."""
    if PAGES is not None and page not in PAGES:
        return html
    out, pos = [], 0
    for b in _BLOCK_OPEN_RE.finditer(html):
        if b.start() < pos:
            continue
        end = _div_end(html, b.start())
        block = html[b.start():end]
        card = _single_card(block)
        if not card or _in_pair(html, b.start()):
            continue
        left = block[:card[0]] + block[card[1]:]
        left, under = _rows_under(left)
        out.append(html[pos:b.start()] + '<div class="single-right">' + left
                   + '<span class="sr-line" aria-hidden="true"></span>' + block[card[0]:card[1]] + "</div>" + under)
        pos = end
    out.append(html[pos:])
    return "".join(out)


_SUMMARY_UL_RE = re.compile(r'(<ul class="changes ability-change-summary-ul">)(.*?)(</ul>)', re.S)


def _rows_under(block):
    """(block, rows under the card): the card's caption ("New facet") stays by the card, the block's other rows go under
    the card, in an icon-less block of their own, so a row's % stands at the line's end, not in the middle (owner
    2026-11-06, 7.38 Voidbringer: "Number of times +2 All Attributes … надо ниже карточки поставить")."""
    m = _SUMMARY_UL_RE.search(block)
    if not m:
        return block, ""
    from .page import _split_top_li
    _prefix, items, _suffix = _split_top_li(m.group(2))
    moving = [li for li in items[1:] if "iab-covered" not in li.split(">", 1)[0]]   # hidden ones stay
    if not moving:
        return block, ""
    rest = "".join(moving)
    kept = m.group(2)
    for li in moving:
        kept = kept.replace(li, "", 1)
    return (block[:m.start(2)] + kept + block[m.end(2):],
            f'<div class="ability-block sr-under"><ul class="changes">{rest}</ul></div>')


_ENTITY_RE = re.compile(r'<div class="entity-block[ "]')
_FACET_BLOCK_RE = re.compile(r'<div class="ability-block facet-block[ "]')
_REMOVED_ROWS_RE = re.compile(r'<ul class="changes">\s*<li data-tag="del[^"]*"><span class="badge del"[^>]*>DEL</span>'
                              r'<span class="row-text">(?:<span class="li-tail">)?Removed(?:</span>)?</span></li>\s*</ul>')


def pair_replaced_facets(html, page=None):
    """A hero who lost one facet and got one new: the new one with its card on the left, the lost one ("Removed") on the
    right, one line, where the lost one stood (owner 2026-11-06, 7.38 Meepo Pack Rat / Codependent, Phantom Assassin
    Veiled One / Sweet Release: "просто поставить слева «аспект удалён», а справа уже добавить новый")."""
    if PAGES is not None and page not in PAGES:
        return html
    out, pos = [], 0
    for e in _ENTITY_RE.finditer(html):
        if e.start() < pos:
            continue
        end = _div_end(html, e.start())
        ent = html[e.start():end]
        facets = [(f.start(), _div_end(ent, f.start())) for f in _FACET_BLOCK_RE.finditer(ent)]
        gone = [(s, t) for s, t in facets if _REMOVED_ROWS_RE.search(ent[s:t]) and "ability-change" not in ent[s:t]]
        new = [(s, t) for s, t in facets if _pairable(ent[s:t]) and "New facet" in ent[s:t]]
        if len(gone) != 1 or len(new) != 1 or _in_pair(ent, new[0][0]) or new[0][0] < gone[0][1]:
            continue
        (gs, gt), (ns, nt) = gone[0], new[0]
        # the new one first: its card says what the hero has now (owner 2026-11-06: "меняй местами новый и удалённый")
        pair = '<div class="card-pair facet-swap">' + ent[ns:nt] + ent[gs:gt] + "</div>"
        ent = ent[:gs] + pair + ent[gt:ns] + ent[nt:]
        out.append(html[pos:e.start()] + ent)
        pos = end
    out.append(html[pos:])
    return "".join(out)


def _in_pair(html, at):
    """The block at `at` is in a pair or a trio: the nearest card-pair opened before it is not closed yet."""
    k = html.rfind('<div class="card-pair', 0, at)
    return k >= 0 and _div_end(html, k) > at


def _runs(html):
    """Runs of neighbouring pairable blocks: lists of (start, end)."""
    runs, run = [], []
    for b in _BLOCK_OPEN_RE.finditer(html):
        if run and b.start() < run[-1][1]:
            continue                               # a block inside the last one
        end = _div_end(html, b.start())
        if not _pairable(html[b.start():end]):
            if run:
                runs.append(run)
            run = []
            continue
        if run and html[run[-1][1]:b.start()].strip():
            runs.append(run)
            run = []
        run.append((b.start(), end))
    if run:
        runs.append(run)
    return runs


def pair_new_cards(html, page=None):
    """Wrap each two neighbouring pairable blocks in <div class="card-pair">; exactly three in a row stand in one line,
    <div class="card-pair card-trio"> (owner 2026-11-06, 7.38 Invoker's three facets: "Сделай на сайте как ты аспекта
    эти 3 рядом расположил"); src/js/card-trio.js starts their cards' parts on one line."""
    if PAGES is not None and page not in PAGES:
        return html
    out, pos = [], 0
    for run in _runs(html):
        groups = [run] if len(run) == 3 else [run[i:i + 2] for i in range(0, len(run) - 1, 2)]
        for g in groups:
            cls = "card-pair card-trio" if len(g) == 3 else "card-pair"
            blocks = [html[s:e] for s, e in g]
            if len(g) == 3 and any(_FOLD in b for b in blocks):
                blocks = [b if _FOLD in b else _fold_after_first(b) for b in blocks]
            gap = [html[g[k][1]:g[k + 1][0]] for k in range(len(g) - 1)] + [""]
            out.append(html[pos:g[0][0]] + f'<div class="{cls}">' + "".join(b + s for b, s in zip(blocks, gap)) + "</div>")
            pos = g[-1][1]
    out.append(html[pos:])
    return "".join(out)


_FOLD = '<div class="acr-fold'
_BODY = '<div class="ability-change-body">'
_TOGGLE = ('<button type="button" class="acr-fold-toggle" aria-expanded="false" aria-label="Show the whole text">'
           '</button>')


def _fold_after_first(block):
    """A card of a trio whose neighbours fold folds too, after its first row (owner 2026-11-06: three cards folded alike,
    "они в свёрнутом состоянии одинаковые"; 7.38 Agent of Gallaron stood open beside two folded ones)."""
    at = block.find(_BODY)
    if at < 0:
        return block
    end = _div_end(block, at)
    inner_start, inner_end = at + len(_BODY), end - len("</div>")
    first = block.find("<div", inner_start)
    if first < 0:
        return block
    rest = _div_end(block, first)
    if not block[rest:inner_end].strip():
        return block                                       # one row: nothing to fold
    return (block[:rest] + f'<div class="acr-fold"><div class="acr-fold-body">{block[rest:inner_end]}</div>{_TOGGLE}'
            f'</div>' + block[inner_end:])
