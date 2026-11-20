"""A phone's scroll must not redraw the page's card lines (owner 2026-11-20: "сайт на телефоне очень лагает,
прокрутка — фриз на 3 секунды"). Its address bar hides and shows as it scrolls: a resize of the height only. Each one
redrew every connector of the page (155 ms on a computer for 7.42, seconds on a phone)."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_connectors_redraw_only_on_a_new_width_and_once_it_settles():
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert not re.search(r"addEventListener\('resize',\s*draw(?:AbilityChange|Brewling)Connectors\)", js)
    assert "window.innerWidth === lastW" in js and "setTimeout(window.sloppyDrawConnectors" in js


def test_a_moved_talent_with_another_case_is_the_same_talent():
    # 7.42 Elder Titan: "+2.5% … Move Speed Per Hero" -> "+3.5% … Move Speed per Hero" read as two talents ("was …")
    from patch.talent_marks import change_cells
    name, _level, value = change_cells("+2.5% Astral Spirit Bonus Move Speed Per Hero",
                                       "+3.5% Astral Spirit Bonus Move Speed per Hero", 10, 15)
    assert name == "Astral Spirit Bonus Move Speed per Hero" and value.startswith("+2.5% → ") and "was" not in value


def test_a_neutral_ability_with_four_values_scales_with_game_time():
    # 7.42 Odobenus Blight "2 3 4 5": level 2 at 15:00, 3 at 30:00, 4 from Helm of the Overlord / Chen's Shard
    from patch.ability_kv import ability_props
    from patch.card_sections import time_levels_hint
    assert ability_props("odobenus_blight", "7.42").get("time_scaled")
    html = ('<div class="ability-change x"><div class="ability-change-pane">Passive – scales with game time</div>'
            '<div class="vt-v"><b class="iab-num">2/3/4/5</b></div></div><div class="ability-block">')
    out = time_levels_hint(html)
    assert "Levels with game time" in out and "From 15:00" in out and "Helm of the Overlord" in out


def test_terrain_stats_head_sticks_on_a_phone():
    # 2026-11-20: the table's own sideways scroll box held its sticky head, so on a phone the head ran off with the page
    css = (ROOT / "src" / "css" / "terrain-controls.css").read_text(encoding="utf-8")
    assert not re.search(r"\.ts-table-wrap\s*\{[^}]*overflow-x:\s*auto", css)
    phone = css[css.index(".terrain-stats-page .ts-wrap { display: contents; }") - 40:]
    assert "@media (max-width: 760px)" in phone and "position: sticky; left: 0;" in phone


def test_a_phone_has_no_blur_under_the_sticky_header():
    css = (ROOT / "src" / "css" / "phones.css").read_text(encoding="utf-8")
    block = css[css.index("@media (max-width: 760px)"):]
    assert "nav.top-nav { backdrop-filter: none;" in block
