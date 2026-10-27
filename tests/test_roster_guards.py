"""Hand-kept rosters / texts that the game files cannot fill by themselves — each guarded so a new patch that
adds or changes an entity the list does not know fails CI with a clear message (instead of a page silently
missing it). Values that CAN be read are read (creep self-auras, creep names fall back to the game's)."""
import json
from functools import lru_cache
from pathlib import Path

from patch.meta import latest_stats_version
from tools.slim_from_kv import load_kv

ROOT = Path(__file__).resolve().parent.parent
STATS = ROOT / "data" / "stats"
LATEST = latest_stats_version()


@lru_cache(maxsize=None)
def _units(version):
    return load_kv(STATS / version / "npc_units.txt").get("DOTAUnits", {})


@lru_cache(maxsize=None)
def _abilities(version):
    """Every ability block of a patch: npc_abilities.txt + the per-hero files (Ogre Frostmage's Frost Armor
    and the Dark Troll Summoner's spells live in hero files)."""
    from patch.kv import hero_ability_blocks
    out = dict(load_kv(STATS / version / "npc_abilities.txt").get("DOTAAbilities", {}))
    for p in sorted((STATS / version / "heroes").glob("npc_dota_hero_*.txt")):
        for name, block in hero_ability_blocks(load_kv(p)).items():
            out.setdefault(name, block)
    return out


# ---------------------------------------------------------------- Neutral Stats (builders/creeps.py)

def test_every_neutral_in_the_game_files_has_a_table_row():
    from builders import creeps as c
    known = set(c.CREEP_NAME_TO_NPC.values()) | c.NOT_CAMP_UNITS
    unknown = sorted(k for k, b in _units(LATEST).items()
                     if k.startswith("npc_dota_neutral_") and isinstance(b, dict)
                     and str(b.get("IsNeutralUnitType", "")) == "1" and k not in known)
    assert not unknown, (f"{LATEST} npc_units.txt has neutral creeps the Neutral Stats table does not know: "
                         f"{unknown} — add a data/creeps_raw.csv row + CREEP_NAME_TO_NPC / CREEP_CAMP "
                         f"(or NOT_CAMP_UNITS if it spawns in no camp)")


def test_every_table_creep_still_exists_and_has_a_camp_and_name():
    from builders import creeps as c
    units = _units(LATEST)
    gone = sorted(n for n in set(c.CREEP_NAME_TO_NPC.values()) if n not in units)
    assert not gone, f"CREEP_NAME_TO_NPC lists units the {LATEST} game files no longer have: {gone}"
    no_camp = sorted(k for k in c.CREEP_NAME_TO_NPC if k not in c.CREEP_CAMP)
    assert not no_camp, f"creeps without a camp in CREEP_CAMP: {no_camp}"
    for npc in c.CREEP_NAME_TO_NPC.values():
        assert c.CREEP_DISPLAY_NAMES.get(npc) or c.game_unit_name(npc), npc


def test_csv_rows_are_all_mapped():
    import csv
    from builders import creeps as c
    with open(ROOT / "data" / "creeps_raw.csv", encoding="utf-8") as f:
        rows = list(csv.reader(f))[1:]
    tokens = {r[3].strip() for r in rows if len(r) > 3 and r[3].strip()} - c.HIDDEN_CREATEHERO
    assert sorted(tokens - set(c.CREEP_NAME_TO_NPC)) == []


def test_a_new_neutral_gets_the_games_name_not_a_made_up_one():
    from builders import creeps as c
    assert c.game_unit_name("npc_dota_neutral_jungle_stalker") == "Ancient Stalker"   # not "Jungle Stalker"


def test_self_auras_are_read_from_the_game_files():
    from builders import creeps as c
    for short, auras in c.AURA_SELF.items():
        for stat, spec in auras.items():
            assert c.aura_self_value(*spec) is not None, \
                f"{short} {stat}: {spec[1]}.{spec[2]} is not in the {LATEST} npc_abilities.json"
    assert c.aura_self_value("%", "granite_golem_hp_aura", "bonus_hp") == ("*", 1.16)
    assert c.aura_self_value("+", "satyr_hellcaller_unholy_aura", "health_regen") == ("+", 3.0)


# ---------------------------------------------------------------- Neutral Abilities (creeps_abilities.py)

def _table_abilities(version):
    from builders import creeps as c
    from builders.creeps_common import ABILITY_SKIP
    out = set()
    for npc in set(c.CREEP_NAME_TO_NPC.values()):
        u = _units(version).get(npc) or {}
        for i in range(1, 9):
            s = str(u.get(f"Ability{i}") or "").strip()
            if s and s not in ABILITY_SKIP:
                out.add(s)
    return out


