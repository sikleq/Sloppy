"""A card's list of values as a table (owner 2026-11-05: "значения таблицей во всех карточках"): "Speed: 1600. Distance: 1200.
Damage: 27 + 3 per level." at the end of a card's text becomes rows of name | value across the whole card, lines between the
cells, values centred. Only values that are numbers or formulas go in ("Grants this ability: …" stays text); a formula's level
table opens right under its own row. Applied to the saved page (patch/page.py), so every kind of card gets it."""
import re

# two values make a table too (owner 2026-11-06, 7.38 Power Capture's Magnetic Field: "без таблицы - сделай"); one
# value reads fine as a sentence
MIN_VALUES = 2

_ROW_OPEN_RE = re.compile(r'<div class="ability-change-row(?: [^"]*)?">')
_TAG_RE = re.compile(r"<[^>]+>")
# a value's name starts a sentence: the text's start or after ". "; the value runs to the next ". " or the end
_PAIR_RE = re.compile(r"(?:(?<=^)|(?<=\. )|(?<=\.\x00))([A-Z][A-Za-z0-9 %'()/\-]{1,48}):\s*(.+?)(?:\.(?=\s|\x00|$)|$)")
_FORMULA_ID_RE = re.compile(r'class="formula-trigger" data-formula="([^"]+)"')


def _div_end(html, start):
    """Index just past the </div> that closes the <div at `start`."""
    depth = 0
    for m in re.finditer(r"<div\b|</div>", html[start:]):
        depth += 1 if m.group(0) == "<div" else -1
        if depth == 0:
            return start + m.end()
    return len(html)


# a word value the game lists among the numbers: "DISPEL TYPE: Basic Dispel" (owner 2026-11-06, 7.38 Demonic Cleanse:
# "можно Basic Dispel и 300/450/600 значения хила" in the table)
_WORD_VALUE_RE = re.compile(r"(?:Basic|Strong|Weak) Dispel$")


def _is_value(html):
    text = _TAG_RE.sub("", html).strip()
    return ('class="formula-trigger"' in html or bool(re.match(r"[+\-−]?x?\d", text))
            or bool(_WORD_VALUE_RE.fullmatch(text)))


def _split(inner, minimum=MIN_VALUES):
    """(text before, [(name, value html)], text after) of a row, or None when it holds fewer values than `minimum`."""
    tags = []
    flat = _TAG_RE.sub(lambda m: tags.append(m.group(0)) or "\x00", inner)
    pieces = [m for m in _PAIR_RE.finditer(flat) if _is_value(_restore(flat, tags, m.start(2), m.end(2)))]
    if not pieces or len(pieces) < minimum:
        return None
    before = _restore(flat, tags, 0, pieces[0].start()).rstrip()
    # the game's capitals ("DISPEL TYPE") read as every other label: "Dispel type"
    label = lambda s: s[:1] + s[1:].lower() if s.isupper() else s
    pairs = [(label(_restore(flat, tags, m.start(1), m.end(1))), _restore(flat, tags, m.start(2), m.end(2)).strip())
             for m in pieces]
    rest, pos = [], pieces[0].start()
    for m in pieces:
        rest.append(_restore(flat, tags, pos, m.start()))
        pos = m.end()
    rest.append(_restore(flat, tags, pos, len(flat)))
    after = re.sub(r"^[\s.]+", "", "".join(rest).strip())
    lone_tips = re.sub(r'<span class="info-tip".*?</span>\s*</span>', "", after, flags=re.S)
    if after and not _TAG_RE.sub("", lone_tips).strip(" ."):
        # only a [?] after the last value (7.41 Midnight Feast): it belongs to that value, not to a line of its own
        pairs[-1] = (pairs[-1][0], pairs[-1][1] + after.rstrip(" ."))
        after = ""
    return before, pairs, after


def _restore(flat, tags, a, b):
    """flat[a:b] with its tag placeholders put back."""
    k = flat[:a].count("\x00")
    out = []
    for ch in flat[a:b]:
        if ch == "\x00":
            out.append(tags[k])
            k += 1
        else:
            out.append(ch)
    return "".join(out)


_ABILITY_ICON_RE = re.compile(r'abilities/([a-z0-9_]+)\.(?:png|webp)')
_TRAILING_NOTE_RE = re.compile(r"\s*\(((?:[^()]|<[^>]*>)*)\)\s*$")
NOTE_FROM_WORDS = 4                  # a longer bracket after a value goes under [?]


def _label(name, slug):
    """The name, with its own icon when the ability has one for it (owner 2026-11-05, 7.41 Diviner's Deck: "The Fool")."""
    from .images import ABIL_CDN, _LOCAL_ABIL_ICONS
    from .mech_abilities import ability_chip
    icon = f"{slug}_{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}" if slug else ""
    return ability_chip(name, f"{ABIL_CDN}{icon}.png") + name if icon in _LOCAL_ABIL_ICONS else name


