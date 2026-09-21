"""Talent -> ability filter tagging (_tag_talent_rows).

Regression: a Level 20 talent "Eidolon Damage ..." belongs to Enigma's Demonic
Summoning, but the ability filter missed it because the talent names the summoned
unit, not the ability. These tests lock in the three ways a talent links to an
ability: display name (plural tolerated), alias keyword, and talents folded into
a facet/ability block.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from builders.entity_changes import _tag_talent_rows, _TALENT_ALIASES, _wrap_scopes


def _talents_block(inner_text):
    return ('<div class="ability-block talents-block"><ul class="changes">'
            f'<li data-tag="nerf"><span class="row-text">{inner_text}</span></li>'
            '</ul></div>')


def _ab(html):
    m = re.search(r'data-ec-ab="([^"]*)"', html)
    return m.group(1) if m else None


def test_alias_eidolon_maps_to_demonic_summoning():
    body = _talents_block("Level 20 Talent: Eidolon Damage decreased from +40 to +30")
    out = _tag_talent_rows(body, ["Malefice", "Demonic Summoning", "Black Hole"], hero_slug="enigma")
    assert _ab(out) == "Demonic Summoning"


def test_alias_needs_the_target_to_be_a_chip():
    # Demonic Summoning is NOT in names -> no chip to attach to -> stay untagged
    body = _talents_block("Level 20 Talent: Eidolon Damage decreased from +40 to +30")
    out = _tag_talent_rows(body, ["Malefice", "Black Hole"], hero_slug="enigma")
    assert _ab(out) is None


def test_plural_ability_name_matches():
    body = _talents_block("Level 20 Talent: Gale Creates Plague Wards replaced with +50 Base Damage")
    out = _tag_talent_rows(body, ["Venomous Gale", "Plague Ward", "Noxious Plague"], hero_slug="venomancer")
    assert "Plague Ward" in (_ab(out) or "")


def test_talent_outside_talents_block_is_caught():
    # a "Level N Talent" row folded into a facet block (pass 2)
    body = ('<div class="ability-block facet-block"><ul>'
            '<li><span class="row-text">Level 10 Talent: Bone Guard Duration increased</span></li>'
            '</ul></div>')
    out = _tag_talent_rows(body, ["Wraithfire Blast", "Bone Guard", "Reincarnation"], hero_slug="wraith-king")
    assert "Bone Guard" in (_ab(out) or "")


def test_generic_stat_talent_stays_untagged():
    body = _talents_block("Level 10 Talent: +30 Base Damage")
    out = _tag_talent_rows(body, ["Malefice", "Demonic Summoning"], hero_slug="enigma")
    assert _ab(out) is None


def test_non_talent_row_untouched_by_pass_two():
    # a normal ability-change row that mentions an ability but is not a talent
    body = ('<div class="ability-block"><ul>'
            '<li><span class="row-text">Malefice damage increased from 40 to 50</span></li>'
            '</ul></div>')
    out = _tag_talent_rows(body, ["Malefice", "Demonic Summoning"], hero_slug="enigma")
    assert _ab(out) is None


def test_facets_become_their_own_chip_titles():
    """Facets are collected apart from abilities so they render as facet chips
    (a talent naming the facet then filters to it)."""
    body = ('<div class="entity-block">'
            '<h4 class="subgroup">Abilities</h4>'
            '<div class="ability-block"><h4 class="ability-title">Malefice</h4></div>'
            '<h4 class="subgroup">Facets</h4>'
            '<div class="ability-block facet-block">'
            '<div class="ability-icon-wrap facet-icon-wrap"><img data-slug="enigma_x"></div>'
            '<h4 class="ability-title">Splitting Image</h4></div>'
            '</div>')
    html_out, scopes, titles, facets = _wrap_scopes(body)
    assert "Malefice" in titles
    assert "Splitting Image" not in titles      # not mixed into ability chips
    assert "Splitting Image" in facets          # its own facet chip
    assert 'data-scope="facets"' in html_out


def test_alias_file_targets_are_nonempty_strings():
    for slug, mp in _TALENT_ALIASES.items():
        assert isinstance(mp, dict) and mp, slug
        for kw, canon in mp.items():
            assert kw and isinstance(kw, str), slug
            assert canon and isinstance(canon, str), (slug, kw)
