"""A mechanic section's list of abilities as icons (owner 2026-10-27/28, 7.40 Invulnerability Targeting, 7.38 Lifesteal,
7.41 Health Restoration and Lifesteal).

Valve list the abilities a reworked mechanic touches in a note behind the row's "?": "<Owner>'s <Ability> <what
changed>" one per line (7.40), or the names alone (7.41 "Affected spells: Eye of Skadi's Cold Attack, Sange, …"). On the
page that list is rows under the row's text instead: the ability's (or the item's) icon in place of its name, the name on
hover; abilities whose sentence is the same share one row ("With Aghanim's Scepter", "With talent" are such a sentence),
the names alone are one row of icons, and a line's own caveat in brackets becomes a "?" next to its icon. A list with a
line whose ability has no icon stays the note it was.
"""
import functools as _functools
import html as _html
import os as _os
import re

from .images import ABIL_CDN, HERO_SLUG, ITEM_CDN, ITEM_SLUG, _LOCAL_ABIL_ICONS
from .state import page_cache

_ITEM_ICON_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "icons", "items")

# the lines of each info_tip (its rendered html -> its lines joined by <br>): li() reads a list back from it
TIP_RAW = page_cache({})
# the info_tips inline_list made: a list the row introduces, opened as a table in a Reworked mechanic
LIST_TIPS = page_cache(set())

_SUB = "&nbsp;&nbsp;– "
_CATEGORY_RE = re.compile(r"^(?:Items|Neutral Creeps|Heroes|Creeps|Units)(?:\s+—\s+|$)")
_NOTE_ONLY_RE = re.compile(r'^<span class="pop-note">(.*)</span>$', re.S)
_TRAIL_NOTE_RE = re.compile(r'\s*<span class="pop-note">\(?(.*?)\)?</span>\s*$', re.S)
# an ability's name: capitalised words ("Fortune's End", "Storm Hammer"); the sentence starts at the first lower-case one
_ABIL_RE = re.compile(r"((?:[A-Z][\w'\-]*)(?: [A-Z][\w'\-]*)*)(?: (?=[a-z])|$)")
_OWNER_END_RE = re.compile(r"'s |(?<=s)' ")             # "Oracle's Fortune's End", "Mars' Bulwark"


def ability_chip(label, src):
    """An ability's icon as a small square, its name on hover only (facet rows, mechanic lists)."""
    label = _html.escape(label)
    return (f'<span class="ability-chip" data-tooltip="{label}" role="img" aria-label="{label}"><img src="{src}" '
            f'alt="" loading="lazy" width="19" height="19"></span>')


_ENCHANT_RE = re.compile(r"^(?:Item bonus from )?(\w+) [Ee]nchantment$")   # "Audacious Enchantment"
# a unit named like an ability: the icon of the ability that summons it (7.41 "Warlock's Golem with talent")
_ICON_ALIASES = {("warlock", "Golem"): "warlock_rain_of_chaos"}


# a rune's name in the notes -> its icon (scripts/fetch/fetch_rune_icons.py; Illusion has none in the game)
RUNE_ICONS = {"Bounty": "bounty", "Haste": "haste", "Double Damage": "doubledamage", "Amplify Damage": "doubledamage",
              "Invisibility": "invisibility", "Regeneration": "regeneration", "Arcane": "arcane", "Shield": "shield",
              "Water": "water", "Wisdom": "wisdom", "Power": "power"}
_RUNE_ROW_RE = re.compile(r"(?P<name>[A-Z][a-z]+(?: [A-Z][a-z]+)?) Runes?:\s")
_RUNE_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "icons", "runes")


def rune_row_chip(text, prefix="../"):
    """"Haste Rune: Duration no longer …" -> the rune's icon (its name on hover) + "Duration no longer …", like a facet
    row's ability (owner 2026-10-28, 7.40 Runes). The text as it was for a rune without an icon (Illusion)."""
    m = _RUNE_ROW_RE.match(text)
    key = RUNE_ICONS.get(m.group("name")) if m else None
    if not key or not _os.path.exists(_os.path.join(_RUNE_DIR, f"{key}.png")):
        return text
    rest = text[m.end():]
    return ability_chip(f"{m.group('name')} Rune", f"{prefix}icons/runes/{key}.png") + rest[:1].upper() + rest[1:]


