"""Second proofread of 7.38 (2026-11-02), each tag rule in the generator so the next patch gets it too."""
from patch.css_bundle import read_css
import glob
import os
import re

import pytest

import tools.generate_patch_code_v2 as g

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _p738():
    with open(os.path.join(ROOT, "content", "p738.py"), encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize("text, tag", [
    ("Vision Radius is now affected by changes to Area of Effect", "NEW"),
    ("All sources of evasion are doubled for the duration, including Redirect Chance from Mistwoods Wayfarer", "NEW"),
    ("Secondary shot now prioritizes heroes, then non-hero units, then buildings", "NEW"),
    ("Tricks of the Trade: When Riki kills a non-hero unit during Tricks of the Trade, the cooldown is reduced by 0.75s",
     "NEW"),
    ("Backstab: Riki also gets 25/75/125/175 bonus experience for courier and ward kills", "NEW"),
    ("Succubus: Now also makes Spell Lifesteal apply to reflected Magical and Pure Damage", "NEW"),
    ("Compared to previous iterations, ability duration can now be decreased by Status Resistance or increased by "
     "Debuff Duration bonuses", "NEW"),
    ("Now Talent Tree's All Attribute bonus provides an additional +3 to Morphling's primary attribute", "NEW"),
    ("Improved Glaive collision behavior for orbiting Glaives", "QoL"),
    ("Can now be put on autocast so Clinkz will throw a tar bomb when attacking, if the ability is available", "QoL"),
])
def test_7_38_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


@pytest.mark.parametrize("text, tag", [
    ("Strike Damage is now classified as reflection damage", "REWORK"),
    ("Quill Sprays that were released by the ability now deal damage that is classified as reflection damage", "REWORK"),
    ("Affected units no longer take increased magical and pure damage bonus from Winter Wyvern by default", "DEL"),
    ("Skill points can now be spent on All Attributes starting at level 2 instead of level 6", "REWORK"),
    ("Hookshot: Now requires at least one other allied hero to be within a 350 radius of the Hookshot target", "NEW"),
])
def test_the_owners_answers_on_7_38(text, tag):
    assert g._guess_tag(text) == tag
    row = re.search(re.escape(text) + r'", t\("(\w+)"\)', _p738())
    assert row and row.group(1) == tag


def test_arc_wardens_same_effect_is_rework_on_its_cards():
    # the row became the summary of a card (owner 2026-11-05): patch/two_selves.py writes the tag
    from patch.two_selves import SAME_EFFECT
    assert g._guess_tag(SAME_EFFECT) == "REWORK"


def test_a_hero_has_his_facets_then_his_abilities_on_every_page():
    # owner 2026-11-02, 7.38 Morphling: "сначала способность, потом фасеты, потом опять способности. Это неправильно"
    for path in glob.glob(os.path.join(ROOT, "content", "p7*.py")):
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        assert g._postprocess_facets_first(lines) == lines, path


def test_the_generator_writes_a_heroes_facets_before_his_innate_block():
    src = g.generate("7.38")
    morphling = src[src.index('hero_header("Morphling")'):]
    assert morphling.index('facet_header("morphling_agi")') < morphling.index('ability("Accumulation"')


def test_facets_first_keeps_the_rest_in_order_and_leaves_owned_abilities_alone():
    lines = ['W(hero_header("X"))', 'W(ul_open())', 'W(ul_close())', 'W(ability("Innate", slug="x_i", innate=True))', 'W(ul_open())',
             'W(ul_close())', 'W(facet_header("x_f"))', 'W(ul_open())', 'W(ul_close())', 'W(ability("Q", slug="x_q"))',
             'W(subgroup("Talents"))', '# Y', 'W(hero_header("Y"))']
    out = g._postprocess_facets_first(lines)
    order = [ln for ln in out if "facet_header" in ln or "W(ability" in ln]
    assert order == ['W(facet_header("x_f"))', 'W(ability("Innate", slug="x_i", innate=True))', 'W(ability("Q", slug="x_q"))']
    assert out[-3:] == lines[-3:]
    owned = ['W(hero_header("I"))', 'W(ability("Q", slug="q", sub=True))', 'W(facet_header("f"))', 'W(hero_header("J"))']
    assert g._postprocess_facets_first(owned) == owned


def test_a_facet_improving_an_ability_is_one_row():
    lines = ['W(li("Now is a facet that improves Succubus", t("NEW")))',
             'W(li("Succubus: Now also makes Spell Lifesteal apply", t("MISC"), extra=inline_note("x")))']
    assert g._postprocess_facet_improves_row(lines) == [
        'W(li("Now is a facet that improves Succubus: also makes Spell Lifesteal apply", t("NEW"), extra=inline_note("x")))']
    assert "Now is a facet that improves Succubus: also makes" in _p738()


def test_succubus_card_says_the_old_numbers_and_shows_the_new_ones():
    src = _p738()
    assert "Minimum lifesteal: 12%. Maximum lifesteal: 18%." in src
    assert 'hl("2%", "nerf")' in src and 'hl("14%", "nerf")' in src
    assert 'li("Spell Lifesteal decreased from 12-18% to 2-14%", br(12, 18, 2, 14), covered=True)' in src
    assert 'desc=game_ability_desc("queenofpain_succubus"' not in src


def test_the_generator_covers_a_row_its_innate_card_shows():
    src = g.generate("7.38")
    assert re.search(r'li\("Spell Lifesteal decreased from 12-18% to 2-14%".*covered=True\)', src)
    assert "TODO[old-values]" in src
    assert g._row_values_in_text('W(li("Damage increased from 5 to 9", t("BUFF")))', "Deals 3 damage") is False


def test_precision_aura_is_a_table_by_hero_level():
    src = _p738()
    assert 'li_formula("Self Agility percentage bonus rescaled", "2% per hero level", "4/8/12/16% + 1% per level"' in src
    assert 'li_formula("Self Agility percentage bonus rescaled", "2% per hero level", "4/8/12/16% + 1% per level"' in g.generate("7.38")
    assert "tag_levels=range(1, 31)" in src and "tag_levels=range(1, 31)" in g.generate("7.38")


def test_precision_auras_tag_counts_every_hero_level_not_only_the_shown_columns():
    # owner 2026-11-02: NERF. 5% against 2% at level 1 is +150%, one of nine columns made the row BUFF; over all 30 levels -1.75%
    from patch.formula_rows import li_formula
    shown = [1, 5, 6, 11, 12, 17, 18, 25, 30]

    def row(**kw):
        return li_formula("Bonus rescaled", "2% per hero level", "4/8/12/16% + 1% per level", lambda L: 2 * L,
                          lambda L: [4, 8, 12, 16][0 if L < 6 else min(3, (L - 6) // 6 + 1)] + L,
                          levels=shown, label="Hero level", value_fmt="{:g}%", **kw)
    assert 'data-tag="buff"' in row()
    html = row(tag_levels=range(1, 31))
    assert 'data-tag="nerf"' in html and 'data-tag="buff"' not in html
    assert "150%" in html and "-23%" in html                      # the badges still show the start and the end
    head = html[html.index("<thead>"):html.index("</thead>")]
    assert len(re.findall(r"<th[ >]", head)) == len(shown) + 1    # the table keeps its columns


def test_a_row_about_an_ability_whose_slug_its_name_does_not_spell_gets_the_icon():
    from patch.cards_rows import _lead_ability_chip
    from patch.state import _State
    _State.current_hero, _State.current_patch_version = "ringmaster", "7.38"
    chips, rest = _lead_ability_chip("Unicycle: After a 0.5s preparation, Ringmaster mounts a speedy unicycle")
    assert "ringmaster_summon_unicycle.png" in chips[0] and rest.startswith("After a 0.5s")


def test_runes_named_in_a_card_row_get_their_icons():
    from patch.mech_abilities import rune_name_chips
    out = rune_name_chips("Level 3 - Invisibility, Arcane and Haste Runes")
    for key in ("invisibility", "arcane", "haste"):
        assert f"icons/runes/{key}.png" in out
    # a list: the icons alone by commas, the names on hover (owner 2026-11-06)
    assert "Runes" not in out.replace('Rune"', "") and out.count("</span>, <span") == 2
    assert 'data-tooltip="Haste Rune"' in out
    one = rune_name_chips("Level 1 - Invisibility Rune")
    assert one.startswith("Level 1 - <span") and one.endswith("</span>")
    # inside a sentence too (owner 2026-11-06, 7.41 Runic Infusion); "or" stays, "and" is a comma
    inside = rune_name_chips("Infused with the bonuses of Power Runes for 10s")
    assert "icons/runes/power.png" in inside and inside.endswith("</span> for 10s") and "Power Runes" not in inside
    either = rune_name_chips("Duration is reduced by 33% for activating Bounty or Water Runes.")
    assert "</span> or <span" in either and either.endswith("</span>.") and "Water Runes" not in either
    assert rune_name_chips(inside) == inside                              # a second pass changes nothing
    buff = rune_name_chips("Arc Warden gains the Regeneration Rune buff for 4s")
    assert 'data-tooltip="Regeneration Rune"' in buff and "</span> buff for 4s" in buff
    plain = "Tornado pulls enemies. Any rune nearby"
    assert rune_name_chips(plain) == plain
    note = "Text<!--TIP-->Automatic Regeneration Rune effect<!--/TIP-->"
    assert rune_name_chips(note) == note


@pytest.mark.parametrize("text", [
    "Vision Radius is now affected by changes to Area of Effect",
    "All sources of evasion are doubled for the duration, including Redirect Chance from Mistwoods Wayfarer",
    "Secondary shot now prioritizes heroes, then non-hero units, then buildings",
    "Improved Glaive collision behavior for orbiting Glaives",
])
def test_the_page_carries_the_tag_the_generator_gives(text):
    row = re.search(re.escape(text) + r'", t\("(\w+)"\)', _p738())
    assert row and row.group(1) == g._guess_tag(text)


@pytest.mark.parametrize("left", [
    "Accumulation:", "Ruin and Restoration:", "Tar Bomb:",
])
def test_a_note_named_after_an_ability_sits_in_that_ability_block(left):
    assert f'li("{left}' not in _p738()


def test_the_blocks_those_notes_moved_to_exist():
    src = _p738()
    assert 'ability("Accumulation", slug="morphling_accumulation", innate=True)' in src
    assert 'ability("Ruin and Restoration", slug="skywrath_mage_ruin_and_restoration", innate=True)' in src
    assert 'ability("Tar Bomb", slug="clinkz_tar_bomb")' in src


def test_a_basic_ability_turned_innate_is_a_card():
    src = _p738()
    assert 'summary="Now is an innate ability."' in src
    assert 'li("Now is an innate ability", t("REWORK"), covered=True)' in src


def test_valves_whole_sentence_about_blocked_camps():
    assert "attempting to stack that camp will not create another Ancient creep" in _p738()


def test_every_damage_at_level_30_range_row_shows_its_percent():
    bare = re.findall(r'li\("Damage at level 30 [^"]*\(from \d+-\d+ to \d+-\d+\)", t\(', _p738())
    assert not bare


def test_a_chips_hidden_name_takes_no_width():
    # opacity 0 keeps its width: in the Lifesteal tables by the right edge it widened a 375 px page to 401 px
    css = read_css()
    assert re.search(r"\.ability-chip\[data-tooltip\]:not\(:hover\)::after \{ display: none; \}", css)


def test_a_long_card_header_wraps_on_a_phone():
    # 7.38 Demonic Cleanse "Active – granted by Shard, shares level with Demonic Purge" made a 375 px page 471 px wide
    # 2026-11-06: the title wraps everywhere (the values stay on the first line); on a phone the values may go under it
    css = read_css()
    assert ".iab-title { white-space: normal;" in css
    assert re.search(r"@media \(max-width: 640px\) \{ \.iab-head \{ flex-wrap: wrap; \} \}", css)
