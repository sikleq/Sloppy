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

_LOC_RE = _re.compile(r'"([^"]+)"\s+"((?:[^"\\]|\\.)*)"')


def _load_item_tooltips() -> dict[str, dict]:
    """Parse abilities_english.txt for item tooltip data (desc, lore, stat labels)."""
    path = _HERE / "data" / "abilities_english.txt"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    entries: dict[str, str] = {}
    for m in _LOC_RE.finditer(text):
        k, v = m.group(1), m.group(2).replace('\\"', '"')
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
        if "_note" in rest or "_searchalias" in rest or ":f" in rest or "_bound" in rest:
            continue
        attr_keys.append((rest, val))
    # Build a set of all known item ids from the first pass
    all_item_ids = set(out.keys())
    # Also discover enchantment items from name keys
    name_prefix = "dota_tooltip_ability_"
    for key in entries:
        if key.startswith(name_prefix + "item_enhancement_") and "_" not in key[len(name_prefix) + len("item_enhancement_"):].lstrip("abcdefghijklmnopqrstuvwxyz0123456789_"):
            rest = key[len(name_prefix):]
            if not rest.endswith("_description") and not rest.endswith("_lore") and "_note" not in rest and ":f" not in rest:
                all_item_ids.add(rest)
    # Match item names exactly from the Tooltip_Ability entries (the name-only keys)
    for key, val in entries.items():
        if key.startswith(name_prefix + "item_") and val and "_" not in key[len(name_prefix):].replace("item_", "", 1).replace("enhancement_", "").replace("_", "X", 0):
            pass
    # Simple approach: for each attr key, find the longest known item_id prefix
    for rest, val in attr_keys:
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
            out.setdefault(best, {}).setdefault("attribs", []).append(val)
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


def _item_bonus(fields: dict) -> dict[str, float]:
    # "+N All Attributes" is a single line in the in-game tooltip — don't split
    # it into Strength/Agility/Intellect rows. Per-attribute fields stay
    # separate so items can mix (e.g. +6 All + extra Strength).
    all_stats = _first(fields, "bonus_all_stats", "bonus_stats", "all_stats")
    str_bonus = _sum(fields, "bonus_strength", "bonus_str")
    agi_bonus = _sum(fields, "bonus_agility", "bonus_agi")
    int_bonus = _sum(fields, "bonus_intellect", "bonus_int", "bonus_intelligence")
    return {
        "all": all_stats,
        "str": str_bonus,
        "agi": agi_bonus,
        "int": int_bonus,
        "hp": _sum(fields, "bonus_health", "bonus_hp", "bonus_max_health", "health_bonus"),
        "mp": _sum(fields, "bonus_mana", "max_mana", "bonus_max_mana"),
        "hpr": _sum(fields, "bonus_health_regen", "health_regen", "bonus_hp_regen", "hp_regen", "bonus_regen"),
        "mpr": _sum(fields, "bonus_mana_regen", "mana_regen", "bonus_mp_regen", "mp_regen", "aura_mana_regen"),
        "armor": _sum(fields, "bonus_armor", "aura_bonus_armor"),
        "mr": _sum(fields, "bonus_magic_resistance", "bonus_magical_armor", "bonus_spell_resist", "magic_resistance"),
        "evasion": _sum(fields, "bonus_evasion", "evasion"),
        "damage": _sum(fields, "bonus_damage"),
        "damageMelee": _sum(fields, "bonus_damage_melee"),
        "damageRanged": _sum(fields, "bonus_damage_range", "bonus_damage_ranged"),
        "aspd": _sum(fields, "bonus_attack_speed", "attack_speed", "bonus_as"),
        "ms": _sum(fields, "bonus_movement_speed", "bonus_move_speed", "movement_speed"),
        "msMelee": _sum(fields, "bonus_movement_speed_melee", "bonus_move_speed_melee"),
        "msRanged": _sum(fields, "bonus_movement_speed_ranged", "bonus_move_speed_ranged"),
        "range": _sum(fields, "bonus_attack_range", "attack_range_bonus", "base_attack_range"),
    }


