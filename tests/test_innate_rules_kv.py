"""Hero innate rules follow the game files (builders/innate_rules.py).

* An effect with a "kv" map is read from data/stats/<v>/heroes/ for every patch newer than the rules'
  `_checked_version` — a new value gets its own history entry with no edit.
* Everything else is guarded: review() lists innates that changed in the latest patch in a way the rules
  do not follow (a reworked innate, a hero with a new innate, a new hero), and the test fails with that list."""
import pytest

from builders import innate_rules as ir


@pytest.fixture(scope="module")
def raw():
    return ir._raw()


def _active(eff, version):
    from builders.heroes_stats import _active_entry
    return _active_entry(eff, version)


def _kv_effects(rules):
    for slug, hero in rules["heroes"].items():
        for eff in hero.get("effects", []):
            if eff.get("kv"):
                yield slug, eff.get("kv_ability") or hero["innate"], eff


def test_mapped_values_match_the_game_at_the_checked_patch(raw):
    checked = raw["_checked_version"]
    bad = []
    for slug, ability, eff in _kv_effects(raw):
        entry = _active(eff, checked)
        assert entry is not None, f"{slug} {eff['target']}: kv effect not active at {checked}"
        game = ir.kv_values(slug, ability, eff["kv"], checked)
        assert game is not None, f"{slug} {eff['target']}: {ability} lacks a kv key in {checked}"
        for field, value in game.items():
            if abs(float(entry[field]) - value) > 1e-9:
                bad.append(f"{slug} {eff['target']}.{field}: rules {entry[field]}, game {value}")
    assert not bad, "hero_stat_innates.json disagrees with the game at its _checked_version:\n" + "\n".join(bad)


def test_rules_are_still_right_for_the_latest_patch(raw):
    latest = ir.stats_versions()[-1]
    problems = ir.review(raw["_checked_version"], latest)
    assert not problems, (
        f"innates changed since {raw['_checked_version']} in a way data/rules/hero_stat_innates.json does not "
        f"follow by itself. Re-check each, update the rule, then set _checked_version to {latest}:\n"
        + "\n".join(problems))


def test_open_mapped_effects_still_find_their_keys(raw):
    latest = ir.stats_versions()[-1]
    lost = [f"{slug} {eff['target']} ({ability}: {sorted({s[0] for s in eff['kv'].values()})})"
            for slug, ability, eff in _kv_effects(raw)
            if _active(eff, latest) is not None and ir.kv_values(slug, ability, eff["kv"], latest) is None]
    assert not lost, f"the latest game files lack these innate keys — the rules stopped following them: {lost}"


def test_review_names_what_changed():
    lines = ir.review("7.40c", "7.41a")          # 7.41a gave Chen a new innate (Zealot)
    assert any(ln.startswith("chen: innate changed") for ln in lines), lines
    # 7.41d moved Morphling's Ebb & Flow numbers — all of them are followed via kv, nothing to re-check
    assert not any(ln.startswith("morphling:") for ln in ir.review("7.41c", "7.41d"))
    assert ir.review("7.41f", "7.41f") == []


