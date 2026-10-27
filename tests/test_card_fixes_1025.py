"""Card fixes of 2026-10-25 (owner, 7.41 proofreading): "A + B per level" in a card is a formula pill with its table;
the header doesn't repeat a radius the text names or a cast range equal to the radius; a header value's % on hover;
"by 25%" after flat Aghanim numbers goes; a removed upgrade is old -> nothing; "X is now an innate ability (previously
a basic ability)" under the card showing X as the innate is hidden; the "scales with" card has no caption."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patch import elements as el  # noqa: E402
from patch.state import _State  # noqa: E402
from patch import cards_aghs  # noqa: E402
from patch import cards_item_abilities  # noqa: E402


def test_per_level_formula_becomes_a_pill_with_its_table():
    head, body = cards_item_abilities._pane_parts(["Passive.", "Explode radius: 400. Base damage: 17 + 3 per level."])
    assert 'class="formula-trigger"' in body and ">17 + 3 per level</span>" in re.sub(r'<b class="iab-num">|</b>', "", body)
    assert '<table class="formula-table' in body
    # the level table: 17 + 3 * L
    assert "<td>20</td>" in body and "<td>107</td>" in body


def test_percent_and_bold_formulas_and_decimals():
    _, body = cards_item_abilities._pane_parts(["Passive.", "Damage (1.5% + 0.05% per level) for every 100 units."])
    assert "<td>1.55%</td>" in body
    _, body = cards_item_abilities._pane_parts(["Passive.", "Restore percentage is equal to <b>10% + 2%</b> per hero level."])
    assert body.count('class="formula-trigger"') == 1 and "<td>12%</td>" in body


def test_an_existing_pill_and_per_level_up_are_left_alone():
    trig = '<span class="formula-trigger" data-formula="f9">9 + 1 per level</span>'
    _, body = cards_item_abilities._pane_parts(["Passive.", f"Deals <b>{trig}</b> damage."])
    assert body.count("formula-trigger") == 1
    html, tables = cards_item_abilities._pill_formulas("Heal changed from 1.5% + 1.5% per level up")
    assert "formula-trigger" not in html and not tables


def test_header_skips_a_radius_the_text_names_and_a_cast_range_equal_to_it():
    props = {"kind": "Active", "aoe": "625/550/475/400", "castrange": "625/550/475/400", "manacost": "50",
             "cooldown": "45"}
    head, _ = cards_item_abilities._pane_parts(["Phantom Assassin blurs her body. Vanish radius: 625/550/475/400."], props)
    assert "aoe.png" not in head and "castrange.png" not in head
    assert "manacost.png" in head and "cooldown.png" in head
    head, _ = cards_item_abilities._pane_parts(["Shields allies nearby."], {"kind": "Active", "aoe": "1200", "castrange": "1200"})
    assert head.count("iab-ico") == 1 and "aoe.png" in head
    head, _ = cards_item_abilities._pane_parts(["Throws a flare."], {"kind": "Active", "aoe": "300", "castrange": "700"})
    assert "aoe.png" in head and "castrange.png" in head


def test_header_value_gets_its_percent_on_hover():
    cards_item_abilities._CARD_CONFIRMED.add((991, "manacost"))
    html = cards_item_abilities.resolve_chip_marks("<!--CHIPMARK:991:manacost:buff:200/300/400-->200/250/300<!--/CHIPMARK-->")
    assert "iab-hl-num" in html and "iab-tip-pct" in html and "-17%" in html
    old = cards_item_abilities.resolve_chip_marks("<!--CHIPMARK:991:manacost:nerf:-->200/300/400<!--/CHIPMARK-->")
    assert "iab-tip-pct" not in old and "iab-hl-nerf" in old
    assert cards_item_abilities.resolve_chip_marks("<!--CHIPMARK:992:manacost:buff:1-->2<!--/CHIPMARK-->") == "2"


def test_by_percent_goes_after_flat_aghanim_numbers():
    text = ("Increases cast range and projectile speed by 25%. When it impacts heroes, 2 wards are created.\n"
            "Cast range: +200. Projectile speed: +300.")
    out = cards_aghs._aghs_inline(text)
    assert out.startswith("Increases cast range (+200) and projectile speed (+300).") and "25%" not in out
    # another effect's "by 25%" stays
    out = cards_aghs._aghs_inline("Reduces armor and slows by 25%.\nArmor: -5.")
    assert "slows by 25%" in out


def test_innate_row_under_its_card_is_hidden():
    _State.card_innate = "Poison Sting"
    try:
        row = el.li("Poison Sting is now an innate ability (previously a basic ability)", "")
        assert "iab-covered" in row
        row = el.li("Silent as the Grave is now an innate ability (previously granted by Aghanim's Scepter)", "")
        assert "iab-covered" not in row
    finally:
        _State.card_innate = None


def test_card_without_caption_has_no_caption_row():
    html = cards_aghs._under_rows_card(None, "rework", "", "scale-change", "<div>o</div>", "<div>n</div>")
    assert "under-rows-caption" not in html and "scale-change" in html
