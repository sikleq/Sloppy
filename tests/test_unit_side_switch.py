"""Owner 2026-11-22: Unit Changes gets a Side switch next to Removed — Radiant / Dire show that side's home-jungle
creeps (7.42), neither pressed (the default) shows both."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "builders"))
import entity_changes as ec  # noqa: E402


def test_home_jungle_creeps_carry_their_side_and_others_none():
    card = ec._unit_card({"kind": "unit", "name": "Kobold", "slug": "kobold", "icon": "../icons/units/npc_dota_neutral_kobold.png",
                          "_npc": "npc_dota_neutral_kobold"})
    assert 'data-side="radiant"' in card
    card = ec._unit_card({"kind": "unit", "name": "Mud Golem", "slug": "mud-golem", "_npc": "npc_dota_neutral_mud_golem",
                          "icon": "../icons/units/npc_dota_neutral_mud_golem.png"})
    assert 'data-side="dire"' in card
    card = ec._unit_card({"kind": "unit", "name": "Melee Creep", "slug": "melee-creep", "_npc": "npc_dota_creep_goodguys_melee",
                          "icon": "../icons/units/npc_dota_creep_goodguys_melee.png"})
    assert "data-side" not in card                         # lane creeps are on both sides


def test_the_switch_starts_neutral():
    assert ec.SIDE_SWITCH.count('aria-pressed="false"') == 2 and 'aria-pressed="true"' not in ec.SIDE_SWITCH
    assert 'data-ec-side="radiant"' in ec.SIDE_SWITCH and 'data-ec-side="dire"' in ec.SIDE_SWITCH
    js = (ROOT / "src" / "js" / "changes-index.js").read_text(encoding="utf-8")
    assert "[data-ec-side]" in js


def test_both_sides_have_creeps():
    sides = list(ec._HOME_SIDE.values())
    assert sides.count("radiant") >= 10 and sides.count("dire") >= 10


def test_aghanim_card_icons_do_not_grow_on_hover():
    # owner 2026-11-22 (7.42 Blade Fury): the lead icon of an Aghanim's card stays put on hover
    css = (ROOT / "src" / "css" / "patch-new-entity-rows.css").read_text(encoding="utf-8")
    assert ".aghs-change .ac-sub:hover > .ac-sub-ico { transform: none;" in css
