"""Every number a card's text says gets a row in its values card (owner 2026-11-10: "всё ещё неправильно определяешь,
сколько и какие значения писать в правой карточке" — 7.37 Impending Doom's "every 6.66 minutes … by 0.66s", 7.41 Ready
to Roll's "15/20/25/30% bonus movespeed for 4s", 7.37 Immolation's "damage (10/20/30/40) per second" had none). A number
the game's files name keeps the game's name (patch/deck_extra.py); any other is named by its own sentence:

  "for 4s"                        -> Duration        "every 6.66 minutes"     -> Interval
  "15/20/25/30% bonus movespeed"  -> Bonus movespeed "damage (10/20) per second" -> Damage per second
  "duration is increased by 0.66s" -> Duration (+0.66s)   "3x against creeps"  -> Multiplier against creeps

and a pair of rows for creeps and for heroes is one row, the creeps' value under the heroes' (owner 2026-11-10, 7.36c
Astral Spirit: "можно как-то лучше creeps/heroes значения записать, чтобы не так длинно было").
"""
import functools
import json
import os
import re

from .html_util import TAG_RE, div_end

# the names written for numbers by their sentence (owner 2026-11-10: "словарь подписей"): {key: name}; "" = no row
# (an example in brackets, a number that names nothing). Drafted per card, proofread; tools/value_names.py lists the
# numbers that have none.
NAMES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rules", "value_names.json")
KEY_BEFORE, KEY_AFTER = 6, 4