def _item_icon(name):
    m = _ENCHANT_RE.match(name)
    item = (f"enhancement_{m.group(1).lower()}" if m
            else ITEM_SLUG.get(name, name.lower().replace(" ", "_").replace("'", "")))
    if _os.path.exists(_os.path.join(_ITEM_ICON_DIR, f"{item}.png")):
        return f"{ITEM_CDN}{item}.png"
    return None


@_functools.lru_cache(maxsize=1)
def _creep_prefixes():
    """{a neutral creep's name in the game ("Satyr Banisher"): its abilities' prefix ("satyr_trickster")} from the
    game's localization — the names Valve's notes use."""
    path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "abilities_english.txt")
    if not _os.path.exists(path):
        return {}
    text = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    for npc, name in re.findall(r'^\s*"npc_dota_neutral_([a-z0-9_]+)"\s+"([^"]*)"', text, re.M):
        out.setdefault(name, npc)
    return out


def _creep_prefix(owner):
    return _creep_prefixes().get(owner)


def _icon(owner, abil):
    """The icon of <owner>'s <abil> (a hero's, an item's or a neutral creep's ability), or None."""
    if owner in HERO_SLUG:
        from .elements import INNATE_ABILITIES, INNATE_ICON_URL, _hero_ability_slug
        hero = HERO_SLUG[owner]
        slug = _ICON_ALIASES.get((hero, abil)) or _hero_ability_slug(hero, abil)
        if slug in _LOCAL_ABIL_ICONS:
            return f"{ABIL_CDN}{slug}.png"
        # an innate without an icon of its own gets the innate mark, as its ability header does
        return INNATE_ICON_URL if (hero, abil) in INNATE_ABILITIES else None
    icon = _item_icon(owner)                         # an item's ability: the item's own icon
    if icon:
        return icon
    prefix = _creep_prefix(owner)
    if prefix:
        slug = f"{prefix}_{abil.lower().replace(' ', '_')}"
        return f"{ABIL_CDN}{slug}.png" if slug in _LOCAL_ABIL_ICONS else None
    return None


def _sentence(rest):
    rest = rest.strip()
    return rest[:1].upper() + rest[1:]


def _parse_line(line):
    """'Oracle's Fortune's End can no longer …' -> (label, icon, sentence, caveat); 'Sange' -> (…, "", ""); or None."""
    caveat = ""
    m = _TRAIL_NOTE_RE.search(line)
    if m:
        caveat, line = m.group(1).strip(), line[:m.start()]
    line = line.replace("’", "'").strip()
    icon = _item_icon(line)
    if icon:
        return line, icon, "", caveat
    for end in _OWNER_END_RE.finditer(line):
        owner = line[:end.start()]
        m = _ABIL_RE.match(line, end.end())
        icon = m and _icon(owner, m.group(1))
        if icon:
            return line[:m.end(1)], icon, _sentence(line[m.end():]), caveat
    return None


