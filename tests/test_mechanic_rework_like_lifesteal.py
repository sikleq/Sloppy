"""7.40 Invulnerability Targeting "like 7.38 Lifesteal" (owner 2026-10-27): a "Reworked mechanic" with REWORK rows in
one list, the changed spells in the row's (?), a note on one spell in brackets after it, no row restating the header."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import generate_patch_code_v2 as gen  # noqa: E402


def test_the_rule_its_list_and_special_cases_are_rework():
    assert gen._guess_tag("Most items and abilities that previously could target and/or affect invulnerable units "
                          "no longer do so") == "REWORK"
    assert gen._guess_tag("The following spells have been changed") == "REWORK"
    assert gen._guess_tag("Since Cyclone effects also make the unit invulnerable, all changes mentioned above apply "
                          "to them as well. As a result, there are these special cases") == "REWORK"


def test_a_row_restating_the_header_goes_and_the_mechanic_is_one_list():
    rows = ['W(plain_header("Invulnerability Targeting"))', 'W(ul_open())',
            'W(li("Invulnerability targeting rules of certain items and abilities have been updated", t("MISC")))',
            'W(li("Most items and abilities that previously could target and/or affect invulnerable units no longer '
            'do so", t("REWORK")))',
            'W(li("The following spells have been changed", t("REWORK")))', 'W(ul_close())', 'W(ul_open())',
            'W(li("Since Cyclone effects also make the unit invulnerable. As a result, there are these special cases", '
            't("REWORK")))', 'W(ul_close())', 'W(section("Item Updates"))']
    out = gen._postprocess_mechanic_rules_row(rows)
    out = gen._postprocess_mechanic_rules_row(gen._postprocess_new_block_label(out), after_label=True)
    assert out[0] == 'W(plain_header("Invulnerability Targeting", new="Reworked mechanic"))'
    assert not any("rules of certain" in line for line in out)
    assert out.count('W(ul_open())') == 1 and out.count('W(ul_close())') == 1


def test_the_following_spells_row_joins_the_row_above():
    """7.40: "… no longer do so. The following spells have been changed" in one line (owner 2026-10-28)."""
    rows = ['W(plain_header("Invulnerability Targeting", new="Reworked mechanic"))', 'W(ul_open())',
            'W(li("Most items no longer do so", t("REWORK")))',
            'W(li("The following spells have been changed", t("REWORK"), extra=inline_note("A<br>B")))',
            'W(ul_close())']
    out = gen._postprocess_mechanic_rules_row(rows, after_label=True)
    assert out[2] == ('W(li("Most items no longer do so. The following spells have been changed", t("REWORK"), '
                      'extra=inline_note("A<br>B")))')
    assert len(out) == 4


def test_a_list_the_row_introduces_is_an_inline_list():
    """7.38 Lifesteal "…consistent across every ability:" + its rules -> inline_list (open as a table in a Reworked
    mechanic, owner 2026-10-28); a row of clarifications (7.38 Tormentor) keeps inline_note."""
    listed = [{"note": "Lifesteal mechanics are now consistent across every ability:", "indent_level": 1},
              {"note": "Lifesteal applies to physical damage from attacks", "indent_level": 2},
              {"note": "Neither applies to pure damage", "indent_level": 2}]
    lines, _ = gen._emit_notes(listed, general=True)
    row = next(x for x in lines if x.startswith("W(li("))
    assert "extra=inline_list(" in row and "every ability:" not in row
    # a hero's / item's list keeps inline_note: the rule stays in General Updates (owner 2026-10-28)
    lines, _ = gen._emit_notes(listed)
    assert "extra=inline_note(" in next(x for x in lines if x.startswith("W(li("))
    plain = [{"note": "Tormentor is also dependent on the day and night cycle", "indent_level": 1},
             {"note": "Or at Dire side in Turbo", "indent_level": 2}]
    lines, _ = gen._emit_notes(plain, general=True)
    row = next(x for x in lines if x.startswith("W(li("))
    assert "extra=inline_note(" in row


def test_a_note_on_a_listed_spell_goes_in_brackets_and_all_three_gets_its_own_line():
    notes = [{"note": "Heroes", "indent_level": 2},
             {"note": "Ogre Magi's Bloodlust can no longer target invulnerable units", "indent_level": 3},
             {"note": "Can still target invulnerable buildings (i.e. Tier 2-4 towers)", "indent_level": 4},
             {"note": "Sniper's Assassinate can no longer target invulnerable units", "indent_level": 3}]
    text = gen._nested_info_text(notes, 1, range(4))
    assert ("Ogre Magi's Bloodlust can no longer target invulnerable units <span class=\"pop-note\">(Can still target "
            "invulnerable buildings, i.e. Tier 2-4 towers)</span>") in text
    assert text.count("&nbsp;&nbsp;– ") == 2
    notes = [{"note": "Nullifier's Nullify will dispel Cyclone", "indent_level": 2},
             {"note": "Sven's Storm Hammer will dispel Cyclone", "indent_level": 2},
             {"note": "All three of these will also dispel Cyclone if …", "indent_level": 3}]
    text = gen._nested_info_text(notes, 1, range(3))
    assert text.endswith('<br><span class="pop-note">All three of these will also dispel Cyclone if …</span>')