def test_a_new_patch_value_gets_its_own_history_entry(monkeypatch, raw):
    checked = raw["_checked_version"]
    real = ir.innate_blocks

    def fake(slug, version):
        if version != "9.99":
            return real(slug, version)
        blocks = {k: {**b, "AbilityValues": dict(b.get("AbilityValues") or {})} for k, b in real(slug, checked).items()}
        if slug == "void_spirit":
            blocks["void_spirit_intrinsic_edge"]["AbilityValues"]["secondary_stat_bonus_pct"] = "35"
        if slug == "ogre_magi":
            blocks["ogre_magi_dumb_luck"]["AbilityValues"]["mana_per_str"] = {"value": "7"}
        return blocks

    monkeypatch.setattr(ir, "innate_blocks", fake)
    rules = ir.load(ir.stats_versions() + ["9.99"])
    void = next(e for e in rules["heroes"]["void_spirit"]["effects"] if e["target"] == "hpr")
    assert void["history"][-2]["until"] == checked
    assert void["history"][-1] == {"since": "9.99", "factor": 0.35}
    assert _active(void, checked)["factor"] == 0.3                      # the past keeps its value
    ogre = next(e for e in rules["heroes"]["ogre_magi"]["effects"] if e["target"] == "mp")
    assert _active(ogre, "7.38")["factor"] == 6.0 and _active(ogre, "9.99")["factor"] == 7.0
    assert ogre["factor"] == 7.0                                       # readers of the effect itself: today
    dmg = next(e for e in rules["heroes"]["void_spirit"]["effects"] if e["target"] == "dmg")
    assert "history" not in dmg and dmg["factor"] == 0.15               # unchanged effects stay as written


def test_pages_use_the_followed_rules():
    import builders.heroes_stats as hs
    assert hs._INNATE_RULES == ir.load()["heroes"]
    import builders.hero_lab as hl
    from pathlib import Path
    src = Path(hl.__file__).read_text(encoding="utf-8")
    assert "hero_stat_innates.json" not in src, "Hero Lab must read the rules through builders.innate_rules"


def test_techies_void_ogre_medusa_numbers_come_from_the_rules():
    import builders.heroes_stats as hs
    hs._set_ctx_version("7.41b")
    assert hs._innate_entry("techies", "mpr", "mana_pool_pct_per_level")["base_pct"] == 0.0008
    hs._set_ctx_version(hs._LATEST_STATS_VERSION)
    assert hs._innate_entry("techies", "mpr", "mana_pool_pct_per_level")["per_level_pct"] == 0.0001
    assert hs._innate_entry("ogre_magi", "mpr", "attr_substitution")["factor"] == 0.02
    from pathlib import Path
    js = (Path(hs.__file__).resolve().parent.parent / "src" / "scripts.js").read_text(encoding="utf-8")
    for literal in ("2 + 0.1 * level", "* 1.15", "0.001 + lvl", "wa.str * 6", "str * 0.02", "mana * 0.98"):
        assert literal not in js, f"scripts.js types an innate number again: {literal!r}"


def test_ogre_dumb_luck_regen_follows_its_history():
    # owner 2026-10-21: 7.37 reduced Dumb Luck's mana regen per Strength 0.03 -> 0.02. Dumb Luck came in 7.33
    # ("New innate ability": 0 Int, 6 MP and 0.03 MP regen per Str) — game files 7.35-7.36c say 0.03
    import builders.heroes_stats as hs
    for version, factor in (("7.33", 0.03), ("7.35d", 0.03), ("7.36c", 0.03), ("7.37", 0.02), ("7.41f", 0.02)):
        hs._set_ctx_version(version)
        assert hs._innate_entry("ogre_magi", "mpr", "attr_substitution")["factor"] == factor, version
        assert hs._innate_entry("ogre_magi", "mp", "attr_substitution")["factor"] == 6.0, version
        game = ir.kv_values("ogre_magi", "ogre_magi_dumb_luck", {"factor": ["mana_regen_per_str", "value", 1]}, version)
        assert game in (None, {"factor": factor}), version          # None: no per-hero file before 7.35
    hs._set_ctx_version("7.32e")                     # before 7.33 Ogre's mana came from Intelligence
    assert hs._innate_entry("ogre_magi", "mp", "attr_substitution") is None
    assert hs._innate_entry("ogre_magi", "mpr", "attr_substitution") is None
    hs._set_ctx_version(hs._LATEST_STATS_VERSION)
    from pathlib import Path
    js = (Path(hs.__file__).resolve().parent.parent / "src" / "scripts.js").read_text(encoding="utf-8")
    assert "s.slug === 'ogre_magi' ? 0 : bonus" not in js      # the Int level-ups follow the same rule in JS
