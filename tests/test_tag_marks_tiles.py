"""Guards how a row's tag is drawn: tiles, marks, diamonds, hover, the tag column.
"""

import pathlib
from patch import elements as el

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_tags_as_tiles_run_on_every_page():
    from patch import page
    from patch.css_bundle import read_css
    assert page.TAG_MARK_PAGES is None
    css = read_css()
    for tag in ("buff", "nerf", "new", "del", "swap", "rework"):
        assert (f'.tag-marks .badge[data-tag~="{tag}"], .filter-btn[data-filter="{tag}"] '
                f'{{ --tm: url("data:image/svg+xml,') in css
    assert css.index('[data-tag~="nerf"]') < css.index('[data-tag~="del"], ')     # "del nerf" shows the cross


def test_tag_marks_run_on_every_patch_page():
    # the trial on 7.41f + 7.38 rolled out to all patches (owner 2026-11-07)
    from patch import page
    assert page.TAG_MARK_PAGES is None


def test_entity_pages_draw_tags_as_tiles_too():
    # owner 2026-11-19, Melee Creep's page: "тут на страницах юнитов старые теги нарисованы, это норм?"
    src = (ROOT / "builders" / "entity_changes.py").read_text(encoding="utf-8")
    assert '"patch-page entity-page tag-marks"' in src


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
    # the ability's own name on hover, not its hero's (2026-11-07: "только название способности")
    assert 'class="ability-chip chip-word" data-tooltip="Feast"' in html
    assert "ac-sub-name" not in html and "life_stealer_feast" in html


def test_a_terrain_row_has_a_gold_diamond_and_no_tag_or_number():
    from patch.tag_marks import terrain_rows_tagged
    row = ('<li data-tag="del nerf" class="terrain-row"><span class="badge tnum">2</span>'
           '<span class="row-text">Corner outposts have been removed</span></li>')
    out = terrain_rows_tagged(row)
    # 2026-11-07: "убери теги"; "буквально такие же [ромбики] … только золотые. Без цифр"
    assert out.startswith('<li data-tag="del nerf" class="terrain-row"><span class="tnum-dia tnum-nerf" role="img" '
                          'aria-label="2 on the map"></span><span class="row-text">Corner outposts')
    assert "badge" not in out
    # the outposts are an object taken off the map: red ("Corner outposts … красим ромбик в красный")
    assert '<span class="tnum-dia tnum-nerf" role="img" aria-label="2 on the map"></span>' in out
    # a row with a % in its colour ("Watcher night vision range decreased … ромбик красный")
    pct = '<li data-tag="nerf" class="terrain-row"><span class="badge tnum tnum-nerf">1</span><span class="row-text">X</span></li>'
    assert '<span class="tnum-dia tnum-nerf" role="img" aria-label="1 on the map"></span>' in terrain_rows_tagged(pct)
    up = '<li data-tag="buff" class="terrain-row"><span class="badge tnum tnum-buff">1</span><span class="row-text">X</span></li>'
    assert 'class="tnum-dia tnum-buff"' in terrain_rows_tagged(up)
    # trees taken away are the map's ground, no object: gold; a removed display, no object either
    trees = ('<li data-tag="del nerf" class="terrain-row"><span class="badge tnum">1</span><span class="row-text">'
             'Several trees have been removed</span></li>')
    assert '<span class="tnum-dia" role="img"' in terrain_rows_tagged(trees)
    watchers = ('<li data-tag="del nerf" class="terrain-row"><span class="badge tnum">1</span><span class="row-text">'
                'The watchers near the small water camps have been removed</span></li>')
    assert 'class="tnum-dia tnum-nerf"' in terrain_rows_tagged(watchers)
    ring = ('<li data-tag="del nerf" class="terrain-row"><span class="badge tnum">1</span><span class="row-text">'
            'Watchers no longer display the green AoE ring</span></li>')
    assert '<span class="tnum-dia" role="img"' in terrain_rows_tagged(ring)
    other = '<li data-tag="rework"><span class="badge tnum">1</span><span class="row-text">X</span></li>'
    assert terrain_rows_tagged(other) == other


def test_a_terrain_diamond_stands_in_the_tag_column():
    from pathlib import Path
    css = Path(__file__).resolve().parents[1].joinpath("src", "css", "patch-tag-marks.css").read_text(encoding="utf-8")
    assert ".tag-marks ul.changes > li.terrain-row > .tnum-dia { position: absolute; left: 8px;" in css
    # the small solid diamond of the 06.11 mock, gold
    # the mock's ◆ glyph at 8px, gold ("там были маленькие")
    assert 'color: var(--gold); font-size: 8px;' in css and '.tnum-dia::before { content: "\\25C6"; }' in css


