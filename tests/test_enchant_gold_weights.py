"""Enchantment rows weighed in gold (patch/enchant_gold.py; owner 2026-11-26).

Values per tier from data/rules/enchant_tables.json 7.42, stat prices from data/rules/item_stat_prices.json."""
import pytest

import patch.weights as W
from patch.enchant_gold import (_block, _sides, _stat_row, _value_at, clean_label, enchant_row_gold, is_penalty,
                                stat_is_pct, survival)
from patch.state import _State


def _ctx(name, ver="7.42"):
    return {"kind": "enchant", "enchant": name, "version": ver}


def _without_gold(monkeypatch, text, tags, ctx):
    monkeypatch.setattr(W, "_enchant_row_scores", lambda *a: None)
    return W._row_scores(text, tags, "", ctx)


def _price_of(ver="7.42"):
    return lambda st: W._price(W._stat_key(clean_label(st), stat_is_pct(st), None), ver)


def _by_minute(pieces, held=(0, 75)):
    """Survival-weighted mean of a step function given by hand as [(from, to, value)] over the minutes the
    enchantment is held on both sides."""
    num = sum(survival(m + 0.5) * v for a, b, v in pieces for m in range(a, b))
    return num / sum(survival(m + 0.5) for m in range(*held))


def test_health_row_is_scored_in_gold_of_the_enchantment():
    net, vol = W._row_scores("Health bonus changed from +110/150/190/230 to +110/170/230", {"buff"}, "",
                             _ctx("Brawny"))
    assert 0 < net == vol < 0.41          # was the flat 0.41 of the hero formula: a few HP is a small part


def test_new_stat_takes_its_gold_and_sign():
    net, _ = W._row_scores("Now provides +0/0/16% Lifesteal", {"new"}, "", _ctx("Brawny"))
    assert net > 0.5


def test_values_are_compared_tier_against_tier():
    # owner 2026-11-26 "с тиром": both sides on the 7.42 schedule (tiers at 0/15/30/50). Brawny health old
    # 110/150/190/230 (tiers 1-4), new 110/170/230 (tiers 1-3): tier 2 (15-30) +20, tier 3 (30-50) +40; tier 4
    # (50+) has no Brawny in 7.42, players swap it there, so only 0-50 counts.
    gold, worth = enchant_row_gold("Health bonus changed from +110/150/190/230 to +110/170/230", "Brawny", "7.42",
                                   _price_of())
    want = _by_minute([(15, 30, 20), (30, 50, 40)], held=(0, 50))
    assert gold == pytest.approx(want * W._price("health", "7.42"))
    assert worth > 0


def test_schedule_change_is_not_put_on_the_enchantment():
    # Keen-eyed Mana Regen 1/1.5/2 -> 1/2: tier 3 gives 2 instead of 1.5 = a buff. By real minutes the later tier 3
    # (30:00 instead of 25:00) cancelled it (+0.03); tier against tier it is +0.5 over the tier-3 slot
    gold, _ = enchant_row_gold("Mana Regen bonus changed from +1/1.5/2 to +1/2", "Keen-eyed", "7.42", _price_of())
    assert gold == pytest.approx(_by_minute([(30, 50, 0.5)], held=(15, 50)) * W._price("mana_regen", "7.42"))


def test_bonus_on_a_tier_the_enchantment_left_is_not_compared():
    # Brawny Slow Resist was tier 4 only; 7.42 Brawny has no tier 4 (swapped there): no tier to compare -> old formula
    assert enchant_row_gold("No longer provides +0/0/0/25% Slow Resist", "Brawny", "7.42", _price_of()) is None


