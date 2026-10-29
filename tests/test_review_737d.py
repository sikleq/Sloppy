"""Proofread of 7.37d (2026-10-29), each rule in the generator so the next patch gets it too."""
import pytest

import tools.generate_patch_code_v2 as g


@pytest.mark.parametrize("text, tag", [
    ("No longer doubles its bonuses at 25 minutes", "DEL"),
    ("Suppress no longer makes caster or ally unslowable", "DEL"),
    ("Soul Release now always gains a charge when the owner dies", "NEW"),                 # owner 2026-10-29
    ("Sacrificing creeps with Martyrdom (Aghanim's Scepter) now triggers On Death effects", "NEW"),   # owner
    ("Enemy heroes caught are no longer pulled to the center of the formation. Now they are placed inside as far away "
     "from the center as possible while not touching a cog", "REWORK"),                     # owner
    ("Alt cast behavior now has 50% of base spell's cast range", "NERF"),                  # owner
    ("Now heals creeps for 50% effectiveness", "NERF"),   # creeps were healed in full in 7.37c (KV, tooltip)
    ("Absorbing damage with Mana Shield now disables Blink Dagger", "NERF"),
    ("Aghanim's Shard no longer allows to hit the same enemy unit by multiple secondary Starstorms in a single cast",
     "DEL"),
    ("Effects that percentually change the base damage now also affect base damage bonus provided by Illusory "
     "Armaments", "NEW"),                                                                  # owner 2026-10-29
    ("Toggling items no longer breaks invisibility", "QoL"),
    ("Focus Fire: Windranger can no longer shoot arrows while channeling", "DEL"),
    ("Aghanim's Scepter invisibility buff is now dispelled if the base Windrun buff is dispelled", "NERF"),
])
def test_7_37d_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


def test_a_min_max_range_per_level_is_compared_by_each_middle():
    """7.37d Nature's Call: "Treant Damage decreased from 28-32/44-48/60-64/76-80 to 22-26/40-44/58-62/76-80" — a % per
    level against each range's middle, as the 7.37e single range, not a bare NERF tag."""
    text = "Nature's Call: Treant Damage decreased from 28-32/44-48/60-64/76-80 to 22-26/40-44/58-62/76-80"
    assert g._emit_badge(text) == "b([30, 46, 62, 78], [24, 42, 60, 78])"


def test_the_same_text_for_two_abilities_is_not_flagged_as_misplaced():
    """7.37d Omniknight: Purification and Repel both "Mana Cost increased from 80/95/110/125 to 90/105/120/135" (both
    changed in the game) — the loc map kept only the last key, and Purification's row read "belongs to omniknight_martyr"."""
    loc = g._load_patchnotes_loc("7.37d")["omniknight"]
    slugs = loc["mana cost increased from 80/95/110/125 to 90/105/120/135"]
    assert slugs == {"omniknight_purification", "omniknight_martyr"}


def test_a_hero_note_named_after_an_innate_goes_in_the_innate_block():
    """7.37d "Duelist: Bonus damage increased from 10% to 12%" — Juggernaut's innate that patch: its own innate block,
    not a plain row under the hero."""
    from patch.ability_kv import hero_innates
    assert hero_innates("juggernaut", "7.37d").get("duelist") == "juggernaut_duelist"
    out = "\n".join(g._render_hero({"hero_id": 8, "hero_notes": [
        {"indent_level": 1, "note": "Duelist: Bonus damage increased from 10% to 12%"}]}, version="7.37d"))
    assert 'W(ability("Duelist", slug="juggernaut_duelist", innate=True))' in out
    assert 'W(li("Bonus damage increased from 10% to 12%", b(10, 12)))' in out
