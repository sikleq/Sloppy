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

from patch import game_files
from patch.kv import _decode_bytes, hero_ability_blocks, parse_kv

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATS = os.path.join(_ROOT, "data", "stats")
_RADIUS_KEYS = ("radius", "aura_radius")        # the one radius an ability has; start/end/bounce radii are not it


@functools.lru_cache(maxsize=None)
def _hero_blocks(version):
    """{ability slug: its KV block} of every hero ability in a version."""
    out = {}
    folder = os.path.join(_STATS, version, "heroes")
    if not os.path.isdir(folder):
        return _store_blocks(version)
    for name in sorted(os.listdir(folder)):
        if not name.startswith("npc_dota_hero_") or name == "npc_dota_hero_base.txt":
            continue
        with open(os.path.join(folder, name), "rb") as f:
            root = hero_ability_blocks(parse_kv(_decode_bytes(f.read())))
        out.update({k: v for k, v in (root or {}).items() if isinstance(v, dict)})
    return out


def _store_blocks(version):
    """A patch without data/stats/<v>/heroes (7.08-7.34, owner 2026-10-25: "мы должны решать такое и добыть все
    данные"): the store's own build — one npc_abilities.txt for every ability then, or per-hero files if it has them."""
    if version not in game_files.versions():
        return {}
    out = {}
    heroes = [p for p in game_files.listing(version, "scripts/npc/heroes")
              if p.rsplit("/", 1)[-1].startswith("npc_dota_hero_") and not p.endswith("npc_dota_hero_base.txt")]
    texts = [game_files.read(version, p) for p in heroes] or [game_files.npc(version, "npc_abilities.txt")]
    for text in texts:
        root = hero_ability_blocks(parse_kv(text)) if text else {}
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


def _kind(behavior, innate=False):
    b = (behavior or "").upper()
    if "PASSIVE" in b:
        return "Passive"
    if "TOGGLE" in b:
        return "Toggle"
    if re.search(r"UNIT_TARGET|POINT|NO_TARGET|CHANNELLED|AUTOCAST", b):
        return "Active"
    # an innate with nothing to cast is passive though its KV says only NOT_LEARNABLE (7.39 Electromagnetic
    # Repulsion; owner 2026-10-27: "the header lacks Passive")
    return "Passive" if innate else ""


def _names_facet(node, facet):
    """True when a KV block names the facet: a "special_bonus_facet_<facet>" value or "RequiresFacet" "<facet>"."""
    if isinstance(node, dict):
        return any(k == f"special_bonus_facet_{facet}" or (k == "RequiresFacet" and v == facet) or _names_facet(v, facet)
                   for k, v in node.items())
    return False


@functools.lru_cache(maxsize=None)
def _facet_grants(version):
    """{ability slug: facet slug} of the abilities a facet grants in a version (Facets → <facet> → Abilities →
    AbilityName in the heroes' KV of that patch's build, the game-files store)."""
    from patch.kv import parse_kv as _parse
    if version not in game_files.versions():
        return {}
    texts = [game_files.npc(version, "npc_heroes.txt") or ""] + [
        game_files.read(version, p) or "" for p in game_files.listing(version, "scripts/npc/heroes")
        if p.rsplit("/", 1)[-1].startswith("npc_dota_hero_")]
    out = {}
    for text in texts:
        for root in _parse(text).values():
            for hero in (root.values() if isinstance(root, dict) else []):
                for fslug, f in ((hero.get("Facets") or {}).items() if isinstance(hero, dict) else []):
                    if not isinstance(f, dict) or f.get("Deprecated"):
                        continue                # 7.41: facets gone, their abilities live on as innates (Slugger)
                    for a in (f.get("Abilities") or {}).values():
                        if isinstance(a, dict) and a.get("AbilityName"):
                            out.setdefault(a["AbilityName"], fslug)
    return out


def facet_of_ability(slug, version):
    """The facet that grants an ability in a version, or None (7.38b Venomous Volley: Medusa's slow-attacks facet; a
    hidden passive without art of its own — the game shows the facet's icon)."""
    return _facet_grants(version).get(slug) if slug and version else None


@functools.lru_cache(maxsize=None)
def hero_facets(hero_slug, version):
    """{facet slug: (name, colour, icon)} of a hero in a version, in the game's order: npc_heroes.txt "Facets" of that
    patch's build (Color + GradientID -> "Purple0", the name from the patch's own texts). The facets a later patch
    removes are named and drawn from here (owner 2026-10-29, 7.38 "Removed Agnostic and Elitist Facets")."""
    from patch import loc_history
    text = game_files.npc(version, "npc_heroes.txt") if version in game_files.versions() else None
    hero = next((h for root in parse_kv(text or "").values() if isinstance(root, dict)
                 for k, h in root.items() if k == f"npc_dota_hero_{hero_slug}" and isinstance(h, dict)), None)
    out = {}
    for slug, f in ((hero or {}).get("Facets") or {}).items():
        if not isinstance(f, dict) or f.get("Deprecated"):
            continue
        name = loc_history.tooltip(f"DOTA_Tooltip_Facet_{slug}", version) or ""
        if not name:                            # a facet that grants an ability is named by it (7.37e Phantasmagoria)
            granted = [a.get("AbilityName") for a in (f.get("Abilities") or {}).values() if isinstance(a, dict)]
            name = next((n for a in granted if a and (n := loc_history.tooltip(f"DOTA_Tooltip_Ability_{a}", version))),
                        "")
        out[slug] = (name, f"{f.get('Color', 'Gray')}{f.get('GradientID', '0')}", f.get("Icon", ""))
    return out


def facet_ability(facet, version):
    """The hero ability a facet changes — the one ability whose KV names the facet — or None (none or several)."""
    hits = [s for s, b in _hero_blocks(version).items() if isinstance(b, dict) and _names_facet(b, facet)]
    return hits[0] if len(hits) == 1 else None


def ability_props(slug, version):
    """{"kind", "aoe", "castrange", "manacost", "healthcost", "cooldown"} — "" for what the files don't say."""
    out = dict.fromkeys(("kind", "aoe", "castrange", "manacost", "healthcost", "cooldown"), "")
    if not slug or not version:
        return out
    block = _hero_blocks(version).get(slug)
    if block:
        values = block.get("AbilityValues") or {}
        pick = lambda key: block.get(key) or values.get(key)
        out.update(kind=_kind(block.get("AbilityBehavior"), innate=str(block.get("Innate", "")).strip() == "1"),
                   castrange=_levels(pick("AbilityCastRange")),
                   manacost=_levels(pick("AbilityManaCost")), healthcost=_levels(pick("AbilityHealthCost")),
                   cooldown=_levels(pick("AbilityCooldown")),
                   aoe=next((_levels(values[k]) for k in _RADIUS_KEYS if k in values), ""))
        # a value that grows with the hero's level ("hero_levelup", 7.41 innates): the header says "scales with level"
        out["level_scaled"] = any(isinstance(v, dict) and "hero_levelup" in v for v in values.values())
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
