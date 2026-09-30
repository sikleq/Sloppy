"""An ability's own properties in one patch, from the game files (owner 2026-09-30: "1200 range — that is a radius,
read the abilities' properties from the files"): whether it is Passive / Active / Toggle, and its cast range, mana
cost, health cost, cooldown and radius, for the header of an ability card or an ability row.

Sources (all in the repo, per version): data/stats/<v>/heroes/*.txt (hero abilities, raw KV),
data/stats/<v>/abilities.json (other abilities: behaviour, cast range, mana, cooldown) and
data/stats/<v>/npc_abilities.json (neutral creeps' abilities: "av_<value>" — their radius)."""
import functools
import json
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATS = os.path.join(_ROOT, "data", "stats")
_RADIUS_KEYS = ("radius", "aura_radius")        # the one radius an ability has; start/end/bounce radii are not it


@functools.lru_cache(maxsize=None)
def _hero_blocks(version):
    """{ability slug: its KV block} of every hero ability in a version."""
    from builders.silent import _decode_bytes, parse_kv
    import builders.site_common as site
    out = {}
    folder = os.path.join(_STATS, version, "heroes")
    if not os.path.isdir(folder):
        return out
    for name in sorted(os.listdir(folder)):
        if not name.startswith("npc_dota_hero_") or name == "npc_dota_hero_base.txt":
            continue
        with open(os.path.join(folder, name), "rb") as f:
            root = site.hero_ability_blocks(parse_kv(_decode_bytes(f.read())))
        out.update({k: v for k, v in (root or {}).items() if isinstance(v, dict)})
    return out


@functools.lru_cache(maxsize=None)
def _json(version, name):
    path = os.path.join(_STATS, version, name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _levels(raw):
    """KV "16 14 12" / 16 / {"value": "16 14"} -> "16/14/12"; "" when absent or all zero."""
    if isinstance(raw, dict):
        raw = raw.get("value", "")
    vals = [v for v in re.split(r"\s+", str(raw).strip()) if v]
    nums = []
    for v in vals:
        try:
            f = float(v)
        except ValueError:
            return ""
        nums.append(f"{f:g}")
    if not nums or all(float(n) == 0 for n in nums):
        return ""
    return nums[0] if len(set(nums)) == 1 else "/".join(nums)


def _kind(behavior):
    b = (behavior or "").upper()
    if "PASSIVE" in b:
        return "Passive"
    if "TOGGLE" in b:
        return "Toggle"
    if re.search(r"UNIT_TARGET|POINT|NO_TARGET|CHANNELLED|AUTOCAST", b):
        return "Active"
    return ""


def ability_props(slug, version):
    """{"kind", "aoe", "castrange", "manacost", "healthcost", "cooldown"} — "" for what the files don't say."""
    out = dict.fromkeys(("kind", "aoe", "castrange", "manacost", "healthcost", "cooldown"), "")
    if not slug or not version:
        return out
    block = _hero_blocks(version).get(slug)
    if block:
        values = block.get("AbilityValues") or {}
        pick = lambda key: block.get(key) or values.get(key)
        out.update(kind=_kind(block.get("AbilityBehavior")), castrange=_levels(pick("AbilityCastRange")),
                   manacost=_levels(pick("AbilityManaCost")), healthcost=_levels(pick("AbilityHealthCost")),
                   cooldown=_levels(pick("AbilityCooldown")),
                   aoe=next((_levels(values[k]) for k in _RADIUS_KEYS if k in values), ""))
        return out
    other = _json(version, "abilities.json").get(slug) or {}
    npc = _json(version, "npc_abilities.json").get(slug) or {}
    if other or npc:
        out.update(kind=_kind(other.get("AbilityBehavior")),
                   castrange=_levels(other.get("AbilityCastRange") or npc.get("AbilityCastRange", "")),
                   manacost=_levels(other.get("AbilityManaCost") or npc.get("AbilityManaCost", "")),
                   cooldown=_levels(other.get("AbilityCooldown") or npc.get("AbilityCooldown", "")),
                   aoe=next((_levels(npc[f"av_{k}"]) for k in _RADIUS_KEYS if f"av_{k}" in npc), ""))
    return out


def slug_of(spec_or_url):
    """An ability's slug from a card spec ({"slug"} or {"icon_url"}) or an icon url: ".../miniboss_alleviation.png"."""
    if isinstance(spec_or_url, dict):
        return spec_or_url.get("slug") or slug_of(spec_or_url.get("icon_url") or "")
    m = re.search(r"/([a-z0-9_]+)\.(?:png|webp|jpg)$", spec_or_url or "")
    return m.group(1) if m else ""
