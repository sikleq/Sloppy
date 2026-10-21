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
    from builders.site_common import hero_ability_blocks
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
