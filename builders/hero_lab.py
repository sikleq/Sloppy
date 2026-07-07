"""Build hero_lab.html: side-by-side hero + item stat calculator.

The page is current-patch first. Hero base data comes from the same latest
stats files as Hero Stats; item passive bonuses come from the current
items.txt AbilityValues / AbilitySpecial blocks, with items.json used only for
cost fallback.
"""
from __future__ import annotations

import html as _html
import json as _json
import re as _re
import sys as _sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_ROOT))
_sys.path.insert(0, str(_ROOT / "builders"))

import builders.site_common as _site
from mana_items import parse_kv
from heroes_stats import (
    _HERE,
    STATS_DIR,
    _versions,
    _ge,
    _load_display_names,
    _display_name,
    _load_raw_heroes,
    _inject_spirit_bear,
    _row_stats,
    _attack_type,
    _EXCLUDE,
    SPIRIT_BEAR_HERO,
)

_esc = lambda s: _html.escape(str(s), quote=True)

_LOC_RE = _re.compile(r'"(DOTA_[^"]+)"\s+"((?:[^"\\]|\\.)*)"', _re.IGNORECASE)


def _load_item_tooltips() -> dict[str, dict]:
    """Parse abilities_english.txt for item tooltip data (desc, lore, stat labels)."""
    path = _HERE / "data" / "abilities_english.txt"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    entries: dict[str, str] = {}
    for m in _LOC_RE.finditer(text):
        k, v = m.group(1), m.group(2).replace('\\"', '"')
        if " " in k:
            continue
        entries[k.lower()] = v
    out: dict[str, dict] = {}
    prefix = "dota_tooltip_ability_"
    for key, val in entries.items():
        if not key.startswith(prefix + "item_"):
            continue
        rest = key[len(prefix):]  # e.g. "item_cyclone_description"
        if rest.endswith("_description"):
            item_id = rest[:-len("_description")]
            out.setdefault(item_id, {})["desc"] = val
        elif rest.endswith("_lore"):
            pass
    # Collect stat labels — match attr keys to known item ids
    attr_keys: list[tuple[str, str]] = []  # (rest, val)
    for key, val in entries.items():
        if not key.startswith(prefix + "item_"):
            continue
        rest = key[len(prefix):]
        if rest.endswith("_description") or rest.endswith("_lore"):
            continue
        if "_note" in rest or "_searchalias" in rest or ":f" in rest or ":n" in rest or "_bound" in rest:
            continue
        attr_keys.append((rest, val))
    # Build a set of all known item ids.  Description-only discovery misses
    # pure stat items and enchantments, whose localization often consists of
    # only a name plus attribute/Note rows.
    all_item_ids = set(out.keys())
    all_item_ids.update(_load_item_names().keys())
    # Also discover enchantment items from name keys
    name_prefix = "dota_tooltip_ability_"
    for key in entries:
        if key.startswith(name_prefix + "item_enhancement_") and "_" not in key[len(name_prefix) + len("item_enhancement_"):].lstrip("abcdefghijklmnopqrstuvwxyz0123456789_"):
            rest = key[len(name_prefix):]
            if not rest.endswith("_description") and not rest.endswith("_lore") and "_note" not in rest and ":f" not in rest:
                all_item_ids.add(rest)
    # Simple approach: for each attr key, find the longest known item_id prefix
    for rest, val in attr_keys:
        if rest in all_item_ids:
            continue
        best = ""
        for item_id in all_item_ids:
            if rest.startswith(item_id + "_") and len(item_id) > len(best):
                best = item_id
        if not best:
            # Try to match as item_enhancement_X_statname
            parts = rest.split("_")
            if len(parts) >= 4 and parts[0] == "item" and parts[1] == "enhancement":
                candidate = "_".join(parts[:3])
                best = candidate
                all_item_ids.add(candidate)
        if best:
            field = rest[len(best) + 1:] if rest.startswith(best + "_") else ""
            out.setdefault(best, {}).setdefault("attribs", []).append({
                "text": val,
                "field": field,
            })

    # Notes carry gameplay restrictions that are part of Valve's tooltip
    # (stacking rules, target limitations, exceptions).  They were previously
    # discarded, which made several item descriptions materially incomplete.
    for item_id in all_item_ids:
        note_prefix = prefix + item_id + "_note"
        notes = [
            (key, val) for key, val in entries.items()
            if key.startswith(note_prefix) and val
        ]
        if notes:
            notes.sort(key=lambda pair: pair[0])
            out.setdefault(item_id, {})["notes"] = [val for _, val in notes]
    return out


def _load_ability_tooltips() -> dict[str, dict[str, str]]:
    """Parse abilities_english.txt for ability names/descriptions."""
    path = _HERE / "data" / "abilities_english.txt"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    entries: dict[str, str] = {}
    for m in _LOC_RE.finditer(text):
        k, v = m.group(1), m.group(2).replace('\\"', '"')
        entries[k.lower()] = v
    out: dict[str, dict[str, str]] = {}
    prefix = "dota_tooltip_ability_"
    for key, val in entries.items():
        if not key.startswith(prefix):
            continue
        rest = key[len(prefix):]
        if rest.endswith("_description"):
            out.setdefault(rest[:-len("_description")], {})["desc"] = val
        elif rest.endswith("_lore"):
            continue
        elif "_note" not in rest and ":f" not in rest and not rest.endswith("_facet"):
            out.setdefault(rest, {})["name"] = val
    return out


def _load_item_npedesc() -> dict[str, str]:
    """Parse dota_english.txt for item short descriptions (npedesc)."""
    path = _HERE / "data" / "dota_english.txt"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for m in _LOC_RE.finditer(text):
        k, v = m.group(1), m.group(2)
        if k.endswith("_npedesc") and k.startswith("item_"):
            out["item_" + k.removesuffix("_npedesc").removeprefix("item_")] = v
    return out


def _latest_href() -> str:
    from patch.meta import latest_patch_filename as _lpf
    _fallback = _lpf()
    try:
        meta = _json.loads((_HERE / "data" / "site_meta.json").read_text(encoding="utf-8"))
        return meta.get("latest_patch_filename", _fallback)
    except Exception:
        return _fallback


def _num(v) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    m = _re.search(r"-?\d+(?:\.\d+)?", str(v or ""))
    return float(m.group(0)) if m else 0.0


def _load_item_names() -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        data = _json.loads((_HERE / "data" / "itemlist.json").read_text(encoding="utf-8"))
        for it in data["result"]["data"]["itemabilities"]:
            name = it.get("name")
            label = it.get("name_english_loc") or it.get("name_loc") or ""
            if name and label:
                out[name] = label.replace("\n", " ")
    except Exception:
        pass
    return out


def _slug_from_item(item: str) -> str:
    return item.removeprefix("item_")


def _load_item_meta() -> dict[str, dict]:
    try:
        dyn = _json.loads((_HERE / "_dynamics.json").read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, dict] = {}
    for rec in dyn.get("items", []):
        if not rec.get("current"):
            continue
        icon = rec.get("icon")
        if not icon:
            continue
        out[f"item_{icon}"] = {
            "class": rec.get("class", "regular"),
            "category": rec.get("category"),
            "tier": rec.get("tier"),
            "icon": icon,
        }
    return out


def _flatten_special(d: dict) -> dict[str, object]:
    out: dict[str, object] = {}

    def walk(node, parent_key: str = ""):
        if not isinstance(node, dict):
            return
        for k, v in node.items():
            if isinstance(v, dict):
                if "value" in v and parent_key == "":
                    out.setdefault(k, v["value"])
                walk(v, k)
            elif k not in out:
                out[k] = v

    walk(d.get("AbilityValues", {}))
    walk(d.get("AbilitySpecial", {}))
    return out


