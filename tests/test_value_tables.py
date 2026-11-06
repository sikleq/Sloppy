"""A card's values as a table (owner 2026-11-05), patch/value_tables.py."""
import pathlib
import re

from patch.value_tables import _LI_RE, _TRIGGER_RE, _div_end, _formula_key, value_tables

FORMULA = ('<span class="formula-trigger" data-formula="f72"><b class="iab-num">27</b> + <b class="iab-num">3</b> per level</span>')
WRAP = '<div class="formula-table-wrap"><table class="formula-table" id="f72" hidden><tr><td>30</td></tr></table></div>'


def _card(row, tail=""):
    return '<div class="ability-change-body"><div class="ability-change-row">' + row + "</div>" + tail + "</div>"


def test_three_values_or_more_become_a_table_after_the_sentence():
    html = value_tables(_card('Sends them flying. Speed: <b class="iab-num">1600</b>. Distance: <b class="iab-num">1200</b>. '
                              'Damage: <b class="iab-num">7%</b>.'))
    assert html.count('class="vt-l') == 3 and html.count('class="vt-v') == 3
    assert html.index("Sends them flying.") < html.index('class="value-table"')
    assert '<div class="vt-v vt-first"><b class="iab-num">1600</b></div>' in html


def test_a_sentence_is_no_value_and_two_values_stay_text():
    html = value_tables(_card("Grants this ability: Summons archers. Range: 900. Count: 5. Spawn interval: 0.15"))
    assert "Grants this ability: Summons archers." in html and html.count('class="vt-l') == 3
    # two values make a table too (owner 2026-11-06), one stays text
    assert value_tables(_card("Range: 900. Count: 5.")).count('class="vt-l') == 2
    one = _card("Summons archers. Range: 900.")
    assert value_tables(one) == one


def test_a_formula_is_a_value_and_its_level_table_opens_under_its_row():
    html = value_tables(_card("Speed: 1600. Damage: " + FORMULA + ". Distance: 1200.", WRAP))
    table = html[html.index('class="value-table"'):]
    assert table.index("Damage") < table.index('id="f72"') < table.index("Distance")
    assert html.count('id="f72"') == 1


def test_a_value_with_dots_inside_and_a_tooltip_with_a_full_stop_stay_whole():
    tip = '<span class="iab-hint" data-tooltip="Was 2. Now 3.">0.4/0.6</span>'
    html = value_tables(_card("Duration: 2.5s. Vanish buffer: " + tip + ". Radius: 375."))
    assert '<div class="vt-v">' + tip + "</div>" in html and '<div class="vt-v vt-first">2.5s</div>' in html


def test_rows_already_laid_out_are_left_alone():
    selves = _card('<span class="selves-table">Damage: 1. Speed: 2. Slow: 3.</span>')
    assert value_tables(selves) == selves


def test_every_built_page_keeps_each_formula_table_once():
    root = pathlib.Path(__file__).resolve().parents[1] / "dist" / "patches"
    for page in root.glob("*.html"):
        s = page.read_text(encoding="utf-8")
        for fid in set(re.findall(r'data-formula="([^"]+)"', s)):
            assert s.count(f'id="{fid}"') == 1, (page.name, fid)


def test_one_card_decides_for_both_its_sides():
    card = ('<div class="ability-change unified-panes"><div class="ability-change-pane ability-change-old"><div class="ability-change-body">'
            '<div class="ability-change-row">Health regen per kill: 3.5. Mana regen per kill: 3.5. Hero kill multiplier: 6.</div></div></div>'
            '<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
            '<div class="ability-change-row">Hp/mana regen: 3.7. Hero kill multiplier: 6.</div></div></div></div>')
    html = value_tables(card)
    assert html.count('class="value-table"') == 2 and html.count('class="vt-l') == 5


def test_a_lone_note_after_the_last_value_stays_with_it():
    tip = '<span class="info-tip">?<span class="info-pop">Was 8</span></span>'
    html = value_tables(_card("Lifesteal: 12%. Max health: 10%. Max mana: 10%. " + tip))
    assert '<div class="vt-v">10%' + tip + "</div>" in html and "vt-after" not in html


def test_a_name_with_an_icon_of_its_own_shows_it():
    row = ('<img class="ac-sub-ico" src="../icons/_t/abilities/oracle_diviners_deck.webp" alt=""> Grants this ability: pulls a card. '
           "Death: 40% Spell Amplification. The Fool: 100% Increased Gold Gain. Unknown Card: 5%.")
    html = value_tables(_card(row))
    assert 'aria-label="The Fool"' in html and "oracle_diviners_deck_the_fool.png" in html
    assert 'aria-label="Unknown Card"' not in html


