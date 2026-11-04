"""tools/css_dead_rules.py: it may only call dead what can never take effect."""
from tools.css_dead_rules import dead_declarations, rules


def _dead(css):
    return [(r.selector, d.prop, d.value) for r, d, _later in dead_declarations(css)]


def test_a_later_declaration_of_the_same_selector_kills_the_earlier():
    assert _dead(".a { color: red; margin: 0 } .b { color: blue } .a { color: green }") == [(".a", "color", "red")]


def test_a_different_media_does_not_kill():
    assert _dead(".a { color: red } @media (max-width: 700px) { .a { color: green } }") == []
    assert _dead("@media (max-width: 700px) { .a { color: red } .a { color: green } }") == [(".a", "color", "red")]


def test_important_does_not_lose_to_a_plain_declaration():
    assert _dead(".a { color: red !important } .a { color: green }") == []


def test_a_selector_list_counts_as_written():
    assert _dead(".a, .b { color: red } .a { color: green }") == []
    assert _dead(".a,.b { color: red } .a ,  .b { color: green }") == [(".a, .b", "color", "red")]


def test_a_value_a_browser_may_reject_keeps_the_earlier_as_its_fallback():
    assert _dead(".a { height: 100vh; height: 100dvh }") == []
    assert _dead(".a { color: red; color: color-mix(in srgb, red, blue) }") == []
    assert _dead(".a { width: 10px; width: clamp(1px, 2vw, 3px) }") == []


def test_vendor_prefixes_are_left_alone():
    assert _dead(".a { -webkit-box-shadow: none; -webkit-box-shadow: 0 0 1px red }") == []


def test_keyframes_and_font_face_are_left_alone():
    assert _dead("@keyframes x { from { top: 0 } from { top: 1px } } @font-face { src: url(a) ; src: url(b) }") == []


def test_data_urls_comments_and_strings_do_not_break_the_parse():
    css = """.a { background: url(data:image/png;base64,AA==); /* ; } */ content: "}"; color: red }"""
    assert [d.prop for d in rules(css)[0].decls] == ["background", "content", "color"]
