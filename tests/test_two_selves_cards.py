"""Guards the cards of heroes with two selves (Arc Warden and his Tempest Double): columns, rows above the cards.
"""

import importlib
import pathlib
import pytest
import re
import sys
from patch import elements
from patch.state import _State, reset_page_state

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
post_cards = importlib.import_module("patchgen.post_cards")


@pytest.fixture
def page():
    reset_page_state()
    _State.current_patch_version = "7.38"
    yield
    reset_page_state()


def test_the_two_selves_columns_are_the_games_labels():
    from tools.patchgen.post_cards import _selves_columns
    kv = ("Summons a Spark Wraith.\nActivation delay: 2. Damage: 100/180/260/340. Wraith speed: 400. Slow duration: "
          "0.6/0.8/1/1.2. Activation delay: 1. Damage: 75/140/205/270. Wraith speed: 725. Slow duration: 0.4/0.5/0.6/0.7.")
    cols = _selves_columns("Spark Wraith", kv,
                           "Spark activates in 2 seconds, flies at a speed of 400, slows enemy for 0.6/0.8/1/1.2s, deals 100/180/260/340 damage",
                           "Spark activates in 1 second, flies at a speed of 725, slows enemy for 0.4/0.5/0.6/0.7s and deals 75/140/205/270 damage",
                           "Spark activates in 1.5 seconds, flies at a speed of 550, slows enemy for 0.5/0.6/0.7/0.8s and deals 100/170/240/310 damage")
    assert cols[0] == ("Activation delay", "Speed", "Slow duration", "Damage")
    assert cols[1] == ("2s", "400", "0.6/0.8/1/1.2s", "100/180/260/340") and cols[3][0] == "1.5s"
    # the double's numbers are other values of the game (7.38 Magnetic Field): no shared columns
    mf = "Field.\nAttack speed bonus: 30/60/90/120. Evasion bonus: 100%. Bonus attack range: 150. Bonus attack damage: 20/40/60/80."
    assert _selves_columns("Magnetic Field", mf, "100% evasion, 30/60/90/120 bonus attack speed",
                           "150 bonus attack range, 20/40/60/80 base attack damage", "100% evasion, 30/60/90/120 bonus attack speed") is None


def test_two_selves_card_shows_each_self_before_and_their_one_line_after(page):
    from patch.api import two_selves_change
    elements.hero_header("Arc Warden")
    html = two_selves_change("Flux", "arc_warden_flux", old_desc="Old text.", hero="15 damage", double="20 damage",
                             new_desc="New text.", both="15 damage, 14% slow")
    assert "Now has the same effect for both Arc Warden and Tempest Double" in html and 'data-tag="rework"' in html
    assert html.count('aria-label="Arc Warden"') == 2 and html.count('aria-label="Tempest Double"') == 2
    assert "Disorder facet" in html
    plain = re.sub(r"<[^>]+>", "", html)
    assert plain.index("20 damage") < plain.index("New text.") < plain.index("15 damage, 14% slow")


def test_arc_wardens_three_abilities_are_cards_on_the_page():
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    for name in ("Flux", "Magnetic Field", "Spark Wraith"):
        assert f'W(two_selves_change("{name}", ' in text and f'W(ability("{name}", slug="arc_warden_' not in text
    assert "Now has the same effect for both" not in text


def test_the_rows_come_before_the_caption_and_the_card(page):
    from patch.api import ability_change, li, t
    elements.hero_header("Arc Warden")
    html = ability_change(old=dict(name="Flux", slug="arc_warden_flux", desc=["Old."]),
                          new=dict(name="Flux", slug="arc_warden_flux", desc=["New."]),
                          summary="Ability reworked", tag="rework",
                          rows_first=lambda: [li("First row", t("DEL")), li("Second row", t("NEW"))])
    assert html.index("First row") < html.index("Second row") < html.index("Ability reworked") < html.index('class="ability-change')
    assert "ROWSFIRST" not in html
    plain = ability_change(old=dict(name="Flux", slug="arc_warden_flux", desc=["Old."]),
                           new=dict(name="Flux", slug="arc_warden_flux", desc=["New."]), summary="Ability reworked", tag="rework")
    assert "ROWSFIRST" not in plain


def test_arc_wardens_rows_stand_above_their_cards():
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    block = text[text.index('W(hero_header("Arc Warden"))'):text.index('W(hero_header("Axe"))')]
    field = block[block.index('two_selves_change("Magnetic Field"'):block.index('two_selves_change("Spark Wraith"')]
    assert field.index("rows_first=lambda") < field.index("No longer upgraded with Aghanim's Shard") < field.index("Now is a Point Targeted")
    assert "W(li(" not in field
    double = block[block.index('game_ability_pair("arc_warden_tempest_double"'):block.index('W(subgroup("Talents"))')]
    assert "rows_first=lambda" in double and "W(li(" not in double