def test_a_long_bracket_after_a_value_goes_under_a_note():
    html = value_tables(_card("Death: 40%. Tower: 400 All Damage Barrier (regenerates after not taking damage for 7s). "
                              "Range: 900 (short)."))
    assert "400 All Damage Barrier<!--INLINETIP-->" in html and "(regenerates" not in html
    assert "900 (short)" in html


def test_no_card_shows_a_level_formula_as_plain_text():
    # 7.41 Outworld Destroyer's card said "40% + 5% per 5 levels" with no level table (owner 2026-11-05); rows keep their
    # old formula as text ("changed from 10% + 1% per level to ..."), cards must not
    formula = re.compile(r"\d+(?:\.\d+)?%? \+ \d+(?:\.\d+)?%? per (?:\d+ )?levels?")
    root = pathlib.Path(__file__).resolve().parents[1] / "dist" / "patches"
    bad = []
    for page in root.glob("*.html"):
        s = page.read_text(encoding="utf-8")
        for start in (m.start() for m in re.finditer(r'<div class="ability-change-pane[ "]', s)):
            pane = s[start:_div_end(s, start)]                  # the pane alone, closed where its own <div> closes
            text = re.sub(r"<[^>]+>", "", re.sub(r'<span class="formula-trigger"[^>]*>.*?</span>', "", pane, flags=re.S))
            # a formula a row of the same block opens is plain in the card on purpose (owner 2026-11-06, 7.41 Persecutor)
            b = s.rfind('<div class="ability-block', 0, start)
            block = s[b:_div_end(s, b)] if b >= 0 else ""
            said = {_formula_key(t.group(2)) for li in _LI_RE.finditer(block) for t in _TRIGGER_RE.finditer(li.group(0))}
            bad += [f"{page.name}: {m.group(0)}" for m in formula.finditer(text) if m.group(0) not in said]
    assert not bad, bad[:10]


