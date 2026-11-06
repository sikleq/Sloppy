"""Owner's ninth round of 2026-11-06: terrain rows numbered "1." with their tag on the line, marks by the headers that
name a block New / Reworked / Returning and by the mechanic paragraphs, the marks with their word, neutral AI as MISC,
GENERAL's icon square symmetric."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def test_a_terrain_row_gets_its_tag_back_and_its_number_in_the_text():
    from patch.tag_marks import terrain_rows_tagged
    row = ('<li data-tag="del nerf" class="terrain-row"><span class="badge tnum">2</span>'
           '<span class="row-text">Corner outposts have been removed</span></li>')
    out = terrain_rows_tagged(row)
    assert '<span class="badge del" data-tag="del" data-overall="nerf">DEL</span>' in out
    # no number in the text either (owner 2026-11-06: "отказываемся от нумерации в подобных случаях")
    assert '<span class="row-text">Corner outposts' in out
    assert "badge tnum" not in out and "2." not in out
    # a row with a % keeps BUFF / NERF; a row outside a terrain block is left alone
    pct = '<li data-tag="nerf" class="terrain-row"><span class="badge tnum tnum-nerf">1</span><span class="row-text">X</span></li>'
    assert 'class="badge nerf-text" data-tag="nerf"' in terrain_rows_tagged(pct)
    other = '<li data-tag="rework"><span class="badge tnum">1</span><span class="row-text">X</span></li>'
    assert terrain_rows_tagged(other) == other


def test_a_rows_kinds_come_before_the_filters_aliases():
    from patch.tag_marks import row_kinds
    assert row_kinds("buff new") == ["new"]
    assert row_kinds("del nerf") == ["del"]
    assert row_kinds("rework misc qol") == ["rework", "misc", "qol"]
    assert row_kinds("nerf") == ["nerf"]
    assert row_kinds("") == []


def test_nothing_stands_on_the_panels_line_any_more():
    # owner 2026-11-06, 7.38 Heaven's Halberd "Item Reworked": "тут забыл реворки убрать. в целом старые расположения
    # закладок не надо оставлять было" — no bookmarks of headers, paragraphs or cards; the script is gone
    from patch import tag_marks
    from patch.css_bundle import read_css
    from patch.js_bundle import JS_PARTS, read_js
    css, js = read_css(), read_js()
    assert "tag-marks" not in JS_PARTS and not (ROOT / "src" / "js" / "tag-marks.js").exists()
    assert "tm-block" not in css + js and "tm-said" not in css and "@media (min-width: 1180px)" not in (
        css.split("Tags as small tiles", 1)[1].split("generated icons: begin", 1)[0])
    assert not hasattr(tag_marks, "said_by_header") and not hasattr(tag_marks, "header_tag")
    # a row's 18px tile: its middle on the middle of the row's first line, as the old 20px tag at 3px
    assert re.search(r"\.tag-marks ul\.changes > li > \.badge\[data-tag\] \{ left: 0; top: 4px; z-index: 2; \}", css)


def test_a_stats_cards_tags_are_tiles_too():
    # owner 2026-11-06, 7.38 Heaven's Halberd: "ты забыл внутри карточек теги поменять на теги-закладки"
    from patch.css_bundle import read_css
    css = read_css()
    assert ("  .tag-marks ul.changes > li > .badge[data-tag], .tag-marks .properties-change .property-tag .badge[data-tag] {\n"
            "    width: 22px; min-width: 0; height: 18px;") in css
    # an item's abilities card (iab-change) keeps its one column
    assert ("  .tag-marks .properties-change:not(.iab-change) .properties-pane { grid-template-columns: 22px 1fr auto; }"
            in css)


def test_the_swap_icon_is_two_arrows_on_a_round_orbit():
    # owner 2026-11-06: "иконку свапа поменяй на стрелочки с более круговой орбитой"
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen_tm", ROOT / "scripts" / "gen" / "gen_tag_marks_css.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    swap = dict((tag, path) for tag, path, _w in gen.ICONS)["swap"]
    assert swap.count("A4.6 4.6 0 0 1") == 2 and "h8.8" not in swap
    from patch.css_bundle import read_css
    assert gen.block() in read_css().replace("\r\n", "\n")


def test_tiles_are_solid_with_a_dark_icon():
    # filled with the tag's colour, a dark icon, no word (owner 2026-11-06, from mock variant 2 to the tiles)
    from patch import page
    from patch.css_bundle import read_css
    css = read_css()
    assert not hasattr(page, "TAG_MARK_LABELS") and "tm-label" not in css
    # a little brighter than the first try (owner 2026-11-06: "чуть-чуть ярче")
    assert "background: color-mix(in srgb, currentColor 94%, #000); }" in css and "background: #15120f;" in css
    assert css.count("viewBox='0 0 14 14'") == 7
    # REWORK is a gear (owner 2026-11-06: "Rework тег иконки сделай шестерёнку"), filled on its own grid
    rework = css.split('.tag-marks .badge[data-tag~="rework"] {', 1)[1].split("\n", 1)[0]
    assert "viewBox='0 0 256 256' fill='black'" in rework and "M237.94,107.21" in rework
    src = (ROOT / "patch" / "page.py").read_text(encoding="utf-8")
    assert "terrain_rows_tagged(out)" in src


def test_neutral_ai_rows_are_misc():
    from patchgen.tags import _guess_tag
    assert _guess_tag("Neutrals will cast this ability on the closest enemy if there are three or more enemies") == "MISC"
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert not re.search(r'li\("Neutrals will [^"]*", t\("(?:NEW|NERF)"\)', p738)
    assert 'W(li("Now has +25% base Slow Resistance", t("NEW")))' in p738


def test_generals_icon_square_is_symmetric():
    from patch.css_bundle import read_css
    css = read_css()
    # two side by side the full height (the block's 2-row grid had won over it), three: two over one in the middle
    assert ".ability-block.other-block > .ability-icon-wrap > .stat-mosaic.n2 { grid-template-rows: 1fr; }" in css
    assert ".stat-mosaic.n3 > .sm-cell:last-child { grid-column: span 2; }" in css
    # never more than four: no grids of five or six (owner 2026-11-06)
    assert ".stat-mosaic.n5" not in css and ".stat-more" not in css


def test_a_recipe_side_stays_on_one_line():
    # owner 2026-11-06, 7.38 Battle Fury: "часть с рецептом в новой карточке уехала на другую строчку"
    from patch.css_bundle import read_css
    css = read_css()
    assert "  .components-change .components-row { flex-wrap: nowrap; min-width: 0; }" in css
    assert "  .components-change .component img { max-width: 100%; height: auto; aspect-ratio: 4 / 3; }" in css


def test_a_tag_shows_no_word_on_hover():
    # owner 2026-11-06: "убери нововведение, когда наводишь на закладку - выдвигается текст"
    from patch.css_bundle import read_css
    from patch.js_bundle import read_js
    css, js = read_css(), read_js()
    tm = css.split("Tags as small tiles", 1)[1].split("generated icons: begin", 1)[0]
    assert "--tm-wide" not in tm + js and "openWidth" not in js and "text-fill-color" not in tm
    assert ".badge[data-tag]:hover" not in tm and ".tm-block.tm-placed:not(.tm-dup):hover" not in tm
    # the filters' tags a little brighter (owner 2026-11-06: "и сами фильтры-теги")
    assert "  filter: brightness(1.15);" in css.split(".legend-tags .badge.filter-btn {", 1)[1].split("}", 1)[0]


def test_a_new_blocks_row_of_another_tag_has_its_tab_and_bullets_share_the_edge():
    # owner 2026-11-06, 7.38 Ancient Croaker: "Neutrals will cast … стоят не там, где все остальные с ромбиками.
    # Смещены ближе к центру"
    from patch.css_bundle import read_css
    css = read_css()
    assert ('.tag-marks .entity-block.is-new ul.changes > li:not([data-tag~="new"]) > .badge[data-tag] { display: flex; }'
            in css)                                                   # a new block's NEW rows keep their bullet
    assert "display: inline-block; width: 22px; margin: 0 8px 0 -30px; text-align: center; }" in css
