"""Proofread of 7.37b (2026-10-30), each rule in the generator so the next patch gets it too."""
import pytest

import tools.generate_patch_code_v2 as g


@pytest.mark.parametrize("text, tag", [
    ("Hookshot: Now refunds Clockwerk 75% of the mana spent", "NEW"),
    ("Enchant: Now also increases attack range for units under Enchantress' control against the target", "NEW"),
    ("Scurry: Now increases duration to 3.5/4/4.5/5s", "NEW"),
    ("Burning Spear: Duration is no longer reduced", "BUFF"),
    ("Can now be cast during channeling and does not break invisibility", "NEW"),
    ("Level 15 Talent All Stats per hero hit with Reverse Polarity now stacks instead of refreshing", "NEW"),
    ("100% of bonus damage is converted to base damage for Phantom Lancer. Phantom Lancer illusions still convert 65% "
     "of the bonus damage", "BUFF"),
    ("Trample: Now provides +10% Self Bonus Move Speed when activated", "NEW"),
    ("Stun Duration now increases by 0.2s per ally in Snowball", "NEW"),
    ("Now counts one debuff per unique ability/item (e.g. Shiva's Guard will count as 1 debuff instead of 3)", "NERF"),
    ("Bonus damage is now decreased by the illusion damage reduction amount if applied by illusions", "NERF"),
    ("Death Ward: Now has a primary and secondary target", "NEW"),
])
def test_7_37b_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


def test_less_time_to_reach_the_max_is_lower_is_better():
    assert "l=True" in g._emit_badge("Time to max damage/attack speed decreased from 8s to 6s (total duration unchanged)")


def test_a_hero_note_named_after_a_facet_of_that_patch_goes_under_the_facet():
    """7.37b "Elitist: Exort: Spell Amplification …" — Elitist was Invoker's facet (not in badges.FACETS: removed in
    7.38); it became an innate ability block."""
    out = "\n".join(g._render_hero({"hero_id": 74, "hero_notes": [
        {"indent_level": 1, "note": "Elitist: Exort: Spell Amplification per instance increased from 2/3% to 3/4%"}]},
        version="7.37b"))
    assert 'W(facet_header("invoker_elitist"))' in out
    assert "innate=True" not in out


def test_an_ability_innate_in_its_own_patch_is_marked_innate():
    """7.37b Viper's Predator and Ursa's Maul were innates (KV "Innate" "1" of that build); the block said nothing."""
    out = "\n".join(g._render_hero({"hero_id": 47, "abilities": [{"ability_id": next(
        k for k, v in g.ABILS.items() if v[1] == "viper_predator"), "ability_notes": [
        {"indent_level": 1, "note": "Bonus damage is now decreased by the illusion damage reduction amount"}]}]},
        version="7.37b"))
    assert 'W(ability("Predator", slug="viper_predator", innate=True))' in out


def test_a_value_of_the_new_secondary_target_goes_in_the_rows_question_mark():
    """Owner 2026-10-30 (7.37b Death Ward): "Damage to secondary target is equal to 65% of the primary" is not a row of
    its own — it goes in the "?" of "Now has a primary and secondary target", even with another row between them."""
    body, _ = g._emit_notes([
        {"indent_level": 1, "note": "Death Ward: Damage to primary target increased from 45/70/95 to 55/90/125"},
        {"indent_level": 1, "note": "Death Ward: Now has a primary and secondary target"},
        {"indent_level": 1, "note": "Death Ward: Damage to secondary target is equal to 65% of the primary"}])
    rows = [ln for ln in body if ln.startswith("W(li(")]
    assert len(rows) == 2
    assert ('W(li("Death Ward: Now has a primary and secondary target", t("NEW"), '
            'extra=inline_note("Damage to secondary target is equal to 65% of the primary")))') in rows


def test_the_validator_reads_a_negated_direction():
    from tools.validate_data import _check_change
    issues = []
    _check_change({"name": "Huskar"}, {"text": "Burning Spear: Duration is no longer reduced", "tag": "buff"}, issues)
    assert issues == []
