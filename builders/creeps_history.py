"""Per-stat history across all patches (7.08 → latest) for the Neutral Stats
per-cell changelog tooltips (builders/creeps.py).

Walks data/stats/<patch>/npc_units.json chronologically and records each
change per neutral. npc_units.json (written by scripts/fetch/fetch_npc_history.py
from dotabuff/d2vpkr) is the full Valve KV, present for all 115 patches — so
EVERY stat column can carry history, raw or derived. Patch dates come from
site_meta.json. Ability cells use npc_abilities.json (written by
scripts/fetch/fetch_ability_history.py) for their value changelog.
"""
import json as _json
import os as _os
import re
from dataclasses import dataclass

from builders.creeps_common import (
    ABILITY_SKIP, HULL_BOUNDS, NEUTRAL_DEFAULT_HULL, NEUTRAL_DEFAULT_TURN_RATE,
    ability_dname, armor_factor, ehp_mag_val, ehp_phys_val, fmt_num,
)

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
STATS_DIR = _os.path.join(_HERE, "data", "stats")
META_PATH = _os.path.join(_HERE, "data", "site_meta.json")

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


@dataclass(frozen=True)
class StatHistory:
    """Everything the changelog tooltips read, loaded once per build."""
    patches: tuple        # versions with a data/stats/<v>/ folder, chronological
    patch_dates: dict     # version → release date (site_meta.json)
    raw_by_patch: dict    # [field][version] = {npc_key: parsed_value}
    abil_by_patch: dict   # [version][slug] = {field: value}


# ---- Loading ----

def _ver_key(v):
    return tuple(int(p) if p.isdigit() else p
                 for p in re.split(r'(\d+)', v))


def _num(x):
    """Parse a KV value to int/float (integral floats → int), else str."""
    try:
        f = float(x)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return x


def _load_patch_dates():
    try:
        meta = _json.loads(open(META_PATH, encoding="utf-8").read())
        return meta.get("patch_dates", {})
    except Exception:
        return {}


def _list_patches():
    if not _os.path.isdir(STATS_DIR):
        return ()
    return tuple(sorted(
        (d for d in _os.listdir(STATS_DIR)
         if _os.path.isdir(_os.path.join(STATS_DIR, d))),
        key=_ver_key,
    ))


def _load_raw_by_patch(patches):
    """raw_by_patch[field][version] = {npc_key: parsed_value}."""
    raw_by_patch = {f: {} for f in RAW_HIST_FIELDS}
    for v in patches:
        np_path = _os.path.join(STATS_DIR, v, "npc_units.json")
        if not _os.path.exists(np_path):
            continue
        try:
            npc = _json.loads(open(np_path, encoding="utf-8").read())
        except Exception:
            continue
        for f in RAW_HIST_FIELDS:
            raw_by_patch[f][v] = {k: _num(entry[f]) for k, entry in npc.items()
                                  if isinstance(entry, dict) and entry.get(f) is not None}
    return raw_by_patch


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


def _load_abil_by_patch(patches):
    """Per-patch neutral ability balance data (from npc_abilities.json).
    abil_by_patch[version][slug] = {field: value} — used for the ability-cell
    value changelog."""
    abil_by_patch = {}
    for v in patches:
        ap_path = _os.path.join(STATS_DIR, v, "npc_abilities.json")
        if not _os.path.exists(ap_path):
            continue
        try:
            raw_ab = _json.loads(open(ap_path, encoding="utf-8").read())
            abil_by_patch[v] = {s: _norm_abil_fields(f) for s, f in raw_ab.items()}
        except Exception:
            abil_by_patch[v] = {}
    return abil_by_patch


def load_history():
    patches = _list_patches()
    return StatHistory(
        patches=patches,
        patch_dates=_load_patch_dates(),
        raw_by_patch=_load_raw_by_patch(patches),
        abil_by_patch=_load_abil_by_patch(patches),
    )


