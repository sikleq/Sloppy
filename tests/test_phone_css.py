"""The phone block of styles.css (2026-10-05): last in the file and entirely inside one narrow-screen media query,
so nothing in it can reach the desktop layout (docs/agent-rules/ui-style.md "Телефоны")."""
from pathlib import Path

CSS = (Path(__file__).resolve().parent.parent / "styles.css").read_text(encoding="utf-8")


def _phone_block():
    start = CSS.index("PHONES (2026-10-05)")
    body = CSS[CSS.index("*/", start) + 2:].strip()
    return body


def test_phone_rules_sit_in_one_narrow_media_query_at_the_end():
    body = _phone_block()
    assert body.startswith("@media (max-width: 760px) {")
    depth, closed_at = 0, None
    for i, ch in enumerate(body):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                closed_at = i
                break
    assert closed_at is not None
    assert body[closed_at + 1:].strip() == "", "nothing may follow the phone block (it must win the cascade, and "\
                                               "a rule after it would not be phone-only)"


def test_phone_block_hides_the_in_row_popup_copies_that_widened_the_page():
    body = _phone_block()
    assert ".info-tip .info-pop { display: none; }" in body
    assert ".enchant-chip[data-tooltip]::after" in body
