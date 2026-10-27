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
    chip = ('<span class="ability-chip" data-tooltip="Defense Matrix" role="img" aria-label="Defense Matrix"><img '
            'src="../icons/abilities/tinker_defense_matrix.png" alt="" loading="lazy" width="19" height="19"></span>')
    # the name only on hover, as a facet talent's facet chip (owner 2026-10-27)
    assert f'{chip}No longer blinks Tinker' in row and "Defense Matrix:" not in row


def test_a_facet_row_without_an_ability_name_gets_none():
    assert "ability-chip" not in _facet_row("Now also restores mana")



def test_a_facet_row_naming_the_facet_itself_drops_the_name():
    """7.40 "Arsonist: No longer has decreased number of …" -> "No longer has …": the header says whose (owner
    2026-10-27)."""
    row = _facet_row("Translocator: something changed")
    assert '<span class="row-text">Something changed' in row and "Translocator:" not in row and "ability-chip" not in row
