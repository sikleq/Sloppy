"""Item prices (signal A v2, tools/fit_item_prices.py -> data/rules/item_stat_prices.json) and how
patch/weights.py applies them — docs/weights.md "Item prices — every stat in gold (2026-09-25)"."""
import json
import os

import pytest

import patch.weights as W
from patch.badges import b, t
from patch.state import _State

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICES = json.load(open(os.path.join(ROOT, "data", "rules", "item_stat_prices.json"), encoding="utf-8"))


def _ctx(item, version):
    return {"kind": "item", "item": item, "version": version}


def _net(text, tags, item, version, badge=""):
    return W.row_scores(text, set(tags), badge, _ctx(item, version))[0]


@pytest.fixture
def v738():
    _State.current_patch_version = "7.38"
    _State.current_ability_slug = None
    _State.pending_cost_panel = None
    for key in ("item|heavens-halberd", "item|gleipnir", "item|shadow-blade", "item|eye-of-skadi"):
        _State.dynamics.pop(key, None)             # other tests / builds may have filled them
    yield
    _State.pending_cost_panel = None


def _cell(key, ver):
    return _State.dynamics[key]["patches"][ver]


# ---- the price table -------------------------------------------------------------------------

EVERY_ITEM_STAT = ["strength", "agility", "intelligence", "all_stats", "damage", "armor", "attack_speed",
                   "move_speed", "move_speed_pct", "boots_move_speed", "health", "mana", "health_regen",
                   "mana_regen", "magic_res", "evasion", "lifesteal", "spell_lifesteal", "spell_amp",
                   "slow_res", "status_res", "restoration_amp", "mana_regen_amp", "manacost_reduction",
                   "cooldown_reduction", "cast_range", "attack_range", "damage_block", "aoe_bonus"]


def test_every_item_stat_has_a_price_in_the_latest_patch():
    latest = PRICES["versions"]["7.41f"]
    assert [s for s in EVERY_ITEM_STAT if s not in latest] == []
    assert all(PRICES["confidence"]["7.41f"][s] in ("anchor", "fit", "single") or PRICES["confidence"]["7.41f"][s].startswith("pooled")
               for s in latest)       # no "prior" left: pooling splits the Sange family (2026-09-26)


@pytest.mark.parametrize("stat,lo,hi", [
    ("strength", 50, 120), ("agility", 50, 120), ("intelligence", 50, 120), ("all_stats", 110, 220),
    ("damage", 35, 80), ("armor", 80, 160), ("attack_speed", 15, 40), ("health", 1.5, 5),
    ("mana", 1.5, 5), ("health_regen", 80, 200), ("mana_regen", 150, 450), ("magic_res", 25, 70),
    ("evasion", 35, 100), ("damage_block", 8, 40),
])
def test_prices_stay_near_valves_basic_items(stat, lo, hi):
    """Anchors: Ogre Axe / Blade / Staff 100 g per point, Vitality Booster 4 g per HP, Cloak 50 g per
    1 % magic resistance, Vanguard's block — a fit far off these means the stat parser broke."""
    for v in ("7.38", "7.41f"):
        assert lo <= W._price(stat, v) <= hi, (stat, v)


def test_damage_block_values_come_from_the_kv():
    assert PRICES["damage_block"]["7.38"]["heavens_halberd"] == pytest.approx(27.0)   # 60% x (60+30)/2
    assert PRICES["damage_block"]["7.41f"]["vanguard"] == pytest.approx(22.5)          # 60% x (50+25)/2
    assert "heavens_halberd" not in PRICES["damage_block"]["7.41f"]


def test_items_the_shop_does_not_sell_are_not_priced():
    assert W._item_base_cost("refresher_shard", "7.41e") == 0
    assert W._item_base_cost("heavens_halberd", "7.38") == pytest.approx((3500 + 2600) / 2)


# ---- stat rows in gold -----------------------------------------------------------------------