# Neutral-item primary stats — variable name → (display label, is-percent).
# In-game the tooltip shows these as "+N <Label>" rows above the ability bar.
# Sourced from AbilityValues flagged `apply_curio_bonus: 1`, which is Valve's
# marker for "this value is the headline scalable bonus".
_NEUTRAL_STAT_LABELS = {
    "spell_amp":           ("Spell Amplification",   True),
    "manacost_reduction":  ("Mana Cost Reduction",   True),
    "heal_reduce":         ("Heal Reduction",        True),
    "damage":              ("Damage",                False),
    "damage_illusions":    ("Damage vs Illusions",   False),
    "damage_creep":        ("Damage vs Creeps",      False),
    "summon_duration":     ("Summon Duration",       False),
    "bonus_damage":        ("Damage",                False),
    "bonus_armor":         ("Armor",                 False),
    "bonus_attack_speed":  ("Attack Speed",          False),
    "bonus_movement_speed":("Movement Speed",        False),
    "bonus_strength":      ("Strength",              False),
    "bonus_agility":       ("Agility",               False),
    "bonus_intellect":     ("Intelligence",          False),
    "bonus_all_stats":     ("All Attributes",        False),
    "bonus_health":        ("Health",                False),
    "bonus_mana":          ("Mana",                  False),
    "bonus_mp_regen":      ("Mana Regeneration",     False),
    "bonus_hp_regen":      ("Health Regeneration",   False),
    "magic_resistance":    ("Magic Resistance",      True),
    "evasion":             ("Evasion",               True),
    "lifesteal":           ("Lifesteal",             True),
    "spell_lifesteal":     ("Spell Lifesteal",       True),
    "status_resist":       ("Status Resistance",     True),
    "cooldown_reduction":  ("Cooldown Reduction",    True),
    "debuff_amp":          ("Debuff Amplification",  True),
}


def _neutral_curio_bonuses(data: dict) -> list[dict]:
    """Return AbilityValues flagged apply_curio_bonus=1 as headline stat rows
    (the "+6% Spell Amplification" lines you see above the ability bar in-game
    on neutrals). Falls back to a Title-Cased label when the variable name
    isn't in _NEUTRAL_STAT_LABELS."""
    out: list[dict] = []
    av = data.get("AbilityValues") or {}
    for varname, node in av.items():
        if not isinstance(node, dict):
            continue
        if str(node.get("apply_curio_bonus", "")) != "1":
            continue
        raw = node.get("value")
        if raw is None:
            continue
        # Take the first level only (curio values are typically single-level).
        s = str(raw).split(" ")[0]
        try:
            n = float(s)
            val_str = str(int(n)) if n == int(n) else s
        except ValueError:
            val_str = s
        label, is_pct = _NEUTRAL_STAT_LABELS.get(
            varname, (varname.replace("_", " ").title(), False)
        )
        out.append({"value": val_str, "label": label, "pct": is_pct})
    return out


def _first(fields: dict, *keys: str) -> float:
    for k in keys:
        if k in fields:
            return _num(fields[k])
    return 0.0


def _sum(fields: dict, *keys: str) -> float:
    return sum(_num(fields.get(k, 0)) for k in keys)


def _num_at(v, idx: int) -> float:
    parts = str(v or "").split()
    s = parts[idx] if idx < len(parts) else parts[-1] if parts else "0"
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _sum_at(fields: dict, idx: int, *keys: str) -> float:
    return sum(_num_at(fields.get(k, 0), idx) for k in keys)


def _item_bonus_at(fields: dict, idx: int) -> dict[str, float]:
    return {
        "all": _num_at(fields.get("bonus_all_stats", fields.get("bonus_stats", fields.get("all_stats", 0))), idx),
        "str": _sum_at(fields, idx, "bonus_strength", "bonus_str", "strength"),
        "agi": _sum_at(fields, idx, "bonus_agility", "bonus_agi", "agility"),
        "int": _sum_at(fields, idx, "bonus_intellect", "bonus_int", "bonus_intelligence"),
        "hp": _sum_at(fields, idx, "bonus_health", "bonus_hp", "bonus_max_health", "health_bonus"),
        "mp": _sum_at(fields, idx, "bonus_mana", "max_mana", "bonus_max_mana"),
        "hpr": _sum_at(fields, idx, "bonus_health_regen", "bonus_hp_regen", "hp_regen", "bonus_regen", "health_regen", "aura_health_regen"),
        "mpr": _sum_at(fields, idx, "bonus_mana_regen", "bonus_mp_regen", "mp_regen", "mana_regen", "aura_mana_regen", "mana_regen_aura"),
        "armor": _sum_at(fields, idx, "bonus_armor", "aura_bonus_armor", "armor", "armor_aura", "bonus_aoe_armor"),
        "mr": _sum_at(fields, idx, "bonus_magic_resistance", "bonus_magical_armor", "bonus_spell_resist", "magic_resistance", "magic_resist", "magic_resistance_aura", "magic_res"),
        "evasion": _sum_at(fields, idx, "bonus_evasion", "evasion"),
        "damage": _sum_at(fields, idx, "bonus_damage", "damage_aura", "base_attack_damage", "damage"),
        "aspd": _sum_at(fields, idx, "bonus_attack_speed", "attack_speed"),
        "ms": _sum_at(fields, idx, "bonus_movement_speed", "bonus_move_speed", "movement_speed", "aura_movement_speed", "bonus_movement", "movespeed"),
        "range": _sum_at(fields, idx, "bonus_attack_range", "attack_range_bonus", "attack_range"),
        "rangeUniqueAll": _sum_at(fields, idx, "melee_attack_range"),
        "rangeUniqueRanged": _sum_at(fields, idx, "base_attack_range"),
        "dvision": _sum_at(fields, idx, "bonus_day_vision", "bonus_vision"),
        "nvision": _sum_at(fields, idx, "bonus_night_vision", "night_vision_bonus"),
        "spellAmp": _sum_at(fields, idx, "spell_amp", "bonus_spell_amp"),
        "statusRes": _sum_at(fields, idx, "status_resistance", "status_resist"),
        "slowRes": _sum_at(fields, idx, "slow_resistance", "slow_resist", "bonus_slow_resist"),
        "hprAmp": 0,
        "mprAmp": _sum_at(fields, idx, "mana_regen_multiplier"),
        "castRange": _sum_at(fields, idx, "bonus_cast_range", "cast_range_bonus", "cast_range"),
        "lifesteal": _sum_at(fields, idx, "attack_lifesteal", "lifesteal", "lifesteal_percent"),
        "spellLifesteal": _sum_at(fields, idx, "spell_lifesteal", "bonus_spell_lifesteal"),
        "mpPct": _sum_at(fields, idx, "bonus_max_mana_percentage", "max_mana_pct"),
        "batReduce": _sum_at(fields, idx, "bat_reduce"),
        "healthRestoration": _sum_at(fields, idx, "health_restoration", "hp_regen_amp", "heal_amp"),
        "cooldownReduction": _sum_at(fields, idx, "cooldown_reduction", "bonus_cooldown"),
        "incomingDamage": _sum_at(fields, idx, "incoming_damage"),
        "magicDamage": _sum_at(fields, idx, "magic_damage"),
        "castSpeed": _sum_at(fields, idx, "cast_speed"),
        "visionReduce": _sum_at(fields, idx, "vision_reduce"),
        "manacostIncrease": _sum_at(fields, idx, "cost_increase"),
        "intelligencePct": _sum_at(fields, idx, "intelligence_pct"),
        "hpPct": _sum_at(fields, idx, "max_health"),
        "maxHpRegen": _sum_at(fields, idx, "max_health_regen"),
        "hpRegenReduce": _sum_at(fields, idx, "hp_regen_reduce"),
        "knockbackResist": _sum_at(fields, idx, "knockback_resist"),
        "msPct": _sum_at(fields, idx, "movespeed_pct", "movement_speed_percent_bonus"),
        "manacostReduction": _sum_at(fields, idx, "manacost_reduction"),
        "debuffAmp": _sum_at(fields, idx, "debuff_amp"),
        "gpm": _sum_at(fields, idx, "bonus_gpm"),
        "xpm": _sum_at(fields, idx, "bonus_xpm"),
        "manaReductionPct": _sum_at(fields, idx, "mana_reduction_pct"),
        "projSpeed": _sum_at(fields, idx, "projectile_speed"),
    }


