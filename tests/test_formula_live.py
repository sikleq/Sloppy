"""Live game formula (owner 2026-11-18, pilot 7.42 "Hero kill bounty rescaled"): the generator turns an
"OLD: <formula><br>NEW: <formula>" row into formula_change(inputs=, chart=), the element gives a field for every
variable, both results and a chart of both curves. Kept apart from test_generator.py so branches merge cleanly."""
import re
from pathlib import Path

import tools.generate_patch_code_v2 as g
from patch.formula_rows import formula_change

ROOT = Path(__file__).resolve().parent.parent
BOUNTY_ROW = ('W(li("Hero kill bounty rescaled", t("REWORK"), extra=inline_note('
              '"OLD: 125 + (8 * VictimLevel) + KillstreakFactor<br>NEW: 100 + (10 * VictimLevel) + KillstreakFactor")))')
BOUNTY_BLOCK = ('W(formula_change("Hero kill bounty", "125 + (8 * VictimLevel) + KillstreakFactor", '
                '"100 + (10 * VictimLevel) + KillstreakFactor", tag="REWORK", '
                'inputs={"VictimLevel": 15, "KillstreakFactor": 0}, '
                'chart=("VictimLevel", "Victim Level", 1, 30), unit="Gold"))')


def test_old_new_formula_row_becomes_a_live_formula_block():
    lines = ['W(subgroup("Gold and Experience"))', 'W(ul_open())', BOUNTY_ROW,
             'W(li("Roshan gold per player decreased from 135 to 125", b(135, 125)))', 'W(ul_close())']
    out = g._postprocess_formula_rows(lines)
    assert out == ['W(subgroup("Gold and Experience"))', BOUNTY_BLOCK, 'W(ul_open())', lines[3], 'W(ul_close())']


def test_formula_tag_follows_the_curves():
    up = BOUNTY_ROW.replace("NEW: 100 +", "NEW: 130 +")        # more gold at every level
    assert 'tag="BUFF"' in g.formula_block(up)
    down = BOUNTY_ROW.replace("(10 * VictimLevel)", "(8 * VictimLevel)")   # 25 less at every level
    assert 'tag="NERF"' in g.formula_block(down)
    assert 'tag="REWORK"' in g.formula_block(BOUNTY_ROW)      # the curves cross at level 12.5


def test_rows_that_are_not_a_computable_formula_stay_notes():
    siege = ('W(li("Reworked Siege creep spawn count", t("REWORK"), extra=inline_note('
             '"OLD: Every 5 minutes, 1 siege creep<br>NEW: Every 2.5 minutes, 1 siege creep")))')
    unknown = BOUNTY_ROW.replace("KillstreakFactor", "MysteryThing")     # no default we could stand behind
    for line in (siege, unknown, 'W(li("Roshan gold per player decreased from 135 to 125", b(135, 125)))'):
        assert g._postprocess_formula_rows([line]) == [line]


def test_live_formula_has_a_field_per_variable_results_and_chart():
    html = formula_change("Hero kill bounty", "125 + (8 * VictimLevel) + KillstreakFactor",
                          "100 + (10 * VictimLevel) + KillstreakFactor",
                          inputs={"VictimLevel": 15, "KillstreakFactor": 0},
                          chart=("VictimLevel", "Victim Level", 1, 30), unit="Gold")
    assert re.findall(r'data-var="(\w+)"', html) == ["VictimLevel", "KillstreakFactor"]
    assert '<span class="fx-val fx-val-old">245</span>' in html
    assert '<span class="fx-val fx-val-new">250</span>' in html
    assert html.count('<polyline class="fx-line') == 2 and 'fx-ruler' in html
    assert 'data-fx-chart="VictimLevel" data-fx-lo="1" data-fx-hi="30"' in html


