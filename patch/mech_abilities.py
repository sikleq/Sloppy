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
from .state import _State, page_cache

_ITEM_ICON_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "icons", "items")

# the lines of each info_tip (its rendered html -> its lines joined by <br>): li() reads a list back from it
TIP_RAW = page_cache({})
# the info_tips inline_list made: a list the row introduces, opened as a table in a Reworked mechanic
LIST_TIPS = page_cache(set())

_SUB = "&nbsp;&nbsp;– "
_CATEGORY_RE = re.compile(r"^(?:Items|Neutral Creeps|Heroes|Creeps|Units)(?:\s+—\s+|$)")
_NOTE_ONLY_RE = re.compile(r'^<span class="pop-note">(.*)</span>$', re.S)
_TIP_ONLY_RE = re.compile(r'^<span class="pop-tip">(.*)</span>$', re.S)     # hero_ability_rows: a "?" on the lead
_LEAD_ONLY_RE = re.compile(r'^<span class="pop-lead">(.*)</span>$', re.S)   # … a sentence before the lead
_TRAIL_NOTE_RE = re.compile(r'\s*<span class="pop-note">\(?(.*?)\)?</span>\s*$', re.S)
_TRAIL_BRACKET_RE = re.compile(r"\s+\(([^()<>]+)\)\s*$")
_TRAIL_ABILITY_RE = re.compile(r" ability$")
# an ability's name: capitalised words ("Fortune's End", "Storm Hammer"); the sentence starts at the first lower-case one
# ("Scream of Pain", "Echo of the Wild": a small "of" / "the" between capitalised words is still the name)
_ABIL_RE = re.compile(r"((?:[A-Z][\w'\-!]*)(?: (?:of |the |of the |and )?[A-Z][\w'\-!]*)*)(?: (?=[a-z])|[.,]|$)")
# "Oracle's Fortune's End", "Mars' Bulwark", and 7.37's lists "Chen: Divine Favor"
_OWNER_END_RE = re.compile(r"'s |(?<=s)' |: ")


def ability_chip(label, src):
    """An ability's icon as a small square, its name on hover only (facet rows, mechanic lists). A facet ("facet:<colour>:
    <icon>", from _icon_of_patch) is its coloured chip, as on every patch page (owner 2026-10-30: "фасеты … с цветами")."""
    label = _html.escape(label)
    if src.startswith("facet:"):
        from .badges import _FACET_COLOR_GRADIENT
        _f, colour, icon = src.split(":", 2)
        grad = _FACET_COLOR_GRADIENT.get(colour, _FACET_COLOR_GRADIENT["Gray0"])
        return (f'<span class="facet-chip" style="background-image:{grad}" data-tooltip="{label}" role="img" '
                f'aria-label="{label}"><img src="../icons/facets/{icon}.png" alt="" loading="lazy" width="16" '
                f'height="16"></span>')
    return (f'<span class="ability-chip" data-tooltip="{label}" role="img" aria-label="{label}"><img src="{src}" '
            f'alt="" loading="lazy" width="19" height="19"></span>')


_ENCHANT_RE = re.compile(r"^(?:Item bonus from )?(\w+) [Ee]nchantment$")   # "Audacious Enchantment"
# a unit named like an ability: the icon of the ability that summons it (7.41 "Warlock's Golem with talent")
_ICON_ALIASES = {("warlock", "Golem"): "warlock_rain_of_chaos",
                 ("lone_druid", "Spirit Bear's Return"): "lone_druid_spirit_bear_return"}   # the game's name: "Return"
# a map unit that is neither a hero nor a neutral creep: its abilities' prefix (7.41 "Tormentor's Reflect")
_UNIT_PREFIXES = {"Tormentor": "miniboss"}


# a rune's name in the notes -> its icon (scripts/fetch/fetch_rune_icons.py; Illusion has none in the game client —
# its icon is the Terrain page's own power-rune picture, icons/ui/gothic/tc_rune_3.png, owner 2026-10-28)
RUNE_ICONS = {"Bounty": "bounty", "Haste": "haste", "Double Damage": "doubledamage", "Amplify Damage": "doubledamage",
              "Illusion": "illusion",
              "Invisibility": "invisibility", "Regeneration": "regeneration", "Arcane": "arcane", "Shield": "shield",
              "Water": "water", "Wisdom": "wisdom",
              "Power": "power"}       # the game has none for the power runes as a whole: ours, gen_power_rune_icon.py
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