def test_a_one_sided_aghanims_card_is_as_wide_as_one_side():
    css = (pathlib.Path(__file__).resolve().parents[1] / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    # every one-sided card ("New ability." too, owner 2026-11-05), not only Aghanim's
    rule = css[css.index(".ability-change.unified-panes.is-single-new {"):]
    assert "grid-template-columns: 1fr 23px 1fr;" in rule[:rule.index("}")]
    pane = css[css.index(".ability-change.unified-panes.is-single-new > .ability-change-pane {"):]
    assert "grid-column: 1;" in pane[:pane.index("}")]
    assert "aghs-change.is-single-new { grid-template-columns" not in css


def test_each_formula_table_stands_under_the_row_with_its_button():
    trig = lambda fid: f'<span class="formula-trigger" data-formula="{fid}">40% + 5% per 5 levels</span>'
    wrap = lambda fid: f'<div class="formula-table-wrap"><table class="formula-table" id="{fid}" hidden><tr><td>1</td></tr></table></div>'
    body = ('<div class="ability-change-body"><div class="ability-change-row">Passive.</div>'
            '<div class="ability-change-row">Regular: ' + trig("f1") + '.</div>'
            '<div class="ability-change-row">Attack: ' + trig("f2") + '.</div>' + wrap("f1") + wrap("f2") + "</div>")
    html = value_tables(body)
    assert html.index('data-formula="f1"') < html.index('id="f1"') < html.index("Attack:") < html.index('id="f2"')
    assert html.count('id="f1"') == 1 and html.count('id="f2"') == 1


def test_a_cards_lines_stand_close_together():
    root = pathlib.Path(__file__).resolve().parents[1] / "src" / "css"
    labels = (root / "patch-entity-labels.css").read_text(encoding="utf-8")
    assert ".ability-change-row { padding: 1px 0;" in labels
    body = labels[labels.index(".ability-change-body {"):]
    assert "gap: 4px;" in body[:body.index("}")]
    assert "margin-top: -4px;" in (root / "patch-ability-change.css").read_text(encoding="utf-8")


def test_an_aghanims_row_puts_a_colon_after_the_abilitys_name():
    src = (pathlib.Path(__file__).resolve().parents[1] / "patch" / "cards_aghs.py").read_text(encoding="utf-8")
    assert src.count('or s) + ": "') == 3 and 'or slug) + ": " + esc(new)' in src
    assert 'or s) + " "' not in src


def test_a_step_every_few_levels_reads_per_n_levels():
    from patch.aghs_text import _per_level
    assert _per_level("40", "5", "%", "5") == "40% + 5% per 5 levels"
    assert _per_level("10", "1", "%") == "10% + 1% per level" and _per_level("10", "1", "%", "1") == "10% + 1% per level"
    assert _per_level("6.9", "-0.1") == "6.9 - 0.1 per level"


def test_an_upgrade_says_the_value_it_gives_not_the_bonus():
    # owner 2026-11-06: "Вообще везде можем сделать не +X, а to X"; 7.41 Mana Break read "(+1.5)" with no %
    from patch.aghs_text import _is_pct, _total
    assert _total("1.6 2.4 3.2 4.0", "+1.5") == "3.1/3.9/4.7/5.5"
    assert _total("12", "+4") == "16" and _total("36 34 32 30", "-10") == "26/24/22/20"
    assert _total("250", "x1.8") == "450" and _total("45 50 55 60", "-50%") == "22.5/25/27.5/30"
    assert _total("1200", "=-1") == "-1" and _total("", "+1") is None and _total("1 2", "1 2 3") is None
    assert _is_pct("MAX MANA BURNED PER HIT:", {"display_type": "kManaPercentage"}) and _is_pct("%MAX MANA BARRIER:", {})
    assert not _is_pct("BARRIER:", {"value": "120"})


def test_a_total_after_increases_reads_to_and_a_table_takes_every_value():
    from patch.cards_aghs import _aghs_inline
    assert _aghs_inline("Increases Max Mana Burned per Hit.\nMax mana burned per hit: =3.1/3.9/4.7/5.5%.") == \
        "Increases Max Mana Burned per Hit to 3.1/3.9/4.7/5.5%."
    assert _aghs_inline("Grants a barrier.\nBarrier: 300.") == "Grants a barrier (300)."
    # three values or more make a table: none goes into the sentence (7.41 Objurgation's barrier, owner 2026-11-06)
    text = "Protects with a barrier equal to a flat amount.\nBarrier: 120/180/240/300. Bonus mana: 80/160. Duration: 10."
    assert _aghs_inline(text, loose=False) == ("Protects with a barrier equal to a flat amount. Barrier: 120/180/240/300. "
                                               "Bonus mana: 80/160. Duration: 10.")


def test_a_formula_the_rows_already_open_is_plain_text_in_the_card():
    row = ('<li class="li-formula"><span class="row-text">Min Movement Slow rescaled from 12.5% to '
           '<span class="formula-trigger" data-formula="f53">12% + 0.5% per level</span></span>'
           '<table class="formula-table" id="f53" hidden></table></li>')
    card = ('<div class="ability-change unified-panes"><div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
            '<div class="ability-change-row">Min movement slow: <span class="formula-trigger" data-formula="f51"><b class="iab-num">12%</b>'
            ' + <b class="iab-num">0.5%</b> per level</span>. Max: <span class="formula-trigger" data-formula="f52">24% + 1% per level'
            '</span>.</div><div class="formula-table-wrap"><table class="formula-table" id="f51" hidden></table></div>'
            '<div class="formula-table-wrap"><table class="formula-table" id="f52" hidden></table></div></div></div></div>')
    from patch.value_tables import drop_formulas_said_above
    html = drop_formulas_said_above('<div class="ability-block"><ul class="changes">' + row + "</ul>" + card + "</div>")
    assert 'data-formula="f51"' not in html and 'id="f51"' not in html and '<b class="iab-num">12%</b> + ' in html
    assert 'data-formula="f53"' in html and 'id="f53"' in html          # the row keeps its own
    assert 'data-formula="f52"' in html and 'id="f52"' in html          # a formula no row opens stays a button


def test_a_value_table_has_no_frame_of_its_own_inside_the_card():
    css = (pathlib.Path(__file__).resolve().parents[1] / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    for sel in (".value-table {", ".selves-table {"):
        rule = css[css.index(sel):]
        rule = rule[:rule.index("}")]
        assert "border-radius" not in rule and "border: 1px" not in rule and "calc(-1 * var(--px, 0px))" in rule
    # on a phone the two-selves table scrolls inside the card, yet reaches both its edges (it stood 9px short)
    phones = (pathlib.Path(__file__).resolve().parents[1] / "src" / "css" / "phones.css").read_text(encoding="utf-8")
    assert "max-width: calc(100% + 2 * var(--px, 0px)); overflow-x: auto;" in phones


def test_a_card_formula_every_few_levels_gets_its_button_and_table():
    from patch.cards_item_abilities import _pill_formulas
    html, tables = _pill_formulas("Max Mana Restoration is <b>40% + 5% per 5 levels</b>.")
    assert 'class="formula-trigger"' in html and "40% + 5% per 5 levels" in html
    cells = re.findall(r"<td[^>]*>([^<]+)</td>", tables)
    heads = re.findall(r"<th[^>]*>L(\d+)</th>", tables)
    values = dict(zip(heads, cells))
    assert values["1"] == "40%" and values["5"] == "45%" and values["30"] == "70%"
    assert "_od_regular" not in (pathlib.Path(__file__).resolve().parents[1] / "content" / "p741.py").read_text(encoding="utf-8")
