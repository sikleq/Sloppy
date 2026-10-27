"""ability_change cards: header values the old / new pair changed are coloured, and the row under the card that says
exactly that change is hidden like the rows marked covered=True (owner 2026-10-24, "всё в карточку")."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patch import elements as el  # noqa: E402
from patch.state import _State  # noqa: E402
from patch import cards_aghs  # noqa: E402
from patch import cards_item_abilities  # noqa: E402


def test_new_value_takes_the_changes_colour_and_the_old_one_the_opposite():
    old_m, new_m = cards_item_abilities._iab_meta_marks({"cooldown": "20", "manacost": "75", "castrange": "1050"},
                                      {"cooldown": "25", "manacost": "100", "castrange": "1200"})
    assert new_m == {"cooldown": "nerf", "manacost": "nerf", "castrange": "buff"}
    assert old_m == {"cooldown": "buff", "manacost": "buff", "castrange": "nerf"}
    assert cards_item_abilities._iab_meta_marks({"cooldown": "45/40/35/30"}, {"cooldown": "30"})[1] == {"cooldown": "buff"}
    assert cards_item_abilities._iab_meta_marks({"cooldown": "30"}, {"cooldown": "30.0"}) == ({}, {})


def test_header_value_is_coloured_only_when_a_row_under_the_card_names_the_change():
    html = cards_item_abilities._iab_meta_chips({"cooldown": "25", "manacost": "70"},
                              marks={"cooldown": ("nerf", 9001), "manacost": ("nerf", 9001)})
    _State.card_meta = {"cooldown": ("20", "25", 9001), "manacost": ("50", "70", 9001)}
    assert cards_aghs._card_meta_covered("Cooldown increased from 20s to 25s")         # the row: hidden, confirms the chip
    out = cards_item_abilities.resolve_chip_marks(html)
    assert 'iab-hl-nerf">25</span>' in out
    assert ">70</span>" in out and 'iab-hl-nerf">70' not in out                # mana: no row names it (Kinetic Fence)
    assert "CHIPMARK" not in out
    el.ul_close()


def test_row_saying_the_header_change_is_hidden_until_the_list_closes():
    _State.card_meta = {"cooldown": ("20", "25", 9002), "manacost": ("75", "100", 9002)}
    assert cards_aghs._card_meta_covered("Cooldown increased from 20s to 25s")
    assert cards_aghs._card_meta_covered("Mana Cost increased from 75 to 100")
    assert not cards_aghs._card_meta_covered("Cooldown increased from 18s to 25s")      # not what the headers show
    assert not cards_aghs._card_meta_covered("Cooldown changed from 240s to 245s - 5s per level")   # a formula, not 245
    assert not cards_aghs._card_meta_covered("Duration decreased from 7s to 6s")
    el.ul_close()
    assert not cards_aghs._card_meta_covered("Cooldown increased from 20s to 25s")


def test_pane_values_take_the_texts_sentences_when_the_files_say_nothing():
    assert cards_item_abilities._pane_values(["Active.", "Mana Cost: 50. Cooldown: 30s."]) == {"manacost": "50", "cooldown": "30"}
    assert cards_item_abilities._pane_values(["Cooldown: 30s."], {"cooldown": "28"}) == {"cooldown": "28"}
