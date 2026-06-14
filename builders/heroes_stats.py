"""Build heroes_stats.html — the Hero Stats table (Materials sub-tab).

One row per hero, columns = base stats. Three view modes via the View
dropdown (mirrors Neutral Stats):
  * Base     — bare values from the game files (StatusHealth = 120 etc).
  * Starting — level-1 values WITH attribute bonuses (HP = 120 + 22×Str,
               MP = base + 12×Int, Armor = base + Agi/6, Mag.resist = base +
               0.1×Int, Damage = base + primary-attr bonus, Attack Speed =
               base + 1×Agi). DEFAULT mode.
  * Expanded — everything in Starting + extra inspection columns (Gains/lvl,
               Armor %, Dmg min/max, Time to hit, projectile, turn rate,
               collision, bound radius).

Each "computed" column carries both Base and Starting values; the View
dropdown swaps them in via JS (data-base-* attrs on the td). Per-patch
change history (`data-hist` tooltip with overall first→today summary)
follows the current mode — base values get base history, starting values
get starting history.

Data sources:
  * data/stats/<patch>/heroes.json — slim scrape (attributes, base HP/mana,
    armor, damage, BAT, MS, range, magic resistance). All 116 patches.
  * data/stats/<patch>/heroes_raw.json — raw-only fields (vision day/night,
    projectile speed, base attack speed, turn rate, collision hull, bound
    radius). Built by scripts/fetch_hero_history.py from d2vpkr's historical
    npc_heroes.txt. All 116 patches.
  * Spirit Bear is injected from data/stats/<patch>/units.json plus its
    npc_units.txt block, because it is a ConsideredHero unit rather than a
    normal npc_dota_hero_* entry.

Run AFTER build_patch.py (needs data/site_meta.json):
    python build_patch.py
    python build_heroes_stats.py
"""
from __future__ import annotations

import html as _html
import json as _json
import math as _math
import re as _re
from pathlib import Path

import sys as _sys

_HERE = Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_HERE))

import site_common as _site

STATS_DIR = _HERE / "data" / "stats"
ASSET_VERSION = _site.compute_asset_version()

_esc = lambda s: _html.escape(str(s), quote=True)

# ---- engine constants for "Starting" mode (level-1 with attribute bonuses) ---
# Current-patch values. User-correctable — adjust here when Valve tweaks any
# of these and rerun the build. The computed columns' HISTORY uses these
# constants for past patches too (the historical constants did differ).
HP_PER_STR        = 22.0   # +22 max HP per Strength
HPREG_PER_STR     = 0.1    # +0.1 HP regen per Strength
MANA_PER_INT      = 12.0   # +12 max mana per Intelligence
MANAREG_PER_INT   = 0.05   # +0.05 mana regen per Intelligence
ARMOR_PER_AGI     = 1 / 6  # 0.1667 armor per Agility
MR_PER_INT        = 0.1    # +0.1 % magic resistance per Intelligence
AS_PER_AGI        = 1.0    # +1 attack speed per Agility
DMG_PER_PRIMARY   = 1.0    # Str/Agi/Int hero gains +1 damage per primary point
# Universal heroes get a multiplier on the SUM of all three attributes, FLOORED
# before adding to base damage (Abaddon 0.45×62 = 27.9 → 27 → 22-32 base = 49-59).
# The multiplier has changed over time — patch-gated in _universal_dmg_mult():
#   7.33  → 0.6 (introduced with Universal heroes)
#   7.33c → 0.7
#   7.38  → 0.45 (current)

# Ogre Magi innate — mana / mana regen scale with Strength (he has 0 base Int).
OGRE_MANA_PER_STR    = 6.0
OGRE_MANAREG_PER_STR = 0.02


# ---------- patch ordering / dates ----------

def _patch_sort_key(v: str):
    parts = v.split(".")
    major = int(parts[0]) if parts[0].isdigit() else 0
    rest = parts[1] if len(parts) > 1 else "0"
    num, suf = "", ""
    for c in rest:
        if c.isdigit():
            num += c
        else:
            suf += c
    return (major, int(num or 0), suf)


def _load_patch_dates() -> dict[str, str]:
    meta = _HERE / "data" / "site_meta.json"
    try:
        return _json.loads(meta.read_text(encoding="utf-8")).get("patch_dates", {})
    except Exception:
        return {}


def _versions() -> list[str]:
    vers = [p.name for p in STATS_DIR.iterdir()
            if (p / "heroes.json").exists()]
    return sorted(vers, key=_patch_sort_key)


# ---------- hero identity ----------

_NAME_OVERRIDES = {
    "largo": "Largo",
}
_EXCLUDE = {"npc_dota_hero_base", "npc_dota_hero_target_dummy"}
SPIRIT_BEAR_HERO = "npc_dota_hero_spirit_bear"
SPIRIT_BEAR_UNIT = "npc_dota_lone_druid_bear1"
SPIRIT_BEAR_NAME = "Spirit Bear"


def _load_display_names() -> dict[str, str]:
    out = {}
    try:
        data = _json.loads((_HERE / "data" / "herolist.json").read_text(encoding="utf-8"))
        for h in data["result"]["data"]["heroes"]:
            out[h["name"]] = h.get("name_english_loc") or h.get("name_loc") or h["name"]
    except Exception as exc:
        print(f"  ! herolist.json unreadable ({exc}) — falling back to slugs")
    return out


def _display_name(internal: str, names: dict[str, str]) -> str:
    if internal == SPIRIT_BEAR_HERO:
        return SPIRIT_BEAR_NAME
    if internal in names:
        return names[internal]
    slug = internal.replace("npc_dota_hero_", "")
    if slug in _NAME_OVERRIDES:
        return _NAME_OVERRIDES[slug]
    pretty = slug.replace("_", " ").title()
    print(f"  ! no display name for {internal} — using '{pretty}' "
          f"(add to _NAME_OVERRIDES)")
    return pretty


# ---------- per-patch field access (heroes.json) ----------

_NUM_RE = _re.compile(r"-?\d+(?:\.\d+)?")


def _to_float(v):
    """Robust numeric parse — old KV scrapes occasionally carry typo'd
    values like '21a' (Valve's own files). Take the leading number."""
    try:
        return float(v)
    except (TypeError, ValueError):
        m = _NUM_RE.search(str(v))
        return float(m.group(0)) if m else None


_FIELD_DEFAULTS = {
    "ArmorPhysical": -1, "AttackDamageMin": 0, "AttackDamageMax": 0,
    "AttackRate": 1.7, "AttackRange": 150, "MovementSpeed": 300,
    "AttributeBaseStrength": 0, "AttributeStrengthGain": 0,
    "AttributeBaseAgility": 0, "AttributeAgilityGain": 0,
    "AttributeBaseIntelligence": 0, "AttributeIntelligenceGain": 0,
    "StatusHealth": 120, "StatusMana": 75,
    "StatusHealthRegen": 0.25, "StatusManaRegen": 0,
    "MagicalResistance": 25,
}


def _field(snap: dict, hero: str, f: str):
    """Hero's value for field f in one patch snapshot, falling back to
    npc_dota_hero_base (the engine default block) and then to the static
    defaults table."""
    h = snap.get(hero) or {}
    if f in h:
        v = _to_float(h[f])
        if v is not None:
            return v
    base = snap.get("npc_dota_hero_base") or {}
    if f in base:
        v = _to_float(base[f])
        if v is not None:
            return v
    return float(_FIELD_DEFAULTS.get(f, 0))


_ATTR_META = {
    "DOTA_ATTRIBUTE_STRENGTH":  ("str", "Strength",     "strength.webp",     0),
    "DOTA_ATTRIBUTE_AGILITY":   ("agi", "Agility",      "agility.webp",      1),
    "DOTA_ATTRIBUTE_INTELLECT": ("int", "Intelligence", "intelligence.webp", 2),
    "DOTA_ATTRIBUTE_ALL":       ("uni", "Universal",    "universal.webp",    3),
}


def _attr_filter_buttons() -> str:
    buttons = [
        ("str", "Strength", "icons/strength.webp"),
        ("agi", "Agility", "icons/agility.webp"),
        ("int", "Intelligence", "icons/intelligence.webp"),
        ("uni", "Universal", "icons/universal.webp"),
    ]
    html = ['<span class="hs-attr-filter-group" aria-label="Primary attribute filter">']
    for key, label, icon in buttons:
        html.append(
            '<button type="button" class="hs-attr-filter" '
            f'data-attr-filter="{key}" aria-pressed="false" title="Show {label} heroes">'
            f'<img src="{icon}" alt="{label}" loading="lazy"></button>'
        )
    html.append('</span>')
    return ''.join(html)


def _attr_of(snap: dict, hero: str):
    raw = (snap.get(hero) or {}).get("AttributePrimary", "")
    return _ATTR_META.get(raw)


# ---------- raw KV (npc_heroes.txt → heroes_raw.json per patch) ----------

