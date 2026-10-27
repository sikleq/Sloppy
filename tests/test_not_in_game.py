"""Abilities that sit in the game files but were never in the game stay off the site (owner 2026-10-27: 7.39 showed
Ice Age and Naga Siren's Critical Strike as "Grants this ability"). data/rules/abilities_not_in_game.json is built by
tools/build_ability_registry.py from every patch's own build: no Ability slot or facet ever named them."""
import json
import os

from patch import aghs_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "data", "rules", "abilities_not_in_game.json")


def _reg():
    with open(REG, encoding="utf-8") as f:
        return json.load(f)["abilities"]


def test_the_known_dust_is_in_the_registry():
    reg = _reg()
    assert reg["ancient_apparition_ice_age"]["kind"] == "never"
    assert reg["arc_warden_tempest_recall"]["kind"] == "never"
    assert reg["naga_siren_crit"]["kind"] == "old"            # Naga's ability before 7.08, a leftover since
    assert reg["invoker_emp_ad"]["kind"] == "draft"           # Ability Draft copy, not Invoker's E.M.P.


def test_abilities_granted_in_code_are_not_dust():
    from patch.known_exceptions import KNOWN_UNSLOTTED_REAL
    reg = _reg()
    assert KNOWN_UNSLOTTED_REAL and all(reg.get(s, {}).get("kind") in (None, "code") for s in KNOWN_UNSLOTTED_REAL)
    assert {"tinker_shrink_ray", "treant_super_bloom"} <= set(KNOWN_UNSLOTTED_REAL)
    assert "tinker_shrink_ray" not in aghs_text.not_in_game()


def test_an_aghanims_card_never_names_dust(monkeypatch):
    blocks = {"ancient_apparition_ice_blast": {"HasShardUpgrade": "1"},
              "ancient_apparition_ice_age": {"IsGrantedByShard": "1"},
              "naga_siren_crit": {"IsGrantedByScepter": "1"}, "naga_siren_ensnare": {"HasScepterUpgrade": "1"}}
    monkeypatch.setattr(aghs_text, "_blocks", lambda v: blocks)
    assert aghs_text.holders("ancient_apparition", "shard", "7.39") == ["ancient_apparition_ice_blast"]
    assert aghs_text.holders("naga_siren", "scepter", "7.39") == ["naga_siren_ensnare"]


def test_every_row_has_its_evidence():
    for slug, r in _reg().items():
        assert r["kind"] in ("never", "old", "helper", "draft", "code"), slug
        assert r["first"] and r["last"] and r["hero"] and slug.startswith(r["hero"] + "_"), slug
        if r["kind"] == "old":
            assert r["liquipedia"], slug
