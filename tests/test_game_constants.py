"""The attribute constants (HP per Strength, armor per Agility, Universal damage, ...) live in the game DLL,
so they are typed in one place, patch/game_constants.py. These tests are the guard:
  * the game's own tooltips (data/dota_english.txt) must agree with today's values — the day Valve changes
    one, this fails and says which row to add;
  * no other file may type them again (Hero Stats / Hero Lab JS read them from the page)."""
import re
from pathlib import Path

import pytest

from patch import game_constants as gc
from patch.meta import RELEASE_HISTORY

ROOT = Path(__file__).resolve().parent.parent


def _tooltip(key):
    text = (ROOT / "data" / "dota_english.txt").read_text(encoding="utf-8", errors="replace")
    m = re.search(r'"%s"\s+"([^"]*)"' % re.escape(key), text)
    assert m, f"dota_english.txt has no {key} — the game renamed its attribute tooltip, find the new one"
    return m.group(1)


def _shown(value, tip):
    """The tooltip shows the value rounded/truncated to its own decimals (1/6 armor -> "0.16")."""
    decimals = len(tip.split(".")[1]) if "." in tip else 0
    return abs(value - float(tip)) < 10 ** -decimals


def _numbers(key, pattern):
    text = _tooltip(key)
    m = re.search(pattern, text)
    assert m, f"{key} no longer reads like {pattern!r}: {text!r} — check the constants in patch/game_constants.py"
    return m.groups()


def test_strength_matches_the_game_tooltip():
    hp, regen = _numbers("DOTA_HeroStats_Strength_Desc", r"grants ([\d.]+) Health and ([\d.]+) Health Regen")
    assert _shown(gc.HP_PER_STR, hp), f"game says {hp} HP per Strength, HP_PER_STR = {gc.HP_PER_STR}"
    assert _shown(gc.HPREG_PER_STR, regen), f"game says {regen} HP regen per Strength, HPREG_PER_STR = {gc.HPREG_PER_STR}"


def test_agility_matches_the_game_tooltip():
    aspd, armor = _numbers("DOTA_HeroStats_Agility_Desc", r"grants ([\d.]+) Attack Speed and ([\d.]+) Armor")
    assert _shown(gc.AS_PER_AGI, aspd), f"game says {aspd} attack speed per Agility, AS_PER_AGI = {gc.AS_PER_AGI}"
    assert _shown(gc.ARMOR_PER_AGI, armor), f"game says {armor} armor per Agility, ARMOR_PER_AGI = {gc.ARMOR_PER_AGI}"


def test_intelligence_matches_the_game_tooltip():
    mana, regen, mr = _numbers("DOTA_HeroStats_Intelligence_Desc",
                               r"grants ([\d.]+) Mana, ([\d.]+) Mana Regen, and ([\d.]+)% Magic Resistance")
    assert _shown(gc.MANA_PER_INT, mana), f"game says {mana} mana per Int: add a row to INT_MANA_HIST"
    assert _shown(gc.MANAREG_PER_INT, regen), f"game says {regen} mana regen per Int: add a row to INT_REGEN_HIST"
    assert _shown(gc.MR_PER_INT, mr), f"game says {mr}% magic resist per Int, MR_PER_INT = {gc.MR_PER_INT}"


def test_universal_damage_matches_the_game_tooltip():
    (mult,) = _numbers("DOTA_Loadout_PrimaryAttribute_Universal_Tooltip", r"main attack damage by ([\d.]+)")
    assert _shown(gc.UNIVERSAL_DMG_PER_ATTR, mult), \
        f"game says {mult} damage per attribute: add a row to UNIVERSAL_DMG_HIST"


def test_histories_are_chronological_and_dated_like_the_release_history():
    dates = {r["version"]: r["date"] for r in RELEASE_HISTORY}
    for name in [n for n in dir(gc) if n.endswith("_HIST")]:     # every history, the new ones too
        hist = getattr(gc, name)
        keys = [gc._vkey(p) for p, _d, _o, _n in hist]
        assert keys == sorted(keys), f"{name} is not oldest-first"
        for (p, d, old, _new), prev in zip(hist, [None] + list(hist)):
            if p in dates:
                assert d == dates[p], f"{name} {p}: date {d}, the release history says {dates[p]}"
            if prev is not None:
                assert old == prev[3], f"{name} {p}: 'old' {old} != the previous row's new value {prev[3]}"


def test_value_in_effect_at_a_patch():
    assert gc.at(gc.UNIVERSAL_DMG_HIST, "7.33b") == 0.6
    assert gc.at(gc.UNIVERSAL_DMG_HIST, "7.33c") == 0.7
    assert gc.at(gc.UNIVERSAL_DMG_HIST, "7.37e") == 0.7
    assert gc.at(gc.UNIVERSAL_DMG_HIST, "7.38") == 0.45
    assert gc.at(gc.INT_MANA_HIST, "7.37") == 12           # server.dll 2024–2025: never 11 (owner 2026-10-22)
    assert gc.at(gc.INT_MANA_HIST, "7.06") == 11           # Liquipedia changelog: 11 in 7.06, 12 from 7.07
    assert gc.at(gc.INT_MANA_HIST) == gc.MANA_PER_INT


@pytest.mark.parametrize("version, ordinary, primary", [
    ("7.08", 20, 20),
    ("7.12", 20, 20),
    ("7.13", 18, 22.5),
    ("7.20e", 18, 22.5),
    ("7.21", 20, 20),
    ("7.32e", 20, 20),
    ("7.33", 22, 22),
    ("7.33b", 22, 22),
])
def test_hp_per_strength_history(version, ordinary, primary):
    assert gc.hp_per_strength(version) == ordinary
    assert gc.hp_per_strength(version, primary=True) == primary