def test_a_removed_stat_is_valued_by_its_amount_not_a_flat_del_weight():
    """+20 Strength removed was worth the same as +5 All Attributes added (flat DEL/NEW weight)."""
    s20 = _net("+20 Strength", {"del"}, "heavens_halberd", "7.38")
    a5 = _net("+5 All Attributes", {"new"}, "heavens_halberd", "7.38")
    gold = 20 * W._price("strength", "7.38")
    assert s20 == pytest.approx(-W.ITEM_GOLD_W * W.ITEM_GOLD_K * gold / 3050, abs=2e-3)
    assert a5 > 0 and abs(s20) > 1.5 * a5


@pytest.mark.parametrize("text,stat,amount", [
    ("+25% Health and Lifesteal Amp", "restoration_amp", 25),
    ("+25% Slow Resistance", "slow_res", 25),
    ("+25% Evasion", "evasion", 25),
    ("+6 Health Regen", "health_regen", 6),
    ("+50 Attack Range (Melee & Ranged)", "attack_range", 50),
    ("+75 AoE Bonus", "aoe_bonus", 75),
])
def test_property_pane_sides_are_parsed_as_one_stat(text, stat, amount):
    g = W._item_gold(text, {"new"}, _ctx("heavens_halberd", "7.41f"))
    assert g is not None and g[0] == pytest.approx(amount * W._price(stat, "7.41f"))


def test_percent_and_flat_move_speed_are_different_stats():
    flat = W._item_gold("Movement Speed bonus decreased from +20 to +15", {"nerf"}, _ctx("wind_lace", "7.38"))
    assert flat[0] == pytest.approx(-5 * W._price("move_speed", "7.38"))
    pct = W._item_gold("+10% Movement Speed", {"new"}, _ctx("yasha", "7.41f"))
    assert pct[0] == pytest.approx(10 * W._price("move_speed_pct", "7.41f"))
    boots = W._item_gold("Movement Speed bonus increased from +45 to +50", {"buff"}, _ctx("boots", "7.41f"))
    assert boots[0] == pytest.approx(5 * W._price("boots_move_speed", "7.41f"))


def test_provides_rows_and_lists():
    ctx = _ctx("ancient_janggo", "7.41")
    assert W._item_gold("Provides +8 Agility", {"new"}, ctx)[0] == pytest.approx(8 * W._price("agility", "7.41"))
    lost = W._item_gold("No longer provides +6 Health Regen, +3 Mana Regen, or +20 Damage", {"del"}, ctx)[0]
    assert lost == pytest.approx(-(6 * W._price("health_regen", "7.41") + 3 * W._price("mana_regen", "7.41")
                                   + 20 * W._price("damage", "7.41")))
    aura = W._item_gold("Swiftness Aura now also provides +2.5 Health Regen", {"new"}, ctx)[0]
    assert aura == pytest.approx(2.5 * W._price("health_regen", "7.41"))
    # a passive / conditional bonus is not the item's stat line
    assert W._item_gold("Relentless now also provides +10% status resistance per enemy within 300 units",
                        {"new"}, ctx) is None
    assert W._item_gold("Now also provides passive Behemoth's Blood", {"new"}, ctx) is None


def test_stat_swap_rework_takes_the_sign_of_the_gold():
    """Khanda 7.38 "+8 Mana Regen instead of +50 Damage": a REWORK row, but priced both sides."""
    net, vol = W.row_scores("Now provides +8 Mana Regen instead of +50 Damage", {"rework"}, "",
                            _ctx("angels_demise", "7.38"))
    gold = 8 * W._price("mana_regen", "7.38") - 50 * W._price("damage", "7.38")
    assert gold < 0 and net < 0 and vol >= abs(net)
    # a rework that names only the new side stays sign-less
    assert W.row_scores("Provides +35 Damage and +16% Spell Lifesteal", {"rework"}, "",
                        _ctx("revenants_brooch", "7.38"))[0] == 0.0


