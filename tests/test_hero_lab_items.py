"""Regression coverage for Hero Lab item stats and tooltip data."""
from __future__ import annotations

import re

import pytest

from builders.hero_lab import _load_items, _versions


@pytest.fixture(scope="module")
def items():
    versions = _versions()
    if not versions:
        pytest.skip("no patch data available")
    result = {item["id"]: item for item in _load_items(versions[-1])}
    if not result:
        pytest.skip("no items loaded (data files missing)")
    return result


@pytest.mark.parametrize(
    ("item_id", "stat"),
    [
        ("item_tango", "hpr"),
        ("item_flask", "hpr"),
        ("item_clarity", "mpr"),
    ],
)
def test_consumable_restoration_is_not_a_passive_stat(items, item_id, stat):
    assert items[item_id]["bonus"][stat] == 0


def test_passive_and_aura_mana_regen_remain_available(items):
    assert items["item_ring_of_basilius"]["bonus"]["mpr"] == pytest.approx(1.25)
    assert items["item_arcane_boots"]["bonus"]["mpr"] == pytest.approx(1.25)


def test_bauble_enchant_scale_comes_from_kv(items):
    """scripts.js multiplies tier-5 enchantments by these values instead of
    hardcoding them — 7.41e moved the recraft bonus from 40% to 35%."""
    scale = items["item_enchanters_bauble"]["enchantScale"]
    assert scale["base"] == pytest.approx(0.10)
    assert scale["growth"] == pytest.approx(0.35)


def test_neutral_headline_bonuses_are_extracted(items):
    bonuses = items["item_harmonizer"]["tip"]["neutralBonuses"]
    assert bonuses == [
        {"value": "7", "label": "Mana Cost Reduction", "pct": True},
        {"value": "6", "label": "Spell Amplification", "pct": True},
    ]


def test_neutral_ability_values_do_not_become_hero_stats(items):
    gunpowder = items["item_gunpowder_gauntlets"]
    assert gunpowder["bonus"]["damage"] == 0
    assert all(value == 0 for value in gunpowder["bonus"].values())


def test_zero_value_attribute_rows_are_omitted(items):
    shivas = items["item_shivas_guard"]["tip"]["attribs"]
    assert not any(re.match(r"^[+\-]?0(?:\.0+)?%?\s", row) for row in shivas)


def test_core_attribute_placeholders_are_resolved(items):
    assert "+6 Agility" in items["item_boots_of_elves"]["tip"]["attribs"]
    assert "+5 Strength" in items["item_bracer"]["tip"]["attribs"]
    assert "+2 All Attributes" in items["item_circlet"]["tip"]["attribs"]


def test_no_raw_dollar_placeholders_reach_tooltips(items):
    unresolved = [
        (item["id"], row)
        for item in items.values()
        for row in item.get("tip", {}).get("attribs", [])
        if "$" in row
    ]
    assert unresolved == []


def test_enchantment_attribute_values_are_resolved(items):
    crude = items["item_enhancement_crude"]["tip"]["attribs"]
    assert "+9% Health Restoration" in crude
    assert "-6% Base Attack Time" in crude

    evolved = items["item_enhancement_evolved"]["tip"]["attribs"]
    assert "+40 Primary Attribute" in evolved

    # 7.41e replaced Feverish's mana-cost penalty with a max-mana penalty.
    # Valve encodes it as a bare `max_mana` KV value — it must render as a
    # percentage penalty, not as a flat mana bonus.
    feverish = items["item_enhancement_feverish"]["tip"]["attribs"]
    assert "-20% Max Mana" in feverish
    assert items["item_enhancement_feverish"]["bonus"]["mpPct"] == -20
    assert items["item_enhancement_feverish"]["bonus"]["mp"] == 0

    audacious = items["item_enhancement_audacious"]["tip"]["attribs"]
    assert "+10% Incoming Damage" in audacious


def test_item_notes_are_preserved(items):
    notes = items["item_tango"]["tip"]["notes"]
    assert any("Ironwood Tree" in note for note in notes)


def test_noise_attribute_rows_are_omitted(items):
    bottle_rows = items["item_bottle"]["tip"].get("attribs", [])
    tango_rows = items["item_tango"]["tip"].get("attribs", [])
    assert not any(row.startswith("Rune:") for row in bottle_rows)
    assert "Tango (Shared)" not in tango_rows


def test_divine_rapier_uses_base_bonus_plus_toggle_modes(items):
    rapier = items["item_rapier"]
    assert rapier["bonus"]["damage"] == pytest.approx(100)
    assert rapier["bonus"]["spellAmp"] == 0
    assert rapier["modes"]["default"] == "damage"
    assert rapier["modes"]["damage"]["damage"] == pytest.approx(250)
    assert rapier["modes"]["spell"]["spellAmp"] == pytest.approx(25)
    assert rapier["tip"]["attribs"] == ["+100 Damage"]


def test_dagon_is_collapsed_into_one_item_with_level_modes(items):
    assert "item_dagon" in items
    assert "item_dagon_2" not in items
    assert "item_dagon_3" not in items
    dagon = items["item_dagon"]
    assert dagon["modes"]["default"] == "lvl1"
    assert dagon["modes"]["lvl1"]["costOverride"] == 3000
    assert dagon["modes"]["lvl5"]["costOverride"] == 7400
    assert dagon["modes"]["lvl1"]["all"] == pytest.approx(6)
    assert dagon["modes"]["lvl5"]["all"] == pytest.approx(10)
    assert dagon["modes"]["lvl1"]["dagonDamage"] == pytest.approx(400)
    assert dagon["modes"]["lvl5"]["dagonDamage"] == pytest.approx(800)
    assert [lvl["cost"] for lvl in dagon["tip"]["levels"]] == [3000, 4100, 5200, 6300, 7400]


def test_no_raw_percent_placeholders_reach_tooltips(items):
    unresolved = []
    pattern = re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%")
    for item in items.values():
        tip = item.get("tip", {})
        for key in ("desc", "short"):
            text = tip.get(key, "")
            if pattern.search(text):
                unresolved.append((item["id"], key, text))
        for text in tip.get("notes", []):
            if pattern.search(text):
                unresolved.append((item["id"], "note", text))
    assert unresolved == []
