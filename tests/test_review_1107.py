"""Owner's review of 2026-11-07: a card side folds by its height, the arrow points at the shorter side, tag tiles on every
patch page."""
from pathlib import Path

from patch.cards_rows import FOLD_CHARS, TABLE_ROW_CHARS, _side_weight, fold_long_rows

ROOT = Path(__file__).resolve().parent.parent


def _row(text):
    return f'<div class="ability-change-row">{text}</div>'


def test_values_that_become_a_table_weigh_by_their_rows():
    # 7.38 Arcane Curse: 379 characters of text and a six-row table stood open ("карточка достаточно высокая")
    values = _row("Initial Damage: 20/40/60/80. Damage: 16/24/32/40. Base Duration: 6s. Movement Slow: 16/19/22/25%. "
                  "Penalty Duration: 2s. Silenced Multiplier: 1.5x")
    assert _side_weight(values) == 6 * TABLE_ROW_CHARS


def test_a_side_with_short_text_and_a_tall_table_folds():
    text = _row("x " * 190)
    values = _row("Initial Damage: 20/40/60/80. Damage: 16/24/32/40. Base Duration: 6s. Movement Slow: 16/19/22/25%. "
                  "Penalty Duration: 2s. Silenced Multiplier: 1.5x")
    assert sum(len(r) for r in (text, values)) < FOLD_CHARS + 200     # by characters alone it stayed open
    out = fold_long_rows([text, values])
    assert out[0] == text and 'class="acr-fold' in out[1]


def test_a_plain_text_row_weighs_its_characters():
    assert _side_weight(_row("Grants +1 Leap charge.")) == len("Grants +1 Leap charge.")


def test_the_arrow_stands_at_the_shorter_side_of_top_aligned_cards():
    # 7.38 Mirana Leap: "стрелочка в пустоту указывает, а не блок новой карточки из-за разницы в размерах"
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert "document.querySelectorAll('.ability-change.unified-panes').forEach((card) => {" in js
    assert "const p = o.height <= n.height ? o : n;" in js


def test_a_talent_that_only_moved_says_where_once():
    # 7.38 Pangolier: the "?" told each talent twice ("не читаемы, это много текста сплошняком")
    import pytest
    page = ROOT / "dist" / "patches" / "7.38.html"
    if not page.exists():
        pytest.skip("the site is not built")
    html = page.read_text(encoding="utf-8")
    assert ('<span class="tm-n">+15% Attack Damage as Swashbuckle Damage</span><span class="tm-c">20 → '
            '<span class="iab-hl iab-hl-buff iab-hl-num">15</span></span>' in html)
    assert "where it was +15% Attack Damage as Swashbuckle Damage" not in html


def test_a_moved_talent_with_new_numbers_names_only_the_numbers():
    # 7.38 Legion Commander: "…: moved from Level 10, where it was +1.5% Max HP Regen while inside The Calling"
    from patch.talent_marks import _changed_part
    assert _changed_part("+1.5% Max HP Regen while inside The Calling", "+3% Max HP Regen while inside The Calling") == "+1.5%"
    assert _changed_part("+30% Spirit Form Bright Speed Bonus", "+10% Spirit Form Movement Speed Bonus") == \
        "+30% Spirit Form Bright Speed Bonus"
    # the hand-written ones are rows of the same table: (talent, level, value)
    from patch.talent_marks import _KNOWN
    assert all(len(row) == 3 for _, row in _KNOWN.values())