def _value(value):
    """A value with a long bracket after it keeps the number, the bracket goes under [?] (owner 2026-11-05, 7.41 The Tower:
    "400 All Damage Barrier (regenerates after not taking damage for 7s)")."""
    from .elements import inline_note
    m = _TRAILING_NOTE_RE.search(value)
    if not m or len(_TAG_RE.sub(" ", m.group(1)).split()) < NOTE_FROM_WORDS:
        return value
    return value[:m.start()] + inline_note(m.group(1))


def _lift_inlined(before):
    """(sentence, [(label, value)]): the numbers a card put into its sentence in brackets ("dealing damage (150)",
    cards_aghs.INLINED) go back to the table that stands under it, the brackets leave the sentence (owner 2026-11-06:
    "всё в таблицу")."""
    from .cards_aghs import INLINED
    lifted = []
    for key, label in INLINED.items():
        word, _, value = key.rpartition(" (")
        rx = re.compile(rf"(?i)\b({re.escape(word)}) \(((?:<b[^>]*>)?{re.escape(value[:-1])}(?:</b>)?)\)")
        m = rx.search(before)
        if m:
            before = before[:m.end(1)] + before[m.end():]
            lifted.append((label, m.group(2)))
    return before, lifted


def _table(pairs, formulas, slug=None):
    cells = []
    for n, (name, value) in enumerate(pairs):
        first = " vt-first" if n == 0 else ""
        cells.append(f'<div class="vt-l{first}">{_label(name, slug)}</div><div class="vt-v{first}">{_value(value)}</div>')
        for fid in _FORMULA_ID_RE.findall(value):
            if fid in formulas:
                cells.append(f'<div class="vt-f">{formulas[fid]}</div>')
    return f'<div class="value-table">{"".join(cells)}</div>'


_CARD_OPEN_RE = re.compile(r'<div class="ability-change[ "]')


def _rows_to_table(html):
    """{row start: split} of the rows that become tables. A card decides for both its sides: once one side has MIN_VALUES
    values, the other side's values are a table too, even two of them (owner 2026-11-05, 7.41 Sadist: a table on the left,
    a sentence on the right)."""
    cards = [(c.start(), _div_end(html, c.start())) for c in _CARD_OPEN_RE.finditer(html)]
    rows, by_card = {}, {}
    for m in _ROW_OPEN_RE.finditer(html):
        end = _div_end(html, m.start())
        inner = html[m.end():end - len("</div>")]
        if "<div" in inner or 'class="selves-table"' in inner:
            continue
        split = _split(inner, 1)
        if not split:
            continue
        card = max((c for c in cards if c[0] <= m.start() and end <= c[1]), default=None, key=lambda c: c[0])
        rows[m.start()] = split
        by_card.setdefault(card or m.start(), []).append(m.start())
    keep = {}
    for starts in by_card.values():
        if max(len(rows[s][1]) for s in starts) >= MIN_VALUES:
            keep.update({s: rows[s] for s in starts})
    return keep


_BLOCK_OPEN_RE = re.compile(r'<div class="ability-block[ "]')
_TRIGGER_RE = re.compile(r'<span class="formula-trigger" data-formula="([^"]+)">(.*?)</span>', re.S)
_LI_RE = re.compile(r"<li\b.*?</li>", re.S)
_CARD_OPEN_RE = re.compile(r'<div class="ability-change[ "]')


def _formula_key(inner):
    return re.sub(r"\s+", " ", _TAG_RE.sub("", inner)).strip()


def _drop_formulas_said_above(block):
    """A card's formula the rows over it already open as a level table (7.41 Persecutor: "Min Movement Slow rescaled from
    12.5/15/17.5/20% to 12% + 0.5% per level" and the same formula in the card): plain text in the card, without a second
    button and table (owner 2026-11-06: "лучше не дублировать, а убрать formula table из карточек")."""
    said = {_formula_key(m.group(2)) for li in _LI_RE.finditer(block) for m in _TRIGGER_RE.finditer(li.group(0))}
    if not said:
        return block
    dropped, out, pos = [], [], 0
    for c in _CARD_OPEN_RE.finditer(block):
        if c.start() < pos:
            continue
        end = _div_end(block, c.start())

        def plain(m):
            if _formula_key(m.group(2)) not in said:
                return m.group(0)
            dropped.append(m.group(1))
            return m.group(2)
        out.append(block[pos:c.start()] + _TRIGGER_RE.sub(plain, block[c.start():end]))
        pos = end
    out.append(block[pos:])
    block = "".join(out)
    for fid in dropped:
        w = re.search(rf'(?:<div class="vt-f">)?<div class="formula-table-wrap"><table[^>]*\bid="{re.escape(fid)}"', block)
        if w:
            block = block[:w.start()] + block[_div_end(block, w.start()):]
    return block


def drop_formulas_said_above(html):
    """_drop_formulas_said_above in every ability block of a page."""
    out, pos = [], 0
    for b in _BLOCK_OPEN_RE.finditer(html):
        if b.start() < pos:
            continue
        end = _div_end(html, b.start())
        out.append(html[pos:b.start()] + _drop_formulas_said_above(html[b.start():end]))
        pos = end
    out.append(html[pos:])
    return "".join(out)


