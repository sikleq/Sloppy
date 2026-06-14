"""Hero/item rosters, neutral/shop helpers, and build_rosters() that writes _dynamics.json."""

import os as _os
import json as _json
import re

from .state import _State
from .images import ITEM_SLUG, HERO_SLUG
from .meta import RELEASE_HISTORY, PATCHES


def _slugify(name):
    """Lowercase, strip apostrophes/punct, spaces → '-'. Used for entity DOM
    anchors and dynamics-manifest keys."""
    s = name.lower().replace("'", "").replace("’", "")
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


# ---------- Stats DB (needed for item presence scanning) ----------

def _load_stats_db():
    db_h, db_i, db_u = {}, {}, {}
    base = _os.path.join(_os.path.dirname(__file__), "..", "data", "stats")
    if not _os.path.isdir(base):
        return db_h, db_i, db_u
    for ver in _os.listdir(base):
        vdir = _os.path.join(base, ver)
        if not _os.path.isdir(vdir):
            continue
        for fname, target in (("heroes.json", db_h),
                              ("items.json",  db_i),
                              ("units.json",  db_u)):
            fp = _os.path.join(vdir, fname)
            if _os.path.exists(fp):
                with open(fp, encoding="utf-8") as f:
                    target[ver] = _json.load(f)
    return db_h, db_i, db_u


_STATS_H, _STATS_I, _STATS_U = _load_stats_db()


def _load_item_classes(version):
    """Parse data/stats/<version>/items.txt → (neutral, obsolete, present) sets."""
    path = _os.path.join(_os.path.dirname(__file__), "..", "data", "stats", version, "items.txt")
    present, neutral, obsolete = set(), set(), set()
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return neutral, obsolete, present
    cur = None
    name_re = re.compile(r'^\s*"(item_[a-z0-9_]+)"\s*$')
    for ln in lines:
        m = name_re.match(ln)
        if m:
            cur = m.group(1)
            present.add(cur)
            continue
        if not cur:
            continue
        if 'ItemIsNeutralActiveDrop' in ln and '"1"' in ln:
            neutral.add(cur)
        if 'IsObsolete' in ln and '"1"' in ln:
            obsolete.add(cur)
    return neutral, obsolete, present


# Chronological patch order (oldest → newest) for item lifespan windows.
_CHRON = [_r["version"] for _r in reversed(RELEASE_HISTORY)]
_CHRON_IDX = {_v: _i for _i, _v in enumerate(_CHRON)}


def _load_neutral_pool_current():
    """Set of game slugs currently in the neutral drop pool, from the datafeed's
    `neutral_item_tier` (>= 0)."""
    path = _os.path.join(_os.path.dirname(__file__), "..", "data", "itemlist.json")
    try:
        data = _json.load(open(path, encoding="utf-8"))
        items = data["result"]["data"]["itemabilities"]
    except (OSError, KeyError, ValueError) as exc:
        print(f"  ! itemlist.json unreadable ({exc}) — neutral pool empty")
        return set()
    return {it["name"] for it in items
            if it.get("neutral_item_tier", -1) >= 0
            and not it["name"].startswith("item_recipe_")}


def _load_neutral_tier_map():
    """{game slug → tier int} from data/itemlist.json."""
    path = _os.path.join(_os.path.dirname(__file__), "..", "data", "itemlist.json")
    try:
        data = _json.load(open(path, encoding="utf-8"))
        items = data["result"]["data"]["itemabilities"]
    except (OSError, KeyError, ValueError):
        return {}
    return {it["name"]: (it.get("neutral_item_tier") if it.get("neutral_item_tier", -1) >= 0
                          else 99)
            for it in items
            if not it["name"].startswith("item_recipe_")}


def _load_neutral_cycled_versions():
    """icon-slug -> patch version where a neutral was "cycled out" of the pool."""
    out = {}
    path = _os.path.join(_os.path.dirname(__file__), "..", "data", "patchnotes_english.txt")
    try:
        for ln in open(path, encoding="utf-8").read().splitlines():
            if "cycled out" in ln.lower():
                mk = re.search(r'_item_([a-z0-9_]+)"', ln)
                mv = re.search(r'DOTA_Patch_(\d+_\d+[a-z]?)_', ln)
                if mk and mv:
                    out[mk.group(1)] = mv.group(1).replace("_", ".")
    except OSError:
        pass
    return out


