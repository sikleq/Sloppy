"""build_creeps.py — generates creeps.html, the neutral-creeps stats
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
import site_common as _site

ASSET_VERSION = _site.compute_asset_version()
_HERE = _os.path.dirname(_os.path.abspath(__file__))


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
    """Generate creeps.html — neutral-creeps stats table. CSV provides the
    ordering, level (Ур.) and createhero name; every other column is
    auto-pulled from data/stats/7.41c/units.json + npc_units.txt and
    abilities_slim.json. Derived columns (Armor %, EHP Phys/Mag, Avg dmg,
    Avg gold, t/1 attack) are computed from formulas. Tier-level rows are
    separated with a horizontal divider when Ур. changes.

    Per-CSV-row icon/display-name mapping lives in CREEP_NAME_TO_NPC plus
    CREEP_DISPLAY_NAMES below — update those to add new neutrals."""
    import csv as _csv
    import re as _re

    csv_path = _os.path.join(_os.path.dirname(__file__),
                              'data', 'creeps_raw.csv')
    if not _os.path.exists(csv_path):
        print(f"  ! creeps_raw.csv not found, skipping creeps.html")
        return

    # ---- Source files ----
    UNITS_PATH = _os.path.join(_os.path.dirname(__file__),
                                'data', 'stats', '7.41c', 'units.json')
    NPC_KV_PATH = _os.path.join(_os.path.dirname(__file__),
                                 'data', 'stats', '7.41c', 'npc_units.txt')
    ABIL_SLIM_PATH = _os.path.join(_os.path.dirname(__file__),
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
    _abil_by_patch = {}
    for _v in _patches_chrono:
        _ap_path = _os.path.join(STATS_DIR, _v, "npc_abilities.json")
        if not _os.path.exists(_ap_path):
            continue
        try:
            _abil_by_patch[_v] = _json.loads(open(_ap_path, encoding="utf-8").read())
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

    def _ability_dname(slug):
        if not slug or slug in ABILITY_SKIP:
            return ''
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
        """Heuristic: melee attack capability → "Обычный" (Hero), ranged
        → "Проникающий" (Pierce). Matches the CSV's authored values."""
        cap = npc.get('AttackCapabilities', '')
        if 'RANGED' in cap:
            return 'Проникающий'
        return 'Обычный'

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
        dmg_avg = (dmg_min + dmg_max) / 2 if (dmg_min or dmg_max) else 0
        gold_avg = (gold_min + gold_max) / 2 if gold_min or gold_max else 0
        t_per_attack = bat * 100 / ats if ats else bat

        # Ability dnames (skip hidden marker abilities and blanks)
        abilities = []
        for i in range(1, 6):
            slug = npc.get(f'Ability{i}', '').strip()
            if not slug or slug in ABILITY_SKIP:
                continue
            abilities.append(_ability_dname(slug))
        abilities += [''] * (3 - len(abilities)) if len(abilities) < 3 else []

        return {
            'hp':            _fmt_num(hp) if hp else '',
            # Resolved creeps always show a regen value; "0" when the KV
            # has no StatusHealthRegen (e.g. Skeleton Warrior) instead of
            # a blank cell.
            'hp_regen':      (f'+{_fmt_num(hp_regen)}' if hp_regen
                              else ('0' if npc else '')),
            'mp':            _fmt_num(mp) if mp else '-',
            'mp_regen':      f'+{_fmt_num(mp_regen)}' if mp_regen else '',
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
            'ability1':      abilities[0] if len(abilities) > 0 else '',
            'ability2':      abilities[1] if len(abilities) > 1 else '',
            'ability3':      abilities[2] if len(abilities) > 2 else '',
        }

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
        return _fmt_num(((mn or 0) + (mx or 0)) / 2)

    def _gold_vf(version, npc_key):
        gmn = _raw_at('BountyGoldMin', version, npc_key)
        gmx = _raw_at('BountyGoldMax', version, npc_key)
        if gmn is None and gmx is None:
            return None
        return _fmt_num(((gmn or 0) + (gmx or 0)) / 2)

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
        'AbilityCooldown': 'Cooldown', 'AbilityManaCost': 'Mana',
        'AbilityCastRange': 'Cast range', 'AbilityCastPoint': 'Cast point',
        'AbilityDamage': 'Damage', 'AbilityChannelTime': 'Channel',
        'AbilityDuration': 'Duration', 'AbilityUnitDamageType': 'Damage type',
        'SpellImmunityType': 'Spell immunity', 'SpellDispellableType': 'Dispellable',
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
            return fld[3:].replace('_', ' ').capitalize()
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
            return 'cooldown' in n or 'manacost' in n or 'mana_cost' in n
        return False

    def _slash(s):
        """Per-level KV values are space-separated → show as 2/3/4/5, with
        each token trimmed (12.0 → 12) via _fmt_num."""
        return '/'.join(_fmt_num(t) for t in str(s).split())

    _FIRST_PATCH = _patches_chrono[0] if _patches_chrono else None

    def _ability_changelog(npc_key, slot):
        """Combined changelog for the ability cell at `slot`. Returns typed
        entries scripts.js renders:
          (patch, date, 'A', name)            — ability added
          (patch, date, 'R', name)            — ability removed
          (patch, date, 'P', old, new)        — ability replaced
          (patch, date, 'F', label, old, new) — value change (cooldown, …)
        The baseline (ability present at the FIRST tracked patch, 7.08) emits
        nothing; a unit introduced later (e.g. frogs in 7.38) shows ADDED."""
        if not npc_key:
            return []
        entries = []
        prev_slug = None
        prev_fields = None
        started = False
        for v in _patches_chrono:
            if _raw_at('StatusHealth', v, npc_key) is None:
                continue  # unit absent this patch
            slugs = _ability_slugs_at(v, npc_key)
            cur = slugs[slot] if slot < len(slugs) else None
            cur_fields = _abil_by_patch.get(v, {}).get(cur, {}) if cur else {}
            dt = PATCH_DATES.get(v, '')
            if not started:
                started = True
                if v == _FIRST_PATCH:
                    # data baseline (was already there at 7.08) — adopt silently
                    prev_slug, prev_fields = cur, cur_fields
                    continue
                # unit introduced mid-history → prev_slug stays None → ADDED below
            if prev_slug != cur:
                if not prev_slug and cur:
                    entries.append((v, dt, 'A', _ability_dname(cur)))
                elif prev_slug and not cur:
                    entries.append((v, dt, 'R', _ability_dname(prev_slug)))
                else:
                    entries.append((v, dt, 'P', _ability_dname(prev_slug),
                                    _ability_dname(cur)))
            if cur and cur == prev_slug and prev_fields:
                for fld, val in cur_fields.items():
                    old = prev_fields.get(fld)
                    if old is None or old == val:
                        continue
                    if fld in ABIL_ENUM_FIELDS:
                        of_, nf_, pol = _humanize_enum(old), _humanize_enum(val), 'hi'
                    else:
                        of_, nf_ = _slash(old), _slash(val)
                        pol = 'lo' if _abil_lower_better(fld) else 'hi'
                    # Skip no-op diffs that only differ before formatting
                    # (e.g. "6.0" → "6", or "6 6 6" → "6").
                    if of_ == nf_:
                        continue
                    entries.append((v, dt, 'F', _abil_field_label(fld), of_, nf_, pol))
            prev_slug, prev_fields = cur, cur_fields
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
        'gold':          _gold_vf,
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
    COLUMNS = [
        ('lvl',          'Lvl'),
        ('icon',         ''),
        ('name',         'Unit'),
        ('hp',           'HP'),
        ('hp_regen',     'HP/sec'),
        # EHP физ/маг hidden — still computed into row data for the future
        # extended-columns toggle.
        ('mp',           'MP'),
        ('mp_regen',     'MP/sec'),
        ('armor',        'Armor'),
        ('armor_pct',    'Armor (%)'),
        ('magres',       'Mag. resist'),
        # Урон (мин)/(макс) hidden — values still pulled into row data for the
        # future extended-columns toggle. Only the computed average is shown.
        ('dmg_avg',      'Attack Dmg'),
        ('as',           'AS'),
        ('t_per_attack', 'Time to hit'),
        ('bat',          'BAT'),
        ('ms',           'MS'),
        # Золото shows the average; min/max stay in row data for the extended
        # toggle (separate min/max gold columns later).
        ('gold',         'Gold'),
        ('xp',           'XP'),
        ('attack_range', 'Attack Range'),
        ('attack_type',  'Attack Type'),
        ('vision',       'Vision'),
        # «Дальность агра» (aggro) hidden — kept in row data for the extended
        # toggle. New movement/projectile columns slot in after Обзор.
        ('ap',             'AP'),
        ('turn_rate',      'Turn Rate'),
        ('collision_size', 'Collision Size'),
        ('bound_radius',   'Bound Radius'),
        ('projectile',     'Projectile Speed'),
        ('ability1',     'Ability 1'),
        ('ability2',     'Ability 2'),
        ('ability3',     'Ability 3'),
    ]
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
            if csv_atk:
                data['attack_type'] = csv_atk
        rendered.append({'data': data, 'tier_break': is_break,
                          'level': level_for_row, 'npc_key': npc_key})
    # No rowspan merge: every row carries its own level cell so the table
    # can be re-sorted by any column. scripts.js collapses repeated level
    # numbers in the current row order (showing the number once per run +
    # a divider) to keep the grouped look in the default/level-sorted view.

    # ---- HTML emission ----
    nav = _site.render_top_nav('creeps', _latest_href(), patch_context=False)
    # No colgroup: table-layout: auto lets the browser size each column
    # to fit content (and each header) on one line. Headers and cells
    # are explicitly centred via CSS so the auto-width math doesn't have
    # to budget for tag-width differences across columns.
    # Columns that get a vertical separator on their RIGHT edge — they
    # group the table into logical sections (identity | survivability |
    # offense | economy | utility | abilities).
    SEP_AFTER = {'lvl', 'name', 'mp_regen', 'bat', 'vision', 'projectile'}
    # Identity columns pinned to the left edge during horizontal scroll
    # (scripts.js computes their cumulative left offsets after layout).
    STICKY_COLS = {'lvl', 'icon', 'name'}

    def _col_cls(k, value=''):
        cls = [f'col-{k}']
        if k in STICKY_COLS:
            cls.append('sticky-col')
        if k in SEP_AFTER:
            cls.append('col-sep')
        if k == 'attack_type':
            if value == 'Обычный':
                cls.append('atk-basic')
            elif value == 'Проникающий':
                cls.append('atk-pierce')
        return ' '.join(cls)

    def _label_html(label):
        """Header label HTML. A '\\n' splits it into a main line + a small
        sub-line below (used by EHP columns: "EHP" over a tiny "физ"/"маг"
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
        if k == 'name':
            thead_list.append(
                f'<th class="{_col_cls(k)} sortable" colspan="2" '
                f'data-col="{k}" data-idx="{name_idx}">'
                f'<span class="th-label">{_label_html(label)}</span>'
                f'<span class="sort-ind"></span></th>'
            )
        elif not label:
            thead_list.append(f'<th class="{_col_cls(k)}"></th>')
        else:
            thead_list.append(
                f'<th class="{_col_cls(k)} sortable" data-col="{k}" '
                f'data-idx="{i}">'
                f'<span class="th-label">{_label_html(label)}</span>'
                f'<span class="sort-ind"></span></th>'
            )
    thead_cells = ''.join(thead_list)

    def _cell_inner(k, v, d):
        """Inner HTML for a data cell. Attack Range gets a glass melee/ranged
        icon badge to the right of the number."""
        if k == 'attack_range' and v:
            typ = 'ranged' if d.get('attack_range_ranged') else 'melee'
            return (f'{_esc(v)}<span class="atk-badge atk-{typ}">'
                    f'<img src="icons/ui/atk_{typ}.png" alt="{typ}" '
                    f'loading="lazy"></span>')
        return _esc(v) if v else '&nbsp;'

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
                if hist:
                    extra = f' data-hist="{_esc(payload)}"'
                    cls += ' has-history'
                cells.append(
                    f'<td class="{cls}"{extra}>{_cell_inner(k, v, d)}</td>'
                )
            else:
                cells.append(f'<td class="{_col_cls(k, v)}">{_cell_inner(k, v, d)}</td>')
        body_parts.append(f'<tr{tr_cls}>{"".join(cells)}</tr>')

    html = (
        '<!DOCTYPE html>\n'
        '<html lang="ru">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<title>Sloppy - Creeps Table</title>\n'
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
        '<table class="creeps-table">\n'
        f'<thead><tr>{thead_cells}</tr></thead>\n'
        f'<tbody>\n{chr(10).join(body_parts)}\n</tbody>\n'
        '</table>\n'
        '</div>\n'
        '</div>\n'
        f'<script src="scripts.js?v={ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n'
    )
    with open('creeps.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  → creeps.html: {len(html):,} bytes")

if __name__ == "__main__":
    save_creeps_html()
