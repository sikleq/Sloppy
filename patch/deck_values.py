"""A deck's new values card: the values that changed lit (owner 2026-11-09, 7.38 Time Zone: "остальные значения не
подкрашивать в карточке справа? (в new)" -> "да, так"). Run by patch/card_deck.py on the new side only; the old card
stays plain, it is there to compare.

  a value a change row under the ability names ("Duration decreased …", NERF)  -> that row's colour, buff or nerf;
  a value that changed with no such row (a rework), or that is new              -> gold, "changed";
  a value as it was                                                             -> as it is.

A number lit as the header's numbers are: its colour and a dotted line (elements.mark_number_highlights).
"""
import re

from .html_util import plain as _plain      # noqa: E402
_CELL_RE = re.compile(r'<div class="vt-l(?P<lf>[^"]*)">(?P<label>(?:(?!<div|</div>).)*)</div>'
                      r'<div class="vt-v(?P<vf>[^"]*)">(?P<value>(?:(?!<div|</div>).)*)</div>', re.S)
_ROW_RE = re.compile(r'<li data-tag="(?P<tag>\w+)"[^>]*>.*?<span class="row-text">(?P<text>.*?)</span>', re.S)
_BLOCK_RE = re.compile(r'<div class="ability-(?:change-)?block[ "]')
_COLOURS = {"buff", "nerf"}


def _cells(inner):
    """{label: value text} of the first value table in a pane's markup."""
    return {_plain(m.group("label")).lower(): _plain(m.group("value")) for m in _CELL_RE.finditer(inner)}


def rows_before(html, card_start):
    """[(tag, row text)] of the change rows of the block a card stands in, above it and under it (a card's own rows
    stand under it, card_pairs._rows_after_card — Sonnet 2026-11-09, 7.40 Clinkz "Spawn Interval improved", BUFF, lit
    red by its card)."""
    starts = [m.start() for m in _BLOCK_RE.finditer(html, max(0, card_start - 40000), card_start)]
    nxt = _BLOCK_RE.search(html, card_start + 1)
    part = html[starts[-1] if starts else card_start:nxt.start() if nxt else card_start + 40000]
    return [(m.group("tag"), _plain(m.group("text")).lower()) for m in _ROW_RE.finditer(part)]


_VERB_RE = re.compile(r"\b(?:increased|decreased|reduced|changed|rescaled|reworked|now|from|to|is|are)\b")
_SAME = {"movement": "move", "movespeed": "move speed", "hp": "health", "max": "max", "bonus": ""}


def _words(text):
    """The words of a name, alike however the game or the notes say it ("Movespeed" / "Movement Speed bonus")."""
    words = re.findall(r"[a-z0-9]+", text.lower().replace("'s", ""))
    return {w for x in words for w in _SAME.get(x, x).split()}


def _row_tag(label, rows):
    """The buff / nerf of the change row that names the value: it starts with the name, or — only one row — its subject
    holds all the name's words (Sonnet 2026-11-09, 7.41: "Hp regen" in the card, "Bonus HP Regen changed" in the row;
    "Movespeed" / "Movement Speed bonus rescaled"; "Max health damage" / "Dying unit's max health as damage")."""
    coloured = [(t, text) for t, text in rows if t in _COLOURS]
    tag = next((t for t, text in coloured if text.startswith(label + " ")), None)
    if tag:
        return tag
    want = _words(label)
    hits = {t for t, text in coloured if want and want <= _words(_VERB_RE.split(text, 1)[0])}
    return hits.pop() if len(hits) == 1 else None


_SUB_NAME_RE = re.compile(r'<b class="ac-sub-name">([^<]+)</b>')
_TITLE_RE = re.compile(r'<div class="ability-block[^"]*">(?:(?!</h4>).){0,600}?<h4 class="ability-title">([^<]+)</h4>', re.S)