@functools.lru_cache(maxsize=None)
def names():
    try:
        with open(NAMES_FILE, encoding="utf-8") as f:
            return {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    except FileNotFoundError:
        return {}


def name_key(flat, a, b):
    """The words round a number, its own and other numbers left out ("#"): the same sentence in another patch, its
    numbers changed, finds the same name."""
    num = r"[+\-−]?\d[\d./]*[%xs]?"
    before = re.sub(num, "#", flat[:a]).lower().split()[-KEY_BEFORE:]
    after = re.sub(num, "#", flat[b:]).lower().split()[:KEY_AFTER]
    clean = lambda ws: [re.sub(r"[^a-z#'%/-]", "", w) for w in ws]
    return " ".join(w for w in clean(before) if w) + " [#] " + " ".join(w for w in clean(after) if w)

_NUM_RE = re.compile(r'<b class="iab-num">([^<]+)</b>')
_ROW_RE = re.compile(r'<div class="ability-change-row[^"]*">')
_VT = '<div class="value-table">'
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
# words that are no part of a value's name
_SKIP = {"is", "are", "was", "were", "be", "been", "increased", "decreased", "reduced", "rescaled", "changed", "raised",
         "lowered", "improved", "now", "by", "to", "from", "for", "of", "with", "the", "a", "an", "and", "or", "at", "in",
         "on", "within", "up", "its", "his", "her", "their", "every", "each", "all", "any", "over", "while", "when",
         "grants", "grant", "gains", "gain", "deals", "deal", "dealing", "has", "have", "that", "this", "it", "as",
         "also", "additional", "extra", "then", "after", "before", "if", "into", "than", "which", "who", "they", "he",
         "she", "takes", "take", "applies", "apply", "causes", "cause", "makes", "make", "level", "max", "increases",
         "decreases", "reduces", "increase", "decrease", "reduce", "raises", "lowers"}
_UNIT_TIME = {"second": "s", "seconds": "s", "s": "s", "sec": "s", "minute": " min", "minutes": " min"}
MAX_WORDS = 4


def _spans(row):
    """(the row's plain text, [(start, end, number as written)])."""
    flat, spans, pos = "", [], 0
    for m in _NUM_RE.finditer(row):
        flat += re.sub(r"\s+", " ", TAG_RE.sub(" ", row[pos:m.start()]))
        a = len(flat)
        flat += m.group(1)
        spans.append((a, len(flat), m.group(1)))
        pos = m.end()
    return flat + re.sub(r"\s+", " ", TAG_RE.sub(" ", row[pos:])), spans


def _phrase(words):
    """Up to MAX_WORDS name words from the start of `words`; [] when the first is no name word."""
    out = []
    for w in words:
        if w.lower() in _SKIP or len(out) == MAX_WORDS:
            break
        out.append(w)
    return out


def _name(words):
    while words and words[-1].lower() == "per":         # "bonus movespeed per level": the name ends before "per"
        words = words[:-1]
    while words and words[0].lower() == "per":
        words = words[1:]
    return " ".join(words).strip().capitalize() if words else None


def text_label(flat, a, b, text):
    """(label, value as shown) of the number at flat[a:b] by its sentence, or None when the sentence names nothing."""
    before = flat[:a].rstrip(" (")
    after = flat[b:].lstrip(" )")
    bw = _WORD_RE.findall(before)
    aw = _WORD_RE.findall(re.split(r"[.,;:!?()]", after, maxsplit=1)[0])
    unit = _UNIT_TIME.get(aw[0].lower()) if aw else None
    shown = text + unit if unit and not re.search(r"[a-z%]$", text) else text
    if unit:
        aw = aw[1:]
    last = bw[-1].lower() if bw else ""
    # "Cannonball projectile radius: 100" — the words before the colon name it
    if before.endswith(":"):
        named = _name(_WORD_RE.findall(re.split(r"[.;!?()]", before[:-1])[-1])[-MAX_WORDS:])
        if named:
            return named, shown
    if last in ("every", "each"):
        return "Interval", shown
    if last in ("for", "lasts", "last", "lasting") and (unit or text.endswith("s")):
        return "Duration", shown
    if text.endswith("x"):
        tail = " against " + aw[1] if len(aw) > 1 and aw[0].lower() == "against" else ""
        return "Multiplier" + tail, shown
    # "40% of Ghostship's damage", "20% of his max health": a share of the thing after "of"
    if aw and aw[0].lower() == "of":
        of = [w for w in _phrase([w for w in aw[1:] if not w.endswith("'s") and w.lower() not in ("his", "her", "its",
                                                                                                 "their", "the")])]
        if of:
            return _name(of), shown
    # the name after the number ("15% bonus movespeed", "900 speed"), "per second" with it
    own = _phrase(aw) if not (aw and aw[0].lower() == "per") else []
    per = " per second" if re.match(r"\s*(?:\w+\s+){0,3}per second\b", after) else ""
    if own:
        return _name(own) + (per if "second" not in " ".join(own).lower() else ""), shown
    # else the name before it, numbers and verbs passed over ("damage per second is decreased from X to …", "radius to
    # 450", "dealing damage (10/20/30/40) per second")
    # only the words of its own clause ("Every 6.66 minutes, duration is increased by": "duration")
    clause = re.split(r"[.,;:!?()]", before)[-1]
    prev = [w for w in _WORD_RE.findall(clause) if not re.fullmatch(r"[\d./%xs]+", w)]
    i = len(prev)
    while i and prev[i - 1].lower() in _SKIP:
        i -= 1
    j = i
    while j and prev[j - 1].lower() not in _SKIP and i - j < MAX_WORDS:
        j -= 1
    name = _name(prev[j:i])
    if not name:
        return None
    by = re.search(r"\bby\s*$", before)
    if by and not text.startswith(("+", "-", "−")):
        shown = _by_sign(before) + shown             # "increased by 0.66s": the change, not the value
    return name + (per if "second" not in name.lower() else ""), shown


# verbs only: "increases damage reduction by 5%" goes up, the noun "reduction" says nothing of the way
_DECREASE_RE = re.compile(r"(?:reduc|decreas)(?:e|es|ed|ing)|lower(?:s|ed|ing)?|slow(?:s|ed|ing)|decay(?:s|ed|ing)?|"
                          r"cut(?:s|ting)?|shorten(?:s|ed|ing)?|drop(?:s|ped|ping)?|weaken(?:s|ed|ing)?")
_INCREASE_RE = re.compile(r"(?:increas|rais|improv)(?:e|es|ed|ing)|boost(?:s|ed|ing)?|extend(?:s|ed|ing)?|"
                          r"grow(?:s|ing)?|amplif(?:y|ies|ied|ying)|add(?:s|ed|ing)?|gain(?:s|ed|ing)?|grant(?:s|ed|ing)?")


def _by_sign(before):
    """The sign of a change "by N": its sentence's last verb says which way ("reduces cooldown by 1s" -> "−",
    "slowing movement speed by 35%" -> "−", "increases damage by 10, radius by 175" -> "+")."""
    sentence = re.split(r"[.;!?]", before)[-1].lower()
    for w in reversed(_WORD_RE.findall(sentence)):
        if _DECREASE_RE.fullmatch(w):
            return "−"
        if _INCREASE_RE.fullmatch(w):
            return "+"
    return "+"


def without_tables(row):
    """A row's markup with its value tables taken out (Ghostship's Scepter: its text, then the table, in one row)."""
    while _VT in row:
        i = row.index(_VT)
        row = row[:i] + row[div_end(row, i):]
    return row


def _near(flat, a):
    """A name for a number its sentence names by no rule: the words of its clause before it."""
    clause = re.split(r"[.;:!?()]", flat[:a])[-1]
    words = [w for w in _WORD_RE.findall(clause) if w.lower() not in _SKIP][-MAX_WORDS:]
    return _name(words) or "Value"


def written_numbers(inner, norm):
    """The numbers of the pane's text the dictionary names: their rows come from it, not from the game's files."""
    known, out = names(), set()
    for m in _ROW_RE.finditer(inner):
        flat, spans = _spans(without_tables(inner[m.start():div_end(inner, m.start())]))
        out |= {norm(t) for a, b, t in spans if name_key(flat, a, b) in known}
    return out


def free_rows(inner, taken, labels, norm):
    """[(label, value html)] of the numbers of the pane's text that no row shows yet (`taken`: normalised numbers;
    `labels`: names in use, lower case), each named by its sentence. A number after "from" is the value before."""
    out = []
    for m in _ROW_RE.finditer(inner):
        row = inner[m.start():div_end(inner, m.start())]
        row = without_tables(row)               # a row holding the table still says numbers in its text
        # an Aghanim's part's numbers are the upgrade's: its name says so ("Damage (Shard) +10" beside "Damage")
        # ... where the card has the ability's own text too: a card that is all the upgrade needs no word for it
        part = next((f" ({k.title()})" for k in ("scepter", "shard") if f"aghanim-{k}" in m.group(0)), "") if any(
            "aghanim-" not in r.group(0) for r in _ROW_RE.finditer(inner)) else ""
        flat, spans = _spans(row)
        for a, b, text in spans:
            n = norm(text)
            # a 0 is a flag; a number after "from" the value before
            if n == "0" or re.search(r"\bfrom\s*$", flat[:a]):
                continue
            # a 1 only where its sentence names a thing ("1 cannonball per volley"), not "deals 1 more"
            got = text_label(flat, a, b, text) or (None if n == "1" else (_near(flat, a), text))
            written = names().get(name_key(flat, a, b))
            if written is not None:
                if not written:
                    continue                    # the dictionary says: no row for this number
                got = (written, got[1] if got else text)
            if not got or not got[0]:
                continue
            label, shown = got
            # a number a row shows already is not said twice; a change by it ("radius by 175" over "Radius 175") is
            # another value (7.37 Immolation's Shard)
            if n in taken and not shown.startswith(("+", "-", "−")):
                continue
            label += part
            if label.lower() in labels and any(l.lower() == label.lower() and norm(v) == n for l, v in out):
                continue
            taken.add(n)
            labels.add(label.lower())
            out.append((label, f'<b class="iab-num">{shown}</b>'))
    return out


_PAIR_RE = re.compile(r'<div class="vt-l(?P<lc>[^"]*)">(?P<l>(?:(?!</div>).)*?)\s*\((?P<who>creeps|heroes|hero|creep)\)'
                      r'</div><div class="vt-v(?P<vc>[^"]*)">(?P<v>(?:(?!<div|</div>).)*)</div>', re.S | re.I)


def merge_unit_pairs(table):
    """A table's "X (heroes)" and "X (creeps)" rows as one "X" row: the heroes' value, the creeps' under it."""
    cells = list(_PAIR_RE.finditer(table))
    by = {}
    for c in cells:
        who = "hero" if c.group("who").lower().startswith("hero") else "creep"
        by.setdefault(TAG_RE.sub("", c.group("l")).strip().lower(), {})[who] = c
    for name, two in by.items():
        if set(two) != {"hero", "creep"}:
            continue
        h, c = two["hero"], two["creep"]
        first = h if h.start() < c.start() else c
        merged = (f'<div class="vt-l{first.group("lc")}">{h.group("l").strip()}</div>'
                  f'<div class="vt-v{first.group("vc")}">{h.group("v")}'
                  f'<span class="vt-sub">creeps {c.group("v")}</span></div>')
        table = table.replace(first.group(0), merged, 1).replace((c if first is h else h).group(0), "", 1)
    return table
