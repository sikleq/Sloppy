"""Card header strip: the text's own "Passive, levels up with Duel." goes to the header as "Passive (Scales with Duel)",
"No Mana Cost. Cooldown: 120s." in bold still goes to the header, and a "Radius: 1500." followed by a tag too
(owner 2026-10-24, 7.41 Outfight Them! / Gravity Well / Distortion Field / Sacrifice / Death Charge)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patch import elements as el  # noqa: E402


def test_passive_with_what_it_levels_with_goes_to_the_header():
    head, body = el._pane_parts(["Passive, levels up with Duel.", "When attacking an enemy hero, she heals."])
    assert '<b class="iab-kind">Passive</b> <span class="iab-scale">(Scales with Duel)</span>' in head
    assert "levels up" not in body and "Passive" not in body


def test_scales_and_improves_wordings_and_active_kind():
    head, _ = el._pane_parts(["Passive, scales with Black Hole.", "Allies in a 500 radius take less damage."])
    assert "(Scales with Black Hole)" in head
    head, body = el._pane_parts(["Active, levels with Holy Persuasion.", "Chen summons a convert."])
    assert '<b class="iab-kind">Active</b>' in head and "(Scales with Holy Persuasion)" in head
    assert "levels with" not in body


def test_highlight_on_the_phrase_moves_with_it():
    head, body = el._pane_parts(["Passive, " + el.hl("levels up with Chronosphere", "del") + ".", "Slows projectiles."])
    assert "(" + el.hl("Scales with Chronosphere", "del") + ")" in head
    assert "Chronosphere" not in body


def test_two_level_phrases_stay_in_the_text():
    _, body = el._pane_parts(["Passive.", "Levels with Shadow Dance.", "Improves with Essence Shift."])
    assert "Levels with Shadow Dance" in body and "Improves with Essence Shift" in body


def test_comma_clause_after_the_kind_starts_the_text():
    head, body = el._pane_parts(["Active, targets an allied creep within 700 range and instantly kills it."])
    assert '<b class="iab-kind">Active</b>' in head
    assert body.startswith('<div class="ability-change-row">Targets an allied creep')


def test_bold_cost_and_cooldown_go_to_the_header():
    head, body = el._pane_parts(["Active.", "<b>No Mana Cost. Cooldown: 120s.</b> Starts on extended cooldown."])
    assert "cooldown.png" in head and "120" in head
    assert "No Mana Cost" not in body and "Cooldown:" not in body and "<b></b>" not in body
    assert "Starts on extended cooldown" in body


def test_bold_run_with_other_words_stays_bold():
    _, body = el._pane_parts(["Passive.", "<b>Stacks up to 5 times.</b> Duration: 4s."])
    assert "<b>Stacks up to" in body


def test_highlighted_value_goes_to_the_header_with_its_colour():
    head, body = el._pane_parts(["Active.", "Hawk Duration: 25s. Cooldown: " + el.hl("45/40/35/30s", "nerf") + "."])
    assert el.hl("45/40/35/30", "nerf") in head
    assert "Cooldown" not in body and "Hawk Duration" in body
    # the game files' value, coloured by the text's highlight
    head, _ = el._pane_parts(["Active.", "Cooldown: " + el.hl("14s", "new") + "."], props={"cooldown": "14"})
    assert el.hl("14", "new") in head


def test_value_before_its_note_goes_to_the_header():
    head, body = el._pane_parts(["Passive.", "Kills any creep. Cooldown: 15s " + el.inline_note("Can't be toggled")])
    assert "cooldown.png" in head and "15" in head
    assert "Cooldown" not in body and "Can't be toggled" in body


def test_value_of_one_named_sub_ability_among_several_stays_in_the_text():
    head, body = el._pane_parts(["Crystal Ball: Scans an area.", "Weighted Pie: Tosses a pie. Cast Range: 750."])
    assert "castrange.png" not in head and "Cast Range:" in body and "750" in body
    # "Cooldown: 14s." / "Bonus Move Speed: 25" are labels, not sub-abilities (7.41 Kinetic Fence)
    head, _ = el._pane_parts(["Active.", "Charge Restore Time: 30s.", "Formation Time: Instant.", "Cooldown: 14s."])
    assert "cooldown.png" in head
    head, _ = el._pane_parts(["Active.", "Passive: grants lifesteal.", "Active: cast on an ally. Cast Range: 500."])
    assert "castrange.png" in head                  # "Passive:" / "Active:" are not sub-abilities


def test_innate_cannot_be_leveled_up_is_never_said():
    _, body = el._pane_parts(["Innate, cannot be leveled up.", "Summons a Spirit Bear."], props={"kind": "Active"})
    assert "leveled" not in body and "Summons a Spirit Bear" in body


def test_highlighter_preview_hero_block_has_its_class():
    assert 'class="entity-block hl-marker"' in el.hero_header("Dragon Knight")
    assert "hl-marker" not in el.hero_header("Axe")


def test_radius_sentence_followed_by_a_tag_goes_to_the_header():
    head, body = el._pane_parts(["Passive.", "<b>Radius:</b> 1500. <b>Max Mana Restored:</b> 2.5% (Creep)."])
    assert "aoe.png" in head and "1500" in head
    assert "Radius" not in body and "Max Mana Restored" in body
