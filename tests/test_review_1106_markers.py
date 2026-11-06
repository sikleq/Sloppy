"""Owner's 2026-11-06 follow-ups to the bookmarks: a row's tag as a small tile where its tag stood (mock variant 1, it
replaced the diamonds of variant 3), an example in a text as its icon alone, abilities each doing something as a table (7.38 Lifesteal Amp)."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_a_rows_tag_is_a_small_tile_where_its_tag_stood():
    # owner 2026-11-06, mock "Вариант 1 Плитка 22x18": "закладки в строке вместо ромбика … такое же расположение, как
    # раньше теги стояли, только более компактно" — the diamonds and the rows' bookmarks on the line are gone
    from patch.css_bundle import read_css
    from patch.js_bundle import read_js
    from patch import tag_marks
    css, js = read_css(), read_js()
    assert '"◆"' not in css and "--tm-gap" not in css + js and "placeTagMark" not in js
    assert "  .tag-marks ul.changes > li > .badge[data-tag] { left: 0; top: 4px; z-index: 2; }" in css
    assert "    width: 22px; min-width: 0; height: 18px; padding: 0; display: flex;" in css
    assert "> .badge[data-tag] + .row-text {\n    padding-left: 30px; }" in css
    assert "display: inline-block; width: 22px; margin: 0 8px 0 -30px; text-align: center; }" in css   # a bullet row
    assert "@media (min-width: 761px) {" in css.split("generated icons: begin")[0].split("Tags as small tiles")[1]
    assert not hasattr(tag_marks, "lead_icon_rows") and "li-lead-icon" not in css     # it only kept a diamond off


def test_a_card_has_no_tag_of_its_own_as_before():
    # owner 2026-11-06, 7.41f Silver Edge / Greedy: "не ставь их тут, будут такие же положения, как раньше стояли теги"
    from patch.js_bundle import read_js
    js = read_js()
    for gone in ("function blockMarks()", "SHOWN_BY", "SELF_TOLD", "function anchorOf(", "function innerKinds(",
                 "function rowAbove(", "function headerMarks()", "function paragraphMarks()"):
        assert gone not in js, gone


def test_an_example_in_a_text_is_its_icon_with_the_name_on_hover():
    # owner 2026-11-06: "Lifestealer's Feast... убираем название и оставляем иконку которая подписана при наведении"
    from patch.mech_abilities import mech_example
    html = mech_example("Lifestealer's Feast")
    assert 'class="ability-chip chip-word" data-tooltip="Lifestealer&#x27;s Feast"' in html
    assert "ac-sub-name" not in html and "life_stealer_feast" in html


def test_abilities_each_doing_something_make_a_table():
    # 7.38 Lifesteal Amp as the table above it (owner 2026-11-06): the list rule of abilities gives each its icon
    from patch.mech_abilities import ability_list_rows
    raw = "<br>".join(["Lifestealer's Open Wounds heals attackers for a percentage of the damage done",
                       "Meepo's Ransack heals all Meepos a flat amount for each strike",
                       '<span class="pop-note">Holding Alt will describe it</span>'])
    rows, notes = ability_list_rows(raw, least=1)
    assert "life_stealer_open_wounds" in rows and "meepo_ransack" in rows
    assert "Heals all Meepos a flat amount for each strike" in rows and notes == ["Holding Alt will describe it"]
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert ("can benefit from Lifesteal Amp\", t(\"REWORK\"), extra=inline_list(\"Lifestealer's Open Wounds" in p738)