# map objects a list may name among items (7.37 Teleport Classification "Twin Gates"): the Terrain page's own icon
_MAP_OBJECT_ICONS = {"Twin Gates": "../icons/ui/gothic/tc_twingates.png"}


def _item_slug(name):
    if name == "Town Portal Scroll":
        return "tpscroll"
    m = _ENCHANT_RE.match(name)
    return (f"enhancement_{m.group(1).lower()}" if m
            else ITEM_SLUG.get(name, name.lower().replace(" ", "_").replace("'", "")))


def _item_icon(name):
    if name in _MAP_OBJECT_ICONS:
        return _MAP_OBJECT_ICONS[name]
    item = _item_slug(name)
    if _os.path.exists(_os.path.join(_ITEM_ICON_DIR, f"{item}.png")):
        return f"{ITEM_CDN}{item}.png"
    return None


_UPGRADE_OF_RE = re.compile(r"<h1>\s*Upgrade:\s*([^<]+?)\s*</h1>")


def _item_ability(name, version):
    """The item's own active in `version`, from the game's tooltip: Town Portal Scroll → "Teleport", Book of Shadows →
    "Shadows"; an item that upgrades another one's ("Upgrade: Town Portal Scroll", Boots of Travel) → that one's. None
    when the game names none (Twin Gates is a map object) — owner 2026-10-30: "у предметов тоже есть способности"."""
    from .item_ability_text import item_abilities
    from .loc_history import tooltip
    slug = _item_slug(name)
    for text in item_abilities(slug, version) or []:
        m = re.match(r"(?:Active|Use): ([^.!]+)", text)
        if m:
            return m.group(1).strip()
    up = _UPGRADE_OF_RE.search(tooltip(f"DOTA_Tooltip_Ability_item_{slug}_Description", version) or "")
    return _item_ability(up.group(1), version) if up and up.group(1) != name else None


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
        if (hero, abil) in INNATE_ABILITIES:
            return INNATE_ICON_URL
        return _icon_of_patch(hero, abil)
    icon = _item_icon(owner)                         # an item's ability: the item's own icon
    if icon:
        return icon
    prefix = _UNIT_PREFIXES.get(owner) or _creep_prefix(owner)
    if prefix:
        slug = f"{prefix}_{abil.lower().replace(' ', '_')}"
        return f"{ABIL_CDN}{slug}.png" if slug in _LOCAL_ABIL_ICONS else None
    return None


def _icon_of_patch(hero, name):
    """The icon of a hero's ability or facet by its name in the page's own patch — 7.37's lists name innates and
    facets gone since (Smoldering Resin, Cold Comfort): the ability's art, the innate mark, or the facet's icon."""
    from .ability_kv import hero_abilities, hero_facets
    from .elements import INNATE_ICON_URL
    version = _State.current_patch_version
    if not version:
        return None
    own = hero_abilities(hero, version).get(name.lower())
    if own:
        slug, innate = own
        if slug in _LOCAL_ABIL_ICONS:
            return f"{ABIL_CDN}{slug}.png"
        if innate:
            return INNATE_ICON_URL
    # a facet's ability without art (7.37 Heart of Battle, Phantasmagoria): the facet's icon, as its header shows
    for fname, colour, icon in hero_facets(hero, version).values():
        if fname.lower() == name.lower() and icon:
            path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "icons", "facets", f"{icon}.png")
            if _os.path.exists(path):
                return f"facet:{colour}:{icon}"            # drawn by ability_chip as the facet's coloured chip
    return None


def _sentence(rest):
    rest = rest.strip()
    return rest[:1].upper() + rest[1:]


def _parse_line(line):
    """'Oracle's Fortune's End can no longer …' -> (label, icon, sentence, caveat); 'Sange' -> (…, "", ""); or None."""
    caveat = ""
    m = _TRAIL_NOTE_RE.search(line) or _TRAIL_BRACKET_RE.search(line)
    if m:
        caveat, line = m.group(1).strip(), line[:m.start()]
    # Valve's own words around a name: "Tormentor's Reflect ability", "Blade Mail (both active and passive)" (7.41)
    line = _TRAIL_ABILITY_RE.sub("", line.replace("’", "'").strip())
    icon = _item_icon(line)
    if icon:
        return line, icon, "", caveat
    for end in _OWNER_END_RE.finditer(line):
        owner = line[:end.start()]
        m = _ABIL_RE.match(line, end.end())
        if not m:
            continue
        # the longest name with an icon: "Call of the Wild Hawk Dive Bomb" is Call of the Wild Hawk's Dive Bomb (7.37)
        words = m.group(1).split(" ")
        for n in range(len(words), 0, -1):
            name = " ".join(words[:n])
            icon = _icon(owner, name)
            if icon:
                cut = end.end() + len(name)
                rest = line[cut:] if n < len(words) else line[m.end():]
                return line[:cut], icon, _sentence(rest), caveat
    return None


