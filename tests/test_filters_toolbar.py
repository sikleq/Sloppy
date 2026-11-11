"""Guards the page controls: the filters card and its button, the corner stack, the info card, search, back-to-top.
"""

import os
import pathlib
import pytest
import re
from patch.js_bundle import read_js

ROOT = pathlib.Path(__file__).resolve().parents[1]


# ---- second review of 2026-11-08 (audit before 7.42) ----

def _page(v):
    html = ROOT / "dist" / "patches" / f"{v}.html"
    if not html.exists():
        pytest.skip("no build")
    return html.read_text(encoding="utf-8")


_ROOT_1110 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_search_jumps_at_once_and_lights_the_block():
    from patch.js_bundle import read_js
    from patch.css_bundle import read_css
    js = read_js()
    assert "behavior: 'instant'" in js and "hit.classList.add('search-hit')" in js
    assert ".ability-change-pane .iab-head .iab-name" in js                  # Tree Dance in a facet's card head
    assert "@keyframes search-hit" in read_css()


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


def test_the_patch_info_is_a_folded_card_above_the_filters():
    # owner 2026-11-07, mock "Вариант 1": "Official notes и другую инфу сделать в таком же блоке, только выше панели
    # фильтров … кнопку … в центр верхней кромки панели тегов-фильтров"
    from patch.page import filter_pop_html, patch_info_html
    html = patch_info_html("7.38", "19.02.2025")
    assert html.startswith('<div class="pinfo-card" id="pinfo-card"><a class="pi-official" '
                           'href="https://www.dota2.com/patches/7.38"')
    assert '<span>Released</span><span class="pi-val"><b>19.02.2025</b> 00:53 UTC</span>' in html
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


def test_a_named_subgroup_stays_under_a_filter():
    # "при включении фильтра new исчезли названия" (7.38 Lotus Pools, Shrines of Wisdom)
    css = (ROOT / "src" / "css" / "patch-formula-tables.css").read_text(encoding="utf-8")
    assert "body.filter-active h4.subgroup:not(.subgroup-named) { display: none; }" in css
    from patch.elements import GENERIC_SUBGROUPS
    assert {"abilities", "facets", "general"} <= GENERIC_SUBGROUPS
    from builders.entity_changes import _SUBGROUP_RE
    assert _SUBGROUP_RE.search('<h4 class="subgroup subgroup-named">Lotus Pools</h4>').group(1) == "Lotus Pools"


def test_the_patch_info_card_is_folded_at_first():
    # "по умолчанию такая инфа свёрнута"; then "Вариант 1": a card above the filters
    from patch.page import patch_info_html
    html = patch_info_html("7.39", "22.05.2025")
    # open at first since 2026-11-07 evening ("official notes блок пусть тоже по умолчанию включен")
    assert html.startswith('<div class="pinfo-card" id="pinfo-card">')
    assert '<span>After 7.38c</span><span class="pi-val"><b>56</b> days</span>' in html   # 7.39 out 22.05.2025
    css = (ROOT / "src" / "css" / "patch-toolbar.css").read_text(encoding="utf-8")
    assert "sec-pinfo" not in css and ".pinfo-card[hidden] { display: none; }" in css


def test_the_filters_button_stands_in_the_corner_stack():
    # "иконку фильтров всё же вынеси сюда и адаптируй"; the card "по правому краю … центрировано на странице"
    js = (ROOT / "src" / "js" / "filter-fab.js").read_text(encoding="utf-8")
    assert "rail.style.top" not in js
    nav = (ROOT / "src" / "css" / "nav.css").read_text(encoding="utf-8")
    assert "filter-toggle" not in nav


def test_the_index_has_no_colour_blind_switch():
    # "убрать с index фильтр дальтонизма, т.к там нет ничего для этого режима"
    from patch.site_common import render_top_nav
    assert 'class="cb-toggle"' not in render_top_nav("main", "patches/7.41f.html", centre_tabs=False,
                                                     colour_blind=False)
    assert 'class="cb-toggle"' in render_top_nav("materials", "patches/7.41f.html")
    # the calendar too ("в календаре ещё кнопка, если там нечего перекрашивать — тоже убери")
    for name in ("index_page.py", "calendar.py"):
        assert "colour_blind=False)" in (ROOT / "patch" / name).read_text(encoding="utf-8")


def test_back_to_top_is_grey_at_the_pages_top():
    # "кнопка «наверх» должна быть тусклой/серой, если я наверху страницы уже"
    js = (ROOT / "src" / "js" / "back-to-top.js").read_text(encoding="utf-8")
    assert "btt.classList.toggle('at-top', atTop)" in js
    css = (ROOT / "src" / "css" / "pixel-skin.css").read_text(encoding="utf-8")
    assert ".corner-dock > .back-to-top.at-top { filter: grayscale(1); opacity: 0.4;" in css


def test_back_to_top_jumps_at_once():
    # "чтобы телепортировало наверх, а не везло"
    for f in (ROOT / "patch" / "page.py", ROOT / "builders" / "entity_changes.py"):
        src = f.read_text(encoding="utf-8")
        assert "behavior:\\'instant\\'" in src and "behavior:\\'smooth\\'" not in src


def test_the_weights_button_on_is_framed_like_its_neighbours():
    # owner: "она загорается полностью, а не рамку"
    css = (ROOT / "src" / "css" / "pixel-skin.css").read_text(encoding="utf-8")
    rule = css[css.index(".corner-dock > .dyn-w-fab.active {"):]
    rule = rule[:rule.index("}")]
    assert "box-shadow: inset 0 0 0 1px rgba(227, 196, 106, 0.6)" in rule and "%23e3c46a" in rule


def test_old_cards_are_not_dimmed_and_the_dock_has_no_button_for_it():
    # 2026-11-08 the old halves were dimmed with a corner button; 2026-11-09 "фильтр блюра для предметов удалить, как и
    # функцию. предметы пусть как сейчас" — the old ability card lies under the new one instead (card_deck)
    text = _page("7.40")
    dock = text[text.index('<div class="corner-dock">'):]
    dock = dock[:dock.index("</div>")]
    assert "old-fab" not in dock and "old-cards-btn" not in text
    css = (ROOT / "src" / "css" / "pixel-skin.css").read_text(encoding="utf-8")
    assert "show-old" not in css and "old-fab" not in css
    assert "grid-template-columns: repeat(4, 34px)" in css      # "панель в 4 иконки"
    from patch.js_bundle import JS_PARTS
    assert "old-cards" not in JS_PARTS and not (ROOT / "src" / "js" / "old-cards.js").exists()


def test_search_result_owner_keeps_its_gap():
    css = open(os.path.join(_ROOT_1110, "src", "css", "patch-toolbar.css"), encoding="utf-8").read()
    assert "white-space: nowrap; margin-left: 4px; }" in css


def test_the_search_knows_facets_and_abilities_a_row_names_by_its_icon():
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert ".ability-chip[aria-label], .facet-chip[aria-label]" in js      # 7.38 Exorcism has rows and no block
    assert "kind: isFacet ? 'facet' : 'ability'" in js                     # 7.38 Ebb read "ability"
    assert 'class="result-facet"' in js                                    # ... with an empty picture
    assert ".stack-icon" in js                                             # each of a block's icons by its own name


def test_filter_keeps_a_header_only_ability_apart_from_its_rows():
    # Brewmaster 7.41: Primal Split (rows live in the Brewling blocks under it) stayed hidden after the Heroes
    # category filter was switched off
    js = read_js()
    assert "if (!ul) { headerOnly.push(block); return; }" in js
