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
    # Reads tracked fields per neutral from every
    # data/stats/<patch>/units.json, walks them chronologically, and
    # records each change for the per-cell changelog tooltips. Patch dates
    # come from data/site_meta.json (written by build_patch.py).
    #   HP, Armor, Mana → present 115/115.
    #   MagicalResistance → absent from units.json (neutrals default to 0),
    #     so its history is always empty; wired up for completeness.
    HIST_FIELDS = ('StatusHealth', 'ArmorPhysical', 'StatusMana',
                   'MagicalResistance')
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

    _patches_chrono = []
    if _os.path.isdir(STATS_DIR):
        _patches_chrono = sorted(
            (d for d in _os.listdir(STATS_DIR)
             if _os.path.isdir(_os.path.join(STATS_DIR, d))),
            key=_ver_key,
        )
    # _stat_by_patch[field][version] = {npc_key: value}
    _stat_by_patch = {f: {} for f in HIST_FIELDS}
    for _v in _patches_chrono:
        _up = _os.path.join(STATS_DIR, _v, "units.json")
        if not _os.path.exists(_up):
            continue
        try:
            _u = _json.loads(open(_up, encoding="utf-8").read())
        except Exception:
            continue
        for _f in HIST_FIELDS:
            _stat_by_patch[_f][_v] = {
                k: val.get(_f)
                for k, val in _u.items()
                if isinstance(val, dict) and val.get(_f) is not None
            }

    def _stat_history(npc_key, field):
        """List of (patch, date, old, new) changes of `field` for a
        neutral, chronological. Empty if no recorded changes."""
        if not npc_key:
            return []
        changes = []
        prev = None
        by_patch = _stat_by_patch.get(field, {})
        for _v in _patches_chrono:
            cur = by_patch.get(_v, {}).get(npc_key)
            if cur is None:
                continue
            if prev is not None and cur != prev:
                changes.append((_v, PATCH_DATES.get(_v, ""), prev, cur))
            prev = cur
        return changes

    # Column key → units.json field for the changelog tooltip.
    HIST_COL_FIELD = {
        'hp':     'StatusHealth',
        'armor':  'ArmorPhysical',
        'mp':     'StatusMana',
        'magres': 'MagicalResistance',
    }

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

    def _attack_type(npc):
        """Heuristic: melee attack capability → "Обычный" (Hero), ranged
        → "Проникающий" (Pierce). Matches the CSV's authored values."""
        cap = npc.get('AttackCapabilities', '')
        if 'RANGED' in cap:
            return 'Проникающий'
        return 'Обычный'

    def _attack_range_label(npc):
        rng = _safe_int(npc.get('AttackRange'), 0)
        cap = npc.get('AttackCapabilities', '')
        if 'RANGED' in cap or rng > 200:
            return _fmt_num(rng)
        return f'Ближняя ({rng})' if rng else ''

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
            'gold':          f'{gold_min}-{gold_max}' if (gold_min or gold_max) else '',
            'gold_avg':      _fmt_num(gold_avg) if gold_avg else '',
            'xp':            _fmt_num(xp) if xp else '',
            'attack_range':  _attack_range_label(npc),
            'attack_type':   _attack_type(npc) if npc else '',
            'vision':        f'{vis_day}/{vis_night}' if vis_day and vis_night else '',
            'aggro':         aggro,
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

    # ---- Read CSV ----
    csv_rows = list(_csv.reader(open(csv_path, encoding='utf-8')))
    body_rows = csv_rows[1:]

    # ---- Column structure ----
    COLUMNS = [
        ('lvl',          'Ур.'),
        ('icon',         ''),
        ('name',         'Юнит'),
        ('hp',           'HP'),
        ('hp_regen',     'HP/sec'),
        ('ehp_phys',     'EHP (физ)'),
        ('ehp_mag',      'EHP (маг)'),
        ('mp',           'MP'),
        ('mp_regen',     'МП/сек'),
        ('armor',        'Броня'),
        ('armor_pct',    'Броня (%)'),
        ('magres',       'Магрез'),
        ('dmg_min',      'Урон (мин)'),
        ('dmg_max',      'Урон (макс)'),
        ('dmg_avg',      'Ср. урон'),
        ('as',           'АС'),
        ('t_per_attack', 't/1 удар'),
        ('bat',          'BAT'),
        ('ms',           'МС'),
        ('gold',         'Золото'),
        ('gold_avg',     'Ср. золото'),
        ('xp',           'Опыт'),
        ('attack_range', 'Дальность атаки'),
        ('attack_type',  'Тип атаки'),
        ('vision',       'Обзор'),
        ('aggro',        'Дальность агра'),
        ('ability1',     'Способность 1'),
        ('ability2',     'Способность 2'),
        ('ability3',     'Способность 3'),
    ]
    COL_WIDTHS = {
        'lvl': 30, 'icon': 56, 'name': 170, 'createhero': 130,
        'hp': 50, 'hp_regen': 52, 'mp': 50, 'mp_regen': 52,
        'armor': 52, 'armor_pct': 64, 'ehp_phys': 64, 'magres': 56,
        'ehp_mag': 64, 'dmg_min': 64, 'dmg_max': 70, 'dmg_avg': 60,
        'as': 38, 't_per_attack': 58, 'bat': 38, 'ms': 38,
        'gold': 56, 'gold_avg': 64, 'xp': 42, 'attack_range': 110,
        'attack_type': 100, 'vision': 70, 'aggro': 70,
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
    SEP_AFTER = {'lvl', 'name', 'ehp_mag', 'bat', 'aggro'}
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
                f'<span class="th-label">{_esc(label)}</span>'
                f'<span class="sort-ind"></span></th>'
            )
        elif not label:
            thead_list.append(f'<th class="{_col_cls(k)}"></th>')
        else:
            thead_list.append(
                f'<th class="{_col_cls(k)} sortable" data-col="{k}" '
                f'data-idx="{i}">'
                f'<span class="th-label">{_esc(label)}</span>'
                f'<span class="sort-ind"></span></th>'
            )
    thead_cells = ''.join(thead_list)

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
            elif k in HIST_COL_FIELD:
                # Stat cell (HP / Armor / Mana / Magres) carries its full
                # change history as a compact data attribute
                # (patch|date|old|new;...) — scripts.js renders a changelog
                # tooltip on hover. Only emitted when the unit actually has
                # recorded changes for that field.
                hist = _stat_history(row.get('npc_key'), HIST_COL_FIELD[k])
                extra = ''
                cls = _col_cls(k, v)
                if hist:
                    payload = ';'.join(
                        f'{p}|{dt}|{ov}|{nv}' for (p, dt, ov, nv) in hist
                    )
                    extra = f' data-hist="{_esc(payload)}"'
                    cls += ' has-history'
                cells.append(
                    f'<td class="{cls}"{extra}>{_esc(v) if v else "&nbsp;"}</td>'
                )
            else:
                cells.append(f'<td class="{_col_cls(k, v)}">{_esc(v) if v else "&nbsp;"}</td>')
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