def _resolve_pct(desc: str, fields: dict) -> str:
    """Replace %var% placeholders in tooltip descriptions with actual values.

    Substituted values are wrapped in <span class="GameplayVariable"> so the
    tooltip CSS can highlight them brighter than the body text — matching the
    in-game Dota tooltip, where resolved numbers stand out from the prose."""
    def _repl(m):
        key = m.group(1)
        if key.startswith("d") and key[1:] in fields:
            key = key[1:]
        val = fields.get(key)
        if val is None:
            return m.group(0)
        s = str(val).split(" ")[0]
        try:
            n = float(s)
            s = str(int(n)) if n == int(n) else s
        except (ValueError, TypeError):
            pass
        return f'<span class="GameplayVariable">{s}</span>'
    return _re.sub(r"%([a-zA-Z_][a-zA-Z0-9_]*)%", _repl, desc)


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
        bonus = _item_bonus(fields)
        cls = meta.get("class", "regular")
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
            "consumable": str(fields.get("ItemQuality", "")).lower() == "consumable",
            "bonus": bonus,
        }
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
            tip["desc"] = resolved
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
        raw_attribs = tt.get("attribs", [])
        if raw_attribs:
            _STAT_NAMES = {
                "move_speed": "Movement Speed", "movespeed": "Movement Speed",
                "attack_lifesteal": "Lifesteal", "lifesteal": "Lifesteal",
                "spell_lifesteal": "Spell Lifesteal",
                "bonus_night_vision": "Night Vision",
                "debuff_amp": "Debuff Duration",
                "spell_amp": "Spell Amplification",
                "int": "Intelligence", "str": "Strength", "agi": "Agility",
                "mana_regen": "Mana Regeneration", "move_speed": "Movement Speed",
            }
            resolved: list[str] = []
            for a in raw_attribs:
                m2 = _re.search(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", a)
                if m2:
                    vname = m2.group(1)
                    # Try exact key, then without underscores, then common alternates
                    val = fields.get(vname)
                    if val is None:
                        val = fields.get(vname.replace("_", ""))
                    if val is None and vname == "lifesteal":
                        val = fields.get("attack_lifesteal")
                    label = _STAT_NAMES.get(vname, vname.replace("_", " ").title())
                    prefix = a[:m2.start()].replace("%", "").strip()
                    if val is not None:
                        s = str(val).split(" ")[0]  # first level value
                        try:
                            n = float(s)
                            ns = str(int(n)) if n == int(n) else s
                        except (ValueError, TypeError):
                            ns = s
                        pct = "%" if "%" in a[:m2.start()] else ""
                        resolved.append(f"{prefix}{ns}{pct} {label}")
                    else:
                        resolved.append(a.replace("$" + vname, label).replace("%", "").strip())
                elif not a.endswith(":") and "DURATION" not in a.upper():
                    cleaned = a.replace("%", "").strip()
                    if cleaned:
                        # Try to find value for known plain-text attribs
                        _PLAIN_MAP = {
                            "+Night Vision": ("bonus_night_vision", "Night Vision", ""),
                            "+Spell Amplification": ("spell_amp", "Spell Amplification", "%"),
                        }
                        pm = _PLAIN_MAP.get(cleaned)
                        if pm:
                            fval = fields.get(pm[0])
                            if fval is not None:
                                s = str(fval).split(" ")[0]
                                try:
                                    n = float(s)
                                    ns = str(int(n)) if n == int(n) else s
                                except (ValueError, TypeError):
                                    ns = s
                                cleaned = f"+{ns}{pm[2]} {pm[1]}"
                        resolved.append(cleaned)
            if resolved:
                tip["attribs"] = resolved
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
            rec["tip"] = tip
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


def _load_heroes(version: str) -> list[dict]:
    snap = _json.loads((STATS_DIR / version / "heroes.json").read_text(encoding="utf-8"))
    raw = _load_raw_heroes(version)
    snaps = {version: snap}
    raws = {version: raw}
    _inject_spirit_bear(snaps, raws)
    snap, raw = snaps[version], raws[version]
    names = _load_display_names()
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
        out.append({
            "id": slug,
            "name": name,
            "icon": f"icons/heroes/{icon_slug}.png",
            "attackType": _attack_type(version, hero, raw),
            "stats": stats,
        })
    return out


def render_html() -> str:
    version = _versions()[-1]
    heroes = _load_heroes(version)
    items = _load_items(version)
    data = _json.dumps({"patch": version, "heroes": heroes, "items": items}, separators=(",", ":"))
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
<script id="hero-lab-data" type="application/json">{data_script}</script>
<div class="hero-lab" data-patch="{_esc(version)}">
  <div class="hl-panel" data-side="a"></div>
  <div class="hl-diff-panel">
    <div class="hl-diff-head">
      <strong id="hl-diff-title">none vs none</strong>
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
