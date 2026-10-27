"""General Updates regrouping (owner 2026-10-16, 7.41 Global Changes): topic subgroups ("Scaling with Hero Level",
"Lane Creeps") for topics with two rows or more, "<X> removed from the game" as the section's intro line, and Valve's
follow-up "All <same subject> …" sentence as the "?" of the row before it."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools.generate_patch_code_v2 as g  # noqa: E402

SIEGE = "W(li(\"First +1 siege creep timing decreased from 35:00 to 30:00\", t(\"REWORK\"), also_dyn=['unit|siege-creep']))"
FLAG = ("W(li(\"Flagbearer Creep Experience Bounty increased from 57 to 60\", b(57, 60), "
        "also_dyn=['unit|flagbearer-creep']))")
CURRENTS = 'W(li("All sections of currents now give a max movement speed bonus of 150", t("BUFF")))'
FACETS = 'W(li("Facets removed from the game", t("DEL")))'
INNATE = 'W(li("Innate abilities no longer scale with other abilities\' level", t("REWORK")))'
UI = 'W(li("Added UI icon that shows which parameters increase with hero level", t("QoL")))'
LANES = ['W(ul_open())', FACETS, INNATE, UI, 'W(ul_close())', 'W(ul_open())', SIEGE, FLAG, 'W(ul_close())',
         'W(ul_open())', CURRENTS, 'W(ul_close())']


MEET = ("W(li(\"Adjusted the meeting point of the lane creeps toward the offlane\", t(\"MISC\"), "
        "also_dyn=['unit|melee-creep', 'unit|ranged-creep']))")
SIEGE2 = "W(li(\"Second +1 siege creep timing now occurs at 60:00\", t(\"REWORK\"), also_dyn=['unit|siege-creep']))"


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
                  'general=False, page="flagbearer-creep"))')
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
    assert g._guess_tag("First +1 siege creep timing decreased from 35:00 to 30:00") == "BUFF"   # sooner = its buff


def test_a_per_minute_growth_becomes_a_minute_table():
    out = g._postprocess_per_minute(['W(li("Barrier upgrade per minute increased from 20 to 50", b(20, 50)))',
                                     'W(li("Experience per Minute bonus increased from +600 to +1000", b(600, 1000)))'])
    assert out[0].startswith('W(li_formula("Barrier upgrade increased", "20 per minute", "50 per minute"')
    assert "level_prefix='M'" in out[0]
    assert out[1].startswith('W(li("Experience per Minute')                          # a rate, not a growth: left


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
    rows = ["W(li(\"Inspiration Aura no longer affects heroes\", t(\"DEL\"), also_dyn=['unit|flagbearer-creep']))",
            "W(li(\"AoE Bounty Radius increased from 1200 to 1500\", b(1200, 1500), also_dyn=['unit|flagbearer-creep']))"]
    plain, per = g._lane_card_abilities("unit|flagbearer-creep", rows)
    assert plain == rows[1:] and list(per) == ["Inspiration Aura"]
    assert per["Inspiration Aura"][1][0].startswith('W(li("No longer affects heroes"')


def test_a_bosss_rows_go_to_its_card_without_its_name():
    """Owner 2026-10-16: "Tormentor's spawn preference has switched" -> "Spawn preference has switched" on the card;
    a stray "Roshan's ..." row in a flat list moves to Roshan's card."""
    lines = ['W(ul_open())', 'W(li("Wisdom Shrines now reverse their countdowns", t("REWORK")))',
             'W(li("Roshan' + "'" + 's pit preference has switched", t("MISC")))', 'W(ul_close())',
             'W(unit_header("Tormentor", "../icons/units/npc_dota_miniboss.png", general=False, track=True))',
             'W(ul_open())', 'W(li("Tormentor' + "'" + 's spawn preference has switched", t("MISC")))', 'W(ul_close())']
    out = g._postprocess_unit_possessive(g._postprocess_boss_rows_home(lines))
    r = out.index('W(unit_header("Roshan", "../icons/units/npc_dota_roshan.png", general=False, track=True))')
    assert out[r + 2] == 'W(li("Pit preference has switched", t("MISC")))'
    assert 'W(li("Spawn preference has switched", t("MISC")))' in out
    assert not any("Roshan's" in line for line in out[:r])