@pytest.mark.parametrize("hist, version, ordinary, primary", [
    # owner 2026-10-22 (after PR #14): every secondary bonus by patch, Valve's 7.13 table and the tooltips
    ("AGI_ARMOR_HIST", "7.12", 0.17, 0.17),
    ("AGI_ARMOR_HIST", "7.13", 0.16, 0.2),
    ("AGI_ARMOR_HIST", "7.26", 0.16, 0.16),
    ("AGI_ARMOR_HIST", "7.27", 1 / 6, 1 / 6),
    ("INT_MANA_HIST", "7.12", 12, 12),
    ("INT_MANA_HIST", "7.13", 12, 15),
    ("INT_MANA_HIST", "7.21", 12, 12),
    ("INT_MR_HIST", "7.12", 0.15, 0.15),
    ("INT_MR_HIST", "7.13", 0, 0),
    ("INT_MR_HIST", "7.33", 0.1, 0.1),
    ("STR_MR_HIST", "7.13", 0.08, 0.1),
    ("STR_MR_HIST", "7.26", 0, 0),
    ("STR_HPREG_HIST", "7.19d", 0, 0),
    ("STR_HPREG_HIST", "7.20", 0.1, 0.125),               # server.dll: 0.1 from 7.20 (tooltip's 0.09 was wrong)
    ("STR_HPREG_HIST", "7.40c", 0.1, 0.1),
    ("INT_MANA_HIST", "7.37", 12, 12),                     # server.dll: never 11
    ("STR_HPREG_AMP_HIST", "7.13", 0.55, 0.6875),
    ("INT_REGEN_AMP_HIST", "7.13", 1.8, 2.25),
    ("INT_REGEN_HIST", "7.19d", 0, 0),
    ("INT_REGEN_HIST", "7.20", 0.05, 0.0625),
    ("AGI_MS_HIST", "7.13", 0.05, 0.0625),
    ("AGI_MS_HIST", "7.26", 0, 0),
])
def test_secondary_bonus_history(hist, version, ordinary, primary):
    h = getattr(gc, hist)
    assert gc.per_point(h, version) == pytest.approx(ordinary)
    assert gc.per_point(h, version, primary=True) == pytest.approx(primary)


def test_armor_formula_by_patch():
    # 7.20 "( 0.052 * Armor ) / ( 0.9+ 0.048 * Armor)", 7.27 back to "Armor * 0.06 / ( 1 + Armor * 0.06 )"
    assert gc.armor_reduction(10, "7.19") == pytest.approx(0.5 / 1.5)        # server.dll of 17.11.2018: 0.05
    assert gc.armor_reduction(10, "7.20") == pytest.approx(0.52 / 1.38)
    assert gc.armor_reduction(10, "7.26") == pytest.approx(0.52 / 1.38)
    assert gc.armor_reduction(10, "7.27") == gc.armor_reduction(10) == pytest.approx(0.6 / 1.6)
    assert gc.armor_reduction(-5, "7.20") == pytest.approx(-0.26 / 1.14)
    from builders.creeps_common import armor_factor
    assert armor_factor(10, "7.20") == gc.armor_reduction(10, "7.20")


def test_today_values_are_the_last_rows():
    assert (gc.ARMOR_PER_AGI, gc.MR_PER_INT, gc.HPREG_PER_STR) == (1 / 6, 0.1, 0.1)
    assert gc.for_js()["armorAgi"] == gc.per_point(gc.AGI_ARMOR_HIST)


def test_current_hp_coefficient_matches_the_history_and_browser():
    assert gc.hp_per_strength() == gc.hp_per_strength(primary=True) == gc.HP_PER_STR
    assert gc.for_js()["hpStr"] == gc.hp_per_strength()


def test_patch_cards_and_hero_stats_share_the_universal_history():
    from patch import hero_stats
    import builders.heroes_stats as hs
    for v in ("7.33", "7.33c", "7.37e", "7.38", "7.41f"):
        hs._set_ctx_version(v)
        assert hs._universal_dmg_mult() == hero_stats.universal_multiplier(v), v
    hs._set_ctx_version(hs._LATEST_STATS_VERSION)


def test_attribute_bonus_is_read_from_the_game_files():
    from patch import hero_stats
    assert hero_stats._attribute_bonus_max() == hero_stats.ATTRIBUTE_BONUS_MAX, \
        "special_bonus_attributes not found in the latest npc_abilities.txt — damage at level 30 uses a guess"


_LITERALS = re.compile(r"\* ?(?:22|0\.16667|0\.45)\b|(?:0\.45|0\.16667) ?\*|a\.agi / 6|'hpr:str': 0\.1")


def test_scripts_js_types_no_attribute_constant():
    js = (ROOT / "src" / "scripts.js").read_text(encoding="utf-8")
    hits = [ln.strip() for ln in js.splitlines() if _LITERALS.search(ln)]
    assert not hits, f"scripts.js types attribute constants again (read C.* from the page): {hits}"
    for key in gc.for_js():
        assert f"C.{key}" in js, f"for_js() key {key} is unused in scripts.js"


def test_pages_embed_the_constants():
    import builders.heroes_stats as hs
    assert 'id="hs-game-constants"' in Path(hs.__file__).read_text(encoding="utf-8")
    import builders.hero_lab as hl
    assert '"constants": _game_constants()' in Path(hl.__file__).read_text(encoding="utf-8")
