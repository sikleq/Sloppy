"""Weights (patch/weights.py + the scoring hooks in patch/elements.py) — regression tests for the
2026-09-25 audit (docs/weights.md "Audit 2026-09-25")."""
import os
import re

import pytest

import patch.weights as W
from patch.badges import b, t
from patch.state import _State

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def v741():
    _State.current_patch_version = "7.41"
    _State.current_ability_slug = None
    _State.current_ability_innate = False
    yield
    _State.current_ability_slug = None
    _State.current_ability_innate = False


def _cell(key, ver="7.41"):
    return _State.dynamics[key]["patches"][ver]


# ---- context -------------------------------------------------------------------------------

def test_ability_context_does_not_leak_into_the_next_entity(v741):
    """The previous hero's ability slug gave Tormentor rows Wraith King's ultimate x1.3."""
    from patch.elements import _row_ctx, ability, enchant_header, hero_header
    hero_header("Wraith King")
    ability("Reincarnation", slug="skeleton_king_reincarnation")
    assert _row_ctx("x")["ability"] == "skeleton_king_reincarnation"
    enchant_header("Titanic")
    assert _row_ctx("x")["ability"] is None
    assert W.context_multiplier(_row_ctx("x")) == 1.0


def test_ultimates_read_from_741f_kv_layout():
    """7.41f moved hero abilities under DOTAHeroes -> hero -> AbilityDefinitions."""
    ults = W.ultimates()
    assert {"antimage_mana_void", "skeleton_king_reincarnation", "enigma_black_hole"} <= ults
    assert len(ults) >= 120


# ---- magnitude -----------------------------------------------------------------------------

def test_small_change_floor_uses_the_last_level_that_changed():
    # max rank unchanged (15s -> 15s): the change is 20 -> 18s at level 3, not "0 s"
    assert W._small_change_damp("Cooldown decreased from 30/25/20/15s to 24/21/18/15s") == 1.0
    assert W._small_change_damp("Cooldown decreased from 140/120/100s to 120/110/100s") == 1.0
    assert W._small_change_damp("Duration increased from 1.2s to 1.3s") == 0.35
    assert W._small_change_damp("Damage to Healing rescaled from 20% to 10/15/20/25%") == 1.0


def test_signal_j_is_not_inflated_by_hero_base_stats():
    """J was fitted with hero base-stat events pooled in (tiny % steps -> huge u), then applied to
    spell rows: "Base Damage 270 -> 240" weighed 2.6x "Damage 270 -> 240"."""
    j = W._WJ["J"]
    assert "base_u" in j and j["base_u"]["base_damage"] > 2 * j["u"]["base_damage"]
    badge = b(270, 240)
    spell_base, _ = W.row_scores("Base Damage decreased from 270 to 240", {"nerf"}, badge)
    plain_dmg, _ = W.row_scores("Damage decreased from 270 to 240", {"nerf"}, badge)
    assert spell_base < 0 and plain_dmg < 0
    assert abs(spell_base) / abs(plain_dmg) < 1.5


@pytest.mark.parametrize("text,kind", [
    ("Jex return speed increased from 600 to 800", "move_speed"),
    ("Turn Speed Manipulation increased from 40% to 60%", "turn_rate"),
    ("Cast Speed Manipulation increased from 40% to 60%", "cast_point"),
    ("Health Cost per second decreased from 6% to 5%", "health"),
    ("Katana Base Attack Rate increased from 1.4s to 1.5s", "attack_speed"),
    ("Cost decreased from 250 to 225", "cost"),
])
def test_classifier_fixes(text, kind):
    assert W.classify(text) == kind


# ---- items: gold scale ---------------------------------------------------------------------

def _item_ctx(item, version):
    return {"kind": "item", "item": item, "version": version}


def test_item_gold_prices_only_the_items_own_stat_line():
    # an active's bonus / a dominated creep's speed are not the item's movement speed stat
    assert W._item_gold_fraction("Glimmer Bonus Movement Speed decreased from 40 to 20",
                                 _item_ctx("glimmer_cape", "7.38b")) is None
    assert W._item_gold_fraction("Dominated Creep movement speed decreased from 380 to 370",
                                 _item_ctx("helm_of_the_dominator", "7.39e")) is None
    assert W._item_gold_fraction("Arctic Blast damage increased from 200 to 260",
                                 _item_ctx("shivas_guard", "7.41")) is None
    assert W._item_gold_fraction("Movement Speed bonus decreased from +20 to +15",
                                 _item_ctx("wind_lace", "7.38")) > 0
    assert W._item_gold_fraction("Bonus Mana Regen decreased from +1.4 to +1.25",
                                 _item_ctx("urn_of_shadows", "7.40")) > 0


