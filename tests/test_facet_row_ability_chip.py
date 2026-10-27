"""A facet's row that opens with an ability's name gets that ability's icon as a small square (owner 2026-10-27, 7.39b
Tinker Translocator "Defense Matrix: No longer blinks Tinker …"), like a facet talent's facet chip."""
from patch import elements
from patch.state import _State, reset_page_state


def _facet_row(text):
    reset_page_state()
    _State.current_patch_version = "7.39b"
    try:
        elements.hero_header("Tinker")
        elements.facet_header("tinker_translocator")
        return elements.li(text, '<span class="badge del" data-tag="del">DEL</span>')
    finally:
        reset_page_state()


def test_a_facet_row_naming_an_ability_shows_its_icon():
    row = _facet_row("Defense Matrix: No longer blinks Tinker if he is rooted or leashed")
    assert ('<span class="ability-chip" role="img" aria-label="Defense Matrix"><img src="../icons/abilities/'
            'tinker_defense_matrix.png"') in row


def test_a_facet_row_without_an_ability_name_gets_none():
    assert "ability-chip" not in _facet_row("Now also restores mana")
    assert "ability-chip" not in _facet_row("Translocator: something")      # the facet's own name has no icon file
