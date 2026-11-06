"""An Aghanim's upgrade that moved whole to another ability: the old -> new card stands under the ability that got it
("Added Aghanim's Shard.": Mist Coil's old upgrade -> Aphotic Shield's), the one that lost it keeps the row "Removed
Aghanim's Shard bonus from this ability." alone (owner 2026-10-27, 7.39 Abaddon: a card there too was one too many)."""
from patch import aghs_text, cards_aghs
from patch.state import _State

OLD = {"abaddon_death_coil": "Causes Mist Coil to also deal attack damage."}
NEW = {"abaddon_aphotic_shield": "75% of absorbed damage is dealt to nearby enemies."}


def _setup(monkeypatch):
    monkeypatch.setattr(aghs_text, "holders", lambda hero, kind, v: sorted(
        (OLD if v == "7.38c" else NEW) if kind == "shard" else {}))
    monkeypatch.setattr(aghs_text, "aghs_text", lambda s, kind, v, *_: (OLD if v == "7.38c" else NEW).get(s))
    monkeypatch.setattr(aghs_text, "ability_name", lambda s, v: {"abaddon_death_coil": "Mist Coil",
                                                                 "abaddon_aphotic_shield": "Aphotic Shield"}[s])
    monkeypatch.setattr(_State, "current_patch_version", "7.39")
    monkeypatch.setattr(_State, "current_hero", "abaddon")


def test_the_generator_writes_the_row_the_card_is_drawn_from():
    """Valve nests the upgrade's text under "Now upgraded with Aghanim's Shard"; the draft gets one row "Aghanim's
    Shard: <text>" (NEW) — the card's row — not two (NEW + a MISC description) to merge by hand (owner 2026-10-27)."""
    import tools.generate_patch_code_v2 as g
    notes = [{"indent_level": 1, "note": "Now upgraded with Aghanim's Shard", "aghanims": "shard"},
             {"indent_level": 2, "note": "Deals 75% of absorbed damage to nearby enemies"},
             {"indent_level": 1, "note": "Cooldown decreased from 12 to 10"}]
    assert [n["note"] for n in g._merge_aghs_description(notes)] == [
        "Aghanim's Shard: Deals 75% of absorbed damage to nearby enemies", "Cooldown decreased from 12 to 10"]
    lines, _ = g._emit_notes(notes)
    assert any(ln.startswith('W(li("Aghanim\'s Shard: Deals 75% of absorbed damage') and 't("NEW")' in ln for ln in lines)
    # a kid that is its own row keeps both
    kept = [{"indent_level": 1, "note": "Now upgraded with Aghanim's Scepter"},
            {"indent_level": 2, "note": "No longer reduces armor"}]
    assert g._merge_aghs_description(kept) == kept


def test_no_card_under_the_ability_that_lost_it(monkeypatch):
    _setup(monkeypatch)
    monkeypatch.setattr(_State, "current_ability_slug", "abaddon_death_coil")
    assert cards_aghs._aghs_removed_row("No longer upgraded with Aghanim's Shard") == \
        "Removed Aghanim's Shard."
    monkeypatch.setattr(_State, "aghs_part_slug", ("abaddon_death_coil", "abaddon"))
    assert cards_aghs._aghs_parts_cards() == ""


def test_the_ability_that_got_it_shows_old_and_new(monkeypatch):
    _setup(monkeypatch)
    monkeypatch.setattr(_State, "current_ability_slug", "abaddon_aphotic_shield")
    monkeypatch.setattr(_State, "aghs_cards", [])
    assert cards_aghs._aghs_rework_card("Aghanim's Shard: Deals 75% of absorbed damage to nearby enemies")
    card = _State.aghs_cards[-1]
    assert "Added Aghanim's Shard." in card and "Mist Coil" in card and "absorbed damage" in card
