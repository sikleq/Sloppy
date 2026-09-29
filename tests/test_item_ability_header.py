"""Owner 2026-09-27: an item ability row gets a light header like the game's item tooltip — name left,
cast range / mana / health cost / cooldown right with the game's icons; numbers bold."""
from patch import elements as el


def test_meta_goes_to_the_header_and_leaves_the_description():
    h = el._item_ability_html("Active: Ribbit. Increases an ally's health regeneration by 8 for 10 seconds. "
                              "Cast Range: 1000. Mana Cost: 40. Cooldown: 45s")
    head, desc = h.split('<span class="iab-desc">')
    assert '<span class="iab-name">Ribbit</span>' in head
    assert "castrange.png" in head and ">1000<" in head and "manacost.png" in head and ">40<" in head
    assert "cooldown.png" in head and ">45<" in head
    assert "Cast Range" not in desc and "Cooldown" not in desc and '<b class="iab-num">8</b>' in desc


def test_a_multiplier_is_bold_whole_not_cut_at_its_decimal_point():
    # 7.39 Sister's Shroud "reduces this evasion bonus to 0.25x" showed a bold "0" and a plain ".25x"
    html = el._iab_bold_numbers("reduces it to 0.25x of its value, take 1.5x damage, ends at 5. Then 2x")
    assert '<b class="iab-num">0.25x</b> of' in html and '<b class="iab-num">1.5x</b> damage' in html
    assert '<b class="iab-num">5</b>. Then <b class="iab-num">2x</b>' in html


def test_no_mana_cost_is_dropped_and_a_name_with_bang_is_kept():
    h = el._item_ability_html("Active: Pig, Out! Turn your hero into a critter for 4 seconds. No Mana Cost. Cooldown: 25s")
    assert "Pig, Out!" in h and "No Mana Cost" not in h and "manacost.png" not in h


def test_a_description_without_a_name_keeps_its_first_sentence():
    h = el._item_ability_html("Active: Increases your current and max health by 240 for 10 seconds")
    assert "iab-name" not in h and "Increases your current" in h


def test_a_radius_sentence_goes_to_the_header_with_the_aoe_icon():
    h = el._item_ability_html("Active: Arctic Blast. Emits a freezing wave. Radius: 825. Mana Cost: 75. Cooldown: 27s")
    head, desc = h.split('<span class="iab-desc">')
    assert "aoe.png" in head and ">825<" in head and "Radius" not in desc


def test_a_misc_radius_row_joins_the_header_grey_with_its_note_on_hover():
    # Gleipnir 7.38: the radius is only in the prose, the row says why it doesn't matter
    from patch.state import _State
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        _State.current_entity_key, _State.current_patch_version = "item|gleipnir-test", "7.38"
        el.item_abilities_change(
            old=["Active: Eternal Chains. Roots all enemies in a target 350 radius for 2 seconds. Cooldown: 18s"],
            new=["Active: Eternal Chains. Roots all enemies in a 350 radius for 2 seconds. Cooldown: 18s"])
        row = ("Eternal Chains radius decreased from 350 to 275 "
               "(effective spell radius unchanged due to item's built-in AoE Bonus)")
        assert el._iab_covered_change(row, {"misc"})
        assert not el._iab_covered_change("Chain Lightning radius increased from 600 to 650", {"buff"})
        old, new = el.render_iab_card("item|gleipnir-test|7.38").split("pane-new")
        assert "aoe.png" in old and ">350<" in old
        assert 'class="iab-m iab-misc"' in new and "aoe.png" in new
        assert ('class="iab-hint abil-ico-hint" data-tooltip="Effective spell radius unchanged due to '
                'item&#x27;s built-in AoE Bonus">275</span>') in new
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved


def test_abilities_pair_by_name_and_only_a_pair_gets_an_arrow():
    # Heaven's Halberd 7.38: Disarm -> Disarm gets the arrow, the new Damage Block has nothing to point from
    rows = el._iab_pair_rows(["Active: Disarm. Old text."],
                             ["Active: Disarm. New text.", "Passive: Damage Block. Blocks damage."])
    assert rows == [("Active: Disarm. Old text.", "Active: Disarm. New text."),
                    (None, "Passive: Damage Block. Blocks damage.")]
    # Gleipnir 7.38: the removed Chain Lightning keeps its place, an empty cell on the right
    rows = el._iab_pair_rows(["Active: Eternal Chains. A.", "Passive: Chain Lightning. B."], ["Active: Eternal Chains. C."])
    assert rows[1] == ("Passive: Chain Lightning. B.", None)
    from patch.state import _State
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        _State.current_entity_key, _State.current_patch_version = "item|halberd-test", "7.38"
        el.item_abilities_change(old=["Active: Disarm. Old text."],
                                 new=["Active: Disarm. New text.", "Passive: Damage Block. Blocks damage."])
        html = el.render_iab_card("item|halberd-test|7.38")
        # one arrow for the whole card (owner 2026-09-27), centred across every row
        assert html.count('class="properties-arrow"') == 1 and 'style="grid-row:1 / -1"' in html
        assert 'class="iab-none"' in html.split("pane-new")[0]            # the empty cell is on the old side
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved


def test_a_removed_and_an_added_ability_are_a_replacement_row():
    # Revenant's Brooch 7.38: Toggle: Phantom Province -> Passive: Phantom Critical (owner 2026-09-28)
    rows = el._iab_pair_rows(["Toggle: Phantom Province. Attacks cost 50 mana."],
                             ["Passive: Phantom Critical. Grants each attack a 30% chance."])
    assert rows == [("Toggle: Phantom Province. Attacks cost 50 mana.", "Passive: Phantom Critical. Grants each attack a 30% chance.")]
    # a removal with nothing added stays alone (Gleipnir 7.38), and so does an addition (Heaven's Halberd 7.38)
    assert el._iab_pair_rows(["Active: A. x.", "Passive: B. y."], ["Active: A. z."])[1] == ("Passive: B. y.", None)
    assert not el._iab_same_ability("Toggle: Phantom Province. a.", "Passive: Phantom Critical. b.")


def test_a_row_without_numbers_colours_the_card_text_it_describes():
    # Bloodstone 7.38: "Bloodpact now applies a basic dispel on cast" = the new "Dispel Type: Basic Dispel."
    from patch.state import _State
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        _State.current_entity_key, _State.current_patch_version = "item|bloodstone-test", "7.38"
        el.item_abilities_change(old=["Active: Bloodpact. Increases Spell Lifesteal by 4x. Lasts 5 seconds. Cooldown: 35s"],
                                 new=["Active: Bloodpact. Increases Spell Lifesteal by 4x. Lasts 5 seconds. "
                                      "Dispel Type: Basic Dispel. Cooldown: 35s"])
        assert el._iab_text_change("Bloodpact now applies a basic dispel on cast", {"new"})
        assert not el._iab_text_change("Bloodpact lifesteal increased from 4x to 5x", {"buff"})   # numbers: not this rule
        new = el.render_iab_card("item|bloodstone-test|7.38").split("pane-new")[1]
        assert '<span class="iab-hl iab-hl-new" data-tag="new">Dispel Type: Basic Dispel</span>.' in new
        assert "cooldown.png" in new                                    # the header values still found
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved


def _card_for(key, old, new):
    from patch.state import _State
    _State.current_entity_key, _State.current_patch_version = key, "7.38"
    el.item_abilities_change(old=old, new=new)


def test_no_longer_colours_the_removed_sentence_red_not_the_rewritten_fragment():
    from patch.state import _State
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        # Drum of Endurance 7.38: "Comes with 8 charges." went away; "Consumes a charge and gives" was rewritten
        _card_for("item|drum2-test",
                  ["Active: Endurance. Consumes a charge and gives +45 attack speed for 6 seconds. Comes with 8 charges."],
                  ["Active: Endurance. Gives +35 attack speed for 6 seconds."])
        assert el._iab_text_change("Endurance no longer uses charges", {"rework"})
        old = el.render_iab_card("item|drum2-test|7.38").split("pane-new")[0]
        assert '<span class="iab-hl iab-hl-del" data-tag="del">Comes with <b class="iab-num">8</b> charges</span>' in old
        assert "iab-hl-del\">Consumes" not in old
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved


def test_a_phrase_is_found_when_no_changed_piece_holds_the_rows_words():
    # Khanda 7.38: "Empower Spell no longer deals attack damage" = the old "your attack damage"
    from patch.state import _State
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        _card_for("item|khanda2-test",
                  ["Passive: Empower Spell. The next spell deals 150 + 60% of your attack damage as bonus damage to the target."],
                  ["Passive: Empower Spell. The next spell deals a separate 250 additional damage to the target."])
        assert el._iab_text_change("Empower Spell no longer deals attack damage", {"del"})
        old = el.render_iab_card("item|khanda2-test|7.38").split("pane-new")[0]
        assert '<span class="iab-hl iab-hl-del" data-tag="del">your attack damage</span>' in old
        # what stopped must be in the text: "no longer stack with …" is not "bonus damage"
        assert not el._iab_text_change("Empower Spell no longer stacks with Khanda", {"del"})
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved


def test_can_now_be_dispelled_adds_dispellable_at_the_end_of_the_description():
    from patch.state import _State
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        _card_for("item|halberd2-test",
                  ["Active: Disarm. Prevents a target from attacking for 3 seconds. Cast Range: 650. Cooldown: 18s"],
                  ["Active: Disarm. Prevents a target from attacking for 3 seconds. Cast Range: 650. Cooldown: 18s"])
        assert el._iab_text_change("Disarm can now be dispelled", {"nerf"})
        new = el.render_iab_card("item|halberd2-test|7.38").split("pane-new")[1]
        assert '<b class="iab-num">3</b> seconds. <span class="iab-hl iab-hl-nerf" data-tag="nerf">Dispellable</span>.' in new
        assert "castrange.png" in new and "cooldown.png" in new           # the header values still found
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved


