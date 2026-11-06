"""The generator drafts what the 7.39 review fixed by hand (owner 2026-10-27: "is every fix also in the generator?")."""
import tools.generate_patch_code_v2 as g


def test_ability_level_rescale_becomes_a_formula_table():
    out = g._postprocess_ability_level_formula(
        ['W(li("Aftershock: Radius increase rescaled from (+50 with every 10 hero levels) to (+40 with every level of '
         'Echo Slam)", t("REWORK")))'], "7.39")
    text = "\n".join(out)
    assert text.startswith('W(li_formula("Aftershock: Radius increase rescaled"')
    assert "lambda L: 50 * (L // 10)" in text and "(L - 6) // 6 + 1" in text      # Echo Slam is an ultimate: 6/12/18
    assert 'label="Hero level"' in text


def _block(name, slug, *rows):
    return [f'W(ability("{name}", slug="{slug}"))', "W(ul_open())", *rows, "W(ul_close())"]


def test_an_ability_that_became_innate_gets_its_card():
    out = g._postprocess_innate_cards(_block("Blur", "phantom_assassin_blur",
                                             'W(li("Now is an innate ability that improves with Coup de Grace level", '
                                             't("REWORK")))',
                                             'W(li("Now dispelled when attacking Roshan or enemy Barracks", t("NERF")))'),
                                      "7.39")
    text = "\n".join(out)
    assert 'summary="Now is an innate ability."' in text
    assert 'game_ability_desc("phantom_assassin_blur", "7.38c")' in text and "innate=True" in text
    assert 'Coup de Grace level", t("REWORK"), covered=True))' in text
    assert 'Barracks", t("NERF")))' in text                                       # its own change stays a row


def test_a_reworked_innate_gets_its_card_but_a_renamed_mechanic_does_not():
    out = g._postprocess_innate_cards(_block("Outfight Them!", "legion_commander_outfight_them",
                                             'W(li("Now levels up with Duel", t("REWORK")))'), "7.39")
    assert 'summary="Innate reworked."' in "\n".join(out)
    out = g._postprocess_innate_cards(_block("Withering Mist", "abaddon_withering_mist",
                                             'W(li("Instead of reducing Healing, Health Regen, Lifesteal, and Spell '
                                             'Lifesteal by 35%, now reduces Health Restoration by 35%", t("MISC")))'),
                                      "7.39")
    assert "ability_change" not in "\n".join(out)