# ---- passives that are priced stats elsewhere ------------------------------------------------

def test_damage_block_passive_is_priced_like_vanguard():
    text = ("Passive: Damage Block. Grants a 60% chance to block 60 damage from attacks on melee "
            "heroes, and 30 on ranged")
    g = W._item_gold(text, {"new"}, _ctx("heavens_halberd", "7.38"))
    assert g[0] == pytest.approx(27.0 * W._price("damage_block", "7.38"))
    # no numbers: the removed block is read from the KV of the previous patch (7.40c)
    g = W._item_gold("Damage Block (passive)", {"del"}, _ctx("heavens_halberd", "7.41"))
    assert g[0] == pytest.approx(-27.0 * W._price("damage_block", "7.41"))


# ---- mana costs ------------------------------------------------------------------------------

def test_item_mana_cost_is_the_mana_in_gold_not_its_percent():
    """Disarm 75 -> 25 (-67 %) was +2.51, the heaviest row of the Halberd rework. Now: 50 mana
    x gold per max mana, measured against the item's cost."""
    net = _net("Disarm Mana Cost decreased from 75 to 25", {"buff"}, "heavens_halberd", "7.38", b(75, 25, l=True))
    assert net == pytest.approx(W.ITEM_GOLD_W * W.ITEM_GOLD_K * 50 * W._price("mana", "7.38") / 3050, abs=2e-3)
    assert 0 < net < 0.4
    assert _net("Dominate now has a 50 mana cost", {"nerf"}, "helm_of_the_dominator", "7.39e") < 0
    # neutral items have no price: the reference cost of an item with an active
    ref = W._item_gold("Ribbit mana cost decreased from 40 to 0", {"buff"}, _ctx("pollywog_charm", "7.38c"))
    assert ref[1] == PRICES["ref_cost"]["7.38c"] and ref[0] > 0
    # hero spells keep signal J
    hero = W.row_scores("Mana Cost decreased from 75 to 25", {"buff"}, b(75, 25, l=True),
                        {"kind": "hero", "version": "7.38"})[0]
    assert hero > 1.5


def test_mana_cost_reduction_stat_is_not_a_mana_cost_row():
    gold, _ = W._item_gold("Mana Cost/Mana Loss Reduction bonus increased from +20% to +25%", {"buff"},
                           _ctx("kaya_and_sange", "7.41f"))
    assert gold == pytest.approx(5 * W._price("manacost_reduction", "7.41f"))


# ---- the components panel --------------------------------------------------------------------

def _halberd_738():
    from patch.elements import (components_change, item_header, li, properties_change, ul_close,
                                ul_open)
    item_header("Heaven's Halberd", changed="Item Reworked")
    components_change(old=[("Sange", 2100), ("Talisman of Evasion", 1300)],
                      new=[("Vanguard", 1700), ("Crown", 450)], total_old=3500, total_new=2600,
                      recipe_old=("Recipe", 100), recipe_new=("Recipe", 450))
    properties_change(old=[("DEL", "+20 Strength"), ("DEL", "+25% Evasion"),
                           ("DEL", "+25% Slow Resistance"), ("DEL", "+25% Health and Lifesteal Amp")],
                      new=[("NEW", "+275 Health"), ("NEW", "+6 Health Regen"), ("NEW", "+5 All Attributes")])
    ul_open()
    li("Disarm can now be dispelled", t("NERF"))
    li("Disarm Mana Cost decreased from 75 to 25", b(75, 25, l=True))
    li("Disarm Duration on Ranged heroes decreased from 5s to 4s", b(5, 4))
    li("Passive: Damage Block. Grants a 60% chance to block 60 damage from attacks on melee heroes, "
       "and 30 on ranged", t("NEW"))
    ul_close()