def test_enchantment_counts_only_while_its_tier_is_the_current_one():
    # owner 2026-11-26: "чары точно всегда меняют" — Keen-eyed 7.42 (tiers 2-3) is not held before 15:00 (tier 1)
    # nor from 50:00 (tier 4 without it); the old side, on the same schedule, still has its tier 4
    old_s, new_s = _sides(_block("Keen-eyed", "7.42"), "7.42")
    cast = next(s for s in _block("Keen-eyed", "7.42")["stats"] if clean_label(s) == "Cast Range")
    assert _value_at(new_s, cast["new"], 10) is None
    assert (_value_at(old_s, cast["old"], 20), _value_at(new_s, cast["new"], 20)) == (125, 100)
    assert (_value_at(old_s, cast["old"], 40), _value_at(new_s, cast["new"], 40)) == (135, 120)
    assert _value_at(new_s, cast["new"], 55) is None
    assert _value_at(old_s, cast["old"], 55) == 145


def test_enchantment_with_an_unpriced_stat_keeps_the_old_formula(monkeypatch):
    # Timeless: Debuff Duration has no shop price, its worth would be too low (scored -3.2 before this guard)
    text, tags = "Spell Amplification bonus changed from +5/12% to +10%", {"nerf"}
    assert W._row_scores(text, tags, "", _ctx("Timeless")) == _without_gold(monkeypatch, text, tags,
                                                                            _ctx("Timeless"))


def test_penalty_rows_are_not_priced():
    # 7.42 table: label "<font color='#e03e2e'>Max Mana</font>", penalty flag false -> the red colour decides
    text = "Max Mana penalty changed from 10/12/14% to 10/14%"
    st = _stat_row(_block("Keen-eyed", "7.42"), text)
    assert st is not None and is_penalty(st)
    assert enchant_row_gold(text, "Keen-eyed", "7.42", lambda st: 1.0) is None


def test_enchantment_with_a_red_penalty_is_still_priced(monkeypatch):
    # Keen-eyed 7.42 went to the old formula whole: its red Max Mana label looked like an unpriced stat
    text, tags = "Cast Range bonus changed from +125/135/145 to +100/120", {"nerf"}
    assert W._row_scores(text, tags, "", _ctx("Keen-eyed")) != _without_gold(monkeypatch, text, tags,
                                                                             _ctx("Keen-eyed"))


def test_attack_range_label_with_markup_has_a_price():
    st = next(s for s in _block("Vast", "7.38c")["stats"] if "Attack Range" in s["label"])
    assert W._price(W._stat_key(clean_label(st), stat_is_pct(st), None), "7.38c")


def test_enchantment_name_ignores_case():
    assert _block("Keen-eyed", "7.41") is not None      # the 7.41 table says "Keen-Eyed"


def test_patch_without_a_table_keeps_the_old_formula(monkeypatch):
    text, tags = "Health bonus changed from +110 to +120", {"buff"}
    assert W._row_scores(text, tags, "", _ctx("Brawny", "7.08")) == _without_gold(monkeypatch, text, tags,
                                                                                 _ctx("Brawny", "7.08"))


def test_use_multiplier_follows_pick_share(monkeypatch):
    monkeypatch.setattr(W, "_NEUTRAL_SHARE", {"7.42": {
        "enchants": {"mystical": {"ratio": 4.0, "n": 10 ** 9}, "vital": {"ratio": 0.01, "n": 10 ** 9},
                     "alert": {"ratio": 4.0, "n": 200}},
        "items": {"pogo_stick": {"ratio": 2.25, "n": 10 ** 9}}}})
    assert W.neutral_use_multiplier(_ctx("Mystical")) == pytest.approx(2.0, abs=1e-3)      # sqrt(4)
    assert W.neutral_use_multiplier(_ctx("Vital")) == pytest.approx(0.5, abs=1e-3)         # floor
    assert W.neutral_use_multiplier(_ctx("Alert")) == pytest.approx(1.5, abs=1e-3)         # half trusted at n=200
    item = {"kind": "item", "item": "pogo_stick", "neutral": True, "version": "7.42a"}  # 7.42a -> 7.42
    assert W.neutral_use_multiplier(item) == pytest.approx(1.5, abs=1e-3)
    assert W.neutral_use_multiplier(dict(item, neutral=False)) == 1.0                      # shop item
    assert W.neutral_use_multiplier(_ctx("Mystical", "7.37")) == 1.0                       # no data