def test_hand_written_ability_cells_still_match_the_game():
    from builders import creeps_abilities as ca
    checked = ca.ABIL_MANUAL_CHECKED
    if checked == LATEST:
        return
    old, new = _abilities(checked), _abilities(LATEST)
    problems = []
    for s in sorted(_table_abilities(LATEST) | set(ca.ABIL_MANUAL)):
        if s not in old and s in new:
            problems.append(f"{s}: new neutral ability")
        elif s in old and s not in new:
            problems.append(f"{s}: gone from the game files")
        elif s in old and old[s] != new[s]:
            keys = sorted(k for k in set(old[s]) | set(new[s]) if old[s].get(k) != new[s].get(k))
            av_o, av_n = old[s].get("AbilityValues") or {}, new[s].get("AbilityValues") or {}
            keys += sorted(f"AbilityValues.{k}" for k in set(av_o) | set(av_n) if av_o.get(k) != av_n.get(k))
            problems.append(f"{s}: {', '.join(k for k in keys if k != 'AbilityValues')}")
    assert not problems, (f"neutral-creep abilities changed between {checked} and {LATEST}: re-check their "
                          f"hand-written cells (ABIL_MANUAL / TYPE_MANUAL / DMGTYPE_MANUAL / DISPEL_MANUAL / "
                          f"THROUGH_BKB in builders/creeps_abilities.py), then set ABIL_MANUAL_CHECKED = "
                          f"'{LATEST}':\n" + "\n".join(problems))


def test_autocast_list_matches_the_game():
    from builders.creeps_common import AUTOCAST_ABILITIES
    blocks = _abilities(LATEST)
    auto = {s for s in _table_abilities(LATEST)
            if "AUTOCAST" in str((blocks.get(s) or {}).get("AbilityBehavior", ""))}
    # the list may hold more (Ogre Frostmage's Frost Armor autocasts in game, its KV block does not say so)
    missing = sorted(auto - set(AUTOCAST_ABILITIES))
    assert not missing, f"autocast neutral abilities missing from creeps_common.AUTOCAST_ABILITIES: {missing}"


# ---------------------------------------------------------------- Mana Items (builders/mana_items.py)

def test_manual_pre_733_history_ends_at_the_first_value_the_game_files_show():
    import builders.mana_items as m
    from patch.game_constants import _vkey
    deep =set(m.INT_FIELDS) | set(m.ALL_STATS_FIELDS) | set(m.MAX_MANA_FIELDS) | set(m.PASSIVE_REGEN_FIELDS)
    first = None
    for patch, _date in m._patches_with_items():
        data = json.loads((STATS / patch / "items.json").read_text(encoding="utf-8"))
        if any(isinstance(f, dict) and any(k in f for k in deep) for f in data.values()):
            first = (patch, data)
            break
    assert first, "no items.json with mana fields"
    patch, data = first
    for (slug, kind), entries in m._MANUAL_METRIC_HISTORY.items():
        assert _vkey(entries[-1][1]) < _vkey(patch), \
            f"{slug}: manual history row {entries[-1][1]} is covered by the game files (from {patch}) — drop it"
        value = m._flat_metric(data.get(slug) or {}, kind, slug, patch)
        assert round(value, 3) == round(entries[-1][4], 3), \
            (f"{slug} {kind}: the manual pre-{patch} history ends at {entries[-1][4]}, "
             f"but {patch} items.json says {value}")
    # Wind Waker's 7.33 regen cut comes from the game files, once (it used to be listed twice)
    ww = [e for e in m.load_metric_history("regen").get("item_wind_waker", []) if e[1] == "7.33"]
    assert len(ww) == 1, ww


# ---------------------------------------------------------------- AoE Increase (builders/aoe_increase.py)

def test_aoe_items_are_found_in_the_game_files():
    import builders.aoe_increase as aoe
    items = aoe._resolve_items(LATEST)
    assert [i[0] for i in items] == ["chasm_stone", "shivas_guard", "gungir", "dezun_bloodrite"]
    for key, _label, icon, _kind, _amt in items:
        assert (ROOT / "icons" / "items" / icon).exists(), f"AoE item {key} has no icons/items/{icon}"


_FAKE_ITEMS = """"DOTAAbilities"
{
 "item_chasm_stone" { "AbilityValues" { "aoe_bonus" "50" } }
 "item_new_orb" { "AbilityValues" { "bonus_aoe" { "value" "30" } } }
 "item_old_orb" { "IsObsolete" "1" "AbilityValues" { "bonus_aoe" "99" } }
 "item_lost_neutral" { "ItemIsNeutralActiveDrop" "1" "AbilityValues" { "aoe_pct" "10" } }
}
"""


