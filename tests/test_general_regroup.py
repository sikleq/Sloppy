"""General Updates regrouping (owner 2026-10-16, 7.41 Global Changes): topic subgroups ("Scaling with Hero Level",
"Lane Creeps") for topics with two rows or more, "<X> removed from the game" as the section's intro line, and Valve's
follow-up "All <same subject> …" sentence as the "?" of the row before it."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generate_patch_code_v2 as g  # noqa: E402

SIEGE = "W(li(\"First +1 siege creep timing decreased from 35:00 to 30:00\", t(\"REWORK\"), also_dyn=['unit|goodguys-siege']))"
FLAG = ("W(li(\"Flagbearer Creep Experience Bounty increased from 57 to 60\", b(57, 60), "
        "also_dyn=['unit|creep-goodguys-flagbearer']))")
CURRENTS = 'W(li("All sections of currents now give a max movement speed bonus of 150", t("BUFF")))'
FACETS = 'W(li("Facets removed from the game", t("DEL")))'
INNATE = 'W(li("Innate abilities no longer scale with other abilities\' level", t("REWORK")))'
UI = 'W(li("Added UI icon that shows which parameters increase with hero level", t("QoL")))'
LANES = ['W(ul_open())', FACETS, INNATE, UI, 'W(ul_close())', 'W(ul_open())', SIEGE, FLAG, 'W(ul_close())',
         'W(ul_open())', CURRENTS, 'W(ul_close())']


MEET = ("W(li(\"Adjusted the meeting point of the lane creeps toward the offlane\", t(\"MISC\"), "
        "also_dyn=['unit|creep-goodguys-melee', 'unit|creep-goodguys-ranged']))")
SIEGE2 = "W(li(\"Second +1 siege creep timing now occurs at 60:00\", t(\"REWORK\"), also_dyn=['unit|goodguys-siege']))"


def test_topics_become_subgroups_and_the_lead_a_major_row():
    out = g._general_topics(LANES + ['W(ul_open())', MEET, 'W(ul_close())'], "Global Changes")
    assert out[1] == 'W(li("Facets removed from the game", t("DEL"), major=True))'   # stand-out, tag kept
    s, l = out.index('W(subgroup("Scaling with Hero Level"))'), out.index('W(subgroup("Lane Creeps"))')
    assert out.index(CURRENTS) < s < l                                  # a row of no topic stays on top
    assert out[s + 2:s + 4] == [INNATE, UI]
    assert out[l + 2] == MEET                                           # a row about several creeps
    f = out.index('W(unit_header("Flagbearer Creep", "../icons/units/npc_dota_creep_goodguys_flagbearer.png", '
                  'general=False))')
    assert out[f + 2].startswith('W(li("Experience Bounty increased from 57 to 60"')   # its name prefix goes
    assert l < f and any(x.startswith('W(unit_header("Siege Creep"') for x in out[f:])   # cards after the subgroups
    assert 'W(ul_open())\nW(ul_close())' not in "\n".join(out)          # emptied blocks are gone


def test_first_and_second_rows_become_one():
    out = g._merge_ordinal_pair([SIEGE, SIEGE2])
    assert len(out) == 1
    assert g._li_parts(out[0])[0] == ("First +1 siege creep timing decreased from 35:00 to 30:00, "
                                      "second now occurs at 60:00")
    assert "t(\"REWORK\")" in out[0] and "goodguys-siege" in out[0]


def test_a_lone_topic_row_stays_and_map_sections_are_left_alone():
    one = ['W(ul_open())', SIEGE, CURRENTS, 'W(ul_close())']
    assert g._general_topics(one, "Global Changes") == one
    assert g._general_topics(LANES, "Map Changes") == LANES


def test_a_clock_time_timing_is_rework():
    assert g._guess_tag("Second +1 siege creep timing now occurs at 60:00") == "REWORK"


def test_all_followup_goes_into_the_rows_note():
    rows = ['W(li("Innate abilities no longer scale with other abilities\' level", t("MISC")))',
            'W(li("All innate abilities that used to scale with other abilities now improve on \'per level\' basis", '
            't("MISC"), extra=inline_note("Abilities that improve with hero level have a base value")))',
            CURRENTS]
    out = g._merge_all_followup(rows)
    assert len(out) == 2
    text, kw, _ = g._li_parts(out[0])
    assert text == "Innate abilities no longer scale with other abilities' level"
    assert kw["extra"].startswith("inline_note(\"All innate abilities") and "base value" in kw["extra"]
    assert out[1] == CURRENTS                                           # another subject: left alone
