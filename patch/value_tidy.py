"""The values card's rows written the one way (Sonnet proofread 2026-11-10 of all 540 cards: 252 rows read wrong):

  "Movement slow +35%"            -> "Movement slow 35%"     a slow, a reduction is its amount, no sign
  "Duration 10", "Torrent interval 0.25" -> "10s", "0.25s"   a time has its unit ("Consume time 10 min" by its text)
  "Hp regen", "Dps", "Agi damage mult" -> "Health regen", "Damage per second", "Agility damage multiplier"
  "Root Duration"                 -> "Root duration"         sentence case; a name the text writes capitalised stays
  "Scepter max level (Scepter)"   -> "Max level (Scepter)"   the part once, at the end
  "Num cannon volleys"            -> "Cannon volleys"        names the game's keys give badly: data/rules/value_labels.json
"""
import functools
import json
import os
import re

LABELS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rules", "value_labels.json")

# a header value's name has its icon first ("<img …>Cooldown")
_CELL_RE = re.compile(r'(?P<open><div class="vt-l[^"]*">(?:<img[^>]*>)?)(?P<l>[^<]*)(?P<mid></div><div class="vt-v[^"]*">)'
                      r'(?P<v>(?:(?!</div>).)*)(?P<close></div>)', re.S)
# a header's number comes lit already, a span of its own ("<span class="iab-hl iab-hl-nerf iab-hl-num">100/90/80</span>")
# ... its % on hover a span inside that ("<span class="iab-hint" data-t="…">60/55/50</span>")
_NUM_RE = re.compile(r'(<b class="iab-num">|<span class="iab-(?:hl|hint)[^"]*"[^>]*>)([^<]+)(</b>|</span>)')
# the last word of a name that says the value takes away: its number is the amount, no minus ("Cooldown reduction
# 10s"; "increases damage reduction by 5%" keeps its +); a slow is its amount, no sign at all; a penalty keeps its
# sign, it is the change of one ("Max level penalty −1")
DECREASE_HEADS = {"reduction", "decrease", "decay", "loss", "amp", "amplification"}   # "-20% more vulnerable": 20%
SLOW_HEADS = {"slow", "slows"}
TIME_HEADS = {"duration", "delay", "interval", "cooldown", "time", "buffer", "timer", "airtime"}
_ABBR = {"hp": "health", "dps": "damage per second", "agi": "agility", "int": "intelligence", "mult": "multiplier",
         "num": "", "pct": "", "resist": "resistance"}


@functools.lru_cache(maxsize=None)
def labels():
    """{(name as built, lower case, words its card's text must have or ""): name to show}."""
    try:
        with open(LABELS_FILE, encoding="utf-8") as f:
            raw = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    except FileNotFoundError:
        return {}
    out = {}
    for k, v in raw.items():
        name, _, words = k.partition(" | ")
        out[(name.strip().lower(), words.strip().lower())] = v
    return out


def _renamed(label, text):
    low, txt = label.lower(), text.lower()
    scoped = [v for (n, w), v in labels().items() if n == low and w and w in txt]
    return scoped[0] if scoped else labels().get((low, ""))


# names the site shows as icons or writes capitalised everywhere (Invoker's orbs, the attributes)
ALWAYS_NAMES = ("Quas", "Wex", "Exort", "Strength", "Agility", "Intelligence")


def _head(label):
    """The word a name is about: "Movement slow per stack (Scepter)" -> "slow"."""
    core = re.sub(r"\s*\([^)]*\)\s*$", "", label)
    core = re.split(r"\s+(?:per|in|by|on|near|at|for|against|from)\s+", core, maxsplit=1)[0]   # "Attack slow in water"
    words = core.lower().split()
    return words[-1] if words else ""


