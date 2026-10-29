"""Proofread of 7.37e (2026-10-28), each rule in the generator so the next patch gets it too."""
import pytest

import tools.generate_patch_code_v2 as g


@pytest.mark.parametrize("text, tag", [
    ("Natural Order: Enemies that leave the AoE now lose 1 stack per second instead of all stacks instantly", "BUFF"),
    ("Now also applies to units under Lycan's control. Bonus is still based on Lycan's level", "BUFF"),
    ("Chain Frost: If the affected hero dies and buys back, Chain Frost will no longer follow that hero", "DEL"),
    ("Presence of the Dark Lord: Now Bonus Armor Reduction buff is removed when Shadow Fiend dies", "NERF"),
    ("Rolling Thunder: Turn Rate bonus changed from flat +110 to +40% (results in +48)", "NERF"),
    ("Nature's Call: Treant gold bounty rescaled from 18-24 on all levels to 16/24/32/40", "NERF"),
    ("Imps no longer explode if killed by enemy heroes", "DEL"),
    ("Eidolon gold bounty increased from 14-20 to 17-20", "NERF"),
    ("Stroke of Fate: Improved behavior when casting at maximum cast range", "QoL"),   # owner 2026-10-28
])
def test_7_37e_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


@pytest.mark.parametrize("text", [
    "Aghanim's Scepter charge restoration time increased from 60s to 70/65/60s",
    "Outgoing Spell Damage reflected increased from 20% to 21%",
])
def test_own_waits_and_self_damage_are_lower_is_better(text):
    assert "l=True" in g._emit_badge(text)


def test_an_old_min_max_range_is_compared_by_its_middle():
    """Owner 2026-10-28: "Treant gold bounty rescaled from 18-24 on all levels to 16/24/32/40" — a % per level against
    the middle of 18-24, not a bare tag; the enemy's gold, so lower is better."""
    text = "Nature's Call: Treant gold bounty rescaled from 18-24 on all levels to 16/24/32/40"
    assert g._emit_badge(text, hero_side=True) == "b(21, [16, 24, 32, 40], l=True)"
    assert g._emit_badge("Eidolon gold bounty increased from 14-20 to 17-20", hero_side=True) == "br(14, 20, 17, 20, l=True)"


def test_a_flat_bonus_turned_percent_compares_the_totals():
    """Owner 2026-10-29: Rolling Thunder "from flat +110 to +40% (results in +48)" — the base is 48 / 40% = 120, so the
    turn rate went 230 → 168 (−27%), a % badge, not a bare NERF tag."""
    text = "Rolling Thunder: Turn Rate bonus changed from flat +110 to +40% (results in +48)"
    assert g._emit_badge(text) == "b(230, 168)"


def test_an_added_upgrade_card_has_the_ability_header_and_charges_take_the_cooldown():
    """Owner 2026-10-28 (7.37e Escape Act): an "Added Aghanim's Scepter." card has its ability's header (Active, range,
    mana, cooldown); an upgrade that swaps the cooldown for charges shows the charge restore time there instead."""
    from patch.cards_aghs import _added_upgrade_head
    text = ("Escape Act has 2 charges. When the box pops open, Impalement Art daggers are thrown in all directions, and "
            "all enemies in an 225 radius take 300 damage. Cooldown: -100%. Charge restore time: 38/32/26/20s.")
    body, head = _added_upgrade_head("ringmaster_the_box", "7.37e", text)
    assert "Cooldown" not in body and "Charge restore" not in body and body.endswith("300 damage.")
    assert '<b class="iab-kind">Active</b>' in head
    assert all(v in head for v in (">600<", ">80<", ">38/32/26/20<"))


def test_an_enemy_damage_reflection_stays_higher_is_better():
    assert "l=True" not in g._emit_badge("Damage reflected increased from 10% to 12%")


def test_a_card_row_with_its_own_badges_gets_the_hover_ruler_class():
    """Owner 2026-10-29 (7.38 Ice Breaker): a card row's % sit at its right edge and the row has the list rows' dashed
    hover ruler — a build-time class, no CSS :has() on patch pages."""
    from patch.static_has import add_static_has_classes
    html = ('<div class="ability-change-row">Path Duration <span class="badge-group"><span class="badge">+1</span>'
            '</span></div><div class="ability-change-row">no badges</div>')
    out = add_static_has_classes(html)
    assert out.count("acr-bg") == 1 and out.startswith('<div class="ability-change-row acr-bg">')


def test_removed_facets_are_facet_blocks_and_a_removed_innate_is_its_own_block():
    """Owner 2026-10-29 (7.38 Invoker, "где картинки фасетов? Mastermind вообще innate"): each removed facet is its own
    block (icon, name, "Removed" row) before the hero's new facets, as 7.39 does; a removed innate is its block first in
    Abilities; a GENERAL list left empty goes. Names from the game files of 7.37e."""
    ul = ['W(ul_open())', 'W(li("Removed", t("DEL")))', 'W(ul_close())']
    lines = [
        'W(hero_header("Invoker"))', 'W(ul_open())', 'W(li("Base Intelligence increased from 19 to 20", b(19, 20)))',
        'W(li("Removed Mastermind ability", t("DEL")))', 'W(li("Removed Agnostic and Elitist Facets", t("DEL")))',
        'W(ul_close())', 'W(new_facet("invoker_quas_focus", desc=[]))', 'W(ability("Quas", slug="invoker_quas"))',
        'W(hero_header("Chaos Knight"))', 'W(ul_open())', 'W(li("Removed Phantasmagoria Facet", t("DEL")))',
        'W(ul_close())', 'W(ability("Chaos Bolt", slug="chaos_knight_chaos_bolt"))',
    ]
    out = g._postprocess_removed_facets(lines, "7.38")
    assert out == [
        'W(hero_header("Invoker"))', 'W(ul_open())', 'W(li("Base Intelligence increased from 19 to 20", b(19, 20)))',
        'W(ul_close())', 'W(facet_header("invoker_agnostic"))', *ul, 'W(facet_header("invoker_elitist"))', *ul,
        'W(new_facet("invoker_quas_focus", desc=[]))',
        'W(ability("Mastermind", slug="invoker_mastermind", innate=True))', *ul,
        'W(ability("Quas", slug="invoker_quas"))',
        # a facet that grants an ability is named by it: Phantasmagoria = chaos_knight_strong_illusions
        'W(hero_header("Chaos Knight"))', 'W(facet_header("chaos_knight_strong_illusions"))', *ul,
        'W(ability("Chaos Bolt", slug="chaos_knight_chaos_bolt"))',
    ]
