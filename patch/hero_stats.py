"""A hero's base attributes and attack damage by level, from the game files of a patch (data/stats/<v>/heroes.json).

Attack damage = base damage + the primary attribute (x1), or for a Universal hero every attribute x the
Universal multiplier (0.6 in 7.33, 0.7 from 7.33c, 0.45 from 7.38 — the history is in
patch/game_constants.UNIVERSAL_DMG_HIST, shared with Hero Stats). An attribute at level L = base + gain x (L - 1).
Valve's own "Damage at level 30" counts the 7 Attribute Bonus levels too (+2 to every attribute each, +14 in
all, read from special_bonus_attributes in the latest npc_abilities.txt): damage_at(..., bonus=True).
Checked against Valve's 7.38 rows for every Universal hero (tests/test_hero_stat_card.py)."""
import os
import re

from . import game_constants
from .meta import latest_stats_version
from .stats import stat_h

ATTRS = (("Strength", "str"), ("Agility", "agi"), ("Intelligence", "int"))
_PRIMARY = {"DOTA_ATTRIBUTE_STRENGTH": "Strength", "DOTA_ATTRIBUTE_AGILITY": "Agility",
            "DOTA_ATTRIBUTE_INTELLECT": "Intelligence", "DOTA_ATTRIBUTE_ALL": "all"}


def _attribute_bonus_max():
    """+2 to every attribute per Attribute Bonus level: the last of special_bonus_attributes' values
    ("2 4 6 8 10 12 14" -> 14). None when the latest npc_abilities.txt lacks it (a test guards that)."""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "stats", latest_stats_version(),
                        "npc_abilities.txt")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    m = re.search(r'"special_bonus_attributes"\s*\{.*?"value"\s*"([\d .]+)"', text, re.S)
    return int(float(m.group(1).split()[-1])) if m else None


ATTRIBUTE_BONUS_MAX = _attribute_bonus_max() or 14     # 14 = 7 levels x +2 (7.33+), if the file lacks it


def universal_multiplier(version):
    return game_constants.at(game_constants.UNIVERSAL_DMG_HIST, version)


def hero_stats(hero, version):
    """{"primary", "dmg_min", "dmg_max", "Strength": (base, gain), ...} or None when the game files lack it."""
    out = {"primary": _PRIMARY.get(stat_h(hero, "AttributePrimary", version) or "", "")}
    for field, key in (("AttackDamageMin", "dmg_min"), ("AttackDamageMax", "dmg_max")):
        out[key] = stat_h(hero, field, version)
    for attr, _ in ATTRS:
        out[attr] = (stat_h(hero, f"AttributeBase{attr}", version), stat_h(hero, f"Attribute{attr}Gain", version))
    if not out["primary"] or out["dmg_min"] is None or any(None in out[a] for a, _ in ATTRS):
        return None
    return out


def attrs_changed(hero, before, after):
    """Did an attribute (base / gain), the main attribute or the Universal multiplier change? Only then the
    attributes card says something (Chaos Knight 7.40: only the damage spread moved -> no card)."""
    o, n = hero_stats(hero, before), hero_stats(hero, after)
    if not (o and n):
        return False
    uni = "all" in (o["primary"], n["primary"])
    return (any(o[a] != n[a] for a, _ in ATTRS) or o["primary"] != n["primary"]
            or (uni and universal_multiplier(before) != universal_multiplier(after)))


def damage_at(stats, version, level, bonus=False):
    """(min, max) attack damage at `level`."""
    extra = ATTRIBUTE_BONUS_MAX if bonus else 0
    value = {a: stats[a][0] + stats[a][1] * (level - 1) + extra for a, _ in ATTRS}
    add = (universal_multiplier(version) * sum(value.values()) if stats["primary"] == "all"
           else value[stats["primary"]])
    return stats["dmg_min"] + add, stats["dmg_max"] + add