def rows_of_named(html, card_start, card_html):
    """The rows of the hero's blocks of the abilities a card names in its parts ("Burning Army: …" in Clinkz's Scepter
    card): their change rows stand under their own block (Sonnet 2026-11-09, 7.40 "Spawn Interval improved")."""
    names = {n.strip().lower() for n in _SUB_NAME_RE.findall(card_html)}
    if not names:
        return []
    a = html.rfind('<div class="entity-block', 0, card_start)
    b = html.find('<div class="entity-block', card_start)
    part = html[max(a, 0):b if b > 0 else len(html)]
    out = []
    for m in _TITLE_RE.finditer(part):
        if m.group(1).strip().lower() in names:
            nxt = _BLOCK_RE.search(part, m.end())
            body = part[m.end():nxt.start() if nxt else len(part)]
            out += [(r.group("tag"), _plain(r.group("text")).lower()) for r in _ROW_RE.finditer(body)]
    return out


_LIT_RE = re.compile(r'<span class="iab-hl iab-hl-(\w+) iab-hl-num">(.*)</span>', re.S)
_HINT_OPEN_RE = re.compile(r'<span class="iab-hint[^"]*" data-tooltip="[^"]*">')
# the values where less is better: what a cast costs or how long one waits
_LOWER_BETTER_RE = re.compile(r"\b(?:cooldown|mana cost|health cost|cast point|charge restore|restore time|delay|"
                              r"interval|fade time|attack time|required level)\b")


def _unhint(html):
    """A value without the % tip a card gave it (its colours may say the other way)."""
    m = _HINT_OPEN_RE.search(html)
    if not m:
        return html
    depth, pos = 1, m.end()
    for t in re.finditer(r"<span\b|</span>", html[pos:]):
        depth += 1 if t.group() == "<span" else -1
        if depth == 0:
            end = pos + t.start()
            return html[:m.start()] + html[m.end():end] + html[end + len("</span>"):]
    return html


def _nums(text):
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", _plain(text))]


def _way(was, inner, label):
    """"buff" / "nerf" of a value against what it was, by the value's own way — less is better for a cooldown or a cost,
    more for the rest; None when the two can't be compared (no numbers, a formula)."""
    if re.search(r"\bper\b", _plain(was) + " " + _plain(inner)):
        return None
    o, n = _nums(was), _nums(inner)
    if not o or not n or sum(n) / len(n) == sum(o) / len(o):
        return None
    up = sum(n) / len(n) > sum(o) / len(o)
    return "buff" if up != bool(_LOWER_BETTER_RE.search(label)) else "nerf"


def _tip(was, inner, mark, label):
    """The value with the % of its change on hover, its colours by what the change means: the row's buff / nerf, else the
    value's own way — less is better for a cooldown or a cost, more for the rest (Sonnet 2026-11-09: 7.41 Lich
    Sacrifice's gold "Cooldown 120" showed its +100% green; 7.38 Demonic Cleanse's heal kept the card's reversed tip)."""
    from .number_tips import _number_tip
    # a formula ("245s - 5s per level", "6.9 + 0.1 per level") is no list of levels: its step read as a level's value
    # gave -98% (Sonnet 2026-11-09, 7.41 Marci Special Delivery, Dazzle) — no %, the colour says it
    if re.search(r"\bper\b", _plain(was) + " " + _plain(inner)):
        return None
    kind = mark if mark in ("buff", "nerf") else _way(was, inner, label)
    if not kind:
        return None
    o, n = _nums(was), _nums(inner)
    if len(o) > 1 and len(n) > 1 and len(o) != len(n):
        # lists of different lengths (an ultimate's three levels made a basic ability's four): the first level against
        # the first, the last against the last (owner 2026-11-10, 7.40 Shadow Step "Cooldown" 60/55/50 -> 32/28/24/20:
        # "не показывают % разницу")
        from .badges import b
        from .cards_item_abilities import _iab_hint
        lower_better = (kind == "buff") == (sum(n) / len(n) < sum(o) / len(o))
        pct = b([o[0], o[-1]], [n[0], n[-1]], l=lower_better)
        return _iab_hint(_unhint(inner), f'<span class="iab-tip-pct">{pct}</span>') if "badge" in pct else None
    return _number_tip(was, _unhint(inner), kind)
_FROM_RE = re.compile(r"\bfrom ([+\-−]?\d[\d.,/]*\s*(?:%|s)?) to\b")


