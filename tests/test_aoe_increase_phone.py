"""AoE Increase on a phone: the hero column is the hero's icon, its name kept for search and screen readers (design
review 2026-11-21: the name took 60% of a 375 px screen and one ability column showed)."""
from patch.css_bundle import read_css


def test_the_hero_is_its_icon_on_a_phone():
    css = read_css()
    block = css.split("td.aoe-name .mr-name-body { vertical-align: middle; }", 1)[1].split("}\n}", 1)[0]
    assert "@media (max-width: 760px)" in block
    assert ".mr-table.aoe-table td.aoe-name .mr-name-body, .mr-table.aoe-table thead th.aoe-name .th-label" in block
    assert "clip: rect(0 0 0 0)" in block                 # visually hidden, not display:none: search still reads it