def test_heavens_halberd_738_is_a_nerf(v738):
    """The owner's case: -20 Str, -25 % Evasion, -Slow Resistance, -restoration amp for +275 HP,
    +6 regen, +5 All, a Damage Block passive and 900 g off the price. It netted +0.70."""
    from patch.elements import item_header
    _halberd_738()
    item_header("Heart of Tarrasque")          # ends the block: the panel's cost row is added
    cell = _cell("item|heavens-halberd", "7.38")
    # stat side + price cut ~ 0 (Valve priced the swap fairly); the Disarm nerfs, on the same gold
    # scale as the stats (ITEM_ABILITY_F), make it a mild nerf (-1.43 before 2026-09-26: Disarm was
    # on the louder hero scale and outweighed everything)
    assert -1.0 < cell["w"] < -0.2
    assert cell["new"] == 4 and cell["del"] == 4 and cell["rework"] == 1


def test_panel_total_cost_is_counted_once(v738):
    from patch.elements import components_change, item_header, li, ul_close, ul_open
    item_header("Gleipnir", changed="Item Reworked")
    components_change(old=[("Maelstrom", 2950)], new=[("Point Booster", 1200)],
                      total_old=5750, total_new=4550)
    ul_open()
    li("Recipe cost increased from 550 to 1100 " + b(550, 1100, l=True)
       + ". Total cost decreased from 5750 to 4550", b(5750, 4550, l=True))
    ul_close()
    item_header("Mage Slayer")
    with_row = _cell("item|gleipnir", "7.38")["w"]
    only_row = W.row_scores("Recipe cost increased from 550 to 1100. Total cost decreased from 5750 to 4550",
                            {"buff"}, b(5750, 4550, l=True), _ctx("gungir", "7.38"))[0]
    assert with_row == pytest.approx(only_row, abs=1e-3)


def test_panel_alone_scores_the_total_and_unchanged_totals_score_nothing(v738):
    from patch.elements import components_change, item_header, section
    item_header("Shadow Blade", changed=True)
    components_change(old=[("Claymore", 1350)], new=[("Broadsword", 1000)], total_old=3000, total_new=3350)
    item_header("Eye of Skadi", changed=True)
    components_change(old=[("Ultimate Orb", 2800)], new=[("Ultimate Orb", 2800)], total_old=5300, total_new=5300)
    section("Neutral Items")                   # the block ends with the section
    blade = _cell("item|shadow-blade", "7.38")
    assert blade["w"] == pytest.approx(-W.ITEM_GOLD_W * W.ITEM_GOLD_K * 350 / W._item_base_cost("invis_sword", "7.38"), abs=2e-3)
    assert _cell("item|eye-of-skadi", "7.38").get("w", 0) == 0


def test_every_item_name_resolves_to_a_kv_key():
    """The weights price an item row by its KV cost, looked up by the icon slug. A name whose naive slug
    is not the engine one (Boots of Speed -> item_boots) would silently lose its price (review 2026-09-25)."""
    import glob
    import json
    import os
    import re
    from patch.images import ITEM_SLUG
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keys = set()
    for f in glob.glob(os.path.join(root, "data", "stats", "*", "items.json")):
        keys |= set(json.load(open(f, encoding="utf-8")))
    if not keys:
        import pytest
        pytest.skip("no KV snapshots")
    names = {"Boots of Speed", "Boots of Travel", "Boots of Travel 2"}
    for f in glob.glob(os.path.join(root, "content", "p7*.py")):
        names |= set(re.findall(r'item_header\("([^"]+)"', open(f, encoding="utf-8").read()))
    slug = lambda n: ITEM_SLUG.get(n, n.lower().replace(" ", "_").replace("'", ""))
    assert [n for n in sorted(names) if "item_" + slug(n) not in keys] == []