# stat words: a capitalised run of them is Valve's Title Case ("Debuff Duration bonuses"), no name
_COMMON = {"damage", "duration", "radius", "base", "bonus", "max", "min", "speed", "health", "mana", "cooldown", "range",
           "attack", "movement", "move", "slow", "stun", "heal", "amp", "armor", "gold", "gain", "increased", "debuff",
           "buff", "per", "chance", "time", "regen", "magic", "physical", "spell", "level", "levels", "all", "status",
           "resistance", "the", "a", "an", "of", "and", "or", "to", "with", "is", "are", "now", "no", "barrier"}
_RUN_RE = re.compile(r"[A-Z][\w']*(?:\s+[A-Z][\w']*)*")


def _names(text):
    """The names the card's text writes ("Blade Fury", "Shadow Wave", "Quas", "Groovin'"), longest first: a run of
    capitalised words with no stat word in it; a lone word only after a lower case word, not as a sentence's first."""
    out = set()
    for m in _RUN_RE.finditer(text):
        words = [w[:-2] if w.endswith("'s") else w for w in m.group(0).split()]
        if any(w.lower() in _COMMON for w in words) or all(w.isupper() for w in words):
            continue
        if len(words) == 1 and not re.search(r"(?:^|[\s(])[a-z0-9][\w'%]*[,)]?\s+$", text[:m.start()]):
            continue
        out.add(" ".join(words))
    return sorted(out, key=len, reverse=True)


def tidy_label(label, text):
    lab = label.strip()
    mapped = _renamed(lab, text)
    if mapped:
        return mapped
    words = []
    for w in lab.split():
        low = w.lower()
        if low in _ABBR:
            words += _ABBR[low].split()
        else:
            words.append(w)
    for part in ("Scepter", "Shard"):
        if words and words[0].lower() == part.lower() and len(words) > 1:
            words = words[1:]
            if f"({part})" not in words:
                words.append(f"({part})")
    # sentence case, then the names the text writes get their capitals back ("Blade fury radius" -> "Blade Fury radius")
    out = [w if i == 0 or w.isupper() or w.startswith("(") else w.lower() for i, w in enumerate(words)]
    tidy = " ".join(out)
    for name in _names(text) + list(ALWAYS_NAMES):
        tidy = re.sub(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", name, tidy, flags=re.I)
    tidy = tidy[:1].upper() + tidy[1:]
    return tidy if tidy else label


def tidy_value(label, value, text):
    m = _NUM_RE.search(value)
    if not m:
        return value
    num = m.group(2)
    head = _head(label)
    if head in SLOW_HEADS:                       # "3 / -6 / -9%" (7.37 Plague Carrier) -> "3/6/9%"
        num = re.sub(r"\s*/\s*", "/", re.sub(r"(?:(?<=^)|(?<=/)|(?<=\s))[+\-−]", "", num))
    elif head in DECREASE_HEADS and num[:1] in "-−":
        num = num[1:]
    bare = re.fullmatch(r"[\d./]+", num)
    if bare and head == "lifesteal":             # a lifesteal is a share (7.41 Midnight Feast "12/16/20/24")
        num += "%"
    if bare and head == "angle":                 # "Vision cone angle 90"
        num += "°"
    distance = re.search(r"\b(?:range|distance|radius|width|length)\b", label.lower())   # "Attack range buffer 125"
    # a time is the name's last word, or a word before its "reduction"/"bonus" ("Base attack time reduction 0.25")
    timed = head in TIME_HEADS or (head in ("reduction", "bonus", "increase", "decrease")
                                   and TIME_HEADS & set(label.lower().split()))
    if timed and not distance and re.fullmatch(r"[\d./]+", num):
        num += " min" if re.search(re.escape(num) + r"\s*min", text) else "s"
    return value[:m.start(2)] + num + value[m.end(2):]


def tidy(html, text):
    """`html` with its values card rows written the one way; `text`: the card's plain text, for units and names."""
    def cell(m):
        label = tidy_label(m.group("l"), text) if m.group("l").strip() else m.group("l")
        return m.group("open") + label + m.group("mid") + tidy_value(label, m.group("v"), text) + m.group("close")
    return _CELL_RE.sub(cell, html)