def test_a_stats_cards_tags_are_tiles_too():
    # owner 2026-11-06, 7.38 Heaven's Halberd: "ты забыл внутри карточек теги поменять на теги-закладки"
    from patch.css_bundle import read_css
    css = read_css()
    # ... and a game formula's title (owner 2026-11-08, 7.40 Assist Gold Formula)
    assert ("  .tag-marks ul.changes > li > .badge[data-tag], .tag-marks .properties-change .property-tag .badge[data-tag],\n"
            "  .tag-marks .formula-change-title > .badge[data-tag] {\n"
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
    assert css.count("viewBox='0 0 14 14'") == 8          # + TEASER's tentacle (owner 2026-11-19)
    # REWORK is a filled gear like the owner's reference picture (2026-11-07; pixel gears were "маленькая и толстая",
    # "опять ужасная"), shown 16px: a ring, 8 teeth, a hole
    rework = css.split('.filter-btn[data-filter="rework"] {', 1)[1].split("\n", 1)[0]
    assert "viewBox='0 0 16 16' fill='black'" in rework and "crispEdges" not in rework
    from scripts.gen.gen_tag_marks_css import gear_path
    d = gear_path()
    assert d.count("z") == 10 and d.count("A") == 4          # ring + 8 teeth + hole
    assert '.badge[data-tag~="rework"]::before { width: 16px; height: 16px; }' in css
    src = (ROOT / "patch" / "page.py").read_text(encoding="utf-8")
    assert "terrain_rows_tagged(out)" in src


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


def test_a_game_formula_title_tag_is_a_tile():
    # 7.40 Assist Gold Formula: "остался старый тег rework"
    css = (ROOT / "src" / "css" / "patch-tag-marks.css").read_text(encoding="utf-8")
    assert ".tag-marks .formula-change-title > .badge[data-tag] {" in css
    assert '.tag-marks .formula-change-title > .badge[data-tag~="rework"]::before' in css


def test_a_covered_row_is_hidden_but_keeps_its_tag():
    from patch.badges import t
    html = el.li("Now also increases Battery Assault radius to 330", t("NEW"), covered=True)
    assert 'class="iab-covered covered-card"' in html and 'data-tag="buff new"' in html


def test_an_item_potency_row_has_a_grey_stripe_and_the_games_icon():
    # owner 2026-11-19: "по аналогии со строками aghanim scepter/shard … чуть подсвеченную (допустим серым) строчку и
    # эту иконку для строк с item potency"
    from patch.css_bundle import read_css
    html = el.li("Bash chance is now modified by Item Potency", el.t("NEW") if hasattr(el, "t") else "")
    assert 'class="item-potency"' in html or "item-potency" in html.split(">", 1)[0]
    assert '<span class="aghanim-marker potency"></span>' in html
    css = read_css()
    assert ".aghanim-marker.potency" in css and "ul.changes li.item-potency" in css
    assert (ROOT / "icons" / "stats" / "item_potency.png").exists()


def test_no_all_changes_tip_and_only_the_name_links():
    # owner 2026-11-19: "All changes of X убрать из подсказок отовсюду … переходить только если кликнуть по названию,
    # а не иконке" (the icon is kept for the Item Potency mark)
    for html in (el.item_header("Desolator"), el.hero_header("Axe")):
        assert "All changes of" not in html
        icon = html.split('class="entity-icon', 1)[1].split("</div>", 1)[0]
        assert "<a " not in icon
        assert 'class="entity-link"' in html.split('class="entity-name"', 1)[1]


def test_rows_of_a_new_block_get_no_bullet():
    # owner 2026-11-19, 7.42 Radigull's Eggstremism "• New ability": "забыл убрать точки … мы таких не ставим никогда"
    from patch.css_bundle import read_css
    css = read_css()
    assert '.entity-block.is-new ul.changes li:not([class*="ability-row"]) > .row-text::before,' not in css
    assert '.entity-block.is-new ul.changes li:not([class*="ability-row"]) > .row-text::before {' not in css


def test_item_icon_marks_come_from_the_games_flags():
    # owner 2026-11-19: variant 2 — the Item Potency mark on the item's icon, a Dormant Curio one under it; the values
    # are the items.txt entries flagged apply_effectiveness / apply_curio_bonus, shown as the game's tooltip sentences
    from patch.item_marks import item_marks
    skadi = item_marks("Eye of Skadi", "7.42")
    assert "item-mark-potency" in skadi and "<b>-20%</b>" in skadi and "<b>-40%</b>" in skadi
    assert "item-mark-curio" not in skadi
    assert "item-mark-curio" in item_marks("Gunpowder Gauntlets", "7.42")
    assert item_marks("Blink Dagger", "7.42") == ""
    from patch.state import _State
    saved = _State.current_patch_version
    try:
        _State.current_patch_version = "7.42"
        icon = el.item_header("Eye of Skadi").split('class="entity-icon', 1)[1].split('<div class="entity-name"', 1)[0]
        assert '<span class="item-marks">' in icon
    finally:
        _State.current_patch_version = saved
    html = el.li("Now improved by Dormant Curio", "")
    assert "curio-row" in html and '<span class="aghanim-marker curio"></span>' in html


def test_abilities_that_set_attack_potency_carry_the_mark_from_742():
    # owner 2026-11-19: "Ставить такой значок на иконки этих способностей — да"; data from the code of 7.42
    from patch.item_marks import ability_marks
    assert "Slashes: 60% Item Potency" in ability_marks("pangolier_swashbuckle", "7.42")
    assert ability_marks("pangolier_swashbuckle", "7.41f") == ""          # values known for 7.42 on
    assert ability_marks("pangolier_rolling_thunder", "7.42") == ""
    from patch.item_marks import item_marks
    assert "Illusions (20% Item Potency): <b>8</b>" in item_marks("Diffusal Blade", "7.42")
