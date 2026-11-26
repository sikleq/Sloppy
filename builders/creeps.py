"""build_creeps.py — generates units_stats.html (was neutral_stats.html), the unit stats
table. This is a standalone side-project, decoupled from the patch
changelog generator (builders/build_patches.py). Both share the site chrome via
site_common.py.

Data sources (read-only):
  data/creeps_raw.csv               — ordering, level, createhero names
  data/stats/<latest>/units.json       — base neutral stats
  data/stats/<latest>/npc_units.txt    — full KV (regen, bounty, vision, abilities)
  data/abilities_slim.json          — ability slug → display name
  data/site_meta.json               — latest patch href (written by builders/build_patches.py)
  icons/units/*.png                 — creep portraits

Run AFTER builders/build_patches.py (which writes data/site_meta.json). If the meta
file is missing the Changelogs nav link falls back to a sensible default.

This module is the entry point (save_creeps_html) and owns the unit data, the
row data and the Neutral Stats page. Helpers live next to it:
  builders/creeps_common.py    — value formatting, escaping, ability icons, page shell
  builders/creeps_history.py   — per-patch history behind the cell changelog tooltips
  builders/creeps_abilities.py — the Neutral Abilities companion page
NOTE: builders/entity_changes.py reads CREEP_NAME_TO_NPC, CREEP_DISPLAY_NAMES
and CREEP_CAMP straight from this file's source text — keep them here.
"""
import csv as _csv
import functools as _functools
import json as _json
import os as _os
import re
import sys as _sys
from dataclasses import dataclass
from typing import NamedTuple

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _HERE)

import patch.site_common as _site
from builders.creeps_abilities import UA_CANONICAL_UNIT, save_neutral_abilities_html
from builders.creeps_common import (
    ABILITY_COLS, ABILITY_SKIP, DASH, GROUP_SWITCHES, HULL_BOUNDS, NEUTRAL_DEFAULT_HULL, attr_esc,
    NEUTRAL_DEFAULT_TURN_RATE, abil_icon_html, ability_dname, armor_factor,
    ehp_mag_val, ehp_phys_val, esc, fmt_num, fmt_regen, has_abil_icon,
    page_shell, safe_float, safe_int, unit_group, write_dist,
)
from builders.creeps_history import (
    COL_CHANGELOG, COL_HIST, StatHistory, ability_changelog, load_history,
    value_history,
)

ASSET_VERSION = _site.compute_asset_version()


_latest_href = _site.latest_patch_href


# ---- Source files ----

NPC_FIELDS = ('StatusHealth', 'StatusHealthRegen', 'StatusMana',
              'StatusManaRegen', 'ArmorPhysical', 'MagicalResistance',
              'AttackDamageMin', 'AttackDamageMax', 'AttackRate',
              'BaseAttackSpeed', 'AttackRange', 'AttackCapabilities',
              'AttackAcquisitionRange', 'MovementSpeed',
              'AttackAnimationPoint', 'MovementTurnRate',
              'ProjectileSpeed', 'BoundsHullName', 'RingRadius',
              'BountyGoldMin', 'BountyGoldMax', 'BountyXP',
              'VisionDaytimeRange', 'VisionNighttimeRange',
              'Ability1', 'Ability2', 'Ability3', 'Ability4', 'Ability5')
# Capture both neutrals AND the hero-summoned units we surface
# in the table (e.g. Dark Troll Summoner's skeleton_warrior).
_NPC_HEAD_RE = re.compile(r'^\s*"(npc_dota_(?:neutral_[a-z0-9_]+|dark_troll_warlord_skeleton_warrior'
                          r'|creep_goodguys_(?:melee|ranged|flagbearer)(?:_upgraded(?:_mega)?)?'
                          r'|goodguys_siege(?:_upgraded(?:_mega)?)?))"\s*$')
_NPC_FIELD_RE = re.compile(r'^\s*"([A-Za-z_][A-Za-z0-9_]*)"\s+"([^"]+)"')


@dataclass(frozen=True)
class CreepSources:
    """The current patch's data files plus the per-patch history."""
    units: dict          # data/stats/<latest>/units.json
    npc_data: dict       # npc_units.txt → {npc key: {NPC_FIELDS field: raw value}}
    abil_slim: dict      # data/abilities_slim.json
    hist: StatHistory    # builders/creeps_history.py