def test_unpriced_item_row_is_scaled_to_the_gold_scale():
    """An item active's number (Disarm duration 5s -> 4s) has no gold price: it is scored like a hero
    spell row, times ITEM_ABILITY_F, so it does not drown the item's gold-priced stat rows."""
    text = "Disarm Duration on Ranged heroes decreased from 5s to 4s"
    hero = W.row_scores(text, {"nerf"}, "", {"kind": "hero", "version": "7.38"})
    item = W.row_scores(text, {"nerf"}, "", _ctx("heavens_halberd", "7.38"))
    assert item[0] == pytest.approx(hero[0] * W.ITEM_ABILITY_F / W.context_multiplier(
        {"kind": "hero", "version": "7.38"}) * W.context_multiplier({"kind": "item"}), abs=2e-3)


def test_rework_row_takes_the_adoption_shift_the_other_rows_do_not_explain(monkeypatch):
    """Signal R: Orb of Corrosion 7.38 lost ~1000 g of stats (net -3.84), yet pros bought it ~3x as often:
    the REWORK row (new Corrosion passive) gets the unexplained part, capped and shrunk by sample size."""
    monkeypatch.setitem(W._ADOPT["item"], "7.38", {"games": [8447, 1010], "n": {"orb_of_corrosion": [354, 120]}})
    ctx = {"kind": "item", "version": "7.38", "item": "orb_of_corrosion"}
    net = W.rework_adoption_net(ctx, -3.84)
    assert 0 < net <= W.ITEM_REWORK_CAP
    # the same shift, fully explained by the other rows -> nothing left for the rework
    assert W.rework_adoption_net(ctx, 2.2) == 0.0


def test_rework_row_without_adoption_data_stays_zero(monkeypatch):
    monkeypatch.setitem(W._ADOPT["item"], "7.38", {"games": [8447, 1010], "n": {"orb_of_corrosion": [10, 5]}})
    assert W.rework_adoption_net({"kind": "item", "version": "7.38", "item": "orb_of_corrosion"}, 0.0) is None
    assert W.rework_adoption_net({"kind": "item", "version": "7.99", "item": "orb_of_corrosion"}, 0.0) is None


def test_hero_rework_uses_the_pro_pick_share(monkeypatch):
    """Signal R for heroes: a hero picked 3x as often after a patch whose numbered rows net ~0 -> its
    REWORK rows are a buff; picked as the other rows predict -> nothing."""
    monkeypatch.setitem(W._ADOPT["hero"], "7.39", {"games": [10000, 10000], "n": {"pudge": [100, 300]}})
    ctx = {"kind": "hero", "version": "7.39", "hero": "pudge"}
    assert W.rework_adoption_net(ctx, 0.0) > 1.0
    assert W.rework_adoption_net({**ctx, "kind": "ability"}, 0.0) is None


def test_base_damage_next_to_effective_damage_rows_is_scored_once(v738, monkeypatch):
    """Dark Seer 7.38 (owner): "Base Damage increased by 26" only makes up for the Universal multiplier
    0.7 -> 0.45; the real change is "Damage at level 1" / "at level 30". "Damage gain per level" is the
    L30 row again. Only L1 + L30 (and the other rows) count."""
    from patch.elements import hero_header, li, ul_open, ul_close
    monkeypatch.setitem(W._ADOPT, "hero", {})                 # no signal R in this test
    _State.dynamics.pop("hero|dark-seer", None)
    hero_header("Dark Seer")
    ul_open()
    li("Base Damage increased by 26", b(24, 50))
    li("Damage at level 1 increased by 5 (from 49-55 to 54-60)", b(52, 57))
    li("Damage gain per level decreased from +5 to +2.7", b(5, 2.7))
    li("Damage at level 30 decreased by 75 (from 221-227 to 146-152)", t("NERF"))
    ul_close()
    hero_header("Dark Willow")                                # ends the block
    cell = _cell("hero|dark-seer", "7.38")
    assert cell["w"] == pytest.approx(1.00 - 1.80, abs=0.05)       # L1 +1.00, L30 -1.80 (was -0.85 with all four)
    assert cell["buff"] == 2 and cell["nerf"] == 2                 # the rows are still shown and tallied