def test_a_new_aoe_item_appears_by_itself(tmp_path, monkeypatch):
    import builders.aoe_increase as aoe
    (tmp_path / "9.99").mkdir()
    (tmp_path / "9.99" / "items.txt").write_text(_FAKE_ITEMS, encoding="utf-8")
    monkeypatch.setattr(aoe, "STATS_DIR", tmp_path)
    got = aoe._resolve_items("9.99")
    assert [(k, kind, amt) for k, _l, _i, kind, amt in got] == [("new_orb", "flat", 30), ("chasm_stone", "flat", 50)]


# ---------------------------------------------------------------- Hero Lab enchantments (builders/hero_lab.py)

@lru_cache(maxsize=None)
def _items(version):
    return load_kv(STATS / version / "items.txt").get("DOTAAbilities", {})


def _levels(block):
    """How many levels an enchantment has: the longest "a b c" value list of its AbilityValues."""
    out = 1
    for v in (block.get("AbilityValues") or {}).values():
        raw = v.get("value") if isinstance(v, dict) else v
        if raw is not None:
            out = max(out, len(str(raw).split()))
    return out


def test_every_enchantment_has_tiers_and_attributes():
    import builders.hero_lab as hl
    from patch.rosters import _PHANTOM_ITEMS
    current = {k: b for k, b in _items(LATEST).items()
               if k.startswith("item_enhancement_") and k not in _PHANTOM_ITEMS and isinstance(b, dict)}
    for table in ("_ENCHANT_TIER_LABELS", "_ENCHANT_ATTRS"):
        known = getattr(hl, table)
        new = sorted(set(current) - set(known))
        assert not new, f"{LATEST} items.txt has enchantments hero_lab.{table} does not know: {new}"
        gone = sorted(set(known) - set(current))
        assert not gone, f"hero_lab.{table} lists enchantments {LATEST} no longer has: {gone}"
    wrong = [f"{k}: {len(hl._ENCHANT_TIER_LABELS[k][2])} tiers listed, {_levels(b)} levels in the game"
             for k, b in current.items() if len(hl._ENCHANT_TIER_LABELS[k][2]) != _levels(b)]
    assert not wrong, f"enchantment tiers out of step with items.txt (fix _ENCHANT_TIER_LABELS): {wrong}"


# ---------------------------------------------------------------- Item rosters (patch/rosters.py)

def _neutral_pool():
    data = json.loads((ROOT / "data" / "itemlist.json").read_text(encoding="utf-8"))
    return {i["name"] for i in data["result"]["data"]["itemabilities"] if i.get("neutral_item_tier", -1) >= 0}


def test_hand_kept_item_lists_still_hold():
    from patch import rosters as r
    items, pool = _items(LATEST), _neutral_pool()
    shops = (ROOT / "data" / "shops.txt").read_text(encoding="utf-8")
    real = sorted(p for p in r._PHANTOM_ITEMS if p in pool or f'"{p}"' in shops)
    assert not real, f"_PHANTOM_ITEMS are in the shop / neutral pool now (no longer phantoms): {real}"
    back = sorted(k for k in r._OBSOLETE_REMOVED if k in items and str(items[k].get("IsObsolete", "")) != "1")
    assert not back, f"_OBSOLETE_REMOVED items are not IsObsolete in {LATEST} any more: {back}"
    pooled = sorted(k for k in r._NEUTRAL_REMOVED_MANUAL if f"item_{k}" in pool)
    assert not pooled, f"_NEUTRAL_REMOVED_MANUAL neutrals are back in the pool: {pooled}"


def test_every_shop_section_is_mapped():
    import re
    from patch import rosters as r
    want = {k for k, _ in r._SHOP_CATEGORY_ORDER}
    cur, with_items = None, set()
    for ln in (ROOT / "data" / "shops.txt").read_text(encoding="utf-8").splitlines():
        if re.match(r'^\s*"item"\s*"item_', ln):
            with_items.add(cur)
            continue
        m = re.match(r'^\s*"([a-z0-9_]+)"\s*(?://.*)?$', ln)
        if m:
            cur = m.group(1)
    unknown = sorted(s for s in with_items - want
                     if s and s != "dota_shops" and not s.startswith("sideshop") and "pregame" not in s)
    assert not unknown, f"shops.txt has shop sections _SHOP_CATEGORY_ORDER does not map: {unknown}"


