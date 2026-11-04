"""7.40 Assist Gold Formula (owner 2026-10-27: "tags of different sizes?"): the formula block's title tag is 64px wide,
like every row's tag (it was 60px — the width rule covered only ul.changes rows)."""
from patch.css_bundle import read_css
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_formula_title_tag_is_as_wide_as_a_rows():
    css = read_css()
    rule = re.search(r"\.formula-change-title > \.badge \{([^}]*)\}", css)
    assert rule and "width: 64px" in rule.group(1) and "min-width: 64px" in rule.group(1)
