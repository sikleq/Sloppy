"""Hero / item summons on Unit Stats (owner 2026-11-26: "добавить других summon units (не wards)"): the game's
numbers from data/rules/summon_units.json, only sure entries, no growth with Upgrade, off by default (Type)."""
import json
import re
from pathlib import Path

import pytest

from builders import creeps_summons as cs

ROOT = Path(__file__).resolve().parents[1]


def test_only_sure_entries_and_no_aghanim_guesses():
    keep = cs.entries()
    assert keep and all(e["sure"] for e in keep)
    assert not any("scepter" in e["key"] for e in keep)
    keys = {e["key"] for e in keep}
    assert {"warlock_golem_1", "lycan_wolf_4", "brewmaster_earth_4"} <= keys
    assert not keys & {"enigma_eidolon_1", "chen_zealot", "beastmaster_raptor_1"}      # numbers worked out in code


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
