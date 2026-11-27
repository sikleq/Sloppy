"""Hero / item summons on Unit Stats (owner 2026-11-26: "добавить других summon units (не wards)"): the game's
numbers from data/rules/summon_units.json, only sure entries, no growth with Upgrade, off by default (Type)."""
import json
import re
from pathlib import Path

import pytest

from builders import creeps_summons as cs

ROOT = Path(__file__).resolve().parents[1]


def test_only_sure_entries():
    keep = cs.entries()
    assert keep and all(e["sure"] and not e.get("not_in_game") for e in keep)
    keys = {e["key"] for e in keep}
    assert {"warlock_golem_1", "lycan_wolf_4", "brewmaster_earth_4"} <= keys
    # confirmed by server.dll 6997 (2026-11-27): Aghanim golem, Book of the Dead (level 3 only), Raptor
    assert {"warlock_golem_scepter_1", "book_of_the_dead_warrior_3", "book_of_the_dead_archer_3",
            "beastmaster_raptor_4"} <= keys
    # numbers that depend on the hero (Enigma's HP, hero level) and units the game does not summon
    assert not keys & {"enigma_eidolon_1", "chen_zealot", "warlock_minor_imp", "clinkz_skeleton_walk",
                       "book_of_the_dead_warrior_1", "enigma_eidolon_5", "warlock_major_imp", "brewmaster_void_1"}


def test_confirmed_numbers_from_server_dll():
    by = {e["key"]: e for e in cs.entries()}
    g = by["warlock_golem_scepter_1"]
    assert (g["dmg_min"], g["dmg_max"], g["armor"], g["hp"]) == (75, 85, 8, 1500)     # golem_dmg_scepter -+5
    w = by["book_of_the_dead_warrior_3"]
    assert w["hp"] == 1600 and (w["dmg_min"], w["dmg_max"]) == (122.5, 148.75)         # +100% HP, +75% base damage
    assert cs.display_name(w) == "Demonic Warrior (Book of the Dead)"
    assert by["beastmaster_raptor_1"]["dmg_min"] is None


def test_ability_numbers_override_the_unit_kv():
    golem = next(e for e in cs.entries() if e["key"] == "warlock_golem_1")
    kv = cs.kv_overrides(golem)
    assert kv["StatusHealth"] == "1500" and kv["ArmorPhysical"] == "8"     # Chaotic Offering, not the KV's 0 armor
    assert kv["AttackCapabilities"] == "DOTA_UNIT_CAP_MELEE_ATTACK"


def test_names_and_icons():
    names = {e["key"]: cs.display_name(e) for e in cs.entries()}
    assert names["lycan_wolf_1"] == "Lycan Wolf 1"
    assert names["furion_treant_2"] == "Treant 2 (Nature's Prophet)"
    assert names["undying_zombie_torso"] == "Zombie Torso (Undying)"
    for e in cs.entries():
        assert (ROOT / cs.icon(e)).exists(), e["key"]


def test_summons_show_their_abilities_with_icons_and_the_hero_link():
    # owner 2026-11-26: "способность у суммонов отсутствуют"
    assert cs.ability_name("warlock_golem_flaming_fists") == "Flaming Fists"
    got = cs.abilities({"Ability1": "generic_hidden", "Ability2": "warlock_golem_flaming_fists",
                        "Ability3": "special_bonus_unique_x", "Ability4": "lycan_summon_wolves_hightail"})
    assert got == [("warlock_golem_flaming_fists", "Flaming Fists"), ("lycan_summon_wolves_hightail", "Hightail"),
                   ("", "")]
    html = (ROOT / "dist" / "units_stats.html").read_text(encoding="utf-8")
    i = html.find('id="unit-summon_warlock_golem_1"')
    row = html[i:html.find("</tr>", i)]
    assert 'href="heroes/warlock.html"' in row and "icons/abilities/warlock_golem_flaming_fists.png" in row
    for slug in re.findall(r'class="abil-ico" src="icons/abilities/([a-z0-9_]+)\.png"', row):
        assert (ROOT / "icons" / "abilities" / f"{slug}.png").exists(), slug


def test_empty_file_is_an_error(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        cs.entries(str(p))
    p.write_text(json.dumps([{"key": "x", "npc": "n", "sure": False, "hp": 1}]), encoding="utf-8")
    with pytest.raises(ValueError):
        cs.entries(str(p))


def test_summon_rows_on_the_page_do_not_grow_and_start_hidden():
    html = (ROOT / "dist" / "units_stats.html").read_text(encoding="utf-8")
    assert 'id="unit-summon_warlock_golem_1" data-group="summon"' in html
    assert 'id="unit-summon_warlock_golem_1" data-group="summon" data-attack-type="melee" data-upg="{}"' in html
    js = (ROOT / "src" / "js" / "creeps-upgrade.js").read_text(encoding="utf-8")
    assert "tr.dataset.group !== 'lane' && tr.dataset.upg === undefined" in js
    from builders.creeps_common import unit_group, UNIT_GROUPS_OFF
    assert unit_group("summon_lycan_wolf_1") == "summon" and "summon" in UNIT_GROUPS_OFF


def test_summons_do_not_grow_in_the_timeline():
    # 2026-11-27: Timeline added the neutral upgrade (+3 damage, +30 HP a step) to hero summons
    from builders import creeps as cr
    d = {'createhero': 'summon_warlock_golem_1', 'hp': '1500', 'dmg_avg': '100', 'armor': '8', 'as': '100',
         'gold_min': '100', 'gold_max': '100'}
    for stat in ('hp', 'dmg', 'armor', 'as', 'gold'):
        assert cr.timeline_value(d, stat, 8) == cr.timeline_value(d, stat, 0), stat
