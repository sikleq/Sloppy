"""Hero / item summons on Unit Stats (owner 2026-11-26: "добавить других summon units (не wards)").

Their numbers are the game's, not the plain unit KV: many summons take HP / damage / armor … from the summoning
ability's values (data/rules/summon_units.json, gathered 2026-11-26 from data/stats/7.42a: unit KV with
include_keys_from + the hero ability values; data/rules/summon_units.md says where each number came from).
Only entries marked sure are shown; an entry whose numbers the game works out in code (sure: false) or the
Aghanim variants with guessed fields are left out until they are confirmed. They do not grow with Upgrade.
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
                r'npc_dota_wraith_king_skeleton_warrior': 'icons/abilities/skeleton_king_bone_guard.png'}


def entries(path=SUMMON_FILE):
    """The summons to show, in the file's order. A missing / empty file is an error, not an empty table."""
    with open(path, encoding='utf-8') as f:
        data = _json.load(f)
    if not data:
        raise ValueError(f'{path}: no summon units')
    keep = [e for e in data
            if e.get('sure') and 'scepter' not in e['key'] and 'all' not in (e.get('unsure_fields') or [])
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


def head_names(path=SUMMON_FILE):
    """npc keys whose blocks the npc_units.txt reader must also keep (vision, projectile, hull …)."""
    return {e['npc'] for e in entries(path)}
