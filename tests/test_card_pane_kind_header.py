"""Card header strip: the text's own "Passive, levels up with Duel." goes to the header as "Passive (Scales with Duel)",
"No Mana Cost. Cooldown: 120s." in bold still goes to the header, and a "Radius: 1500." followed by a tag too
(owner 2026-10-24, 7.41 Outfight Them! / Gravity Well / Distortion Field / Sacrifice / Death Charge)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patch import elements as el  # noqa: E402


def test_passive_with_what_it_levels_with_goes_to_the_header():
    head, body = el._pane_parts(["Passive, levels up with Duel.", "When attacking an enemy hero, she heals."])
    assert '<b class="iab-kind">Passive</b> <span class="iab-scale">– scales with Duel</span>' in head
    assert "levels up" not in body and "Passive" not in body


def test_scales_and_improves_wordings_and_active_kind():
    head, _ = el._pane_parts(["Passive, scales with Black Hole.", "Allies in a 500 radius take less damage."])
    assert "– scales with Black Hole" in head
    head, body = el._pane_parts(["Active, levels with Holy Persuasion.", "Chen summons a convert."])
    assert '<b class="iab-kind">Active</b>' in head and "– scales with Holy Persuasion" in head
    assert "levels with" not in body


def test_phrase_moves_to_the_header_without_its_colour():
    # owner 2026-10-25: "в шапке не крась scales with"
    head, body = el._pane_parts(["Passive, " + el.hl("levels up with Chronosphere", "del") + ".", "Slows projectiles."])
    assert '<span class="iab-scale">– scales with Chronosphere</span>' in head
    assert "Chronosphere" not in body and "iab-hl" not in head


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


def test_value_growing_with_hero_level_says_scales_with_level():
    # owner 2026-10-25: "Passive - scales with level." (the game files' hero_levelup, 7.41 Precision Aura)
    head, _ = el._pane_parts(["Passive.", "Grants agility."], props={"kind": "Passive", "level_scaled": True})
    assert '<span class="iab-scale">– scales with level</span>' in head


def test_no_longer_levels_with_row_gets_a_header_card(monkeypatch):
    from patch import ability_kv
    props = {"7.40c": {"kind": "Passive", "level_scaled": False}, "7.41": {"kind": "Passive", "level_scaled": True}}
    monkeypatch.setattr(ability_kv, "ability_props", lambda slug, v: dict(props[v]))
    monkeypatch.setattr(el._State, "current_ability_slug", "drow_ranger_trueshot")
    monkeypatch.setattr(el._State, "current_patch_version", "7.41")
    monkeypatch.setattr(el._State, "aghs_cards", [])
    row = el.li("No longer levels with Marksmanship", "")
    assert "iab-covered" in row
    card = el.ul_close()
    assert '<span class="iab-scale">– scales with Marksmanship</span>' in card
    assert '<span class="iab-scale">– scales with level</span>' in card
    # both sides carry the ability's own text from the game files (owner 2026-10-25: "нет описаний")
    assert card.count('class="ability-change-row"') >= 2 and "per level" in card
    # a fixed value now: the new header is the kind alone
    props["7.41"]["level_scaled"] = False
    el.li("No longer levels with Marksmanship", "")
    assert "scales with level" not in el.ul_close()


def test_highlighter_is_the_whole_site_not_a_preview():
    # owner 2026-10-25: the Dragon Knight preview became every card's look; no per-hero class is left
    assert "hl-marker" not in el.hero_header("Dragon Knight")
    css = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles.css"),
               encoding="utf-8").read()
    assert ".hl-marker" not in css
    assert ".iab-hl-new { --hl-bg: rgba(224, 189, 98, 0.15); }" in css


def test_radius_sentence_followed_by_a_tag_goes_to_the_header():
    head, body = el._pane_parts(["Passive.", "<b>Radius:</b> 1500. <b>Max Mana Restored:</b> 2.5% (Creep)."])
    assert "aoe.png" in head and "1500" in head
    assert "Radius" not in body and "Max Mana Restored" in body
