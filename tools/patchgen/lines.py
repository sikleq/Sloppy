"""What several passes share about the scaffold's lines: the patterns of its blocks, the bosses, small helpers."""
import ast
import os
import re

from .common import _HERE

def _li_parts(line):
    """(text, keyword sources {name: source}, call node) of a one-line W(li("text", ...)) statement, else None."""
    try:
        call = ast.parse(line.strip()).body[0].value
    except (SyntaxError, IndexError, AttributeError):
        return None
    if not (isinstance(call, ast.Call) and getattr(call.func, "id", "") == "W" and call.args
            and isinstance(call.args[0], ast.Call) and getattr(call.args[0].func, "id", "") == "li"):
        return None
    li = call.args[0]
    if not (li.args and isinstance(li.args[0], ast.Constant) and isinstance(li.args[0].value, str)):
        return None
    src = line.strip()
    return li.args[0].value, {k.arg: ast.get_source_segment(src, k.value) for k in li.keywords}, li
# "Bonus Armor decreased from +6 to +7" or "Mana Regen bonus increased from +1.5 to +1"
# We allow the stat name to come BEFORE the verb ("Bonus Armor decreased")
# OR AFTER ("Armor bonus decreased"); both forms appear in patchnotes.
_PROP_CHANGE_RE = re.compile(
    r'^(?P<stat>[A-Z][a-zA-Z\'/ ]+?)\s+'
    r'(?:bonus\s+)?(?P<verb>increased|decreased|rescaled|changed)\s+'
    r'from\s+\+?(?P<old>[\d./]+%?)\s+to\s+\+?(?P<new>[\d./]+%?)\s*$'
)
_ENTITY_START_RE = re.compile(r'^\s*W\((?:item|hero|unit|plain|enchant)_header\(|^\s*W\(section\(')


# Valve described the damage GROWTH as rescaled (7.38 Universal heroes, Spectre 7.40): a gain-per-level or a
# level-30 row. A lone "Damage at level 1" (+1 base damage) keeps its own row.
_HERO_DMG_ROW_RE = re.compile(r'W\(li\(\s*"(?:Damage gain per level|Damage at level 30) ')


_REMOVED_FACETS_RE = re.compile(r'W\(li\("Removed (.+?) Facets?", t\("DEL"\)(?:, extra=(.*))?\)\)$')
_REMOVED_ABILITY_RE = re.compile(r'W\(li\("Removed ([A-Z][^"]*?) ability", t\("DEL"\)(?:, extra=(.*))?\)\)$')
_FACET_BLOCK_RE = re.compile(r'W\((?:facet_header|new_facet|facet_change)\(')
_HERO_NAME_RE = re.compile(r'W\(hero_header\("([^"]+)"')


def _py_repr(v):
    """Format a number or list-of-numbers for inline emission."""
    if isinstance(v, list):
        return '[' + ', '.join(_py_repr(x) for x in v) + ']'
    return repr(v)


_ROW_RE = re.compile(r'^W\(li\("(?P<text>(?:[^"\\]|\\.)*)", (?P<badge>t\("(?P<tag>[A-Za-z]+)"\))'
                     r'(?:, extra=inline_note\("(?P<note>(?:[^"\\]|\\.)*)"\))?\)\)$')


def _row(text, tag, note=None):
    extra = f', extra=inline_note("{note}")' if note else ''
    return f'W(li("{text}", t("{tag}"){extra}))'


# Map bosses: an ability-by-ability layout like a hero (7.38 Roshan / Tormentor).
_BOSSES = {
    "Roshan": ("../icons/units/npc_dota_roshan.png", "roshan_"),
    "Tormentor": ("../icons/units/npc_dota_miniboss.png", "miniboss_"),
}
_BOSS_ABIL_CACHE = {}


def _boss_abilities(prefix):
    """{display name: icon url} of a boss's abilities, from the game localization."""
    if prefix not in _BOSS_ABIL_CACHE:
        path = os.path.join(_HERE, "data", "abilities_english.txt")
        found = {}
        try:
            txt = open(path, encoding="utf-8").read()
        except OSError:
            txt = ""
        for m in re.finditer(r'"DOTA_Tooltip_Ability_(' + prefix + r'[a-z_]+?)"\s+"([^"]+)"', txt, re.I):
            slug, name = m.group(1).lower(), m.group(2)
            if name not in found:
                found[name] = f"../icons/abilities/{slug}.png"
        _BOSS_ABIL_CACHE[prefix] = found
    return _BOSS_ABIL_CACHE[prefix]


def _drop_empty_ul(lines):
    """W(ul_open()) right before W(ul_close()) — every row of the block moved into a card — is dropped."""
    out = []
    for ln in lines:
        if ln.strip() == "W(ul_close())" and out and out[-1].strip() == "W(ul_open())":
            out.pop()
            continue
        out.append(ln)
    return out
