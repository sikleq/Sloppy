"""A hero's base attributes and attack damage by level, from the game files of a patch (data/stats/<v>/heroes.json).

Attack damage = base damage + the primary attribute (x1), or for a Universal hero every attribute x the
Universal multiplier (0.7 until 7.37e, 0.45 from 7.38: "Universal Heroes' damage per attribute decreased from
0.7 to 0.45"). An attribute at level L = base + gain x (L - 1). Valve's own "Damage at level 30" counts the
7 Attribute Bonus levels too (+2 to every attribute each, +14 in all): damage_at(..., bonus=True).
Checked against Valve's 7.38 rows for every Universal hero (tests/test_hero_stat_card.py)."""
from .meta import RELEASE_HISTORY
from .stats import stat_h

ATTRS = (("Strength", "str"), ("Agility", "agi"), ("Intelligence", "int"))
_PRIMARY = {"DOTA_ATTRIBUTE_STRENGTH": "Strength", "DOTA_ATTRIBUTE_AGILITY": "Agility",
            "DOTA_ATTRIBUTE_INTELLECT": "Intelligence", "DOTA_ATTRIBUTE_ALL": "all"}
ATTRIBUTE_BONUS_MAX = 14            # 7 levels x +2 to every attribute (special_bonus_attributes)
_UNIVERSAL_FROM = (("7.38", 0.45),)  # (first version, damage per attribute); before the first: 0.7


def _order():
    return [r["version"] for r in RELEASE_HISTORY][::-1]      # oldest first


def universal_multiplier(version):
    order, mult = _order(), 0.7
    for first, value in _UNIVERSAL_FROM:
        if version in order and first in order and order.index(version) >= order.index(first):
            mult = value
    return mult


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
