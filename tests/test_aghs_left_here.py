"""An Aghanim's upgrade that moved whole to another ability: the old -> new card stands under the ability that lost it
("Removed Aghanim's Shard bonus from this ability." said nothing of what still works — owner 2026-10-27, 7.39 Mist
Coil -> Aphotic Shield); the ability that got it shows its new text alone."""
from patch import aghs_text, cards_aghs
from patch.state import _State

OLD = {"abaddon_death_coil": "Causes Mist Coil to also deal attack damage."}
NEW = {"abaddon_aphotic_shield": "75% of absorbed damage is dealt to nearby enemies."}


def _setup(monkeypatch):
    monkeypatch.setattr(aghs_text, "holders", lambda hero, kind, v: sorted(
        (OLD if v == "7.38c" else NEW) if kind == "shard" else {}))
    monkeypatch.setattr(aghs_text, "aghs_text", lambda s, kind, v: (OLD if v == "7.38c" else NEW).get(s))
    monkeypatch.setattr(aghs_text, "ability_name", lambda s, v: {"abaddon_death_coil": "Mist Coil",
                                                                 "abaddon_aphotic_shield": "Aphotic Shield"}[s])
    monkeypatch.setattr(_State, "current_patch_version", "7.39")
    monkeypatch.setattr(_State, "current_hero", "abaddon")


def test_the_card_stands_under_the_ability_that_lost_it(monkeypatch):
    _setup(monkeypatch)
    monkeypatch.setattr(_State, "current_ability_slug", "abaddon_death_coil")
    assert cards_aghs._aghs_removed_row("No longer upgraded with Aghanim's Shard")   # the row the card stands under
    monkeypatch.setattr(_State, "aghs_part_slug", ("abaddon_death_coil", "abaddon"))
    html = cards_aghs._aghs_parts_cards()
    assert "Mist Coil" in html and "Aphotic Shield" in html and "Added Aghanim" not in html
    assert ("7.39", "abaddon", "shard") in cards_aghs._AGHS_SHOWN


def test_no_card_under_an_ability_without_the_removed_row(monkeypatch):
    _setup(monkeypatch)
    monkeypatch.setattr(_State, "aghs_part_slug", ("abaddon_death_coil", "abaddon"))
    assert cards_aghs._aghs_parts_cards() == ""


def test_the_ability_that_got_it_shows_the_new_text_alone(monkeypatch):
    _setup(monkeypatch)
    cards_aghs._AGHS_SHOWN.add(("7.39", "abaddon", "shard"))
    monkeypatch.setattr(_State, "current_ability_slug", "abaddon_aphotic_shield")
    monkeypatch.setattr(_State, "aghs_cards", [])
    assert cards_aghs._aghs_rework_card("Aghanim's Shard: Deals 75% of absorbed damage to nearby enemies")
    card = _State.aghs_cards[-1]
    assert "Added Aghanim's Shard." in card and "Mist Coil" not in card and "absorbed damage" in card
