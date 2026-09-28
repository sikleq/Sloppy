"""Owner 2026-09-28 (Abaddon 7.38): a hero whose damage growth Valve rescaled gets two rows at the top of GENERAL,
"Starting damage …" and "Damage gain per level …", each with its own tag, the second opening the damage by level;
Valve's damage rows under them are hidden."""
import re

from patch import elements as el
from patch.hero_stats import damage_at, hero_stats, universal_multiplier
from patch.state import _State


def test_the_damage_model_matches_valves_level_1_figures():
    # Valve's own "Damage at level 1 increased by 10 (from 40-50 to 50-60)"
    old, new = hero_stats("Abaddon", "7.37e"), hero_stats("Abaddon", "7.38")
    assert tuple(int(x) for x in damage_at(old, "7.37e", 1)) == (40, 50)
    assert tuple(int(x) for x in damage_at(new, "7.38", 1)) == (50, 60)
    # "Damage at level 30 ... (from 173-183 to 148-158)": with all 7 Attribute Bonus levels
    assert tuple(int(x) for x in damage_at(old, "7.37e", 30, bonus=True)) == (173, 183)
    assert universal_multiplier("7.37e") == 0.7 and universal_multiplier("7.38") == 0.45


def test_card_hides_its_rows_and_carries_their_tags():
    saved = (_State.current_entity_key, _State.current_patch_version, _State.current_hero, _State.hs_card)
    try:
        _State.current_entity_key, _State.current_patch_version, _State.current_hero = "hero|abaddon", "7.38", "Abaddon"
        slot = el.hero_stat_card()
        assert slot == "<!--HSCARD:hero|abaddon|7.38-->"
        assert el._hs_covered("Base Damage increased by 26", {"buff"})
        assert el._hs_covered("Damage at level 1 increased by 10 (from 40-50 to 50-60)", {"buff"})
        assert el._hs_covered("Damage at level 30 decreased by 25 (from 173-183 to 148-158)", {"nerf"})
        # the attribute rows stay rows (owner 2026-09-28: "more laconic")
        assert not el._hs_covered("Strength gain increased from 2.2 to 2.6", {"buff"})
        assert not el._hs_covered("Mist Coil damage increased from 100 to 120", {"buff"})
        assert el._hs_covered("Damage gain per level decreased from +3.6 to +2.7", {"nerf"})
        html = el.render_hs_card("hero|abaddon|7.38")
        # TWO rows, each with its own tag (owner 2026-09-28: the start went up, the growth went down)
        start, gain = re.findall(r"<li .*?</li>(?=<li |$)", html, re.S)
        assert start.startswith('<li data-tag="buff" class="li-bg hs-dmg-li">')
        assert "Starting damage increased from 40–50 to 50–60<" in start and ">+22%<" in start
        assert gain.startswith('<li data-tag="nerf" class="li-bg hs-dmg-li">')
        assert ">Damage gain per level decreased from 3.6 to 2.7<" in gain and ">-25%<" in gain
        # no table by level (owner 2026-09-28: the two numbers already say it)
        assert "formula-table" not in html and "formula-trigger" not in html
        # the (?): level 30 = Valve's figure, all 7 Attribute Bonus levels counted; the multiplier
        assert "Damage at level 30: 173–183 → 148–158 (-14%)" in gain and "0.7 → 0.45 damage per attribute" in gain
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.current_hero, _State.hs_card = saved


def test_generator_puts_the_card_first_in_general():
    import generate_patch_code_v2 as g
    lines = ['W(hero_header("Abaddon"))', "W(ul_open())", 'W(li("Base Damage increased by 26", t("BUFF")))',
             'W(li("Damage at level 1 increased by 10 (from 40-50 to 50-60)", br(40, 50, 50, 60)))',
             'W(li("Damage gain per level decreased from +3.6 to +2.7", b(3.6, 2.7)))', "W(ul_close())"]
    out = g._postprocess_hero_stat_card(lines, "7.38")
    assert out[2] == "W(hero_stat_card())" and g._postprocess_hero_stat_card(out, "7.38") == out
    plain = ['W(hero_header("Axe"))', "W(ul_open())", 'W(li("Base Armor increased by 1", t("BUFF")))', "W(ul_close())"]
    assert g._postprocess_hero_stat_card(plain, "7.38") == plain
    # a lone "+1 damage at level 1" (Sven 7.41): Valve did not rescale the growth -> its own rows stay
    lone = ['W(hero_header("Sven"))', "W(ul_open())",
            'W(li("Damage at level 1 increased from 60–62 to 61–63", br(60, 62, 61, 63)))', "W(ul_close())"]
    assert g._postprocess_hero_stat_card(lone, "7.41") == lone


def test_unchanged_starting_damage_is_said_so():
    saved = (_State.current_entity_key, _State.current_patch_version, _State.current_hero, _State.hs_card)
    try:
        _State.current_entity_key, _State.current_patch_version, _State.current_hero = "hero|batrider", "7.38", "Batrider"
        el.hero_stat_card()
        el._hs_covered("Damage at level 1 increased by 0 (from 39-43 to 39-43)", {"misc"})
        html = el.render_hs_card("hero|batrider|7.38")
        # the start did not move: no row for it, only the growth's row, the (?) says so
        assert html.count("<li ") == 1 and "Starting damage unchanged at 39–43" in html
        assert re.search(r'data-tag="nerf".*>Damage gain per level decreased from [\d.]+ to [\d.]+<', html)
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.current_hero, _State.hs_card = saved
