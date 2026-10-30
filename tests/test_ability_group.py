"""Sibling abilities with the very same change → one block with their icons together (owner 2026-10-30, 7.37b Quas /
Wex / Exort / Invoke "Can now be cast during channeling and does not break invisibility")."""
import tools.generate_patch_code_v2 as g

ROW = 'W(li("Can now be cast during channeling and does not break invisibility", t("NEW")))'


def _block(name, slug, row=ROW):
    head = f'W(ability("{name}", slug="{slug}"))' if slug else f'W(ability("{name}"))'
    return [head, 'W(ul_open())', row, 'W(ul_close())']


def test_consecutive_sibling_blocks_with_the_same_rows_become_one_group():
    lines = (_block("Quas", "invoker_quas") + _block("Wex", "invoker_wex") + _block("Exort", "invoker_exort")
             + _block("Invoke", "invoker_invoke") + _block("Sun Strike", "invoker_sun_strike", 'W(li("other"))'))
    out = g._postprocess_same_change_abilities(lines)
    assert out[:4] == ['W(ability_group(("Quas", "invoker_quas"), ("Wex", "invoker_wex"), ("Exort", "invoker_exort"), '
                       '("Invoke", "invoker_invoke")))', 'W(ul_open())', ROW, 'W(ul_close())']
    assert out[4:] == _block("Sun Strike", "invoker_sun_strike", 'W(li("other"))')


def test_different_abilities_of_a_hero_stay_apart():
    """Owner: Omniknight's Purification and Repel with the same mana row are different abilities — two blocks."""
    row = 'W(li("Mana Cost increased from 80/95/110/125 to 90/105/120/135"))'
    lines = _block("Purification", "omniknight_purification", row) + _block("Repel", "omniknight_martyr", row)
    assert g._postprocess_same_change_abilities(lines) == lines


def test_a_block_without_slug_and_a_stale_belongs_to_marker_still_group():
    """7.41 names the orbs without a slug; 7.38 Morphling had a "# [patchnotes: belongs to …]" line from before the
    same-text fix — it goes."""
    row = 'W(li("Mana Cost rescaled from 5/10/15/20 to 10"))'
    lines = ['W(ability("Attribute Shift (Agility Gain)", slug="morphling_morph_agi"))', 'W(ul_open())',
             '# [patchnotes: belongs to morphling_morph_str]', row, 'W(ul_close())',
             *_block("Attribute Shift (Strength Gain)", None, row)]
    out = g._postprocess_same_change_abilities(lines)
    assert out == ['W(ability_group(("Attribute Shift (Agility Gain)", "morphling_morph_agi"), '
                   '("Attribute Shift (Strength Gain)", "morphling_morph_str")))', 'W(ul_open())', row, 'W(ul_close())']


def test_the_group_keeps_its_icons_in_the_usual_square_with_names_on_hover():
    """Owner 2026-10-30: the tag and the text must not move right — the icons share the 48px square (2x2 for 3-4,
    the diagonal for 2), each with its name on hover (data-tooltip, as the ability chips)."""
    from patch.ability_group import ability_group, _tiles
    from patch.state import _State
    _State.current_hero = "invoker"
    try:
        html = ability_group(("Quas", "invoker_quas"), ("Wex", "invoker_wex"), ("Exort", "invoker_exort"),
                             ("Invoke", "invoker_invoke"))
    finally:
        _State.current_hero = None
    assert 'class="ability-block has-icon-stack"' in html
    assert '<div class="ability-icon-wrap ability-icon-stack">' in html          # no width of its own: 48px column
    assert html.count('class="stack-icon" data-tooltip=') == 4 and 'data-tooltip="Invoke"' in html
    assert '<h4 class="ability-title">Quas, Wex, Exort, Invoke</h4>' in html
    assert all(left + size <= 48 and top + size <= 48 for left, top, size in _tiles(4) + _tiles(2) + _tiles(3))