def ability_list_rows(raw):
    """The note's lines as rows of icons, or None when it is not a list of abilities that all have an icon."""
    groups, caveats, notes = {}, {}, []
    for line in (x.strip() for x in raw.split("<br>")):
        if line.startswith(_SUB):
            line = line[len(_SUB):]
        line = _CATEGORY_RE.sub("", line).strip()
        if not line:
            continue                                  # a bare category ("Heroes"): the icons say what each one is
        m = _NOTE_ONLY_RE.match(line)
        if m:
            notes.append(m.group(1))
            continue
        parsed = _parse_line(line)
        if parsed is None:
            return None
        label, icon, sentence, caveat = parsed
        groups.setdefault(sentence, []).append(ability_chip(label, icon))
        if caveat:
            # extra words about one ability: a "?" after the row's sentence, not among the icons where it read as one
            # more ability (owner 2026-10-28, 7.40 Bloodlust)
            caveats.setdefault(sentence, []).append(f"{label}: {caveat[:1].upper()}{caveat[1:]}")
    if sum(len(v) for v in groups.values()) < 2:
        return None
    from .elements import info_tip
    rows = ""                                          # the list's closing notes: the caller puts them in the row's text
    for sentence, chips in groups.items():
        tip = f" {info_tip(*caveats[sentence])}" if sentence in caveats else ""
        if sentence:
            rows += (f'<span class="mech-abil-row"><span class="mech-abil-icons">{"".join(chips)}</span>'
                     f'<span class="mech-abil-text">{sentence}{tip}</span></span>')
        else:
            rows += (f'<span class="mech-abil-row mech-abil-only"><span class="mech-abil-icons">{"".join(chips)}'
                     f'{tip}</span></span>')
    return f'<span class="mech-abils">{rows}</span>', notes


_EXAMPLES_RE = re.compile(r"^(?:(?P<pre>.*?),?\s+like\s+|Examples?:\s*)(?P<list>.+)$", re.S)
# a mechanic named without an owner: the icon of what players know it from (7.38 "Examples: Cleave, …")
_GENERIC_ICONS = {"Cleave": f"{ITEM_CDN}bfury.png"}


def _example_chip(name):
    """An example's icon (an item, "<Owner>'s <Ability>", "Blade Mail return damage" -> Blade Mail), else its name."""
    if name in _GENERIC_ICONS:
        return ability_chip(name, _GENERIC_ICONS[name])
    words = name.split()
    for n in range(len(words), 0, -1):
        parsed = _parse_line(" ".join(words[:n]))
        if parsed and not parsed[2]:
            return ability_chip(name, parsed[1])
    return f'<span class="mech-ex-name">{name}</span>'


def _split_examples(caveat):
    """"Examples: Cleave, Luna's Bouncing Glaives" -> ("", [chips]); "Effects that don't break Blink Dagger, like Orb
    of Venom or Necrophos' Heartstopper Aura" -> ("Effects that don't break Blink Dagger", [chips]); else None."""
    m = _EXAMPLES_RE.match(caveat)
    if not m:
        return None
    names = [x.strip() for x in re.split(r",\s*|\s+or\s+|\s+and\s+", m.group("list")) if x.strip()]
    return (m.group("pre") or "").strip(), [_example_chip(x) for x in names]


def text_list_rows(raw, row_text=""):
    """A list that names no abilities (7.38 Lifesteal "The following sources and targets do not provide any
    lifesteal"): its lines as the table's rows, open on the page instead of behind a "?" (owner 2026-10-28); a line's
    caveat in brackets is a "?" after it, its examples ("Examples: …", "… like X or Y") a column of icons. None for
    a single line or a list with sub-items (it stays a "?")."""
    lines, notes = [], []
    for line in (x.strip() for x in raw.split("<br>")):
        if not line:
            continue
        if line.startswith(_SUB):
            return None
        m = _NOTE_ONLY_RE.match(line)
        if m:
            notes.append(m.group(1))
            continue
        lines.append(line)
    if len(lines) < 2:
        return None
    from .elements import info_tip
    cells = []                                   # (the line with its "?", its examples' icons)
    for line in lines:
        examples = ""
        m = _TRAIL_NOTE_RE.search(line)
        if m:
            line, caveat = line[:m.start()].rstrip(), m.group(1).strip()
            split = _split_examples(caveat)
            if split:
                caveat, chips = split
                examples = "".join(chips)
            if caveat:
                line = f"{line} {info_tip(_sentence(caveat))}"
        cells.append((line, examples))
    if not any(ex for _l, ex in cells):
        rows = "".join(f'<span class="mech-abil-row"><span class="mech-abil-line">{line}</span></span>'
                       for line, _ex in cells)
        return f'<span class="mech-abils">{rows}</span>', notes
    # every column has its title (owner 2026-10-28): the first one names what the row lists ("The following sources
    # and targets …" -> "Sources and targets"); an empty examples cell is a short dash
    rows = (f'<span class="mech-abil-row mech-head"><span class="mech-cell mech-label">{_list_title(row_text)}</span>'
            '<span class="mech-cell">Examples</span></span>')
    rows += "".join(f'<span class="mech-abil-row"><span class="mech-cell mech-label">{line}</span>'
                    f'<span class="mech-cell mech-ex">{ex or "–"}</span></span>' for line, ex in cells)
    return f'<span class="mech-abils mech-cols-ex">{rows}</span>', notes


