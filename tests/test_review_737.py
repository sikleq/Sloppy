"""Proofread of 7.37 (2026-10-30) — the innate rework patch; each rule in the generator so the next patch gets it too."""
import pytest

import tools.generate_patch_code_v2 as g


@pytest.mark.parametrize("text, tag", [
    ("No longer an innate ability", "REWORK"),
    ("Starting from his second death, Roshan now always drops Roshan's Banner", "NEW"),
    ("The following are now Fully Disabled by Break", "NERF"),
    ("Fade no longer requires the target to remain still", "BUFF"),
    ("Returning as a Tier 1 Neutral item", "NEW"),
    ("Now is a Tier 3 Neutral item", "REWORK"),
    ("No longer procs Magic Stick", "BUFF"),
    ("Now procs Magic Stick", "NERF"),
    ("Illusory Orb: Now shows a preview of the orb trajectory", "QoL"),
    ("Can now be put on alt-cast to only pull Tusk towards his target ally", "NEW"),
    ("New Facet", "NEW"),
])
def test_7_37_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


def test_every_value_negative_compares_the_sizes():
    """"Armor Corruption decreased from -4 to -3": a weaker armor reduction — a nerf, as Valve's word says."""
    assert g._emit_badge("Level 20 Talent Armor Corruption decreased from -4 to -3") == "b(4, 3)"
    assert g._normalize_note_text("Level 20 Talent Armor Corruption decreased from -4 to -3")["tag"] == "nerf"


def test_a_row_without_from_still_has_its_badge():
    assert g._emit_badge("Damage increase per armor decreased 0.3% to 0.25%") == "b(0.3, 0.25)"
    assert g._emit_badge("Split Amount rescaled 80/85/90/95/100% to 85/90/95/100%") == \
        "b([80, 85, 90, 95, 100], [85, 90, 95, 100])"


def test_a_new_innate_block_becomes_the_old_to_new_card_and_the_removed_block_goes():
    lines = ['W(hero_header("Abaddon"))',
             'W(ability("Font of Avernus", slug="abaddon_font_of_avernus", innate=True))', 'W(ul_open())',
             'W(li("Ability removed", t("DEL")))', 'W(ul_close())',
             'W(ability("Withering Mist", slug="abaddon_withering_mist", innate=True))', 'W(ul_open())',
             'W(li("New Innate ability. Passive, can\'t be leveled up", t("MISC")))', 'W(ul_close())']
    out = "\n".join(g._postprocess_new_innate_cards(lines, "7.37"))
    assert 'old=dict(name="Font of Avernus", slug="abaddon_font_of_avernus"' in out
    assert 'new=dict(name="Withering Mist", slug="abaddon_withering_mist", innate=True' in out
    assert 'summary="New innate ability."' in out and 'tag="new"' in out
    assert "Ability removed" not in out and "covered=True" in out


def test_a_new_basic_ability_block_becomes_the_new_ability_card():
    lines = ['W(hero_header("Medusa"))', 'W(ability("Gorgon\'s Grasp", slug="medusa_gorgon_grasp"))', 'W(ul_open())',
             'W(li("New basic ability.", t("MISC")))', 'W(ul_close())']
    out = g._postprocess_new_innate_cards(lines, "7.37")
    assert out[1] == 'W(new_ability("Gorgon\'s Grasp", "medusa_gorgon_grasp", version="7.37"))'


def test_an_old_innates_level_0_value_leaves_the_comparison():
    """7.36 innates had a value at level 0 (5 values); as a basic ability in 7.37 they have 4 levels."""
    lines = ['W(hero_header("Anti-Mage"))', 'W(ability("Mana Break", slug="antimage_mana_break"))', 'W(ul_open())',
             'W(li("Mana Burned per hit rescaled from 16/23/30/37/44 to 25/30/35/40", '
             'b([16, 23, 30, 37, 44], [25, 30, 35, 40])))', 'W(ul_close())']
    out = g._postprocess_innate_level0(lines, "7.37")
    assert "b([23, 30, 37, 44], [25, 30, 35, 40])" in out[3]


def test_a_new_facet_row_becomes_the_new_facet_card():
    lines = ['W(facet_header("medusa_slow_attacks"))', 'W(ul_open())', 'W(li("New Facet", t("NEW")))',
             'W(li("Medusa applies a poison to every fifth attack", t("MISC")))', 'W(ul_close())']
    assert g._postprocess_new_facet_rows(lines) == [
        'W(new_facet("medusa_slow_attacks", desc=["Medusa applies a poison to every fifth attack"]))']


def test_a_reworked_facets_old_pane_is_its_text_of_the_patch_before():
    """7.37 Ferocity / Voidblades: the card's old side said "TODO" — the visual check saw it on the page. The facet's
    text of 7.36c with its number ({s:bonus_roared_bonus_aoe_pct} = 10)."""
    from patch.aghs_text import facet_text
    assert facet_text("primal_beast_ferocity", "7.36c") == \
        "When activated, Uproar provides 10% increased area of effect per stack."
    card = "\n".join(g._facet_card("primal_beast_ferocity", "hero_facet ReworkedFacet",
                                   ['W(li("Pulverize: Now provides 20% AoE increase", t("NEW")))'], "7.37"))
    assert "TODO" not in card and "Uproar provides 10% increased area" in card


def test_no_page_keeps_the_old_facet_placeholder():
    from pathlib import Path
    pages = Path(__file__).resolve().parents[1].glob("content/p*.py")
    left = [p.name for p in pages if "TODO: the facet as it was in the previous patch" in p.read_text(encoding="utf-8")]
    assert left == []


def test_two_lists_back_to_back_become_one():
    lines = ['W(ul_open())', 'W(li("a"))', 'W(ul_close())', 'W(ul_open())', 'W(li("b"))', 'W(ul_close())']
    assert g._merge_adjacent_lists(lines) == ['W(ul_open())', 'W(li("a"))', 'W(li("b"))', 'W(ul_close())']


def test_a_facet_prefix_with_the_word_facet_and_an_old_abilitys_real_slug():
    """"Cold Comfort Facet: Blueheart Floe: …" is the facet Cold Comfort; "Selemene's Favor: Ability removed" is the
    7.36 innate luna_selemenes_favor (from the files), not a made-up luna_selemene_s_favor."""
    cm = "\n".join(g._render_hero({"hero_id": 5, "hero_notes": [{"indent_level": 1, "note":
         "Cold Comfort Facet: Blueheart Floe: Now also increases mana regen amplification from 50% to 75%"}]},
         version="7.37"))
    assert 'facet_header("crystal_maiden_cold_comfort")' in cm and "Cold Comfort Facet" not in cm
    luna = "\n".join(g._render_hero({"hero_id": 48, "hero_notes": [
        {"indent_level": 1, "note": "Selemene's Favor: Ability removed"}]}, version="7.37"))
    assert 'slug="luna_selemenes_favor"' in luna