# Hull name → collision radius (engine table; heroes are all _HERO = 24).
_HULL_RADIUS = {
    "DOTA_HULL_SIZE_HERO": 24, "DOTA_HULL_SIZE_REGULAR": 16,
    "DOTA_HULL_SIZE_SMALL": 8, "DOTA_HULL_SIZE_SIEGE": 16,
    "DOTA_HULL_SIZE_HUGE": 80, "DOTA_HULL_SIZE_BUILDING": 81,
}
_RAW_DEFAULTS = {
    "ProjectileSpeed": 900, "BaseAttackSpeed": 100, "MovementTurnRate": 0.6,
    "VisionDaytimeRange": 1800, "VisionNighttimeRange": 800, "RingRadius": 70,
    "BoundsHullName": "DOTA_HULL_SIZE_HERO",
    "AttackCapabilities": "DOTA_UNIT_CAP_MELEE_ATTACK",
}


def _load_raw_heroes(version: str) -> dict[str, dict]:
    """Raw-only hero fields for one patch, from the pre-parsed
    data/stats/<version>/heroes_raw.json (produced by
    scripts/fetch_hero_history.py from d2vpkr's historical npc_heroes.txt)."""
    path = STATS_DIR / version / "heroes_raw.json"
    if not path.exists():
        return {}
    try:
        return _json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  ! {path} unreadable ({exc})")
        return {}


def _load_units(version: str) -> dict[str, dict]:
    path = STATS_DIR / version / "units.json"
    if not path.exists():
        return {}
    try:
        return _json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  ! {path} unreadable ({exc})")
        return {}


_KV_BLOCK_CACHE: dict[tuple[str, str], str] = {}


