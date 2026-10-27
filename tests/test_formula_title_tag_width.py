"""7.40 Assist Gold Formula (owner 2026-10-27: "tags of different sizes?"): the formula block's title tag is 64px wide,
like every row's tag (it was 60px — the width rule covered only ul.changes rows)."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_formula_title_tag_is_as_wide_as_a_rows():
    with open(os.path.join(ROOT, "styles.css"), encoding="utf-8") as f:
        css = f.read()
    rule = re.search(r"\.formula-change-title > \.badge \{([^}]*)\}", css)
    assert rule and "width: 64px" in rule.group(1) and "min-width: 64px" in rule.group(1)
