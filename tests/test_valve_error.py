"""A mistake in Valve's notes: the tag glows red, the real change on hover, no note under a [?] (owner 2026-11-21)."""
from patch.valve_error import HEAD, valve_error_tags

_ROW = ('<li data-tag="nerf" class="li-bg"><span class="badge nerf-text" data-tag="nerf">NERF</span><span class="row-text">'
        'Rush Range decreased from <span class="wrong-word">575</span> to <span class="li-tail">525<span class="info-tip" '
        'tabindex="0">?<span class="info-pop"><span class="info-pop-h">Note:</span>{note}</span></span></span></span></li>')


def test_the_note_moves_to_the_tags_hover():
    out = valve_error_tags(_ROW.format(note="This change is wrongly stated. The real change is 650 &rarr; 525"))
    # the gold head every tooltip has, the words under it (owner 2026-11-21)
    assert (f'data-tooltip="&lt;b class=&quot;tip-head&quot;&gt;{HEAD}&lt;/b&gt;The real change is 650 → 525" '
            'tabindex="0" class="tb-tip-target valve-error badge') in out
    assert "info-tip" not in out and "wrongly stated" not in out
    assert '<span class="wrong-word">575</span>' in out


def test_a_wrong_direction_word_keeps_its_sentence():
    out = valve_error_tags(_ROW.format(note='The patch text says "decreased", but the values actually went up.'))
    assert "valve-error" in out and "the values actually went up." in out and "info-tip" not in out


def test_a_merged_question_mark_keeps_its_other_part():
    # 7.42 Tormentor (advisor review 2026-11-21): the note is one pop-part of two; no empty part may stay
    li = ('<li data-tag="nerf"><span class="badge nerf-text" data-tag="nerf">NERF</span><span class="row-text">x '
          '<span class="li-tail"><span class="info-tip" tabindex="0">?<span class="info-pop"><span class="pop-part">'
          '<span class="info-pop-h">Note:</span>This change is wrongly stated. It was 30% since 7.41</span>'
          '<span class="pop-part">Still grows over time</span></span></span></span></span></li>')
    out = valve_error_tags(li)
    assert '<span class="info-pop"><span class="pop-part">Still grows over time</span></span>' in out
    assert "pop-part\"></span>" not in out and "It was 30% since 7.41" in out.split("data-tooltip=")[1]
    assert out.count("<span") == out.count("</span>")


def test_a_covered_row_and_a_percent_badge_are_not_marked():
    covered = _ROW.format(note="This change is wrongly stated. x").replace('class="li-bg"', 'class="iab-covered li-bg"')
    assert valve_error_tags(covered) == covered
    untagged = ('<li><span class="row-text">a <span class="info-tip" tabindex="0">?<span class="info-pop">This change is '
                'wrongly stated. y</span></span></span><span class="badge nerf4">-10%</span></li>')
    assert "valve-error" not in valve_error_tags(untagged)


def test_every_item_cards_before_number_is_the_files_one():
    # 7.42 Crimson Guard: Valve's "+4 -> +5 Armor", the files 6 -> 5 (owner 2026-11-21: "Везде всё проверь")
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "audit"))
    from audit_card_values import card_mismatches
    found, checked, _ = card_mismatches()
    assert not found, f"check each and add it to data/rules/valve_errors.json: {found}"
    assert checked >= 100


def test_a_card_with_valves_mistake_shows_the_files_number_and_a_red_tag():
    import sys
    sys.path.insert(0, "tools")
    from patchgen.post_late import _postprocess_valve_card_errors
    from patch.cards_item_stats import _prop_tag
    lines = ['    W(item_header("Crimson Guard", changed=True))',
             '    W(properties_change(old=[("BUFF", "+4 Armor")], new=[("", "+5 Armor", b(4, 5))]))']
    out = _postprocess_valve_card_errors(lines, "7.42")[1]
    assert '("", "+6 Armor")' in out and 'b(6, 5)' in out and '("NERF|Patch notes state: +4 Armor &rarr; +5 Armor<br>Game files: +6 Armor' in out
    assert _postprocess_valve_card_errors([lines[0], out], "7.42")[1] == out          # once
    tag = _prop_tag("NERF|Patch notes state: +4 Armor &rarr; +5 Armor")
    assert '&lt;b class=&quot;tip-head&quot;&gt;Error in the patch notes&lt;/b&gt;Patch notes state: +4' in tag
    assert 'class="tb-tip-target valve-error badge' in tag and ">NERF<" in tag and 'tabindex="0"' in tag


def test_rows_without_the_mark_are_left_alone():
    row = _ROW.format(note="Dormant Curio increases min range to 260")
    assert valve_error_tags(row) == row