def _item_bonus(fields: dict, *, consumable: bool = False) -> dict[str, float]:
    # "+N All Attributes" is a single line in the in-game tooltip — don't split
    # it into Strength/Agility/Intellect rows. Per-attribute fields stay
    # separate so items can mix (e.g. +6 All + extra Strength).
    all_stats = _first(fields, "bonus_all_stats", "bonus_stats", "all_stats")
    str_bonus = _sum(fields, "bonus_strength", "bonus_str", "strength")
    agi_bonus = _sum(fields, "bonus_agility", "bonus_agi", "agility")
    int_bonus = _sum(fields, "bonus_intellect", "bonus_int", "bonus_intelligence")
    # Bare `health_regen` / `mana_regen` keys are overloaded in Valve KV: on
    # equipment they are passive stats, while on Tango/Salve/Clarity they are
    # the temporary effect of using the consumable.  Never turn a consumable's
    # active restoration into an always-on inventory bonus.
    health_regen_keys = (
        "bonus_health_regen", "bonus_hp_regen", "hp_regen", "bonus_regen",
    ) + (() if consumable else ("health_regen",))
    mana_regen_keys = (
        "bonus_mana_regen", "bonus_mp_regen", "mp_regen", "aura_mana_regen", "mana_regen_aura",
    ) + (() if consumable else ("mana_regen",))
    return {
        "all": all_stats,
        "str": str_bonus,
        "agi": agi_bonus,
        "int": int_bonus,
        "hp": _sum(fields, "bonus_health", "bonus_hp", "bonus_max_health", "health_bonus"),
        "mp": _sum(fields, "bonus_mana", "max_mana", "bonus_max_mana"),
        "hpr": _sum(fields, *health_regen_keys, "aura_health_regen"),
        "mpr": _sum(fields, *mana_regen_keys),
        "armor": _sum(fields, "bonus_armor", "aura_bonus_armor", "armor", "armor_aura", "bonus_aoe_armor"),
        "mr": _sum(fields, "bonus_magic_resistance", "bonus_magical_armor", "bonus_spell_resist", "magic_resistance", "magic_resistance_aura", "magic_res", "magic_resist"),
        "evasion": _sum(fields, "bonus_evasion", "evasion"),
        "damage": _sum(fields, "bonus_damage", "base_attack_damage", "damage"),
        "damagePct": _sum(fields, "damage_aura"),
        "damageMelee": _sum(fields, "bonus_damage_melee"),
        "damageRanged": _sum(fields, "bonus_damage_range", "bonus_damage_ranged"),
        "aspd": _sum(fields, "bonus_attack_speed", "attack_speed", "bonus_as"),
        "ms": _sum(fields, "bonus_movement_speed", "bonus_move_speed", "movement_speed", "aura_movement_speed", "bonus_movement", "movespeed"),
        "msMelee": _sum(fields, "bonus_movement_speed_melee", "bonus_move_speed_melee"),
        "msRanged": _sum(fields, "bonus_movement_speed_ranged", "bonus_move_speed_ranged"),
        "range": _sum(fields, "bonus_attack_range", "attack_range_bonus", "attack_range"),
        "rangeUniqueAll": _sum(fields, "melee_attack_range"),
        "rangeUniqueRanged": _sum(fields, "base_attack_range"),
        "dvision": _sum(fields, "bonus_day_vision", "bonus_vision", "bonus_daytime_vision"),
        "nvision": _sum(fields, "bonus_night_vision", "night_vision_bonus", "bonus_nighttime_vision"),
        "spellAmp": _sum(fields, "spell_amp", "bonus_spell_amp"),
        "statusRes": _sum(fields, "status_resistance", "status_resist"),
        "slowRes": _sum(fields, "slow_resistance", "slow_resist", "bonus_slow_resist"),
        "hprAmp": 0,
        "mprAmp": _sum(fields, "mana_regen_multiplier"),
        "hprPct": _sum(fields, "hp_regen_pct"),
        "missingHprPct": _sum(fields, "missing_health_regen"),
        "mpPct": _sum(fields, "bonus_max_mana_percentage", "max_mana_pct"),
        "lifesteal": _sum(fields, "attack_lifesteal", "lifesteal", "lifesteal_percent", "lifesteal_aura"),
        "spellLifesteal": _sum(fields, "spell_lifesteal", "bonus_spell_lifesteal"),
        "castRange": _sum(fields, "bonus_cast_range", "cast_range_bonus", "cast_range"),
        "primaryStat": _sum(fields, "primary_stat"),
        "primaryStatUni": _sum(fields, "primary_stat_universal"),
        "batReduce": _sum(fields, "bat_reduce"),
        "healthRestoration": _sum(fields, "health_restoration", "hp_regen_amp", "heal_amp"),
        "cooldownReduction": _sum(fields, "cooldown_reduction", "bonus_cooldown"),
        "incomingDamage": _sum(fields, "incoming_damage"),
        "magicDamage": _sum(fields, "magic_damage"),
        "castSpeed": _sum(fields, "cast_speed"),
        "visionReduce": _sum(fields, "vision_reduce"),
        "manacostIncrease": _sum(fields, "cost_increase"),
        "intelligencePct": _sum(fields, "intelligence_pct"),
        "hpPct": _sum(fields, "max_health"),
        "maxHpRegen": _sum(fields, "max_health_regen"),
        "hpRegenReduce": _sum(fields, "hp_regen_reduce"),
        "knockbackResist": _sum(fields, "knockback_resist"),
        "msPct": _sum(fields, "movespeed_pct", "movement_speed_percent_bonus"),
        "manacostReduction": _sum(fields, "manacost_reduction"),
        "debuffAmp": _sum(fields, "debuff_amp"),
        "gpm": _sum(fields, "bonus_gpm"),
        "xpm": _sum(fields, "bonus_xpm"),
        "manaReductionPct": _sum(fields, "mana_reduction_pct"),
        "projSpeed": _sum(fields, "projectile_speed"),
    }



