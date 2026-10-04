"""build_creeps.py — generates neutral_stats.html, the neutral stats
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
import json as _json
import os as _os
import re
import sys as _sys
from dataclasses import dataclass
from typing import NamedTuple

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _HERE)

import builders.site_common as _site
from builders.creeps_abilities import UA_CANONICAL_UNIT, save_neutral_abilities_html
from builders.creeps_common import (
    ABILITY_COLS, ABILITY_SKIP, DASH, HULL_BOUNDS, NEUTRAL_DEFAULT_HULL,
    NEUTRAL_DEFAULT_TURN_RATE, abil_icon_html, ability_dname, armor_factor,
    ehp_mag_val, ehp_phys_val, esc, fmt_num, fmt_regen, has_abil_icon,
    page_shell, safe_float, safe_int, write_dist,
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
_NPC_HEAD_RE = re.compile(r'^\s*"(npc_dota_(?:neutral_[a-z0-9_]+|dark_troll_warlord_skeleton_warrior))"\s*$')
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
    # Hero-summoned unit surfaced in the table — Dark Troll
    # Summoner's skeleton (data lives in the npc_dota_dark_troll_
    # warlord_skeleton_warrior block, captured by the broadened
    # _NPC_HEAD_RE above).
    'skeleton_warrior':   'npc_dota_dark_troll_warlord_skeleton_warrior',
}

# CSV rows that should be HIDDEN from the table entirely (lane creeps
# belong to a different section that will be added later).
HIDDEN_CREATEHERO = {'flag / melee', 'ranged'}

# Full display name (Russian/English) shown in the new Крип column.
CREEP_DISPLAY_NAMES = {
    'npc_dota_neutral_wildkin':              'Wildwing',
    'npc_dota_neutral_kobold':               'Kobold',
    'npc_dota_neutral_kobold_tunneler':      'Kobold Tunneler',
    'npc_dota_neutral_kobold_taskmaster':    'Kobold Taskmaster',
    'npc_dota_neutral_forest_troll_berserker':   'Forest Troll Berserker',
    'npc_dota_neutral_forest_troll_high_priest': 'Forest Troll High Priest',
    'npc_dota_neutral_gnoll_assassin':       'Gnoll Assassin',
    'npc_dota_neutral_fel_beast':            'Fel Beast',
    'npc_dota_neutral_harpy_scout':          'Harpy Scout',
    'npc_dota_neutral_harpy_storm':          'Harpy Stormcrafter',
    'npc_dota_neutral_ogre_mauler':          'Ogre Bruiser',
    'npc_dota_neutral_ogre_magi':            'Ogre Frostmage',
    'npc_dota_neutral_ghost':                'Ghost',
    'npc_dota_neutral_satyr_trickster':      'Satyr Banisher',
    'npc_dota_neutral_satyr_soulstealer':    'Satyr Mindstealer',
    'npc_dota_neutral_satyr_hellcaller':     'Satyr Hellcaller',
    'npc_dota_neutral_centaur_outrunner':    'Centaur Courser',
    'npc_dota_neutral_centaur_khan':         'Centaur Conqueror',
    'npc_dota_neutral_tadpole':              'Tadpole',
    'npc_dota_neutral_giant_wolf':           'Giant Wolf',
    'npc_dota_neutral_alpha_wolf':           'Alpha Wolf',
    'npc_dota_neutral_froglet':              'Froglet',
    'npc_dota_neutral_froglet_mage':         'Froglet Mage',
    'npc_dota_neutral_grown_frog':           'Grown Frog',
    'npc_dota_neutral_grown_frog_mage':      'Grown Frog Mage',
    'npc_dota_neutral_ancient_frog':         'Ancient Frog',
    'npc_dota_neutral_ancient_frog_mage':    'Ancient Frog Mage',
    'npc_dota_neutral_mud_golem':            'Mud Golem',
    'npc_dota_neutral_mud_golem_split':      'Mud Golem Splinter',
    'npc_dota_neutral_dark_troll':           'Dark Troll',
    'npc_dota_neutral_dark_troll_warlord':   'Dark Troll Summoner',
    'npc_dota_neutral_warpine_raider':       'Warpine Raider',
    'npc_dota_neutral_polar_furbolg_ursa_warrior': 'Hellbear',
    'npc_dota_neutral_polar_furbolg_champion':     'Hellbear Smasher',
    'npc_dota_neutral_prowler_acolyte':      'Prowler Acolyte',
    'npc_dota_neutral_prowler_shaman':       'Prowler Shaman',
    'npc_dota_neutral_frostbitten_golem':    'Frostbitten Golem',
    'npc_dota_neutral_rock_golem':           'Rock Golem',
    'npc_dota_neutral_enraged_wildkin':      'Wildwing Ripper',
    'npc_dota_neutral_big_thunder_lizard':   'Thunderhide',
    'npc_dota_neutral_small_thunder_lizard': 'Small Thunder Lizard',
    'npc_dota_neutral_jungle_stalker':       'Jungle Stalker',
    'npc_dota_neutral_elder_jungle_stalker': 'Elder Jungle Stalker',
    'npc_dota_neutral_ice_shaman':           'Ice Shaman',
    'npc_dota_neutral_granite_golem':        'Granite Golem',
    'npc_dota_neutral_black_drake':          'Black Drake',
    'npc_dota_neutral_black_dragon':         'Black Dragon',
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
    'outrunner':            ['mid', 'big'],
    'tad':                  ['small'],
    'trickster':            ['mid', 'big'],
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
    'khan':                 ['mid', 'big'],
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
}
CAMP_LABEL = {'small': 'Small camp', 'mid': 'Medium camp',
              'big': 'Large camp', 'ancient': 'Ancient camp'}

# Auras that buff the caster's OWN stats — the creep benefits from its own
# aura, so the displayed stat shows "base (with-aura)". Level-1 aura values,
# from npc_abilities.json (av_* fields). Keyed by createhero shortname.
# op '+' = additive flat, '*' = multiplicative. 'dmg' covers min/max/avg.
AURA_SELF = {
    'hellcaller':           {'hp_regen': ('+', 3)},      # Unholy Aura
    'skeleton_warrior':     {'dmg': ('+', 2)},           # Rally
    'taskmaster':           {'ms': ('*', 1.12)},         # Speed Aura +12%
    'soulstealer':          {'mp_regen': ('+', 1.75)},   # Mana Aura (Mindstealer)
    'outrunner':            {'magres': ('+', 20)},       # Cloak Aura (creep value)
    'prowler_acolyte':      {'hp_regen': ('+', 9)},      # Spawnlord HP-reg aura
    'alpha':                {'dmg': ('*', 1.2)},         # Command Aura +20%
    'enraged':              {'armor': ('+', 3)},         # Toughness Aura
    'small_thunder_lizard': {'as': ('+', 25)},           # War Drums (atk speed)
    'black_dragon':         {'armor': ('+', 3)},         # Dragonhide Aura
    'granite':              {'hp': ('*', 1.16)},         # Granite Aura +16%
}


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
    for stat, (op, val) in aura.items():
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
        display_name = CREEP_DISPLAY_NAMES.get(
            npc_key,
            npc_key.replace('npc_dota_neutral_', '').replace('_', ' ').title()
        )
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
    return rendered


# ---- Neutral Stats: column structure ----
# Super-categories → columns (key, label, mode). mode 'std' = visible in
# both Standard and Expanded; 'exp' = Expanded only. Render order follows
# this structure; the View toggle hides 'exp' columns in Standard mode.
CATEGORIES = [
    ('Basic', [
        ('lvl',          'Lvl',              'std'),
        ('icon',         '',                 'std'),
        ('name',         'Unit',             'std'),
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
        ('camp',         'Camp',             'std'),
        ('ms',           'Movespeed',        'std'),
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
COLUMNS = [(k, label) for _cat, cols in CATEGORIES for (k, label, _m) in cols]
COL_MODE = {k: m for _cat, cols in CATEGORIES for (k, _l, m) in cols}
_CAT_SLUG = {'Basic': 'basic', 'Vitality': 'vitality', 'Attack': 'attack',
             'Bounty': 'bounty', 'Other': 'other', 'Abilities': 'abilities'}
COL_CAT = {k: _CAT_SLUG[cat] for cat, cols in CATEGORIES for (k, _l, _m) in cols}
COL_WIDTHS = {
    'lvl': 30, 'icon': 56, 'name': 170, 'createhero': 130,
    'hp': 50, 'hp_regen': 52, 'mp': 50, 'mp_regen': 52,
    'armor': 52, 'armor_pct': 64, 'ehp_phys': 64, 'magres': 56,
    'ehp_mag': 64, 'dmg_avg': 60,
    'as': 38, 't_per_attack': 58, 'bat': 38, 'ms': 38,
    'gold': 56, 'xp': 42, 'attack_range': 110,
    'attack_type': 100, 'vision': 70, 'aggro': 70,
    'ap': 48, 'turn_rate': 64, 'collision_size': 96,
    'bound_radius': 88, 'projectile': 100,
    'ability1': 150, 'ability2': 150, 'ability3': 150,
}
# No colgroup: table-layout: auto lets the browser size each column
# to fit content (and each header) on one line. Headers and cells
# are explicitly centred via CSS so the auto-width math doesn't have
# to budget for tag-width differences across columns.
# Columns that get a vertical separator on their RIGHT edge — they
# group the table into logical sections (identity | survivability |
# offense | economy | utility | abilities).
# Left-border on the first (always-visible) column of each super-category.
SEP_AFTER = {'hp', 'dmg_avg', 'gold', 'camp', 'ability1'}
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
    # body-cell index, so the sort logic survives the colspan on Юнит).
    # The "Юнит" header spans the icon + name columns (colspan=2) so it
    # reads as centered over the whole unit-identity block; the separate
    # icon <th> is dropped.
    name_idx = [k for k, _ in COLUMNS].index('name')
    thead_list = []
    for i, (k, label) in enumerate(COLUMNS):
        if k == 'icon':
            continue  # folded into the colspan=2 Юнит header
        cat = COL_CAT.get(k, '')
        if k == 'name':
            thead_list.append(
                f'<th class="{_col_cls(k)} sortable" colspan="2" '
                f'data-col="{k}" data-idx="{name_idx}" data-cat="{cat}">'
                f'<span class="th-label">{_label_html(label)}</span>'
                f'<span class="sort-ind"></span></th>'
            )
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
    return ''.join(
        f'<th class="cat-head cat-{_CAT_SLUG.get(cat, "x")}" '
        f'data-cat="{_CAT_SLUG.get(cat, "x")}" colspan="{len(cols)}">{esc(cat)}</th>'
        for cat, cols in CATEGORIES
    )


# ---- Neutral Stats: cells ----

def _load_unit_page_slugs():
    # npc -> Unit Changes page slug, so a creep's name links to its change page.
    # Derived from the same patch pages the Unit Changes index reads (the patch
    # step runs before this one, so dist/patches is already populated).
    try:
        import builders.entity_changes as _echg
        return _echg.unit_page_slugs()
    except Exception:
        return {}


def _name_inner(v, d, unit_page_slugs):
    slug = unit_page_slugs.get(d.get('npc_key'))
    if slug:
        return (f'<a class="creep-name-link" href="units/{slug}.html">'
                f'{esc(v)}</a>')
    return esc(v)


def _camp_inner(v):
    if not v:
        return DASH
    imgs = []
    for t in v.split(','):
        label = CAMP_LABEL.get(t, t)
        imgs.append(
            f'<img class="camp-ico" src="icons/camps/creepcamp_{t}.png" '
            f'alt="{esc(label)}" title="{esc(label)}" loading="lazy">')
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
            f'href="neutral_abilities.html#{target_ch}-{slug}">{inner}</a>'
            if slug else inner)


def _cell_inner(k, v, d, unit_page_slugs):
    """Inner HTML for a data cell. Attack Range → number + glass badge.
    Ability cells → the ability ICON (changelog style, smaller); the name
    is shown on hover. Falls back to the name text when no icon exists."""
    if k == 'name':
        return _name_inner(v, d, unit_page_slugs)
    if k == 'camp':
        return _camp_inner(v)
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
    return f'<tr{rid} data-attack-type="{attack_type}"{tr_cls}>{cells}</tr>'


# ---- Neutral Stats: page ----

_STATS_TOOLBAR = (
    '<div class="cal-toggle-bar inbox-bar"><div class="toolbar-panel">'
    '<span class="view-group">'
    '<strong>View</strong>'
    '<select class="cal-mode-select" id="view-mode">'
    '<option value="standard">Standard</option>'
    '<option value="expanded">Expanded</option>'
    '</select>'
    '</span>'
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
    '</div></div>\n'
)

# Backward-compat redirects: any old bookmark / external link to the former
# /neutral_creeps.html, /creeps.html or /materials.html bounces to
# /neutral_stats.html. Removed
# once we're confident no traffic references the old URLs.
_STATS_REDIRECT_PAGES = ('neutral_creeps.html', 'creeps.html', 'materials.html')
_STATS_REDIRECT_HTML = (
    '<!DOCTYPE html><html><head><meta charset="UTF-8">'
    '<meta http-equiv="refresh" content="0; url=neutral_stats.html">'
    '<link rel="canonical" href="neutral_stats.html">'
    '<title>Sloppy — moved</title></head><body>'
    '<p>This page moved to '
    '<a href="neutral_stats.html">neutral_stats.html</a>.</p>'
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
    return page_shell('Neutral Stats', nav, inner, asset_version)


def save_neutral_stats_html(rendered, src):
    """Write neutral_stats.html (+ the old-URL redirects)."""
    unit_page_slugs = _load_unit_page_slugs()
    body_parts = [_stats_row_html(row, src, unit_page_slugs) for row in rendered]
    html = stats_page_html(body_parts, ASSET_VERSION)
    write_dist('neutral_stats.html', html)
    print(f"  -> dist/neutral_stats.html: {len(html):,} bytes")
    for old in _STATS_REDIRECT_PAGES:
        write_dist(old, _STATS_REDIRECT_HTML)


def save_creeps_html():
    """Generate neutral_stats.html — neutral stats table. CSV provides the
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
        print(f"  ! creeps_raw.csv not found, skipping neutral_stats.html")
        return
    src = load_sources()
    with open(csv_path, encoding='utf-8') as f:
        csv_rows = list(_csv.reader(f))
    rendered = build_rows(csv_rows, src)
    save_neutral_stats_html(rendered, src)
    save_neutral_abilities_html(rendered, src.hist, ASSET_VERSION)


if __name__ == "__main__":
    save_creeps_html()