def _parse_npc_kv(path):
    """Parse npc_units.txt for full stats per neutral: {npc key: {field: value}}
    for the NPC_FIELDS at each unit's own block level."""
    npc_data = {}
    if not _os.path.exists(path):
        return npc_data
    # Line-based parser with brace-depth tracking. Each top-level npc
    # block can contain deeply nested KV subblocks (AbilityValues,
    # CalculateSpellDamageTooltip etc.); plain regex can't balance
    # arbitrary depth.
    kv_lines = open(path, encoding='utf-8').read().splitlines()
    n_lines = len(kv_lines)
    i = 0
    while i < n_lines:
        m = _NPC_HEAD_RE.match(kv_lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        # Find the opening brace (typically next line)
        j = i + 1
        while j < n_lines and '{' not in kv_lines[j]:
            j += 1
        if j >= n_lines:
            break
        depth = kv_lines[j].count('{') - kv_lines[j].count('}')
        j += 1
        entry = {}
        while j < n_lines and depth > 0:
            line = kv_lines[j]
            # Capture field only when we're at the npc's own depth
            # (depth==1 means inside the npc block but outside any
            # nested AbilityValues / similar subblock).
            if depth == 1:
                fm = _NPC_FIELD_RE.match(line)
                if fm and fm.group(1) in NPC_FIELDS:
                    entry[fm.group(1)] = fm.group(2)
            depth += line.count('{') - line.count('}')
            j += 1
        npc_data[name] = entry
        i = j
    return npc_data


def load_sources():
    from patch.meta import latest_stats_version as _lsv
    ver = _lsv()
    units_path = _os.path.join(_HERE, 'data', 'stats', ver, 'units.json')
    npc_kv_path = _os.path.join(_HERE, 'data', 'stats', ver, 'npc_units.txt')
    abil_slim_path = _os.path.join(_HERE, 'data', 'abilities_slim.json')
    units = _json.loads(open(units_path, encoding='utf-8').read()) \
        if _os.path.exists(units_path) else {}
    abil_slim = _json.loads(open(abil_slim_path, encoding='utf-8').read()) \
        if _os.path.exists(abil_slim_path) else {}
    return CreepSources(units=units, npc_data=_parse_npc_kv(npc_kv_path),
                        abil_slim=abil_slim, hist=load_history())


# ---- Mappings ----
# createhero name (CSV col 3) → npc_dota_neutral_* key. None = no
# overlay (lane creeps or unknown summons).
CREEP_NAME_TO_NPC = {
    # Verified against the CSV's exact createhero shortcuts.
    'wildkin':            'npc_dota_neutral_wildkin',
    'kobold':             'npc_dota_neutral_kobold',
    'tunneler':           'npc_dota_neutral_kobold_tunneler',
    'taskmaster':         'npc_dota_neutral_kobold_taskmaster',
    'berserker':          'npc_dota_neutral_forest_troll_berserker',
    'priest':             'npc_dota_neutral_forest_troll_high_priest',
    'gnoll':              'npc_dota_neutral_gnoll_assassin',
    'fel':                'npc_dota_neutral_fel_beast',
    'harpy':              'npc_dota_neutral_harpy_scout',
    'harpy_storm':        'npc_dota_neutral_harpy_storm',
    'mauler':             'npc_dota_neutral_ogre_mauler',
    'neutral_ogre_magi':  'npc_dota_neutral_ogre_magi',
    'ghost':              'npc_dota_neutral_ghost',
    'trickster':          'npc_dota_neutral_satyr_trickster',
    'soulstealer':        'npc_dota_neutral_satyr_soulstealer',
    'hellcaller':         'npc_dota_neutral_satyr_hellcaller',
    'outrunner':          'npc_dota_neutral_centaur_outrunner',
    'khan':               'npc_dota_neutral_centaur_khan',
    'tad':                'npc_dota_neutral_tadpole',
    'wolf':               'npc_dota_neutral_giant_wolf',
    'alpha':              'npc_dota_neutral_alpha_wolf',
    'frog':               'npc_dota_neutral_froglet',
    'froglet_mage':       'npc_dota_neutral_froglet_mage',
    'grown_frog':         'npc_dota_neutral_grown_frog',
    'grown_frog_mage':    'npc_dota_neutral_grown_frog_mage',
    'ancient_frog':       'npc_dota_neutral_ancient_frog',
    'ancient_frog_mage':  'npc_dota_neutral_ancient_frog_mage',
    'mud':                'npc_dota_neutral_mud_golem',
    'dark_troll':         'npc_dota_neutral_dark_troll',
    'dark_troll_warlord': 'npc_dota_neutral_dark_troll_warlord',
    'pine':               'npc_dota_neutral_warpine_raider',
    'warrior':            'npc_dota_neutral_polar_furbolg_ursa_warrior',
    'champion':           'npc_dota_neutral_polar_furbolg_champion',
    'prowler_acolyte':    'npc_dota_neutral_prowler_acolyte',
    'prowler_shaman':     'npc_dota_neutral_prowler_shaman',
    'frost':              'npc_dota_neutral_frostbitten_golem',
    'rock':               'npc_dota_neutral_rock_golem',
    'enraged':            'npc_dota_neutral_enraged_wildkin',
    'lizard':             'npc_dota_neutral_big_thunder_lizard',
    'small_thunder_lizard': 'npc_dota_neutral_small_thunder_lizard',
    'ice':                'npc_dota_neutral_ice_shaman',
    'granite':            'npc_dota_neutral_granite_golem',
    'drake':              'npc_dota_neutral_black_drake',
    'black_dragon':       'npc_dota_neutral_black_dragon',
    # 7.42 camps: Radigull (Radiant medium), Odobenus (Dire medium), Eimermole (Radiant large), Ancient Ogre Seal
    'radigull':           'npc_dota_neutral_radigull',
    'odobenus_footman':   'npc_dota_neutral_odobenus_footman',
    'odobenus_frostmage': 'npc_dota_neutral_odobenus_frostmage',
    'eimermole':          'npc_dota_neutral_eimermole',
    'eimermole_foreman':  'npc_dota_neutral_eimermole_foreman',
    'ogre_seal':          'npc_dota_neutral_ogre_seal',
    'ogre_seal_pup':      'npc_dota_neutral_ogre_seal_pup',
    # Hero-summoned unit surfaced in the table — Dark Troll
    # Summoner's skeleton (data lives in the npc_dota_dark_troll_
    # warlord_skeleton_warrior block, captured by the broadened
    # _NPC_HEAD_RE above).
    'skeleton_warrior':   'npc_dota_dark_troll_warlord_skeleton_warrior',
}

# CSV rows that should be HIDDEN from the table entirely (lane creeps
# belong to a different section that will be added later).
HIDDEN_CREATEHERO = {'flag / melee', 'ranged'}

# Neutral units of npc_units.txt that spawn in no camp (splits / units no camp
# uses). tests/test_roster_guards.py fails for any OTHER neutral the latest
# game files carry that CREEP_NAME_TO_NPC (and so the table) does not know.
NOT_CAMP_UNITS = {
    'npc_dota_neutral_mud_golem_split',       # Mud Golem's splinters
    'npc_dota_neutral_mud_golem_split_doom',  # the same, for a Doom-devoured golem
    'npc_dota_neutral_jungle_stalker',        # in the files, in no camp
    'npc_dota_neutral_elder_jungle_stalker',
    # 7.42: "_gold" copies with the hidden ability neutral_gold_upgrade_ability; no patch note, no camp of their own
    'npc_dota_neutral_alpha_wolf_gold',
    'npc_dota_neutral_enraged_wildkin_gold',
    'npc_dota_neutral_gnoll_assassin_gold',
    'npc_dota_neutral_kobold_tunneler_gold',
    'npc_dota_neutral_mud_golem_gold',
    'npc_dota_neutral_polar_furbolg_champion_gold',
}

# Full display name (Russian/English) shown in the new Крип column.
CREEP_DISPLAY_NAMES = {
    'npc_dota_neutral_wildkin':              'Wildwing',
    'npc_dota_neutral_kobold':               'Kobold',
    'npc_dota_neutral_kobold_tunneler':      'Kobold Soldier',
    'npc_dota_neutral_kobold_taskmaster':    'Kobold Foreman',
    'npc_dota_neutral_forest_troll_berserker':   'Hill Troll Berserker',
    'npc_dota_neutral_forest_troll_high_priest': 'Hill Troll Priest',
    'npc_dota_neutral_gnoll_assassin':       'Vhoul Assassin',
    'npc_dota_neutral_fel_beast':            'Fell Spirit',
    'npc_dota_neutral_harpy_scout':          'Harpy Scout',
    'npc_dota_neutral_harpy_storm':          'Harpy Stormcrafter',
    'npc_dota_neutral_ogre_mauler':          'Ogre Bruiser',
    'npc_dota_neutral_ogre_magi':            'Ogre Frostmage',
    'npc_dota_neutral_ghost':                'Ghost',
    'npc_dota_neutral_satyr_trickster':      'Satyr Banisher',
    'npc_dota_neutral_satyr_soulstealer':    'Satyr Mindstealer',
    'npc_dota_neutral_satyr_hellcaller':     'Satyr Tormenter',     # the game's name, as on the patch pages (10-25)
    'npc_dota_neutral_centaur_outrunner':    'Centaur Courser',
    'npc_dota_neutral_centaur_khan':         'Centaur Conqueror',
    'npc_dota_neutral_tadpole':              'Pollywog',
    'npc_dota_neutral_giant_wolf':           'Giant Wolf',
    'npc_dota_neutral_alpha_wolf':           'Alpha Wolf',
    'npc_dota_neutral_froglet':              'Boglet',
    'npc_dota_neutral_froglet_mage':         'Marshmage Apprentice',
    'npc_dota_neutral_grown_frog':           'Croaker',
    'npc_dota_neutral_grown_frog_mage':      'Marshmage',
    'npc_dota_neutral_ancient_frog':         'Ancient Croaker',
    'npc_dota_neutral_ancient_frog_mage':    'Ancient Marshmage',
    'npc_dota_neutral_mud_golem':            'Mud Golem',
    'npc_dota_neutral_mud_golem_split':      'Shard Golem',
    'npc_dota_neutral_dark_troll':           'Dark Troll Trapper',   # the game's name since 7.42 (Hill Troll before)
    'npc_dota_neutral_dark_troll_warlord':   'Dark Troll Summoner',
    'npc_dota_neutral_warpine_raider':       'Warpine Raider',
    # as in the game (dota_english): the ursa warrior (Thunder Clap, 950 HP) is the Smasher — was swapped until 2026-10-21
    'npc_dota_neutral_polar_furbolg_ursa_warrior': 'Hellbear Smasher',
    'npc_dota_neutral_polar_furbolg_champion':     'Hellbear',
    'npc_dota_neutral_prowler_acolyte':      'Ancient Prowler Acolyte',
    'npc_dota_neutral_prowler_shaman':       'Ancient Prowler Shaman',
    'npc_dota_neutral_frostbitten_golem':    'Ancient Frostbitten Golem',
    'npc_dota_neutral_rock_golem':           'Ancient Rock Golem',
    'npc_dota_neutral_enraged_wildkin':      'Wildwing Ripper',
    'npc_dota_neutral_big_thunder_lizard':   'Ancient Thunderhide',
    'npc_dota_neutral_small_thunder_lizard': 'Ancient Rumblehide',
    'npc_dota_neutral_jungle_stalker':       'Ancient Stalker',
    'npc_dota_neutral_elder_jungle_stalker': 'Ancient Primal Stalker',
    'npc_dota_neutral_ice_shaman':           'Ancient Ice Shaman',
    'npc_dota_neutral_granite_golem':        'Ancient Granite Golem',
    'npc_dota_neutral_black_drake':          'Ancient Black Drake',
    'npc_dota_neutral_black_dragon':         'Ancient Black Dragon',
    'npc_dota_neutral_radigull':             'Radigull',                # 7.42
    'npc_dota_neutral_odobenus_footman':     'Odobenus Footman',        # 7.42
    'npc_dota_neutral_odobenus_frostmage':   'Odobenus Frostmage',      # 7.42
    'npc_dota_neutral_eimermole':            'Eimermole',               # 7.42
    'npc_dota_neutral_eimermole_foreman':    'Eimermole Foreman',       # 7.42
    'npc_dota_neutral_ogre_seal':            'Ancient Ogre Seal',       # 7.42
    'npc_dota_neutral_ogre_seal_pup':        'Ancient Ogre Seal Pup',   # 7.42
    # Hero-summoned units shown alongside neutrals
    'npc_dota_dark_troll_warlord_skeleton_warrior': 'Skeleton Warrior',
}

# Camp type(s) per neutral (small / mid / big / ancient) — the in-game
# minimap camp marker. Not present in npc_units.txt (it lives in the map's
# spawn data), so this mapping is maintained by hand. Keyed by the
# createhero shortname (same token as the "-createhero <name>" column).
# A creep that spawns in two camp sizes lists both → both icons render.
# (User roster terms: medium→mid, large/hard→big.)
CREEP_CAMP = {
    'wildkin':              ['big'],
    'kobold':               ['small'],
    'tunneler':             ['small'],
    'skeleton_warrior':     ['big'],
    'berserker':            ['small'],
    'gnoll':                ['small'],
    'fel':                  ['small'],
    'harpy':                ['small'],
    'mauler':               ['mid'],
    'taskmaster':           ['small'],
    'priest':               ['small'],
    'outrunner':            ['big'],          # 7.42 "Medium Centaur camp removed"
    'tad':                  ['small'],
    'trickster':            ['mid'],          # 7.42: the Large Satyr camp's Banisher -> a second Mindstealer
    'wolf':                 ['mid'],
    'dark_troll':           ['big'],
    'ghost':                ['small'],
    'harpy_storm':          ['small'],
    'drake':                ['ancient'],
    'prowler_acolyte':      ['ancient'],
    'neutral_ogre_magi':    ['mid'],
    'mud':                  ['mid'],
    'frog':                 ['mid'],
    'grown_frog':           ['big'],
    'froglet_mage':         ['mid'],
    'grown_frog_mage':      ['big'],
    'champion':             ['big'],
    'soulstealer':          ['mid', 'big'],
    'alpha':                ['mid'],
    'khan':                 ['big'],          # 7.42 "Medium Centaur camp removed"
    'warrior':              ['big'],
    'enraged':              ['big'],
    'pine':                 ['big'],
    'ancient_frog':         ['ancient'],
    'rock':                 ['ancient'],
    'frost':                ['ancient'],
    'small_thunder_lizard': ['ancient'],
    'ancient_frog_mage':    ['ancient'],
    'hellcaller':           ['big'],
    'dark_troll_warlord':   ['big'],
    'prowler_shaman':       ['ancient'],
    'black_dragon':         ['ancient'],
    'granite':              ['ancient'],
    'lizard':               ['ancient'],
    'ice':                  ['ancient'],
    # 7.42 (patch notes "Neutral Creep Updates")
    'radigull':             ['mid'],
    'odobenus_footman':     ['mid'],
    'odobenus_frostmage':   ['mid'],
    'eimermole':            ['big'],
    'eimermole_foreman':    ['big'],
    'ogre_seal':            ['ancient'],
    'ogre_seal_pup':        ['ancient'],
}
# Creeps whose camp left the game (createhero -> the patch). Their rows stay, hidden until the toolbar's
# "Removed" button shows them (owner 2026-11-18: «убрать, но добавить переключатель»). 7.42: "Large Warpine
# Raider camp removed", "Ancient Thunderhide camp removed".
REMOVED_CREEPS = {'pine': '7.42', 'lizard': '7.42', 'small_thunder_lizard': '7.42'}
# A camp a creep was in until a patch (createhero -> {camp: patch}): the camp tables of server.dll 6976 (the last
# build before 7.42, RVA 0x4A85D70) against 6984 (7.42, RVA 0x4C2E270). Shown in the camp cell's hover with the
# creep's first patch (data/rules/creep_since.json, scripts/gen/gen_creep_since.py) — owner 2026-11-19: "при
# наведении на ячейку camp состояние крипа - в каком лагере был и когда был введен/удален".
CAMP_UNTIL = {
    'outrunner': {'mid': '7.42'}, 'khan': {'mid': '7.42'},            # Medium Centaur camp removed
    'trickster': {'big': '7.42'},                                     # the Large Satyr camp's Banisher -> Mindstealer
    'pine': {'big': '7.42'}, 'lizard': {'ancient': '7.42'}, 'small_thunder_lizard': {'ancient': '7.42'},
}


@_functools.lru_cache(maxsize=1)
def _creep_since() -> dict:
    """npc_dota_neutral_* -> the first patch it is in the game files (only those after 7.08, the store's start)"""
    with open(_os.path.join(_HERE, 'data', 'rules', 'creep_since.json'), encoding='utf-8') as f:
        return _json.load(f)
CAMP_LABEL = {'small': 'Small camp', 'mid': 'Medium camp',
              'big': 'Large camp', 'ancient': 'Ancient camp'}

# Auras that buff the caster's OWN stats — the creep benefits from its own
# aura, so the displayed stat shows "base (with-aura)". Keyed by createhero
# shortname: stat -> (op, ability, AbilityValues key). The NUMBER is the
# level-1 value read from the latest npc_abilities.json (av_<key>), so a
# balance change reaches the table by itself. op '+' = additive flat,
# '%' = multiplicative percent (+12 -> x1.12). 'dmg' covers min/max/avg.
AURA_SELF = {
    'hellcaller':           {'hp_regen': ('+', 'satyr_hellcaller_unholy_aura', 'health_regen')},
    'skeleton_warrior':     {'dmg': ('+', 'hill_troll_rally', 'damage_bonus')},
    'taskmaster':           {'ms': ('%', 'kobold_taskmaster_speed_aura', 'bonus_movement_speed')},
    'soulstealer':          {'mp_regen': ('+', 'forest_troll_high_priest_mana_aura', 'mana_regen')},
    'outrunner':            {'magres': ('+', 'mudgolem_cloak_aura', 'bonus_magical_armor_creeps')},
    'prowler_acolyte':      {'hp_regen': ('+', 'spawnlord_aura', 'hp_regen')},
    'alpha':                {'dmg': ('%', 'alpha_wolf_command_aura', 'bonus_damage_pct')},
    'enraged':              {'armor': ('+', 'enraged_wildkin_toughness_aura', 'bonus_armor')},
    'small_thunder_lizard': {'as': ('+', 'big_thunder_lizard_wardrums_aura', 'speed_bonus')},
    'black_dragon':         {'armor': ('+', 'black_dragon_dragonhide_aura', 'bonus_armor')},
    'granite':              {'hp': ('%', 'granite_golem_hp_aura', 'bonus_hp')},
}


@_functools.lru_cache(maxsize=1)
def _game_unit_names() -> dict:
    """{npc_dota_* : name} from the game's localization (abilities_english.txt)."""
    path = _os.path.join(_HERE, 'data', 'abilities_english.txt')
    out = {}
    if _os.path.exists(path):
        text = open(path, encoding='utf-8', errors='replace').read()
        for k, v in re.findall(r'^\s*"(npc_dota_[a-z0-9_]+)"\s+"([^"]*)"', text, re.M):
            out.setdefault(k, v)
    return out


def game_unit_name(npc_key: str) -> str:
    """A creep CREEP_DISPLAY_NAMES does not list: the game's own name, so a
    new neutral never shows a made-up title-cased slug."""
    return (_game_unit_names().get(npc_key)
            or npc_key.replace('npc_dota_neutral_', '').replace('_', ' ').title())


@_functools.lru_cache(maxsize=1)
def _latest_abilities() -> dict:
    from patch.meta import latest_stats_version as _lsv
    path = _os.path.join(_HERE, 'data', 'stats', _lsv(), 'npc_abilities.json')
    return _json.loads(open(path, encoding='utf-8').read()) if _os.path.exists(path) else {}


def aura_self_value(op: str, ability: str, key: str):
    """(op, value) for _aura_total from the game files: '+' flat level-1
    value, '%' -> ('*', 1 + pct/100). None when the ability / key is gone
    (tests/test_roster_guards.py fails then)."""
    raw = (_latest_abilities().get(ability) or {}).get('av_' + key)
    if raw is None:
        return None
    val = float(str(raw).split()[0])
    return ('*', 1 + val / 100) if op == '%' else ('+', val)


# ---- Row data ----

class UnitStats(NamedTuple):
    """One creep's current numbers — npc_units.txt first, units.json for the
    basic fields — plus the derived ones."""
    hp: int
    hp_regen: float
    mp: int
    mp_regen: float
    armor: float
    armor_pct: str       # '' when the unit has no armor data
    ehp_phys: int
    magres: float
    ehp_mag: int
    dmg_min: int
    dmg_max: int
    dmg_avg: int
    bat: float
    ats: int
    t_per_attack: float
    ms: int
    gold_min: int
    gold_max: int
    gold_avg: int
    xp: int
    ap: float
    turn_rate: float
    projectile: int
    collision: object    # int, or None without a unit
    bound_radius: object


def _attack_type(npc):
    """Ranged attack capability → "Piercing", else "Default"."""
    cap = npc.get('AttackCapabilities', '')
    return 'Piercing' if 'RANGED' in cap else 'Default'


def _attack_range_label(npc):
    # Just the number — no "Ближняя", no parentheses. The melee/ranged
    # marker is rendered separately as a glass icon badge in the cell.
    rng = safe_int(npc.get('AttackRange'), 0)
    return fmt_num(rng) if rng else ''


def _is_ranged(npc):
    return 'RANGED' in npc.get('AttackCapabilities', '')


def _hull_for(npc):
    return (npc.get('BoundsHullName') or NEUTRAL_DEFAULT_HULL) if npc else None


def _hull_collision(npc):
    h = _hull_for(npc)
    return HULL_BOUNDS.get(h, (None, None))[0] if h else None


def _hull_bound(npc):
    h = _hull_for(npc)
    return HULL_BOUNDS.get(h, (None, None))[1] if h else None


def _unit_stats(npc, u):
    # Prefer npc_units.txt; fall back to units.json for the basic fields.
    hp = safe_int(npc.get('StatusHealth') or u.get('StatusHealth'))
    armor = safe_float(npc.get('ArmorPhysical')
                       if 'ArmorPhysical' in npc
                       else u.get('ArmorPhysical', 0))
    magres = safe_float(npc.get('MagicalResistance'), 0)  # default 0
    dmg_min = safe_int(npc.get('AttackDamageMin') or u.get('AttackDamageMin'))
    dmg_max = safe_int(npc.get('AttackDamageMax') or u.get('AttackDamageMax'))
    bat = safe_float(npc.get('AttackRate') or u.get('AttackRate'))
    ats = safe_int(npc.get('BaseAttackSpeed'), 100)
    gold_min = safe_int(npc.get('BountyGoldMin'))
    gold_max = safe_int(npc.get('BountyGoldMax'))
    tr = npc.get('MovementTurnRate')
    # Damage Factor formula: (0.06 × armor) / (1 + 0.06 × |armor|).
    # Positive armor reduces incoming damage; user wants absorption %.
    if armor != 0 or 'ArmorPhysical' in npc:
        armor_pct = f'{round(armor_factor(armor) * 100)}%'
        ehp_phys = ehp_phys_val(hp, armor)
    else:
        armor_pct, ehp_phys = '', 0
    return UnitStats(
        hp=hp,
        hp_regen=safe_float(npc.get('StatusHealthRegen')),
        mp=safe_int(npc.get('StatusMana') or u.get('StatusMana') or 0),
        mp_regen=safe_float(npc.get('StatusManaRegen')),
        armor=armor, armor_pct=armor_pct, ehp_phys=ehp_phys,
        magres=magres, ehp_mag=ehp_mag_val(hp, magres),
        dmg_min=dmg_min, dmg_max=dmg_max,
        # Average damage rounded UP (12.5 → 13).
        dmg_avg=-(-(dmg_min + dmg_max) // 2) if (dmg_min or dmg_max) else 0,
        bat=bat, ats=ats,
        t_per_attack=bat * 100 / ats if ats else bat,
        ms=safe_int(npc.get('MovementSpeed') or u.get('MovementSpeed')),
        gold_min=gold_min, gold_max=gold_max,
        # Average gold rounded UP (45.5 → 46).
        gold_avg=-(-(gold_min + gold_max) // 2) if gold_min or gold_max else 0,
        xp=safe_int(npc.get('BountyXP')),
        ap=safe_float(npc.get('AttackAnimationPoint')),
        turn_rate=(safe_float(tr) if tr is not None
                   else (NEUTRAL_DEFAULT_TURN_RATE if npc else 0)),
        projectile=safe_int(npc.get('ProjectileSpeed')),
        collision=_hull_collision(npc),
        bound_radius=_hull_bound(npc),
    )


def _row_abilities(npc, abil_slim):
    """Abilities as (slug, dname) pairs (skip hidden markers/blanks), padded
    to the 3 ability columns."""
    abilities = []
    for i in range(1, 6):
        slug = npc.get(f'Ability{i}', '').strip()
        if not slug or slug in ABILITY_SKIP:
            continue
        abilities.append((slug, ability_dname(slug, abil_slim)))
    # Riverborn Aura is shared by every frog unit — pin it to the first
    # ability slot so the aura lines up in ONE column across all frogmen
    # (consistent column-highlight / sort). Their unique ability shifts to
    # slot 2. Stable sort keeps the rest of the order intact.
    abilities.sort(key=lambda sd: 0 if sd[0] == 'frogmen_riverborn_aura' else 1)
    abilities += [('', '')] * (3 - len(abilities)) if len(abilities) < 3 else []
    return abilities


def _format_stats(s, npc, abilities, createhero):
    """Display strings keyed by column id; missing keys render as blank."""
    vis_day = npc.get('VisionDaytimeRange', '')
    vis_night = npc.get('VisionNighttimeRange', '')
    return {
        'hp':            fmt_num(s.hp) if s.hp else '',
        # Resolved creeps always show a regen value; "0" when the KV
        # has no StatusHealthRegen (e.g. Skeleton Warrior) instead of
        # a blank cell.
        'hp_regen':      (fmt_regen(s.hp_regen) if s.hp_regen
                          else ('0' if npc else '')),
        'mp':            fmt_num(s.mp) if s.mp else '-',
        # No mana → "-" (matches MP); mana but no regen → "0".
        'mp_regen':      (fmt_regen(s.mp_regen) if s.mp_regen
                          else ('-' if (npc and not s.mp) else ('0' if npc else ''))),
        'armor':         fmt_num(s.armor) if s.armor or 'ArmorPhysical' in npc else '',
        'armor_pct':     s.armor_pct,
        'ehp_phys':      fmt_num(s.ehp_phys) if s.ehp_phys else '',
        'magres':        f'{int(s.magres)}%',
        'ehp_mag':       fmt_num(s.ehp_mag) if s.ehp_mag else '',
        'dmg_min':       fmt_num(s.dmg_min) if s.dmg_min else '',
        'dmg_max':       fmt_num(s.dmg_max) if s.dmg_max else '',
        'dmg_avg':       fmt_num(s.dmg_avg) if s.dmg_avg else '',
        'as':            fmt_num(s.ats) if s.ats and npc else '',
        't_per_attack':  fmt_num(round(s.t_per_attack, 2)) if s.t_per_attack else '',
        'bat':           fmt_num(s.bat) if s.bat else '',
        'ms':            fmt_num(s.ms) if s.ms else '',
        # Золото = average; min/max kept (hidden) for the extended toggle.
        'gold':          fmt_num(s.gold_avg) if s.gold_avg else '',
        'gold_min':      fmt_num(s.gold_min) if s.gold_min else '',
        'gold_max':      fmt_num(s.gold_max) if s.gold_max else '',
        'xp':            fmt_num(s.xp) if s.xp else '',
        'attack_range':  _attack_range_label(npc),
        'attack_range_ranged': _is_ranged(npc) if npc else False,
        'attack_type':   _attack_type(npc) if npc else '',
        'vision':        f'{vis_day}/{vis_night}' if vis_day and vis_night else '',
        'aggro':         npc.get('AttackAcquisitionRange', ''),
        'ap':            fmt_num(s.ap) if s.ap else '',
        'turn_rate':     fmt_num(s.turn_rate) if s.turn_rate else '',
        'collision_size': fmt_num(s.collision) if s.collision else '',
        'bound_radius':  fmt_num(s.bound_radius) if s.bound_radius else '',
        # Melee units have ProjectileSpeed 0 → show a dash, not blank.
        'projectile':    fmt_num(s.projectile) if s.projectile else ('-' if npc else ''),
        'ability1':      abilities[0][1], 'ability1_slug': abilities[0][0],
        'ability2':      abilities[1][1], 'ability2_slug': abilities[1][0],
        'ability3':      abilities[2][1], 'ability3_slug': abilities[2][0],
        'camp':          ','.join(CREEP_CAMP.get((createhero or '').strip(), [])),
    }


def _aura_total(base, op, val):
    return base + val if op == '+' else round(base * val)


def _with_self_aura(result, s, createhero):
    """Self-affecting auras: show "base (with-aura)" on the buffed stat."""
    aura = AURA_SELF.get((createhero or '').strip())
    if not aura:
        return result
    out = dict(result)
    for stat, spec in aura.items():
        resolved = aura_self_value(*spec)
        if resolved is None:
            print(f"  ! creeps: aura {spec[1]}.{spec[2]} not in the latest npc_abilities.json — skipped")
            continue
        op, val = resolved
        if stat == 'dmg':
            for dk, dv in (('dmg_min', s.dmg_min), ('dmg_max', s.dmg_max),
                           ('dmg_avg', s.dmg_avg)):
                if dv:
                    out[dk] = f'{fmt_num(dv)} ({fmt_num(_aura_total(dv, op, val))})'
        elif stat == 'hp_regen' and s.hp_regen:
            out['hp_regen'] = f'{fmt_regen(s.hp_regen)} ({fmt_regen(_aura_total(s.hp_regen, op, val))})'
        elif stat == 'mp_regen' and s.mp_regen:
            out['mp_regen'] = f'{fmt_regen(s.mp_regen)} ({fmt_regen(_aura_total(s.mp_regen, op, val))})'
        elif stat == 'magres':
            out['magres'] = f'{int(s.magres)}% ({int(_aura_total(s.magres, op, val))}%)'
        elif stat == 'armor':
            out['armor'] = f'{fmt_num(s.armor)} ({fmt_num(_aura_total(s.armor, op, val))})'
        elif stat == 'as' and s.ats:
            out['as'] = f'{fmt_num(s.ats)} ({fmt_num(_aura_total(s.ats, op, val))})'
        elif stat == 'ms' and s.ms:
            out['ms'] = f'{fmt_num(s.ms)} ({fmt_num(_aura_total(s.ms, op, val))})'
        elif stat == 'hp' and s.hp:
            out['hp'] = f'{fmt_num(s.hp)} ({fmt_num(_aura_total(s.hp, op, val))})'
    return out


def _row_data(npc_key, createhero, src):
    """Compute the full set of overlay values for one creep. Returns
    a dict keyed by column id; missing keys render as blank."""
    npc = src.npc_data.get(npc_key, {}) if npc_key else {}
    u = src.units.get(npc_key, {}) if npc_key else {}
    s = _unit_stats(npc, u)
    result = _format_stats(s, npc, _row_abilities(npc, src.abil_slim), createhero)
    return _with_self_aura(result, s, createhero)


def _resolve(createhero, units):
    n = (createhero or '').strip()
    if not n:
        return None
    if n in CREEP_NAME_TO_NPC:
        return CREEP_NAME_TO_NPC[n]
    # Try direct prefix
    direct = f'npc_dota_neutral_{n}'
    if direct in units:
        return direct
    return None


def _csv_attack_idx(header):
    # CSV column index of "Тип атаки" — the curated attack type. The game
    # files don't expose CombatClassAttack for neutrals, so the CSV is the
    # authoritative source (ranged ≠ Pierce reliably, e.g. Dark Troll
    # Summoner is ranged but deals "Обычный").
    try:
        return next(i for i, h in enumerate(header) if 'Тип атаки' in h)
    except StopIteration:
        return None


def _creep_data(createhero, level, padded, atk_idx, src):
    """(npc key, row data) for one visible CSV row."""
    npc_key = _resolve(createhero, src.units)
    if npc_key:
        # site names first (CREEP_DISPLAY_NAMES), else the game's own unit name
        display_name = CREEP_DISPLAY_NAMES.get(npc_key) or game_unit_name(npc_key)
        icon_path = f'icons/units/{npc_key}.png'
    else:
        display_name = createhero.replace('_', ' ').title()
        icon_path = None
    data = {
        **_row_data(npc_key, createhero, src),
        'lvl': level,  # always set; rowspan handles merging
        'createhero': createhero,
        'name': display_name,
        'npc_key': npc_key,      # for the Unit Changes name link
        'icon': icon_path,
    }
    # Override the heuristic attack type with the curated CSV value
    # (strip trailing */** footnote markers). Falls back to the
    # heuristic when the CSV cell is blank.
    if atk_idx is not None and atk_idx < len(padded):
        csv_atk = padded[atk_idx].strip().rstrip('*').strip()
        csv_atk = {'Обычный': 'Default',
                   'Проникающий': 'Piercing'}.get(csv_atk, csv_atk)
        if csv_atk:
            data['attack_type'] = csv_atk
    return npc_key, data


def build_rows(csv_rows, src):
    """One entry per visible creeps_raw.csv row, in CSV order:
    {'data': row data, 'tier_break': bool, 'level': str, 'npc_key': str|None}.
    Both pages render from this list."""
    rendered = []
    current_lvl = ''
    csv_level_pointer = ''  # tracks the latest Ур. seen, INCLUDING on
    # rows we later skip (a hidden row can carry
    # a level marker that the next non-hidden
    # row inherits — e.g. the 'ranged' lane
    # creep sits on row '5', so we must record
    # level 5 even though we drop the row).
    atk_idx = _csv_attack_idx(csv_rows[0])
    for r in csv_rows[1:]:
        padded = r + [''] * (max(0, 28 - len(r)))
        csv_lvl = padded[1].strip()
        createhero = padded[3].strip()
        if csv_lvl:
            csv_level_pointer = csv_lvl
        # Skip legend rows (start with "ТИР" in col 2) and fully-blank rows
        col_c_text = padded[2].strip()
        if col_c_text.startswith('ТИР') or col_c_text.startswith('Тир крипов'):
            continue
        if not createhero and not csv_lvl:
            continue
        # Skip hidden lane-creep rows (the user wants them in a separate
        # section that will be added later). Level pointer already updated
        # above so the next non-hidden row inherits correctly.
        if createhero in HIDDEN_CREATEHERO:
            continue
        level_for_row = csv_level_pointer
        npc_key, data = _creep_data(createhero, level_for_row, padded, atk_idx, src)
        is_break = (level_for_row != current_lvl)
        current_lvl = level_for_row
        rendered.append({'data': data, 'tier_break': is_break,
                         'level': level_for_row, 'npc_key': npc_key})
    # No rowspan merge: every row carries its own level cell so the table
    # can be re-sorted by any column. scripts.js collapses repeated level
    # numbers in the current row order (showing the number once per run +
    # a divider) to keep the grouped look in the default/level-sorted view.
    return rendered + lane_rows(src)


# ---- Lane creeps (owner 2026-11-26: "добавить lane melee, ranged, siege, flagbearer") ----
# Radiant's units: Dire's carry the same numbers in every patch (npc_units.txt). Row token -> npc key, name.
LANE_CREEPS = (
    ('lane_melee',      'npc_dota_creep_goodguys_melee',      'Melee Creep'),
    ('lane_ranged',     'npc_dota_creep_goodguys_ranged',     'Ranged Creep'),
    ('lane_siege',      'npc_dota_goodguys_siege',            'Siege Creep'),
    ('lane_flagbearer', 'npc_dota_creep_goodguys_flagbearer', 'Flagbearer Creep'),
)
LANE_ATTACK_TYPE = {'lane_siege': 'Siege'}
# Normal / Super / Mega (owner 2026-11-26: "у lane creeps есть статус super/mega … добавить выбор в тулбаре"): the
# game spawns <unit>_upgraded once the enemy barracks of that lane fall, <unit>_upgraded_mega when all six are down.
# One row per variant; the toolbar's choice (#lane-tier, src/js/creeps-pinned.js) shows one set of four.
LANE_TIERS = (('normal', '', ''), ('super', '_upgraded', 'Super '), ('mega', '_upgraded_mega', 'Mega '))


def lane_rows(src):
    """The lane creep rows, after the neutrals, in the same row format as build_rows: each creep in its Normal, Super
    and Mega unit (row token lane_<creep>, lane_<creep>_super, lane_<creep>_mega)."""
    out = []
    for tier, suffix, prefix in LANE_TIERS:
        for i, (token, base_npc, name) in enumerate(LANE_CREEPS):
            npc_key = base_npc + suffix
            row_token = token if tier == 'normal' else f'{token}_{tier}'
            data = {**_row_data(npc_key, row_token, src), 'lvl': '', 'createhero': row_token,
                    'name': prefix + name, 'npc_key': npc_key, 'lane_tier': tier,
                    # the variants wear the base unit's portrait; no camp: a dash
                    'icon': f'icons/units/{base_npc}.png', 'camp': ''}
            if token in LANE_ATTACK_TYPE:
                data['attack_type'] = LANE_ATTACK_TYPE[token]
            out.append({'data': data, 'tier_break': i == 0, 'level': '', 'npc_key': npc_key})
    return out


# ---- Neutral Stats: column structure ----
# Super-categories → columns (key, label, mode). mode 'std' = visible in
# both Standard and Expanded; 'exp' = Expanded only. Render order follows
# this structure; the View toggle hides 'exp' columns in Standard mode.
CATEGORIES = [
    ('Basic', [
        ('lvl',          'Lvl',              'std'),
        ('icon',         'Copy',             'std'),
        ('name',         'Unit',             'std'),
        ('camp',         'Camp',             'std'),   # owner 2026-11-19: right after Unit
    ]),
    ('Vitality', [
        ('hp',           'HP',               'std'),
        ('hp_regen',     'HP/sec',           'std'),
        ('ehp_phys',     'EHP\nphys',        'exp'),
        ('ehp_mag',      'EHP\nmag',         'exp'),
        ('mp',           'MP',               'std'),
        ('mp_regen',     'MP/sec',           'std'),
        ('armor',        'Armor',            'std'),
        ('armor_pct',    'Armor %',          'exp'),
        ('magres',       'Mag. resist',      'std'),
    ]),
    ('Attack', [
        ('dmg_avg',      'Damage',           'std'),
        ('dmg_min',      'Dmg\nmin',         'exp'),
        ('dmg_max',      'Dmg\nmax',         'exp'),
        ('as',           'Speed',            'std'),
        ('t_per_attack', 'Attack Interval',  'std'),
        ('bat',          'BAT',              'std'),
        ('attack_range', 'Range',            'std'),
        ('attack_type',  'Type',             'std'),
        ('ap',           'Point',            'exp'),
        ('projectile',   'Projectile Speed', 'exp'),
    ]),
    ('Bounty', [
        ('gold',         'Gold',             'std'),
        ('gold_min',     'Gold\nmin',        'exp'),
        ('gold_max',     'Gold\nmax',        'exp'),
        ('xp',           'XP',               'std'),
    ]),
    ('Other', [
        ('ms',          'Movespeed',        'std'),
        ('vision',       'Vision',           'std'),
        ('aggro',        'Acquisition Range', 'exp'),
        ('turn_rate',    'Turn Rate',        'exp'),
        ('collision_size', 'Collision Size', 'exp'),
        ('bound_radius', 'Bound Radius',     'exp'),
    ]),
    ('Abilities', [
        ('ability1',     'Ability 1',        'std'),
        ('ability2',     'Ability 2',        'std'),
        ('ability3',     'Ability 3',        'std'),
    ]),
]
# View "Timeline" (owner 2026-11-26, a sheet of the owner's: every stat at each 7:30 upgrade step): beside the Basic
# columns, HP / Armor / Damage / Attack speed / Avg gold at 0:00, 7:30 … 60:00, worked out by the same upgrade rules
# as the Upgrade box (neutral_upgrade; a lane creep's LANE_UPGRADE). Shown only in that view (mode 'tl').
TL_STEPS = tuple(range(9))                     # 0:00 … 60:00
TL_STATS = (('hp', 'HP'), ('armor', 'Armor'), ('dmg', 'Damage'), ('as', 'Attack speed'), ('gold', 'Avg gold'))
_TL_SLUG = {label: f'tl-{key}' for key, label in TL_STATS}


def _tl_time(step):
    s = step * 450
    return f'{s // 60}:{s % 60:02d}'


CATEGORIES += [(label, [(f'tl_{key}_{i}', _tl_time(i), 'tl') for i in TL_STEPS]) for key, label in TL_STATS]
COLUMNS = [(k, label) for _cat, cols in CATEGORIES for (k, label, _m) in cols]
COL_MODE = {k: m for _cat, cols in CATEGORIES for (k, _l, m) in cols}
_CAT_SLUG = {'Basic': 'basic', 'Vitality': 'vitality', 'Attack': 'attack',
             'Bounty': 'bounty', 'Other': 'other', 'Abilities': 'abilities', **_TL_SLUG}
COL_CAT = {k: _CAT_SLUG[cat] for cat, cols in CATEGORIES for (k, _l, _m) in cols}
# No colgroup: table-layout: auto lets the browser size each column
# to fit content (and each header) on one line. Headers and cells
# are explicitly centred via CSS so the auto-width math doesn't have
# to budget for tag-width differences across columns.
# Columns that get a vertical separator on their RIGHT edge — they
# group the table into logical sections (identity | survivability |
# offense | economy | utility | abilities).
# Left-border on the first (always-visible) column of each super-category.
SEP_AFTER = {'hp', 'dmg_avg', 'gold', 'ms', 'ability1'}
# Identity columns pinned to the left edge during horizontal scroll
# (scripts.js computes their cumulative left offsets after layout).
STICKY_COLS = {'lvl', 'icon', 'name'}
CAMP_RANK = {'small': 1, 'mid': 2, 'big': 3, 'ancient': 4}


def _col_cls(k, value=''):
    cls = [f'col-{k}']
    if k in STICKY_COLS:
        cls.append('sticky-col')
    if k in SEP_AFTER:
        cls.append('col-sep')
    if COL_MODE.get(k) == 'exp':
        cls.append('col-exp')          # hidden in Standard view
    if COL_MODE.get(k) == 'tl':
        cls.append('col-tl')           # only in the Timeline view
        if k.endswith('_0'):
            cls.append('col-sep')
    elif COL_CAT.get(k) != 'basic':
        cls.append('col-main')         # hidden in the Timeline view
    if k == 'attack_type':
        if value == 'Default':
            cls.append('atk-basic')
        elif value == 'Piercing':
            cls.append('atk-pierce')
    if k in ('hp_regen', 'mp_regen') and value == '0':
        cls.append('regen-zero')
    return ' '.join(cls)


def _sort_attr(k, value):
    if k == 'camp' and value:
        # Use the lowest rank present (single-camp creeps are common;
        # multi-camp creeps get ranked by their primary/smallest camp).
        ranks = [CAMP_RANK[t] for t in str(value).split(',') if t in CAMP_RANK]
        if ranks:
            return f' data-sort="{min(ranks)}"'
        return ''
    if k not in ('hp_regen', 'mp_regen') or value in ('', '-'):
        return ''
    first = str(value).split(' ', 1)[0].replace(',', '.')
    try:
        return f' data-sort="{float(first):g}"'
    except ValueError:
        return ''


def _label_html(label):
    """Header label HTML. A '\\n' splits it into a main line + a small
    sub-line below (used by EHP columns: "EHP" over a tiny "phys"/"mag"
    so the column stays narrow)."""
    if '\n' in label:
        main, sub = label.split('\n', 1)
        return (f'{esc(main)}<span class="th-sub">{esc(sub)}</span>')
    return esc(label)


def _stats_thead():
    # Header: each sortable th carries data-col (key) and data-idx (its
    # body-cell index). One <th> per column: lvl, Copy (icon), Unit, Camp…
    thead_list = []
    for i, (k, label) in enumerate(COLUMNS):
        cat = COL_CAT.get(k, '')
        if k == 'icon':
            # owner 2026-11-19: the icon column has its own "Copy" header
            # (clicking an icon copies the spawn command); not sortable.
            thead_list.append(
                f'<th class="{_col_cls(k)}" data-cat="{cat}">'
                f'<span class="th-label">{_label_html(label)}</span></th>')
        elif not label:
            thead_list.append(f'<th class="{_col_cls(k)}" data-cat="{cat}"></th>')
        else:
            thead_list.append(
                f'<th class="{_col_cls(k)} sortable" data-col="{k}" '
                f'data-idx="{i}" data-cat="{cat}">'
                f'<span class="th-label">{_label_html(label)}</span>'
                f'<span class="sort-ind"></span></th>'
            )
    return ''.join(thead_list)


def _stats_cat_cells():
    # Super-category row: one cell per category, colspan = its leaf columns.
    # Each category has at least one Standard column, so the cell always shows;
    # when Expanded columns under it are hidden, the cell shrinks naturally.
    def view_cls(cat):
        slug = _CAT_SLUG.get(cat, 'x')
        return ' col-tl' if slug.startswith('tl-') else ('' if slug == 'basic' else ' col-main')
    return ''.join(
        f'<th class="cat-head cat-{_CAT_SLUG.get(cat, "x")}{view_cls(cat)}" '
        f'data-cat="{_CAT_SLUG.get(cat, "x")}" colspan="{len(cols)}">{esc(cat)}</th>'
        for cat, cols in CATEGORIES
    )


def _first_num(v):
    """The unit's own number of a cell ("1500 (1740)" -> 1500.0), None when there is none."""
    m = re.search(r'-?\d+(?:[.,]\d+)?', str(v or ''))
    return float(m.group(0).replace(',', '.')) if m else None


def timeline_value(d, stat, step):
    """A stat of one row at an upgrade step, by the Upgrade box's rules (src/js/creeps-upgrade.js `rule`):
    neutrals +30 HP, +0.5 armor, +3 damage, +5 attack speed, gold min +floor(L/2), max +floor((L+1)/2); a lane
    creep by its LANE_UPGRADE (HP and damage to its cap, mega's floor; gold every step; no armor or attack speed;
    without an entry — siege — it does not grow). None when the row has no such number."""
    key = {'hp': 'hp', 'armor': 'armor', 'dmg': 'dmg_avg', 'as': 'as', 'gold': 'gold'}[stat]
    base = _first_num(d.get(key))
    if base is None:
        return None
    ch = (d.get('createhero') or '').strip()
    if unit_group(ch) == 'lane':
        u = LANE_UPGRADE.get(ch, {})
        c = max(min(step, u.get('cap', step)), u.get('floor', 0))
        add = {'hp': u.get('hp', 0) * c, 'dmg': u.get('dmg', 0) * c, 'gold': u.get('gold', 0) * step}.get(stat, 0)
    else:
        add = {'hp': 30 * step, 'armor': 0.5 * step, 'dmg': 3 * step, 'as': 5 * step,
               'gold': (step // 2 + (step + 1) // 2) / 2}[stat]
    return base + add


def _tl_cell(k, d):
    _, stat, step = k.split('_')
    v = timeline_value(d, stat, int(step))
    text = DASH if v is None else (str(int(round(v))) if stat in ('hp', 'as') else fmt_num(v))
    sort = '' if v is None else f' data-sort="{v:g}"'
    return f'<td class="{_col_cls(k)}"{sort}>{text}</td>'


# ---- Neutral Stats: cells ----

def _load_unit_page_slugs():
    # npc -> Unit Changes page slug, so a creep's name links to its change page.
    # Derived from the same patch pages the Unit Changes index reads (the patch
    # step runs before this one, so dist/patches is already populated).
    try:
        import builders.entity_changes as _echg
        return _echg.unit_page_slugs()
    except ImportError:               # a bug inside it must show, not unlink every creep
        return {}


def _name_inner(v, d, unit_page_slugs):
    slug = unit_page_slugs.get(d.get('npc_key'))
    # a creep whose camp left the game: its row grey (creeps-cells.css tr[data-removed]), when in its camp cell's history
    # (owner 2026-11-19: "не нравится, сделай просто серым")
    return f'<a class="creep-name-link" href="units/{slug}.html">{esc(v)}</a>' if slug else esc(v)


def camp_changelog(createhero, dates=None):
    """The camp cell's history in the stat cells' format (patch, date, kind, camp), oldest first: the patch the creep
    came into the game (game files, only after 7.08) with its first camps, and a camp it left. Owner 2026-11-20:
    "наподобии как в других ячейках, только без % разницы"."""
    dates = dates or {}
    short = (createhero or '').strip()
    until = CAMP_UNTIL.get(short, {})
    camps = list(dict.fromkeys(list(until) + CREEP_CAMP.get(short, [])))
    out = []
    since = _creep_since().get(CREEP_NAME_TO_NPC.get(short) or '')
    if since:
        out += [(since, dates.get(since, ''), 'A', CAMP_LABEL.get(t, t)) for t in camps]
    out += [(p, dates.get(p, ''), 'R', CAMP_LABEL.get(t, t)) for t, p in until.items()]
    return out


def _camp_inner(v, d=None):
    if not v:
        return DASH
    imgs = []
    for t in v.split(','):
        label = CAMP_LABEL.get(t, t)
        imgs.append(
            # the crisp 16 px glyph (scripts/gen/gen_camp_icons.py), the 32 px one blurred at 16 (owner 2026-11-19)
            f'<img class="camp-ico" src="icons/camps/creepcamp_{t}_16.png" '
            f'srcset="icons/camps/creepcamp_{t}_16.png 1x, icons/camps/creepcamp_{t}_16@2x.png 2x" '
            f'alt="{esc(label)}" loading="lazy">')
    return ''.join(imgs)


def _attack_range_inner(v, d):
    typ = 'ranged' if d.get('attack_range_ranged') else 'melee'
    # Fixed-width number keeps every badge at the same x position.
    tip = 'Ranged' if typ == 'ranged' else 'Melee'
    return (f'<span class="atk-num">{esc(v)}</span>'
            f'<span class="atk-badge atk-{typ}" title="{tip}">'
            f'<img src="icons/ui/atk_{typ}.png" alt="{tip}" '
            f'title="{tip}" loading="lazy"></span>')


def _ability_inner(k, v, d):
    if not v:
        return DASH
    slug = d.get(k + '_slug', '')
    if has_abil_icon(slug):
        inner = abil_icon_html(slug, v)
    else:
        inner = esc(v)   # no icon on CDN → keep the name text
    # Clicking an ability jumps to its (unit, ability) row on the Unit
    # Abilities page. For abilities that share a single canonical row
    # across units (e.g. Riverborn Aura), route to that canonical unit.
    ch = (d.get('createhero') or '').strip()
    target_ch = UA_CANONICAL_UNIT.get(slug, ch)
    return (f'<a class="abil-link" '
            f'href="units_abilities.html#{target_ch}-{slug}">{inner}</a>'
            if slug else inner)


def _cell_inner(k, v, d, unit_page_slugs):
    """Inner HTML for a data cell. Attack Range → number + glass badge.
    Ability cells → the ability ICON (changelog style, smaller); the name
    is shown on hover. Falls back to the name text when no icon exists."""
    if k == 'name':
        return _name_inner(v, d, unit_page_slugs)
    if k == 'camp':
        return _camp_inner(v, d)
    if k == 'attack_range' and v:
        return _attack_range_inner(v, d)
    if k in ABILITY_COLS:
        return _ability_inner(k, v, d)
    return esc(v) if v else DASH


def _history_attrs(k, v, npc_key, src):
    """(extra <td> attributes, has history) for a stat / ability cell."""
    # Stat / ability cell carries its full change history as a
    # compact data attribute (patch|date|old|new;...) — scripts.js
    # renders a changelog tooltip on hover. Only emitted when the
    # unit actually has recorded changes for that column.
    extra = ''
    if k in COL_CHANGELOG:
        # Typed entries (variable length): patch|date|kind|...parts
        hist = ability_changelog(src.hist, src.abil_slim, npc_key, COL_CHANGELOG[k])
        payload = ';'.join('|'.join(str(x) for x in e) for e in hist)
    else:
        # Stat value change → 'V' kind: patch|date|V|old|new|pol.
        # BAT / time-to-hit are buffs when they DROP (lower = better).
        hist = value_history(src.hist, npc_key, COL_HIST[k])
        pol = 'lo' if k in ('bat', 't_per_attack') else 'hi'
        payload = ';'.join(f'{p}|{dt}|V|{ov}|{nv}|{pol}'
                           for (p, dt, ov, nv) in hist)
        # NET-CHANGE SUMMARY: every numeric stat column that changed
        # >1 time. Rendered INSIDE the hover tooltip by scripts.js —
        # at the top, above the newest patch, with a divider — NOT in
        # the cell. data-net just marks which cells get the summary.
        if len(hist) >= 2:
            extra += ' data-net=""'
    if hist:
        extra += f' data-hist="{esc(payload)}"'
    # Ability cells carry the name for the hover tooltip header.
    if k in COL_CHANGELOG and v:
        extra += f' data-name="{esc(v)}"'
    return extra, bool(hist)


def _stats_cell(k, row, src, unit_page_slugs):
    d = row['data']
    if COL_MODE.get(k) == 'tl':
        return _tl_cell(k, d)
    v = d.get(k, '')
    if k == 'lvl':
        # Per-row level cell (no rowspan). data-lvl lets scripts.js
        # collapse repeated numbers within a run and draw a divider
        # at group starts, in whatever order the table is sorted.
        return (f'<td class="lvl-cell {_col_cls(k)}" '
                f'data-lvl="{esc(v)}">{esc(v)}</td>')
    if k == 'icon':
        if not v:
            return f'<td class="creep-icon-cell {_col_cls(k)}"></td>'
        if unit_group(d.get('createhero')) == 'lane':      # no "-createhero <name> neutral" for a lane creep
            return (f'<td class="creep-icon-cell {_col_cls(k)}">'
                    f'<img class="creep-copy" src="{esc(v)}" alt="" loading="lazy" width="128" height="72" '
                    f'onerror="this.style.visibility=\'hidden\'"></td>')
        # Clicking the icon copies the dev-console spawn command
        # "-createhero <name> neutral" to the clipboard (handled
        # in scripts.js via the data-cmd attribute).
        cmd = f'-createhero {d.get("createhero", "")} neutral'
        return (f'<td class="creep-icon-cell {_col_cls(k)}">'
                f'<img class="creep-copy" src="{esc(v)}" alt="" '
                f'loading="lazy" width="128" height="72" data-cmd="{esc(cmd)}" '
                f'title="{esc(cmd)}" '
                f'onerror="this.style.visibility=\'hidden\'"></td>')
    inner = _cell_inner(k, v, d, unit_page_slugs)
    if k == 'camp':
        # the stat cells' history popup (creeps-changelog.js): ADDED / REMOVED rows, no %
        hist = camp_changelog(d.get('createhero'), src.hist.patch_dates)
        payload = ';'.join('|'.join(e) for e in hist)
        extra = f' data-hist="{esc(payload)}"' if hist else ''
        cls = _col_cls(k, v) + (' has-history' if hist else '')
        return f'<td class="{cls}"{_sort_attr(k, v)}{extra}>{inner}</td>'
    if k in COL_HIST or k in COL_CHANGELOG:
        extra, has_hist = _history_attrs(k, v, row.get('npc_key'), src)
        cls = _col_cls(k, v) + (' has-history' if has_hist else '')
        return f'<td class="{cls}"{_sort_attr(k, v)}{extra}>{inner}</td>'
    return f'<td class="{_col_cls(k, v)}"{_sort_attr(k, v)}>{inner}</td>'


def _stats_row_html(row, src, unit_page_slugs):
    d = row['data']
    tr_cls = ' class="tier-break"' if row['tier_break'] else ''
    cells = ''.join(_stats_cell(k, row, src, unit_page_slugs) for k, _ in COLUMNS)
    rid = f' id="unit-{esc((d.get("createhero") or "").strip())}"'
    attack_type = 'ranged' if d.get('attack_range_ranged') else 'melee'
    gone = REMOVED_CREEPS.get((d.get("createhero") or "").strip())
    removed = f' data-removed="{esc(gone)}"' if gone else ''
    group = unit_group(d.get('createhero'))
    upg = LANE_UPGRADE.get((d.get('createhero') or '').strip())
    upg_attr = f' data-upg="{attr_esc(_json.dumps(upg, separators=(",", ":")))}"' if upg else ''
    tier = f' data-lane-tier="{d["lane_tier"]}"' if d.get('lane_tier') else ''
    return (f'<tr{rid} data-group="{group}"{tier} data-attack-type="{attack_type}"{removed}{upg_attr}{tr_cls}>'
            f'{cells}</tr>')


# Lane creeps grow by their own rule, not neutral_upgrade (src/js/creeps-upgrade.js reads data-upg): every 7:30,
# per step flat; HP and damage stop at 30 steps ("cap"), gold and XP do not. server.dll 6997 (7.42a; the same in
# 6728 and 6978, increments table 0x187e3a0, applied at 0x26bb4d0) and Liquipedia "Lane Creeps" agree. Siege creeps
# do not grow at all: the spawner calls the upgrade only for "melee" / "range" / "flagbearer" names — no data-upg.
LANE_UPGRADE = {
    'lane_melee':      {'hp': 12, 'dmg': 1, 'gold': 1, 'xp': 0, 'cap': 30},
    'lane_flagbearer': {'hp': 12, 'dmg': 1, 'gold': 1, 'xp': 0, 'cap': 30},
    'lane_ranged':     {'hp': 12, 'dmg': 2, 'gold': 3, 'xp': 8, 'cap': 30},
    # super (the increments table's "upgraded" rows): melee and flagbearer give no extra gold
    'lane_melee_super':      {'hp': 19, 'dmg': 2, 'gold': 0, 'xp': 0, 'cap': 30},
    'lane_flagbearer_super': {'hp': 19, 'dmg': 2, 'gold': 0, 'xp': 0, 'cap': 30},
    'lane_ranged_super':     {'hp': 18, 'dmg': 3, 'gold': 3, 'xp': 0, 'cap': 30},
}
# mega: the super increments, HP and damage at the 30 steps from the start (all six barracks down); gold and XP still
# by the real number of steps ("floor": the lowest number of steps HP / damage count)
LANE_UPGRADE.update({k.replace('_super', '_mega'): {**v, 'floor': 30}
                     for k, v in list(LANE_UPGRADE.items()) if k.endswith('_super')})


# ---- Neutral Stats: page ----

def _aura_button():
    """Inspiration Aura on / off (owner 2026-11-26): the flagbearer's aura on every lane creep row at the chosen
    upgrade step — +HP regen, and magic resistance growing every 7:30 up to its maximum, stacked multiplicatively
    with the creep's own (src/js/creeps-upgrade.js). The numbers come from the current KV; a renamed key fails."""
    a = _latest_abilities().get('flagbearer_creep_aura_effect') or {}
    vals = {k: a.get('av_' + k) for k in ('bonus_health_regen', 'bonus_magic_resistance_per_interval',
                                          'maximum_intervals')}
    if any(v is None for v in vals.values()):
        raise KeyError(f"flagbearer_creep_aura_effect: {vals} — a key is missing from the current npc_abilities.json")
    return ('<button type="button" class="hs-attack-filter aura-toggle" id="flag-aura" aria-pressed="false" '
            f'data-regen="{vals["bonus_health_regen"]}" data-mr-step="{vals["bonus_magic_resistance_per_interval"]}" '
            f'data-mr-max="{vals["maximum_intervals"]}" aria-label="Inspiration Aura">'
            # just the icon (owner 2026-11-26: "просто иконкой, а не полным именем")
            '<img class="aura-ico" src="icons/abilities/flagbearer_creep_aura_effect.png" alt=""></button>')


_AURA_BUTTON = _aura_button()
# Nuke (owner 2026-11-26): magic and physical damage in two boxes; every row's HP cell turns light green when the
# unit survives, red when it dies — after its armor and magic resistance at the chosen step (src/js/creeps-upgrade.js)
_NUKE_FIELDS = (
    '<label class="ua-upgrades-toggle"><span class="ua-upgrades-label">Nuke</span>'
    '<input type="checkbox" id="nuke-toggle" class="ua-switch-input">'
    '<span class="ua-switch" aria-hidden="true"></span></label>'
    # the boxes keep their place while Nuke is off (invisible, not removed), so switching it never moves the toolbar
    # (owner 2026-11-26: "nuke не должно делать так, чтобы на другую строку всё сползало")
    '<span class="view-group nuke-group nuke-off" id="nuke-fields">'
    # no words beside the boxes (owner 2026-11-26: the toolbar grew a second row): a grey hint inside each, the
    # number in its damage type's colour — magic blue, physical red, as on Unit Abilities
    '<input type="text" inputmode="numeric" pattern="[0-9]*" maxlength="5" id="nuke-mag" '
    'class="upg-input nuke-input nuke-mag" value="" placeholder="Mag" aria-label="Magic damage">'
    '<input type="text" inputmode="numeric" pattern="[0-9]*" maxlength="5" id="nuke-phys" '
    'class="upg-input nuke-input nuke-phys" value="" placeholder="Phys" aria-label="Physical damage">'
    # pure damage: no armor, no resistance takes anything off it (owner 2026-11-26)
    '<input type="text" inputmode="numeric" pattern="[0-9]*" maxlength="5" id="nuke-pure" '
    'class="upg-input nuke-input nuke-pure" value="" placeholder="Pure" aria-label="Pure damage">'
    '</span>'
)

_STATS_TOOLBAR = (
    '<div class="cal-toggle-bar inbox-bar"><div class="toolbar-panel">'
    '<span class="view-group">'
    '<strong>View</strong>'
    '<select class="cal-mode-select" id="view-mode">'
    '<option value="standard">Standard</option>'
    '<option value="expanded">Expanded</option>'
    '<option value="timeline">Timeline</option>'   # every stat at each 7:30 step (TL_STATS)
    '</select>'
    '</span>'
    # lane creeps: Normal / Super (that lane's enemy barracks down) / Mega (all six down) — LANE_TIERS; beside View
    # (owner 2026-11-26: "Creeps поставить рядом с view")
    '<span class="view-group"><strong>Creeps</strong>'
    '<select class="cal-mode-select" id="lane-tier" aria-label="Lane creeps: normal, super or mega">'
    '<option value="normal">Normal</option><option value="super">Super</option><option value="mega">Mega</option>'
    '</select></span>'
    '<span class="hs-attack-filter-group" aria-label="Attack type filter">'
    '<button type="button" class="hs-attack-filter" data-attack-filter="melee" '
    'aria-pressed="false" title="Show melee units">'
    '<span class="atk-badge" aria-hidden="true">'
    '<img src="icons/ui/atk_melee.png" alt=""></span><span>Melee</span></button>'
    '<button type="button" class="hs-attack-filter" data-attack-filter="ranged" '
    'aria-pressed="false" title="Show ranged units">'
    '<span class="atk-badge" aria-hidden="true">'
    '<img src="icons/ui/atk_ranged.png" alt=""></span><span>Ranged</span></button>'
    '</span>'
    # creeps whose camp left the game (REMOVED_CREEPS): hidden until pressed
    '<button type="button" class="hs-attack-filter" id="removed-toggle" aria-pressed="false">'
    '<span>Removed</span></button>'
    + GROUP_SWITCHES +
    # neutral_upgrade: every 7:30 from the horn, up to 30 steps (src/js/creeps-upgrade.js; owner 2026-11-23); after the
    # group switches (owner 2026-11-26)
    '<label class="view-group upg-group"><strong>Upgrade</strong>'
    # the step's game time is the box's hover hint, not a chip beside it (owner 2026-11-26)
    '<input type="text" inputmode="numeric" pattern="[0-9]*" maxlength="2" id="upgrade-step" '
    'class="upg-input tb-tip-target" value="0" data-tooltip="0:00" '
    'aria-label="Creep upgrade number, 0 to 30"></label>'
    + _AURA_BUTTON + _NUKE_FIELDS +
    '</div></div>\n'
)

# Backward-compat redirects: any old bookmark / external link to the former
# /neutral_creeps.html, /creeps.html or /materials.html bounces to
# /units_stats.html (neutral_stats.html until 2026-11-26). Removed
# once we're confident no traffic references the old URLs.
_STATS_REDIRECT_PAGES = ('neutral_stats.html', 'neutral_creeps.html', 'creeps.html', 'materials.html')
_STATS_REDIRECT_HTML = (
    '<!DOCTYPE html><html><head><meta charset="UTF-8">'
    '<meta http-equiv="refresh" content="0; url=units_stats.html">'
    '<link rel="canonical" href="units_stats.html">'
    '<title>Sloppy — moved</title></head><body>'
    '<p>This page moved to '
    '<a href="units_stats.html">units_stats.html</a>.</p>'
    '</body></html>'
)


def stats_page_html(body_parts, asset_version):
    # Materials sub-tabs are embedded directly into the site header now
    # (subtabs_active), so there's no separate strip below it to freeze on
    # scroll. Build one nav per page with the correct active sub-tab.
    # subnav_in_header=False: the sub-tab bar is placed INSIDE the scroll box
    # (below) so it scrolls away with the table like Mana Items, instead of
    # staying pinned under the nav.
    nav = _site.render_top_nav('materials', _latest_href(),
                               patch_context=False, subtabs_active='creeps',
                               subnav_in_header=False)
    inner = (
        f'{_site.render_materials_subnav("creeps")}'
        + _STATS_TOOLBAR +
        '<table class="creeps-table mode-standard">\n'
        f'<thead><tr class="cat-row">{_stats_cat_cells()}</tr>'
        f'<tr class="col-row">{_stats_thead()}</tr></thead>\n'
        f'<tbody>\n{chr(10).join(body_parts)}\n</tbody>\n'
        '</table>\n'
    )
    return page_shell('Unit Stats', nav, inner, asset_version)


def save_neutral_stats_html(rendered, src):
    """Write units_stats.html (+ the old-URL redirects, neutral_stats.html among them)."""
    unit_page_slugs = _load_unit_page_slugs()
    body_parts = [_stats_row_html(row, src, unit_page_slugs) for row in rendered]
    html = stats_page_html(body_parts, ASSET_VERSION)
    write_dist('units_stats.html', html)
    print(f"  -> dist/units_stats.html: {len(html):,} bytes")
    for old in _STATS_REDIRECT_PAGES:
        write_dist(old, _STATS_REDIRECT_HTML)


def save_creeps_html():
    """Generate units_stats.html — unit stats table. CSV provides the
    ordering, level (Ур.) and createhero name; every other column is
    auto-pulled from data/stats/<latest>/units.json (latest_stats_version()) + npc_units.txt and
    abilities_slim.json. Derived columns (Armor %, EHP Phys/Mag, Avg dmg,
    Avg gold, t/1 attack) are computed from formulas. Tier-level rows are
    separated with a horizontal divider when Ур. changes.

    Per-CSV-row icon/display-name mapping lives in CREEP_NAME_TO_NPC plus
    CREEP_DISPLAY_NAMES above — update those to add new neutrals."""
    csv_path = _os.path.join(_HERE,
                             'data', 'creeps_raw.csv')
    if not _os.path.exists(csv_path):
        print("  ! creeps_raw.csv not found, skipping units_stats.html")
        return
    src = load_sources()
    with open(csv_path, encoding='utf-8') as f:
        csv_rows = list(_csv.reader(f))
    rendered = build_rows(csv_rows, src)
    save_neutral_stats_html(rendered, src)
    save_neutral_abilities_html(rendered, src.hist, ASSET_VERSION)


if __name__ == "__main__":
    save_creeps_html()
