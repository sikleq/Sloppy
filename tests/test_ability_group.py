"""Several abilities with the very same change → one block with their icons stacked (owner 2026-10-30, 7.37b Quas /
Wex / Exort / Invoke "Can now be cast during channeling and does not break invisibility")."""
import tools.generate_patch_code_v2 as g

ROW = 'W(li("Can now be cast during channeling and does not break invisibility", t("NEW")))'


def _block(name, slug, row=ROW):
    return [f'W(ability("{name}", slug="{slug}"))', 'W(ul_open())', row, 'W(ul_close())']


def test_consecutive_blocks_with_the_same_rows_become_one_group():
    lines = (_block("Quas", "invoker_quas") + _block("Wex", "invoker_wex") + _block("Exort", "invoker_exort")
             + _block("Invoke", "invoker_invoke") + _block("Sun Strike", "invoker_sun_strike", 'W(li("other"))'))
    out = g._postprocess_same_change_abilities(lines)
    assert out[:4] == ['W(ability_group(("Quas", "invoker_quas"), ("Wex", "invoker_wex"), ("Exort", "invoker_exort"), '
                       '("Invoke", "invoker_invoke")))', 'W(ul_open())', ROW, 'W(ul_close())']
    assert out[4:] == _block("Sun Strike", "invoker_sun_strike", 'W(li("other"))')


def test_a_single_block_or_different_rows_stay_as_they_are():
    lines = _block("Quas", "invoker_quas") + _block("Wex", "invoker_wex", 'W(li("other"))')
    assert g._postprocess_same_change_abilities(lines) == lines


def test_the_group_block_stacks_every_icon_and_lists_the_names():
    from patch.ability_group import ability_group
    from patch.state import _State
    _State.current_hero = "invoker"
    try:
        html = ability_group(("Quas", "invoker_quas"), ("Wex", "invoker_wex"), ("Exort", "invoker_exort"))
    finally:
        _State.current_hero = None
    assert 'class="ability-block has-icon-stack"' in html
    assert 'class="ability-icon-wrap ability-icon-stack" style="width:88px"' in html
    assert html.count('class="ability-icon-img"') == 3 and "left:40px;z-index:3" in html
    assert '<h4 class="ability-title">Quas, Wex, Exort</h4>' in html