_ENCHANT_TIER_LABELS = {
    "item_enhancement_vital":       ("", 0, [1]),
    "item_enhancement_alert":       ("", 1, [1, 2, 3, 4]),
    "item_enhancement_brawny":      ("", 2, [1, 2, 3, 4]),
    "item_enhancement_mystical":    ("", 3, [1, 2, 3, 4]),
    "item_enhancement_quickened":   ("", 4, [1, 2, 3, 4]),
    "item_enhancement_tough":       ("", 5, [1, 2, 3, 4]),
    "item_enhancement_greedy":      ("", 6, [2, 3]),
    "item_enhancement_crude":       ("", 7, [2, 3, 4]),
    "item_enhancement_keen_eyed":   ("", 8, [2, 3, 4]),
    "item_enhancement_nimble":      ("", 9, [2, 3, 4]),
    "item_enhancement_titanic":     ("", 10, [2, 3, 4]),
    "item_enhancement_vast":        ("", 11, [2, 3, 4]),
    "item_enhancement_timeless":    ("", 12, [4, 5]),
    "item_enhancement_feverish":    ("", 13, [5]),
    "item_enhancement_audacious":   ("", 14, [5]),
    "item_enhancement_evolved":     ("", 15, [5]),
    "item_enhancement_fleetfooted": ("", 16, [5]),
    "item_enhancement_hulking":     ("", 17, [5]),
    "item_enhancement_manic":       ("", 18, [5]),
    "item_enhancement_vampiric":    ("", 19, [5]),
    "item_enhancement_boundless":   ("", 20, [5]),
    "item_enhancement_wise":        ("", 21, [5]),
}

# Which primary attributes can pick each enchantment.
# "all" = available to every hero regardless of attribute.
_ENCHANT_ATTRS: dict[str, set[str]] = {
    "item_enhancement_vital":       {"all"},
    "item_enhancement_quickened":   {"all"},
    "item_enhancement_greedy":      {"all"},
    "item_enhancement_timeless":    {"all"},
    "item_enhancement_evolved":     {"all"},
    "item_enhancement_fleetfooted": {"all"},
    "item_enhancement_vampiric":    {"all"},
    "item_enhancement_vast":        {"all"},
    "item_enhancement_boundless":   {"all"},
    "item_enhancement_wise":        {"all"},
    "item_enhancement_brawny":      {"str", "agi"},
    "item_enhancement_tough":       {"str", "int"},
    "item_enhancement_alert":       {"agi", "uni"},
    "item_enhancement_mystical":    {"int", "uni"},
    "item_enhancement_crude":       {"str"},
    "item_enhancement_hulking":     {"str"},
    "item_enhancement_nimble":      {"agi"},
    "item_enhancement_audacious":   {"agi"},
    "item_enhancement_keen_eyed":   {"int"},
    "item_enhancement_feverish":    {"int"},
    "item_enhancement_titanic":     {"uni"},
    "item_enhancement_manic":       {"uni"},
}


_ITEM_VALUE_ALIASES = {
    "agi": ("bonus_agility", "bonus_agi", "agility"),
    "all": ("bonus_all_stats", "bonus_attributes", "bonus_stats"),
    "aoe_bonus": ("bonus_aoe", "aoe_bonus"),
    "abilitycastrange": ("AbilityCastRange",),
    "attack": ("bonus_attack_speed", "attack_speed"),
    "attack_pct": ("bonus_attack_speed_pct",),
    "attack_range": ("bonus_attack_range", "attack_range_bonus", "base_attack_range"),
    "attack_range_all": ("bonus_attack_range", "attack_range", "base_attack_range"),
    "attack_range_melee": ("melee_attack_range", "bonus_attack_range_melee"),
    "armor": ("bonus_armor", "armor"),
    "cast_range": ("cast_range_bonus", "bonus_cast_range", "AbilityCastRange"),
    "cooldown_reduction": ("cooldown_reduction", "bonus_cooldown"),
    "damage": ("bonus_damage", "damage"),
    "debuff_amp": ("debuff_amp",),
    "evasion": ("bonus_evasion", "evasion"),
    "health": ("bonus_health", "bonus_max_health", "max_health", "health", "health_bonus", "bonus_hp"),
    "hp_regen": ("bonus_health_regen", "bonus_hp_regen", "bonus_regen", "hp_regen", "health_regen", "health_regen_bonus"),
    "int": ("bonus_intellect", "bonus_intelligence", "bonus_int"),
    "lifesteal": ("attack_lifesteal", "lifesteal", "lifesteal_percent"),
    "mana": ("bonus_mana", "max_mana", "mana"),
    "mana_regen": ("bonus_mana_regen", "bonus_mp_regen", "mp_regen", "mana_regen"),
    "max_mana_percentage": ("bonus_max_mana_percentage",),
    "move_speed": ("bonus_movement_speed", "bonus_movement", "bonus_move_speed", "movement_speed", "move_speed", "movement_speed_percent_bonus"),
    "restoration_amp": ("hp_regen_amp", "restoration_amp"),
    "selected_attrib": ("bonus_stat", "selected_attrib"),
    "str": ("bonus_strength", "bonus_str", "strength"),
    "primary_attribute": ("primary_stat",),
    "slow_resistance": ("slow_resistance", "slow_resist", "bonus_slow_resist"),
    "spell_amp": ("spell_amp", "bonus_spell_amp"),
    "projectile_speed": ("projectile_speed",),
    "spell_lifesteal": ("spell_lifesteal", "bonus_spell_lifesteal"),
    "spell_resist": ("bonus_magic_resistance", "bonus_magical_armor", "bonus_spell_resist", "magic_resistance", "magic_resist"),
    "status_resist": ("status_resistance", "status_resist"),
}

_ITEM_ATTR_LABELS = {
    "agi": "Agility",
    "all": "All Attributes",
    "aoe_bonus": "Area of Effect",
    "armor": "Armor",
    "attack": "Attack Speed",
    "attack_pct": "Attack Speed",
    "attack_range": "Attack Range",
    "attack_range_melee": "Attack Range",
    "attack_range_all": "Attack Range",
    "cast_range": "Cast Range",
    "cooldown_reduction": "Cooldown Reduction",
    "damage": "Damage",
    "debuff_amp": "Debuff Duration",
    "evasion": "Evasion",
    "health": "Health",
    "hp_regen": "Health Regeneration",
    "int": "Intelligence",
    "lifesteal": "Lifesteal",
    "mana": "Mana",
    "mana_regen": "Mana Regeneration",
    "max_mana_percentage": "Max Mana",
    "move_speed": "Movement Speed",
    "primary_attribute": "Primary Attribute",
    "restoration_amp": "Health Restoration",
    "selected_attrib": "Selected Attribute",
    "slow_resistance": "Slow Resistance",
    "spell_amp": "Spell Amplification",
    "spell_lifesteal": "Spell Lifesteal",
    "projectile_speed": "Projectile Speed",
    "spell_resist": "Magic Resistance",
    "status_resist": "Status Resistance",
    "str": "Strength",
}


def _field_value(fields: dict, key: str):
    """Resolve localization variables against KV fields case-insensitively."""
    if key in fields:
        return fields[key]
    lower = {str(k).lower(): v for k, v in fields.items()}
    if key.lower() in lower:
        return lower[key.lower()]
    for alias in _ITEM_VALUE_ALIASES.get(key.lower(), ()):
        if alias in fields:
            return fields[alias]
        if alias.lower() in lower:
            return lower[alias.lower()]
    return None


def _display_value(value) -> str:
    s = str(value).split(" ")[0]
    try:
        n = float(s)
        return str(int(n)) if n == int(n) else s
    except (ValueError, TypeError):
        return s


def _series_numbers(value) -> list[float]:
    if value is None:
        return []
    out: list[float] = []
    for part in str(value).split():
        try:
            out.append(float(part))
        except (TypeError, ValueError):
            continue
    return out
    return out


