"""Hero / item summons on Unit Stats (owner 2026-11-26: "добавить других summon units (не wards)").

Their numbers are the game's, not the plain unit KV: many summons take HP / damage / armor … from the summoning
ability's values (data/rules/summon_units.json, gathered 2026-11-26 from data/stats/7.42a: unit KV with
include_keys_from + the hero ability values; data/rules/summon_units.md says where each number came from).
Only entries marked sure are shown; an entry whose numbers the game works out from its hero (sure: false: Enigma's HP,
the hero's level) or a unit the game never summons (not_in_game) is left out. The Aghanim golem, Book of the Dead and
Raptor were confirmed by server.dll 6997 (2026-11-27). They do not grow with Upgrade.
A new patch: gather the file again for that patch."""
import json as _json
import os as _os
import re as _re

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
SUMMON_FILE = _os.path.join(_HERE, 'data', 'rules', 'summon_units.json')
ROW_PREFIX = 'summon_'
# the file's field -> the unit KV key the table's own reader (builders/creeps.py _unit_stats) understands
KV_FIELD = {'hp': 'StatusHealth', 'hp_regen': 'StatusHealthRegen', 'mana': 'StatusMana', 'armor': 'ArmorPhysical',
            'magres': 'MagicalResistance', 'dmg_min': 'AttackDamageMin', 'dmg_max': 'AttackDamageMax',
            'bat': 'AttackRate', 'as': 'BaseAttackSpeed', 'range': 'AttackRange', 'ms': 'MovementSpeed',
            'gold_min': 'BountyGoldMin', 'gold_max': 'BountyGoldMax', 'xp': 'BountyXP'}
ATTACK_CAP = {'melee': 'DOTA_UNIT_CAP_MELEE_ATTACK', 'ranged': 'DOTA_UNIT_CAP_RANGED_ATTACK'}
# the unit has no portrait of its own: one shared by its levels, else the summoning ability's icon (as Unit Changes)
_ICON_SHARED = {r'npc_dota_lycan_wolf\d': 'icons/units/npc_dota_lycan_wolf.png',
                r'npc_dota_visage_familiar\d': 'icons/units/npc_dota_visage_familiar.png',
                r'npc_dota_brewmaster_(earth|storm|fire|void)_\d': r'icons/units/brewmaster_\1_unit.png',
                r'npc_dota_unit_undying_zombie_torso': 'icons/units/npc_dota_unit_undying_zombie.png',
                r'npc_dota_beastmaster_thunderhide': 'icons/abilities/beastmaster_summon_thunderhide.png',
                r'npc_dota_wraith_king_skeleton_warrior': 'icons/abilities/skeleton_king_bone_guard.png',
                r'npc_dota_necronomicon_(warrior|archer)_\d': r'icons/units/npc_dota_necronomicon_\1.png'}


def entries(path=SUMMON_FILE):
    """The summons to show, in the file's order. A missing / empty file is an error, not an empty table."""
    with open(path, encoding='utf-8') as f:
        data = _json.load(f)
    if not data:
        raise ValueError(f'{path}: no summon units')
    # 2026-11-27: the Aghanim golem, Book of the Dead and Raptor confirmed by server.dll 6997 (summon_units.md)
    keep = [e for e in data
            if e.get('sure') and not e.get('not_in_game') and 'all' not in (e.get('unsure_fields') or [])
            and e.get('hp')]
    if not keep:
        raise ValueError(f'{path}: no summon marked sure')
    return keep


def kv_overrides(e):
    """The entry's numbers as unit KV keys (None = not known: the KV's own value stays)."""
    out = {KV_FIELD[k]: str(v) for k, v in e.items() if k in KV_FIELD and v is not None}
    if e.get('attack') in ATTACK_CAP:
        out['AttackCapabilities'] = ATTACK_CAP[e['attack']]
    return out


def display_name(e):
    # "Zombie (torso)" -> "Zombie Torso": one pair of brackets, the hero's
    base = _re.sub(r' \((\w+)\)', lambda m: ' ' + m.group(1).title(), e['name'])
    name = base + (f" {e['level']}" if e.get('level') else '')
    hero = e.get('hero') or ''
    return name if not hero or hero.split()[0] in name else f'{name} ({hero})'


def icon(e, exists=_os.path.exists):
    npc = e['npc']
    own = f'icons/units/{npc}.png'
    if exists(_os.path.join(_HERE, own)):
        return own
    for pat, src in _ICON_SHARED.items():
        if _re.fullmatch(pat, npc):
            return _re.sub(pat, src, npc)
    return f"icons/abilities/{e['ability']}.png"


_LOC_FILE = _os.path.join(_HERE, 'data', 'abilities_english.txt')
_LOC = None


def ability_name(slug):
    """The game's English name of a hero ability (abilities_english.txt), '' when it has none."""
    global _LOC
    if _LOC is None:
        _LOC = (open(_LOC_FILE, encoding='utf-8', errors='replace').read()
                if _os.path.exists(_LOC_FILE) else '')
    m = _re.search(r'"DOTA_Tooltip_ability_' + _re.escape(slug) + r'"\s+"([^"]*)"', _LOC, _re.I)
    return m.group(1) if m else ''


def abilities(npc, skip=()):
    """[(slug, name)] of the unit's own abilities, at most 3 (the table's columns): no hidden markers, no talents,
    nothing without a game name (owner 2026-11-26: "способность у суммонов отсутствуют")."""
    out = []
    for i in range(1, 6):
        slug = (npc.get(f'Ability{i}') or '').strip()
        if not slug or slug in skip or slug == 'generic_hidden' or slug.startswith('special_bonus_'):
            continue
        name = ability_name(slug)
        if name and '{' not in name:
            out.append((slug, name))
    return out[:3] + [('', '')] * (3 - len(out[:3]))


def head_names(path=SUMMON_FILE):
    """npc keys whose blocks the npc_units.txt reader must also keep (vision, projectile, hull …)."""
    return {e['npc'] for e in entries(path)}