_NEUTRAL_REMOVED_MANUAL = {
    "ancient_guardian": "7.38", "arcane_ring": "7.38", "force_field": "7.38",
    "ascetic_cap": "7.38", "avianas_feather": "7.38", "ballista": "7.30",
    "book_of_shadows": "7.38", "broom_handle": "7.38", "bullwhip": "7.38",
    "clumsy_net": "7.28", "craggy_coat": "7.38", "doubloon": "7.38",
    "dragon_scale": "7.38", "elixer": "7.23d", "elven_tunic": "7.38",
    "enchanted_quiver": "7.38", "faded_broach": "7.38", "paintball": "7.32",
    "force_boots": "7.38", "fusion_rune": "7.24", "giants_ring": "7.38",
    "grove_bow": "7.38", "havoc_hammer": "7.38", "illusionsts_cape": "7.30",
    "imp_claw": "7.30", "ironwood_tree": "7.30", "keen_optic": "7.32",
    "lance_of_pursuit": "7.38", "light_collector": "7.38", "mirror_shield": "7.38",
    "ocean_heart": "7.32", "phoenix_ash": "7.24", "princes_knife": "7.28",
    "quicksilver_amulet": "7.32", "repair_kit": "7.28", "royal_jelly": "7.38",
    "safety_bubble": "7.38", "seer_stone": "7.38", "spy_gadget": "7.38",
    "the_leveller": "7.32", "third_eye": "7.23c", "tome_of_aghanim": "7.23a",
    "trickster_cloak": "7.38", "trident": "7.28", "unwavering_condition": "7.38",
    "vambrace": "7.38", "vindicators_axe": "7.38", "witless_shako": "7.28",
    "woodland_striders": "7.28",
}

_SHOP_CATEGORY_ORDER = [
    ("consumables", "Consumables"), ("attributes", "Attributes"),
    ("weapons_armor", "Equipment"), ("misc", "Miscellaneous"),
    ("secretshop", "Secret Shop"),
    ("basics", "Accessories"), ("support", "Support"), ("magics", "Magical"),
    ("defense", "Armor"), ("weapons", "Weapons"), ("artifacts", "Armaments"),
]
_SHOP_CATEGORY_OTHER = "Other"

_PHANTOM_ITEMS = {
    "item_greater_mango", "item_greater_faerie_fire",
    "item_bottomless_chalice", "item_horizon", "item_mechanical_arm",
    "item_enhancement_curious", "item_enhancement_dominant",
    "item_enhancement_fierce", "item_enhancement_restorative",
    "item_enhancement_thick",
}

_FREE_ALLOW = {
    "item_aegis", "item_cheese", "item_refresher_shard", "item_roshans_banner",
    "item_famango", "item_great_famango", "item_greater_famango",
    "item_royale_with_cheese", "item_ward_observer",
    "item_ultimate_scepter_2",
}
_ITEM_BLOCK = {"item_furion_gold_bag", "item_caster_rapier", "item_pocket_roshan"}

_OBSOLETE_REMOVED = {
    "item_necronomicon": "7.29",
    "item_hood_of_defiance": "7.33",
    "item_flicker": "7.33",
    "item_nether_shawl": "7.33",
    "item_wraith_pact": "7.33",
    "item_tome_of_knowledge": "7.33",
    "item_quarterstaff": "7.35",
    "item_stout_shield": "7.23",
}


