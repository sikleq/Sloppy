"""Owner 2026-09-28 (Abaddon 7.38): a hero's GENERAL block starts with an attributes card (base + gain, base damage,
damage per attribute; before -> after) and a table of attack damage by level; the rows it shows are hidden."""
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
        assert el._hs_covered("Damage at level 30 decreased by 25 (from 173-183 to 148-158)", {"nerf"})
        assert el._hs_covered("Strength gain increased from 2.2 to 2.6", {"buff"})
        assert el._hs_covered("Base Intelligence decreased from 19 to 18", {"nerf"})
        assert not el._hs_covered("Mist Coil damage increased from 100 to 120", {"buff"})
        html = el.render_hs_card("hero|abaddon|7.38")
        assert 'data-tag="buff nerf"' in html
        assert "173–183" in html and "148–158" in html                     # Valve's level-30 figures
        # one line per attribute: "1.6 → 2.0" (the new value in its %'s shade) and the % beside it
        assert re.search(r'<span class="hs-old">2\.2</span><span class="hs-to">→</span>'
                         r'<span class="badge buff\d+ tone">2\.6</span>', html)
        assert '<span class="hs-same">22</span>' in html                   # an unchanged base stays plain
        assert "0.45" in html and "Makes up for the lower damage per attribute" in html
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.current_hero, _State.hs_card = saved


def test_generator_puts_the_card_first_in_general():
    import generate_patch_code_v2 as g
    lines = ['W(hero_header("Abaddon"))', "W(ul_open())", 'W(li("Base Damage increased by 26", t("BUFF")))',
             'W(li("Damage at level 1 increased by 10 (from 40-50 to 50-60)", br(40, 50, 50, 60)))', "W(ul_close())"]
    out = g._postprocess_hero_stat_card(lines)
    assert out[2] == "W(hero_stat_card())" and g._postprocess_hero_stat_card(out) == out
    plain = ['W(hero_header("Axe"))', "W(ul_open())", 'W(li("Base Armor increased by 1", t("BUFF")))', "W(ul_close())"]
    assert g._postprocess_hero_stat_card(plain) == plain
