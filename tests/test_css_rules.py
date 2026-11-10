"""Guards plain stylesheet and script rules: layout of headers, icons, folds, tooltips, fonts, phone width.
"""

import pathlib
import pytest
import re
from patch.css_bundle import read_css
from pathlib import Path

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_head_icons_line_up_with_the_digits_and_tails_never_break():
    from patch.css_bundle import read_css
    from patch.cards_rows import _glue_tail
    assert "position: relative; top: -1px; }" in read_css().split(".iab-ico {", 1)[1].split("\n", 1)[0]
    chip = '<span class="ability-chip chip-word" data-tooltip="Power Rune" role="img"><img src="p.png"></span>'
    out = _glue_tail("upon activating any " + chip + ' <!--TIP--><span class="info-tip">?</span><!--/TIP-->')
    assert out.startswith('upon activating <span class="li-tail">any ' + chip)


def test_regen_icons_are_heart_and_drop_with_a_plus():
    # the up arrow misled on a decrease; the plus in the corner (owner 2026-11-06, variant 5)
    for name in ("health_regen.svg", "mana_regen.svg"):
        svg = (ROOT / "icons" / name).read_text(encoding="utf-8")
        assert '<circle cx="194" cy="194" r="62"' in svg and "translate(146 146) scale(0.375)" in svg
        assert "H140v76" in svg and "l96-96" not in svg                     # the plus, not the arrow


def test_generals_icon_square_is_symmetric():
    from patch.css_bundle import read_css
    css = read_css()
    # two side by side the full height (the block's 2-row grid had won over it), three: two over one in the middle
    assert ".ability-block.other-block > .ability-icon-wrap > .stat-mosaic.n2 { grid-template-rows: 1fr; }" in css
    assert ".stat-mosaic.n3 > .sm-cell:last-child { grid-column: span 2; }" in css
    # never more than four: no grids of five or six (owner 2026-11-06)
    assert ".stat-mosaic.n5" not in css and ".stat-more" not in css


def test_the_version_arrows_light_up_alike_without_a_jerk():
    # "если на стрелочку влево наводить … подсвечивается. если на правую, то дёргается"
    css = (ROOT / "src" / "css" / "version-nav.css").read_text(encoding="utf-8")
    assert ".version-nav-arrow.is-next:hover" not in css and ".version-nav-arrow.is-prev:hover" not in css


def test_a_tall_tooltip_stays_on_the_screen():
    # audit: 7.38c Flaming Lasso's list ran 33px off the screen's foot
    js = (ROOT / "src" / "js" / "tooltips.js").read_text(encoding="utf-8")
    assert "top = Math.max(8, window.innerHeight - tipRect.height - 8)" in js


def test_layout_fixes_of_the_audit():
    css = lambda n: (ROOT / "src" / "css" / f"{n}.css").read_text(encoding="utf-8")
    assert ".terrain-stats-page .ts-table-wrap { overflow-x: visible; }" in css("terrain-controls")
    assert ".terrain-stats-page .tf-tiles.ts-tiles { grid-template-columns: repeat(3," in css("terrain-controls")
    assert "@media (max-width: 1500px) { .ec-hs-table .ec-hs-face { display: none; } }" in css("overrides")
    assert ".mr-table { display: block; overflow-x: auto; }" in css("mana-items")
    assert "@media (min-width: 821px) and (max-width: 1500px)" in css("hero-lab-tooltip")
    assert ".creeps-page.ec-index .creeps-scroll { min-height:" in css("creeps-table")
    assert ".hd-remove-group { flex-wrap: wrap;" in css("hero-lab-tooltip")
    js = (ROOT / "src" / "js" / "changes-index.js").read_text(encoding="utf-8")
    assert "// once at load too" in js


def test_the_barracks_card_is_a_picture_not_a_square():
    pil = pytest.importorskip("PIL.Image")
    im = pil.open(ROOT / "icons" / "structures" / "barracks.png").convert("RGB")
    assert im.size == (128, 72) and len(set(im.getdata())) > 50


def test_the_line_under_a_card_starts_at_the_pane_it_runs_under():
    # audit, 7.38 Sanguivore: the line hung 22px under the left pane, from the taller right one's foot
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert "const above = before && (before.querySelector(':scope > .ability-change-old" in js


def test_the_calendar_summary_has_no_dot_separator():
    from patch import calendar
    src = Path(calendar.__file__).read_text(encoding="utf-8")
    assert "&middot;" not in src and 'class="cal-ys-item"' in src


def test_the_fold_glass_is_light_on_the_page():
    """Owner 2026-10-30: "озаботься, чтобы не нагружало страницу" — the fold control has no animation and blurs only
    while folded."""
    import re
    css = read_css()
    block = css[css.index("/* the open / close control"):]
    block = block[:block.index("@media (prefers-reduced-motion: reduce) { .acr-fold-toggle")]
    assert not re.search(r"\banimation(?:-name)?\s*:", block) and "@keyframes" not in block
    assert "backdrop-filter: blur(" in block
    assert re.search(r"\.acr-fold\.is-open \.acr-fold-toggle \{[^}]*backdrop-filter: none", block)


def test_a_folded_texts_icons_do_not_grow():
    import re
    """Owner 2026-10-30: a hovered icon in a folded text was cut with the text (7.38 Mind of Tornarus' Wex)."""
    css = read_css()
    assert ".acr-fold:not(.is-open) .acr-fold-body .ability-chip:hover > img { transform: none;" in css
    # open, nothing cuts it (owner: "wex тут всё ещё обрезается при наведении")
    assert re.search(r"\.acr-fold\.is-open \.acr-fold-body \{[^}]*overflow: visible", css)


def test_a_chips_hidden_name_takes_no_width():
    # opacity 0 keeps its width: in the Lifesteal tables by the right edge it widened a 375 px page to 401 px
    css = read_css()
    assert re.search(r"\.ability-chip\[data-tooltip\]:not\(:hover\)::after \{ display: none; \}", css)


def test_a_long_card_header_wraps_on_a_phone():
    # 7.38 Demonic Cleanse "Active – granted by Shard, shares level with Demonic Purge" made a 375 px page 471 px wide
    # 2026-11-06: the title wraps everywhere (the values stay on the first line); on a phone the values may go under it
    css = read_css()
    assert ".iab-title { white-space: normal;" in css
    assert re.search(r"@media \(max-width: 640px\) \{ \.iab-head \{ flex-wrap: wrap; \} \}", css)


def test_the_innate_mark_stays_on_the_grown_icon():
    css = (ROOT / "src" / "css" / "patch-new-entity-rows.css").read_text(encoding="utf-8")
    rule = css[css.index(".ability-chip:hover > .chip-innate-marker {"):]
    rule = rule[:rule.index("}")]
    assert "display: none" not in rule and "scale(2)" in rule


def test_every_page_head_has_the_phone_viewport_and_local_fonts():
    import patch.site_common as site
    head = site.head_common("../")
    assert head.count('name="viewport" content="width=device-width, initial-scale=1"') == 1
    for name in site.PRELOAD_FONTS:
        assert f'href="../src/fonts/{name}.woff2" as="font"' in head
        assert (ROOT / "src" / "fonts" / f"{name}.woff2").exists()


def test_aghanims_cards_keep_even_padding_inside_an_ability_change_block():
    css = read_css()
    rule = re.search(r"\.ability-change-block \.ability-change\.unified-panes\.aghs-change > \.ability-change-pane"
                     r"\s*\{([^}]*)\}", css)
    assert rule and "padding: 10px 14px" in rule.group(1) and "--pt: 10px" in rule.group(1)