def _load_shop_categories():
    path = _os.path.join(_os.path.dirname(__file__), "..", "data", "shops.txt")
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return {}
    want = dict(_SHOP_CATEGORY_ORDER)
    sec_re = re.compile(r'^\s*"([a-z0-9_]+)"\s*(?://.*)?$')
    item_re = re.compile(r'^\s*"item"\s*"(item_[a-z0-9_]+)"')
    per_cat = {}
    sections_with_items = set()
    cur = None
    for ln in lines:
        mi = item_re.match(ln)
        if mi:
            if cur:
                sections_with_items.add(cur)
            if cur in want:
                per_cat.setdefault(cur, []).append(mi.group(1))
            continue
        ms = sec_re.match(ln)
        if ms:
            cur = ms.group(1)

    def _ignored(s):
        return s == "dota_shops" or s.startswith("sideshop") or "pregame" in s
    unknown = sorted(s for s in sections_with_items
                     if s not in want and not _ignored(s))
    if unknown:
        print(f"  ! shops.txt has UNMAPPED shop section(s): {unknown} — items there "
              f"fall to 'Other'. Add them to _SHOP_CATEGORY_ORDER in patch/rosters.py.")
    out = {}
    for key, _disp in _SHOP_CATEGORY_ORDER:
        for slug in per_cat.get(key, []):
            out.setdefault(slug, want[key])
    return out


def _item_category(gslug, cls):
    if cls != "regular":
        return None
    return _SHOP_CATEGORIES.get(gslug, _SHOP_CATEGORY_OTHER)


def _item_class_and_current(rec, neutral_slugs, obsolete_slugs, present_slugs,
                             neutral_pool_current):
    icon = rec.get("icon", rec["name"].lower().replace(" ", "_").replace("'", ""))
    gslug = "item_" + icon
    if rec.get("kind") == "enchant":
        cls = "enchant"
    elif (gslug in neutral_slugs or rec.get("neutral_section")
          or gslug in neutral_pool_current):
        cls = "neutral"
    else:
        cls = "regular"
    if cls == "neutral":
        current = gslug in neutral_pool_current
    else:
        current = (gslug in present_slugs) and (gslug not in obsolete_slugs)
    return cls, current


def _added_version(icon):
    """Oldest patch whose items.json contains this item."""
    gslug = "item_" + icon
    for _v in _CHRON:
        if gslug in _STATS_I.get(_v, {}):
            return _v
    return None


def _presence_window(icon):
    """(first_present_version, last_present_version_if_gone_else_None)."""
    gslug = "item_" + icon
    pres = [_v for _v in _CHRON if gslug in _STATS_I.get(_v, {})]
    if not pres:
        return None, None
    removed = None if pres[-1] == _CHRON[-1] else pres[-1]
    return pres[0], removed


def _item_default_sort_key(_d, class_order, cat_index, shop_cat_order):
    _cls_rank = class_order.get(_d.get("class"), 99)
    _cat_rank = cat_index.get(_d.get("category"), len(cat_index)) \
        if _d.get("class") == "regular" else 0
    _tier_rank = _d.get("tier") if _d.get("class") == "neutral" else 0
    if _tier_rank is None:
        _tier_rank = 99
    return (_cls_rank, _cat_rank, _tier_rank, _d["name"].lower())


