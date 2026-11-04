"""Owner 2026-10-28: a rune row shows the rune's icon (7.40 "Haste Rune: …"), and every map picture speaks in two
colours only — red dashed = where it was and how, green solid = how it is (yellow "moved" and the green Trees layer
read as a third meaning)."""
from patch.css_bundle import read_css
from patch.js_bundle import read_js
import os
import sys

import pytest

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


def test_a_power_rune_row_shows_our_own_power_rune_icon():
    # the game has none for the power runes as a whole (the HUD timer's is the Water rune): ours (owner 2026-10-28)
    out = rune_row_chip("Power Rune: spawn every 2 minutes")
    assert 'data-tooltip="Power Rune"' in out and "icons/runes/power.png" in out
    assert out.endswith("</span>Spawn every 2 minutes")
    assert 'data-tooltip="Power Rune"' in rune_row_chip("Power Runes: x")


def test_the_power_rune_icon_is_the_generators_bunch_of_three_runes():
    """power.png is what scripts/gen/gen_power_rune_icon.py draws (not a hand-made file): 32 px, transparent round
    the bunch, with the front Double Damage's blue and the Regeneration green and Haste red behind it."""
    pytest.importorskip("PIL")                  # CI installs no imaging libraries
    from PIL import Image, ImageChops
    import gen_power_rune_icon as gp
    on_disk = Image.open(os.path.join(ROOT, "icons", "runes", "power.png")).convert("RGBA")
    assert on_disk.size == (32, 32) and on_disk.getpixel((0, 31))[3] == 0
    assert ImageChops.difference(on_disk, gp.power_icon()).getbbox() is None
    assert [k for k, _, _ in gp.BUNCH] == ["regeneration", "haste", "doubledamage"]


def test_the_terrain_power_layer_button_is_our_power_rune_icon():
    """Owner 2026-10-28: the Terrain page's Power layer button shows our power-rune icon (48 px, like its other
    buttons), no longer a random rune; the map's markers still cycle the 7 runes."""
    pytest.importorskip("PIL")                  # CI installs no imaging libraries
    from PIL import Image, ImageChops
    import gen_power_rune_icon as gp
    btn = Image.open(os.path.join(ROOT, "icons", "ui", "gothic", "tc_power.png")).convert("RGBA")
    assert btn.size == (48, 48) and ImageChops.difference(btn, gp.power_icon(48)).getbbox() is None
    js = read_js()
    assert "powerBtnImg" not in js and "togglePowerCycle" in js


def test_runes_share_the_terrain_page_icons():
    """One style — the minimap icons the Terrain page shows (owner 2026-10-28)."""
    import filecmp
    for key, name in (("haste", "tc_rune_2"), ("illusion", "tc_rune_3"), ("bounty", "tc_bounty")):
        assert filecmp.cmp(os.path.join(ROOT, "icons", "runes", f"{key}.png"),
                           os.path.join(ROOT, "icons", "ui", "gothic", f"{name}.png"), shallow=False)


def test_a_transparent_icon_sits_on_a_dark_square():
    """7.40 Bounty Rune's icon is transparent: grown on hover, the text behind showed through (owner 2026-10-28)."""
    import re
    css = read_css()
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