ALWAYS = "Always"


def ability_list_rows(raw, least=2):
    """The note's lines as rows of icons, or None when it is not a list of abilities that all have an icon. least: a
    list the row introduces ("The following are no longer Disabled by Break: Lich: Death Charge", 7.37) is a table
    even with one icon — as the lists around it."""
    groups, caveats, notes, kinds = {}, {}, [], set()
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
        kinds.add("item" if icon.startswith(ITEM_CDN) else "ability")
    if sum(len(v) for v in groups.values()) < least:
        return None
    from .elements import info_tip
    if list(groups) == [""]:                           # the names alone: one row of icons across, no columns
        tip = f" {info_tip(*caveats[''])}" if "" in caveats else ""
        return (f'<span class="mech-abils"><span class="mech-abil-row mech-abil-only"><span class="mech-abil-icons">'
                f'{"".join(groups[""])}{tip}</span></span></span>', notes)
    # the plain abilities next to ones that need a condition ("with Aghanim's Scepter"): one row like the others,
    # "Always" in its first cell — across the whole table it stood apart and the icons column shrank to the
    # conditions' few icons (owner 2026-10-28, 7.41 Lifesteal "криво")
    if "" in groups:
        groups = {ALWAYS: groups.pop(""), **groups}
        if "" in caveats:
            caveats[ALWAYS] = caveats.pop("")
    # the sentence (or the condition) first, the icons after it, under a header like every table of columns (owner
    # 2026-10-28: "сначала столбец с always", "не хватает шапки, как в Lifesteal 7.38")
    rows = (f'<span class="mech-abil-row mech-head"><span class="mech-cell mech-label">{_first_title(groups)}</span>'
            f'<span class="mech-cell">{_ICONS_TITLE[frozenset(kinds)]}</span></span>')
    for sentence, chips in groups.items():
        tip = f" {info_tip(*caveats[sentence])}" if sentence in caveats else ""
        rows += (f'<span class="mech-abil-row"><span class="mech-cell mech-label">{sentence}{tip}</span>'
                 f'<span class="mech-cell mech-icons">{"".join(chips)}</span></span>')
    return f'<span class="mech-abils mech-cols-icons">{rows}</span>', notes


# the icons column's title: what its icons are (an item's own ability, "Eye of Skadi's Cold Attack", is the item's)
_ICONS_TITLE = {frozenset({"item"}): "Items", frozenset({"ability"}): "Abilities",
                frozenset({"item", "ability"}): "Items and abilities"}


_CONDITION_RE = re.compile(r"^(?:With|Triggered by|During|While) ")


def _first_title(groups):
    """"Condition" when the rows say only when (Always / With Aghanim's Scepter / With talent / Triggered by
    Bristleback passive), else "Change"."""
    return "Condition" if all(s == ALWAYS or _CONDITION_RE.match(s) for s in groups) else "Change"


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


def mech_text(*paragraphs):
    """A mechanic's details as plain paragraphs in the row's box, no table (owner 2026-10-30, 7.38 Roshan's pits: "не
    таблицей, а абзацем с удобной информацией"). li() puts it under the row's text."""
    rows = "".join(f'<span class="mech-abil-row"><span class="mech-abil-line">{p}</span></span>' for p in paragraphs)
    return f'<!--MECHTABLE--><span class="mech-abils mech-cols-1 mech-text">{rows}</span><!--/MECHTABLE-->'


BEFORE, AFTER = "Before", "After"


def mech_before_after(title, rows):
    """How a mechanic worked before the patch and how it works now, one row per thing (owner 2026-10-28, 7.41 Health
    Restoration: Valve's "X now … — before, …" / "… instead of …" rows). rows: (what, before, after)."""
    # Before and After get the same width: side by side they read as a pair
    return mech_table([title, BEFORE, AFTER], [list(r) for r in rows]).replace(
        'class="mech-abils mech-cols-3"', 'class="mech-abils mech-cols-3 mech-ba"', 1)


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