# ---- Stat value history ----

def raw_at(hist, field, version, npc_key):
    return hist.raw_by_patch.get(field, {}).get(version, {}).get(npc_key)


def value_history(hist, npc_key, valuefn):
    """List of (patch, date, old, new) changes, chronological. `valuefn`
    maps (hist, version, npc_key) → display string for that patch (or None
    when the stat is absent). Consecutive distinct values are recorded."""
    if not npc_key:
        return []
    changes = []
    prev = None
    for v in hist.patches:
        cur = valuefn(hist, v, npc_key)
        if cur is None or cur == '':
            continue
        if prev is not None and cur != prev:
            changes.append((v, hist.patch_dates.get(v, ""), prev, cur))
        prev = cur
    return changes


# ---- Per-column changelog value functions ----
# Each maps (hist, version, npc_key) → the column's display value for that
# patch (or None when absent). value_history diffs consecutive distinct values.
# Raw columns read a single KV field; derived ones recompute from raw
# fields exactly as builders/creeps.py _row_data does for the current patch.
def _raw_vf(field):
    def f(hist, version, npc_key):
        x = raw_at(hist, field, version, npc_key)
        return fmt_num(x) if x is not None else None
    return f


def _dmg_avg_vf(hist, version, npc_key):
    mn = raw_at(hist, 'AttackDamageMin', version, npc_key)
    mx = raw_at(hist, 'AttackDamageMax', version, npc_key)
    if mn is None and mx is None:
        return None
    return fmt_num(-(-((mn or 0) + (mx or 0)) // 2))  # round up


def _gold_vf(hist, version, npc_key):
    gmn = raw_at(hist, 'BountyGoldMin', version, npc_key)
    gmx = raw_at(hist, 'BountyGoldMax', version, npc_key)
    if gmn is None and gmx is None:
        return None
    return fmt_num(-(-((gmn or 0) + (gmx or 0)) // 2))  # round up


def _ehp_phys_vf(hist, version, npc_key):
    hp = raw_at(hist, 'StatusHealth', version, npc_key)
    a = raw_at(hist, 'ArmorPhysical', version, npc_key)
    if not hp or a is None:
        return None
    return fmt_num(ehp_phys_val(hp, a))


def _ehp_mag_vf(hist, version, npc_key):
    hp = raw_at(hist, 'StatusHealth', version, npc_key)
    if not hp:
        return None
    mr = raw_at(hist, 'MagicalResistance', version, npc_key) or 0
    return fmt_num(ehp_mag_val(hp, mr))


def _armor_pct_vf(hist, version, npc_key):
    a = raw_at(hist, 'ArmorPhysical', version, npc_key)
    if a is None:
        return None
    return f'{round(armor_factor(a) * 100)}%'


def _t_per_attack_vf(hist, version, npc_key):
    bat = raw_at(hist, 'AttackRate', version, npc_key)
    if not bat:
        return None
    ats = raw_at(hist, 'BaseAttackSpeed', version, npc_key) or 100
    return fmt_num(round(bat * 100 / ats, 2)) if ats else fmt_num(bat)


def _vision_vf(hist, version, npc_key):
    d = raw_at(hist, 'VisionDaytimeRange', version, npc_key)
    n = raw_at(hist, 'VisionNighttimeRange', version, npc_key)
    if d is None and n is None:
        return None
    return '{}/{}'.format(fmt_num(d) if d is not None else '?',
                          fmt_num(n) if n is not None else '?')


def _hull_vf(idx):
    """History valuefn for hull-derived collision (idx 0) / bound (idx 1).
    Unit present that patch → hull (explicit or HERO default) → value."""
    def f(hist, version, npc_key):
        if raw_at(hist, 'StatusHealth', version, npc_key) is None:
            return None  # unit doesn't exist this patch
        hull = raw_at(hist, 'BoundsHullName', version, npc_key) or NEUTRAL_DEFAULT_HULL
        v = HULL_BOUNDS.get(hull, (None, None))[idx]
        return fmt_num(v) if v is not None else None
    return f


def _projectile_vf(hist, version, npc_key):
    s = raw_at(hist, 'ProjectileSpeed', version, npc_key)
    if s is None:
        return None
    return fmt_num(s) if s else '-'


def _turn_rate_vf(hist, version, npc_key):
    if raw_at(hist, 'StatusHealth', version, npc_key) is None:
        return None  # unit doesn't exist this patch
    tr = raw_at(hist, 'MovementTurnRate', version, npc_key)
    return fmt_num(tr if tr is not None else NEUTRAL_DEFAULT_TURN_RATE)


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


# ---- Ability cell changelog ----

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

# Fields where a DECREASE is the buff (green), like the changelog l=True.
ABIL_LOWER_BETTER = {
    'AbilityCooldown', 'AbilityManaCost', 'AbilityCastPoint',
    'AbilityChannelTime',
}

# Ability cells use a richer changelog (presence + value changes) that
# returns typed entries directly, not a per-patch value: column → ability slot.
COL_CHANGELOG = {'ability1': 0, 'ability2': 1, 'ability3': 2}


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
    each token trimmed (12.0 → 12) via fmt_num."""
    return '/'.join(fmt_num(t) for t in str(s).split())


def _abilities_at(hist, abil_slim, version, npc_key):
    """Filtered ability dnames for a neutral at a patch (same filter as
    _row_data: skip hidden markers). Mirrors the displayed slot order."""
    out = []
    for i in range(1, 6):
        slug = raw_at(hist, f'Ability{i}', version, npc_key)
        if not slug or slug in ABILITY_SKIP:
            continue
        out.append(ability_dname(slug, abil_slim))
    return out


def _ability_slugs_at(hist, version, npc_key):
    """Filtered ability SLUGS for a neutral at a patch (slot order)."""
    out = []
    for i in range(1, 6):
        slug = raw_at(hist, f'Ability{i}', version, npc_key)
        if not slug or slug in ABILITY_SKIP:
            continue
        out.append(slug)
    return out


def _current_slot_slug(hist, npc_key, slot):
    """The ability currently shown in `slot` (latest patch with the unit)."""
    for v in reversed(hist.patches):
        if raw_at(hist, 'StatusHealth', v, npc_key) is None:
            continue
        slugs = _ability_slugs_at(hist, v, npc_key)
        return slugs[slot] if slot < len(slugs) else None
    return None


def _field_changes(prev_fields, fields):
    """(label, old, new, polarity) for every ability value that changed
    between two consecutive patches."""
    out = []
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
        out.append((_abil_field_label(fld), of_, nf_, pol))
    return out


def ability_changelog(hist, abil_slim, npc_key, slot):
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
    cur_slug = _current_slot_slug(hist, npc_key, slot)
    if not cur_slug:
        return []
    first_patch = hist.patches[0] if hist.patches else None
    entries = []
    prev_present = False
    prev_fields = None
    started = False
    for v in hist.patches:
        if raw_at(hist, 'StatusHealth', v, npc_key) is None:
            continue  # unit absent this patch
        present = cur_slug in _ability_slugs_at(hist, v, npc_key)
        fields = hist.abil_by_patch.get(v, {}).get(cur_slug, {}) if present else {}
        dt = hist.patch_dates.get(v, '')
        if not started:
            started = True
            if v == first_patch:
                # data baseline — adopt silently (was there since 7.08)
                prev_present, prev_fields = present, fields
                continue
            # else first appearance is mid-history → fall through to ADDED
        if present and not prev_present:
            entries.append((v, dt, 'A', ability_dname(cur_slug, abil_slim)))
        if present and prev_present and prev_fields:
            entries.extend((v, dt, 'F') + ch for ch in _field_changes(prev_fields, fields))
        prev_present, prev_fields = present, fields
    return entries