def test_a_switched_row_takes_its_short_note_into_the_line():
    out = g._postprocess_switched_note(['W(li("Spawn preference has switched", t("MISC"), '
                                        'extra=inline_note("Now begins in the Bottom Chasm")))'])
    assert out == ['W(li("Spawn preference has switched — now begins in the Bottom Chasm", t("MISC")))']


def test_a_mechanics_subgroup_of_rework_rows_is_a_reworked_mechanic():
    """Owner 2026-10-16: 7.41 "Health Restoration" like "Scaling with Hero Level"."""
    lines = ['W(plain_header("Mechanics Changes"))', 'W(subgroup("Health Restoration"))', 'W(ul_open())',
             'W(li("Health Restoration now applies to all forms of life gain", t("REWORK")))',
             'W(li("Incoming Heal Amplification now stacks diminishingly", t("REWORK")))', 'W(ul_close())',
             'W(subgroup("Miscellaneous"))', 'W(ul_open())',
             'W(li("Reflected damage cannot be reflected back", t("NERF")))', 'W(ul_close())']
    out = g._postprocess_new_block_label(lines)
    assert 'W(subgroup("Health Restoration", new="Reworked mechanic"))' in out
    assert 'W(subgroup("Miscellaneous"))' in out                       # a NERF row: an ordinary list


def test_lane_creep_pages_are_named_after_the_creep():
    """Owner 2026-10-16: no goodguys / badguys in the address — we don't split by side; old addresses redirect."""
    from builders import entity_changes as ec
    assert ec._unit_slug("npc_dota_creep_goodguys_flagbearer") == "flagbearer-creep"
    assert ec._unit_slug("npc_dota_goodguys_siege") == "siege-creep"
    assert set(g._LANE_CARDS) == {"unit|melee-creep", "unit|ranged-creep", "unit|flagbearer-creep", "unit|siege-creep"}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    old = os.path.join(root, "dist", "units", "creep-goodguys-flagbearer.html")
    if os.path.exists(old):                                             # built: the old page sends readers on
        assert 'url=flagbearer-creep.html' in open(old, encoding="utf-8").read()


def test_general_changes_split_into_mechanic_blocks_with_every_valve_row():
    # owner 2026-10-26, 7.39 General Changes: each mechanic its own block as 7.38 Lifesteal; Valve's sub-rows stay rows
    note = {"title": "General Changes", "generic": [
        {"indent_level": 1, "note": "Lifesteal Amplification has been removed and a new umbrella stat has been created "
                                    "in its place: Health Restoration"},
        {"indent_level": 2, "note": "Provides a percentage increase to the health gained", "info": "Also negative"},
        {"indent_level": 2, "note": "Health Restoration cannot go higher than 100%"},
        {"indent_level": 1, "hide_dot": True, "note": "<br>"},
        {"indent_level": 1, "note": "Sources of Heal Amplification now stack additively"},
        {"indent_level": 1, "note": "Heal Amplification has no upper limit"},
        {"indent_level": 1, "hide_dot": True, "note": "<br>"},
        {"indent_level": 1, "note": "Effects that root and disarm are now considered Bind Effects"},
    ]}
    out = "\n".join(g._render_general_note(note))
    assert 'W(plain_header("Health Restoration", new="New mechanic"))' in out
    assert 'W(plain_header("Heal Amplification", new="Reworked mechanic"))' in out
    assert 'W(li("Provides a percentage increase to the health gained", t("NEW")' in out    # a row, not a "?"
    assert 'extra=inline_note("Also negative")' in out
    rest = out[out.index('W(plain_header("General Changes"))'):]
    assert "Bind Effects" in rest and "Heal Amplification" not in rest
