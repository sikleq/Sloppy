"""Phone layout rules that a 2026-11-19 visual check found broken (measured with Playwright at 390px):
Hero Stats / Mana Items lost their sticky column heads, hero / item / unit pages scrolled 48px sideways."""
import re

from patch.css_bundle import read_css

CSS = re.sub(r"/\*.*?\*/", "", read_css(), flags=re.S)


def _phone_blocks():
    """Bodies of every @media (max-width: 760px) block."""
    out = []
    for m in re.finditer(r"@media \(max-width: 760px\)\s*\{", CSS):
        depth, i = 1, m.end()
        while depth and i < len(CSS):
            depth += {"{": 1, "}": -1}.get(CSS[i], 0)
            i += 1
        out.append(CSS[m.end():i - 1])
    return "\n".join(out)


def _rules(selector):
    """Declarations of every phone rule whose selector is exactly `selector`."""
    return [body for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", _phone_blocks())
            if selector in [s.strip() for s in sel.split(",")]]


def test_table_inside_the_scroll_box_is_not_a_scroll_box_of_its_own():
    # a sticky <th> sticks to its nearest scroll box: .mr-table { display: block; overflow-x: auto } inside
    # .creeps-scroll made the table that box, and the heads left with it (th at -1070px after scrolling)
    assert not any("overflow" in body for body in _rules(".mr-table"))
    assert any("overflow-x: auto" in body for body in _rules(":not(.creeps-scroll) > .mr-table"))
    assert any("max-content" in body for body in _rules(".creeps-scroll > .mr-table"))


def test_nested_menu_flyout_is_in_the_flow_on_a_phone():
    # left: 100% of a 160px menu put the hidden flyout at x=436 on a 390px screen: scrollWidth 438
    bodies = _rules(".nav-submenu-flyout")
    assert bodies, "no phone rule for .nav-submenu-flyout"
    assert "position: static" in bodies[0] and "visibility: inherit" in bodies[0]
