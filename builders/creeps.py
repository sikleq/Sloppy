"""build_creeps.py — generates neutral_stats.html, the neutral stats
table. This is a standalone side-project, decoupled from the patch
changelog generator (build_patch.py). Both share the site chrome via
site_common.py.

Data sources (read-only):
  data/creeps_raw.csv               — ordering, level, createhero names
  data/stats/7.41c/units.json       — base neutral stats
  data/stats/7.41c/npc_units.txt    — full KV (regen, bounty, vision, abilities)
  data/abilities_slim.json          — ability slug → display name
  data/site_meta.json               — latest patch href (written by build_patch.py)
  icons/units/*.png                 — creep portraits

Run AFTER build_patch.py (which writes data/site_meta.json). If the meta
file is missing the Changelogs nav link falls back to a sensible default.
"""
import json as _json
import os as _os
import re
import sys as _sys

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _HERE)

import site_common as _site

ASSET_VERSION = _site.compute_asset_version()


def _latest_href():
    """Latest patch page href for the Changelogs nav tab. Read from the
    meta file build_patch.py emits; fall back to the newest patches/*.html
    if absent."""
    meta_path = _os.path.join(_HERE, "data", "site_meta.json")
    try:
        meta = _json.loads(open(meta_path, encoding="utf-8").read())
        return meta.get("latest_patch_filename", "patches/7.41c.html")
    except Exception:
        return "patches/7.41c.html"