# ---------------------------------------------------------------- Unit / Item Changes pages (entity_changes.py)

def test_every_shop_category_has_a_panel():
    from builders import entity_changes as ec
    from patch import rosters as r
    shown = {c for _p, cats in ec._SHOP_PANELS for c in cats}
    missing = sorted(({d for _k, d in r._SHOP_CATEGORY_ORDER} | {r._SHOP_CATEGORY_OTHER}) - shown)
    assert not missing, f"item categories with no panel in entity_changes._SHOP_PANELS: {missing}"


def test_neutral_tier_times_follow_the_patch_notes():
    """The unlock times live in the game's neutral_items.txt we do not fetch; Valve announces a change in the
    patch notes ("Tier 1 availability changed from 5:00 to 0:00") — the latest such line must agree."""
    import re
    from builders import entity_changes as ec
    from patch.game_constants import _vkey
    latest = {}
    for ln in (ROOT / "data" / "patchnotes_english.txt").read_text(encoding="utf-8").splitlines():
        mv = re.search(r'"DOTA_Patch_(\d+)_(\d+)([a-z]?)_', ln)
        m = (re.search(r"Tier (\d) (?:Neutral Items? )?availability changed from \S+ to (\d+):(\d\d)", ln)
             or re.search(r"Tier (\d) (?:Neutral )?[Ii]tems now drop at (\d+) minutes()", ln))
        if mv and m:
            ver = f"{mv.group(1)}.{mv.group(2)}{mv.group(3)}"
            tier, minutes = int(m.group(1)), int(m.group(2))
            if tier not in latest or _vkey(ver) >= _vkey(latest[tier][0]):
                latest[tier] = (ver, minutes)
    assert latest, "no neutral tier timing line found in patchnotes_english.txt"
    for tier, (ver, minutes) in latest.items():
        assert ec._TIER_TIME[tier] == f"{minutes}:00+", \
            f"{ver} patch notes: tier {tier} at {minutes}:00, entity_changes._TIER_TIME says {ec._TIER_TIME[tier]}"


def _unit_exists(basename):
    units = _units(LATEST)
    alias = "npc_dota_" + basename.replace("_unit", "")         # brewmaster_fire_unit -> npc_dota_brewmaster_fire*
    return any(k.startswith(basename) or k.startswith(alias) for k in units)


def test_unit_lists_follow_the_game_files():
    from builders import creeps as c
    from builders import entity_changes as ec
    gone = [b for b, _n in ec._SUMMON_UNITS + ec._LANE_UNITS if not _unit_exists(b)]
    assert not gone, f"summon / lane units the {LATEST} npc_units.txt no longer has: {gone} (move to _REMOVED_UNITS)"
    # (the files keep removed units — Necronomicon's are still in npc_units.txt — so _REMOVED_UNITS is not
    # checked against them; their item is: it must stay obsolete)
    assert str(_items(LATEST).get("item_necronomicon", {}).get("IsObsolete", "")) == "1", \
        "Necronomicon is not obsolete any more — its units in _REMOVED_UNITS are back in the game"
    no_parent = [b for b, _n in ec._SUMMON_UNITS if b not in ec._SUMMON_PARENT]
    assert not no_parent, f"summons without a parent page in _SUMMON_PARENT: {no_parent}"
    known = (set(c.CREEP_DISPLAY_NAMES) | {b for b, _n in ec._SUMMON_UNITS + ec._LANE_UNITS}
             | {b for b, _n, _c in ec._REMOVED_UNITS} | set(ec._UNIT_BUCKET) | ec._UNIT_NOT_LISTED)
    icons = sorted(p.stem for p in (ROOT / "icons" / "units").glob("*.png"))
    unlisted = [i for i in icons if i not in known]
    assert not unlisted, f"unit portraits no Changes list knows (add to _SUMMON_UNITS / _LANE_UNITS / ...): {unlisted}"


def test_structures_still_exist():
    from builders import entity_changes as ec
    units = _units(LATEST)
    kinds = {"tower": "npc_dota_goodguys_tower1", "barracks": "npc_dota_goodguys_melee_rax", "tormentor": "npc_dota_miniboss"}
    for _label, entries in ec._STRUCTURE_DEF:
        for icon, _name in entries:
            prefix = next(v for k, v in kinds.items() if icon.startswith(k))
            assert any(u.startswith(prefix) for u in units), f"{icon}: no {prefix}* unit in {LATEST}"
            assert (ROOT / "icons" / "structures" / f"{icon}.png").exists(), icon