def _row_was(label, rows):
    """The "from X" of the change row that names the value ("Cooldown decreased from 150/140/130/120s to 120s")."""
    want = _words(label)
    for _, text in rows:
        if text.startswith(label + " ") or (want and want <= _words(_VERB_RE.split(text, 1)[0])):
            m = _FROM_RE.search(text)
            if m:
                return m.group(1).strip()
    return None


def _mark(label, value, old, rows):
    """The colour of a new value, or None to leave it."""
    if "iab-hl" in value:                         # lit already by its own card
        return None
    tag = _row_tag(label, rows)
    was = old.get(label)
    if was is not None and was == _plain(value):
        return None
    if tag:
        return tag
    return "new" if old else None                 # no old table to compare with: only what a row names


def _lit(mark, inner):
    """A lit value. The dotted line under it says "a % on hover": a value with none (new to the ability, or not to be
    compared) is lit without the line ("iab-hl-flat" — owner 2026-11-10, 7.40 Shadow Step's gold values: "разве тут
    нужен пунктир … это новые значения у способности")."""
    flat = "" if "iab-hint" in inner else " iab-hl-flat"
    return f'<span class="iab-hl iab-hl-{mark} iab-hl-num{flat}">{inner}</span>'


def mark_new_values(new_inner, old_inner, rows):
    """The new pane's markup with its changed values lit."""
    old = _cells(old_inner)

    def cell(m):
        label = _plain(m.group("label")).lower()
        # the value before: the old card's, else the "from X to" of the row that names it (a header value the old
        # card had no table for — owner 2026-11-09, 7.40 Spirit Bear "Cooldown 120": "опять не всплывает % разницы")
        was = old.get(label) or _row_was(label, rows)
        if "iab-hl" in m.group("value"):
            # lit already by its card: a row that names it says the way (Sonnet 2026-11-09, 7.38 Demonic Cleanse: "Cleanse
            # heal" 300/450/600 -> 450 lit red by its mixed %, its row "Cleanse Heal rescaled" is BUFF)
            lit = _LIT_RE.fullmatch(m.group("value"))
            tag = _row_tag(label, rows)
            if not lit:
                return m.group(0)
            mark = tag or lit.group(1)
            inner = lit.group(2)
            if re.search(r"\bper\b", _plain(inner)):
                inner = _unhint(inner)          # a formula's tip its card gave (7.41 Dazzle "6.9 + 0.1 per level": -99%)
                was = None
            # its tip made anew when the row turns its colour or it had none
            if was and (tag and tag != lit.group(1) or "iab-tip-pct" not in inner):
                inner = _tip(was, inner, mark, label) or _unhint(inner)
            value = _lit(mark, inner)
            return (f'<div class="vt-l{m.group("lf")}">{m.group("label")}</div>'
                    f'<div class="vt-v{m.group("vf")}">{value}</div>')
        mark = _mark(label, m.group("value"), old, rows)
        if not mark:
            return m.group(0)
        # a value that changed with no row to say which way: the way its numbers went, as its tip shows it (owner
        # 2026-11-10, 7.40 Shadow Step "Mana cost" 150 -> 60/65/70/75 stood gold over a green tip). A value that is
        # only new to the card, or can't be compared, stays plain: the card lights what changed ("не нужно красить
        # new цветом просто новые значения … иначе если герой получил reworked shard, то всё жёлтым будет")
        if mark == "new":
            mark = _way(was, m.group("value"), label) if was else None
            if not mark:
                return m.group(0)
        # the % of the change on hover, as the header's numbers (owner 2026-11-09: "при наведении на измененные
        # значения не всплывает ничего, а мы показываем % разницу"); a new value has nothing to compare with
        tipped = _tip(was, m.group("value"), mark, label) if was else None
        value = _lit(mark, tipped or m.group("value"))
        return (f'<div class="vt-l{m.group("lf")}">{m.group("label")}</div>'
                f'<div class="vt-v{m.group("vf")}">{value}</div>')
    return _CELL_RE.sub(cell, new_inner)
