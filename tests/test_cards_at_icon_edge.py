"""Owner 2026-11-04: a card under an ability starts at the icon's left edge, on the vertical of the block's other boxes
("There is only a single Tormentor…"), clear of the icon; a thin solid line goes from the icon's bottom down into it
(variant 1 of the mock, instead of a dashed line round the icon)."""
from patch.css_bundle import read_css
from patch.js_bundle import read_js
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*path):
    with open(os.path.join(ROOT, *path), encoding="utf-8") as f:
        return f.read()


def test_cards_span_the_icon_column():
    css = read_css()
    rule = re.search(r"\.ability-block > \.ability-change,\s*\.ability-block > \.properties-change \{([^}]*)\}", css)
    assert rule and "grid-column: 1 / -1" in rule.group(1)


def test_rows_of_the_block_stay_in_their_column():
    # after a card the grid would put a row without a column under the icon
    css = read_css()
    for selector in (r"\.ability-block > ul\.changes", r"\.ability-block > ul\.subnotes"):
        assert re.search(selector + r" \{\s*grid-column: 2;", css), selector


def test_the_card_keeps_clear_of_the_icon():
    css = read_css()
    for selector in (r"\.ability-change-block \.ability-change\.unified-panes \{",
                     r"\.ability-block > \.under-rows-caption \+ \.ability-change \{[^}]*",
                     r"\.ability-block > \.under-rows-connector \+ \.ability-change \{[^}]*"):
        rule = re.search(selector + r"\s*margin-top: (\d+)px", css)
        assert rule and int(rule.group(1)) >= 12, selector


def test_the_line_goes_straight_from_the_icon_into_the_card():
    js = read_js()
    body = re.search(r"function connectorPath\(blockRect, iconRect, paneRect\) \{(.*?)\n  \}", js, re.S).group(1)
    assert "iconRect.bottom - blockRect.top" in body and "paneRect.top - blockRect.top" in body
    assert body.count(" L ") == 1                        # one straight piece, no elbow
    # both kinds of card; a card under rows starts under the card before it, if there is one (7.38 Flux, owner 2026-11-05)
    assert js.count("connectorPath(blockRect, iconRect, paneRect));") == 1
    assert js.count("connectorPath(blockRect, start, paneRect));") == 1


def test_the_line_is_solid_and_styled_in_one_place():
    rule = re.search(r"\.ability-change-connector path \{([^}]*)\}", read_css())
    assert rule and "stroke:" in rule.group(1) and "dash" not in rule.group(1)
    for path in (("patch", "cards_ability_change.py"), ("patch", "cards_facets.py"), ("patch", "cards_aghs.py")):
        source = _read(*path)
        assert 'class="ability-change-connector' in source
        assert '<path d="" />' in source and 'stroke-dasharray="3 3"' not in source, path


def test_the_brewling_tree_keeps_its_own_dashed_line():
    assert "stroke-dasharray: 4 3" in re.search(r"\.brewling-connector path \{([^}]*)\}", read_css()).group(1)


def test_no_card_hangs_left_of_the_icon():
    # item cards hung 15px left of the item's icon (owner 2026-11-04: "нет единого положения карточек")
    css = read_css()
    assert not re.search(r"(?:components-change|properties-change|ench-change|ability-box-tagged)[^{}]*\{[^}]*margin-left: -15px", css)
    assert not re.search(r"(?:ability-row|provides-box|components-box)[^{}]*\{[^}]*margin-left: -15px", css)


def test_a_new_ability_card_has_the_line_too():
    # 7.38 Alleviation: the card has only its new pane
    from patch import cards_ability_change, elements as el
    html = cards_ability_change.ability_change(None, {"name": "Alleviation", "icon_url": "x.png", "desc": ["Heals."]},
                                               summary="New ability", tag="new")
    el._close_ability_block()
    assert "is-single-new" in html and 'class="ability-change-connector"' in html
    js = read_js()
    assert ":scope > .ability-change > .ability-change-new" in js


_TITLE = '<div class="ability-block"><div class="ability-icon-wrap"></div><h4 class="ability-title">Arm of the Deep</h4>\n'
_BOX = '<li class="ability-row item-ability li-notag"><span class="row-text">Active</span></li>'
_ROW = '<li data-tag="buff"><span class="badge buff">BUFF</span><span class="row-text">Damage</span></li>'


def test_an_ability_told_only_by_boxes_stands_beside_the_icon():
    # 7.38 Riverborn Aura: as Water Bubble (Large), whose box has a row below it (owner 2026-11-07: "не лучше Riverborn
    # Aura расположить также, как Water Bubble (Large)?") — no card under the icon, no line
    from patch.page import _wrap_ability_boxes
    alone = _wrap_ability_boxes(_TITLE + f'<ul class="changes">{_BOX}</ul></div>')
    mixed = _wrap_ability_boxes(_TITLE + f'<ul class="changes">{_BOX}{_ROW}</ul></div>')
    for html in (alone, mixed):
        assert '<ul class="changes">' in html and "<svg" not in html
    assert "ability-card-rows" not in read_css() and "ability-card-rows" not in read_js()


def test_a_new_facet_card_has_the_line_too():
    # 7.38 Dividends, Runed Replica: a facet's card is one of the site's cards
    from patch import cards_facets, elements as el
    from patch.badges import FACETS
    html = cards_facets.new_facet(next(iter(FACETS)), ["Grants gold."])
    el._close_ability_block()
    assert "is-single-new" in html and 'class="ability-change-connector"' in html