def test_pierces_debuff_immunity_and_a_no_longer_row_with_its_number():
    # Shiva's Guard 7.41
    from patch.state import _State
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        _card_for("item|shiva-test",
                  ["Passive: Freezing Aura. Reduces the attack speed of all enemies by -45 and Health Restoration "
                   "and Incoming Heal Amplification by 25%. Radius: 1200."],
                  ["Passive: Freezing Aura. Reduces the attack speed of all enemies by -45. Radius: 1200."])
        assert el._iab_text_change("Freezing Aura now pierces debuff immunity", {"new"})
        assert el._iab_text_change("Freezing Aura no longer reduces Health Restoration and Incoming Heal "
                                   "Amplification by 25%", {"del"})
        # a number the card text doesn't show keeps the row
        assert not el._iab_text_change("Freezing Aura no longer reduces Health Restoration by 30%", {"del"})
        old, new = el.render_iab_card("item|shiva-test|7.38").split("pane-new")
        assert 'data-tag="new">Pierces Debuff Immunity</span>.' in new and "aoe.png" in new
        assert 'iab-hl-del" data-tag="del">and Incoming Heal Amplification by <b class="iab-num">25%</b></span>' in old
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved


def test_generator_moves_a_stat_remark_into_the_card_as_info():
    import generate_patch_code_v2 as g
    block = ['W(item_header("Shiva\'s Guard", changed="Item Reworked"))',
             'W(auto_components_change("Shiva\'s Guard", "7.41"))',
             'W(properties_change(old=[("BUFF", "+15 Armor")], new=[("", "+17 Armor", b(15, 17)), ("NEW", "+75 Area of Effect")]))',
             "W(ul_open())",
             'W(li("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack", t("MISC")))',
             "W(ul_close())"]
    out = g._postprocess_card_stat_notes(block)
    assert '("NEW", "+75 Area of Effect" + info_tip("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack"))' in out[2]
    assert not any("W(li(" in x for x in out)
    assert g._postprocess_card_stat_notes(out) == out


def test_removed_ability_row_is_hidden_when_the_card_shows_it_on_one_side():
    from patch.state import _State
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        _State.current_entity_key, _State.current_patch_version = "item|halberd41-test", "7.41"
        el.item_abilities_change(old=["Active: Disarm. A.", "Passive: Damage Block. B."], new=["Active: Disarm. C."])
        assert el._iab_unpaired_row("Removed Damage Block ability", {"del"})
        assert not el._iab_unpaired_row("Removed Disarm ability", {"del"})       # Disarm is on both sides
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved


def test_a_changed_number_carries_its_percent_in_the_hover_tip():
    from patch.state import _State
    from patch.badges import b
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        _State.current_entity_key, _State.current_patch_version = "item|drum-test", "7.38"
        el.item_abilities_change(old=["Passive: Swiftness Aura. Grants 20 movement speed to allies."],
                                 new=["Passive: Swiftness Aura. Grants 15 movement speed to allies."])
        assert el._iab_covered_change("Swiftness Aura movement speed decreased from 20 to 15", {"nerf"}, "", b(20, 15))
        new = el.render_iab_card("item|drum-test|7.38").split("pane-new")[1]
        assert 'class="iab-hint abil-ico-hint" data-tooltip="' in new and "-25%" in new
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved


def test_generator_skips_a_card_whose_tooltips_say_the_same_words():
    import sys
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
    from item_ability_text import _same_words
    # Block of Cheese 7.38: "Try me!" both times, only the 250 cast range gone
    assert _same_words(["Use: Scrumptious. Try me! Cast Range: 250. Cooldown: 40s"],
                       ["Use: Scrumptious. Try me! Cooldown: 40s"])
    assert not _same_words(["Active: Bloodpact. Lasts 5 seconds."], ["Active: Bloodpact. Lasts 5 seconds. Dispel Type: Basic Dispel."])


def test_item_abilities_change_puts_each_ability_in_a_card_on_its_side():
    from patch.state import _State
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        _State.current_entity_key, _State.current_patch_version = "item|khanda-test", "7.38"
        slot = el.item_abilities_change(
            old=["Passive: Empower Spell. Deals 150 bonus damage. Cooldown: 6s", "Passive: Critical Strike. 30% chance"],
            new=["Passive: Empower Spell. Deals 250 bonus damage. Cooldown: 12s"])
        assert slot == "<!--IABCARD:item|khanda-test|7.38-->"          # drawn when the page is saved
        # rows under the card that it already shows: hidden, their numbers coloured
        assert el._iab_covered_change("Empower Spell bonus damage increased from 150 to 250", {"buff"})
        assert el._iab_covered_change("Empower Spell cooldown increased from 6s to 12s", {"nerf"})
        assert not el._iab_covered_change("Recipe cost increased from 500 to 1500", {"nerf"})
        html = el.render_iab_card("item|khanda-test|7.38")
        old, new = html.split('pane-new')
        assert old.count('class="iab-card"') == 2 and new.count('class="iab-card"') == 1
        assert ">6<" in old and '<b class="iab-num iab-buff">250</b>' in new
        assert 'class="iab-m iab-nerf"' in new and "cooldown.png" in new
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved
