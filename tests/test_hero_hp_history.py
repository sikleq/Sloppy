"""Historical HP uses the attribute rules of each patch, including global changes."""
import json

import pytest

from builders import heroes_stats as hs
from patch.meta import RELEASE_HISTORY


HERO = "npc_dota_hero_axe"
DATES = {entry["version"]: entry["date"] for entry in RELEASE_HISTORY}


@pytest.fixture(autouse=True)
def restore_version_context():
    previous = hs._CTX_VERSION[0]
    yield
    hs._set_ctx_version(previous)


def snapshot(*, primary="DOTA_ATTRIBUTE_STRENGTH", strength=24, base_hp=200):
    return {HERO: {
        "AttributePrimary": primary,
        "AttributeBaseStrength": strength,
        "AttributeBaseAgility": 0,
        "AttributeBaseIntelligence": 0,
        "StatusHealth": base_hp,
        "ArmorPhysical": 0,
        "MagicalResistance": 0,
    }}


def history(snaps, column="hp", mode="starting"):
    col = next(col for col in hs.COLUMNS if col["key"] == column)
    return hs._history_for(snaps, list(snaps), DATES, HERO, col, {}, mode=mode)


@pytest.mark.parametrize("version, strength_hp, other_hp", [
    ("7.12", 680, 680),
    ("7.13", 740, 632),
    ("7.20e", 740, 632),
    ("7.21", 680, 680),
    ("7.32e", 680, 680),
    ("7.33", 728, 728),
])
def test_starting_hp_uses_historical_primary_attribute_rules(version, strength_hp, other_hp):
    hs._set_ctx_version(version)
    assert hs._hp_l1(snapshot(), HERO, {}) == strength_hp
    assert hs._hp_l1(snapshot(primary="DOTA_ATTRIBUTE_AGILITY"), HERO, {}) == other_hp


@pytest.mark.parametrize("column", ["hp", "ehp_phys", "ehp_mag"])
def test_global_hp_change_is_recorded_without_hero_stat_changes(column):
    snap = snapshot()
    result = history({"7.32e": snap, "7.33": snap}, column)
    assert result == "7.33|20.04.2023|V|680|728|hi"


def test_primary_bonus_removal_is_recorded():
    snap = snapshot()
    assert history({"7.20e": snap, "7.21": snap}) == "7.21|29.01.2019|V|740|680|hi"


def test_base_hp_does_not_change_with_attribute_rules():
    snap = snapshot()
    assert history({"7.12": snap, "7.13": snap, "7.21": snap, "7.33": snap}, mode="base") == ""


def test_real_axe_history_combines_base_hp_and_strength_coefficient_changes():
    snaps = {
        version: json.loads((hs.STATS_DIR / version / "heroes.json").read_text(encoding="utf-8"))
        for version in ("7.32e", "7.33")
    }
    assert history(snaps) == "7.33|20.04.2023|V|700|670|hi"


def test_change_with_its_own_note_is_not_shifted_to_the_previous_patch(monkeypatch):
    # 2026-10-24: Beastmaster 7.34d "Base Armor decreased by 1" went to 7.34c because 7.34c had a Hawk health note
    monkeypatch.setattr(hs, "_PATCHNOTE_EVENTS", {("axe", "StatusHealth"): ["7.34c", "7.34d"]})
    result = history({"7.34c": snapshot(base_hp=200), "7.34d": snapshot(base_hp=150)}, mode="base")
    assert result.startswith("7.34d|")


def test_change_without_its_own_note_still_takes_the_previous_patchs_note(monkeypatch):
    # 7.14 Axe "+5 movement speed": the files settled on it only in the 7.15 build
    monkeypatch.setattr(hs, "_PATCHNOTE_EVENTS", {("axe", "StatusHealth"): ["7.34c"]})
    result = history({"7.34c": snapshot(base_hp=200), "7.34d": snapshot(base_hp=150)}, mode="base")
    assert result.startswith("7.34c|")


def test_global_hp_change_is_not_shifted_to_an_earlier_hero_note(monkeypatch):
    monkeypatch.setattr(hs, "_PATCHNOTE_EVENTS", {("axe", "AttributeBaseStrength"): ["7.32e"]})
    snap = snapshot()
    assert history({"7.32e": snap, "7.33": snap}) == "7.33|20.04.2023|V|680|728|hi"
