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

import site_common as _site
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


def _latest_href() -> str:
    try:
        meta = _json.loads((_HERE / "data" / "site_meta.json").read_text(encoding="utf-8"))
        return meta.get("latest_patch_filename", "patches/7.41d.html")
    except Exception:
        return "patches/7.41d.html"


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

    def walk(node):
        if not isinstance(node, dict):
            return
        for k, v in node.items():
            if isinstance(v, dict):
                walk(v)
            elif k not in out:
                out[k] = v

    walk(d.get("AbilityValues", {}))
    walk(d.get("AbilitySpecial", {}))
    return out


def _first(fields: dict, *keys: str) -> float:
    for k in keys:
        if k in fields:
            return _num(fields[k])
    return 0.0


def _sum(fields: dict, *keys: str) -> float:
    return sum(_num(fields.get(k, 0)) for k in keys)


def _item_bonus(fields: dict) -> dict[str, float]:
    all_stats = _first(fields, "bonus_all_stats", "bonus_stats", "all_stats")
    str_bonus = all_stats + _sum(fields, "bonus_strength", "bonus_str")
    agi_bonus = all_stats + _sum(fields, "bonus_agility", "bonus_agi")
    int_bonus = all_stats + _sum(fields, "bonus_intellect", "bonus_int", "bonus_intelligence")
    return {
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


def _load_items(version: str) -> list[dict]:
    names = _load_item_names()
    meta_by_id = _load_item_meta()
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
        out.append({
            "id": item,
            "slug": slug,
            "name": label,
            "icon": icon,
            "cost": int(cost),
            "class": cls,
            "category": meta.get("category"),
            "tier": meta.get("tier"),
            "bonus": bonus,
        })
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
<script src="src/scripts.js?v={av}"></script>
</body>
</html>
"""


def main() -> int:
    html = render_html()
    (_HERE / "hero_lab.html").write_text(html, encoding="utf-8")
    print(f"  -> hero_lab.html: {len(html):,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
