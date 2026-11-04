"""A new or returning unit's numbers as the game shows them (owner 2026-11-04, variant 3 of the mock): health and mana as
bars, the rest as tiles, gold and XP in the colours of the Neutral Creeps table. The numbers come from the game's files of
the patch, so a new unit needs no numbers typed by hand. A returning unit's changed number is in its tag's colour, dotted,
"old -> new" and the % on hover; Valve's rows stay in the content with covered=True for tags and weights (7.38 Ancient
Prowlers)."""
import html as _html
import re

from . import game_files
from .state import _State

_UNITS_FILE = "scripts/npc/npc_units.txt"
_BASE_UNIT = "npc_dota_units_base"

# two rows of seven: attack first, then toughness, movement and what the unit pays
TILES = ("Level", "Damage", "Attack Speed", "BAT", "Attack Point", "Attack Range", "Acquisition Range",
         "Armor", "Magic Res", "Move Speed", "Turn Rate", "Vision", "Gold", "XP")
_TILE_CLASS = {"Gold": " us-gold", "XP": " us-xp"}


def _block(text, npc):
    """The unit's own lines of npc_units.txt: {"StatusHealth": "700", …}. A nested block's keys are never asked for."""
    start = re.search(rf'^\s*"{re.escape(npc)}"\s*$', text, re.M)
    if not start:
        return None
    end = re.search(r'^\t"[^"]+"\s*$', text[start.end():], re.M)
    body = text[start.end():start.end() + end.start()] if end else text[start.end():]
    out = {}
    for key, value in re.findall(r'^\s*"(\w+)"\s+"([^"]*)"', body, re.M):
        out.setdefault(key, value)
    return out


def neutrals(text):
    """The neutral creeps of an npc_units.txt that give experience: the ones a player can meet in a camp."""
    names = re.findall(r'^\t"(npc_dota_neutral_[a-z0-9_]+)"\s*$', text, re.M)
    return {n for n in names if float((_block(text, n) or {}).get("BountyXP") or 0) > 0}


def new_neutrals(version, previous):
    """The creeps a patch adds: in its files and not in the previous patch's. None when that cannot be told (a patch
    missing from the game-files store): "no new creeps" would be a lie then."""
    now, before = game_files.read(version, _UNITS_FILE), game_files.read(previous, _UNITS_FILE) if previous else None
    return sorted(neutrals(now) - neutrals(before)) if now and before else None


def _g(value):
    return f"{float(value):g}"


def numbers(text, npc):
    """The unit's numbers as shown, by tile name, with what the game's base unit gives for a value it does not state."""
    base, own = _block(text, _BASE_UNIT) or {}, _block(text, npc)
    if own is None:
        raise ValueError(f"unit_sheet: {npc} is not in the game's units of this patch")
    kv = {**base, **own}
    day, night = _g(kv["VisionDaytimeRange"]), _g(kv["VisionNighttimeRange"])
    return {
        "Health": _g(kv["StatusHealth"]), "Health Regen": _g(kv["StatusHealthRegen"]),
        "Mana": _g(kv["StatusMana"]), "Mana Regen": _g(kv["StatusManaRegen"]),
        "Level": _g(kv["Level"]),
        "Damage": f'{_g(kv["AttackDamageMin"])}-{_g(kv["AttackDamageMax"])}',
        "Attack Speed": _g(kv["BaseAttackSpeed"]),
        "BAT": f'{_g(kv["AttackRate"])}s',
        "Attack Point": f'{_g(kv["AttackAnimationPoint"])}s',
        "Attack Range": _g(kv["AttackRange"]),
        "Acquisition Range": _g(kv["AttackAcquisitionRange"]),
        "Armor": _g(kv["ArmorPhysical"]),
        "Magic Res": f'{_g(kv["MagicalResistance"])}%',
        "Move Speed": _g(kv["MovementSpeed"]),
        "Turn Rate": _g(kv["MovementTurnRate"]),
        "Vision": day if day == night else f"{day}/{night}",
        "Gold": f'{_g(kv["BountyGoldMin"])}-{_g(kv["BountyGoldMax"])}',
        "XP": _g(kv["BountyXP"]),
    }


def changed_value(cls, shown, old, badge):
    """A changed number: the new one alone, in its tag's colour and dotted; "old -> new" and the % in that colour on hover,
    as in the item and ability cards (owner 2026-11-04: "каша в числах"). The site's tooltip reads its text as HTML."""
    overall = re.search(r'data-overall="(buff|nerf)"', badge)
    pct = re.search(r">([+-]?[\d.]+%)<", badge)
    tone = f" iab-{overall.group(1)}" if overall else ""
    note = f"{old} \u2192 {shown}"
    if pct:
        note += f' <span class="iab-num{tone}">({pct.group(1)})</span>'
    return (f'<b class="{cls}{tone}"><span class="iab-hint abil-ico-hint" '
            f'data-tooltip="{_html.escape(note, quote=True)}">{shown}</span></b>')


def _value(name, shown, changes):
    if name not in changes:
        return f'<b class="us-v">{shown}</b>'
    return changed_value("us-v", shown, *changes[name])


def _bar(cls, name, regen, nums, changes):
    regen_html = f'<span class="us-regen">+{nums[regen]}</span>' if float(nums[regen]) else ""
    return f'<span class="us-bar {cls}">{_value(name, nums[name], changes)}{regen_html}</span>'


def render(nums, changes=None, notes=None, tags="buff new"):
    """changes: {tile name: (old value as shown, the row's badge)}. notes: {tile name: the row's "?" text}."""
    from .elements import info_tip
    changes, notes = changes or {}, notes or {}
    unknown = (set(changes) | set(notes)) - set(nums)
    if unknown:
        raise ValueError(f"unit_sheet: no such tile: {sorted(unknown)}")
    if changes:          # the block answers the filters of what changed in it
        found = [w for _old, badge in changes.values() for w in re.findall(r'data-(?:overall|tag)="(\w+)"', badge)]
        tags = " ".join(dict.fromkeys(found))
    bars = _bar("us-hp", "Health", "Health Regen", nums, changes)
    if float(nums["Mana"]):
        bars += _bar("us-mp", "Mana", "Mana Regen", nums, changes)
    tiles = ""
    for name in TILES:
        tip = info_tip(notes[name]) if name in notes else ""
        tiles += (f'<span class="us-tile{_TILE_CLASS.get(name, "")}"><span class="us-k">{_html.escape(name)}{tip}</span>'
                  f'{_value(name, nums[name], changes)}</span>')
    # no tag chips (owner 2026-11-04): the numbers' colours say it; data-tag and the covered rows feed filters and cells
    return f'<li class="unit-sheet" data-tag="{tags}"><span class="us-bars">{bars}</span><span class="us-tiles">{tiles}</span></li>'


def unit_sheet(slug, changes=None, notes=None, version=None):
    """The sheet of npc_dota_neutral_<slug> (or a full npc_ name) in the current patch, a row of a W(ul_open()) list."""
    version = version or _State.current_patch_version
    text = game_files.read(version, _UNITS_FILE)
    if not text:
        raise ValueError(f"unit_sheet: no {_UNITS_FILE} for {version} in the game-files store")
    npc = slug if slug.startswith("npc_") else f"npc_dota_neutral_{slug}"
    return render(numbers(text, npc), changes, notes)