def test_without_the_games_text_the_row_stays(monkeypatch):
    from patch import aghs_text
    monkeypatch.setattr(aghs_text, "ability_text", lambda slug, version, kind="base": None)
    row = ('W(li("Now has the same effect for both Arc Warden and Tempest Double", t("REWORK"), extra=inline_note("Deals 15 '
           '<span class=\\"pop-note\\">(Previous values: Arc Warden: Deals 10. Tempest Double: Deals 20)</span>")))')
    lines = ['W(ability("Flux", slug="arc_warden_flux"))', 'W(ul_open())', row, 'W(ul_close())']
    assert post_cards._postprocess_two_selves_cards(lines, "7.38") == lines


def test_tempest_double_is_a_card_from_the_games_files(page):
    from patch.api import game_ability_pair
    old, new = game_ability_pair("arc_warden_tempest_double", "7.38")
    old_text, new_text = re.sub(r"<[^>]+>", "", " ".join(old)), re.sub(r"<[^>]+>", "", " ".join(new))
    assert "cooldown is restarted" in old_text and "cooldown is restarted" not in new_text
    assert "fractures over time" in new_text and "35%" in new_text and "too far away" in old_text
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert 'game_ability_pair("arc_warden_tempest_double", "7.38")' in text
    assert 'W(ability("Tempest Double", slug="arc_warden_tempest_double"))' not in text


def test_the_line_to_a_second_card_starts_under_the_first():
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    part = js[js.index("svg.under-rows-connector"):js.index("Two sides standing from one top edge")]
    assert "before.classList.contains('ability-change')" in part and "connectorPath(blockRect, start, paneRect)" in part


def test_a_self_table_keeps_the_same_columns_for_both_selves(page):
    from patch.api import two_selves_change
    elements.hero_header("Arc Warden")
    html = two_selves_change("Spark Wraith", "arc_warden_spark_wraith", old_desc="Old.", new_desc="New.",
                             columns=("Damage", "Speed"), hero=("100", "400"), double=("75", "725"), both=("90", "550"))
    assert html.count('class="selves-table"') == 2 and "--cols:2" in html
    assert html.count('class="selves-head"') == 4
    plain = re.sub(r"<[^>]+>", " ", html)
    assert plain.index("725") < plain.index("New.") < plain.index("550")


def test_a_dotted_number_stays_on_its_icons_centre():
    # 2026-11-06: measured by ink, the icon goes up 1px instead (Radiance's digits sit above their line's middle); the
    # 11-05 empty line over a dotted number pushed it 1px under the icon's centre once the icon moved
    css = (ROOT / "src" / "css" / "pixel-skin-filters.css").read_text(encoding="utf-8")
    assert "border-top: 1px solid transparent; }" not in css.split(".iab-hint {", 1)[1].split("/* ---- Silent", 1)[0]
    assert "display: block; position: relative; top: -1px; }" in css


def test_the_note_stands_in_the_doubles_last_cell(page):
    from patch.api import two_selves_change
    elements.hero_header("Arc Warden")
    html = two_selves_change("Spark Wraith", "arc_warden_spark_wraith", old_desc="Old.", new_desc="New.",
                             columns=("Damage", "Speed"), hero=("100", "400"), double=("75", "725"), both=("90", "550"))
    table = html[html.index('class="selves-table"'):html.index("New.")]
    assert table.index("725") < table.index("Disorder facet") < table.rindex("</span></span>")


def test_the_self_table_has_lines_and_centred_cells():
    css = (ROOT / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    rule = css[css.index(".selves-table > span {"):]
    rule = rule[:rule.index("}")]
    assert "justify-content: center" in rule and "border-left: 1px solid var(--line-soft)" in rule
    assert "border-top: 1px solid var(--line-soft)" in rule


def test_the_pass_moves_plain_rows_comments_and_formulas_above_the_card():
    lines = ['W(ability_change(', '    old=dict(name="A"), new=dict(name="A"),', '    summary="Ability reworked", tag="rework",', '))',
             'W(ul_open())', '# from the files', 'W(li("Cooldown decreased", b(5, 4, l=True)))  # a note',
             'W(li_formula("Damage rescaled", "1", "2", f, g))', "W(li(\"Aghanim's Shard: More\", t(\"NEW\")))", 'W(ul_close())']
    out = post_cards._postprocess_rows_first(lines)
    text = "\n".join(out)
    first = text[text.index("rows_first=lambda"):text.index("]))")]
    assert "# from the files" in first and 'li("Cooldown decreased", b(5, 4, l=True)),  # a note' in first
    assert 'li_formula("Damage rescaled", "1", "2", f, g),' in first and "Aghanim" not in first
    assert out[-3:] == ["W(ul_open())", "W(li(\"Aghanim's Shard: More\", t(\"NEW\")))", "W(ul_close())"]


def test_a_list_with_anything_else_stays_as_written():
    lines = ['W(ability_change(old=dict(name="A"), new=dict(name="A"), summary="x", tag="rework"))', 'W(ul_open())',
             '_pill = scale_pill("x")', 'W(li("Row", t("NEW")))', 'W(ul_close())']
    assert post_cards._postprocess_rows_first(lines) == lines