def save_creeps_html():
    """Generate neutral_stats.html — neutral stats table. CSV provides the
    ordering, level (Ур.) and createhero name; every other column is
    auto-pulled from data/stats/7.41c/units.json + npc_units.txt and
    abilities_slim.json. Derived columns (Armor %, EHP Phys/Mag, Avg dmg,
    Avg gold, t/1 attack) are computed from formulas. Tier-level rows are
    separated with a horizontal divider when Ур. changes.

    Per-CSV-row icon/display-name mapping lives in CREEP_NAME_TO_NPC plus
    CREEP_DISPLAY_NAMES below — update those to add new neutrals."""
    import csv as _csv
    import re as _re

    csv_path = _os.path.join(_HERE,
                              'data', 'creeps_raw.csv')
    if not _os.path.exists(csv_path):
        print(f"  ! creeps_raw.csv not found, skipping neutral_stats.html")
        return

    # ---- Source files ----
    UNITS_PATH = _os.path.join(_HERE,
                                'data', 'stats', '7.41c', 'units.json')
    NPC_KV_PATH = _os.path.join(_HERE,
                                 'data', 'stats', '7.41c', 'npc_units.txt')
    ABIL_SLIM_PATH = _os.path.join(_HERE,
                                    'data', 'abilities_slim.json')
    units = _json.loads(open(UNITS_PATH, encoding='utf-8').read()) \
            if _os.path.exists(UNITS_PATH) else {}
    abil_slim = _json.loads(open(ABIL_SLIM_PATH, encoding='utf-8').read()) \
                if _os.path.exists(ABIL_SLIM_PATH) else {}

    # ---- Parse npc_units.txt for full stats per neutral ----
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
    npc_data = {}
    if _os.path.exists(NPC_KV_PATH):
        # Line-based parser with brace-depth tracking. Each top-level npc
        # block can contain deeply nested KV subblocks (AbilityValues,
        # CalculateSpellDamageTooltip etc.); plain regex can't balance
        # arbitrary depth.
        kv_lines = open(NPC_KV_PATH, encoding='utf-8').read().splitlines()
        n_lines = len(kv_lines)
        # Capture both neutrals AND the hero-summoned units we surface
        # in the table (e.g. Dark Troll Summoner's skeleton_warrior).
        head_re = _re.compile(r'^\s*"(npc_dota_(?:neutral_[a-z0-9_]+|dark_troll_warlord_skeleton_warrior))"\s*$')
        field_re = _re.compile(r'^\s*"([A-Za-z_][A-Za-z0-9_]*)"\s+"([^"]+)"')
        i = 0
        while i < n_lines:
            m = head_re.match(kv_lines[i])
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
                    fm = field_re.match(line)
                    if fm and fm.group(1) in NPC_FIELDS:
                        entry[fm.group(1)] = fm.group(2)
                depth += line.count('{') - line.count('}')
                j += 1
            npc_data[name] = entry
            i = j

    # ---- Per-stat history across all patches (7.08 → latest) ----
    # Walks data/stats/<patch>/npc_units.json chronologically and records each
    # change per neutral for the per-cell changelog tooltips. npc_units.json
    # (written by scripts/fetch_npc_history.py from dotabuff/d2vpkr) is the
    # full Valve KV, present for all 115 patches — so EVERY stat column can
    # carry history, raw or derived. Patch dates come from site_meta.json.
    RAW_HIST_FIELDS = (
        'StatusHealth', 'StatusHealthRegen', 'StatusMana', 'StatusManaRegen',
        'ArmorPhysical', 'MagicalResistance', 'AttackRate', 'BaseAttackSpeed',
        'MovementSpeed', 'BountyXP', 'AttackAcquisitionRange', 'AttackRange',
        'AttackDamageMin', 'AttackDamageMax', 'BountyGoldMin', 'BountyGoldMax',
        'VisionDaytimeRange', 'VisionNighttimeRange',
        'AttackAnimationPoint', 'MovementTurnRate', 'ProjectileSpeed',
        'BoundsHullName', 'RingRadius',
        'Ability1', 'Ability2', 'Ability3', 'Ability4', 'Ability5',
    )
    import re as _re_hist
    STATS_DIR = _os.path.join(_HERE, "data", "stats")
    META_PATH = _os.path.join(_HERE, "data", "site_meta.json")
    try:
        _meta = _json.loads(open(META_PATH, encoding="utf-8").read())
        PATCH_DATES = _meta.get("patch_dates", {})
    except Exception:
        PATCH_DATES = {}

    def _ver_key(v):
        return tuple(int(p) if p.isdigit() else p
                     for p in _re_hist.split(r'(\d+)', v))

    def _num(x):
        """Parse a KV value to int/float (integral floats → int), else str."""
        try:
            f = float(x)
            return int(f) if f.is_integer() else f
        except (TypeError, ValueError):
            return x

    _patches_chrono = []
    if _os.path.isdir(STATS_DIR):
        _patches_chrono = sorted(
            (d for d in _os.listdir(STATS_DIR)
             if _os.path.isdir(_os.path.join(STATS_DIR, d))),
            key=_ver_key,
        )
    # _raw_by_patch[field][version] = {npc_key: parsed_value}
    _raw_by_patch = {f: {} for f in RAW_HIST_FIELDS}
    for _v in _patches_chrono:
        _np_path = _os.path.join(STATS_DIR, _v, "npc_units.json")
        if not _os.path.exists(_np_path):
            continue
        try:
            _npc = _json.loads(open(_np_path, encoding="utf-8").read())
        except Exception:
            continue
        for _f in RAW_HIST_FIELDS:
            _bucket = {}
            for _k, _entry in _npc.items():
                if not isinstance(_entry, dict):
                    continue
                _raw = _entry.get(_f)
                if _raw is not None:
                    _bucket[_k] = _num(_raw)
            _raw_by_patch[_f][_v] = _bucket

    # Per-patch neutral ability balance data (from npc_abilities.json, written
    # by scripts/fetch_ability_history.py). _abil_by_patch[version][slug] =
    # {field: value} — used for the ability-cell value changelog.
    def _norm_abil_fields(fields):
        """Collapse `av_X_tooltip` (display-only mirror) onto `av_X` so a value
        moving from a flat tooltip to a real per-level field (e.g. Mud Golem
        Shard Split in 7.33: shard_damage_tooltip 9 → shard_damage 12/16/20/28)
        registers as one change instead of an add+remove that we skip."""
        out = {}
        for k, val in fields.items():
            base = k[:-len('_tooltip')] if k.endswith('_tooltip') else k
            # Prefer the real field over the tooltip mirror when both exist.
            if base in out and k.endswith('_tooltip'):
                continue
            out[base] = val
        return out

    _abil_by_patch = {}
    for _v in _patches_chrono:
        _ap_path = _os.path.join(STATS_DIR, _v, "npc_abilities.json")
        if not _os.path.exists(_ap_path):
            continue
        try:
            _raw_ab = _json.loads(open(_ap_path, encoding="utf-8").read())
            _abil_by_patch[_v] = {s: _norm_abil_fields(f) for s, f in _raw_ab.items()}
        except Exception:
            _abil_by_patch[_v] = {}

    def _raw_at(field, version, npc_key):
        return _raw_by_patch.get(field, {}).get(version, {}).get(npc_key)

    def _value_history(npc_key, valuefn):
        """List of (patch, date, old, new) changes, chronological. `valuefn`
        maps (version, npc_key) → display string for that patch (or None when
        the stat is absent). Consecutive distinct values are recorded."""
        if not npc_key:
            return []
        changes = []
        prev = None
        for _v in _patches_chrono:
            cur = valuefn(_v, npc_key)
            if cur is None or cur == '':
                continue
            if prev is not None and cur != prev:
                changes.append((_v, PATCH_DATES.get(_v, ""), prev, cur))
            prev = cur
        return changes

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
        # head_re above).
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

    # Hidden marker abilities — not real spells, suppressed from output.
    # `neutral_upgrade`: every neutral has this; auto-buff tracker.
    # `creep_piercing`: tags the unit with pierce attack-class. The info
    # already lives in the Тип атаки column, so showing it as an ability
    # is redundant.
    ABILITY_SKIP = {'neutral_upgrade', 'creep_piercing'}

    # Autocast abilities — get the animated golden ring marker on their icon
    # (mirrors the in-game autocast toggle visual). The data feed carries no
    # AbilityBehavior/autocast flag, so this list is maintained by hand.
    AUTOCAST_ABILITIES = {
        'forest_troll_high_priest_heal',   # Heal (Forest Troll High Priest)
        'ogre_magi_frost_armor',           # Ice Armor (Ogre Frostmage)
        'spawnlord_master_freeze',         # Petrify (Prowler Shaman)
    }

    # Through-BKB lookup — kept separate from ABIL_MANUAL so the Through BKB
    # column has a single source of truth. Anything not listed renders "—".
    THROUGH_BKB = {
        # Pierces magic immunity:
        'spawnlord_master_freeze':              'yes',  # Petrify
        # Pierces magic immunity (additional yes-cases):
        'forest_troll_high_priest_heal':        'yes',  # Heal
        'frogmen_water_bubble_small':           'yes',  # Water Bubble (Small)
        'frogmen_water_bubble_medium':          'yes',  # Water Bubble (Medium)
        'frogmen_water_bubble_large':           'yes',  # Water Bubble (Large)
        'big_thunder_lizard_frenzy':            'yes',  # Frenzy
        # Blocked by BKB:
        'enraged_wildkin_tornado':              'no',   # Tornado
        'kobold_disarm':                        'no',   # Steal Weapon
        'berserker_troll_break':                'no',   # Break
        'gnoll_assassin_envenomed_weapon':      'no',   # Envenomed Weapon
        'fel_beast_haunt':                      'no',   # Vex
        'ogre_bruiser_ogre_smash':              'no',   # Ogre Smash!
        'satyr_trickster_purge':                'no',   # Purge
        'giant_wolf_intimidate':                'no',   # Intimidate
        'dark_troll_warlord_ensnare':           'no',   # Ensnare
        'ghost_frost_attack':                   'no',   # Frost Attack
        'black_drake_magic_amplification_aura': 'no',   # Magic Amplification Aura
        'ogre_magi_frost_armor':                'no',   # Ice Armor
        'mud_golem_hurl_boulder':               'no',   # Hurl Boulder
        'frogmen_arm_of_the_deep':              'no',   # Arm of the Deep
        'frogmen_tendrils_of_the_deep':         'no',   # Tendrils of the Deep
        'satyr_soulstealer_mana_burn':          'no',   # Mana Burn
        'centaur_khan_war_stomp':               'no',   # War Stomp
        'polar_furbolg_ursa_warrior_thunder_clap': 'no',  # Thunder Clap
        'enraged_wildkin_hurricane':            'no',   # Hurricane
        'warpine_raider_seed_shot':             'no',   # Seed Shot
        'frogmen_congregation_of_the_deep':     'no',   # Congregations of the Deep
        'ancient_rock_golem_weakening_aura':    'no',   # Weakening Aura
        'satyr_hellcaller_shockwave':           'no',   # Shockwave
        'spawnlord_master_stomp':               'no',   # Desecrate
        'black_dragon_fireball':                'no',   # Fireball
        'harpy_storm_chain_lightning':          'no',   # Chain Lightning
        'big_thunder_lizard_slam':              'no',   # Slam
        'ice_shaman_incendiary_bomb':           'no',   # Icefire Bomb
    }
    # Per-cell `?` hints in the Through BKB column. Keyed by ability slug.
    THROUGH_BKB_TIPS = {
        'ogre_magi_frost_armor': (
            'Can be cast on an ally under BKB, '
            "but the slow on an enemy under BKB doesn't work"),
        'forest_troll_high_priest_heal':
            'Can be cast on an ally under BKB',
        'satyr_trickster_purge': (
            'Can be cast on an ally under BKB, '
            "but the effect on an enemy under BKB doesn't work"),
        'enraged_wildkin_hurricane': (
            'Can be cast on an ally under BKB, '
            "but the effect on an enemy under BKB doesn't work"),
    }

    def _autocast_snake_svg() -> str:
        """Animated golden ring used as the autocast marker on ability icons."""
        _r = ('<rect x="1.5" y="1.5" width="25" height="25" '
              'rx="4.5" ry="4.5" pathLength="100"')
        return (
            '<svg class="autocast-snake" viewBox="0 0 28 28" '
            'preserveAspectRatio="none" aria-hidden="true">'
            f'{_r} class="ac-ring"></rect>'
            f'{_r} class="ac-fluff"></rect>'
            f'{_r} class="ac-tail4"></rect>'
            f'{_r} class="ac-tail3"></rect>'
            f'{_r} class="ac-tail2"></rect>'
            f'{_r} class="ac-tail1"></rect>'
            f'{_r} class="ac-body"></rect>'
            f'{_r} class="ac-pollen"></rect>'
            f'{_r} class="ac-pollen2"></rect>'
            f'{_r} class="ac-pollen3"></rect></svg>')

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

    # Display-name overrides — when Valve's canonical dname diverges from the
    # team's preferred terminology (e.g. Valve calls it "Ice Armor", we use
    # "Frost Armor" to match the creep's "Frostmage" name).
    ABILITY_NAME_OVERRIDES = {
        'ogre_magi_frost_armor': 'Frost Armor',
    }

    def _ability_dname(slug):
        if not slug or slug in ABILITY_SKIP:
            return ''
        if slug in ABILITY_NAME_OVERRIDES:
            return ABILITY_NAME_OVERRIDES[slug]
        entry = abil_slim.get(slug)
        if entry and entry.get('dname'):
            return entry['dname']
        return slug.replace('_', ' ').title()

    def _fmt_num(x):
        if isinstance(x, str):
            try:
                x = float(x) if '.' in x else int(x)
            except ValueError:
                return x
        if isinstance(x, float):
            return f'{x:g}'.replace('.', ',')
        return str(x)

    def _fmt_regen(x):
        x = float(x or 0)
        return '0' if abs(x) < 1e-9 else f'{x:.2f}'.replace('.', ',')

    def _safe_int(v, default=0):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return default

    def _safe_float(v, default=0.0):
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    def _armor_factor(a):
        return (0.06 * a) / (1 + 0.06 * abs(a))

    def _ehp_phys_val(hp, a):
        return round(hp / max(0.01, 1 - _armor_factor(a))) if hp else 0

    def _ehp_mag_val(hp, mr):
        return round(hp / max(0.01, 1 - mr / 100)) if hp else 0

    def _attack_type(npc):
        """Ranged attack capability → "Piercing", else "Default"."""
        cap = npc.get('AttackCapabilities', '')
        return 'Piercing' if 'RANGED' in cap else 'Default'

    def _attack_range_label(npc):
        # Just the number — no "Ближняя", no parentheses. The melee/ranged
        # marker is rendered separately as a glass icon badge in the cell.
        rng = _safe_int(npc.get('AttackRange'), 0)
        return _fmt_num(rng) if rng else ''

    def _is_ranged(npc):
        return 'RANGED' in npc.get('AttackCapabilities', '')

    # Hull → (collision size, bound radius). Values per Liquipedia/Unit_Size,
    # cross-checked in-game via cl_dumpentity (CCollisionProperty m_vecMaxs):
    # a neutral with no explicit BoundsHullName reports ±24 → DOTA_HULL_SIZE_HERO.
    HULL_BOUNDS = {
        'DOTA_HULL_SIZE_HERO':      (27, 24),
        'DOTA_HULL_SIZE_BIG_HERO':  (43, 40),
        'DOTA_HULL_SIZE_LARGE':     (41, 40),
        'DOTA_HULL_SIZE_REGULAR':   (36, 16),
        'DOTA_HULL_SIZE_SIEGE':     (40, 16),
        'DOTA_HULL_SIZE_SMALL':     (18, 8),
        'DOTA_HULL_SIZE_SMALLEST':  (4, 2),
        'DOTA_HULL_SIZE_HUGE':      (80, 80),
        'DOTA_HULL_SIZE_FILLER':    (112, 96),
        'DOTA_HULL_SIZE_TOWER':     (144, 144),
        'DOTA_HULL_SIZE_BARRACKS':  (160, 144),
    }
    # npc_dota_creep_neutral inherits HERO from npc_dota_units_base (the base
    # class is engine-internal / absent from npc_units.txt), so neutrals
    # without an explicit hull resolve to HERO. Verified in-game via
    # cl_dumpentity (CCollisionProperty m_vecMaxs) across 5 units: Kobold,
    # Ogre, Granite Golem, Black Dragon all = ±24 (HERO) regardless of model
    # scale; only skeleton_warrior overrides to SMALL (±8).
    # NOTE: HERO default is NEUTRAL-ONLY. Summons / non-neutral units have
    # different hulls — a future summons table must NOT reuse this default;
    # resolve their hull explicitly or per-unit.
    NEUTRAL_DEFAULT_HULL = 'DOTA_HULL_SIZE_HERO'
    # MovementTurnRate default from npc_dota_units_base = 0.5. 35/49 neutrals
    # explicitly override to 0.9 (so base ≠ 0.9); the 14 that don't are the
    # heavy/slow creeps (golems, frogs, ancients, thunder lizard, warpine) →
    # they inherit 0.5. Inferred (turn rate isn't readable via cl_dumpentity),
    # but the explicit-0.9 pattern + slow-creep grouping make it solid.
    NEUTRAL_DEFAULT_TURN_RATE = 0.5

    def _hull_for(npc):
        return (npc.get('BoundsHullName') or NEUTRAL_DEFAULT_HULL) if npc else None

    def _hull_collision(npc):
        h = _hull_for(npc)
        return HULL_BOUNDS.get(h, (None, None))[0] if h else None

    def _hull_bound(npc):
        h = _hull_for(npc)
        return HULL_BOUNDS.get(h, (None, None))[1] if h else None

    def _row_data(npc_key, createhero):
        """Compute the full set of overlay values for one creep. Returns
        a dict keyed by column id; missing keys render as blank."""
        npc = npc_data.get(npc_key, {}) if npc_key else {}
        u = units.get(npc_key, {}) if npc_key else {}
        # Prefer npc_units.txt; fall back to units.json for the basic fields.
        hp = _safe_int(npc.get('StatusHealth') or u.get('StatusHealth'))
        hp_regen = _safe_float(npc.get('StatusHealthRegen'))
        mp = _safe_int(npc.get('StatusMana') or u.get('StatusMana') or 0)
        mp_regen = _safe_float(npc.get('StatusManaRegen'))
        armor = _safe_float(npc.get('ArmorPhysical')
                             if 'ArmorPhysical' in npc
                             else u.get('ArmorPhysical', 0))
        magres = _safe_float(npc.get('MagicalResistance'), 0)  # default 0
        dmg_min = _safe_int(npc.get('AttackDamageMin') or u.get('AttackDamageMin'))
        dmg_max = _safe_int(npc.get('AttackDamageMax') or u.get('AttackDamageMax'))
        bat = _safe_float(npc.get('AttackRate') or u.get('AttackRate'))
        ats = _safe_int(npc.get('BaseAttackSpeed'), 100)
        ms = _safe_int(npc.get('MovementSpeed') or u.get('MovementSpeed'))
        gold_min = _safe_int(npc.get('BountyGoldMin'))
        gold_max = _safe_int(npc.get('BountyGoldMax'))
        xp = _safe_int(npc.get('BountyXP'))
        vis_day = npc.get('VisionDaytimeRange', '')
        vis_night = npc.get('VisionNighttimeRange', '')
        aggro = npc.get('AttackAcquisitionRange', '')
        ap = _safe_float(npc.get('AttackAnimationPoint'))
        _tr = npc.get('MovementTurnRate')
        turn_rate = (_safe_float(_tr) if _tr is not None
                     else (NEUTRAL_DEFAULT_TURN_RATE if npc else 0))
        projectile = _safe_int(npc.get('ProjectileSpeed'))
        collision = _hull_collision(npc)
        bound_radius = _hull_bound(npc)

        # Derived
        # Damage Factor formula: (0.06 × armor) / (1 + 0.06 × |armor|).
        # Positive armor reduces incoming damage; user wants absorption %.
        if armor != 0 or 'ArmorPhysical' in npc:
            factor = (0.06 * armor) / (1 + 0.06 * abs(armor))
            armor_pct = f'{round(factor * 100)}%'
            ehp_phys = round(hp / max(0.01, 1 - factor)) if hp else 0
        else:
            armor_pct, ehp_phys = '', 0
        ehp_mag = round(hp / max(0.01, 1 - magres / 100)) if hp else 0
        # Average damage rounded UP (12.5 → 13).
        dmg_avg = -(-(dmg_min + dmg_max) // 2) if (dmg_min or dmg_max) else 0
        # Average gold rounded UP (45.5 → 46).
        gold_avg = -(-(gold_min + gold_max) // 2) if gold_min or gold_max else 0
        t_per_attack = bat * 100 / ats if ats else bat

        # Abilities as (slug, dname) pairs (skip hidden markers/blanks).
        abilities = []
        for i in range(1, 6):
            slug = npc.get(f'Ability{i}', '').strip()
            if not slug or slug in ABILITY_SKIP:
                continue
            abilities.append((slug, _ability_dname(slug)))
        # Riverborn Aura is shared by every frog unit — pin it to the first
        # ability slot so the aura lines up in ONE column across all frogmen
        # (consistent column-highlight / sort). Their unique ability shifts to
        # slot 2. Stable sort keeps the rest of the order intact.
        abilities.sort(key=lambda sd: 0 if sd[0] == 'frogmen_riverborn_aura' else 1)
        abilities += [('', '')] * (3 - len(abilities)) if len(abilities) < 3 else []

        result = {
            'hp':            _fmt_num(hp) if hp else '',
            # Resolved creeps always show a regen value; "0" when the KV
            # has no StatusHealthRegen (e.g. Skeleton Warrior) instead of
            # a blank cell.
            'hp_regen':      (_fmt_regen(hp_regen) if hp_regen
                              else ('0' if npc else '')),
            'mp':            _fmt_num(mp) if mp else '-',
            # No mana → "-" (matches MP); mana but no regen → "0".
            'mp_regen':      (_fmt_regen(mp_regen) if mp_regen
                              else ('-' if (npc and not mp) else ('0' if npc else ''))),
            'armor':         _fmt_num(armor) if armor or 'ArmorPhysical' in npc else '',
            'armor_pct':     armor_pct,
            'ehp_phys':      _fmt_num(ehp_phys) if ehp_phys else '',
            'magres':        f'{int(magres)}%',
            'ehp_mag':       _fmt_num(ehp_mag) if ehp_mag else '',
            'dmg_min':       _fmt_num(dmg_min) if dmg_min else '',
            'dmg_max':       _fmt_num(dmg_max) if dmg_max else '',
            'dmg_avg':       _fmt_num(dmg_avg) if dmg_avg else '',
            'as':            _fmt_num(ats) if ats and npc else '',
            't_per_attack':  _fmt_num(round(t_per_attack, 2)) if t_per_attack else '',
            'bat':           _fmt_num(bat) if bat else '',
            'ms':            _fmt_num(ms) if ms else '',
            # Золото = average; min/max kept (hidden) for the extended toggle.
            'gold':          _fmt_num(gold_avg) if gold_avg else '',
            'gold_min':      _fmt_num(gold_min) if gold_min else '',
            'gold_max':      _fmt_num(gold_max) if gold_max else '',
            'xp':            _fmt_num(xp) if xp else '',
            'attack_range':  _attack_range_label(npc),
            'attack_range_ranged': _is_ranged(npc) if npc else False,
            'attack_type':   _attack_type(npc) if npc else '',
            'vision':        f'{vis_day}/{vis_night}' if vis_day and vis_night else '',
            'aggro':         aggro,
            'ap':            _fmt_num(ap) if ap else '',
            'turn_rate':     _fmt_num(turn_rate) if turn_rate else '',
            'collision_size': _fmt_num(collision) if collision else '',
            'bound_radius':  _fmt_num(bound_radius) if bound_radius else '',
            # Melee units have ProjectileSpeed 0 → show a dash, not blank.
            'projectile':    _fmt_num(projectile) if projectile else ('-' if npc else ''),
            'ability1':      abilities[0][1], 'ability1_slug': abilities[0][0],
            'ability2':      abilities[1][1], 'ability2_slug': abilities[1][0],
            'ability3':      abilities[2][1], 'ability3_slug': abilities[2][0],
            'camp':          ','.join(CREEP_CAMP.get((createhero or '').strip(), [])),
        }

        # Self-affecting auras: show "base (with-aura)" on the buffed stat.
        aura = AURA_SELF.get((createhero or '').strip())
        if aura:
            def _tot(base, op, val):
                return base + val if op == '+' else round(base * val)
            for stat, (op, val) in aura.items():
                if stat == 'dmg':
                    for dk, dv in (('dmg_min', dmg_min), ('dmg_max', dmg_max),
                                   ('dmg_avg', dmg_avg)):
                        if dv:
                            result[dk] = f'{_fmt_num(dv)} ({_fmt_num(_tot(dv, op, val))})'
                elif stat == 'hp_regen' and hp_regen:
                    result['hp_regen'] = f'{_fmt_regen(hp_regen)} ({_fmt_regen(_tot(hp_regen, op, val))})'
                elif stat == 'mp_regen' and mp_regen:
                    result['mp_regen'] = f'{_fmt_regen(mp_regen)} ({_fmt_regen(_tot(mp_regen, op, val))})'
                elif stat == 'magres':
                    result['magres'] = f'{int(magres)}% ({int(_tot(magres, op, val))}%)'
                elif stat == 'armor':
                    result['armor'] = f'{_fmt_num(armor)} ({_fmt_num(_tot(armor, op, val))})'
                elif stat == 'as' and ats:
                    result['as'] = f'{_fmt_num(ats)} ({_fmt_num(_tot(ats, op, val))})'
                elif stat == 'ms' and ms:
                    result['ms'] = f'{_fmt_num(ms)} ({_fmt_num(_tot(ms, op, val))})'
                elif stat == 'hp' and hp:
                    result['hp'] = f'{_fmt_num(hp)} ({_fmt_num(_tot(hp, op, val))})'
        return result

    def _resolve(createhero):
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

    def _esc(s):
        return (str(s).replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;'))

    def _attr_esc(s):
        """_esc + quote escape — safe to drop into a double-quoted attribute."""
        return _esc(s).replace('"', '&quot;')

    # ---- Per-column changelog value functions ----
    # Each maps (version, npc_key) → the column's display value for that patch
    # (or None when absent). _value_history diffs consecutive distinct values.
    # Raw columns read a single KV field; derived ones recompute from raw
    # fields exactly as _row_data does for the current patch.
    def _raw_vf(field):
        def f(version, npc_key):
            x = _raw_at(field, version, npc_key)
            return _fmt_num(x) if x is not None else None
        return f

    def _dmg_avg_vf(version, npc_key):
        mn = _raw_at('AttackDamageMin', version, npc_key)
        mx = _raw_at('AttackDamageMax', version, npc_key)
        if mn is None and mx is None:
            return None
        return _fmt_num(-(-((mn or 0) + (mx or 0)) // 2))  # round up

    def _gold_vf(version, npc_key):
        gmn = _raw_at('BountyGoldMin', version, npc_key)
        gmx = _raw_at('BountyGoldMax', version, npc_key)
        if gmn is None and gmx is None:
            return None
        return _fmt_num(-(-((gmn or 0) + (gmx or 0)) // 2))  # round up

    def _ehp_phys_vf(version, npc_key):
        hp = _raw_at('StatusHealth', version, npc_key)
        a = _raw_at('ArmorPhysical', version, npc_key)
        if not hp or a is None:
            return None
        return _fmt_num(_ehp_phys_val(hp, a))

    def _ehp_mag_vf(version, npc_key):
        hp = _raw_at('StatusHealth', version, npc_key)
        if not hp:
            return None
        mr = _raw_at('MagicalResistance', version, npc_key) or 0
        return _fmt_num(_ehp_mag_val(hp, mr))

    def _armor_pct_vf(version, npc_key):
        a = _raw_at('ArmorPhysical', version, npc_key)
        if a is None:
            return None
        return f'{round(_armor_factor(a) * 100)}%'

    def _t_per_attack_vf(version, npc_key):
        bat = _raw_at('AttackRate', version, npc_key)
        if not bat:
            return None
        ats = _raw_at('BaseAttackSpeed', version, npc_key) or 100
        return _fmt_num(round(bat * 100 / ats, 2)) if ats else _fmt_num(bat)

    def _vision_vf(version, npc_key):
        d = _raw_at('VisionDaytimeRange', version, npc_key)
        n = _raw_at('VisionNighttimeRange', version, npc_key)
        if d is None and n is None:
            return None
        return '{}/{}'.format(_fmt_num(d) if d is not None else '?',
                              _fmt_num(n) if n is not None else '?')

    def _hull_vf(idx):
        """History valuefn for hull-derived collision (idx 0) / bound (idx 1).
        Unit present that patch → hull (explicit or HERO default) → value."""
        def f(version, npc_key):
            if _raw_at('StatusHealth', version, npc_key) is None:
                return None  # unit doesn't exist this patch
            hull = _raw_at('BoundsHullName', version, npc_key) or NEUTRAL_DEFAULT_HULL
            v = HULL_BOUNDS.get(hull, (None, None))[idx]
            return _fmt_num(v) if v is not None else None
        return f

    def _projectile_vf(version, npc_key):
        s = _raw_at('ProjectileSpeed', version, npc_key)
        if s is None:
            return None
        return _fmt_num(s) if s else '-'

    def _turn_rate_vf(version, npc_key):
        if _raw_at('StatusHealth', version, npc_key) is None:
            return None  # unit doesn't exist this patch
        tr = _raw_at('MovementTurnRate', version, npc_key)
        return _fmt_num(tr if tr is not None else NEUTRAL_DEFAULT_TURN_RATE)

    def _abilities_at(version, npc_key):
        """Filtered ability dnames for a neutral at a patch (same filter as
        _row_data: skip hidden markers). Mirrors the displayed slot order."""
        out = []
        for i in range(1, 6):
            slug = _raw_at(f'Ability{i}', version, npc_key)
            if not slug or slug in ABILITY_SKIP:
                continue
            out.append(_ability_dname(slug))
        return out

    def _ability_slugs_at(version, npc_key):
        """Filtered ability SLUGS for a neutral at a patch (slot order)."""
        out = []
        for i in range(1, 6):
            slug = _raw_at(f'Ability{i}', version, npc_key)
            if not slug or slug in ABILITY_SKIP:
                continue
            out.append(slug)
        return out

    # npc_abilities field → friendly label for the changelog tooltip.
    ABIL_FIELD_LABEL = {
        'AbilityCooldown': 'Cooldown', 'AbilityManaCost': 'Manacost',
        'AbilityCastRange': 'Cast Range', 'AbilityCastPoint': 'Cast Point',
        'AbilityDamage': 'Damage', 'AbilityChannelTime': 'Channel Time',
        'AbilityDuration': 'Duration', 'AbilityUnitDamageType': 'Damage Type',
        'SpellImmunityType': 'Spell Immunity', 'SpellDispellableType': 'Dispellable',
    }
    # AbilityValues field (without the av_ prefix) → readable, semantic label.
    AV_LABEL = {
        'bonus_magical_armor': 'Magic Resistance',
        'bonus_magical_armor_creeps': 'Magic Resistance (creeps)',
        'attackspeed_slow': 'Attack Speed Slow', 'attack_slow_tooltip': 'Attack Speed Slow',
        'attackspeed_bonus': 'Attack Speed Bonus', 'bonus_attack_speed': 'Attack Speed',
        'bonus_aspd': 'Attack Speed', 'bonus_movement_speed': 'Move Speed',
        'movespeed': 'Move Speed', 'movespeed_slow': 'Move Speed Slow',
        'move_speed_penalty': 'Move Speed Penalty', 'net_speed': 'Net Speed',
        'damage_per_second': 'Damage / sec', 'cost_per_second': 'Cost / sec',
        'bonus_hp': 'Bonus HP', 'health': 'Health', 'hp_regen': 'HP Regen',
        'health_regen': 'HP Regen', 'mana_regen': 'Mana Regen',
        'armor_bonus': 'Bonus Armor', 'bonus_armor': 'Bonus Armor',
        'armor_reduction': 'Armor Reduction', 'armor_reduction_pct': 'Armor Reduction %',
        'crit_chance': 'Crit Chance', 'crit_mult': 'Crit Multiplier',
        'damage_percent': 'Damage %', 'damage_pct': 'Damage %',
        'bonus_damage_pct': 'Bonus Damage %', 'bonus_dmg_pct': 'Bonus Damage %',
        'building_damage_pct': 'Building Damage %', 'damage_percent_loss': 'Damage Loss %',
        'hero_stun_duration': 'Hero Stun Duration', 'non_hero_stun_duration': 'Creep Stun Duration',
        'hero_duration': 'Hero Duration', 'non_hero_duration': 'Creep Duration',
        'heal_amp': 'Heal Amplification', 'heal_pct': 'Heal %', 'lifesteal': 'Lifesteal',
        'bonus_cdr': 'Cooldown Reduction', 'gpm_aura': 'GPM Aura',
        'burn_damage': 'Burn Damage', 'burn_interval': 'Burn Interval', 'burn_amount': 'Burn Amount',
        'regen_reduction': 'Regen Reduction', 'purge_rate': 'Purge Rate',
        'bonus_outgoing_damage': 'Outgoing Damage', 'damage_absorb': 'Damage Absorb',
        'damage_reduction': 'Damage Reduction', 'initial_damage': 'Initial Damage',
        'damage_creeps': 'Damage (creeps)', 'projectile_speed': 'Projectile Speed',
        'projectile_count': 'Projectile Count', 'projectile_width': 'Projectile Width',
        'max_targets': 'Max Targets', 'bounces': 'Bounces', 'bounce_range': 'Bounce Range',
        'bounce_delay': 'Bounce Delay', 'radius': 'Radius', 'radius_start': 'Start Radius',
        'radius_end': 'End Radius', 'range': 'Range', 'distance': 'Distance',
        'health_threshold_pct': 'Health Threshold %', 'tick_interval': 'Tick Interval',
        'linger_duration': 'Linger Duration', 'int_multiplier': 'Int Multiplier',
        'damage_percent_close': 'Damage % (close)', 'damage_percent_mid': 'Damage % (mid)',
        'damage_percent_far': 'Damage % (far)', 'range_close': 'Range (close)',
        'range_mid': 'Range (mid)', 'range_far': 'Range (far)', 'jump_range': 'Jump Range',
        'jump_delay': 'Jump Delay', 'allow_multiple': 'Allow Multiple',
        'affected_by_aoe_increase': 'Affected by AoE', 'neutral_shared_cooldown': 'Shared Cooldown',
        'accuracy': 'Accuracy', 'distance': 'Distance', 'duration': 'Duration', 'damage': 'Damage',
    }
    # Token replacements for any av_ field not in AV_LABEL.
    AV_TOKEN = {
        'hp': 'HP', 'mp': 'Mana', 'aspd': 'Attack Speed', 'attackspeed': 'Attack Speed',
        'movespeed': 'Move Speed', 'dmg': 'Damage', 'pct': '%', 'cdr': 'Cooldown Reduction',
        'gpm': 'GPM', 'aoe': 'AoE', 'int': 'Int', 'str': 'Str', 'agi': 'Agi',
        'regen': 'Regen', 'pct.': '%',
    }
    # Enum/string fields — values are humanised (no slash/%, just "A → B").
    ABIL_ENUM_FIELDS = {'AbilityUnitDamageType', 'SpellImmunityType',
                        'SpellDispellableType'}
    _ENUM_PREFIXES = ('DAMAGE_TYPE_', 'SPELL_IMMUNITY_', 'SPELL_DISPELLABLE_')

    def _humanize_enum(val):
        s = str(val)
        for p in _ENUM_PREFIXES:
            if s.startswith(p):
                s = s[len(p):]
                break
        return s.replace('_', ' ').title()

    def _abil_field_label(fld):
        if fld in ABIL_FIELD_LABEL:
            return ABIL_FIELD_LABEL[fld]
        if fld.startswith('av_'):
            key = fld[3:]
            if key in AV_LABEL:
                return AV_LABEL[key]
            return ' '.join(AV_TOKEN.get(t, t.capitalize()) for t in key.split('_'))
        return fld

    # Fields where a DECREASE is the buff (green), like the changelog l=True.
    ABIL_LOWER_BETTER = {
        'AbilityCooldown', 'AbilityManaCost', 'AbilityCastPoint',
        'AbilityChannelTime',
    }

    def _abil_lower_better(fld):
        if fld in ABIL_LOWER_BETTER:
            return True
        if fld.startswith('av_'):
            n = fld[3:]
            # Slows/penalties are stored as negative numbers; a MORE-negative
            # value = stronger slow = buff for the caster, so a numeric drop
            # counts as buff.
            return ('cooldown' in n or 'manacost' in n or 'mana_cost' in n
                    or 'slow' in n or 'penalty' in n or 'reduction' in n)
        return False

    def _slash(s):
        """Per-level KV values are space-separated → show as 2/3/4/5, with
        each token trimmed (12.0 → 12) via _fmt_num."""
        return '/'.join(_fmt_num(t) for t in str(s).split())

    _FIRST_PATCH = _patches_chrono[0] if _patches_chrono else None

    def _ability_changelog(npc_key, slot):
        """Changelog for the ability cell at `slot`, tracked by the ability's
        IDENTITY (set membership) — NOT by slot position, so reordering slots
        (e.g. Thunderhide moving Slam slot 3→1) no longer reads as
        replaced/removed. Returns typed entries:
          (patch, date, 'A', name)            — this ability was added
          (patch, date, 'F', label, old, new) — value change (cooldown, …)
        The current ability occupying the slot is tracked across patches by
        whether it is among the neutral's abilities. Baseline (present at the
        FIRST tracked patch) emits nothing; an ability that first appears later
        (frogs in 7.38, or a rename) shows ADDED."""
        if not npc_key:
            return []
        # The ability currently shown in this slot (latest patch with the unit).
        cur_slug = None
        for v in reversed(_patches_chrono):
            if _raw_at('StatusHealth', v, npc_key) is None:
                continue
            slugs = _ability_slugs_at(v, npc_key)
            cur_slug = slugs[slot] if slot < len(slugs) else None
            break
        if not cur_slug:
            return []
        entries = []
        prev_present = False
        prev_fields = None
        started = False
        for v in _patches_chrono:
            if _raw_at('StatusHealth', v, npc_key) is None:
                continue  # unit absent this patch
            present = cur_slug in _ability_slugs_at(v, npc_key)
            fields = _abil_by_patch.get(v, {}).get(cur_slug, {}) if present else {}
            dt = PATCH_DATES.get(v, '')
            if not started:
                started = True
                if v == _FIRST_PATCH:
                    # data baseline — adopt silently (was there since 7.08)
                    prev_present, prev_fields = present, fields
                    continue
                # else first appearance is mid-history → fall through to ADDED
            if present and not prev_present:
                entries.append((v, dt, 'A', _ability_dname(cur_slug)))
            if present and prev_present and prev_fields:
                for fld, val in fields.items():
                    old = prev_fields.get(fld)
                    if old is None or old == val:
                        continue
                    if fld in ABIL_ENUM_FIELDS:
                        of_, nf_, pol = _humanize_enum(old), _humanize_enum(val), 'hi'
                    else:
                        of_, nf_ = _slash(old), _slash(val)
                        pol = 'lo' if _abil_lower_better(fld) else 'hi'
                    if of_ == nf_:   # no-op once formatted (e.g. "6.0"→"6")
                        continue
                    entries.append((v, dt, 'F', _abil_field_label(fld), of_, nf_, pol))
            prev_present, prev_fields = present, fields
        return entries

    COL_HIST = {
        'hp':            _raw_vf('StatusHealth'),
        'hp_regen':      _raw_vf('StatusHealthRegen'),
        'mp':            _raw_vf('StatusMana'),
        'mp_regen':      _raw_vf('StatusManaRegen'),
        'armor':         _raw_vf('ArmorPhysical'),
        'magres':        _raw_vf('MagicalResistance'),
        'as':            _raw_vf('BaseAttackSpeed'),
        'bat':           _raw_vf('AttackRate'),
        'ms':            _raw_vf('MovementSpeed'),
        'xp':            _raw_vf('BountyXP'),
        'aggro':         _raw_vf('AttackAcquisitionRange'),
        'attack_range':  _raw_vf('AttackRange'),
        'dmg_avg':       _dmg_avg_vf,
        'dmg_min':       _raw_vf('AttackDamageMin'),
        'dmg_max':       _raw_vf('AttackDamageMax'),
        'gold':          _gold_vf,
        'gold_min':      _raw_vf('BountyGoldMin'),
        'gold_max':      _raw_vf('BountyGoldMax'),
        'ehp_phys':      _ehp_phys_vf,
        'ehp_mag':       _ehp_mag_vf,
        'armor_pct':     _armor_pct_vf,
        't_per_attack':  _t_per_attack_vf,
        'vision':        _vision_vf,
        'ap':            _raw_vf('AttackAnimationPoint'),
        'turn_rate':     _turn_rate_vf,
        'bound_radius':  _hull_vf(1),
        'projectile':    _projectile_vf,
        'collision_size': _hull_vf(0),
    }

    # Ability cells use a richer changelog (presence + value changes) that
    # returns (patch, date, ov, nv) entries directly, not a per-patch value.
    COL_CHANGELOG = {
        'ability1': lambda k: _ability_changelog(k, 0),
        'ability2': lambda k: _ability_changelog(k, 1),
        'ability3': lambda k: _ability_changelog(k, 2),
    }

    # ---- Read CSV ----
    csv_rows = list(_csv.reader(open(csv_path, encoding='utf-8')))
    body_rows = csv_rows[1:]

    # ---- Column structure ----
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
            ('t_per_attack', 'Time to hit',      'std'),
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

    # ---- Build rows ----
    rendered = []
    current_lvl = ''
    csv_level_pointer = ''  # tracks the latest Ур. seen, INCLUDING on
                              # rows we later skip (a hidden row can carry
                              # a level marker that the next non-hidden
                              # row inherits — e.g. the 'ranged' lane
                              # creep sits on row '5', so we must record
                              # level 5 even though we drop the row).
    # CSV column index of "Тип атаки" — the curated attack type. The game
    # files don't expose CombatClassAttack for neutrals, so the CSV is the
    # authoritative source (ranged ≠ Pierce reliably, e.g. Dark Troll
    # Summoner is ranged but deals "Обычный").
    try:
        CSV_ATK_IDX = next(i for i, h in enumerate(csv_rows[0])
                           if 'Тип атаки' in h)
    except StopIteration:
        CSV_ATK_IDX = None

    for r in body_rows:
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

        npc_key = _resolve(createhero)
        if npc_key:
            display_name = CREEP_DISPLAY_NAMES.get(
                npc_key,
                npc_key.replace('npc_dota_neutral_', '').replace('_', ' ').title()
            )
            icon_path = f'icons/units/{npc_key}.png'
            data = _row_data(npc_key, createhero)
        else:
            display_name = createhero.replace('_', ' ').title()
            icon_path = None
            data = _row_data(None, createhero)

        is_break = (level_for_row != current_lvl)
        current_lvl = level_for_row

        data['lvl'] = level_for_row  # always set; rowspan handles merging
        data['createhero'] = createhero
        data['name'] = display_name
        data['icon'] = icon_path
        # Override the heuristic attack type with the curated CSV value
        # (strip trailing */** footnote markers). Falls back to the
        # heuristic when the CSV cell is blank.
        if CSV_ATK_IDX is not None and CSV_ATK_IDX < len(padded):
            csv_atk = padded[CSV_ATK_IDX].strip().rstrip('*').strip()
            csv_atk = {'Обычный': 'Default',
                       'Проникающий': 'Piercing'}.get(csv_atk, csv_atk)
            if csv_atk:
                data['attack_type'] = csv_atk
        rendered.append({'data': data, 'tier_break': is_break,
                          'level': level_for_row, 'npc_key': npc_key})
    # No rowspan merge: every row carries its own level cell so the table
    # can be re-sorted by any column. scripts.js collapses repeated level
    # numbers in the current row order (showing the number once per run +
    # a divider) to keep the grouped look in the default/level-sorted view.

    # ---- HTML emission ----
    # Materials sub-tabs are embedded directly into the site header now
    # (subtabs_active), so there's no separate strip below it to freeze on
    # scroll. Build one nav per page with the correct active sub-tab.
    # subnav_in_header=False: the sub-tab bar is placed INSIDE the scroll box
    # (below) so it scrolls away with the table like Mana Items, instead of
    # staying pinned under the nav.
    nav = _site.render_top_nav('materials', _latest_href(),
                               patch_context=False, subtabs_active='creeps',
                               subnav_in_header=False)
    nav_ua = _site.render_top_nav('materials', _latest_href(),
                                  patch_context=False, subtabs_active='abilities',
                                  subnav_in_header=False)
    subnav_creeps = _site.render_materials_subnav('creeps')
    subnav_abilities = _site.render_materials_subnav('abilities')
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

    CAMP_RANK = {'small': 1, 'mid': 2, 'big': 3, 'ancient': 4}

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
            return (f'{_esc(main)}<span class="th-sub">{_esc(sub)}</span>')
        return _esc(label)

    # Header: each sortable th carries data-col (key) and data-idx (its
    # body-cell index, so the sort logic survives the colspan on Юнит).
    # The "Юнит" header spans the icon + name columns (colspan=2) so it
    # reads as centered over the whole unit-identity block; the separate
    # icon <th> is dropped.
    col_keys = [k for k, _ in COLUMNS]
    name_idx = col_keys.index('name')
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
    thead_cells = ''.join(thead_list)

    # Super-category row: one cell per category, colspan = its leaf columns.
    # Each category has at least one Standard column, so the cell always shows;
    # when Expanded columns under it are hidden, the cell shrinks naturally.
    cat_cells = ''.join(
        f'<th class="cat-head cat-{_CAT_SLUG.get(cat, "x")}" '
        f'data-cat="{_CAT_SLUG.get(cat, "x")}" colspan="{len(cols)}">{_esc(cat)}</th>'
        for cat, cols in CATEGORIES
    )

    _ABIL_ICON_DIR = _os.path.join(_HERE, 'icons', 'abilities')

    def _has_abil_icon(slug):
        return bool(slug) and _os.path.exists(
            _os.path.join(_ABIL_ICON_DIR, slug + '.png'))

    def _cell_inner(k, v, d):
        """Inner HTML for a data cell. Attack Range → number + glass badge.
        Ability cells → the ability ICON (changelog style, smaller); the name
        is shown on hover. Falls back to the name text when no icon exists."""
        if k == 'camp':
            if not v:
                return '<span class="ua-dash">—</span>'
            imgs = []
            for t in v.split(','):
                label = CAMP_LABEL.get(t, t)
                imgs.append(
                    f'<img class="camp-ico" src="icons/camps/creepcamp_{t}.png" '
                    f'alt="{_esc(label)}" title="{_esc(label)}" loading="lazy">')
            return ''.join(imgs)
        if k == 'attack_range' and v:
            typ = 'ranged' if d.get('attack_range_ranged') else 'melee'
            # Fixed-width number keeps every badge at the same x position.
            tip = 'Ranged' if typ == 'ranged' else 'Melee'
            return (f'<span class="atk-num">{_esc(v)}</span>'
                    f'<span class="atk-badge atk-{typ}" title="{tip}">'
                    f'<img src="icons/ui/atk_{typ}.png" alt="{tip}" '
                    f'title="{tip}" loading="lazy"></span>')
        if k in ('ability1', 'ability2', 'ability3'):
            if not v:
                return '<span class="ua-dash">—</span>'
            slug = d.get(k + '_slug', '')
            if _has_abil_icon(slug):
                img = (f'<img class="abil-ico" src="icons/abilities/{slug}.png" '
                       f'alt="{_esc(v)}" loading="lazy">')
                if slug in AUTOCAST_ABILITIES:
                    # Thin "snake" stroke that crawls along the icon's rounded
                    # frame at constant speed (incl. corners) — SVG dash offset
                    # animation. pathLength=100 normalises the perimeter so the
                    # dash gap loops seamlessly.
                    # Phase-locked strokes (shared offset animation) forming one
                    # fuzzy comet: a wide blurred aura (fluff), a bright body,
                    # stepped tail segments that fade toward the tail tip, and a
                    # cluster of tiny dots riding along (pollen). Head leads at
                    # the high end of the painted range; the tail (low end)
                    # fades out near its tip.
                    inner = (f'<span class="abil-ico-wrap abil-autocast">'
                             f'{img}{_autocast_snake_svg()}</span>')
                else:
                    inner = img
            else:
                inner = _esc(v)   # no icon on CDN → keep the name text
            # Clicking an ability jumps to its (unit, ability) row on the Unit
            # Abilities page. For abilities that share a single canonical row
            # across units (e.g. Riverborn Aura), route to that canonical unit.
            ch = (d.get('createhero') or '').strip()
            ua_canonical = {'frogmen_riverborn_aura': 'tad'}
            target_ch = ua_canonical.get(slug, ch)
            return (f'<a class="abil-link" '
                    f'href="neutral_abilities.html#{target_ch}-{slug}">{inner}</a>'
                    if slug else inner)
        return _esc(v) if v else '<span class="ua-dash">—</span>'

    body_parts = []
    for row in rendered:
        d = row['data']
        tr_cls = ' class="tier-break"' if row['tier_break'] else ''
        cells = []
        for k, _ in COLUMNS:
            v = d.get(k, '')
            if k == 'lvl':
                # Per-row level cell (no rowspan). data-lvl lets scripts.js
                # collapse repeated numbers within a run and draw a divider
                # at group starts, in whatever order the table is sorted.
                cells.append(
                    f'<td class="lvl-cell {_col_cls(k)}" '
                    f'data-lvl="{_esc(v)}">{_esc(v)}</td>'
                )
            elif k == 'icon':
                if v:
                    # Clicking the icon copies the dev-console spawn command
                    # "-createhero <name> neutral" to the clipboard (handled
                    # in scripts.js via the data-cmd attribute).
                    cmd = f'-createhero {d.get("createhero", "")} neutral'
                    cells.append(
                        f'<td class="creep-icon-cell {_col_cls(k)}">'
                        f'<img class="creep-copy" src="{_esc(v)}" alt="" '
                        f'loading="lazy" data-cmd="{_esc(cmd)}" '
                        f'title="{_esc(cmd)}" '
                        f'onerror="this.style.visibility=\'hidden\'"></td>'
                    )
                else:
                    cells.append(f'<td class="creep-icon-cell {_col_cls(k)}"></td>')
            elif k in COL_HIST or k in COL_CHANGELOG:
                # Stat / ability cell carries its full change history as a
                # compact data attribute (patch|date|old|new;...) — scripts.js
                # renders a changelog tooltip on hover. Only emitted when the
                # unit actually has recorded changes for that column.
                extra = ''
                cls = _col_cls(k, v)
                if k in COL_CHANGELOG:
                    # Typed entries (variable length): patch|date|kind|...parts
                    hist = COL_CHANGELOG[k](row.get('npc_key'))
                    payload = ';'.join('|'.join(str(x) for x in e) for e in hist)
                else:
                    # Stat value change → 'V' kind: patch|date|V|old|new|pol.
                    # BAT / time-to-hit are buffs when they DROP (lower = better).
                    hist = _value_history(row.get('npc_key'), COL_HIST[k])
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
                    extra += f' data-hist="{_esc(payload)}"'
                    cls += ' has-history'
                # Ability cells carry the name for the hover tooltip header.
                if k in COL_CHANGELOG and v:
                    extra += f' data-name="{_esc(v)}"'
                cells.append(
                    f'<td class="{cls}"{_sort_attr(k, v)}{extra}>{_cell_inner(k, v, d)}</td>'
                )
            else:
                cells.append(f'<td class="{_col_cls(k, v)}"{_sort_attr(k, v)}>{_cell_inner(k, v, d)}</td>')
        rid = f' id="unit-{_esc((d.get("createhero") or "").strip())}"'
        attack_type = 'ranged' if d.get('attack_range_ranged') else 'melee'
        body_parts.append(
            f'<tr{rid} data-attack-type="{attack_type}"{tr_cls}>'
            f'{"".join(cells)}</tr>'
        )

    html = (
        '<!DOCTYPE html>\n'
        '<html lang="ru">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<title>SIKLE | Neutral Stats</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={ASSET_VERSION}">\n'
        '</head>\n'
        '<body>\n'
        f'{nav}\n'
        '<div class="container creeps-page">\n'
        # Overlay frame outlining the pinned identity block during scroll.
        # Lives OUTSIDE .creeps-scroll (which scrolls) so it never hits the
        # Chrome bug where box-shadow/border on position:sticky cells fails
        # to repaint mid-scroll. scripts.js positions + toggles it.
        '<div class="sticky-frame" aria-hidden="true"></div>\n'
        '<div class="sticky-frame-top" aria-hidden="true"></div>\n'
        '<div class="creeps-scroll">\n'
        # Sub-tab bar + blurb + toolbar all live INSIDE the scroll box (above
        # the table) so they scroll away with the page just like the Mana Items
        # layout — only the site nav and the sticky table headers remain pinned.
        # They're sticky-left so they stay put during horizontal scroll.
        f'{subnav_creeps}'
        '<p class="mr-blurb inbox-bar">Stats and abilities of every neutral '
        'camp creep in Dota 2 — pulled from the current patch\'s KV files. '
        'Hover any cell with the dotted underline to see its change history '
        'across patches. Click a unit icon to copy its demo-mode spawn command '
        '(e.g. <code>-createhero tunneler neutral</code>) to the clipboard. '
        'Click a column header to sort. The '
        '<strong>View</strong> toggle switches between <em>Standard</em> '
        '(essentials only) and <em>Expanded</em> (every numeric column — EHP, '
        'armour %, gold range, collision, projectile speed, etc.).</p>\n'
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
        '<table class="creeps-table mode-standard">\n'
        f'<thead><tr class="cat-row">{cat_cells}</tr>'
        f'<tr class="col-row">{thead_cells}</tr></thead>\n'
        f'<tbody>\n{chr(10).join(body_parts)}\n</tbody>\n'
        '</table>\n'
        '</div>\n'
        '</div>\n'
        f'<script src="src/scripts.js?v={ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n'
    )
    with open('neutral_stats.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  -> neutral_stats.html: {len(html):,} bytes")
    # Backward-compat redirects: any old bookmark / external link to the former
    # /neutral_creeps.html, /creeps.html or /materials.html bounces to
    # /neutral_stats.html. Removed
    # once we're confident no traffic references the old URLs.
    for _old in ('neutral_creeps.html', 'creeps.html', 'materials.html'):
        with open(_old, 'w', encoding='utf-8') as f:
            f.write(
                '<!DOCTYPE html><html><head><meta charset="UTF-8">'
                '<meta http-equiv="refresh" content="0; url=neutral_stats.html">'
                '<link rel="canonical" href="neutral_stats.html">'
                '<title>Sloppy — moved</title></head><body>'
                '<p>This page moved to '
                '<a href="neutral_stats.html">neutral_stats.html</a>.</p>'
                '</body></html>'
            )

    # ---- Neutral Abilities companion page ----
    # One row per (creep, ability), mirroring the Creeps Table's Lvl + Unit
    # identity columns (Unit shows just the hover-zoom icon). Property columns
    # come from the CURRENT patch's npc_abilities.json (av_* + standard KV
    # fields) so a patch that changes an ability updates here automatically.
    # Effect / Effect 2 / Effect 3 and Stackable aren't present in our data
    # files, so they render blank (would need a manual/external source).
    # Current patch — pick the chronologically newest version with extracted
    # ability data. `_patches_chrono` is already sorted via `_ver_key`; fall
    # back to '7.41c' if it's empty (e.g. clean checkout without stats dump).
    CUR_VER = next((v for v in reversed(_patches_chrono)
                    if v in _abil_by_patch), '7.41c')
    print(f"  neutral_abilities source patch: {CUR_VER}")
    cur_ab = _abil_by_patch.get(CUR_VER, {})
    DMG_TYPE = {'DAMAGE_TYPE_MAGICAL': 'Magical', 'DAMAGE_TYPE_PHYSICAL': 'Physical',
                'DAMAGE_TYPE_PURE': 'Pure', 'DAMAGE_TYPE_HP_REMOVAL': 'HP Removal'}
    DISPEL = {'SPELL_DISPELLABLE_YES': 'Yes', 'SPELL_DISPELLABLE_YES_STRONG': 'Strong only',
              'SPELL_DISPELLABLE_NO': 'No'}
    # Aura Stack column: which auras stack with another copy of the same aura.
    # Only these stack (green check); other auras don't (red x); non-auras get
    # a dash. Rally has no 'aura' in its slug but behaves as a stacking aura.
    AURA_STACK_YES = {'black_dragon_dragonhide_aura', 'hill_troll_rally'}
    # Manual dispellable values for abilities whose KV lacks SpellDispellableType
    # (dispellability lives in their modifier/code). User-supplied.
    DISPEL_MANUAL = {
        'berserker_troll_break': 'Yes',        # Break
        'fel_beast_haunt': 'Yes',              # Vex
        'dark_troll_warlord_ensnare': 'Yes',   # Ensnare
        'ogre_magi_frost_armor': 'Yes',        # Ice Armor
        'furbolg_enrage_attack_speed': 'Yes',  # Death Throe: Rush
        'furbolg_enrage_damage': 'Yes',        # Death Throe: Power
        'warpine_raider_seed_shot': 'Yes',     # Seed Shot
        'spawnlord_master_freeze': 'Yes',      # Petrify
        'kobold_disarm': 'Yes',                # Steal Weapon
        'giant_wolf_intimidate': 'Yes',        # Intimidate
        'harpy_scout_take_off': 'No',          # Take Off
        'black_dragon_fireball': 'No',         # Fireball
    }
    # Single merged Type column — fully hand-curated (replaces the old Type +
    # Damage Type pair). Keyed by ability slug; anything not listed → dash.
    TYPE_MANUAL = {
        'enraged_wildkin_tornado': 'Active, Magic Damage',
        'kobold_tunneler_prospecting': 'Passive, Buff Aura',
        'kobold_disarm': 'Passive, Debuff',
        'hill_troll_rally': 'Passive, Buff Aura',
        'berserker_troll_break': 'Passive, Debuff',
        'gnoll_assassin_envenomed_weapon': 'Passive, HP Removal Damage',
        'fel_beast_haunt': 'Active, Debuff',
        'ogre_bruiser_ogre_smash': 'Active, Magic Damage',
        'kobold_taskmaster_speed_aura': 'Passive, Buff Aura',
        'forest_troll_high_priest_heal_amp_aura': 'Passive, Buff Aura',
        'mudgolem_cloak_aura': 'Passive, Buff Aura',
        'frogmen_riverborn_aura': 'Passive, Buff Aura',
        'giant_wolf_intimidate': 'Active, Debuff',
        'dark_troll_warlord_ensnare': 'Active, Debuff',
        'ghost_frost_attack': 'Passive, Debuff',
        'harpy_storm_chain_lightning': 'Active, Magic Damage',
        'black_drake_magic_amplification_aura': 'Passive, Debuff Aura',
        'spawnlord_aura': 'Passive, Buff Aura',
        'ogre_magi_frost_armor': 'Active, Buff',
        'mud_golem_hurl_boulder': 'Active, Magic Damage',
        'frogmen_arm_of_the_deep': 'Active, Magic Damage',
        'frogmen_tendrils_of_the_deep': 'Active, Magic Damage',
        'frogmen_water_bubble_small': 'Active, Buff',
        'frogmen_water_bubble_medium': 'Active, Buff',
        'frogmen_water_bubble_large': 'Active, Buff',
        'centaur_khan_endurance_aura': 'Passive, Buff Aura',
        'furbolg_enrage_attack_speed': 'Passive, Buff',
        'satyr_soulstealer_mana_burn': 'Active, Magic Damage',
        'forest_troll_high_priest_mana_aura': 'Passive, Buff Aura',
        'alpha_wolf_critical_strike': 'Passive, Physical Damage',
        'alpha_wolf_command_aura': 'Passive, Buff Aura',
        'centaur_khan_war_stomp': 'Active, Magic Damage',
        'polar_furbolg_ursa_warrior_thunder_clap': 'Active, Magic Damage',
        'furbolg_enrage_damage': 'Passive, Buff',
        'enraged_wildkin_toughness_aura': 'Passive, Buff Aura',
        'warpine_raider_seed_shot': 'Active, Magic Damage',
        'frogmen_congregation_of_the_deep': 'Active, Magic Damage',
        'ancient_rock_golem_weakening_aura': 'Passive, Debuff Aura',
        'frostbitten_golem_time_warp_aura': 'Passive, Buff Aura',
        'big_thunder_lizard_wardrums_aura': 'Passive, Buff Aura',
        'satyr_hellcaller_shockwave': 'Active, Magic Damage',
        'satyr_hellcaller_unholy_aura': 'Passive, Buff Aura',
        'spawnlord_master_stomp': 'Active, Physical Damage',
        'spawnlord_master_freeze': 'Active, Physical Damage',
        'black_dragon_fireball': 'Active, Magic Damage',
        'black_dragon_splash_attack': 'Passive, Physical Damage',
        'black_dragon_dragonhide_aura': 'Passive, Buff Aura',
        'granite_golem_hp_aura': 'Passive, Buff Aura',
        'big_thunder_lizard_slam': 'Active, Magic Damage',
        'big_thunder_lizard_frenzy': 'Active, Buff',
        'ice_shaman_incendiary_bomb': 'Active, Magic Damage',
        'dark_troll_warlord_raise_dead': 'Active, Summon',
    }
    # (legacy) Damage Type curation — no longer rendered as its own column.
    DMGTYPE_MANUAL = {
        'gnoll_assassin_envenomed_weapon': 'HP Removal',
        'spawnlord_master_stomp': 'Physical',      # Desecrate
        'spawnlord_master_freeze': 'Physical',     # Petrify
        'black_dragon_splash_attack': 'Physical',
        'alpha_wolf_critical_strike': 'Physical',
        'enraged_wildkin_tornado': 'Magical',
        'ogre_bruiser_ogre_smash': 'Magical',
        'harpy_storm_chain_lightning': 'Magical',
        'mud_golem_hurl_boulder': 'Magical',
        'frogmen_arm_of_the_deep': 'Magical',
        'frogmen_tendrils_of_the_deep': 'Magical',
        'satyr_soulstealer_mana_burn': 'Magical',
        'centaur_khan_war_stomp': 'Magical',
        'polar_furbolg_ursa_warrior_thunder_clap': 'Magical',
        'warpine_raider_seed_shot': 'Magical',
        'frogmen_congregation_of_the_deep': 'Magical',
        'satyr_hellcaller_shockwave': 'Magical',
        'black_dragon_fireball': 'Magical',
        'big_thunder_lizard_slam': 'Magical',
        'ice_shaman_incendiary_bomb': 'Magical',
    }

    def _f1(val):
        s = str(val).strip()
        return s.split()[0] if s else ''

    def _prog(val):
        """Full per-level progression as '40/36/32/26'; trims trailing .0."""
        out = []
        for t in str(val).split():
            try:
                f = float(t)
                out.append(str(int(f)) if f == int(f) else str(f))
            except ValueError:
                out.append(t)
        return '/'.join(out)

    # Manual columns not present in our data files (effect text + aura
    # stackability). Filled by hand from the legacy creep-spreadsheet
    # (Эффект / Второй эффект / Третий эффект columns); keyed by ability
    # slug. Anything here overrides the auto-derived blanks.
    _DMG_NUM_RE = re.compile(r'[\d./\-–]*\d+[\d./\-–]*')

    def _dmg_color_html(text: str) -> str:
        """Wrap numeric runs in `.dmg-num` so the damage-type colour paints
        only the numbers, not the words ("per sec.", "(юниты)", "+ 250% Int")."""
        return _DMG_NUM_RE.sub(
            lambda m: f'<span class="dmg-num">{m.group()}</span>', text)

    def _val_qhint(text: str, tip: str) -> str:
        """Raw-HTML cell value: text + framed `?` badge with tooltip. Generic
        version (no number-colour wrap) — for non-Damage columns like Duration."""
        tip_esc = _esc(tip)
        return ('\x01<span class="cell-wrap">' + _esc(text) +
                f'<span class="qhint" tabindex="0" role="button" '
                f'aria-label="{tip_esc}" data-tooltip="{tip_esc}">?</span>'
                '</span>')

    def _dmg_qhint(text: str, tip: str) -> str:
        """Raw-HTML damage cell: value + framed `?` badge with tooltip."""
        tip_esc = _esc(tip)
        return ('\x01<span class="dmg-wrap">' + _dmg_color_html(text) +
                f'<span class="qhint" tabindex="0" role="button" '
                f'aria-label="{tip_esc}" data-tooltip="{tip_esc}">?</span>'
                '</span>')

    ABIL_MANUAL = {
        'enraged_wildkin_tornado': {
            # Wildkin's `enraged_wildkin_tornado` is only the CAST. The actual
            # tornado unit's damage/AoE live in `tornado_tempest`, which isn't
            # in our extracted KV — fill from the legacy sheet by hand.
            'damage': _dmg_qhint(
                '15-45 per sec.',
                "Depends on the proximity to the Tornado's epicenter"),
            'aoe': '150–600',
            'duration': _val_qhint(
                '10 (15)',
                "Channeling duration is 10 seconds + 5 if it's ended or cancelled"),
            'as_effect': '-15%', 'ms_effect': '-15%',
            'effect': 'AoE damage',
            'effect2': '300/300 vision',
            'effect3': 'Slow'},
        'kobold_tunneler_prospecting': {
            'effect': '+20/25/30/40 gold per minute'},
        'kobold_disarm': {
            'effect': 'Disarms 1 target', 'effect2': 'Requires 3 attacks'},
        'hill_troll_rally': {
            'effect': '+2 attack damage to allies'},
        'berserker_troll_break': {
            'effect': 'Break on 1 target'},
        'gnoll_assassin_envenomed_weapon': {
            # HP Removal is rare enough on neutrals to flag in the cell itself
            # (it bypasses magic immunity, ignores magic resist, can't kill etc).
            'damage': _dmg_qhint('0/20/40/80 per sec.', 'HP Removal damage type'),
            'duration': _val_qhint(
                '2 or 20', 'Lasts much longer on creeps (20)'),
            'effect': 'Damage over time',
            'effect2': 'HP regeneration reduction: 75/80/85/90%'},
        'fel_beast_haunt': {
            'effect': 'Silences 1 target',
            'effect2': 'Projectile Speed is 500/600/700/800'},
        'harpy_scout_take_off': {
            # Toggle ability: 20 to activate, then 4% of max MP per second
            # while active (av_cost_per_second:"4").
            'manacost': _val_qhint(
                '20 + 4%',
                'Activation cost 20, plus 4% of max MP per second while active'),
            'ms_effect': _val_qhint(
                '-50/-40/-30/-10%',
                'The unit itself is slowed while the ability is active'),
            'effect': 'Gives flying movement with 1200/800 vision',
            'effect2': 'Slows itself while active'},
        'ogre_bruiser_ogre_smash': {
            # av_damage_pct:"8" — bonus 8% of target's current HP, not surfaced
            # in any other column.
            'damage': _dmg_qhint(
                '200/250/300/400 + 8%',
                "Adds 8% of the target's current HP to the damage"),
            'effect': 'AoE damage', 'effect2': 'Stun'},
        'kobold_taskmaster_speed_aura': {
            'ms_effect': '+12/13/14/16%',
            'effect': 'Movement speed bonus'},
        'forest_troll_high_priest_heal_amp_aura': {
            'effect': 'Increases healing on allies by 15%'},
        'forest_troll_high_priest_heal': {
            'effect': 'Heals +100 HP'},
        'mudgolem_cloak_aura': {
            'effect': 'Heroes magic resistance bonus: +10/12/14/16%',
            'effect2': 'Creeps magic resistance bonus: +20/24/28/32%'},
        'frogmen_riverborn_aura': {
            'ms_effect': '+10/12/14/16%',
            'effect': 'Outgoing damage +10/12/14/16%'},
        'satyr_trickster_purge': {
            # Slow decays from -50% to -10% over 5 seconds; not in any av_* field.
            'ms_effect': _val_qhint(
                '-50% to -10%',
                'Movement slow decays by 10% each second over 5 seconds'),
            'effect': 'Dispel', 'effect2': 'Movement slow'},
        'giant_wolf_intimidate': {
            'effect': 'Reduces attack damage by 60%'},
        'dark_troll_warlord_ensnare': {
            # No entry in 7.41c npc_abilities.json — fill from in-game tooltip.
            'manacost': '75', 'cooldown': '15', 'duration': '1.75',
            'cast_range': '550/625/700/825',
            'effect': 'Roots the target', 'effect2': 'True Sight on the target'},
        'ghost_frost_attack': {
            'effect': 'Slows both attack and movement speed'},
        'harpy_storm_chain_lightning': {
            # KV has AbilityManaCost 60, but in-game tooltip / user verifies 50.
            'manacost': '50',
            # av_initial_damage carries the bounce damage; av_damage_percent_loss
            # is the per-bounce falloff (25/20/15/10%).
            'damage': _dmg_qhint(
                '120/170/220/270',
                'Each bounce reduces damage by 25/20/15/10%'),
            'cast_range': _val_qhint('900', 'Bounces range is 500'),
            'effect': 'Damage to 4 targets'},
        'black_drake_magic_amplification_aura': {
            'effect': _val_qhint(
                'Outgoing spell damage: 5/6/7/9%',
                "Amplifies any damage type if it's spell damage")},
        'spawnlord_aura': {
            'effect': '+9/10/11/12% lifesteal',
            'effect2': '+9/10/11/12 HP regen'},
        'ogre_magi_frost_armor': {
            # Slug missing from 7.41c npc_abilities.json — fill from in-game.
            'manacost': '40', 'cooldown': '5', 'duration': '45',
            'cast_range': '800',
            'as_effect': '-22/24/26/30%', 'ms_effect': '-22/24/26/30%',
            'effect': '+4/5/6/8 armor',
            'effect2': _val_qhint(
                'Shield slows attackers on hit',
                'The slow applies to towers as well')},
        'mud_golem_hurl_boulder': {
            # 75 hero / 150 creep; pretty form with hint icon for the split.
            'damage': _dmg_qhint(
                '75 or 150', 'Deals double the damage to creeps (150)'),
            'effect': 'Single target stun'},
        'mud_golem_rock_destroy': {
            # av_radius describes the death stun (internal tech) — blank to
            # match the old sheet. av_duration in KV is 2 (the death stun),
            # but the SHARD LIFETIME the user cares about is 60s.
            'aoe': '', 'duration': '60',
            # Property 1: spawns-on-death + qhint with shard tier stats. Each
            # row of the qhint is its own .qh-line so the tooltip renders
            # multiline. Marked `leveled` because the qhint shows progressions.
            'effect': (
                '\x01<span class="cell-wrap">'
                'Spawns Golems on death 2/2/3/3'
                '<span class="qhint" tabindex="0" role="button" '
                'aria-label="Shard stats per tier" data-tooltip="'
                '&lt;div class=&quot;qh-line&quot;&gt;HP = 250/280/310/370&lt;/div&gt;'
                '&lt;div class=&quot;qh-line&quot;&gt;Attack damage = 12/16/20/28&lt;/div&gt;'
                '&lt;div class=&quot;qh-line&quot;&gt;Quantity = 2/2/3/3&lt;/div&gt;'
                "&lt;div class=&quot;qh-line&quot;&gt;Hurl Boulder is the same as Mud Golem's&lt;/div&gt;"
                '&lt;div class=&quot;qh-line&quot;&gt;When Devoured, Doom will also spawn 2/2/3/3 small Golems but with his own model&lt;/div&gt;'
                '">?</span></span>'),
            'effect2': (
                '\x01Golems have <a class="ua-inline-link" '
                'href="neutral_abilities.html#mud-mud_golem_hurl_boulder">'
                'Hurl Boulder</a>'),
        },
        'frogmen_arm_of_the_deep': {
            # av_radius missing in KV; the actual stun radius is the
            # av_projectile_width (100). Tentacles also extend +100 further.
            'aoe': '100',
            'cast_range': _val_qhint('275', '375 with tentacles radius'),
            'effect': 'AoE stun', 'effect2': 'AoE damage'},
        'frogmen_tendrils_of_the_deep': {
            'aoe': '100',
            'cast_range': _val_qhint('300', '400 with tentacles radius'),
            'effect': 'AoE stun', 'effect2': 'AoE damage'},
        'frogmen_water_bubble_small': {
            'effect': '100/120/140/160 magic barrier'},
        'frogmen_water_bubble_medium': {
            'effect': '150/180/210/240 magic barrier'},
        'centaur_khan_endurance_aura': {
            'effect': 'Attack speed bonus'},
        'furbolg_enrage_attack_speed': {
            'effect': 'Attack speed bonus over time'},
        'satyr_soulstealer_mana_burn': {
            # Burn = flat + Int multiplier. Raw HTML so we can inline the
            # intelligence icon; sentinel `\x01` lets _prop_cell skip _esc.
            # Only the flat amount is coloured (it deals damage of the cell's
            # type). The Int-multiplier tail stays default colour and sits on
            # a second line so the cell can stay narrow.
            'damage': ('\x01<span class="dmg-wrap dmg-multiline">'
                       '<span class="dmg-num">20/25/30/35</span>'
                       '<span class="dmg-line2">+ 200/250/350/400%'
                       '<img class="stat-ico" src="icons/intelligence.webp" '
                       'alt="Int"></span></span>'),
            'effect': 'Mana burn', 'effect2': 'Damage for burnt mana'},
        'forest_troll_high_priest_mana_aura': {
            'effect': '2 MP/sec regen'},
        'alpha_wolf_command_aura': {
            'effect': '+20% damage increase'},
        'alpha_wolf_critical_strike': {
            'effect': '20% chance to crit for 200/225/250/300%'},
        'centaur_khan_war_stomp': {
            'duration': _val_qhint(
                '1.6 or 3',
                'Lasts longer on creeps (3)'),
            'effect': 'AoE stun', 'effect2': 'AoE damage'},
        'polar_furbolg_ursa_warrior_thunder_clap': {
            'effect': 'AoE damage', 'effect2': 'AoE slow'},
        'furbolg_enrage_damage': {
            'effect': '+60% damage increase over time'},
        'enraged_wildkin_toughness_aura': {
            'effect': '+3 armor'},
        'enraged_wildkin_hurricane': {
            # No av_duration in KV; the knockback travel time is fixed at 0.5s.
            'duration': '0.5',
            'effect': 'Pushes a unit in the vector-targeted direction'},
        'warpine_raider_seed_shot': {
            'cast_range': _val_qhint('575', 'Bounces range is 500'),
            'ms_effect': '-100%',
            'effect': 'Damage to 4/6/8/12 targets',
            'effect2': 'Movement slow'},
        'frogmen_congregation_of_the_deep': {
            # AbilityCastRange=0 (self-cast); effective tentacle reach is the
            # av_range (300) +100 spread = 400.
            'aoe': '100',
            'cast_range': _val_qhint('300', '400 with tentacles radius'),
            'effect': 'AoE stun', 'effect2': 'AoE damage'},
        'ancient_rock_golem_weakening_aura': {
            'effect': '-3/-4/-5/-6 armor'},
        'frostbitten_golem_time_warp_aura': {
            'effect': '8/9/10/11% cooldown reduction'},
        'big_thunder_lizard_wardrums_aura': {
            'effect': 'Attack speed bonus',
            'effect2': 'Accuracy 40/43/46/51%'},
        'frogmen_water_bubble_large': {
            'effect': '210/240/270/300 magic barrier',
            'effect2': '50% of the barrier burst heals the target'},
        'satyr_hellcaller_unholy_aura': {
            'effect': '+3/5/7/11 HP/sec regen'},
        'satyr_hellcaller_shockwave': {
            # av_radius_start:"180", av_radius_end:"200" — cone widens.
            # av_distance:"1380" + av_speed:"900"; effective max range ~1580.
            'aoe': _val_qhint(
                '180', '200 at the end (cone widens along the path)'),
            'cast_range': _val_qhint(
                '700', 'Max travel distance is 1580'),
            'effect': 'AoE damage with a projectile'},
        'dark_troll_warlord_raise_dead': {
            'manacost': '50', 'cooldown': '20', 'duration': '35',
            '_force_leveled': ('effect',),
            'effect': (
                '\x01<span class="cell-wrap">Summons 3 <a class="ua-inline-link" '
                'href="neutral_stats.html#unit-skeleton_warrior">'
                'Skeleton Warriors</a>'
                '<span class="qhint" tabindex="0" role="button" '
                'aria-label="HP = 250/275/300/375, attack damage = 12/15/18/21" '
                'data-tooltip="HP = 250/275/300/375, attack damage = 12/15/18/21"'
                '>?</span></span>'),
            'effect2': (
                '\x01Skeletons have <a class="ua-inline-link" '
                'href="neutral_abilities.html#skeleton_warrior-hill_troll_rally">'
                'Rally</a> aura'),
        },
        'spawnlord_master_stomp': {
            'effect': 'Reduces base (white) armor by 50%',
            'effect2': 'Deals damage'},
        'spawnlord_master_freeze': {
            # av_damage:"100" with av_tick_interval:"0.1" is mislabeled in KV —
            # the in-game tooltip and old sheet both say 100/sec, so force it.
            'damage': _dmg_qhint(
                '100 per sec.', 'Deals damage in 0.1 seconds intervals'),
            'effect': 'Immobilizes', 'effect2': 'Damage over time'},
        'black_dragon_dragonhide_aura': {
            'effect': '+3 armor'},
        'black_dragon_fireball': {
            # av_damage:"85" is mislabeled — actual game effect is 85/sec
            # (total 722.5 over 8s); av_damage path takes priority, so override.
            'damage': '85 per sec.',
            'effect': 'AoE damage', 'effect2': 'Flying vision 300/300'},
        'black_dragon_splash_attack': {
            # av_range:"250" is the splash radius, but our auto-derive reads
            # av_radius only.
            'aoe': '250',
            'effect': 'AoE damage applied by attacks'},
        'granite_golem_hp_aura': {
            'effect': '+16/17/18/19% max HP increase'},
        'big_thunder_lizard_slam': {
            'duration': _val_qhint(
                '2/2.25/2.5/3 or 4',
                'Scaling duration on heroes. Lasts longer on creeps (4)'),
            'as_effect': '-60%',
            'effect': 'AoE damage', 'effect2': 'AoE slow'},
        'big_thunder_lizard_frenzy': {
            'effect': 'Attack speed bonus on 1 ally'},
        'ice_shaman_incendiary_bomb': {
            # av_burn_damage = 50, av_building_damage_pct = 25 → 12.5 to buildings.
            'damage': _dmg_qhint(
                '50 or 12.5 per sec.',
                'Deals 25% of the damage to structures (12.5/sec before resistances).'),
            'effect': 'Single target damage over time (works on buildings)'},
    }

    def _abil_props(slug):
        a = cur_ab.get(slug, {})
        g = lambda k: a.get(k, '')

        def _posnum(x):
            try:
                return float(_f1(x)) > 0
            except Exception:
                return False
        cd, mc = g('AbilityCooldown'), g('AbilityManaCost')
        # Type resolution order:
        #  1) Aura — by slug token OR a TYPE_MANUAL entry containing "Aura".
        #  2) TYPE_MANUAL — first comma-separated word ("Active"/"Passive")
        #     overrides the heuristic for abilities where cd/mc presence is
        #     misleading (Break has a cd but is passive; Ice Armor lacks data).
        #  3) Heuristic — active if cd/mc/cast-range present, else passive.
        MANUAL_AURAS = {s for s, t in TYPE_MANUAL.items() if 'Aura' in t}
        if 'aura' in slug or slug in MANUAL_AURAS:
            typ = 'Aura'
        elif slug in TYPE_MANUAL:
            typ = TYPE_MANUAL[slug].split(',')[0].strip()
        elif _posnum(cd) or _posnum(mc) or g('AbilityCastRange'):
            typ = 'Active'
        else:
            typ = 'Passive'
        # Damage cell. Priority:
        #  1) hero/creep split when both av_damage and av_damage_creeps exist
        #     ("75 (герои) / 150 (крипы)" mirrors the legacy sheet)
        #  2) plain av_damage / AbilityDamage
        #  3) av_damage_per_second → "<v> per sec."
        #  4) av_burn_damage + av_burn_interval → "<v/interval> per sec."
        dmg = g('av_damage') or g('AbilityDamage')
        dmg_creeps = g('av_damage_creeps')
        if dmg and dmg_creeps:
            damage = f'{_prog(dmg)} (герои) / {_prog(dmg_creeps)} (крипы)'
        elif dmg:
            damage = _prog(dmg)
        elif g('av_damage_per_second'):
            damage = f'{_prog(g("av_damage_per_second"))} per sec.'
        elif g('av_burn_damage'):
            interval = g('av_burn_interval')
            try:
                burn = float(_f1(g('av_burn_damage')))
                ivl = float(_f1(interval)) if interval else 1.0
                dps = burn / ivl if ivl else burn
                damage = f'{int(dps) if dps == int(dps) else dps} per sec.'
            except (ValueError, ZeroDivisionError):
                damage = _prog(g('av_burn_damage'))
        else:
            damage = ''

        # Duration cell. Priority:
        #  1) hero/non-hero duration split  (Slam, Envenomed Weapon)
        #  2) hero/non-hero stun-duration split  (War Stomp)
        #  3) plain av_duration / AbilityDuration / av_hero_*  (single value)
        hd, nd = g('av_hero_duration'), g('av_non_hero_duration')
        hsd, nsd = g('av_hero_stun_duration'), g('av_non_hero_stun_duration')
        if hd and nd:
            duration = f'{_prog(hd)} (герои) / {_prog(nd)} (крипы)'
        elif hsd and nsd:
            duration = f'{_prog(hsd)} (герои) / {_prog(nsd)} (крипы)'
        else:
            duration = _prog(g('av_duration') or g('AbilityDuration')
                             or hd or hsd)

        # Cast range cell — augment with jump/bounce range when present.
        cr = _prog(g('AbilityCastRange'))
        jr = g('av_jump_range') or g('av_bounce_range')
        if cr and jr:
            cast_range = f'{cr} ({_prog(jr)} у прыжков)'
        else:
            cast_range = cr

        # Flat-AS bonuses keep no suffix; AS slow and all MS values are %.
        as_fields = (('av_speed_bonus', '+{}'), ('av_bonus_attack_speed', '+{}'),
                     ('av_bonus_aspd', '+{}'), ('av_attackspeed_bonus', '+{}'),
                     ('av_attackspeed_slow', '{}%'))
        ms_fields = (('av_bonus_movement_speed', '+{}%'),
                     ('av_movespeed_slow', '{}%'),
                     ('av_move_speed_penalty', '{}%'))
        as_eff = ' '.join(lbl.format(_prog(g(k))) for k, lbl in as_fields if g(k))
        ms_eff = ' '.join(lbl.format(_prog(g(k))) for k, lbl in ms_fields if g(k))
        leveled = any(len(str(v).split()) > 1 for v in a.values())
        if slug in AURA_STACK_YES:
            stack = 'Yes'
        elif 'aura' in slug or slug in MANUAL_AURAS:
            stack = 'No'
        else:
            stack = ''
        props = {
            'type': typ,
            'dmg_type': DMGTYPE_MANUAL.get(slug, ''),
            'damage': damage,
            'aoe': _prog(g('av_radius')),
            'manacost': _prog(mc),
            'cooldown': _prog(cd),
            'duration': duration,
            'cast_range': cast_range,
            'as_effect': as_eff,
            'ms_effect': ms_eff,
            'effect': '', 'effect2': '', 'effect3': '',
            'dispel': DISPEL_MANUAL.get(slug) or DISPEL.get(g('SpellDispellableType'), ''),
            'through_bkb': THROUGH_BKB.get(slug, ''),
            '_through_bkb_tip': THROUGH_BKB_TIPS.get(slug, ''),
            'stackable': stack,
            'lvl_up': 'Yes' if leveled else 'No',
        }
        # Every aura updates on a 0.5s tick (Valve convention); show it in the
        # Duration cell so it isn't confused with empty/instant abilities.
        if typ == 'Aura' and not props['duration']:
            props['duration'] = '0.5'
        props.update(ABIL_MANUAL.get(slug, {}))
        # Mark cells that carry a per-level progression (3+ slash-separated
        # numeric tokens) — surfaced as a blue outline when the Upgrades view
        # toggle is on. 3+ tokens, not 2+, to avoid false positives like
        # "1200/800 vision" (those are independent values, not a level table).
        # Allow a leading minus so negative progressions (e.g. Frost Attack's
        # "-25/-28/-31/-37" AS/MS slow) are detected as leveled.
        _LVL_RE = re.compile(r'-?\d+(?:\.\d+)?(?:/-?\d+(?:\.\d+)?){2,}')
        leveled = set()
        for _k, _v in props.items():
            if _k.startswith('_'):
                continue
            if isinstance(_v, str) and _v.startswith('\x01'):
                _text = re.sub(r'<[^>]+>', '', _v[1:])
            else:
                _text = str(_v or '')
            if _LVL_RE.search(_text):
                leveled.add(_k)
        # Manual overrides can force cells to render as leveled even when the
        # visible text doesn't carry a slash-progression (e.g. "Summons 3 …"
        # with per-level HP/damage values surfaced via tooltip only).
        leveled.update(props.pop('_force_leveled', ()))
        props['_leveled'] = leveled
        return props

    UA_COLS = [
        ('lvl', 'Lvl'), ('unit', 'Unit'), ('ability', 'Ability'),
        ('type', 'Type'), ('damage', 'Damage'),
        ('manacost', 'Manacost'), ('cooldown', 'Cooldown'),
        ('duration', 'Duration'), ('cast_range', 'Cast Range'),
        ('aoe', 'Radius'), ('stackable', 'Aura Stack'),
        ('dispel', 'Dispellable'), ('through_bkb', 'Through BKB'),
        ('as_effect', 'AS Effect'), ('ms_effect', 'MS Effect'),
        ('effect', 'Property'), ('effect2', 'Property 2'), ('effect3', 'Property 3'),
    ]
    UA_STICKY = {'lvl', 'unit', 'ability'}
    # Vertical dividers are drawn at CATEGORY boundaries only (scripts.js
    # markCatEdges, adapts to both views) — no manual per-column separators.
    UA_SEP = set()
    # Super-category grouping shown above the column headers (mirrors Neutral
    # Creeps so both tables look symmetric). Order/colspans must match UA_COLS.
    # Each column header carries data-cat so scripts.js recomputeCatColspans()
    # can size each category cell — WITHOUT data-cat it counts 0 and collapses
    # every category to colspan=1.
    UA_CATEGORIES = [
        ('Basic',      'basic',      ['lvl', 'unit', 'ability']),
        ('Essentials', 'essentials', ['type', 'damage', 'manacost', 'cooldown',
                                      'duration', 'cast_range', 'aoe']),
        ('Extra',      'extra',      ['stackable', 'dispel', 'through_bkb',
                                      'as_effect', 'ms_effect']),
        ('Effects',    'effects',    ['effect', 'effect2', 'effect3']),
    ]
    UA_COL_CAT = {col: slug for _cat, slug, cols in UA_CATEGORIES for col in cols}
    # Column-header tooltips surfaced via a `?` badge next to the header label.
    # Values support inline HTML (rendered via innerHTML in scripts.js).
    UA_HEAD_HINTS = {
        'duration': 'Most of the auras have linger duration of 0.5 seconds',
        'damage': (
            '<div class="qh-line">Numbers in color mean different damage types: '
            '<span class="dt-magical">magical</span>, '
            '<span class="dt-physical">physical</span>, '
            '<span class="dt-hpremoval">HP removal</span>.</div>'
        ),
        'through_bkb': (
            '<div class="qh-line">If an ability doesn\'t pierce BKB but '
            'also deals damage on top of its effect, the damage still goes '
            'through — reduced by the magic resistance BKB provides.</div>'
            '<div class="qh-line"><span class="hint-aura">Aura</span>: all '
            'positive auras keep working on allies under BKB, but negative '
            'auras don\'t affect enemies under the same effect.</div>'
        ),
        'dispel': (
            '<div class="qh-line">'
            '<span class="ua-yn ua-yn-strong">Yes</span>'
            ' — Strong Dispel only</div>'
            '<div class="qh-line">'
            '<span class="ua-yn ua-yn-yes">Yes</span>'
            ' — Any dispel</div>'
            '<div class="qh-line">'
            '<span class="ua-yn ua-yn-no">No</span>'
            ' — Not dispellable, mostly due to different kind of ability</div>'
        ),
    }
    PROP_COLS = [k for k, _ in UA_COLS
                 if k not in ('lvl', 'unit', 'ability')]

    ua_thead = []
    for idx, (k, label) in enumerate(UA_COLS):
        cls = (f'ua-{k}' + (' sticky-col' if k in UA_STICKY else '')
               + (' col-sep' if k in UA_SEP else ''))
        hint = ''
        if k in UA_HEAD_HINTS:
            # Tooltip value may contain inline HTML (rendered via innerHTML
            # client-side) — escape quotes so the attribute survives.
            tip = _attr_esc(UA_HEAD_HINTS[k])
            hint = (f'<span class="qhint" tabindex="0" role="button" '
                    f'aria-label="{tip}" data-tooltip="{tip}">?</span>')
        ua_thead.append(
            f'<th class="{cls} sortable" data-col="{k}" data-idx="{idx}" '
            f'data-cat="{UA_COL_CAT.get(k, "")}">'
            f'<span class="th-label">{label}</span>{hint}'
            f'<span class="sort-ind"></span></th>')
    ua_head_html = ''.join(ua_thead)

    # Super-category row above the column headers (one cell per category,
    # colspan = its leaf columns). scripts.js recomputeCatColspans() then keeps
    # the colspans in sync with the visible columns (via the data-cat above).
    ua_cat_cells = ''.join(
        f'<th class="cat-head cat-{slug}" data-cat="{slug}" '
        f'colspan="{len(cols)}">{_esc(cat)}</th>'
        for cat, slug, cols in UA_CATEGORIES
    )

    DMG_TYPE_CLS = {'Magical': 'dt-magical', 'Physical': 'dt-physical',
                    'HP Removal': 'dt-hpremoval', 'Pure': 'dt-pure'}

    # A run of >=3 slash-separated numbers ("75/80/85/90", "-15%/-18%/-21%/-25%",
    # "+20/25/30/40"). Each value may carry a trailing %.
    _RUN_RE = re.compile(r'[+-]?\d+(?:[.,]\d+)?%?(?:/[+-]?\d+(?:[.,]\d+)?%?){2,}')

    def _run_button(run):
        """A collapsed "first→last" button for a slash-run; full list in data-full."""
        p = run.split('/')   # run is pure digits/slashes/%/+/- → safe unescaped
        return (f'<button type="button" class="lvl-toggle" aria-expanded="false" '
                f'title="Show per-tier values" data-full="{_attr_esc(" / ".join(p))}">'
                f'{p[0]}→{p[-1]}</button>')

    def _collapse_runs(text):
        """Collapse every long slash-run in PLAIN `text` (escapes non-run text)."""
        out, last = [], 0
        for m in _RUN_RE.finditer(text):
            out.append(_esc(text[last:m.start()]))
            out.append(_run_button(m.group(0)))
            last = m.end()
        out.append(_esc(text[last:]))
        return ''.join(out)

    def _collapse_runs_html(s):
        """Collapse runs in an already-built HTML fragment (\\x01 manual cells) —
        only in text BETWEEN tags, so attribute tooltips (which also contain
        slashed lists) are never touched."""
        return ''.join(
            tok if tok.startswith('<') else _RUN_RE.sub(lambda m: _run_button(m.group(0)), tok)
            for tok in re.split(r'(<[^>]+>)', s)
        )

    def _prop_cell(pk, val, props=None):
        # Type → colour-coded text. Damage cell carries the dt-* class so the
        # value text inherits the damage-type colour (replaces the standalone
        # Damage Type column). Stackable / Dispellable → glyph icons. Every
        # <td> carries data-col so the view-toggle JS can reorder columns by key.
        sep = ' col-sep' if pk in UA_SEP else ''
        # Cells with per-level progression get a `leveled` marker class; the
        # Upgrades view toggle (.show-upgrades) draws a blue outline on them.
        if pk in (props or {}).get('_leveled', ()):
            sep += ' leveled'
        dc = f' data-col="{pk}" data-cat="{UA_COL_CAT.get(pk, "")}"'
        if pk == 'type':
            if not val:
                return f'<td class="ua-type{sep}"{dc}><span class="ua-dash">—</span></td>'
            return f'<td class="ua-type ua-type-{val.lower()}{sep}"{dc}>{_esc(val)}</td>'
        if pk == 'damage':
            dt = (props or {}).get('dmg_type', '')
            dt_cls = f' {DMG_TYPE_CLS[dt]}' if dt in DMG_TYPE_CLS else ''
            if isinstance(val, str) and val.startswith('\x01'):
                # Manual override already has .dmg-num spans where appropriate;
                # still collapse any long slash-run inside its text.
                return (f'<td class="ua-damage{dt_cls}{sep}"{dc}>'
                        f'{_collapse_runs_html(val[1:])}</td>')
            if not val:
                return f'<td class="ua-damage{dt_cls}{sep}"{dc}><span class="ua-dash">—</span></td>'
            collapsed = _collapse_runs(str(val))
            # If a run was collapsed the button carries the dt-* colour via CSS;
            # otherwise keep the per-number .dmg-num colouring.
            inner = collapsed if 'lvl-toggle' in collapsed else _dmg_color_html(_esc(val))
            return f'<td class="ua-damage{dt_cls}{sep}"{dc}>{inner}</td>'
        # Coloured yes/no text. Sort rank: dash (0) < no (1) < yes (2).
        _YES = '<span class="ua-yn ua-yn-yes">yes</span>'
        _NO = '<span class="ua-yn ua-yn-no">no</span>'
        if pk == 'stackable':
            if val == 'Yes':
                g, rank = _YES, 2
            elif val == 'No':
                g, rank = _NO, 1
            else:
                g, rank = '<span class="ua-dash">—</span>', 0
            return f'<td class="ua-stackable{sep}"{dc} data-sort="{rank}">{g}</td>'
        if pk == 'dispel':
            # Per-cell legend was moved to the column header's `?` badge —
            # cells render just the colored yes/no glyph.
            if val == 'Yes':
                g, rank = _YES, 2
            elif val == 'Strong only':
                g, rank = '<span class="ua-yn ua-yn-strong">yes</span>', 2
            elif val == 'No':
                g, rank = _NO, 1
            else:
                g, rank = '<span class="ua-dash">—</span>', 0
            return f'<td class="ua-dispel{sep}"{dc} data-sort="{rank}">{g}</td>'
        # Through BKB: same yes/no glyphs as Dispellable. Sorted yes(2) > no(1) > —(0).
        # Optional per-cell tooltip via `_through_bkb_tip` in props (THROUGH_BKB_TIPS).
        if pk == 'through_bkb':
            v = (val or '').strip().lower()
            if v == 'yes':
                g, rank = _YES, 2
            elif v == 'no':
                g, rank = _NO, 1
            else:
                g, rank = '<span class="ua-dash">—</span>', 0
            tip = (props or {}).get('_through_bkb_tip', '')
            if tip:
                t = _attr_esc(tip)
                qh = (f'<span class="qhint" tabindex="0" role="button" '
                      f'aria-label="{t}" data-tooltip="{t}">?</span>')
                g = f'<span class="cell-wrap">{g}{qh}</span>'
            return f'<td class="ua-through_bkb{sep}"{dc} data-sort="{rank}">{g}</td>'
        # Raw-HTML sentinel: ABIL_MANUAL values prefixed with \x01 bypass _esc
        # so we can inline <img> / <span> markup (used for Mana Burn's Int icon).
        # Still collapse long slash-runs in the inline text (between tags).
        if isinstance(val, str) and val.startswith('\x01'):
            return f'<td class="ua-{pk}{sep}"{dc}>{_collapse_runs_html(val[1:])}</td>'
        sval = '' if val is None else str(val)
        # Collapse any long per-tier run ("75/80/85/90") — even inside descriptive
        # text — to "first→last"; surrounding text kept, full list in a click
        # popover (scripts.js). Empty → dash.
        inner = _collapse_runs(sval) if sval != '' else '<span class="ua-dash">—</span>'
        return f'<td class="ua-{pk}{sep}"{dc}>{inner}</td>'

    # Abilities that are identical across multiple units (same slug, same
    # values) get a single canonical row on the UA page — pinned to the listed
    # createhero. Other units' rows are skipped, and creeps.html ability
    # links route to the canonical row for that slug.
    UA_CANONICAL_UNIT = {
        'frogmen_riverborn_aura': 'tad',
    }
    UA_SHARED_TOOLTIP = {
        'frogmen_riverborn_aura': 'This aura is identical for all frog units',
    }
    # ---- Ability descriptions parsed from data/abilities_english.txt ----
    # Valve ships a single localization file with all ability tooltips, including
    # neutral-creep abilities that don't appear in dota_english.txt. Build a
    # `{slug: description}` dict once; render as a hover tooltip on each icon.
    ABIL_DESC: dict[str, str] = {}
    _ae_path = _os.path.join(_HERE, 'data', 'abilities_english.txt')
    if _os.path.exists(_ae_path):
        with open(_ae_path, encoding='utf-8-sig', errors='replace') as _f:
            _ae_text = _f.read()
        for _m in re.finditer(
            # Case-insensitive: Valve mixes `ability_` and `Ability_` (capital A)
            # in the key names — same key, different casing.
            r'"DOTA_Tooltip_[Aa]bility_([a-z0-9_]+?)_Description"\s+"((?:[^"\\]|\\.)+)"',
            _ae_text,
        ):
            _slug, _desc = _m.group(1), _m.group(2)
            # Strip Valve's localization escapes / formatting macros that don't
            # carry meaning in a plain tooltip (newlines kept as spaces).
            _desc = (_desc.replace('\\n', ' ')
                          .replace('<br>', ' ')
                          .replace('  ', ' ')
                          .strip())
            if _slug not in ABIL_DESC:
                ABIL_DESC[_slug] = _desc
    ua_rows = []
    for row in rendered:
        d = row['data']
        lvl = row.get('level', '')
        ch = (d.get('createhero') or '').strip()
        icon = d.get('icon')
        unit_img = (
            f'<a class="unit-link" href="neutral_stats.html#unit-{_esc(ch)}">'
            f'<img class="creep-copy" src="{_esc(icon)}" alt="" loading="lazy" '
            f'onerror="this.style.visibility=\'hidden\'"></a>' if icon else '')
        slugs = [(kk, d.get(kk + '_slug', ''), d.get(kk, ''))
                 for kk in ('ability1', 'ability2', 'ability3')
                 if d.get(kk + '_slug', '')]
        for kk, slug, name in slugs:
            # Skip duplicate canonical-aura rows.
            if slug in UA_CANONICAL_UNIT and UA_CANONICAL_UNIT[slug] != ch:
                continue
            p = _abil_props(slug)
            if _has_abil_icon(slug):
                img_tag = (f'<img class="abil-ico" src="icons/abilities/{slug}.png" '
                           f'alt="{_esc(name)}" loading="lazy">')
                if slug in AUTOCAST_ABILITIES:
                    aico = (f'<span class="abil-ico-wrap abil-autocast">'
                            f'{img_tag}{_autocast_snake_svg()}</span>')
                else:
                    aico = img_tag
                # Hover-tooltip with Valve's ability description (parsed from
                # abilities_english.txt). Reuses the body-level qhint-tip JS via
                # an `.abil-ico-hint` element carrying data-tooltip.
                _desc = ABIL_DESC.get(slug)
                if _desc:
                    _t = _attr_esc(_desc)
                    aico = (f'<span class="abil-ico-hint" tabindex="0" '
                            f'role="button" aria-label="{_t}" '
                            f'data-tooltip="{_t}">{aico}</span>')
            else:
                aico = ''
            # Question-mark hint icon appended to the ability name when this
            # row stands in for multiple units (Riverborn Aura). Hovering the
            # rest of the cell will surface patchnotes later, so explicit
            # author hints must come through a dedicated `?` badge.
            qhint = ''
            if slug in UA_SHARED_TOOLTIP:
                tip = _esc(UA_SHARED_TOOLTIP[slug])
                qhint = (f'<span class="qhint" tabindex="0" role="button" '
                         f'aria-label="{tip}" data-tooltip="{tip}">?</span>')
            # Every ability row carries its own Lvl + Unit cells (no rowspan):
            # the table is sortable, and sorting reorders rows, which would
            # tear a rowspanned group apart and dump continuation cells into
            # the wrong columns. Self-contained rows always stay aligned.
            cells = [
                f'<td class="ua-lvl lvl-cell sticky-col" data-col="lvl" '
                f'data-cat="basic" data-lvl="{_esc(lvl)}">{_esc(lvl)}</td>',
                f'<td class="ua-unit creep-icon-cell sticky-col" data-col="unit" '
                f'data-cat="basic" data-sort="{_esc(d.get("name", ""))}">{unit_img}</td>',
                f'<td class="ua-ability sticky-col" data-col="ability" data-cat="basic">'
                f'<span class="ua-ability-inner">{aico}'
                f'<span class="ua-ability-name">{_esc(name)}</span>'
                f'{qhint}</span></td>',
            ]
            for pk in PROP_COLS:
                cells.append(_prop_cell(pk, p[pk], p))
            aura_cls = ' class="ua-row-aura"' if p['type'] == 'Aura' else ''
            ua_rows.append(
                f'<tr id="{_esc(ch)}-{slug}" data-unit="{_esc(ch)}"{aura_cls}>'
                f'{"".join(cells)}</tr>')

    ua_html = (
        '<!DOCTYPE html>\n<html lang="ru">\n<head>\n<meta charset="UTF-8">\n'
        '<title>SIKLE | Neutral Abilities</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={ASSET_VERSION}">\n'
        '</head>\n<body>\n'
        f'{nav_ua}\n'
        '<div class="container creeps-page">\n'
        '<div class="sticky-frame" aria-hidden="true"></div>\n'
        '<div class="sticky-frame-top" aria-hidden="true"></div>\n'
        '<div class="creeps-scroll">\n'
        # Sub-tab bar + blurb + toolbar live INSIDE the scroll box so they
        # scroll away with the table (Mana Items behaviour); sticky-left keeps
        # them put during horizontal scroll.
        f'{subnav_abilities}'
        '<p class="mr-blurb inbox-bar">Every ability owned by a neutral camp '
        'creep — one row per (creep, ability). Hover any cell with the dotted '
        'underline to see how its value changed across patches. The '
        '<strong>View</strong> dropdown filters the table: <em>Standard</em> '
        'lists all abilities, <em>Auras</em> shows only the aura-type ones. '
        'The <strong>Upgrades</strong> toggle dots numbers that progress per '
        'neutral tier (e.g. 40/36/32/26).</p>\n'
        '<div class="cal-toggle-bar inbox-bar"><div class="toolbar-panel">'
        '<span class="view-group">'
        '<strong>View</strong>'
        '<select class="cal-mode-select" id="ua-view-mode">'
        '<option value="standard">Standard</option>'
        '<option value="auras">Auras</option>'
        '</select>'
        '</span>'
        # Upgrades — binary switch. ON marks every per-level progression
        # value in the table with a dotted underline (each "40/36/32/26"
        # number gets the marker), so leveled cells self-identify through
        # their own content rather than via an Excel-style outline.
        '<label class="ua-upgrades-toggle">'
        '<span class="ua-upgrades-label">Upgrades</span>'
        '<input type="checkbox" id="ua-upgrades-mode" class="ua-switch-input" checked>'
        '<span class="ua-switch" aria-hidden="true"></span>'
        '</label>'
        '</div></div>\n'
        '<table class="creeps-table unit-abilities-table">\n'
        f'<thead><tr class="cat-row">{ua_cat_cells}</tr>'
        f'<tr class="col-row">{ua_head_html}</tr></thead>\n'
        f'<tbody>\n{chr(10).join(ua_rows)}\n</tbody>\n'
        '</table>\n</div>\n</div>\n'
        f'<script src="src/scripts.js?v={ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n'
    )
    with open('neutral_abilities.html', 'w', encoding='utf-8') as f:
        f.write(ua_html)
    print(f"  -> neutral_abilities.html: {len(ua_html):,} bytes")
    # Tiny redirect for the old URL so existing links (including from
    # generated patch pages, bookmarks, external references) don't 404.
    redirect_html = (
        '<!DOCTYPE html><html><head><meta charset="UTF-8">'
        '<meta http-equiv="refresh" content="0; url=neutral_abilities.html">'
        '<link rel="canonical" href="neutral_abilities.html">'
        '<title>Sloppy - moved</title></head><body>'
        '<p>This page moved to <a href="neutral_abilities.html">'
        'neutral_abilities.html</a>.</p></body></html>'
    )
    with open('unit_abilities.html', 'w', encoding='utf-8') as f:
        f.write(redirect_html)
    print(f"  -> unit_abilities.html: {len(redirect_html)} bytes (redirect)")

if __name__ == "__main__":
    save_creeps_html()
