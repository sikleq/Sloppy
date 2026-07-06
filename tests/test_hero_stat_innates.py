"""Stage 2 — tests for data/rules/hero_stat_innates.json.

Covers:
  • JSON integrity: required fields, known formula types, history ordering.
  • Patch-boundary logic: the helper that selects the right history entry.
  • Formula arithmetic: spot-checks that each formula type produces the
    expected numeric output at level 1 for 7.41d.
  • Patch-history gates: verify that the correct factor is chosen at
    representative boundary patches for heroes with history arrays.
"""
from __future__ import annotations
import json
import math
import os
import pytest

# ---------------------------------------------------------------------------
# Load the rules file
# ---------------------------------------------------------------------------

_RULES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "rules", "hero_stat_innates.json",
)

@pytest.fixture(scope="module")
def rules():
    with open(_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def heroes(rules):
    return rules["heroes"]


@pytest.fixture(scope="module")
def constants(rules):
    return rules["_constants"]


# ---------------------------------------------------------------------------
# Patch comparison helper (mirrors Python _ge / JS patchGe)
# ---------------------------------------------------------------------------

def _patch_key(v: str) -> tuple[int, int]:
    """Return (minor, letter_index) for a patch string like '7.41a'."""
    import re
    m = re.match(r"^7\.(\d+)([a-z]?)$", str(v))
    if not m:
        return (0, 0)
    return (int(m.group(1)), ord(m.group(2)) - 96 if m.group(2) else 0)


def patch_ge(a: str, b: str) -> bool:
    return _patch_key(a) >= _patch_key(b)


def active_entry(effect: dict, patch: str) -> dict | None:
    """Return the history entry that applies at *patch*, or the effect itself
    if there is no history array.  Returns None if no entry is active."""
    if "history" not in effect:
        since = effect.get("since")
        until = effect.get("until")
        if since and not patch_ge(patch, since):
            return None
        if until and not patch_ge(until, patch):
            return None
        return effect
    for entry in reversed(effect["history"]):
        since = entry.get("since", "7.00")
        if patch_ge(patch, since):
            until = entry.get("until")
            if until is None or patch_ge(until, patch):
                return entry
    return None


# ---------------------------------------------------------------------------
# JSON integrity
# ---------------------------------------------------------------------------

KNOWN_FORMULAS = {
    "attr_factor",
    "base_plus_level",
    "flat_per_level",
    "self_attr_pct_per_level",
    "attr_pct_per_level",
    "hp_pct",
    "mana_pool_pct_per_level",
    "ms_multiplier",
    "armor_factor",
    "secondary_attr_factor",
    "dmg_universal_bonus_pct",
    "attr_substitution",
    "mana_shield_ehp",
}

EXPECTED_HEROES = {
    "axe", "beastmaster", "centaur", "dark_seer", "death_prophet",
    "dragon_knight", "drow_ranger", "keeper_of_the_light", "life_stealer",
    "luna", "medusa", "morphling", "naga_siren", "ogre_magi", "razor", "sven", "techies", "tiny",
    "ursa", "void_spirit",
}


class TestJsonIntegrity:
    def test_all_expected_heroes_present(self, heroes):
        assert EXPECTED_HEROES == set(heroes.keys())

    def test_every_hero_has_innate_slug(self, heroes):
        missing = [slug for slug, h in heroes.items() if not h.get("innate")]
        assert missing == [], f"Heroes missing innate slug: {missing}"

    def test_every_hero_has_since(self, heroes):
        missing = [slug for slug, h in heroes.items() if not h.get("since")]
        assert missing == [], f"Heroes missing top-level since: {missing}"

    def test_every_effect_has_target(self, heroes):
        bad = []
        for slug, h in heroes.items():
            for i, eff in enumerate(h.get("effects", [])):
                if "target" not in eff:
                    bad.append(f"{slug}[{i}]")
        assert bad == []

    def test_every_effect_has_known_formula(self, heroes):
        bad = []
        for slug, h in heroes.items():
            for i, eff in enumerate(h.get("effects", [])):
                if eff.get("formula") not in KNOWN_FORMULAS:
                    bad.append(f"{slug}[{i}]: {eff.get('formula')!r}")
        assert bad == []

    def test_history_entries_have_since(self, heroes):
        bad = []
        for slug, h in heroes.items():
            for i, eff in enumerate(h.get("effects", [])):
                for j, entry in enumerate(eff.get("history", [])):
                    if "since" not in entry:
                        bad.append(f"{slug}[{i}].history[{j}]")
        assert bad == []

    def test_history_entries_are_chronological(self, heroes):
        """Each history list must be ordered from oldest to newest patch."""
        bad = []
        for slug, h in heroes.items():
            for i, eff in enumerate(h.get("effects", [])):
                hist = eff.get("history", [])
                for j in range(1, len(hist)):
                    prev = hist[j - 1]["since"]
                    curr = hist[j]["since"]
                    if not patch_ge(curr, prev):
                        bad.append(f"{slug}[{i}] history[{j}]: {curr!r} < {prev!r}")
        assert bad == []

    def test_constants_all_positive(self, constants):
        for k, v in constants.items():
            assert v > 0, f"Constant {k} should be positive, got {v}"


# ---------------------------------------------------------------------------
# active_entry helper
# ---------------------------------------------------------------------------

class TestActiveEntry:
    def test_no_history_always_active(self):
        eff = {"target": "ms", "formula": "flat_per_level", "per_level": 1}
        assert active_entry(eff, "7.41d") is eff

    def test_no_history_respects_since(self):
        eff = {"target": "ms", "formula": "flat_per_level", "per_level": 1, "since": "7.41a"}
        assert active_entry(eff, "7.40c") is None
        assert active_entry(eff, "7.41a") is eff

    def test_history_first_entry(self):
        eff = {"target": "ms", "formula": "attr_factor", "source": "str",
               "history": [
                   {"since": "7.36", "until": "7.36a", "factor": 0.40},
                   {"since": "7.36b", "until": "7.37a", "factor": 0.35},
                   {"since": "7.41a", "factor": 0.40},
               ]}
        e = active_entry(eff, "7.36")
        assert e is not None and e["factor"] == pytest.approx(0.40)

    def test_history_middle_entry(self):
        eff = {"target": "ms", "formula": "attr_factor", "source": "str",
               "history": [
                   {"since": "7.36", "until": "7.36a", "factor": 0.40},
                   {"since": "7.36b", "until": "7.37a", "factor": 0.35},
                   {"since": "7.41a", "factor": 0.40},
               ]}
        e = active_entry(eff, "7.36b")
        assert e is not None and e["factor"] == pytest.approx(0.35)

    def test_history_open_last_entry(self):
        eff = {"target": "ms", "formula": "attr_factor", "source": "str",
               "history": [
                   {"since": "7.36", "until": "7.36a", "factor": 0.40},
                   {"since": "7.36b", "until": "7.37a", "factor": 0.35},
                   {"since": "7.41a", "factor": 0.40},
               ]}
        e = active_entry(eff, "7.41d")
        assert e is not None and e["factor"] == pytest.approx(0.40)

    def test_history_gap_returns_none(self):
        # 7.37b to 7.40 is a gap in the test history above (no matching entry)
        eff = {"target": "ms", "formula": "attr_factor", "source": "str",
               "history": [
                   {"since": "7.36", "until": "7.36a", "factor": 0.40},
                   {"since": "7.36b", "until": "7.37a", "factor": 0.35},
                   {"since": "7.41a", "factor": 0.40},
               ]}
        # 7.37b falls after 7.37a (until) and before 7.41a (since) → gap
        e = active_entry(eff, "7.37b")
        assert e is None


# ---------------------------------------------------------------------------
# Patch-boundary gates per hero
# ---------------------------------------------------------------------------

class TestPatchBoundaries:
    """Verify that the correct factor / params are selected at key boundaries."""

    def _eff(self, heroes, slug, target):
        return next(e for e in heroes[slug]["effects"] if e["target"] == target)

    def test_centaur_factor_7_36(self, heroes):
        e = active_entry(self._eff(heroes, "centaur", "ms"), "7.36")
        assert e["factor"] == pytest.approx(0.40)

    def test_centaur_factor_7_36b(self, heroes):
        e = active_entry(self._eff(heroes, "centaur", "ms"), "7.36b")
        assert e["factor"] == pytest.approx(0.35)

    def test_centaur_factor_7_37b(self, heroes):
        e = active_entry(self._eff(heroes, "centaur", "ms"), "7.37b")
        assert e["factor"] == pytest.approx(0.30)

    def test_centaur_factor_7_41a(self, heroes):
        e = active_entry(self._eff(heroes, "centaur", "ms"), "7.41a")
        assert e["factor"] == pytest.approx(0.40)

    def test_dark_seer_factor_7_36(self, heroes):
        e = active_entry(self._eff(heroes, "dark_seer", "aspd"), "7.36")
        assert e["factor"] == pytest.approx(0.5)

    def test_dark_seer_factor_7_38(self, heroes):
        e = active_entry(self._eff(heroes, "dark_seer", "aspd"), "7.38")
        assert e["factor"] == pytest.approx(1.0)

    def test_morphling_range_factor_7_41(self, heroes):
        e = active_entry(self._eff(heroes, "morphling", "range"), "7.41")
        assert e["factor"] == pytest.approx(0.20)

    def test_morphling_range_factor_7_41d(self, heroes):
        e = active_entry(self._eff(heroes, "morphling", "range"), "7.41d")
        assert e["factor"] == pytest.approx(0.25)

    def test_morphling_ms_before_7_41_inactive(self, heroes):
        e = active_entry(self._eff(heroes, "morphling", "ms"), "7.40c")
        assert e is None

    def test_kotl_factor_7_41a(self, heroes):
        e = active_entry(self._eff(heroes, "keeper_of_the_light", "ms"), "7.41a")
        assert e["factor"] == pytest.approx(0.4)

    def test_kotl_factor_7_41c(self, heroes):
        e = active_entry(self._eff(heroes, "keeper_of_the_light", "ms"), "7.41c")
        assert abs(e["factor"] - 1 / 3) < 1e-4

    def test_kotl_inactive_before_7_41a(self, heroes):
        e = active_entry(self._eff(heroes, "keeper_of_the_light", "ms"), "7.40c")
        assert e is None

    def test_death_prophet_inactive_before_7_40(self, heroes):
        e = active_entry(self._eff(heroes, "death_prophet", "ms"), "7.36")
        assert e is None

    def test_death_prophet_base_7_40(self, heroes):
        e = active_entry(self._eff(heroes, "death_prophet", "ms"), "7.40")
        assert e["base_pct"] == pytest.approx(0.75)
        assert e["per_level_pct"] == pytest.approx(0.75)

    def test_death_prophet_base_7_41a(self, heroes):
        e = active_entry(self._eff(heroes, "death_prophet", "ms"), "7.41a")
        assert e["base_pct"] == pytest.approx(0.50)
        assert e["per_level_pct"] == pytest.approx(0.75)

    def test_ursa_factor_7_36(self, heroes):
        e = active_entry(self._eff(heroes, "ursa", "dmg"), "7.36")
        assert e["factor"] == pytest.approx(1.5)

    def test_ursa_factor_7_39d(self, heroes):
        e = active_entry(self._eff(heroes, "ursa", "dmg"), "7.39d")
        assert e["factor"] == pytest.approx(1.25)

    def test_techies_inactive_before_7_41a(self, heroes):
        e = active_entry(self._eff(heroes, "techies", "mpr"), "7.40c")
        assert e is None

    def test_techies_params_7_41a(self, heroes):
        e = active_entry(self._eff(heroes, "techies", "mpr"), "7.41a")
        assert e["base_pct"] == pytest.approx(0.0008)
        assert e["per_level_pct"] == pytest.approx(0.0002)

    def test_techies_params_7_41c(self, heroes):
        e = active_entry(self._eff(heroes, "techies", "mpr"), "7.41c")
        assert e["base_pct"] == pytest.approx(0.001)
        assert e["per_level_pct"] == pytest.approx(0.0001)

    def test_void_spirit_hpr_pre_7_41(self, heroes):
        e = active_entry(self._eff(heroes, "void_spirit", "hpr"), "7.36b")
        assert e["factor"] == pytest.approx(0.25)

    def test_void_spirit_hpr_7_41(self, heroes):
        e = active_entry(self._eff(heroes, "void_spirit", "hpr"), "7.41")
        assert e["factor"] == pytest.approx(0.30)

    def test_void_spirit_armor_removed_in_7_41(self, heroes):
        e = active_entry(self._eff(heroes, "void_spirit", "armor"), "7.41")
        assert e is None

    def test_void_spirit_mr_removed_in_7_41(self, heroes):
        e = active_entry(self._eff(heroes, "void_spirit", "mr"), "7.41")
        assert e is None

    def test_beastmaster_inactive_before_7_41a(self, heroes):
        e = active_entry(heroes["beastmaster"]["effects"][0], "7.40c")
        assert e is None

    def test_razor_inactive_before_7_41a(self, heroes):
        e = active_entry(heroes["razor"]["effects"][0], "7.40c")
        assert e is None


# ---------------------------------------------------------------------------
# Formula arithmetic spot-checks at 7.41d, level 1
# ---------------------------------------------------------------------------

class TestFormulas:
    """Verify each formula type produces the correct numeric output.
    Uses representative attribute values rather than live KV data so tests
    are fast and deterministic.
    """

    C = {
        "HPREG_PER_STR": 0.1,
        "MANAREG_PER_INT": 0.05,
        "AS_PER_AGI": 1.0,
        "ARMOR_PER_AGI": 1 / 6,
        "MR_PER_INT": 0.1,
        "OGRE_MANA_PER_STR": 6.0,
        "OGRE_MANAREG_PER_STR": 0.02,
    }

    def test_attr_factor_centaur_ms(self, heroes):
        """Centaur: bonus MS = STR * 0.40 at 7.41d."""
        eff = next(e for e in heroes["centaur"]["effects"] if e["target"] == "ms")
        entry = active_entry(eff, "7.41d")
        str_val = 25  # representative
        result = str_val * entry["factor"]
        assert result == pytest.approx(25 * 0.40)

    def test_base_plus_level_dragon_knight_hpr(self, heroes):
        """Dragon Knight: HPR bonus at level 1 = 2 + 0.5 * 1 = 2.5."""
        eff = next(e for e in heroes["dragon_knight"]["effects"] if e["target"] == "hpr")
        entry = active_entry(eff, "7.41d")
        result = entry["base"] + entry["per_level"] * 1
        assert result == pytest.approx(2.5)

    def test_base_plus_level_dragon_knight_armor(self, heroes):
        eff = next(e for e in heroes["dragon_knight"]["effects"] if e["target"] == "armor")
        entry = active_entry(eff, "7.41d")
        result = entry["base"] + entry["per_level"] * 1
        assert result == pytest.approx(2.5)

    def test_base_plus_level_beastmaster_aspd_level1(self, heroes):
        """Beastmaster: ASPD bonus at level 1 = 7 + 3 * 1 = 10."""
        eff = heroes["beastmaster"]["effects"][0]
        entry = active_entry(eff, "7.41d")
        result = entry["base"] + entry["per_level"] * 1
        assert result == pytest.approx(10)

    def test_base_plus_level_beastmaster_aspd_level15(self, heroes):
        eff = heroes["beastmaster"]["effects"][0]
        entry = active_entry(eff, "7.41d")
        result = entry["base"] + entry["per_level"] * 15
        assert result == pytest.approx(52)

    def test_flat_per_level_life_stealer_aspd(self, heroes):
        """Life Stealer: ASPD bonus at level 1 = 4 * 1 = 4."""
        eff = heroes["life_stealer"]["effects"][0]
        entry = active_entry(eff, "7.41d")
        result = entry["per_level"] * 1
        assert result == pytest.approx(4)

    def test_flat_per_level_razor_ms(self, heroes):
        """Razor: MS bonus at level 10 = 1 * 10 = 10."""
        eff = heroes["razor"]["effects"][0]
        entry = active_entry(eff, "7.41d")
        result = entry["per_level"] * 10
        assert result == pytest.approx(10)

    def test_self_attr_pct_per_level_drow_agi(self, heroes):
        """Drow: bonus AGI at level 1 = base_agi * (0.10 + 0.01 * 1)."""
        eff = heroes["drow_ranger"]["effects"][0]
        entry = active_entry(eff, "7.41d")
        base_agi = 26  # representative
        result = base_agi * (entry["base_pct"] + entry["per_level_pct"] * 1)
        assert result == pytest.approx(26 * 0.11)

    def test_attr_pct_per_level_sven_dmg(self, heroes):
        """Sven: bonus damage at level 1 = STR * (0.08 + 0.02 * 1)."""
        eff = heroes["sven"]["effects"][0]
        entry = active_entry(eff, "7.41d")
        str_val = 23  # representative
        result = str_val * (entry["base_pct"] + entry["per_level_pct"] * 1)
        assert result == pytest.approx(23 * 0.10)

    def test_hp_pct_ursa_dmg(self, heroes):
        """Ursa: bonus damage at 7.41d = hp * 1.25 / 100."""
        eff = heroes["ursa"]["effects"][0]
        entry = active_entry(eff, "7.41d")
        hp = 560  # representative
        result = hp * entry["factor"] / 100
        assert result == pytest.approx(560 * 1.25 / 100)

    def test_mana_pool_pct_per_level_techies(self, heroes):
        """Techies 7.41c+: MPR bonus = mp * (0.001 + 0.0001 * level)."""
        eff = heroes["techies"]["effects"][0]
        entry = active_entry(eff, "7.41d")
        mp = 507  # representative
        result = mp * (entry["base_pct"] + entry["per_level_pct"] * 1)
        assert result == pytest.approx(507 * 0.0011, rel=1e-5)

    def test_ms_multiplier_death_prophet_7_41d(self, heroes):
        """Death Prophet 7.41a+: multiplier at level 5 = 1 + (0.5 + 0.75*5)/100."""
        eff = heroes["death_prophet"]["effects"][0]
        entry = active_entry(eff, "7.41d")
        level = 5
        mult = 1 + (entry["base_pct"] + entry["per_level_pct"] * level) / 100
        expected = 1 + (0.5 + 0.75 * 5) / 100
        assert mult == pytest.approx(expected)

    def test_armor_factor_axe_str(self, heroes):
        """Axe: bonus STR = (armor_base + agi * ARMOR_PER_AGI) * 0.5."""
        eff = heroes["axe"]["effects"][0]
        entry = active_entry(eff, "7.41d")
        armor_base = 3.08  # representative
        agi = 17
        bonus = (armor_base + agi * self.C["ARMOR_PER_AGI"]) * entry["factor"]
        expected = (3.08 + 17 / 6) * 0.5
        assert bonus == pytest.approx(expected, rel=1e-5)

    def test_secondary_attr_factor_void_spirit_hpr(self, heroes):
        """Void Spirit 7.41: bonus HPR = STR * HPREG_PER_STR * 0.30."""
        eff = next(e for e in heroes["void_spirit"]["effects"] if e["target"] == "hpr")
        entry = active_entry(eff, "7.41d")
        str_val = 22  # representative
        result = str_val * self.C["HPREG_PER_STR"] * entry["factor"]
        assert result == pytest.approx(22 * 0.1 * 0.30)

    def test_secondary_attr_factor_void_spirit_aspd(self, heroes):
        eff = next(e for e in heroes["void_spirit"]["effects"] if e["target"] == "aspd")
        entry = active_entry(eff, "7.41d")
        agi = 22
        result = agi * self.C["AS_PER_AGI"] * entry["factor"]
        assert result == pytest.approx(22 * 1.0 * 0.30)

    def test_attr_substitution_ogre_mp(self, heroes):
        """Ogre Magi: MP = STR * 6 (not INT * 12)."""
        eff = next(e for e in heroes["ogre_magi"]["effects"] if e["target"] == "mp")
        entry = active_entry(eff, "7.41d")
        str_val = 21  # representative
        result = str_val * entry["factor"]
        assert result == pytest.approx(21 * 6.0)

    def test_attr_substitution_ogre_mpr(self, heroes):
        """Ogre Magi: MPR = STR * 0.02 (not INT * 0.05)."""
        eff = next(e for e in heroes["ogre_magi"]["effects"] if e["target"] == "mpr")
        entry = active_entry(eff, "7.41d")
        str_val = 21
        result = str_val * entry["factor"]
        assert result == pytest.approx(21 * 0.02)

    def test_dmg_universal_bonus_pct_void_spirit(self, heroes):
        """Void Spirit 7.41: damage mult *= 1.15."""
        eff = next(e for e in heroes["void_spirit"]["effects"] if e["target"] == "dmg")
        entry = active_entry(eff, "7.41d")
        base_mult = 0.45
        result = base_mult * (1 + entry["factor"])
        assert result == pytest.approx(0.45 * 1.15)

    def test_dmg_universal_bonus_pct_void_spirit_inactive_before_7_41(self, heroes):
        eff = next(e for e in heroes["void_spirit"]["effects"] if e["target"] == "dmg")
        assert active_entry(eff, "7.40c") is None


# ---------------------------------------------------------------------------
# Luna: nvision not a displayed stat
# ---------------------------------------------------------------------------

class TestLunaEffects:
    def test_luna_has_dmg_and_nvision_effects(self, heroes):
        targets = {e["target"] for e in heroes["luna"]["effects"]}
        assert "dmg" in targets
        assert "nvision" in targets

    def test_luna_dmg_flat_per_level(self, heroes):
        eff = next(e for e in heroes["luna"]["effects"] if e["target"] == "dmg")
        assert eff["formula"] == "flat_per_level"
        assert eff["per_level"] == 2

    def test_luna_dmg_level10(self, heroes):
        eff = next(e for e in heroes["luna"]["effects"] if e["target"] == "dmg")
        entry = active_entry(eff, "7.41d")
        assert entry["per_level"] * 10 == pytest.approx(20)

    def test_luna_nvision_level1(self, heroes):
        eff = next(e for e in heroes["luna"]["effects"] if e["target"] == "nvision")
        entry = active_entry(eff, "7.41d")
        result = entry["base"] + entry["per_level"] * 1
        assert result == pytest.approx(250)