def test_a_moved_talent_is_a_table_row_of_level_and_value_before_and_after():
    # owner 2026-11-07 (7.38 Tiny, Phantom Assassin): "на сколько талант улучшился/ухудшился и куда переехал"; a line
    # "всё равно визуально не читаемо, слишком подряд цифры идут" — a small table: talent, level, value apart
    from patch.talent_marks import change_cells, moves_table
    buff = '<span class="iab-hl iab-hl-buff">'
    nerf = '<span class="iab-hl iab-hl-nerf">'
    assert change_cells("+20% Stifling Dagger Damage", "+15% Stifling Dagger Damage", 20, 15) == \
        ("Stifling Dagger Damage", f"20 → {buff}15</span>", f'+20% → {nerf}+15%</span> <span class="tm-pct">−25%</span>')
    assert change_cells("+110 Rolling Boulder Damage", "+160 Rolling Boulder Damage", 15, 20)[1:] == \
        (f"15 → {nerf}20</span>", f'+110 → {buff}+160</span> <span class="tm-pct">+45%</span>')
    # unchanged numbers stay in the name; the same level is the other side
    assert change_cells("+4 Armor", "+4 Armor", 10, 10) == ("+4 Armor", "10, other side", '<span class="tm-same">same</span>')
    # another bonus: neither better nor worse
    assert 'iab-hl-rework">+30% Bright Speed Bonus' in change_cells("+10% Movement Speed Bonus",
                                                                     "+30% Bright Speed Bonus", 20, 15,
                                                                     label="Spirit Form")[2]
    table = moves_table([("A", "1", "2"), ("B", "3", "4")])
    assert table.startswith('<span class="tal-moves"><span class="tm-h">Talent</span>') and table.count('class="tm-n"') == 2
    from patch.css_bundle import read_css
    assert ".tal-moves { display: grid;" in read_css()


def test_an_item_card_that_hides_no_row_is_not_drawn():
    # owner 2026-11-07, 7.38 Bloodthorn: "излишне тут карточки, т.к предмет особо не менялся"
    from patch.page import drop_cards_hiding_nothing
    block = '<div class="entity-block item-block">'
    shown = '<li data-tag="nerf"><span class="row-text">x</span></li>'
    hidden = '<li data-tag="nerf" class="iab-covered covered-iab"><span class="row-text">y</span></li>'
    page = (f'{block}<!--IABCARD:a--><ul class="changes">{shown}</ul></div>'
            f'{block}<!--IABCARD:b--><ul class="changes">{shown}{hidden}</ul></div>')
    out = drop_cards_hiding_nothing(page)
    assert "<!--IABCARD:a-->" not in out and "<!--IABCARD:b-->" in out


def test_a_qol_row_of_an_item_stays_shown_under_its_card():
    # 7.38 Bloodthorn: "Soul Rend silence visual … tinted red" was hidden as if the card said it ("забыл строку")
    import pytest
    page = ROOT / "dist" / "patches" / "7.38.html"
    if not page.exists():
        pytest.skip("the site is not built")
    html = page.read_text(encoding="utf-8")
    row = html[:html.index("Soul Rend silence visual above affected targets")]
    assert "iab-covered" not in row[row.rindex("<li"):]
    block = html[html.index('id="dyn-item-bloodthorn"'):]
    assert "iab-change" not in block[:block.index('<div class="entity-block')]


def test_a_search_result_of_an_ability_names_its_owner():
    # owner 2026-11-07: seven "Riverborn Aura" results, "непонятно, какая к чему"
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert "e.owner = clone.textContent" in js
    # beside the name in brackets, and "Dragon Knight's" is not said twice (second review 2026-11-07)
    assert '<span class="result-owner">(${escapeHtml(m.owner)})</span>' in js
    assert "if (e.name.startsWith(own)) e.name = e.name.slice(own.length);" in js
    css = (ROOT / "src" / "css" / "patch-toolbar.css").read_text(encoding="utf-8")
    assert ".search-results .result-item .result-owner { font-size: 11.5px;" in css
    assert "result-owner { display: block" not in css