_HERO_LINE_RE = re.compile(r"^([A-Z][\w'.\- ]+?): (\S.*)$")
TWO_PAIRS_FROM = 12           # a list this long reads in two pairs of columns (hero | ability, hero | ability)


def hero_ability_rows(raw, least=1, row_text=""):
    """Valve's 7.37 lists "Hero: Ability (how)" as a table (owner 2026-10-30): the row's own text is its first line
    ("The following are considered a Teleport:" — "встроить внутри таблицы … как начало предложения"); the items and
    map objects of the list ("Town Portal Scroll", "Twin Gates") one line of their own — they are not heroes; then the
    hero (portrait + name) | the ability (its icon, or the facet's coloured chip, + its name, a line's "how" behind a
    "?" on it — no column of its own); a long list in two pairs of columns; the block's sentences about the list as its
    last lines. None when the list is not in that form or a line has no icon."""
    from .elements import info_tip
    from .images import HERO_CDN, HERO_SLUG
    pairs, notes, tips, leads, kinds = [], [], [], [], set()
    for line in (x.strip() for x in raw.split("<br>")):
        if line.startswith(_SUB):
            line = line[len(_SUB):]
        if not line:
            continue
        m = _NOTE_ONLY_RE.match(line)
        if m:
            notes.append(m.group(1))
            continue
        m = _TIP_ONLY_RE.match(line)          # a sentence for the "?" on the leading words (owner 2026-10-30)
        if m:
            tips.append(m.group(1))
            continue
        m = _LEAD_ONLY_RE.match(line)         # a sentence before the leading words (owner 2026-10-30)
        if m:
            leads.append(m.group(1))
            continue
        h = _HERO_LINE_RE.match(line)
        if h and h.group(1) in HERO_SLUG:
            parsed = _parse_line(line)
            if parsed is None:
                return None
            label, icon, sentence, caveat = parsed
            name = label[len(h.group(1)) + 2:]
            how = " ".join(x for x in (sentence.strip(" .,"), caveat) if x)
            hero = (f'<span class="mech-hero"><img src="{HERO_CDN}{HERO_SLUG[h.group(1)]}.png" alt="" loading="lazy" '
                    f'width="32" height="18">{_html.escape(h.group(1))}</span>')
            ability = (name, f'{ability_chip(name, icon)}<span class="mech-abil-name">{_html.escape(name)}</span>')
            kinds.add("Hero")
        else:
            parsed = _parse_line(line) if h else None      # an item's ability: "Gleipnir: Eternal Chains (…)"
            if parsed:
                name, icon, sentence, caveat = parsed
                caveat = " ".join(x for x in (sentence.strip(" .,"), caveat) if x)
            else:
                t = _TRAIL_BRACKET_RE.search(line)
                caveat, name = (t.group(1), line[:t.start()].strip()) if t else ("", line.strip())
                icon = _item_icon(name)
            if not icon:
                return None
            how = caveat
            # an item (or a map object) is a row as a hero is (owner 2026-10-30: "Items … гармонично встроить по
            # аналогии с hero"): its icon and name first, its ability — "Gleipnir: Eternal Chains" — next to it
            owner = h.group(1) if parsed and h else name
            owner_icon = _item_icon(owner) or icon
            hero = (f'<span class="mech-hero mech-hero-item"><img src="{owner_icon}" alt="" loading="lazy" '
                    f'width="25" height="18">{_html.escape(owner)}</span>')
            own = name[len(owner) + 2:] if parsed and h else _item_ability(name, _State.current_patch_version)
            # no ability the game names (Twin Gates): a short dash, not an empty cell (owner 2026-10-30)
            ability = ((own, f'{ability_chip(own, owner_icon)}<span class="mech-abil-name">{_html.escape(own)}</span>')
                       if own else ("", '<span class="mech-none">–</span>'))
            kinds.add("Item")
        detail = how[:1].upper() + how[1:] if how else ""
        # one row per hero (or item), his abilities side by side (owner 2026-10-30: "не дублируй героя")
        same = next((k for k, (hr, _a) in enumerate(pairs) if hr == hero), None)
        if same is None:
            pairs.append((hero, [(*ability, detail)]))
        else:
            pairs[same][1].append((*ability, detail))
    # items alone: a table only in a mechanic block of one box, where every list of the block is one (7.37 "Neutral
    # item active effects …: Book of Shadows, Force Boots"); elsewhere such lists keep their own form (7.41)
    if not ("Hero" in kinds or (kinds and _State.new_mech_one_box)) or len(pairs) < least:
        return None
    two = len(pairs) >= TWO_PAIRS_FROM
    # a short list with its words on how (7.37 "Partially Disabled by Break", the blocking lists): those words in a
    # column of their own; a long one in two pairs keeps them behind a "?" (owner 2026-10-30)
    with_details = not two and any(d for _h, abils in pairs for _n, _a, d in abils)
    width = 4 if two else 2
    line = lambda inner, cls="": (f'<span class="mech-abil-row"><span class="mech-cell mech-abil-line {cls}">'
                                  f'{inner}</span></span>')
    html = ""
    if row_text:
        text = row_text.rstrip()
        tip = f" {info_tip(*tips)}" if tips else ""
        before = "".join(f"{s.rstrip('.')}. " for s in leads)
        html += line(before + (text if text.endswith(":") else f"{text}:") + tip, "mech-table-lead")
    cells = lambda xs: "".join(f'<span class="mech-cell">{x}</span>' for x in xs)

    def tipped(a, d):
        return f'<span class="mech-item">{a}{" " + info_tip(d) if d else ""}</span>'

    def said(abils):                            # the details cell: each ability's words, named when there are two
        named = sum(1 for _n, _a, d in abils if d) > 1
        return "<br>".join(f"{n}: {d}" if named and n else d for n, _a, d in abils if d)
    if with_details:
        pairs = [(hero, f'<span class="mech-abil-set">{"".join(tipped(a, "") for _n, a, _d in abils)}</span>', said(abils))
                 for hero, abils in pairs]
    else:
        pairs = [(hero, f'<span class="mech-abil-set">{"".join(tipped(a, d) for _n, a, d in abils)}</span>')
                 for hero, abils in pairs]
    if pairs:
        first = "Hero or item" if kinds == {"Hero", "Item"} else next(iter(kinds))
        head = [first, "Ability", "Details"] if with_details else [first, "Ability"] * (width // 2)
        html += f'<span class="mech-abil-row mech-head">{cells(head)}</span>'
    if two:
        half = (len(pairs) + 1) // 2
        left, right = pairs[:half], pairs[half:] + [("", "")] * (half - len(pairs[half:]))
        for a, b in zip(left, right):
            html += f'<span class="mech-abil-row">{cells([*a, *b])}</span>'
    else:
        for a in pairs:
            html += f'<span class="mech-abil-row">{cells(a)}</span>'
    # the block's sentences about this list: lines of the table, across it (owner 2026-10-30, 7.37 Breakability)
    for note in notes:
        html += line(note, "mech-table-note")
    cols = "mech-cols-hero4" if two else "mech-cols-hero3" if with_details else "mech-cols-hero2"
    lead = " mech-captioned" if row_text else ""
    return f'<span class="mech-abils mech-cols-hero {cols}{lead}">{html}</span>', []


def lift_ability_lists(tips, open_text=False, row_text=""):
    """A mechanic row's trailing "?" notes: (the ones left, the tables that replace the others, the lists' closing
    notes — they go into the row's own text, "in one line with it" (owner 2026-10-28, 7.40 "All three of these …")).
    open_text: a list without abilities the row introduces (inline_list) opens too — only in a "Reworked mechanic"
    block so far (7.38 Lifesteal); a "New mechanic" (7.38 Neutral Items, Flooded Camps) keeps its "?" until the owner
    says otherwise, and so does a note of clarifications (7.38 Tormentor "Or at Dire side in Turbo …")."""
    left, rows, notes = [], "", []
    for tip in tips:
        raw = TIP_RAW.get(tip)
        found = raw is not None and (hero_ability_rows(raw, row_text=row_text)
                                     or ability_list_rows(raw, least=1 if tip in LIST_TIPS else 2)
                                     or (open_text and tip in LIST_TIPS and text_list_rows(raw, row_text)))
        if found:
            rows += found[0]
            notes += found[1]
        else:
            left.append(tip)
    return left, rows, notes
