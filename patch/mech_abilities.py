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
    rows = ""
    for sentence, chips in groups.items():
        tip = f" {info_tip(*caveats[sentence])}" if sentence in caveats else ""
        if sentence:
            rows += (f'<span class="mech-abil-row"><span class="mech-abil-icons">{"".join(chips)}</span>'
                     f'<span class="mech-abil-text">{sentence}{tip}</span></span>')
        else:
            rows += (f'<span class="mech-abil-row mech-abil-only"><span class="mech-abil-icons">{"".join(chips)}'
                     f'{tip}</span></span>')
    rows += "".join(f'<span class="mech-abil-row"><span class="mech-abil-note">{n}</span></span>' for n in notes)
    return f'<span class="mech-abils">{rows}</span>'


def lift_ability_lists(tips):
    """A mechanic row's trailing "?" notes: (the ones left, the rows of icons that replace the others)."""
    left, rows = [], ""
    for tip in tips:
        html = ability_list_rows(TIP_RAW[tip]) if tip in TIP_RAW else None
        if html:
            rows += html
        else:
            left.append(tip)
    return left, rows