def test_many_values_of_a_one_sided_card_stand_beside_it():
    # owner 2026-11-07, 7.38 Throw, variant A: "отдельным соседним блоком-таблицей"
    from patch.value_tables import SIDE_TABLE_ROWS, tables_beside_single_cards
    cells = "".join(f'<div class="vt-l">a{i}</div><div class="vt-v">{i}</div>' for i in range(SIDE_TABLE_ROWS))
    card = ('<div class="ability-change unified-panes is-single-new"><div class="ability-change-pane"><div class="ability-change-row">'
            f'Text <div class="value-table">{cells}</div></div></div></div>')
    out = tables_beside_single_cards(card)
    assert out.endswith(f'<div class="vt-side"><div class="value-table">{cells}</div></div></div>')
    assert "is-single-new has-vt-side" in out
    # the text that folded for the table's weight opens again
    folded = ('<div class="ability-change unified-panes is-single-new"><div class="ability-change-pane">'
              '<div class="acr-fold"><div class="acr-fold-body"><div class="ability-change-row">'
              f'Text <div class="value-table">{cells}</div></div></div>'
              '<button class="acr-fold-toggle"></button></div></div></div>')
    out = tables_beside_single_cards(folded)
    assert "acr-fold" not in out and '<div class="ability-change-row">Text </div></div><div class="vt-side">' in out
    assert out.count("value-table") == 1
    few = card.replace('<div class="vt-l">a0</div><div class="vt-v">0</div>', "")
    assert tables_beside_single_cards(few) == few
    css = (ROOT / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    assert ".ability-change.unified-panes.is-single-new > .vt-side { grid-column: 3; grid-row: 1; }" in css


def test_a_story_opens_its_list_before_a_new_row():
    # owner 2026-11-07, 7.38 Roshan: "Now has +25% base Slow Resistance" stood above the REWORK story, "должна быть там,
    # где и другие"
    from patch.page import _sort_changes_li
    new = '<li data-tag="buff new"><span class="badge new" data-tag="new">NEW</span><span class="row-text">n</span></li>'
    story = ('<li class="mech-desc li-notag mech-story" data-tag="rework"><span class="row-tag-empty"></span>'
             '<span class="row-text">s</span></li>')
    nerf = '<li data-tag="nerf"><span class="badge nerf-text" data-tag="nerf">NERF</span><span class="row-text">k</span></li>'
    out = _sort_changes_li(f'<ul class="changes">{story}{new}{nerf}</ul>')
    assert out.index("mech-story") < out.index(">NEW<") < out.index(">NERF<")


def test_the_patch_info_is_a_folded_card_above_the_filters():
    # owner 2026-11-07, mock "Вариант 1": "Official notes и другую инфу сделать в таком же блоке, только выше панели
    # фильтров … кнопку … в центр верхней кромки панели тегов-фильтров"
    from patch.page import filter_pop_html, patch_info_html
    html = patch_info_html("7.38", "19.02.2025")
    assert html.startswith('<div class="pinfo-card" id="pinfo-card"><a class="pi-official" '
                           'href="https://www.dota2.com/patches/7.38"')
    assert '<span>Released</span><span class="pi-val"><b>19.02.2025</b></span>' in html
    assert '<span>Ran</span><span class="pi-val"><b>14</b> days</span>' in html
    from patch.elements import section
    from patch.state import _State
    _State.patch_info, _State.section_panel_open = html, False
    first = section("General Updates")
    assert '<h2 class="section" data-section="general">General Updates</h2>' in first and "pinfo" not in first
    pop = filter_pop_html()
    assert pop.startswith('<div class="filter-pop" id="filter-pop">' + html + '<button type="button" class="pinfo-tab" '
                          'aria-expanded="true" aria-controls="pinfo-card"')
    assert _State.patch_info == "" and "pinfo" not in filter_pop_html()
    _State.section_panel_open = False
    _State.current_sections.clear()
    css = (ROOT / "src" / "css" / "patch-toolbar.css").read_text(encoding="utf-8")
    assert ".pinfo-card { position: absolute; left: 0; right: 0; bottom: calc(100% + 22px);" in css
    assert ".pinfo-tab { position: absolute; left: 50%; top: -14px; transform: translateX(-50%);" in css
    js = (ROOT / "src" / "js" / "filter-fab.js").read_text(encoding="utf-8")
    assert "info.hidden = !info.hidden;" in js


def test_the_filters_open_from_a_button_of_the_corner_stack():
    # owner 2026-11-07: variant 3, no word "Filters", tag tiles, opened by a round button like the others
    from patch.page import filter_pop_html
    html = filter_pop_html()
    # a card at the right edge, out from the start ("включены по умолчанию … по правому краю"), its switch a round
    # button of the corner stack ("иконку фильтров всё же вынеси сюда и адаптируй")
    assert html.startswith('<div class="filter-pop" id="filter-pop">') and '<div class="filter-rail">' in html
    from patch.page import FILTER_FAB
    assert FILTER_FAB.startswith('<button class="filter-fab" id="filter-fab" type="button" aria-expanded="true"')
    page_src = (ROOT / "patch" / "page.py").read_text(encoding="utf-8")
    assert "'</button>' + FILTER_FAB +" in page_src and "FILTER_TOGGLE" not in page_src
    assert html.count('<span class="fp-word">') == 8 and "Filters" not in html
    # look 6 of the mock, "галочки в рамке": a framed card, a box before each word, filled when ticked
    assert "fp-tile" not in html
    css = (ROOT / "src" / "css" / "pixel-skin.css").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert ".filter-rail .cat-filter-btn.active::before { background: currentColor;" in css
    # a ticked tag shows its own icon in the filled box, as its tile in a row (2026-11-07: "вместо галочек … иконку тега")
    assert ".filter-rail .legend-tags .badge.filter-btn.active::after {" in css
    assert "mask: var(--tm) center / contain no-repeat; }" in css.split(".filter-btn.active::after {", 1)[1]
    # the middle of the screen's height ("центрировано на странице"), the button above the search, in its look
    assert "position: fixed; right: 10px; top: 50%; transform: translateY(-50%); z-index: 95; width: 168px;" in css
    assert "background: url('icons/ui/gothic/icon_filter.png') center / 22px 22px no-repeat," in css
    # the corner buttons in one framed panel, always bottom right (mock "Вариант A")
    assert ".corner-dock {\n  position: fixed; right: 10px; bottom: 14px;" in css
    assert ".corner-dock > button {\n  position: static; display: block; width: 34px; height: 34px;" in css
    page_src = (ROOT / "patch" / "page.py").read_text(encoding="utf-8")
    dock = page_src[page_src.index("W('<div class=\"corner-dock\">'"):]
    # "top" shows no colour until the script knows where the page is: neither a gold flash at the top ("при ctrl+f5
    # кнопка «наверх» на секунду золотая") nor a grey one lower down ("на секунду серая, потом уже золотая")
    order = [dock.index(k) for k in ('class="back-to-top at-top btt-wait"', "FILTER_FAB", 'class="search-fab"',
                                     'class="dyn-w-fab"')]
    assert order == sorted(order)
    js = (ROOT / "src" / "js" / "filter-fab.js").read_text(encoding="utf-8")
    assert "getElementById('filter-fab')" in js and "if (covers()) close();" in js


def test_the_filter_icon_is_a_funnel_on_the_eyes_grid():
    # owner 2026-11-07: "иконку фильтров сделай заметно лучше и pixelated" — the eye's 24 grid, outline and palette
    import pytest
    pytest.importorskip("PIL")      # not in CI
    from tools.pixel_icons.filter_icon import PALETTE, grid_rows
    rows = grid_rows()
    used = set("".join(rows)) - {"."}
    # sliders, not a funnel (2026-11-07: "поменяй в целом модельку, не вот эту трубу"): outline, light, gold, shade
    assert used <= set(PALETTE) and {"k", "a", "b", "m"} <= used
    from tools.pixel_icons.filter_icon import SLIDERS
    assert len(SLIDERS) == 3
    from PIL import Image
    im = Image.open(ROOT / "icons" / "ui" / "gothic" / "icon_filter.png")
    assert im.size == (48, 48)
