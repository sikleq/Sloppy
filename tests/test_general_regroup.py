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
    l = out.index('W(subgroup("Lane Creeps"))')
    assert out.index(CURRENTS) < l                                      # a row of no topic stays on top
    assert out[l + 2] == MEET                                           # a row about several creeps
    # one system changed as a whole: its own "Reworked mechanic" section after the block, rows REWORK + hidden tag
    s = out.index('W(plain_header("Scaling with Hero Level", new="Reworked mechanic"))')
    assert s > l and out[s + 2] == INNATE
    assert out[s + 3] == UI[:-2].replace('t("QoL")', 't("REWORK")') + ', force_tag="rework qol"))'
    f = out.index('W(unit_header("Flagbearer Creep", "../icons/units/npc_dota_creep_goodguys_flagbearer.png", '
                  'general=False, page="creep-goodguys-flagbearer"))')
    assert out[f + 2].startswith('W(li("Experience Bounty increased from 57 to 60"')   # its name prefix goes
    assert l < f and any(x.startswith('W(unit_header("Siege Creep"') for x in out[f:])   # cards after the subgroups
    assert 'W(ul_open())\nW(ul_close())' not in "\n".join(out)          # emptied blocks are gone


def test_lane_creep_cards_link_their_unit_pages():
    """Owner 2026-10-16: a creep card must be clickable, as a rule — the generator gives it page=, and every lane
    creep card in content/ has it (patch/elements.unit_header links ../units/<page>.html and adds the patch strip)."""
    import glob
    import re
    out = g._general_topics(LANES, "Global Changes")
    cards = [l for l in out if l.startswith("W(unit_header(")]
    assert cards and all('page="' in c for c in cards)
    names = {n for n, _icon in g._LANE_CARDS.values()}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = []
    for path in glob.glob(os.path.join(root, "content", "p*.py")):
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            m = re.search(r'W\(unit_header\("([^"]+)"', line)
            if m and m.group(1) in names and "page=" not in line:
                bad.append(f"{os.path.basename(path)}:{n}")
    assert not bad, bad


def test_first_and_second_timings_stay_two_rows():
    """Owner 2026-10-16: the second timing is a new property of the siege creep — its own row, NEW."""
    out = g._general_topics(['W(ul_open())', SIEGE, SIEGE2, CURRENTS, 'W(ul_close())'], "Global Changes")
    i = out.index(next(l for l in out if l.startswith('W(unit_header("Siege Creep"')))
    assert out[i + 2:i + 4] == [SIEGE, SIEGE2]


def test_a_lone_topic_row_stays_and_map_sections_are_left_alone():
    one = ['W(ul_open())', SIEGE, CURRENTS, 'W(ul_close())']
    assert g._general_topics(one, "Global Changes") == one
    assert g._general_topics(LANES, "Map Changes") == LANES


def test_a_timing_that_now_occurs_is_new():
    assert g._guess_tag("Second +1 siege creep timing now occurs at 60:00") == "NEW"
    assert g._guess_tag("First +1 siege creep timing decreased from 35:00 to 30:00") == "REWORK"


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


def test_a_bonus_row_gets_its_number_badge_from_the_note():
    row = ('W(li("All sections of currents now give a max movement speed bonus of 150", t("BUFF"), '
           'extra=inline_note("Previously other sections provided max bonus of 100")))')
    out = g._bonus_from_note([row])
    assert ', b(100, 150), extra=' in out[0] and 't("BUFF")' not in out[0]


def test_a_boss_ability_without_a_colon_gets_its_block():
    lines = ['W(subgroup("Tormentor"))', 'W(ul_open())',
             'W(li("Now has 25% Status Resistance", t("NEW")))',
             'W(li("Unyielding Shield Base barrier increased from 2000 to 3000", b(2000, 3000)))',
             'W(li("Reflect radius can now be seen by holding ALT key", t("QoL")))', 'W(ul_close())']
    out = g._postprocess_boss_blocks(lines)
    i = out.index('W(ability("Unyielding Shield", icon_url="../icons/abilities/miniboss_unyielding_shield.png"))')
    assert out[i + 2] == 'W(li("Base barrier increased from 2000 to 3000", b(2000, 3000)))'
    j = out.index('W(ability("Reflect", icon_url="../icons/abilities/miniboss_reflect.png"))')
    assert out[j + 2] == 'W(li("Radius can now be seen by holding ALT key", t("QoL")))'


def test_a_lane_creeps_ability_rows_get_its_block():
    rows = ["W(li(\"Inspiration Aura no longer affects heroes\", t(\"DEL\"), also_dyn=['unit|creep-goodguys-flagbearer']))",
            "W(li(\"AoE Bounty Radius increased from 1200 to 1500\", b(1200, 1500), also_dyn=['unit|creep-goodguys-flagbearer']))"]
    plain, per = g._lane_card_abilities("unit|creep-goodguys-flagbearer", rows)
    assert plain == rows[1:] and list(per) == ["Inspiration Aura"]
    assert per["Inspiration Aura"][1][0].startswith('W(li("No longer affects heroes"')