def _load_full_game_items(latest_stats_ver, neutral_slugs, obsolete_slugs, present_slugs,
                          neutral_pool_current, neutral_tier_by_slug, neutral_cycled):
    """[(game_slug, icon, display_name, cls, is_removed), ...] for every real item."""
    txt_path = _os.path.join(_os.path.dirname(__file__), "..", "data", "stats",
                             latest_stats_ver, "items.txt")
    purch, cost = {}, {}
    cur = None
    name_re = re.compile(r'^\s*"(item_[a-z0-9_]+)"\s*$')
    cost_re = re.compile(r'^\s*"ItemCost"\s*"(\d+)"')
    try:
        for ln in open(txt_path, encoding="utf-8").read().splitlines():
            m = name_re.match(ln)
            if m:
                cur = m.group(1)
                purch[cur] = True
                continue
            if not cur:
                continue
            if 'ItemPurchasable' in ln and '"0"' in ln:
                purch[cur] = False
            mc = cost_re.match(ln)
            if mc:
                cost[cur] = int(mc.group(1))
    except OSError:
        return []
    names = {}
    try:
        _il = _json.load(open(_os.path.join(_os.path.dirname(__file__),
                              "..", "data", "itemlist.json"), encoding="utf-8"))
        for _it in _il["result"]["data"]["itemabilities"]:
            names[_it["name"]] = _it.get("name_english_loc")
    except (OSError, KeyError, ValueError):
        pass
    icons_dir = _os.path.join(_os.path.dirname(__file__), "..", "icons", "items")
    try:
        icon_files = set(_os.listdir(icons_dir))
    except OSError:
        icon_files = set()
    variant_re = re.compile(r'(_\d+|_roshan|_broken)$')
    out = []
    for gslug in present_slugs:
        if gslug.startswith("item_recipe_") or gslug in _PHANTOM_ITEMS:
            continue
        icon = gslug[len("item_"):]
        if icon + ".png" not in icon_files:
            continue
        if gslug in _ITEM_BLOCK or gslug.startswith("item_river_painter"):
            continue
        if (variant_re.search(gslug) or gslug == "item_tango_single") \
                and gslug not in _FREE_ALLOW and gslug not in neutral_pool_current:
            continue
        is_obsolete = gslug in obsolete_slugs
        added, gone = _presence_window(icon)
        if gslug.startswith("item_enhancement_"):
            cls, current, removed = "enchant", True, gone
        elif gslug in neutral_slugs or gslug in neutral_pool_current:
            cls = "neutral"
            current = gslug in neutral_pool_current
            removed = None if current else (neutral_cycled.get(icon) or gone)
        else:
            cls = "regular"
            if not (gslug in _FREE_ALLOW or is_obsolete
                    or (purch.get(gslug, True) and (cost.get(gslug) or 0) > 0)):
                continue
            current = not is_obsolete
            removed = (_OBSOLETE_REMOVED.get(gslug) or gone) if is_obsolete else gone
        nm = names.get(gslug) or icon.replace("_", " ").title()
        cost_v = _STATS_I.get(latest_stats_ver, {}).get(gslug, {}).get("ItemCost", 0)
        price = None if cls in ("neutral", "enchant") else (
            cost_v if (cost_v and cost_v > 0) else None)
        out.append({"_gslug": gslug, "name": nm, "icon": icon, "class": cls,
                    "current": current, "added": added, "removed": removed,
                    "category": _item_category(gslug, cls),
                    "tier": neutral_tier_by_slug.get(gslug) if cls == "neutral" else None,
                    "price": price})
    return out


# Module-level pre-computations (needed by build_rosters)
_SHOP_CATEGORIES = _load_shop_categories()


