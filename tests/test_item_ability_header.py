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
