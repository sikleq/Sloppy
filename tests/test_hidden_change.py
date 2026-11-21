"""A change not in Valve's notes: its tag glows gold and says "Hidden change" on hover (owner 2026-11-21: the [?] alone
was not seen)."""
from patch.hidden_change import TIP, hidden_change_tags

_ROW = ('<li data-tag="buff" class="li-bg"><span class="badge buff-text" data-tag="buff">BUFF</span><span class="row-text">'
        'Damage bonus increased from +25 to <span class="li-tail">+30<span class="info-tip" tabindex="0">?<span '
        'class="info-pop">{note}</span></span></span></span></li>')


def test_the_stock_note_becomes_the_tags_hover():
    out = hidden_change_tags("<ul>" + _ROW.format(note="Not in the patch notes: found in the game files") + "</ul>")
    assert f'data-tooltip="{TIP}" class="tb-tip-target hidden-change badge buff-text"' in out
    assert "info-tip" not in out and "Not in the patch notes" not in out


def test_words_of_its_own_stay_in_the_question_mark():
    out = hidden_change_tags(_ROW.format(note="It gave +35 Movement Speed before it was cycled out. Not in the patch "
                                              "notes: found in the game files"))
    assert '<span class="info-pop">It gave +35 Movement Speed before it was cycled out.</span>' in out
    out = hidden_change_tags(_ROW.format(note="Not in the patch notes: before 7.42 the penalty did not apply at all "
                                              "(found in the game files)"))
    assert '<span class="info-pop">Before 7.42 the penalty did not apply at all</span>' in out
    assert "hidden-change" in out


def test_other_rows_are_left_alone():
    row = _ROW.format(note="Dormant Curio increases min range to 260")
    assert hidden_change_tags(row) == row
