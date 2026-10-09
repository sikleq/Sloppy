"""Several (?) at the end of one row become one (owner 2026-10-09, Earth Spirit 7.40 "Base Damage decreased by 6")."""
from patch.elements import info_tip, inline_note, merge_tips


def test_two_tips_become_one_with_both_notes():
    merged = merge_tips([info_tip("Now it's <b>25</b>."), info_tip("Damage at level 1 decreased from 53–57 to 47–51")])
    assert len(merged) == 1
    assert merged[0].count('class="info-tip"') == 1 and merged[0].count('class="pop-part"') == 2
    assert "Now it's <b>25</b>." in merged[0] and "47–51" in merged[0]


def test_one_tip_or_another_shape_stays():
    one = [info_tip("x")]
    assert merge_tips(one) == one
    odd = [info_tip("x"), "<span>not a tip</span>"]
    assert merge_tips(odd) == odd


def test_a_row_with_a_note_box_and_an_inline_note_shows_one_question_mark():
    from patch.elements import li
    html = li("Base Damage decreased by 6", extra=inline_note("Now it's 25.") + inline_note("Damage at level 1 changed"))
    assert html.count('class="info-tip"') == 1