def test_item_cost_rows_on_the_gold_scale():
    ctx = _item_ctx("bfury", "7.41")
    text = "Recipe cost decreased from 600 to 400. Total cost unchanged at 3900g"
    assert W._item_gold_fraction(text, ctx) == 0.0
    assert W.row_scores(text, {"buff"}, b(600, 400, l=True), ctx) == (0.0, 0.0)
    # a basic item's "Cost" is its total cost: same scale as "Total cost A -> B"
    clarity = _item_ctx("clarity", "7.40")
    assert W._item_gold_fraction("Cost increased from 50 to 60", clarity) == pytest.approx(
        W._item_gold_fraction("Total cost increased from 50 to 60", clarity))


def test_total_cost_unchanged_in_the_inline_note_zeroes_the_row(v741):
    from patch.elements import inline_note, item_header, li
    _State.current_patch_version = "7.41e"
    item_header("Shiva's Guard")
    li("Recipe cost decreased from 1350 to 1250", b(1350, 1250, l=True),
       extra=inline_note("Total cost unchanged at 4500g"))
    cell = _cell("item|shivas-guard", "7.41e")
    assert cell["buff"] == 1 and cell.get("w", 0) == 0 and cell.get("v", 0) == 0


# ---- cards that are not li() rows ----------------------------------------------------------

def test_item_property_panes_are_scored(v741):
    """properties_change rows were tallied with scores (0, 0)."""
    from patch.elements import item_header, properties_change
    item_header("Blade Mail")
    properties_change(old=[("BUFF", "+6 Armor")], new=[("", "+7 Armor", b(6, 7))])
    cell = _cell("item|blade-mail")
    assert cell["buff"] == 1
    # +1 armor priced in gold against the item cost, like the li() row "Armor bonus +6 -> +7"
    same, _ = W.row_scores("Armor bonus increased from +6 to +7", {"buff"}, b(6, 7),
                           {"kind": "item", "item": "blade_mail", "version": "7.41"})
    assert cell["w"] == pytest.approx(same, abs=1e-3) and cell["w"] > 0


def test_item_property_new_and_del_score_like_new_del_rows(v741):
    from patch.elements import item_header, properties_change
    item_header("Arcane Boots")
    properties_change(old=[("DEL", "+250 Health")], new=[("NEW", "+125 Mana")])
    cell = _cell("item|arcane-boots")
    assert cell["new"] == 1 and cell["del"] == 1 and cell["v"] > 0


def test_ability_and_facet_cards_add_volume(v741):
    from patch.elements import ability_change, hero_header
    hero_header("Shadow Fiend")
    ability_change({"name": "Frenzy", "slug": "nevermore_frenzy", "desc": ["old"]},
                   {"name": "Frenzy", "slug": "nevermore_frenzy", "desc": ["new"]}, tag="rework")
    cell = _cell("hero|shadow-fiend")
    assert cell["rework"] == 1 and cell.get("w", 0) == 0 and cell["v"] > 0
    assert _State.current_ability_slug == "nevermore_frenzy"     # rows below belong to it
    ability_change(None, {"name": "Raze", "slug": "nevermore_shadowraze1", "desc": ["x"]}, tag="new")
    cell = _cell("hero|shadow-fiend")
    assert cell["new"] == 1 and cell["w"] > 0


# ---- matrix JS -----------------------------------------------------------------------------

def test_matrix_line_ignores_hidden_neighbour():
    """"Hide old": the first visible cell drew a riser from the hidden column's (clipped) level."""
    js = open(os.path.join(ROOT, "src", "scripts.js"), encoding="utf-8").read()
    body = js[js.index("function dynDrawRowLines"):]
    body = body[:body.index("\n  }\n")]
    assert re.search(r"const at = j => \([^)]*!vis\[j\]\)", body)