def build_rosters():
    """Build hero/item rosters and write _dynamics.json. Called after all patches build."""
    from datetime import date as _date

    neutral_pool_current = _load_neutral_pool_current()
    neutral_tier_by_slug = _load_neutral_tier_map()
    neutral_cycled = _load_neutral_cycled_versions()
    neutral_cycled.update(_NEUTRAL_REMOVED_MANUAL)

    # Determine latest stats version with items.txt
    latest_stats_ver = next(
        (_r["version"] for _r in RELEASE_HISTORY
         if _os.path.exists(_os.path.join(_os.path.dirname(__file__), "..",
                                          "data", "stats", _r["version"], "items.txt"))),
        RELEASE_HISTORY[0]["version"])
    neutral_slugs, obsolete_slugs, present_slugs = _load_item_classes(latest_stats_ver)

    # Hero roster
    hero_roster = [{"name": _n, "icon": _s, "key": "hero|" + _slugify(_n)}
                   for _n, _s in sorted(HERO_SLUG.items())]
    hero_roster.append({"name": "Spirit Bear", "icon": "spirit_bear",
                        "key": "creep-hero|spirit-bear"})
    hero_roster.sort(key=lambda h: h["name"].lower())

    # Item roster from dynamics
    item_roster = []
    for _k, _r in _State.dynamics.items():
        if _r.get("kind") not in ("item", "enchant"):
            continue
        _cls, _current_gf = _item_class_and_current(
            _r, neutral_slugs, obsolete_slugs, present_slugs, neutral_pool_current)
        _icon = _r.get("icon", _r["name"].lower().replace(" ", "_").replace("'", ""))
        _removed = _r.get("removed_in")
        if _removed:
            _touch = [_CHRON_IDX[_p] for _p in _r.get("patches", {}) if _p in _CHRON_IDX]
            if _touch and max(_touch) > _CHRON_IDX.get(_removed, -1):
                _removed = None
        if _cls == "neutral":
            if _current_gf:
                _removed = None
            elif _removed is None:
                _removed = neutral_cycled.get(_icon)
        _current = _current_gf and (_removed is None)
        _cost = _STATS_I.get(latest_stats_ver, {}).get("item_" + _icon, {}).get("ItemCost", 0)
        item_roster.append({
            "name": _r["name"], "icon": _icon, "key": _k,
            "class": _cls, "current": _current,
            "added": _added_version(_icon), "removed": _removed,
            "category": _item_category("item_" + _icon, _cls),
            "tier": neutral_tier_by_slug.get("item_" + _icon) if _cls == "neutral" else None,
            "price": _cost if (_cost and _cost > 0) else None})

    # Add every real game item NOT touched in any tracked patch
    _touched_gslugs = {"item_" + _d["icon"] for _d in item_roster}
    for _e in _load_full_game_items(latest_stats_ver, neutral_slugs, obsolete_slugs,
                                    present_slugs, neutral_pool_current,
                                    neutral_tier_by_slug, neutral_cycled):
        if _e.pop("_gslug") in _touched_gslugs:
            continue
        _e["key"] = "item|" + _e["icon"]
        item_roster.append(_e)

    # Sort item roster
    _CLASS_ORDER = {"regular": 0, "neutral": 1, "enchant": 2}
    _CAT_INDEX = {_disp: _i for _i, (_, _disp) in enumerate(_SHOP_CATEGORY_ORDER)}
    _CAT_INDEX[_SHOP_CATEGORY_OTHER] = len(_SHOP_CATEGORY_ORDER)
    item_roster.sort(key=lambda d: _item_default_sort_key(d, _CLASS_ORDER, _CAT_INDEX, _SHOP_CATEGORY_ORDER))

    # Ordered list of categories present
    _present_cats = {_d.get("category") for _d in item_roster if _d.get("category")}
    _item_cat_list = [_disp for _k, _disp in _SHOP_CATEGORY_ORDER if _disp in _present_cats]
    if _SHOP_CATEGORY_OTHER in _present_cats:
        _item_cat_list.append(_SHOP_CATEGORY_OTHER)

    # Build dyn_patches list
    _have_html = {p["version"]: p["filename"].split("/")[-1] for p in PATCHES}
    dyn_patches = [{"version": r["version"],
                    "filename": _have_html.get(r["version"]),
                    "date": r["date"]} for r in RELEASE_HISTORY]

    dyn_payload = {"patches": dyn_patches, "entities": _State.dynamics,
                   "heroes": hero_roster, "items": item_roster,
                   "item_categories": _item_cat_list}
    with open('_dynamics.json', 'w', encoding='utf-8') as _f:
        _json.dump(dyn_payload, _f, separators=(',', ':'))
    print(f"  → _dynamics.json: {len(_State.dynamics)} entities × {len(dyn_patches)} patches in RELEASE_HISTORY")
    _cls_counts = {}
    for _d in item_roster:
        _cls_counts[_d["class"]] = _cls_counts.get(_d["class"], 0) + 1
    _n_removed = sum(1 for _d in item_roster if not _d["current"])
    print(f"     items_dyn roster: {len(item_roster)} ({_cls_counts}); "
          f"{_n_removed} not current (class source: {latest_stats_ver}/items.txt)")

    # Write ability-icon URL list for the validator
    with open('_ability_icons.txt', 'w', encoding='utf-8') as _f:
        for _u in sorted(_State.ability_icons):
            _f.write(_u + '\n')
    print(f"  → _ability_icons.txt: {len(_State.ability_icons)} unique URLs")

    # Write site_meta.json
    import json as _json2
    _site_meta = {
        "latest_patch_filename": PATCHES[0]["filename"] if PATCHES else "patches/7.41c.html",
        "latest_patch_version": PATCHES[0]["version"] if PATCHES else "",
        "asset_version": __import__('site_common').compute_asset_version(),
        "patch_dates": {r["version"]: r["date"] for r in RELEASE_HISTORY},
    }
    _os.makedirs("data", exist_ok=True)
    with open(_os.path.join("data", "site_meta.json"), "w", encoding="utf-8") as _f:
        _json2.dump(_site_meta, _f, ensure_ascii=False, indent=2)
    print(f"  -> data/site_meta.json: latest={_site_meta['latest_patch_filename']}")