def _extract_kv_block(version: str, filename: str, key: str) -> dict[str, str]:
    path = STATS_DIR / version / filename
    if not path.exists():
        return {}
    try:
        cache_key = (version, filename)
        text = _KV_BLOCK_CACHE.get(cache_key)
        if text is None:
            text = path.read_text(encoding="utf-8", errors="ignore")
            _KV_BLOCK_CACHE[cache_key] = text
    except Exception as exc:
        print(f"  ! {path} unreadable ({exc})")
        return {}
    marker = f'"{key}"'
    start = text.find(marker)
    if start < 0:
        return {}
    brace = text.find("{", start + len(marker))
    if brace < 0:
        return {}
    depth = 0
    end = brace
    for idx in range(brace, len(text)):
        ch = text[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = idx
                break
    block = text[brace + 1:end]
    return dict(_re.findall(r'"([^"]+)"\s+"([^"]*)"', block))


def _extract_unit_block(version: str, unit: str) -> dict[str, str]:
    return _extract_kv_block(version, "npc_units.txt", unit)


def _extract_hero_block(version: str, hero: str) -> dict[str, str]:
    return _extract_kv_block(version, "npc_heroes.txt", hero)


def _inject_spirit_bear(snaps: dict[str, dict], raws: dict[str, dict]) -> None:
    """Expose Spirit Bear in Hero Stats without pretending it is in heroes.json.

    The current game treats it as a hero-like unit (`ConsideredHero`), while
    the extracted hero tables only include `npc_dota_hero_*` entries. We map
    the bear's unit stats onto the same fields Hero Stats already understands.
    """
    hero_fields = (
        "ArmorPhysical", "AttackDamageMin", "AttackDamageMax", "AttackRate",
        "AttackRange", "MovementSpeed", "StatusHealth", "StatusHealthRegen",
        "StatusMana", "StatusManaRegen", "MagicalResistance",
        "AttributePrimary", "AttributeBaseStrength", "AttributeStrengthGain",
        "AttributeBaseAgility", "AttributeAgilityGain",
        "AttributeBaseIntelligence", "AttributeIntelligenceGain",
    )
    raw_fields = (
        "ProjectileSpeed", "BaseAttackSpeed", "MovementTurnRate",
        "VisionDaytimeRange", "VisionNighttimeRange", "RingRadius",
        "BoundsHullName", "AttackCapabilities",
    )
    defaults = {
        "AttributePrimary": "DOTA_ATTRIBUTE_ALL",
        "AttributeBaseStrength": 0,
        "AttributeBaseAgility": 0,
        "AttributeBaseIntelligence": 0,
        "AttributeStrengthGain": 0,
        "AttributeAgilityGain": 0,
        "AttributeIntelligenceGain": 0,
        "MagicalResistance": 25,
        "BaseAttackSpeed": 100,
        "ProjectileSpeed": 0,
        "MovementTurnRate": 0.6,
        "VisionDaytimeRange": 1800,
        "VisionNighttimeRange": 800,
        "RingRadius": 70,
        "BoundsHullName": "DOTA_HULL_SIZE_HERO",
        "AttackCapabilities": "DOTA_UNIT_CAP_MELEE_ATTACK",
    }
    for version, snap in snaps.items():
        merged = {}
        merged.update(_load_units(version).get(SPIRIT_BEAR_UNIT, {}))
        merged.update(_extract_unit_block(version, SPIRIT_BEAR_UNIT))
        if not merged:
            continue
        hero = {k: (merged[k] if k in merged else defaults[k]) for k in hero_fields
                if k in merged or k in defaults}
        raw = {k: (merged[k] if k in merged else defaults[k]) for k in raw_fields
               if k in merged or k in defaults}
        snap[SPIRIT_BEAR_HERO] = hero
        raws.setdefault(version, {})[SPIRIT_BEAR_HERO] = raw


def _raw_field(raw: dict, hero: str, key: str):
    h = raw.get(hero) or {}
    if key in h:
        return h[key]
    base = raw.get("npc_dota_hero_base") or {}
    if key in base:
        return base[key]
    return _RAW_DEFAULTS.get(key)


def _raw_num(raw: dict, hero: str, key: str) -> float:
    v = _to_float(_raw_field(raw, hero, key))
    return v if v is not None else float(_RAW_DEFAULTS.get(key, 0))


# ---------- value formatting ----------

def _g(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _g1(v: float) -> str:
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _g0(v: float) -> str:
    return f"{round(v)}"


def _gpct(v: float) -> str:
    return f'{_g(v)}%'


def _g1pct(v: float) -> str:
    return f'{_g1(v)}%'


def _gregen(v: float) -> str:
    return "0" if abs(v) < 1e-9 else f"{v:.2f}"


# ---------- per-hero innate attribute-conversion modifiers ----------
# A handful of heroes have an ALWAYS-ON innate that converts a primary
# attribute into a secondary stat we display (attack range, move speed,
# armor, regens, magic resist). These bonuses are patch-gated and their
# factors change over time. They affect the "Starting"/"Expanded" computed
# values only — never the raw "Base" values. To stay accurate per patch,
# the value functions need to know WHICH patch they're computing; we thread
# the version through a module-global set by the history loop and render.
_CTX_VERSION = ["7.41d"]


def _set_ctx_version(v: str) -> None:
    _CTX_VERSION[0] = v


def _ge(patch: str, ref: str) -> bool:
    return _patch_sort_key(patch) >= _patch_sort_key(ref)


def _innate_bonus(col_key: str, s: dict, h: str, r: dict | None = None) -> float:
    """Extra (additive) bonus to a computed Starting column from a hero's
    innate attribute-conversion ability, gated by the current patch.
    Returns 0 for every hero/column without such an innate.

    Extend this for more heroes — each is one `if slug == … and _ge(...)`
    block. Currently covered:
      • Morphling   — Ebb and Flow (innate 7.41+): Agi→Attack Range,
                      Agi→Move Speed.
      • Void Spirit — Intrinsic Edge (innate 7.36+): patch-gated secondary
                      attribute bonuses; 7.41+ switches to Damage/HP regen/
                      Mana regen/Attack Speed.
      • Centaur     — Horsepower (innate 7.36+): Str→Move Speed (capped).
      • Axe         — One Man Army (innate 7.36+): Armor→Strength.
    Known but NOT yet modelled (don't map to a single displayed column or
    need dynamic state): Dark Seer (Int floor = max of Str/Agi), Tiny /
    Morphling-facet (slow/status/cooldown), Elder Titan Momentum, Silencer
    Glaives, Drow Trueshot aura."""
    slug = h.replace("npc_dota_hero_", "")
    ver = _CTX_VERSION[0]

    if slug == "morphling" and _ge(ver, "7.41"):
        agi = _field(s, h, "AttributeBaseAgility")
        if col_key == "range":
            # Agi→Ranged Attack Range: 20% (7.41) → 25% (7.41d). Morphling
            # is ranged, so it always applies.
            return agi * (0.25 if _ge(ver, "7.41d") else 0.20)
        if col_key == "ms":
            return agi * 0.15            # Agi→Move Speed: 15% (since 7.41)

    if slug == "void_spirit" and _ge(ver, "7.36"):
        # Intrinsic Edge:
        #   7.36-7.36a: +33% secondary bonuses from attributes
        #   7.36b-7.40: +25% secondary bonuses from attributes
        #   7.41+: +30% HP regen / mana regen / attack speed, no armor/MR.
        if _ge(ver, "7.41"):
            pct = 0.30
            if col_key == "hpr":
                return HPREG_PER_STR * _field(s, h, "AttributeBaseStrength") * pct
            if col_key == "mpr":
                return MANAREG_PER_INT * _field(s, h, "AttributeBaseIntelligence") * pct
            if col_key == "aspd":
                return AS_PER_AGI * _field(s, h, "AttributeBaseAgility") * pct
            return 0.0
        pct = 0.25 if _ge(ver, "7.36b") else 0.33
        if col_key == "armor":
            return ARMOR_PER_AGI * _field(s, h, "AttributeBaseAgility") * pct
        if col_key == "hpr":
            return HPREG_PER_STR * _field(s, h, "AttributeBaseStrength") * pct
        if col_key == "mpr":
            return MANAREG_PER_INT * _field(s, h, "AttributeBaseIntelligence") * pct
        if col_key == "mr":
            return MR_PER_INT * _field(s, h, "AttributeBaseIntelligence") * pct

    if slug == "centaur" and _ge(ver, "7.36"):
        if col_key == "ms":
            # Str→Move Speed factor over time: 40% (7.36) → 35% (7.36b) →
            # 30% (7.37b) → 30% (7.41 rework) → 40% (7.41a+).
            if _ge(ver, "7.41a"):
                f = 0.40
            elif _ge(ver, "7.37b"):
                f = 0.30
            elif _ge(ver, "7.36b"):
                f = 0.35
            else:
                f = 0.40
            return _field(s, h, "AttributeBaseStrength") * f

    if slug == "axe" and _ge(ver, "7.36") and col_key == "str":
        armor = (_field(s, h, "ArmorPhysical")
                 + ARMOR_PER_AGI * _field(s, h, "AttributeBaseAgility"))
        return armor * 0.5

    # Dragon Knight — Dragon Blood (innate): bonus HP regen AND armor, both
    # 2 + 0.5 per hero level. Level-1 (Starting) value here; scripts.js owns the
    # per-level recompute, this keeps the server-rendered level-1 cell consistent.
    if slug == "dragon_knight" and col_key in ("hpr", "armor"):
        return 2 + 0.5 * 1
    # Lifestealer — innate bonus Attack Speed, 4 per hero level (level-1 here).
    if slug == "life_stealer" and col_key == "aspd":
        return 4 * 1
    # Drow — innate bonus Agility = 10% + 1% per level of her current Agility
    # (self-referential off base agi at level 1; scripts.js scales per level).
    if slug == "drow_ranger" and col_key == "agi":
        return _field(s, h, "AttributeBaseAgility") * (0.10 + 0.01 * 1)
    # ── Innates added below all delegate per-level / per-patch scaling to
    # scripts.js (`hsTablePatch`/`patchGe`). Here we only seed the level-1 cell.
    # Razor — Unstable Current (7.41a+): +1 Move Speed per level (level 1 → +1).
    if slug == "razor" and col_key == "ms" and _ge(ver, "7.41a"):
        return 1.0
    # Ursa — Earthshock Maul: bonus damage = % of CURRENT HP.
    # 1.5 @ 7.36..7.37a → leveled 1.2/1.3/1.4/1.5 (7.37b..7.39c, take max) → 1.25 @ 7.39d+.
    if slug == "ursa" and col_key == "dmg" and _ge(ver, "7.36"):
        pct = 1.25 if _ge(ver, "7.39d") else 1.5
        # use the base raw HP (StatusHealth) — full HP needs str scaling done in caller
        return _field(s, h, "StatusHealth") * pct / 100.0
    # Dark Seer — Quick Wit: +AS per Int. 0.5 @ 7.36..7.37e → 1.0 @ 7.38+.
    if slug == "dark_seer" and col_key == "aspd" and _ge(ver, "7.36"):
        f = 1.0 if _ge(ver, "7.38") else 0.5
        return _field(s, h, "AttributeBaseIntelligence") * f
    # Keeper of the Light — Bright Speed (7.41a+): +1 MS per N Int. 2.5 (7.41a..7.41b) → 3 (7.41c+).
    if slug == "keeper_of_the_light" and col_key == "ms" and _ge(ver, "7.41a"):
        n = 3.0 if _ge(ver, "7.41c") else 2.5
        return _field(s, h, "AttributeBaseIntelligence") / n
    # Beastmaster — Inner Beast (7.41a+): +(7 + 3·level) Attack Speed, hero only.
    if slug == "beastmaster" and col_key == "aspd" and _ge(ver, "7.41a"):
        return 7 + 3 * 1
    # Death Prophet — Witchcraft: % bonus to MS. We can't return a multiplier
    # via the additive _innate_bonus interface, so leave the level-1 ms cell to
    # scripts.js (it applies the multiplier on every recompute).

    return 0.0


def _start_attr(s, h, r, key: str) -> float:
    field_map = {
        "str": "AttributeBaseStrength",
        "agi": "AttributeBaseAgility",
        "int": "AttributeBaseIntelligence",
    }
    return _field(s, h, field_map[key]) + _innate_bonus(key, s, h, r)


def _whole_start_attr(s, h, r, key: str) -> int:
    return int(_math.floor(_start_attr(s, h, r, key)))


def _techies_pool_regen_l1(s, h, r) -> float:
    if not h.endswith("_techies") or not _ge(_CTX_VERSION[0], "7.41a"):
        return 0.0
    lvl = 1
    pct = (0.001 + 0.0001 * lvl) if _ge(_CTX_VERSION[0], "7.41c") else (0.0008 + 0.0002 * lvl)
    return _mp_l1(s, h, r) * pct


# ---------- value functions ----------

def _f(field):
    """Convenience: return value_fn that reads `field` directly from snap."""
    return lambda s, h, r: _field(s, h, field)


def _universal_dmg_mult() -> float:
    """Damage-per-attribute multiplier for Universal heroes at the current
    context patch. 0.6 (7.33) → 0.7 (7.33c) → 0.45 (7.38+)."""
    ver = _CTX_VERSION[0]
    if _ge(ver, "7.38"):
        return 0.45
    if _ge(ver, "7.33c"):
        return 0.7
    return 0.6   # 7.33–7.33b (and the floor for any earlier ctx; pre-7.33 no
    #              hero is Universal so this branch isn't reached for them)


def _primary_dmg(s, h):
    """Bonus attack damage from primary attribute(s) at level 1, FLOORED
    (in-game truncates the attribute bonus before adding it to base damage).
    Str/Agi/Int heroes: +1 per primary attribute point.
    Universal: multiplier (patch-gated) on the SUM of Str + Agi + Int.
    See https://liquipedia.net/dota2/Attributes."""
    meta = _attr_of(s, h)
    if meta is None:
        return 0.0
    kind = meta[0]
    if kind == "str":
        bonus = DMG_PER_PRIMARY * _whole_start_attr(s, h, None, "str")
    elif kind == "agi":
        bonus = DMG_PER_PRIMARY * _whole_start_attr(s, h, None, "agi")
    elif kind == "int":
        bonus = DMG_PER_PRIMARY * _whole_start_attr(s, h, None, "int")
    else:  # Universal — multiplier on the SUM of all three attributes
        total = (_field(s, h, "AttributeBaseStrength")
                 + _field(s, h, "AttributeBaseAgility")
                 + _field(s, h, "AttributeBaseIntelligence"))
        mult = _universal_dmg_mult()
        if h.endswith("_void_spirit") and _ge(_CTX_VERSION[0], "7.41"):
            # Intrinsic Edge: +15% attack damage per attribute since 7.41.
            mult *= 1.15
        bonus = mult * total
    return float(_math.floor(bonus))


# Damage ---------------------------------------------------------------------

def _dmg_min_base(s, h, r):
    v = _field(s, h, "AttackDamageMin")
    if h.endswith("_void_spirit") and _ge(_CTX_VERSION[0], "7.41") and not _ge(_CTX_VERSION[0], "7.41d"):
        return v - 4
    return v


def _dmg_max_base(s, h, r):
    v = _field(s, h, "AttackDamageMax")
    if h.endswith("_void_spirit") and _ge(_CTX_VERSION[0], "7.41") and not _ge(_CTX_VERSION[0], "7.41d"):
        return v - 4
    return v


def _dmg_avg_base(s, h, r):
    return (_field(s, h, "AttackDamageMin") + _field(s, h, "AttackDamageMax")) / 2


def _dmg_min_start(s, h, r):
    return _dmg_min_base(s, h, r) + _primary_dmg(s, h)


def _dmg_max_start(s, h, r):
    return _dmg_max_base(s, h, r) + _primary_dmg(s, h)


def _dmg_avg_start(s, h, r):
    return _dmg_avg_base(s, h, r) + _primary_dmg(s, h)


def _dmg_range_base(s, h, r):
    return f'{_g0(_dmg_min_base(s, h, r))}–{_g0(_dmg_max_base(s, h, r))}'


def _dmg_range_start(s, h, r):
    return f'{_g0(_dmg_min_start(s, h, r))}–{_g0(_dmg_max_start(s, h, r))}'


# HP / MP / regens -----------------------------------------------------------

def _hp_l1(s, h, r):
    return round(_field(s, h, "StatusHealth")
                 + HP_PER_STR * _whole_start_attr(s, h, r, "str"))


def _hpreg_l1(s, h, r):
    return round(_field(s, h, "StatusHealthRegen")
                 + HPREG_PER_STR * _whole_start_attr(s, h, r, "str")
                 + _innate_bonus("hpr", s, h, r), 2)


def _mp_base_raw(s, h, r):
    """Base mode raw mana — Huskar still forced to 0 (no mana pool ever)."""
    if h.endswith("_huskar"):
        return 0.0
    return _field(s, h, "StatusMana")


def _mp_l1(s, h, r):
    slug = h.replace("npc_dota_hero_", "")
    if slug == "huskar":
        return 0.0
    if slug == "ogre_magi":
        return round(_field(s, h, "StatusMana")
                     + OGRE_MANA_PER_STR * _whole_start_attr(s, h, r, "str")
                     + MANA_PER_INT * _whole_start_attr(s, h, r, "int"))
    return round(_field(s, h, "StatusMana")
                 + MANA_PER_INT * _whole_start_attr(s, h, r, "int"))


def _mpreg_base_raw(s, h, r):
    if h.endswith("_huskar"):
        return 0.0
    return _field(s, h, "StatusManaRegen")


def _mpreg_l1(s, h, r):
    slug = h.replace("npc_dota_hero_", "")
    if slug == "huskar":
        return 0.0
    if slug == "ogre_magi":
        return round(_field(s, h, "StatusManaRegen")
                     + OGRE_MANAREG_PER_STR * _start_attr(s, h, r, "str")
                     + MANAREG_PER_INT * _start_attr(s, h, r, "int"), 2)
    return round(_field(s, h, "StatusManaRegen")
                 + MANAREG_PER_INT * _whole_start_attr(s, h, r, "int")
                 + _innate_bonus("mpr", s, h, r)
                 + _techies_pool_regen_l1(s, h, r), 2)


# Armor / MR / Attack speed --------------------------------------------------

def _armor_base(s, h, r):
    return _field(s, h, "ArmorPhysical")


def _armor_l1(s, h, r):
    return round(_field(s, h, "ArmorPhysical")
                 + ARMOR_PER_AGI * _field(s, h, "AttributeBaseAgility")
                 + _innate_bonus("armor", s, h, r), 1)


def _mr_base(s, h, r):
    return _field(s, h, "MagicalResistance")


def _mr_l1(s, h, r):
    return round(_field(s, h, "MagicalResistance")
                 + MR_PER_INT * _field(s, h, "AttributeBaseIntelligence")
                 + _innate_bonus("mr", s, h, r), 1)


def _aspd_base(s, h, r):
    return _raw_num(r, h, "BaseAttackSpeed")


def _aspd_l1(s, h, r):
    return (_raw_num(r, h, "BaseAttackSpeed")
            + AS_PER_AGI * _field(s, h, "AttributeBaseAgility")
            + _innate_bonus("aspd", s, h, r))


# Attack range / Move speed (Starting may add an innate attribute factor) -----

def _range_base(s, h, r):
    return _field(s, h, "AttackRange")


def _range_l1(s, h, r):
    return round(_field(s, h, "AttackRange") + _innate_bonus("range", s, h, r))


def _ms_base(s, h, r):
    return _field(s, h, "MovementSpeed")


def _ms_l1(s, h, r):
    return round(_field(s, h, "MovementSpeed") + _innate_bonus("ms", s, h, r))


# Expanded helper values ------------------------------------------------------

def _gains_per_level(s, h, r):
    return round(_field(s, h, "AttributeStrengthGain")
                 + _field(s, h, "AttributeAgilityGain")
                 + _field(s, h, "AttributeIntelligenceGain"), 1)


def _armor_factor(a):
    return (0.06 * a) / (1 + 0.06 * abs(a))


def _ehp_phys_base(s, h, r):
    hp = _field(s, h, "StatusHealth")
    return round(hp / max(0.01, 1 - _armor_factor(_armor_base(s, h, r)))) if hp else 0


def _ehp_phys_l1(s, h, r):
    hp = _hp_l1(s, h, r)
    return round(hp / max(0.01, 1 - _armor_factor(_armor_l1(s, h, r)))) if hp else 0


def _ehp_mag_base(s, h, r):
    hp = _field(s, h, "StatusHealth")
    return round(hp / max(0.01, 1 - _mr_base(s, h, r) / 100)) if hp else 0


def _ehp_mag_l1(s, h, r):
    hp = _hp_l1(s, h, r)
    return round(hp / max(0.01, 1 - _mr_l1(s, h, r) / 100)) if hp else 0


def _armor_pct_base(s, h, r):
    return round(_armor_factor(_armor_base(s, h, r)) * 100)


def _armor_pct_l1(s, h, r):
    return round(_armor_factor(_armor_l1(s, h, r)) * 100)


def _t_per_attack_base(s, h, r):
    bat = _field(s, h, "AttackRate")
    ats = _raw_num(r, h, "BaseAttackSpeed") or 100
    return round(bat * 100 / ats, 2) if ats else round(bat, 2)


def _t_per_attack_l1(s, h, r):
    bat = _field(s, h, "AttackRate")
    ats = _aspd_l1(s, h, r) or 100
    return round(bat * 100 / ats, 2) if ats else round(bat, 2)


def _collision(s, h, r):
    return float(_HULL_RADIUS.get(str(_raw_field(r, h, "BoundsHullName")), 24))


# ---------- column model ----------
# Each entry describes one logical column. Cells track BOTH a Base value and a
# Starting value (some columns differ between modes, e.g. HP = 120 raw vs
# 120+22×Str at L1); the View dropdown swaps them on the client via JS.
#   key       — data-col + CSS class hs-col-<key>.
#   label     — header text.
#   mode      — 'core'  always visible | 'extra' visible only in Expanded.
#   pol       — 'hi' / 'lo' heatmap polarity.
#   fmt       — value → string (used when disp_* are None).
#   fn_base / fn_starting — value functions per mode.
#   disp_base / disp_starting — optional HTML producers (e.g. damage range
#                               "21–28", magic-res "26%").
#   hist      — True → emit per-patch change-history tooltip.
#   raw       — True → value uses heroes_raw.json (raw-only field).

def _col(key, label, *, mode="core", pol="hi", fmt=_g,
         fn_base, fn_starting=None,
         disp_base=None, disp_starting=None,
         hist=True, raw=False):
    return {
        "key": key, "label": label, "mode": mode, "pol": pol, "fmt": fmt,
        "fn_base": fn_base, "fn_starting": fn_starting or fn_base,
        "disp_base": disp_base, "disp_starting": disp_starting,
        "hist": hist, "raw": raw,
    }


COLUMNS = [
    # ── HP / MP / regens ────────────────────────────────────────────────
    _col("hp",  "HP", fmt=_g0, fn_base=_f("StatusHealth"), fn_starting=_hp_l1),
    _col("mp",  "MP", fmt=_g0, fn_base=_mp_base_raw,        fn_starting=_mp_l1),
    _col("hpr", "HP regen", fmt=_gregen,
         fn_base=_f("StatusHealthRegen"), fn_starting=_hpreg_l1),
    _col("mpr", "MP regen", fmt=_gregen,
         fn_base=_mpreg_base_raw, fn_starting=_mpreg_l1),

    # ── Attributes ─────────────────────────────────────────────────────
    _col("str",      "STR",      fn_base=_f("AttributeBaseStrength"),
         fn_starting=lambda s, h, r: _start_attr(s, h, r, "str")),
    _col("str_gain", "STR+",     fn_base=_f("AttributeStrengthGain")),
    _col("agi",      "AGI",      fn_base=_f("AttributeBaseAgility"),
         fn_starting=lambda s, h, r: _start_attr(s, h, r, "agi")),
    _col("agi_gain", "AGI+",     fn_base=_f("AttributeAgilityGain")),
    _col("int",      "INT",      fn_base=_f("AttributeBaseIntelligence"),
         fn_starting=lambda s, h, r: _start_attr(s, h, r, "int")),
    _col("int_gain", "INT+",     fn_base=_f("AttributeIntelligenceGain")),
    _col("gper",     "Gains/lvl",       mode="extra", fmt=_g1, fn_base=_gains_per_level),

    # ── Defenses ──────────────────────────────────────────────────────
    _col("armor", "Armor", fmt=_g1, fn_base=_armor_base, fn_starting=_armor_l1),
    _col("mr",    "Mag. resist", fn_base=_mr_base, fn_starting=_mr_l1,
         disp_base=lambda s, h, r: _gpct(_mr_base(s, h, r)),
         disp_starting=lambda s, h, r: _g1pct(_mr_l1(s, h, r))),

    # ── Damage ────────────────────────────────────────────────────────
    _col("dmg",  "Damage", fmt=_g0,
         fn_base=_dmg_avg_base, fn_starting=_dmg_avg_start,
         ),
    _col("dmin", "Min Dmg", mode="extra", fmt=_g0,
         fn_base=_dmg_min_base, fn_starting=_dmg_min_start),
    _col("dmax", "Max Dmg", mode="extra", fmt=_g0,
         fn_base=_dmg_max_base, fn_starting=_dmg_max_start),

    # ── Attack mechanics ──────────────────────────────────────────────
    _col("aspd", "Attack Speed", fmt=_g0,
         fn_base=_aspd_base, fn_starting=_aspd_l1, raw=True),
    _col("ms",   "Move Speed",   fn_base=_ms_base, fn_starting=_ms_l1),
    _col("bat",  "BAT", pol="lo", fn_base=_f("AttackRate")),

    # ── Vision ────────────────────────────────────────────────────────
    _col("dvision", "Day Vision", fmt=_g0,
         fn_base=lambda s, h, r: _raw_num(r, h, "VisionDaytimeRange"), raw=True),
    _col("nvision", "Night Vision", fmt=_g0,
         fn_base=lambda s, h, r: _raw_num(r, h, "VisionNighttimeRange"), raw=True),

    _col("range", "Attack Range", fmt=_g0, fn_base=_range_base, fn_starting=_range_l1),

    # Expanded extras ---------------------------------------------------------
    _col("proj",      "Projectile", mode="extra", fmt=_g0,
         fn_base=lambda s, h, r: _raw_num(r, h, "ProjectileSpeed"), raw=True),
    _col("turn",      "Turn Rate",  mode="extra",
         fn_base=lambda s, h, r: _raw_num(r, h, "MovementTurnRate"), raw=True),
    _col("collision", "Collision",  mode="extra", pol="lo",
         fn_base=_collision, raw=True),
    _col("bound",     "Bound Radius", mode="extra", pol="lo",
         fn_base=lambda s, h, r: _raw_num(r, h, "RingRadius"), raw=True),
]

_BASE_COL_BY_KEY = {col["key"]: col for col in COLUMNS}
_EXTRA_COLS = {
    "ehp_phys": _col("ehp_phys", "EHP\nphys", mode="extra", fmt=_g0,
                     fn_base=_ehp_phys_base, fn_starting=_ehp_phys_l1),
    "ehp_mag": _col("ehp_mag", "EHP\nmag", mode="extra", fmt=_g0,
                    fn_base=_ehp_mag_base, fn_starting=_ehp_mag_l1),
    "armor_pct": _col("armor_pct", "Armor %", mode="extra", fmt=_gpct,
                      fn_base=_armor_pct_base, fn_starting=_armor_pct_l1,
                      disp_base=lambda s, h, r: _gpct(_armor_pct_base(s, h, r)),
                      disp_starting=lambda s, h, r: _gpct(_armor_pct_l1(s, h, r))),
    "t_per_attack": _col("t_per_attack", "Time to hit", pol="lo",
                         fn_base=_t_per_attack_base,
                         fn_starting=_t_per_attack_l1),
}
_BASE_COL_BY_KEY.update(_EXTRA_COLS)

_LABEL_OVERRIDES = {
    "hpr": "HP/sec",
    "mpr": "MP/sec",
    "dmin": "Dmg\nmin",
    "dmax": "Dmg\nmax",
    "aspd": "Speed",
    "range": "Range",
    "proj": "Projectile Speed",
    "collision": "Collision Size",
    "ms": "Movespeed",
    "dvision": "Day",
    "nvision": "Night",
}
for _key, _label in _LABEL_OVERRIDES.items():
    _BASE_COL_BY_KEY[_key]["label"] = _label

CATEGORIES = [
    ("Basic", "basic", []),
    ("Essentials", "vitality", ["hp", "ehp_phys", "ehp_mag", "hpr", "mp", "mpr"]),
    ("Attributes", "attributes", ["str", "str_gain", "agi", "agi_gain",
                                   "int", "int_gain", "gper"]),
    ("Defense", "defense", ["armor", "armor_pct", "mr"]),
    ("Attack", "attack", ["dmg", "dmin", "dmax", "aspd", "t_per_attack",
                           "bat", "range", "proj"]),
    ("Vision", "vision", ["dvision", "nvision"]),
    ("Mobility", "mobility", ["ms", "turn", "collision", "bound"]),
]

for _cat_name, _cat_slug, _keys in CATEGORIES:
    for _key in _keys:
        _BASE_COL_BY_KEY[_key]["cat"] = _cat_slug

COLUMNS = [_BASE_COL_BY_KEY[_key]
           for _cat_name, _cat_slug, _keys in CATEGORIES
           for _key in _keys]
_CAT_FIRST_KEYS = {keys[0] for _cat_name, cat_slug, keys in CATEGORIES
                   if cat_slug != "basic" and keys}


# ---------- patch-note → field event index ----------
# The KV scrape (and d2vpkr's npc_heroes.txt) sometimes captures a balance
# change ONE PATCH LATE — Valve's server-side balance updates can ship in
# patch X but the public KV file only reflects them in X+1 (e.g. Treant
# 7.34d "Base Damage decreased by 2" → KV shows the new value at 7.34e).
# To restore accuracy we parse data/patchnotes_english.txt and shift each
# KV-detected change to the patch where the corresponding patch note
# announces it. The mapping is from `(hero_slug, field)` → ordered list of
# patches in which a base-stat note for that field appears.

_PATCH_KEY_RE = _re.compile(
    r'^\s*"DOTA_Patch_(?P<patch>\d+_\d+(?:_?[a-z])?)_(?P<rest>[a-zA-Z0-9_]+)"'
    r'\s+"(?P<text>.*?)"\s*$'
)

# Patch-note text → list of heroes.json field names it announces.
# Each pattern is a substring (case-insensitive, lowercase form). Order
# matters: the more specific phrases are checked before the generic ones.
_NOTE_FIELD_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # Regen first (catches "base health regen" before "base health")
    ("base health regen",        ("StatusHealthRegen",)),
    ("base hp regen",            ("StatusHealthRegen",)),
    ("base mana regen",          ("StatusManaRegen",)),
    ("base mp regen",            ("StatusManaRegen",)),
    # HP / mana
    ("base health",              ("StatusHealth",)),
    ("base hp",                  ("StatusHealth",)),
    ("base mana",                ("StatusMana",)),
    ("base mp",                  ("StatusMana",)),
    # Defense
    ("base armor",               ("ArmorPhysical",)),
    ("magic resistance",         ("MagicalResistance",)),
    ("magical resistance",       ("MagicalResistance",)),
    # Attributes
    ("strength gain",            ("AttributeStrengthGain",)),
    ("agility gain",             ("AttributeAgilityGain",)),
    ("intelligence gain",        ("AttributeIntelligenceGain",)),
    ("base strength",            ("AttributeBaseStrength",)),
    ("base agility",             ("AttributeBaseAgility",)),
    ("base intelligence",        ("AttributeBaseIntelligence",)),
    # Damage  (covers "base damage", "base attack damage")
    ("base damage",              ("AttackDamageMin", "AttackDamageMax")),
    ("base attack damage",       ("AttackDamageMin", "AttackDamageMax")),
    # Movement / attack mechanics
    ("base movement speed",      ("MovementSpeed",)),
    ("base move speed",          ("MovementSpeed",)),
    ("base attack time",         ("AttackRate",)),
    ("attack range",             ("AttackRange",)),
    ("base attack speed",        ("BaseAttackSpeed",)),
    # Vision
    ("day vision",               ("VisionDaytimeRange",)),
    ("night vision",             ("VisionNighttimeRange",)),
    # Turn rate / projectile / collision
    ("turn rate",                ("MovementTurnRate",)),
    ("projectile speed",         ("ProjectileSpeed",)),
    ("collision",                ("BoundsHullName",)),
    ("bound radius",             ("RingRadius",)),
)


def _patchnotes_path() -> Path:
    return _HERE / "data" / "patchnotes_english.txt"


def _norm_patch(raw: str) -> str:
    """'7_34d' → '7.34d', '7_40' → '7.40'."""
    parts = raw.split("_", 1)
    return f"{parts[0]}.{parts[1] if len(parts) > 1 else '0'}".replace("_", "")


def _hero_slug_aliases() -> dict[str, str]:
    """Patch-note hero slugs sometimes differ from npc_dota_hero_X.
    Build alias map: patch-note slug → canonical heroes.json key. Includes
    a handful of well-known renames the engine kept under legacy slugs."""
    aliases = {
        # engine-name → patch-note-slug shortcut (a few engine names start
        # with a different prefix in patch notes)
        "obsidian_destroyer": "obsidian_destroyer",
        "outworld_destroyer": "obsidian_destroyer",
        "zuus":               "zuus",
        "zeus":               "zuus",
        "wisp":               "wisp",
        "io":                 "wisp",
        "windrunner":         "windrunner",
        "windranger":         "windrunner",
        "skeleton_king":      "skeleton_king",
        "wraith_king":        "skeleton_king",
        "nevermore":          "nevermore",
        "shadow_fiend":       "nevermore",
        "necrolyte":          "necrolyte",
        "necrophos":          "necrolyte",
        "doom_bringer":       "doom_bringer",
        "doom":               "doom_bringer",
        "magnataur":          "magnataur",
        "magnus":             "magnataur",
        "rattletrap":         "rattletrap",
        "clockwerk":          "rattletrap",
        "shredder":           "shredder",
        "timbersaw":          "shredder",
        "furion":             "furion",
        "natures_prophet":    "furion",
    }
    return aliases


def _load_patchnote_events() -> dict[tuple[str, str], list[str]]:
    """Parse patchnotes_english.txt → {(hero_slug, field): [patch, ...]}.
    `hero_slug` is the bare slug WITHOUT the 'npc_dota_hero_' prefix; field
    matches the npc_heroes.txt KV key (StatusHealth, AttackDamageMin, …).
    Patch values are normalized to '7.34d' / '7.41' form so they line up
    with the rest of the build."""
    path = _patchnotes_path()
    if not path.exists():
        return {}
    # Map from patch-note slug → engine canonical slug (some keys we want
    # to translate, others stay as-is — pass-through default).
    alias = _hero_slug_aliases()
    # First pass: collect raw key→text rows.
    events: dict[tuple[str, str], list[str]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _PATCH_KEY_RE.match(line)
        if not m:
            continue
        patch = _norm_patch(m.group("patch"))
        rest = m.group("rest")
        text_low = m.group("text").lower()
        # rest = hero_slug + optional `_N` numeric suffix + optional ability
        # suffix. Hero-base-stat notes look like "treant" or "treant_2" — NO
        # second hero-name-prefixed component. Filter those: strip a trailing
        # numeric suffix, then make sure no underscore-separated `npc`-style
        # ability suffix follows.
        rest_no_num = _re.sub(r"_\d+$", "", rest)
        # Heuristic: a base-stat note has hero_slug == rest_no_num OR
        # rest_no_num is a known hero slug (no extra ability path).
        # Reject talent / ability / facet / innate keys (suffix carries
        # those words). They reference SKILL stats, not base stats.
        if any(tok in rest_no_num for tok in
               ("_talent", "_ability", "_facet", "_innate", "_aghs", "_shard",
                "_scepter")):
            continue
        # Map to canonical slug. If the rest_no_num contains underscores that
        # don't look like a single hero name, skip (likely an ability/facet
        # key we didn't filter above). Allow names with up to 3 underscores
        # like "outworld_destroyer", "obsidian_destroyer", "skeleton_king".
        if rest_no_num.count("_") > 3:
            continue
        slug = alias.get(rest_no_num, rest_no_num)
        # Match text against field-naming substrings.
        for needle, fields in _NOTE_FIELD_PATTERNS:
            if needle in text_low:
                for f in fields:
                    events.setdefault((slug, f), []).append(patch)
                break
    # Dedupe + sort each list by patch order.
    for key, ps in events.items():
        events[key] = sorted(set(ps), key=_patch_sort_key)
    return events


_PATCHNOTE_EVENTS: dict[tuple[str, str], list[str]] | None = None


def _patchnote_events() -> dict[tuple[str, str], list[str]]:
    global _PATCHNOTE_EVENTS
    if _PATCHNOTE_EVENTS is None:
        _PATCHNOTE_EVENTS = _load_patchnote_events()
    return _PATCHNOTE_EVENTS


def _shift_to_patchnote(hero: str, field: str, ver: str, used: set[str]) -> str:
    """If a patch note announces a `field` change for this hero at a patch
    <= ver that hasn't been consumed by a previous change, return that
    patch. Otherwise return `ver` unchanged.
    `used` tracks patches already assigned to earlier changes of this
    (hero, field) so we don't reassign one note to two KV changes."""
    slug = hero.replace("npc_dota_hero_", "")
    events = _patchnote_events().get((slug, field), [])
    if not events:
        return ver
    # Walk events newest→oldest; pick the latest event that is <= ver and
    # not used yet.
    for p in reversed(events):
        if _patch_sort_key(p) > _patch_sort_key(ver):
            continue
        if p in used:
            continue
        used.add(p)
        return p
    return ver


# ---------- history ----------

def _col_fields(col) -> tuple[str, ...]:
    """The KV field names whose patch-note events justify shifting this
    column's KV-detected changes. Returns () for synthetic/computed columns
    that don't correspond to a single KV field."""
    return _COL_TO_FIELDS.get(col["key"], ())


_COL_TO_FIELDS: dict[str, tuple[str, ...]] = {
    "hp": ("StatusHealth", "AttributeBaseStrength"),
    "ehp_phys": ("StatusHealth", "AttributeBaseStrength",
                 "ArmorPhysical", "AttributeBaseAgility"),
    "ehp_mag": ("StatusHealth", "AttributeBaseStrength",
                "MagicalResistance", "AttributeBaseIntelligence"),
    "mp": ("StatusMana", "AttributeBaseIntelligence"),
    "hpr": ("StatusHealthRegen", "AttributeBaseStrength"),
    "mpr": ("StatusManaRegen", "AttributeBaseIntelligence"),
    "str": ("AttributeBaseStrength",),
    "str_gain": ("AttributeStrengthGain",),
    "agi": ("AttributeBaseAgility",),
    "agi_gain": ("AttributeAgilityGain",),
    "int": ("AttributeBaseIntelligence",),
    "int_gain": ("AttributeIntelligenceGain",),
    "armor": ("ArmorPhysical", "AttributeBaseAgility"),
    "mr": ("MagicalResistance", "AttributeBaseIntelligence"),
    "dmg": ("AttackDamageMin", "AttackDamageMax",
            "AttributeBaseStrength", "AttributeBaseAgility",
            "AttributeBaseIntelligence"),
    "dmin": ("AttackDamageMin",),
    "dmax": ("AttackDamageMax",),
    "aspd": ("BaseAttackSpeed", "AttributeBaseAgility"),
    "ms": ("MovementSpeed",),
    "bat": ("AttackRate",),
    "dvision": ("VisionDaytimeRange",),
    "nvision": ("VisionNighttimeRange",),
    "range": ("AttackRange",),
    "proj": ("ProjectileSpeed",),
    "turn": ("MovementTurnRate",),
    "collision": ("BoundsHullName",),
    "bound": ("RingRadius",),
}


def _history_for(snaps, versions, dates, hero, col, raws, *, mode: str) -> str:
    """Per-patch change history for one hero × column in `mode` (base or
    starting). For `raw` columns the iteration restricts to versions whose
    heroes_raw.json carries data. When a patch note announces the
    corresponding field change one or more patches BEFORE the KV-detected
    change, the change is shifted to the patch note's patch (KV scrape is
    often one sub-patch late — see Treant 7.34d "Base Damage decreased by 2")."""
    if not col["hist"]:
        return ""
    fn_key = "fn_base" if mode == "base" else "fn_starting"
    disp_key = "disp_base" if mode == "base" else "disp_starting"
    value_fn = col[fn_key]
    display_fn = col[disp_key]
    fmt = col["fmt"]
    pol = col["pol"]
    iter_versions = ([v for v in versions if raws.get(v)] if col["raw"] else versions)
    if not iter_versions:
        return ""
    # Patch-note shift map. Per (hero, field): which patch-note patches
    # we've already consumed (so multiple KV changes don't collide on the
    # same note). The lookback window is intentionally narrow (≤1 sub-
    # patch) — the KV scrape is at most one sub-patch late in observed
    # cases; widening risks reattributing unrelated long-ago notes.
    fields = _col_fields(col)
    used_per_field: dict[str, set[str]] = {f: set() for f in fields}
    LOOKBACK_PATCHES = 1

    def _adjacent_prior_patches(ver: str, n: int) -> list[str]:
        """Up to `n` versions immediately preceding `ver` in the master
        patch list — i.e. {ver-1, ver-2, …, ver-n} restricted to existing
        sub-patches."""
        try:
            idx = versions.index(ver)
        except ValueError:
            return []
        return versions[max(0, idx - n): idx]

    def shifted_patch(kv_ver: str) -> str:
        """If any of this column's fields has an unused patch-note event
        in the patch immediately before `kv_ver` (within LOOKBACK_PATCHES),
        shift the change there. Otherwise return `kv_ver` unchanged."""
        if not fields:
            return kv_ver
        slug = hero.replace("npc_dota_hero_", "")
        window = set(_adjacent_prior_patches(kv_ver, LOOKBACK_PATCHES))
        if not window:
            return kv_ver
        # Per field, find any unused event whose patch lies in `window`.
        # Prefer the MOST RECENT one (closer to kv_ver) — this lines up
        # with how Valve typically lags KV updates by 1 patch.
        candidates: list[tuple[str, str]] = []   # (patch, field)
        for f in fields:
            events = _patchnote_events().get((slug, f), [])
            used = used_per_field[f]
            for p in reversed(events):
                if p in window and p not in used:
                    candidates.append((p, f))
                    break
        if not candidates:
            return kv_ver
        # Pick the LATEST candidate patch — the closest preceding sub-patch.
        candidates.sort(key=lambda pf: _patch_sort_key(pf[0]), reverse=True)
        chosen_patch, chosen_field = candidates[0]
        used_per_field[chosen_field].add(chosen_patch)
        return chosen_patch

    parts: list[tuple[str, str]] = []  # (patch, payload-without-patch-prefix)
    prev_val = None
    prev_disp = None
    seen = False
    first_ver = iter_versions[0]
    for ver in iter_versions:
        snap = snaps[ver]
        if hero not in snap:
            continue
        rw = raws.get(ver, {})
        # Innate attribute-conversion modifiers are patch-gated — tell the
        # value functions which patch this is.
        _set_ctx_version(ver)
        if not seen:
            seen = True
            if ver != first_ver:
                d0 = dates.get(ver, "")
                parts.append((ver, f"|{d0}|A|New hero"))
            prev_val = value_fn(snap, hero, rw)
            prev_disp = display_fn(snap, hero, rw) if display_fn else None
            continue
        v = value_fn(snap, hero, rw)
        d = display_fn(snap, hero, rw) if display_fn else None
        if abs(v - prev_val) > 1e-9 or (d is not None and d != prev_disp):
            shifted = shifted_patch(ver)
            shifted_date = dates.get(shifted, "")
            if display_fn:
                po = _re.sub(r"<[^>]+>", "", prev_disp)
                dn = _re.sub(r"<[^>]+>", "", d)
                parts.append((shifted,
                              f"|{shifted_date}|C|{po}|{dn}|{prev_val:g}|{v:g}|{pol}"))
            else:
                parts.append((shifted,
                              f"|{shifted_date}|V|{fmt(prev_val)}|{fmt(v)}|{pol}"))
            prev_val, prev_disp = v, d
    # Re-sort by shifted patch so the tooltip lists oldest→newest after shifts.
    parts.sort(key=lambda p: _patch_sort_key(p[0]))

    # Combined columns (Damage, Min/Max-derived ranges, etc.) may see min and
    # max KV fields land as separate snapshots even though the patch note is
    # one logical row. If both transitions shift to the same patch, collapse
    # them into one old→final entry instead of exposing scrape noise.
    merged: list[tuple[str, str]] = []
    for patch, payload in parts:
        if not merged or merged[-1][0] != patch:
            merged.append((patch, payload))
            continue
        prev_patch, prev_payload = merged[-1]
        a = prev_payload.split("|")
        b = payload.split("|")
        if len(a) >= 8 and len(b) >= 8 and a[2] == b[2] == "C" and a[7] == b[7]:
            merged[-1] = (
                prev_patch,
                f"|{a[1]}|C|{a[3]}|{b[4]}|{a[5]}|{b[6]}|{a[7]}",
            )
        elif len(a) >= 6 and len(b) >= 6 and a[2] == b[2] == "V" and a[5] == b[5]:
            merged[-1] = (
                prev_patch,
                f"|{a[1]}|V|{a[3]}|{b[4]}|{a[5]}",
            )
        else:
            merged.append((patch, payload))
    parts = merged
    return ";".join(p[0] + p[1] for p in parts)


def _attr_history(snaps, versions, dates, hero) -> str:
    parts = []
    prev = None
    for ver in versions:
        snap = snaps[ver]
        if hero not in snap:
            continue
        meta = _attr_of(snap, hero)
        if meta is None:
            continue
        if prev is not None and meta[1] != prev:
            parts.append(f"{ver}|{dates.get(ver, '')}|N|{prev}|{meta[1]}")
        prev = meta[1]
    return ";".join(parts)


# ---------- render ----------

def _mode_cls(col) -> str:
    return " hs-extra" if col["mode"] == "extra" else ""


def _sep_cls(col) -> str:
    return " col-sep" if col["key"] in _CAT_FIRST_KEYS else ""


def _label_html(label: str) -> str:
    if "\n" in label:
        main, sub = label.split("\n", 1)
        return f'{_esc(main)}<span class="th-sub">{_esc(sub)}</span>'
    return _esc(label)


def _attack_range_html(value: str, attack_type: str) -> str:
    tip = "Ranged" if attack_type == "ranged" else "Melee"
    return (
        f'<span class="atk-num">{_esc(value)}</span>'
        f'<span class="atk-badge atk-{attack_type}" title="{tip}">'
        f'<img src="icons/ui/atk_{attack_type}.png" alt="{tip}" '
        f'title="{tip}" loading="lazy"></span>'
    )


def _attack_type(version: str, hero: str, raw: dict) -> str:
    cap = _raw_field(raw, hero, "AttackCapabilities") or ""
    return "ranged" if "RANGED" in cap else "melee"


def _row_stats(hero: str, snap: dict, raw: dict) -> str:
    meta = _attr_of(snap, hero) or ("uni", "Universal", "universal.webp", 3)
    slug = hero.replace("npc_dota_hero_", "")
    data = {
        "slug": slug,
        "hasStatInnate": slug in {"axe", "beastmaster", "centaur", "dark_seer", "death_prophet", "dragon_knight", "drow_ranger", "keeper_of_the_light", "life_stealer", "luna", "medusa", "morphling", "ogre_magi", "razor", "sven", "techies", "ursa", "void_spirit"},
        "attr": meta[0],
        "str": _field(snap, hero, "AttributeBaseStrength"),
        "strGain": _field(snap, hero, "AttributeStrengthGain"),
        "agi": _field(snap, hero, "AttributeBaseAgility"),
        "agiGain": _field(snap, hero, "AttributeAgilityGain"),
        "int": _field(snap, hero, "AttributeBaseIntelligence"),
        "intGain": _field(snap, hero, "AttributeIntelligenceGain"),
        "hp": _field(snap, hero, "StatusHealth"),
        "hpr": _field(snap, hero, "StatusHealthRegen"),
        "mp": _mp_base_raw(snap, hero, raw),
        "mpr": _mpreg_base_raw(snap, hero, raw),
        "armor": _armor_base(snap, hero, raw),
        "mr": _mr_base(snap, hero, raw),
        "dmin": _dmg_min_base(snap, hero, raw),
        "dmax": _dmg_max_base(snap, hero, raw),
        "bas": _aspd_base(snap, hero, raw),
        "bat": _field(snap, hero, "AttackRate"),
        "range": _range_base(snap, hero, raw),
        "ms": _ms_base(snap, hero, raw),
        "dvision": _raw_num(raw, hero, "VisionDaytimeRange"),
        "nvision": _raw_num(raw, hero, "VisionNighttimeRange"),
        "proj": _raw_num(raw, hero, "ProjectileSpeed"),
        "turn": _raw_num(raw, hero, "MovementTurnRate"),
        "collision": _collision(snap, hero, raw),
        "bound": _raw_num(raw, hero, "RingRadius"),
    }
    return _esc(_json.dumps(data, separators=(",", ":")))


def render_html() -> str:
    versions = _versions()
    dates = _load_patch_dates()
    snaps = {v: _json.loads((STATS_DIR / v / "heroes.json").read_text(encoding="utf-8"))
             for v in versions}
    raws = {v: _load_raw_heroes(v) for v in versions}
    _inject_spirit_bear(snaps, raws)
    latest = versions[-1]
    cur = snaps[latest]
    raw = raws[latest]
    names = _load_display_names()

    heroes = sorted(
        (h for h in cur if h.startswith("npc_dota_hero_") and h not in _EXCLUDE),
        key=lambda h: _display_name(h, names).lower())

    nav = _site.render_top_nav('materials', _latest_href(),
                               patch_context=False, subtabs_active='heroes_stats',
                               subnav_in_header=False)
    subnav = _site.render_materials_subnav('heroes_stats')

    # ---- header ----
    head = [
        '<th class="mr-th hs-th hs-name sortable" data-col="name" data-cat="basic">'
        '<span class="th-label">Hero</span><span class="sort-ind"></span></th>',
        '<th class="mr-th hs-th hs-col-attr sortable" data-col="attr" data-cat="basic">'
        '<span class="th-label">Attr</span><span class="sort-ind"></span></th>',
    ]
    for col in COLUMNS:
        direction = "lower" if col["pol"] == "lo" else "higher"
        head.append(
            f'<th class="mr-th hs-th hs-col-{col["key"]}{_mode_cls(col)}'
            f'{_sep_cls(col)} sortable" '
            f'data-col="{col["key"]}" data-direction={direction} '
            f'data-cat="{col.get("cat", "other")}">'
            f'<span class="th-label">{_label_html(col["label"])}</span>'
            f'<span class="sort-ind"></span></th>')
    thead = "".join(head)
    cat_cells = ['<th class="cat-head cat-basic" data-cat="basic" colspan="2">Basic</th>']
    for cat_name, cat_slug, keys in CATEGORIES:
        if cat_slug == "basic":
            continue
        cat_cells.append(
            f'<th class="cat-head cat-{cat_slug}" data-cat="{cat_slug}" '
            f'colspan="{len(keys)}">{_esc(cat_name)}</th>')
    cat_row = "".join(cat_cells)

    # ---- body ----
    # Displayed cell values are the LATEST patch's — set the modifier context
    # accordingly (history loop overrides per-version inside _history_for).
    _set_ctx_version(latest)
    body = []
    for hero in heroes:
        slug = hero.replace("npc_dota_hero_", "")
        name = _display_name(hero, names)
        has_stat_innate = slug in {"axe", "beastmaster", "centaur", "dark_seer", "death_prophet", "dragon_knight", "drow_ranger", "keeper_of_the_light", "life_stealer", "luna", "medusa", "morphling", "ogre_magi", "razor", "sven", "techies", "ursa", "void_spirit"}
        attack_type = _attack_type(latest, hero, raw)
        icon = (f'<img class="mr-ico hs-ico" src="icons/heroes/{slug}.png" '
                f'alt="" loading="lazy">'
                if (_HERE / "icons" / "heroes" / f"{slug}.png").exists()
                else '<span class="mr-ico mr-ico-blank"></span>')
        cells = [
            f'<td class="mr-name hs-name" data-cat="basic" data-sort="{_esc(name)}">'
            f'{icon}<span class="mr-name-body">'
            f'<span class="mr-name-text">{_esc(name)}</span>'
            f'<img class="hs-innate-mini{" is-hidden" if not has_stat_innate else ""}" src="icons/misc/innate_icon.png" alt="" '
            f'loading="lazy" aria-hidden="true"></span></td>'
        ]
        meta = _attr_of(cur, hero) or ("uni", "Universal", "universal.webp", 3)
        ah = _attr_history(snaps, versions, dates, hero)
        attr_attrs = (f' class="hs-attr-cell has-history" data-hist="{_esc(ah)}"'
                      if ah else ' class="hs-attr-cell"')
        cells.append(
            f'<td{attr_attrs} data-cat="basic" data-sort="{meta[3]}">'
            f'<img class="hs-attr-ico" src="icons/{meta[2]}" alt="{meta[1]}" '
            f'title="{meta[1]}" width="20" height="20"></td>')
        for col in COLUMNS:
            cls = f"hs-col-{col['key']}{_mode_cls(col)}{_sep_cls(col)} has-history"
            # Displayed values use the LATEST patch's modifier context;
            # _history_for mutates the context, so reset it each cell.
            _set_ctx_version(latest)
            # Starting values are the DEFAULT (data-sort / data-hist).
            v_start = col["fn_starting"](cur, hero, raw)
            disp_start = (col["disp_starting"](cur, hero, raw)
                          if col["disp_starting"] else col["fmt"](v_start))
            hist_start = _history_for(snaps, versions, dates, hero, col, raws,
                                      mode="starting")
            _set_ctx_version(latest)
            # Base values — only stash on the cell when they differ.
            v_base = col["fn_base"](cur, hero, raw)
            disp_base = (col["disp_base"](cur, hero, raw)
                         if col["disp_base"] else col["fmt"](v_base))
            if col["key"] == "range":
                disp_start = _attack_range_html(disp_start, attack_type)
                disp_base = _attack_range_html(disp_base, attack_type)
            if col["key"] in ("hpr", "mpr") and abs(v_start) < 1e-9:
                cls += " regen-zero"
            hist_base = _history_for(snaps, versions, dates, hero, col, raws,
                                     mode="base")
            extra_attrs = (
                f' data-base-sort="{v_base}" '
                f'data-base-html="{_esc(disp_base)}" '
                f'data-base-hist="{_esc(hist_base)}"'
                f' data-start-sort="{v_start}" '
                f'data-start-html="{_esc(disp_start)}" '
                f'data-start-hist="{_esc(hist_start)}"'
            )
            hist_attr = f' data-hist="{_esc(hist_start)}"' if hist_start else ""
            net_attr = ' data-net=""' if hist_start else ""
            cls_final = (cls if hist_start else cls.replace(" has-history", ""))
            cells.append(
                f'<td class="{cls_final}" data-cat="{col.get("cat", "other")}" '
                f'data-col="{col["key"]}" data-sort="{v_start}"{net_attr}{hist_attr}'
                f'{extra_attrs}>{disp_start}</td>')
        body.append(
            f'<tr data-slug="{slug}" data-attack-type="{attack_type}" data-attr-type="{meta[0]}" '
            f'data-hs-stats="{_row_stats(hero, cur, raw)}">'
            f'{"".join(cells)}</tr>'
        )

    table = (
        # data-patch lets scripts.js gate per-patch innate formulas (e.g.
        # Medusa's Mana Shield damage_per_mana: 2.4 @ 7.37 → 2.2 @ 7.38 →
        # 2.0 @ 7.39e → 2+0.1·level @ 7.41a+; values from KV files).
        f'<table class="mr-table hs-table sortable-table" data-patch="{_CTX_VERSION[0]}">'
        f'<thead><tr class="cat-row">{cat_row}</tr>'
        f'<tr class="col-row">{thead}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody>'
        '</table>'
    )

    blurb = (
        '<p class="mr-blurb inbox-bar">Compare hero stats across three views. '
        '<em>Base</em> shows raw level-1 game-file values and ignores the level '
        'control; <em>Starting</em> shows practical values with attribute bonuses '
        'and supported innate conversions; the <em>+2 stats</em> toggle applies '
        'the automatic all-attributes level-ups from 15/16/17/19/20/21/22; '
        'the <em>Innates</em> toggle applies always-on innate-derived stat bonuses '
        'such as Void Spirit, Centaur, Morphling and Techies mana-pool regen; '
        '<em>Expanded</em> adds detailed combat, armor, projectile, mobility and '
        'size columns. Hover any stat for its full patch history since 7.08, then '
        'use search, sorting and heatmap to find outliers quickly.</p>\n'
    )
    toolbar = (
        '<div class="cal-toggle-bar mr-toolbar inbox-bar"><div class="toolbar-panel">'
        '<span class="view-group">'
        '<strong>View</strong>'
        '<select class="cal-mode-select" id="hs-view-mode">'
        '<option value="base">Base</option>'
        '<option value="starting" selected>Starting</option>'
        '<option value="expanded">Expanded</option>'
        '</select>'
        '</span>'
        '<span class="hs-attack-filter-group" aria-label="Attack type filter">'
        '<button type="button" class="hs-attack-filter" data-attack-filter="melee" '
        'aria-pressed="false" title="Show melee heroes">'
        '<span class="atk-badge" aria-hidden="true">'
        '<img src="icons/ui/atk_melee.png" alt=""></span><span>Melee</span></button>'
        '<button type="button" class="hs-attack-filter" data-attack-filter="ranged" '
        'aria-pressed="false" title="Show ranged heroes">'
        '<span class="atk-badge" aria-hidden="true">'
        '<img src="icons/ui/atk_ranged.png" alt=""></span><span>Ranged</span></button>'
        '</span>'
        + _attr_filter_buttons() +
        '<label class="hs-level-group">'
        '<span>Lvl</span>'
        '<input type="number" id="hs-level-input" min="1" max="30" value="1" '
        'inputmode="numeric" aria-label="Hero level">'
        '</label>'
        '<label class="ua-upgrades-toggle hs-plus2-toggle">'
        '<span class="ua-upgrades-label">+2 stats</span>'
        '<input type="checkbox" id="hs-plus2-toggle" class="ua-switch-input" checked>'
        '<span class="ua-switch" aria-hidden="true"></span>'
        '</label>'
        '<label class="ua-upgrades-toggle hs-innates-toggle">'
        '<span class="ua-upgrades-label">Innates</span>'
        '<input type="checkbox" id="hs-innates-toggle" class="ua-switch-input" checked>'
        '<span class="ua-switch" aria-hidden="true"></span>'
        '</label>'
        '<label class="ua-upgrades-toggle">'
        '<span class="ua-upgrades-label">Heatmap</span>'
        '<input type="checkbox" id="mr-heatmap-toggle" class="ua-switch-input">'
        '<span class="ua-switch" aria-hidden="true"></span>'
        '</label>'
        '<span class="search-box hd-search">'
        '<input type="text" id="mr-search" autocomplete="off" spellcheck="false" '
        'placeholder="Search heroes — axe, crystal, wisp…">'
        '</span>'
        '</div></div>\n'
    )

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<title>SIKLE | Hero Stats</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={ASSET_VERSION}">\n'
        '</head>\n<body>\n'
        f'{nav}\n'
        '<div class="container creeps-page">\n'
        # Vertical frozen-pane divider — drawn in the non-scrolling page so its
        # line keeps repainting during horizontal scroll (Chrome drops
        # box-shadow/border on sticky cells mid-scroll). scripts.js
        # `initHsStickyFrame` positions it at the right edge of the pinned Hero
        # column and shows it once scrolled sideways.
        '<div class="sticky-frame hs-sticky-frame"></div>\n'
        '<div class="creeps-scroll">\n'
        f'{subnav}'
        f'{blurb}'
        f'{toolbar}'
        f'{table}\n'
        '</div>\n'
        '</div>\n'
        f'<script src="src/scripts.js?v={ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n'
    )


def _latest_href() -> str:
    meta_path = _HERE / "data" / "site_meta.json"
    try:
        meta = _json.loads(meta_path.read_text(encoding="utf-8"))
        return meta.get("latest_patch_filename", "patches/7.41d.html")
    except Exception:
        return "patches/7.41d.html"


def main() -> int:
    html = render_html()
    out = _HERE / "heroes_stats.html"
    out.write_text(html, encoding="utf-8")
    n_rows = html.count("<tr data-slug=")
    print(f"  -> heroes_stats.html: {len(html):,} bytes ({n_rows} heroes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
