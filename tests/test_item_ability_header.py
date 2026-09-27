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
