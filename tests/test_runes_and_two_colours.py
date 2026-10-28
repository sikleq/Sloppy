"""Owner 2026-10-28: a rune row shows the rune's icon (7.40 "Haste Rune: …"), and every map picture speaks in two
colours only — red dashed = where it was and how, green solid = how it is (yellow "moved" and the green Trees layer
read as a third meaning)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "gen"))
from patch import elements  # noqa: E402
from patch.mech_abilities import RUNE_ICONS, rune_row_chip  # noqa: E402
from patch.state import reset_page_state  # noqa: E402
import terrain_shots as ts  # noqa: E402


def test_a_rune_row_shows_the_rune_icon_with_its_name_on_hover():
    out = rune_row_chip("Haste Rune: Duration no longer increases by 3s per rune cycle")
    assert out.startswith('<span class="ability-chip" data-tooltip="Haste Rune"')
    assert "icons/runes/haste.png" in out and out.endswith("</span>Duration no longer increases by 3s per rune cycle")


def test_illusion_has_its_icon_and_a_row_without_a_rune_keeps_its_text():
    # the client has no 2D Illusion icon: the Terrain page's own power-rune picture (owner 2026-10-28)
    assert "icons/runes/illusion.png" in rune_row_chip("Illusion Rune: Illusions now …")
    assert rune_row_chip("Rune spawn interval increased") == "Rune spawn interval increased"
    assert rune_row_chip("Fire Rune: x") == "Fire Rune: x"


def test_a_transparent_icon_sits_on_a_dark_square():
    """7.40 Bounty Rune's icon is transparent: grown on hover, the text behind showed through (owner 2026-10-28)."""
    import re
    css = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()
    assert re.search(r"\.ability-chip > img \{[^}]*background: var\(--bg-deep-97\)", css)


def test_every_rune_icon_named_is_on_disk():
    for key in set(RUNE_ICONS.values()):
        assert os.path.exists(os.path.join(ROOT, "icons", "runes", f"{key}.png")), key


def test_li_puts_the_icon_in_the_row():
    reset_page_state()
    try:
        row = elements.li("Invisibility Rune: No longer grants incoming damage reduction",
                          '<span class="badge del" data-tag="del">DEL</span>')
    finally:
        reset_page_state()
    assert 'data-tooltip="Invisibility Rune"' in row and "Invisibility Rune:" not in row


def test_pictures_have_two_colours():
    assert set(ts.COLOUR) == {"removed", "added"}
    r, g, _b, _a = ts.TREE_FILL
    assert abs(r - g) < 30            # the Trees layer is neutral, not the "added" green