_HL_OPEN_RE = re.compile(r'<span class="iab-hl iab-hl-\w+">')


def _span_end(html, start):
    """(index of the </span> closing the <span at `start`, index past it)."""
    depth = 0
    for m in re.finditer(r"<span\b|</span>", html[start:]):
        depth += 1 if m.group(0) == "<span" else -1
        if depth == 0:
            return start + m.start(), start + m.end()
    return len(html), len(html)


def _is_phrase(inner):
    text = re.sub(r"\d+(?:\.\d+)?(?:s|x|%)?", "", _TAG_RE.sub("", inner))
    return bool(re.search(r"[A-Za-z]{3,}", text))


def plain_phrases_in_cards(html):
    """Inside a card only numbers are coloured: a highlighted phrase is plain text (owner 2026-10-25: "красим только
    значения … иначе всё слишком покрашенное"; 2026-11-06, 7.41 Muerta's whole Shard sentence stood red). The talent rows'
    swaps outside the cards keep theirs."""
    out, pos = [], 0
    for c in _CARD_OPEN_RE.finditer(html):
        if c.start() < pos:
            continue
        end = _div_end(html, c.start())
        card = html[c.start():end]
        while True:
            hit = next((m for m in _HL_OPEN_RE.finditer(card)
                        if _is_phrase(card[m.end():_span_end(card, m.start())[0]])), None)
            if not hit:
                break
            close, past = _span_end(card, hit.start())
            card = card[:hit.start()] + card[hit.end():close] + card[past:]
        out.append(html[pos:c.start()] + card)
        pos = end
    out.append(html[pos:])
    return "".join(out)


def value_tables(html):
    """Every card with MIN_VALUES values or more on a side, as tables; the level tables of its formulas move under their rows."""
    html = plain_phrases_in_cards(drop_formulas_said_above(html))
    chosen = _rows_to_table(html)
    out, pos = [], 0
    for m in _ROW_OPEN_RE.finditer(html):
        if m.start() < pos or m.start() not in chosen:
            continue
        end = _div_end(html, m.start())
        split = chosen[m.start()]
        before, pairs, after = split
        before, lifted = _lift_inlined(before)
        pairs = lifted + pairs
        # the level tables of this row's formulas stand after it in the same card body
        ids = {fid for _, v in pairs for fid in _FORMULA_ID_RE.findall(v)}
        tail_end = html.find('<div class="ability-change-row', end)
        tail_end = len(html) if tail_end < 0 else tail_end
        tail = html[end:tail_end]
        formulas = {}
        for fid in ids:
            w = re.search(rf'<div class="formula-table-wrap"><table[^>]*\bid="{re.escape(fid)}"', tail)
            if w:
                formulas[fid] = tail[w.start():_div_end(tail, w.start())]
        for wrap in formulas.values():
            tail = tail.replace(wrap, "", 1)
        own = _ABILITY_ICON_RE.search(before)             # the ability the row is about, by its icon (an upgrade's part)
        row = html[m.start():m.end()] + (before + " " if before else "") + _table(pairs, formulas, own and own.group(1)) + (
            f'<span class="vt-after">{after}</span>' if after else "") + "</div>"
        out.append(html[pos:m.start()] + row + tail)
        pos = tail_end
    out.append(html[pos:])
    return formulas_under_their_rows("".join(out))


_BODY_OPEN_RE = re.compile(r'<div class="ability-change-body">')
_WRAP_RE = re.compile(r'<div class="formula-table-wrap"><table[^>]*\bid="([^"]+)"')


def formulas_under_their_rows(html):
    """A card keeps its formulas' level tables at the end of its text; each goes right under the row with its button
    (owner 2026-11-05, 7.41 Essence Flux: two formulas, both tables opened under the whole text)."""
    out, pos = [], 0
    for b in _BODY_OPEN_RE.finditer(html):
        if b.start() < pos:
            continue
        end = _div_end(html, b.start())
        body = html[b.end():end - len("</div>")]
        # a value table already holds its formulas' tables under their rows (.vt-f): those stay where they are
        wraps = {w.group(1): body[w.start():_div_end(body, w.start())] for w in _WRAP_RE.finditer(body)
                 if not body[:w.start()].endswith('<div class="vt-f">')}
        if not wraps:
            continue
        for wrap in wraps.values():
            body = body.replace(wrap, "", 1)
        moved, parts, k = set(), [], 0
        for r in _ROW_OPEN_RE.finditer(body):
            if r.start() < k:
                continue
            r_end = _div_end(body, r.start())
            mine = [fid for fid in _FORMULA_ID_RE.findall(body[r.start():r_end]) if fid in wraps and fid not in moved]
            parts.append(body[k:r_end] + "".join(wraps[fid] for fid in mine))
            moved.update(mine)
            k = r_end
        parts.append(body[k:] + "".join(w for fid, w in wraps.items() if fid not in moved))
        out.append(html[pos:b.end()] + "".join(parts) + "</div>")
        pos = end
    out.append(html[pos:])
    return "".join(out)