def test_gap_between_curves_splits_where_they_cross():
    # 7.42 bounty: less gold below level 12.5 (red), more above (green)
    from patch.formula_rows import _fx_gap_pieces
    xs = list(range(1, 31))
    pieces = _fx_gap_pieces(xs, [125 + 8 * x for x in xs], [100 + 10 * x for x in xs])
    assert [s for s, _ in pieces] == [-1, 1]
    assert pieces[0][1][-1] == pieces[1][1][0] and abs(pieces[0][1][-1][0] - 12.5) < 1e-9
    html = formula_change("Hero kill bounty", "125 + (8 * VictimLevel)", "100 + (10 * VictimLevel)",
                          inputs={"VictimLevel": 15}, chart=("VictimLevel", "Victim Level", 1, 30), unit="Gold")
    assert html.index('fx-gap fx-loss') < html.index('fx-gap fx-gain') < html.index('fx-line-old')
    assert '>250</text>' in html and '>245</text>' in html and 'fx-axis-y' in html


def test_the_740_table_form_is_unchanged():
    html = formula_change("Assist Gold Formula", "60 + ( ( VictimNetworth * 0.037 ) / NumHeroes )",
                          "15 + ( ( 50 + ( VictimNetworth * 0.037 ) ) / NumHeroes )",
                          vary=("NumHeroes", "Heroes", [1, 2, 3, 4, 5]), fixed={"VictimNetworth": 10000}, unit="Gold")
    assert 'formula-live' not in html and 'class="formula-ex"' in html and 'data-fx-invar="VictimNetworth"' in html


def test_chart_geometry_is_the_same_in_python_and_js():
    from patch import formula_rows as fr
    js = (ROOT / "src" / "js" / "formula-calculator.js").read_text(encoding="utf-8")
    want = f"const W = {fr.FX_W}, H = {fr.FX_H}, PL = {fr.FX_PAD_L}, PR = {fr.FX_PAD_R}, PT = {fr.FX_PAD_T}, PB = {fr.FX_PAD_B};"
    assert want in js


ASSIST_BLOCK = ('W(formula_change("Assist Gold Formula", "60 + ( ( VictimNetworth * 0.037 ) / NumHeroes )", '
                '"15 + ( ( 50 + ( VictimNetworth * 0.037 ) ) / NumHeroes )", tag="REWORK", '
                'inputs={"VictimNetworth": 10000, "NumHeroes": 1}, chart=("NumHeroes", "Heroes", 1, 5), unit="Gold"))')


def test_name_row_then_old_and_new_rows_become_one_block():
    # 7.40: Valve writes the name, then "OLD: …" and "NEW: …" as rows of their own
    lines = ['W(ul_open())', 'W(li("Assist Gold Formula Reworked", t("REWORK")))',
             'W(li("OLD: 60 + ( ( VictimNetworth * 0.037 ) / NumHeroes )", t("MISC")))',
             'W(li("NEW: 15 + ( ( 50 + ( VictimNetworth * 0.037 ) ) / NumHeroes )", t("MISC")))', 'W(ul_close())']
    assert g._postprocess_formula_rows(lines) == [ASSIST_BLOCK]
    # 430 -> 435 gold for one hero, 134 -> 99 for five: the curves cross -> REWORK
    assert 'tag="REWORK"' in ASSIST_BLOCK


def test_old_row_without_its_new_row_stays():
    lines = ['W(li("Assist Gold Formula Reworked", t("REWORK")))',
             'W(li("OLD: 60 + ( ( VictimNetworth * 0.037 ) / NumHeroes )", t("MISC")))',
             'W(li("Roshan gold per player decreased from 135 to 125", b(135, 125)))']
    assert g._postprocess_formula_rows(lines) == lines


def test_740_assist_gold_is_the_live_block():
    src = (ROOT / "content" / "p740.py").read_text(encoding="utf-8")
    assert ASSIST_BLOCK in src and "vary=" not in src.split("Assist Gold Formula", 1)[1][:400]


def test_742_bounty_is_the_live_block():
    src = (ROOT / "content" / "p742.py").read_text(encoding="utf-8")
    assert BOUNTY_BLOCK in src and "OLD: 125 + (8 * VictimLevel)" not in src