def _resolve_pct(desc: str, fields: dict) -> str:
    """Replace %var% placeholders in tooltip descriptions with actual values.

    Substituted values are wrapped in <span class="GameplayVariable"> so the
    tooltip CSS can highlight them brighter than the body text — matching the
    in-game Dota tooltip, where resolved numbers stand out from the prose."""
    def _repl(m):
        key = m.group(1)
        if key.startswith("d") and key[1:] in fields:
            key = key[1:]
        val = _field_value(fields, key)
        if val is None:
            return m.group(0)
        s = _display_value(val)
        return f'<span class="GameplayVariable">{s}</span>'
    return _re.sub(r"%([a-zA-Z_][a-zA-Z0-9_]*)%", _repl, desc)


def _resolve_attr_label(label: str, fields: dict) -> str:
    """Resolve Valve's `$field` placeholders used by item stat rows."""
    def repl(match):
        val = _field_value(fields, match.group(1))
        return _display_value(val) if val is not None else match.group(0)
    return _re.sub(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", repl, label)


def _resolve_attribute_entry(entry, fields: dict) -> str:
    """Resolve a localized item attribute row, including rows whose text has
    only a label (for example `%+Health Restoration`) and relies on the
    localization-key suffix to identify its numeric KV field.
    """
    if isinstance(entry, dict):
        raw = str(entry.get("text", ""))
        field = str(entry.get("field", ""))
    else:
        raw, field = str(entry), ""
    placeholders = _re.findall(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", raw)
    text = _resolve_attr_label(raw, fields)
    text_plain = _re.sub(r"<[^>]+>", "", text)
    if "$" not in raw and field and not _re.search(r"\d", text_plain):
        val = _field_value(fields, field)
        if val is not None:
            number = _display_value(val)
            is_pct = "%" in text
            # The KV sign is authoritative when present; otherwise retain the
            # leading sign encoded by the localization row.
            try:
                numeric = float(str(val).split(" ")[0])
                sign = "-" if numeric < 0 else "+" if "+" in text else "-" if "-" in text else ""
                number = _display_value(abs(numeric))
            except (TypeError, ValueError):
                sign = "+" if "+" in text else "-" if "-" in text else ""
            label = _re.sub(r"^[%+\-\s]+", "", text).strip()
            text = f"{sign}{number}{'%' if is_pct else ''} {label}".strip()
    # Valve writes percentage placement as `%+$value` / `%-$value`.
    text = _re.sub(r"^%\+([\d.]+)", r"+\1%", text)
    text = _re.sub(r"^%-([\d.]+)", r"-\1%", text)
    if placeholders and not _re.search(r"[A-Za-z]", _re.sub(r"<[^>]+>", "", text)):
        label = _ITEM_ATTR_LABELS.get(placeholders[0].lower())
        if label:
            text = f"{text} {label}"
    text = _re.sub(r"</?font[^>]*>", "", text)
    return text


def _is_zero_attribute(text: str) -> bool:
    """Return true for localized stat rows such as `+0 Health Regeneration`."""
    plain = _re.sub(r"<[^>]+>", "", text).strip()
    match = _re.match(r"^[+\-]?\s*([\d.]+)%?(?:\s|$)", plain)
    if not match:
        return False
    try:
        return abs(float(match.group(1))) < 1e-9
    except ValueError:
        return False


def _is_noise_attribute(text: str) -> bool:
    plain = _re.sub(r"<[^>]+>", "", text).strip()
    if not plain:
        return True
    if plain.startswith("Rune:"):
        return True
    if plain == "Tango (Shared)":
        return True
    if _re.match(r"^%[+\-]", plain):
        return True
    return False


def _active_history_entry(effect: dict, version: str) -> dict:
    history = effect.get("history")
    if not history:
        return effect
    active = {}
    matched = False
    for entry in history:
        since = entry.get("since")
        until = entry.get("until")
        if since and not _ge(version, since):
            continue
        if until and not _ge(until, version):
            continue
        matched = True
        active.update(entry)
    if not matched:
        return {}
    merged = dict(effect)
    merged.update(active)
    return merged


def _fmt_pct_value(value: float) -> str:
    n = value * 100
    return f"{int(n)}%" if abs(n - round(n)) < 1e-9 else f"{n:.2f}".rstrip("0").rstrip(".") + "%"


def _innate_summary(rule: dict, version: str) -> str:
    target_label = {
        "str": "Strength",
        "agi": "Agility",
        "int": "Intelligence",
        "hp": "Health",
        "mp": "Mana",
        "hpr": "HP Regen",
        "mpr": "Mana Regen",
        "armor": "Armor",
        "mr": "Magic Resistance",
        "dmg": "Damage",
        "aspd": "Attack Speed",
        "ms": "Move Speed",
        "range": "Attack Range",
        "nvision": "Night Vision",
        "slowRes": "Slow Resistance",
        "statusRes": "Status Resistance",
    }
    source_label = {
        "str": "Strength",
        "agi": "Agility",
        "int": "Intelligence",
        "armor": "Armor",
        "hp": "current HP",
        "mp": "mana pool",
    }
    parts: list[str] = []
    for effect in rule.get("effects", []):
        active = _active_history_entry(effect, version)
        if not active:
            continue
        formula = active.get("formula")
        target = target_label.get(active.get("target"), active.get("target", "Stat"))
        source = source_label.get(active.get("source"), active.get("source", ""))
        if formula == "armor_factor":
            parts.append(f"{_fmt_pct_value(float(active.get('factor', 0)))} of Armor as Strength")
        elif formula == "attr_factor":
            parts.append(f"+{_display_value(active.get('factor', 0))} {target.lower()} per {source}")
        elif formula == "base_plus_level":
            base = _display_value(active.get("base", 0))
            per = _display_value(active.get("per_level", 0))
            parts.append(f"+{base} {target.lower()} and +{per} per level")
        elif formula == "flat_per_level":
            per = _display_value(active.get("per_level", 0))
            parts.append(f"+{per} {target.lower()} per level")
        elif formula == "self_attr_pct_per_level":
            base = _fmt_pct_value(float(active.get("base_pct", 0)))
            per = _fmt_pct_value(float(active.get("per_level_pct", 0)))
            parts.append(f"+{base} + {per} per level of current {target} as bonus {target}")
        elif formula == "attr_pct_per_level":
            base = _fmt_pct_value(float(active.get("base_pct", 0)))
            per = _fmt_pct_value(float(active.get("per_level_pct", 0)))
            parts.append(f"+{base} + {per} per level of {source} as {target.lower()}")
        elif formula == "hp_pct":
            parts.append(f"{_display_value(active.get('factor', 0))}% of current HP as damage")
        elif formula == "mana_pool_pct_per_level":
            base = _fmt_pct_value(float(active.get("base_pct", 0)))
            per = _fmt_pct_value(float(active.get("per_level_pct", 0)))
            parts.append(f"{base} + {per} per level of mana pool as mana regen")
        elif formula == "ms_multiplier":
            base = _display_value(active.get("base_pct", 0))
            per = _display_value(active.get("per_level_pct", 0))
            parts.append(f"+{base}% move speed and +{per}% per level")
        elif formula == "secondary_attr_factor":
            parts.append(f"{_fmt_pct_value(float(active.get('factor', 0)))} more {target.lower()} from {source}")
        elif formula == "dmg_universal_bonus_pct":
            parts.append(f"{_fmt_pct_value(float(active.get('factor', 0)))} more attack damage per attribute")
        elif formula == "attr_substitution":
            sub = source_label.get(active.get("sub_attr"), active.get("sub_attr", ""))
            parts.append(f"{target} scales from {sub} instead of Intelligence")
    return "; ".join(parts)


def _load_items(version: str) -> list[dict]:
    names = _load_item_names()
    meta_by_id = _load_item_meta()
    tooltips = _load_item_tooltips()
    npedesc = _load_item_npedesc()
    items_json_path = STATS_DIR / version / "items.json"
    costs = _json.loads(items_json_path.read_text(encoding="utf-8")) if items_json_path.exists() else {}
    root = parse_kv((STATS_DIR / version / "items.txt").read_text(encoding="utf-8"))
    kv_items = root.get("DOTAAbilities", {})
    out: list[dict] = []
    for item, data in kv_items.items():
        if not item.startswith("item_") or item.startswith("item_recipe_"):
            continue
        if item in {"item_dagon_2", "item_dagon_3", "item_dagon_4", "item_dagon_5"}:
            continue
        if not isinstance(data, dict):
            continue
        label = names.get(item)
        if not label:
            continue
        meta = meta_by_id.get(item)
        if not meta:
            continue
        if data.get("ItemRecipe") == "1":
            continue
        fields = dict(data)
        fields.update(_flatten_special(data))
        cost = _num(fields.get("ItemCost", (costs.get(item) or {}).get("ItemCost", 0)))
        consumable = str(fields.get("ItemQuality", "")).lower() == "consumable"
        cls = meta.get("class", "regular")
        # Neutral artifacts provide an active/passive mechanic whose values are
        # affected by their enchantment.  Their AbilityValues are not direct
        # hero stats: e.g. Gunpowder Gauntlets' `bonus_damage = 120` is proc
        # damage, not +120 attack damage.  Only the enchantment contributes
        # direct stats to Hero Lab.
        bonus = {} if cls == "neutral" else _item_bonus(fields, consumable=consumable)
        if item == "item_heart" and bonus:
            bonus["hprPct"] = bonus.get("hpr", 0)
            bonus["hpr"] = 0
        if item == "item_veil_of_discord" and bonus:
            bonus["spellAmp"] = 0
        if item == "item_swift_blink" and bonus:
            bonus["ms"] = 0
        if item == "item_manta" and bonus:
            bonus["msPct"] = bonus.get("msPct", 0) + bonus.get("ms", 0)
            bonus["ms"] = 0
        if item == "item_enhancement_hulking" and bonus:
            bonus["aspdPct"] = bonus.get("aspd", 0)
            bonus["aspd"] = 0
        if item == "item_enhancement_titanic":
            if bonus:
                bonus["aspdPct"] = bonus.get("aspd", 0)
                bonus["aspd"] = 0
        if cls == "neutral":
            bonus = {key: 0 for key in _item_bonus({}, consumable=False)}
        if cls == "regular" and not any(abs(v) > 1e-9 for v in bonus.values()) and cost <= 0:
            continue
        slug = meta.get("icon") or _slug_from_item(item)
        icon = f"icons/items/{slug}.png"
        if not (_HERE / icon).exists():
            icon = f"icons/items/{item}.png"
        rec: dict = {
            "id": item,
            "slug": slug,
            "name": label,
            "icon": icon,
            "cost": int(cost),
            "class": cls,
            "category": meta.get("category"),
            "tier": meta.get("tier"),
            # Consumables (Tango, Salve, …) get the green "Use" ability header
            # in-game; ItemQuality flags them. Drives the green bar in the tooltip.
            "consumable": consumable,
            "bonus": bonus,
        }
        _BOOT_ITEMS = {
            "item_boots", "item_tranquil_boots", "item_arcane_boots",
            "item_guardian_greaves", "item_travel_boots", "item_travel_boots_2",
            "item_phase_boots", "item_power_treads",
        }
        if item in _BOOT_ITEMS:
            rec["isBoot"] = True
        if cls == "enchant":
            tier_label, tier_sort, tier_list = _ENCHANT_TIER_LABELS.get(item, ("", 99, []))
            rec["tierSort"] = tier_sort
            rec["enchantAttr"] = sorted(_ENCHANT_ATTRS.get(item, {"all"}))
            rec["tiersAvailable"] = tier_list
            if len(tier_list) > 1:
                modes: dict = {"default": f"t{tier_list[0]}"}
                for level_idx, tier_num in enumerate(tier_list):
                    modes[f"t{tier_num}"] = _item_bonus_at(fields, level_idx)
                if item in ("item_enhancement_titanic", "item_enhancement_hulking"):
                    for mk, mv in modes.items():
                        if isinstance(mv, dict) and mv.get("aspd"):
                            mv["aspdPct"] = mv.pop("aspd")
                rec["modes"] = modes
                rec["bonus"] = {k: 0 for k in rec["bonus"]}
        if item == "item_desolator":
            step = int(_sum(fields, "bonus_damage_per_kill") or 2)
            max_stacks = int(_sum(fields, "max_damage") or 30)
            deso_modes: dict = {"default": "none", "none": {"damage": 0}}
            for n in range(step, max_stacks + 1, step):
                deso_modes[str(n)] = {"damage": n}
            rec["modes"] = deso_modes
        if item == "item_rapier":
            rec["bonus"]["damage"] = _sum(fields, "bonus_damage_base")
            rec["bonus"]["spellAmp"] = 0
            rec["modes"] = {
                "default": "damage",
                "base": {"damage": _sum(fields, "bonus_damage_base")},
                "damage": {"damage": _sum(fields, "bonus_damage")},
                "spell": {"spellAmp": _sum(fields, "bonus_spell_amp"), "icon": "icons/items/rapier_alt.png"},
            }
        if item == "item_tranquil_boots":
            broken_ms = _sum(fields, "broken_movement_speed") or 40
            active_ms = _sum(fields, "bonus_movement_speed") or 65
            active_hpr = _sum(fields, "bonus_health_regen") or 14
            if rec.get("bonus"):
                rec["bonus"]["ms"] = 0
                rec["bonus"]["hpr"] = 0
            rec["modes"] = {
                "default": "active",
                "active": {"ms": active_ms, "hpr": active_hpr},
                "broken": {"ms": broken_ms, "hpr": 0, "icon": "icons/items/tranquil_boots_active.png"},
            }
        if item == "item_octarine_core" and bonus:
            bonus["cdrUnique"] = bonus.get("cooldownReduction", 0)
            bonus["cooldownReduction"] = 0
        if item == "item_power_treads":
            stat_val = _sum(fields, "bonus_stat", "selected_attrib")
            rec["modes"] = {
                "default": "str",
                "str": {"str": stat_val, "icon": "icons/items/power_treads_str.png"},
                "agi": {"agi": stat_val, "icon": "icons/items/power_treads_agi.png"},
                "int": {"int": stat_val, "icon": "icons/items/power_treads_int.png"},
            }
        if item == "item_dagon":
            level_items = ["item_dagon", "item_dagon_2", "item_dagon_3", "item_dagon_4", "item_dagon_5"]
            all_stats = _series_numbers(fields.get("bonus_all_stats"))
            health = _series_numbers(fields.get("bonus_health"))
            mana = _series_numbers(fields.get("bonus_mana"))
            burst = _series_numbers(fields.get("damage"))
            mana_costs = _series_numbers(fields.get("mana_cost_tooltip") or fields.get("AbilityManaCost"))
            cast_range = _series_numbers(fields.get("cast_range_bonus"))
            cooldowns = _series_numbers(fields.get("AbilityCooldown"))
            levels = []
            mode_map = {"default": "lvl1"}
            rec["bonus"] = {key: 0 for key in rec["bonus"].keys()}
            rec["cost"] = 3000
            for idx, level_item in enumerate(level_items, start=1):
                level_data = kv_items.get(level_item, {}) if idx > 1 else data
                level_fields = dict(level_data) if isinstance(level_data, dict) else {}
                if isinstance(level_data, dict):
                    level_fields.update(_flatten_special(level_data))
                level_cost = int(_num(level_fields.get("ItemCost", rec["cost"])))
                icon_path = f"icons/items/dagon{'_' + str(idx) if idx > 1 else ''}.png"
                icon = icon_path if (_HERE / icon_path).exists() else rec["icon"]
                level_row = {
                    "level": idx,
                    "cost": level_cost,
                    "icon": icon,
                    "all": all_stats[idx - 1] if len(all_stats) >= idx else 0,
                    "hp": health[idx - 1] if len(health) >= idx else 0,
                    "mp": mana[idx - 1] if len(mana) >= idx else 0,
                    "dagonDamage": burst[idx - 1] if len(burst) >= idx else 0,
                    "mc": mana_costs[idx - 1] if len(mana_costs) >= idx else 0,
                    "cr": cast_range[idx - 1] if len(cast_range) >= idx else 0,
                    "cd": cooldowns[idx - 1] if len(cooldowns) >= idx else 0,
                }
                level_row["attribs"] = [
                    f"+{int(level_row['all'])} All Attributes",
                    f"+{int(level_row['hp'])} Health",
                    f"+{int(level_row['mp'])} Mana",
                    f"+{int(level_row['cr'])} Cast Range",
                ]
                levels.append(level_row)
                mode_map[f"lvl{idx}"] = {
                    "level": idx,
                    "icon": icon,
                    "costOverride": level_cost,
                    "all": level_row["all"],
                    "hp": level_row["hp"],
                    "mp": level_row["mp"],
                    "mc": level_row["mc"],
                    "cr": level_row["cr"],
                    "cd": level_row["cd"],
                    "dagonDamage": level_row["dagonDamage"],
                    "attribs": level_row["attribs"],
                }
            rec["modes"] = mode_map
            rec.setdefault("tip", {})
            rec["tip"]["levels"] = levels
        tt = tooltips.get(item, {})
        cd = _num(fields.get("AbilityCooldown", 0))
        mc = _num(fields.get("AbilityManaCost", 0))
        cr = _num(fields.get("AbilityCastRange", 0))
        disp = fields.get("SpellDispellableType", "")
        disp_map = {
            "SPELL_DISPELLABLE_YES": "Yes",
            "SPELL_DISPELLABLE_YES_STRONG": "Strong Dispels Only",
            "SPELL_DISPELLABLE_NO": "No",
        }
        tip: dict = {}
        raw_desc = tt.get("desc", "")
        if raw_desc:
            resolved = _resolve_pct(raw_desc, fields)
            resolved = resolved.replace("%%", "%")
            # Localization can be newer than the checked-in KV snapshot.  Do
            # not expose raw `%variable%` tokens when the corresponding values
            # are unavailable; the short description/stat rows are a cleaner
            # and more truthful fallback.
            if not _re.search(r"%[a-zA-Z_][a-zA-Z0-9_]*%", resolved):
                tip["desc"] = resolved
        notes = tt.get("notes", [])
        if notes:
            resolved_notes = [
                _resolve_pct(_resolve_attr_label(note, fields), fields).replace("%%", "%")
                for note in notes
            ]
            resolved_notes = [
                note for note in resolved_notes
                if not _re.search(r"%[a-zA-Z_][a-zA-Z0-9_]*%", note)
            ]
            if resolved_notes:
                tip["notes"] = resolved_notes
        if cd > 0:
            tip["cd"] = cd if cd != int(cd) else int(cd)
        if mc > 0:
            tip["mc"] = mc if mc != int(mc) else int(mc)
        if cr > 0:
            tip["cr"] = cr if cr != int(cr) else int(cr)
        d = disp_map.get(disp, "")
        if d:
            tip["disp"] = d
        beh = str(fields.get("AbilityBehavior", ""))
        if "UNIT_TARGET" in beh:
            tip["target"] = "Unit Target"
        elif "POINT" in beh:
            tip["target"] = "Point Target"
        elif "NO_TARGET" in beh:
            tip["target"] = "No Target"
        elif "TOGGLE" in beh:
            tip["target"] = "Toggle"
        elif "PASSIVE" in beh:
            # Every item flagged DOTA_ABILITY_BEHAVIOR_PASSIVE shows
            # "ABILITY: Passive" in-game — that's true even for pure-stat items
            # like Blades of Attack and Bracer, which still carry the row.
            tip["target"] = "Passive"
        # AFFECTS: team + unit type (e.g. "Allied Heroes", "Enemy Units"),
        # mirroring the in-game tooltip. From AbilityUnitTargetTeam/Type.
        team = str(fields.get("AbilityUnitTargetTeam", ""))
        typ = str(fields.get("AbilityUnitTargetType", ""))
        if "FRIENDLY" in team:
            team_word = "Allied"
        elif "ENEMY" in team:
            team_word = "Enemy"
        elif "BOTH" in team or "CUSTOM" in team:
            team_word = ""
        else:
            team_word = ""
        type_words = []
        if "HERO" in typ:
            type_words.append("Heroes")
        if "BASIC" in typ:
            type_words.append("Units")
        if "BUILDING" in typ:
            type_words.append("Buildings")
        if "CREEP" in typ and "Units" not in type_words:
            type_words.append("Creeps")
        type_word = " / ".join(type_words) if type_words else ("Units" if typ else "")
        affects = " ".join(w for w in (team_word, type_word) if w).strip()
        if affects:
            tip["affects"] = affects
        # Neutral items: headline "+N <Stat>" rows from AbilityValues with
        # apply_curio_bonus=1 (e.g. Harmonizer's "+6% Spell Amplification").
        # Regular items don't use this convention — bonus_* fields cover them.
        if cls == "neutral":
            neutrals = _neutral_curio_bonuses(data)
            if neutrals:
                tip["neutralBonuses"] = neutrals
        short = npedesc.get(item, "")
        if short:
            tip["short"] = short
        raw_attribs = [
            _resolve_attribute_entry(a, fields) for a in tt.get("attribs", [])
        ]
        has_cast_range_bonus = any(
            fields.get(k) for k in ("bonus_cast_range", "cast_range_bonus", "cast_range")
        )
        if raw_attribs:
            resolved = [
                a.strip() for a in raw_attribs
                if a.strip()
                and not a.strip().endswith(":")
                and "DURATION" not in a.upper()
                and not _is_zero_attribute(a)
                and not _is_noise_attribute(a)
                and "$" not in a
                and not (not has_cast_range_bonus and "Cast Range" in a)
            ]
            if resolved:
                tip["attribs"] = resolved
        if item == "item_power_treads" and "attribs" in tip:
            _PT_NOISE = {"strength", "agility", "intelligence"}
            tip["attribs"] = [a for a in tip["attribs"]
                              if a.strip().lower() not in _PT_NOISE
                              and "selected attribute" not in a.lower()]
        if item == "item_desolator" and "attribs" in tip:
            item_name = (names.get(item) or "").lower()
            tip["attribs"] = [a for a in tip["attribs"] if a.strip().lower() != item_name]
        if item == "item_rapier":
            tip["attribs"] = [f"+{int(_sum(fields, 'bonus_damage_base'))} Damage"]
        # Fallback: generate attribs from known fields if loc had nothing
        if "attribs" not in tip:
            _FIELD_ATTRIBS = {
                "aoe_bonus": ("Area of Effect", ""),
                "spell_lifesteal": ("Spell Lifesteal", "%"),
                "slow_resist": ("Slow Resistance", "%"),
                "status_resist": ("Status Resistance", "%"),
                "magic_resist": ("Magic Resistance", "%"),
                "spell_amp": ("Spell Amplification", "%"),
                "mana_regen_multiplier": ("Mana Regeneration", "%"),
                "hp_regen_amplify_percentage": ("HP Regeneration", "%"),
                "heal_amplify_percentage": ("Heal Amplification", "%"),
                "attack_lifesteal": ("Lifesteal", "%"),
            }
            fallback = []
            for fk, (flabel, fpct) in _FIELD_ATTRIBS.items():
                fv = fields.get(fk)
                if fv is not None:
                    try:
                        n = float(str(fv).split(" ")[0])
                        if abs(n) > 0.001:
                            ns = str(int(n)) if n == int(n) else str(n)
                            fallback.append(f"+{ns}{fpct} {flabel}")
                    except (ValueError, TypeError):
                        pass
            if fallback:
                tip["attribs"] = fallback
        if tip:
            merged_tip = dict(rec.get("tip", {}))
            merged_tip.update(tip)
            rec["tip"] = merged_tip
        out.append(rec)
    cls_rank = {"regular": 0, "neutral": 1, "enchant": 2}
    cat_rank = {
        "Consumables": 0, "Attributes": 1, "Equipment": 2, "Miscellaneous": 3, "Secret Shop": 4,
        "Accessories": 5, "Support": 6, "Magical": 7, "Armor": 8, "Weapons": 9, "Armaments": 10,
    }
    return sorted(
        out,
        key=lambda x: (
            cls_rank.get(x.get("class"), 99),
            cat_rank.get(x.get("category"), 99),
            x.get("tier") if x.get("tier") is not None else 99,
            x["name"].lower(),
        ),
    )


def _hero_innate_slug(version: str, hero_slug: str) -> str:
    path = STATS_DIR / version / "heroes" / f"npc_dota_hero_{hero_slug}.txt"
    if not path.exists():
        return ""
    try:
        root = parse_kv(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    abilities = root.get("DOTAAbilities", {})
    for ability_slug, data in abilities.items():
        if isinstance(data, dict) and str(data.get("Innate", "0")) == "1":
            return ability_slug
    return ""


def _load_heroes(version: str) -> list[dict]:
    snap = _json.loads((STATS_DIR / version / "heroes.json").read_text(encoding="utf-8"))
    raw = _load_raw_heroes(version)
    snaps = {version: snap}
    raws = {version: raw}
    _inject_spirit_bear(snaps, raws)
    snap, raw = snaps[version], raws[version]
    names = _load_display_names()
    ability_tooltips = _load_ability_tooltips()
    innate_rules = _json.loads(
        (_HERE / "data" / "rules" / "hero_stat_innates.json").read_text(encoding="utf-8")
    ).get("heroes", {})
    heroes = sorted(
        (h for h in snap if h.startswith("npc_dota_hero_") and h not in _EXCLUDE),
        key=lambda h: _display_name(h, names).lower(),
    )
    out = []
    for hero in heroes:
        slug = hero.replace("npc_dota_hero_", "")
        name = _display_name(hero, names)
        stats = _json.loads(_html.unescape(_row_stats(hero, snap, raw)))
        icon_slug = "spirit_bear" if hero == SPIRIT_BEAR_HERO else slug
        innate_rule = innate_rules.get(slug, {})
        innate_slug = innate_rule.get("innate") if innate_rule else ""
        innate_tip = ability_tooltips.get(innate_slug, {}) if innate_slug else {}
        innate_icon = f"icons/abilities/{innate_slug}.png" if innate_slug else ""
        if innate_icon and not (_HERE / innate_icon).exists():
            innate_icon = "icons/misc/innate_icon.png"
        innate_desc = innate_tip.get("desc", "") if innate_tip else ""
        if innate_rule and "%" in innate_desc:
            innate_desc = _innate_summary(innate_rule, version)
        out.append({
            "id": slug,
            "name": name,
            "icon": f"icons/heroes/{icon_slug}.png",
            "attackType": _attack_type(version, hero, raw),
            "stats": stats,
            "statInnate": {
                "slug": innate_slug,
                "name": innate_tip.get("name", ""),
                "desc": innate_desc,
                "icon": innate_icon,
            } if innate_rule and innate_slug else None,
        })
    return out


def render_html() -> str:
    version = _versions()[-1]
    heroes = _load_heroes(version)
    items = _load_items(version)
    innate_rules = _json.loads(
        (_HERE / "data" / "rules" / "hero_stat_innates.json").read_text(encoding="utf-8")
    ).get("heroes", {})
    data = _json.dumps(
        {"patch": version, "heroes": heroes, "items": items, "innateRules": innate_rules},
        separators=(",", ":"),
    )
    data_script = data.replace("<", "\\u003c")
    nav = _site.render_top_nav("materials", _latest_href(), subtabs_active="hero_lab", subnav_in_header=False)
    subnav = _site.render_materials_subnav("hero_lab")
    av = _site.compute_asset_version()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SIKLE | Hero Lab</title>
{_site.favicon_links()}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">
<link rel="stylesheet" href="styles.css?v={av}">
</head>
<body>
{nav}
<div class="container creeps-page hero-lab-page">
{subnav}
<div class="creeps-scroll">
<p class="mr-blurb inbox-bar">Compare two heroes side by side with level, six inventory slots, neutral item, enchantment and custom stat overrides. The center column shows the live difference between both builds.</p>
<div class="cal-toggle-bar inbox-bar hero-lab-toolbar">
  <div class="toolbar-panel">
    <div class="hd-dd" data-dd="diffstat" id="hl-diff-dd">
      <button type="button" class="hd-dd-btn" aria-expanded="false" aria-haspopup="true"><span class="hd-dd-label">Difference</span><span class="hd-dd-badge" aria-hidden="true"></span><svg class="hd-dd-caret" viewBox="0 0 10 6" width="10" height="6" aria-hidden="true"><path d="M0 0l5 6 5-6z" fill="currentColor"/></svg></button>
      <div class="hd-dd-menu" data-dd="diffstat" role="group" hidden></div>
    </div>
    <label class="ua-upgrades-toggle">
      <span class="ua-upgrades-label">Innates</span>
      <input type="checkbox" class="ua-switch-input" data-innates-toggle checked>
      <span class="ua-switch" aria-hidden="true"></span>
    </label>
    <label class="ua-upgrades-toggle">
      <span class="ua-upgrades-label">Show totals</span>
      <input type="checkbox" class="ua-switch-input" data-hl-merge-positive-toggle>
      <span class="ua-switch" aria-hidden="true"></span>
    </label>
    <label class="ua-upgrades-toggle">
      <span class="ua-upgrades-label">Percent difference</span>
      <input type="checkbox" class="ua-switch-input" data-hl-diff-percent-toggle>
      <span class="ua-switch" aria-hidden="true"></span>
    </label>
  </div>
</div>
<script id="hero-lab-data" type="application/json">{data_script}</script>
<div class="hero-lab" data-patch="{_esc(version)}">
  <div class="hl-panel" data-side="a"></div>
  <div class="hl-diff-panel">
    <div class="hl-diff-head">
      <strong id="hl-diff-title">DIFFERENCE</strong>
    </div>
    <div class="hl-diff-list" id="hl-diff-list"></div>
  </div>
  <div class="hl-panel" data-side="b"></div>
</div>
</div>
</div>
<script defer src="src/scripts.js?v={av}"></script>
</body>
</html>
"""


def main() -> int:
    html = render_html()
    (_HERE / "dist").mkdir(exist_ok=True)
    (_HERE / "dist" / "hero_lab.html").write_text(html, encoding="utf-8")
    print(f"  -> dist/hero_lab.html: {len(html):,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
