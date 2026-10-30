"""tools/kv_review.py — a patch page's rows against the game files of the patch before (owner 2026-10-30: a report
first). Each case is one the proofread of 7.37b–7.37e found by hand."""
import pytest

import tools.kv_review as kv


def _words(version, monkeypatch=None, page_tags=None):
    if monkeypatch is not None:
        monkeypatch.setattr(kv, "_page_tags", lambda v: page_tags or {})
    _prev, _wrong, words, hidden, checks = kv.review(version)
    return words, hidden, checks


def test_a_word_row_gets_the_file_change_of_its_ability():
    """7.37d Leech Seed "Now heals creeps for 50% effectiveness": the files show the new creep heal reduction."""
    words, _h, _c = _words("7.37d")
    leech = [w for w in words if w[1] == "treant_leech_seed"]
    assert leech and "creep_heal_reduction_pct" in leech[0][3]


def test_a_row_tagged_new_over_a_new_reduction_is_marked_for_a_tag_check(monkeypatch):
    """The generator's first guess for Leech Seed was NEW; the owner's review found a cut — the report flags it."""
    _w, _h, checks = _words("7.37d", monkeypatch, page_tags={})
    words = [w for w in _w if w[1] == "treant_leech_seed"]
    assert checks >= 1 and words[0][4] == "проверить тег"


def test_burning_spear_shows_the_facets_duration_cut_gone():
    words, _h, _c = _words("7.37b")
    spear = [w for w in words if w[1] == "huskar_burning_spear"]
    assert any("duration_for_nothl_conflagration" in f for f in spear[0][3])


@pytest.mark.parametrize("version, slug", [
    ("7.37d", "grimstroke_spirit_walk"),     # per tick 5/8/11/14 vs Valve's per second 25/40/55/70
    ("7.37d", "pangolier_gyroshell"),        # Thunderbolt "-2 → -1" on 10s = the row's 8s → 9s
    ("7.37d", "sandking_sand_storm"),        # a talent's value inside the ability's file
    ("7.37e", "enigma_demonic_conversion"),  # "from 14-20 to 17-20" written in the row's text
])
def test_stated_changes_are_not_reported_as_hidden(version, slug):
    _w, hidden, _c = _words(version)
    assert slug not in {h[1] for h in hidden}


def test_a_new_heros_abilities_are_not_hidden_changes():
    _w, hidden, _c = _words("7.37c")
    assert not any(h[1].startswith("ringmaster_") for h in hidden)


def test_a_value_moved_inside_the_file_is_not_a_change():
    """7.37e Escape Act: the cooldown went from AbilityCooldown into AbilityValues with the same numbers."""
    fields = kv._merge_moves({"AbilityCooldown": ("38 32 26 20", None),
                              "AbilityValues.AbilityCooldown.value": (None, "38 32 26 20"),
                              "AbilityValues.max_charges.value": (None, "2")})
    assert fields == {"max_charges": (None, "2")}