def test_use_multiplier_scales_the_row(monkeypatch):
    text, tags = "Health bonus changed from +110/150/190/230 to +110/170/230", {"buff"}
    monkeypatch.setattr(W, "_NEUTRAL_SHARE", {})
    base = W.row_scores(text, tags, "", _ctx("Brawny"))                         # no share data: x1
    monkeypatch.setattr(W, "_NEUTRAL_SHARE", {"7.42": {"enchants": {"brawny": {"ratio": 4.0, "n": 10 ** 9}},
                                                       "items": {}}})
    net, vol = W.row_scores(text, tags, "", _ctx("Brawny"))
    assert net == pytest.approx(base[0] * 2.0, abs=2e-3) and vol == pytest.approx(base[1] * 2.0, abs=2e-3)


def test_use_multiplier_takes_the_share_before_the_change(monkeypatch):
    # a buff brings picks; the patch's own share would count it twice -> the previous patch's share first
    monkeypatch.setattr(W, "_NEUTRAL_SHARE", {
        "7.41f": {"enchants": {"brawny": {"ratio": 0.25, "n": 10 ** 9}}, "items": {}},
        "7.42": {"enchants": {"brawny": {"ratio": 4.0, "n": 10 ** 9}, "nimble": {"ratio": 4.0, "n": 10 ** 9}},
                 "items": {}}})
    assert W.neutral_use_multiplier(_ctx("Brawny")) == pytest.approx(0.5, abs=1e-3)
    assert W.neutral_use_multiplier(_ctx("Nimble")) == pytest.approx(2.0, abs=1e-3)   # not in 7.41f: own patch


def test_share_builder_normalises_within_tier_and_by_level_reach():
    import sys
    sys.path.insert(0, "tools")
    from build_neutral_share import build
    export = {"7.99": {
        "tiers": {"1": {"hero_games_reaching": 100}, "2": {"hero_games_reaching": 100},
                  "3": {"hero_games_reaching": 50}},
        "trinkets": [{"item": "item_a", "tier": 1, "hero_games": 60}, {"item": "item_b", "tier": 1, "hero_games": 20},
                     {"item": "item_c", "tier": 3, "hero_games": 10}, {"item": "item_d", "tier": 3, "hero_games": 10}],
        "enhancements": [
            {"item": "item_enhancement_x", "level": 1, "hero_games": 40, "offered_to_hero_games": 100},
            {"item": "item_enhancement_x", "level": 3, "hero_games": 20, "offered_to_hero_games": 100},
            {"item": "item_enhancement_y", "level": 1, "hero_games": 40, "offered_to_hero_games": 100}]}}
    out = build(export, tiers_of=lambda v: {"x": {1: 1, 3: 3}, "y": {1: 1}})["7.99"]
    # tier 3 artifacts are compared with tier 3 only: both at the mean
    assert out["items"]["c"]["ratio"] == out["items"]["d"]["ratio"] == 1.0
    assert out["items"]["a"]["ratio"] == pytest.approx(1.5)
    # x level 3 is taken at tier 3, which 50 of 100 reach: 20/50, not 20/100 -> x = mean(0.4, 0.4) = y
    assert out["enchants"]["x"]["ratio"] == out["enchants"]["y"]["ratio"] == 1.0


def test_row_context_names_the_enchantment():
    from patch.enchants import enchant_header
    from patch.row_scores import _row_ctx
    _State.current_patch_version = "7.42"
    enchant_header("Keen-eyed")
    ctx = _row_ctx("x")
    assert ctx["kind"] == "enchant" and ctx["enchant"] == "Keen-eyed"
