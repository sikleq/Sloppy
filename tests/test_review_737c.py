"""Proofread of 7.37c (2026-10-29), each rule in the generator so the next patch gets it too."""
import pytest

import tools.generate_patch_code_v2 as g


@pytest.mark.parametrize("text, tag", [
    # owner 2026-10-29: NEW, not BUFF
    ("No longer requires Enchant Totem to be leveled to be active", "NEW"),
    ("Multicasts now prioritize Ogre Magi himself, followed by heroes, then buildings, then creeps, skipping units that "
     "already have the buff", "NEW"),
    ("Bonus Agility is now applied during the rush as well as the 1.5s after it ends", "NEW"),
])
def test_7_37c_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


def test_a_hero_note_named_after_a_basic_ability_goes_in_its_block():
    """7.37c Tinker "Defense Matrix: Cast Range decreased …" sat among the hero's general rows; Defense Matrix was one of
    his abilities that patch, so the rows go in its own block (as 7.37d's innate Duelist)."""
    out = "\n".join(g._render_hero({"hero_id": 34, "hero_notes": [
        {"indent_level": 1, "note": "Base Mana Regen decreased from 0.75 to 0.5"},
        {"indent_level": 1, "note": "Defense Matrix: Cast Range decreased from 700/750/800/850 to 700"}]},
        version="7.37c"))
    assert 'W(ability("Defense Matrix", slug="tinker_defense_matrix"))' in out
    assert 'W(li("Cast Range decreased from 700/750/800/850 to 700"' in out


def test_the_from_audit_takes_a_left_out_hero_value_from_the_patchs_base_hero():
    """7.37c Dawnbreaker "Base Health Regen increased from 0.25 to 0.5": 7.37b's Dawnbreaker had no own value, so the
    0.25 of npc_dota_hero_base; a hero absent from the patch (Ringmaster in 7.37b) stays unknown."""
    from tests.test_fixes_1022 import _from_audit
    a = _from_audit()
    assert (0.25,) in a._base_values("7.37b", "dawnbreaker")
    assert not a._base_values("7.37b", "ringmaster")


def test_an_auto_registered_facet_takes_the_game_files_colour():
    """Valve's web feed gave Convergence "Yellow0"; npc_heroes.txt of every 7.37 build says Yellow + GradientID 1."""
    from patch.ability_kv import hero_facets
    from patch.badges import FACETS
    assert hero_facets("phantom_lancer", "7.37c")["phantom_lancer_convergence"][1] == "Yellow1"
    assert FACETS["phantom_lancer_convergence"] == ("Convergence", "Yellow1")
    assert FACETS["earthshaker_slugger"][0] == "Slugger"      # the feed's title said "Slugger Facet"
