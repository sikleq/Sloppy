"""A change not in Valve's notes: its tag glows gold and says "Hidden change" on hover (owner 2026-11-21: the [?] alone
was not seen)."""
from patch.hidden_change import TIP, hidden_change_tags

_ROW = ('<li data-tag="buff" class="li-bg"><span class="badge buff-text" data-tag="buff">BUFF</span><span class="row-text">'
        'Damage bonus increased from +25 to <span class="li-tail">+30<span class="info-tip" tabindex="0">?<span '
        'class="info-pop">{note}</span></span></span></span></li>')


def test_the_stock_note_becomes_the_tags_hover():
    out = hidden_change_tags("<ul>" + _ROW.format(note="Not in the patch notes: found in the game files") + "</ul>")
    # the gold head, as every tooltip of the site (owner 2026-11-21)
    assert f'data-tooltip="&lt;b class=&quot;tip-head&quot;&gt;{TIP}&lt;/b&gt;" tabindex="0" class="tb-tip-target hidden-change badge buff-text"' in out
    assert "info-tip" not in out and "Not in the patch notes" not in out


def test_words_of_its_own_stay_in_the_question_mark():
    out = hidden_change_tags(_ROW.format(note="It gave +35 Movement Speed before it was cycled out. Not in the patch "
                                              "notes: found in the game files"))
    assert '<span class="info-pop">It gave +35 Movement Speed before it was cycled out.</span>' in out
    out = hidden_change_tags(_ROW.format(note="Not in the patch notes: before 7.42 the penalty did not apply at all "
                                              "(found in the game files)"))
    assert '<span class="info-pop">Before 7.42 the penalty did not apply at all</span>' in out
    assert "hidden-change" in out


def test_hidden_rows_go_under_their_anchor_once():
    # data/rules/hidden_rows.json 7.42 (owner 2026-11-21): Dire's top small camp; Fiend's Gate's Scepter shots are a
    # draft not in the game ("Не путай заготовки с тем, что скрыто добавили") and must not come back
    import sys
    sys.path.insert(0, "tools")
    from patchgen.post_late import _postprocess_hidden_rows
    lines = ['    W(ability("Fiend\'s Gate", slug="abyssal_underlord_dark_portal"))', "    W(ul_open())",
             '    W(li("Cooldown rescaled", t("MISC")))', "    W(ul_close())",
             '    W(li("Each camp unit now has a \\"home jungle\\", meaning …", t("REWORK")))']
    out = _postprocess_hidden_rows(lines, "7.42")
    assert "portals now shoot" not in "".join(out) and out[3] == "    W(ul_close())"
    assert "never spawns the Vhoul camp" in out[5]
    assert _postprocess_hidden_rows(out, "7.42") == out


def test_pugnas_shard_cast_range_in_7_41d():
    # 7.41d (owner 2026-11-21: "Да, добавь"): Valve named the base 150 -> 175 only, the Shard's =350 -> =375 too
    import sys
    sys.path.insert(0, "tools")
    from patchgen.post_late import _postprocess_hidden_rows
    lines = ['    W(ability("Nether Ward", slug="pugna_nether_ward"))', "    W(ul_open())",
             '    W(li("Cast Range increased from 150 to 175", b(150, 175)))', "    W(ul_close())"]
    out = _postprocess_hidden_rows(lines, "7.41d")
    assert "Aghanim's Shard Cast Range increased from 350 to 375" in out[3] and "Not in the patch notes" in out[3]
    assert _postprocess_hidden_rows(out, "7.41d") == out


def test_other_rows_are_left_alone():
    row = _ROW.format(note="Dormant Curio increases min range to 260")
    assert hidden_change_tags(row) == row


def test_a_glowing_diamond_has_the_tags_ring():
    # 7.42 Dire base shop: the map row's diamond glowed but had no ring (owner 2026-11-21: "тут нет обводки")
    from patch.css_bundle import read_css
    css = read_css()
    # the tag's size and shadows (owner 2026-11-21: "не совпадает с обводкой у тега по размеру")
    ring = css.split(".tnum-dia.hidden-change::after, .tnum-dia.valve-error::after {", 1)[1].split("}", 1)[0]
    assert "width: 22px; height: 18px;" in ring and "border-radius: 3px;" in ring
    tag = css.split(".badge.hidden-change { box-shadow:", 1)[1].split(";", 1)[0].strip()
    assert f"box-shadow: {tag};" in ring