_FOLLOWING_RE = re.compile(r"\bthe following ([a-z][a-z ]*?)(?= (?:do|does|have|has|are|is|will|can|no|now)\b|$)",
                           re.I)


def _list_title(row_text):
    """What a row's list is ("The following sources and targets do not …" -> "Sources and targets"), else "Case"."""
    m = _FOLLOWING_RE.search(re.sub(r"<[^>]+>", "", row_text or ""))
    return _sentence(m.group(1)) if m else "Case"


def mech_table(head, rows):
    """A mechanic's rules as a table written in the content (7.38 Lifesteal: Lifesteal / Spell Lifesteal × what each
    applies to × its cut against non-heroes — Valve's three sentences, owner 2026-10-28 "неудобно читается"). head: the
    column titles; rows: lists of cells, or a str for a line across the whole table. The first column reads as a
    label (left), the others are values (centred). li() puts it under the row's text."""
    cols = len(head)
    out = ('<span class="mech-abil-row mech-head">'
           + "".join(f'<span class="mech-cell{" mech-label" if i == 0 and cols > 1 else ""}">{h}</span>' for i, h in enumerate(head))
           + '</span>')
    for row in rows:
        if isinstance(row, str):
            out += f'<span class="mech-abil-row"><span class="mech-abil-line">{row}</span></span>'
        else:
            out += ('<span class="mech-abil-row">' + "".join(
                f'<span class="mech-cell{" mech-label" if i == 0 and cols > 1 else ""}">{c}</span>' for i, c in enumerate(row))
                + '</span>')
    return f'<!--MECHTABLE--><span class="mech-abils mech-cols-{cols}">{out}</span><!--/MECHTABLE-->'


def mech_pair(main, side):
    """Two mech_tables side by side, their rows level with each other (owner 2026-10-28, 7.38 Lifesteal: "Against
    non-heroes" a block of its own next to the damage types). Both must have the same number of rows."""
    def body(t):
        return re.sub(r"<!--/?MECHTABLE-->", "", t)
    rows = body(main).count('class="mech-abil-row')
    if rows != body(side).count('class="mech-abil-row'):
        raise ValueError("mech_pair: the two tables need the same number of rows")
    return (f'<!--MECHTABLE--><span class="mech-pair" style="--mech-rows:{rows}">{body(main)}{body(side)}</span>'
            '<!--/MECHTABLE-->')


def lift_ability_lists(tips, open_text=False, row_text=""):
    """A mechanic row's trailing "?" notes: (the ones left, the tables that replace the others, the lists' closing
    notes — they go into the row's own text, "in one line with it" (owner 2026-10-28, 7.40 "All three of these …")).
    open_text: a list without abilities the row introduces (inline_list) opens too — only in a "Reworked mechanic"
    block so far (7.38 Lifesteal); a "New mechanic" (7.38 Neutral Items, Flooded Camps) keeps its "?" until the owner
    says otherwise, and so does a note of clarifications (7.38 Tormentor "Or at Dire side in Turbo …")."""
    left, rows, notes = [], "", []
    for tip in tips:
        raw = TIP_RAW.get(tip)
        found = raw is not None and (ability_list_rows(raw)
                                     or (open_text and tip in LIST_TIPS and text_list_rows(raw, row_text)))
        if found:
            rows += found[0]
            notes += found[1]
        else:
            left.append(tip)
    return left, rows, notes
