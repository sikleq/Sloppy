"""An example named in a row or a text carries its icon, and the row's words stay readable from the source (owner 2026-11-05)."""
import ast
import os

import pytest

from patch.elements import li
from patch.mech_abilities import mech_example, row_examples
from tools.patchgen.post_general import _postprocess_example_icons

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_a_label_shows_the_words_of_the_text_with_the_icon_of_the_full_name():
    html = mech_example("Batrider's Firefly", label="Firefly")
    assert "batrider_firefly" in html
    # the icon alone, the ability's name on hover, without "Batrider's" (2026-11-07: "только название способности")
    assert 'data-tooltip="Firefly"' in html


def test_row_examples_replaces_the_words_once():
    html, note = row_examples("by Batrider during Firefly", {"Firefly": "Batrider's Firefly"})
    assert html.startswith("by Batrider during <span") and note == ""


def test_an_aside_naming_an_example_goes_under_the_question_mark_with_its_icon():
    # owner 2026-11-07, 7.38 Ice Wall: "тут Gleipnir иконкой надо. И в целом эту часть в скобках можно под [?] сделать"
    text, note = row_examples("Flat AoE bonuses (like those granted by Gleipnir) no longer increase radial thickness",
                              {"Gleipnir": "Gleipnir"})
    assert text == "Flat AoE bonuses no longer increase radial thickness"
    assert note.startswith("Like those granted by <span") and "gungir" in note


def test_li_puts_the_aside_into_its_note():
    html = li("Flat AoE bonuses (like those granted by Gleipnir) no longer increase the wall", "",
              examples={"Gleipnir": "Gleipnir"})
    assert "(like" not in html and "INLINETIP" not in html and "Like those granted by" in html


def test_generator_reads_like_those_granted_by():
    out = _postprocess_example_icons(['W(li("Flat AoE bonuses (like those granted by Gleipnir) no longer", t("REWORK")))'])
    assert out[0].endswith("examples={'Gleipnir': 'Gleipnir'}))")


def test_row_examples_stops_on_words_the_row_does_not_have():
    with pytest.raises(ValueError):
        row_examples("no such words", {"Firefly": "Batrider's Firefly"})


def test_li_shows_the_icon_and_keeps_its_tag():
    html = li("e.g. Shiva's Guard counts once", "", examples={"Shiva's Guard": "Shiva's Guard"})
    assert "shivas_guard" in html


def _row_of(path, words):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "li" and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str) and words in first.value:
                return node
    return None


def test_the_map_row_of_740_stays_a_literal_the_terrain_page_can_read():
    node = _row_of("content/p740.py", "during Firefly")
    assert node is not None
    assert any(k.arg == "examples" for k in node.keywords)


def test_generator_adds_examples_to_a_row_naming_them():
    out = _postprocess_example_icons(['W(li("Counts once (e.g. Shiva\'s Guard will count as 1)", t("NERF")))'])
    assert out == ['W(li("Counts once (e.g. Shiva\'s Guard will count as 1)", t("NERF"), examples={"Shiva\'s Guard": "Shiva\'s Guard"}))']


def test_generator_output_is_valid_python_for_several_examples():
    out = _postprocess_example_icons(['W(li("Debuffs like Mask of Madness or Lotus Orb\'s Echo Shell", t("MISC")))'])
    call = ast.parse(out[0].strip()).body[0].value.args[0]
    keys = ast.literal_eval(next(k.value for k in call.keywords if k.arg == "examples"))
    assert keys == {"Mask of Madness": "Mask of Madness", "Lotus Orb's Echo Shell": "Lotus Orb's Echo Shell"}


def test_generator_leaves_words_without_an_icon_and_other_lines():
    for line in ['W(li("Like Lotus Pools, the Shrine will not count", t("MISC")))',
                 'W(li("Plain row", t("MISC")))', 'W(ul_open())']:
        assert _postprocess_example_icons([line]) == [line]
