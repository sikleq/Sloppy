"""Owner's second review of 2026-11-07: an ability with no picture shows the game's placeholder, the icon script leaves
an unchanged picture alone, Dragon Knight's shared row starts with the icons."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _script():
    pytest.importorskip("PIL")
    spec = importlib.util.spec_from_file_location("boss_icons", ROOT / "scripts" / "fetch" / "extract_vpk_boss_icons.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_strength_of_the_immortal_has_the_games_placeholder_until_it_gets_a_picture():
    # "лучше не с ликвипедии брать и похожую иконку, а на плейсхолдер"
    mod = _script()
    assert mod.PLACEHOLDER == "empty" and "roshan_devotion" in mod.ABILITIES
    p739 = (ROOT / "content" / "p739.py").read_text(encoding="utf-8")
    assert 'ability("Strength of the Immortal", icon_url="../icons/abilities/roshan_devotion.png")' in p739
    assert "roshan_halloween_levels" not in p739


def test_the_icon_script_does_not_rewrite_a_picture_it_already_has(tmp_path):
    pytest.importorskip("PIL")
    mod = _script()
    from PIL import Image
    dst = tmp_path / "a.png"
    Image.new("RGBA", (4, 4), (10, 20, 30, 255)).save(dst)
    assert mod.same_picture(Image.new("RGBA", (4, 4), (10, 20, 30, 255)), dst)
    assert not mod.same_picture(Image.new("RGBA", (4, 4), (11, 20, 30, 255)), dst)
    # a portrait keeps the size the site has for it (the Tormentor's is square)
    assert mod.unit_portrait(Image.new("RGBA", (128, 72)), dst).size == (4, 4)


def test_a_named_subgroup_stays_under_a_filter():
    # "при включении фильтра new исчезли названия" (7.38 Lotus Pools, Shrines of Wisdom)
    css = (ROOT / "src" / "css" / "patch-formula-tables.css").read_text(encoding="utf-8")
    assert "body.filter-active h4.subgroup:not(.subgroup-named) { display: none; }" in css
    from patch.elements import GENERIC_SUBGROUPS
    assert {"abilities", "facets", "general"} <= GENERIC_SUBGROUPS
    from builders.entity_changes import _SUBGROUP_RE
    assert _SUBGROUP_RE.search('<h4 class="subgroup subgroup-named">Lotus Pools</h4>').group(1) == "Lotus Pools"


def test_how_neutrals_cast_a_new_ability_goes_under_its_question_mark():
    # "это по сути не изменение, а доп. информация механики нейтральных крипов" (7.38 Boglet, Marshmage)
    from tools.patchgen.post_general import _postprocess_neutral_cast_notes
    lines = ['    W(li("Active: Creates a barrier bubble. Cooldown: 16s"))',
             '    W(li("Neutrals will cast this ability on a random ally that is below 50% health", t("MISC")))']
    assert _postprocess_neutral_cast_notes(lines) == [
        '    W(li("Active: Creates a barrier bubble. Cooldown: 16s", extra=inline_note("Neutrals will cast this ability '
        'on a random ally that is below 50% health")))']
    # after a change row it is a change of its own and stays (7.38 Petrify)
    changed = ['    W(li("DPS increased from 75 to 100", b(75, 100)))',
               '    W(li("Neutrals will autocast this ability only if the Shaman has less than 90% health", t("MISC")))']
    assert _postprocess_neutral_cast_notes(changed) == changed
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert 'W(li("Neutrals will cast this ability' not in p738


def test_the_patch_info_card_is_folded_at_first():
    # "по умолчанию такая инфа свёрнута"; then "Вариант 1": a card above the filters
    from patch.page import patch_info_html
    html = patch_info_html("7.39", "21.05.2025")
    # open at first since 2026-11-07 evening ("official notes блок пусть тоже по умолчанию включен")
    assert html.startswith('<div class="pinfo-card" id="pinfo-card">')
    assert '<span>After 7.38c</span><span class="pi-val"><b>55</b> days</span>' in html
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


def test_amplifications_replaced_by_less_health_restoration_are_a_nerf():
    # "+25% Lifesteal and Health Regen Amplifications replaced with +20% Health Restoration — а разве это не nerf?"
    from tools.patchgen.post_general import _postprocess_umbrella_stat_rows
    row = ('    W(li("+25% Lifesteal and Health Regen Amplifications replaced with +20% Health Restoration", '
           't("REWORK")))')
    assert _postprocess_umbrella_stat_rows([row]) == [
        '    W(li("+25% Lifesteal and Health Regen Amplifications replaced with +20% Health Restoration", b(25, 20)))']
    other = '    W(li("Mana Burn replaced with Mana Break", t("REWORK")))'
    assert _postprocess_umbrella_stat_rows([other]) == [other]
    p739 = (ROOT / "content" / "p739.py").read_text(encoding="utf-8")
    assert "Amplifications replaced with +20% Health Restoration\", t(\"REWORK\")" not in p739


def test_a_healing_cut_turned_into_a_7_39_health_restoration_cut_is_a_nerf():
    # "другие случаи тоже проверь": 7.39 Health Restoration did not touch incoming heals (it does since 7.41)
    from tools.patchgen.post_general import _postprocess_lost_heal_cut_rows
    lost = ('    W(li("Frost instead of reducing Healing, Health Regen, Lifesteal, and Spell Lifesteal by 13%, now reduces '
            'Health Restoration by 13%", t("MISC")))')
    out = _postprocess_lost_heal_cut_rows([lost])[0]
    assert ', t("NERF"), extra=inline_note("Health Restoration does not reduce incoming healing' in out
    # Skadi also cuts Heal Amplification: the healing cut stays, MISC
    kept = ('    W(li("Cold Attack instead of reducing Healing, Health Regen, Lifesteal, and Spell Lifesteal by 40%, now '
            'reduces Health Restoration and Heal Amplification by 40%", t("MISC")))')
    assert _postprocess_lost_heal_cut_rows([kept]) == [kept]
    p739 = (ROOT / "content" / "p739.py").read_text(encoding="utf-8")
    assert p739.count('t("NERF"), extra=inline_note("Health Restoration does not reduce incoming healing') == 7


def test_a_facet_text_of_one_string_stays_one_text():
    # "карточки сломались?" — 7.39 Malignant Mist's card showed one row per letter
    from patch.number_tips import _facet_attr_rows
    assert _facet_attr_rows("Mist Coil also deals 40% attack damage") == ("Mist Coil also deals 40% attack damage", "")
    html = (ROOT / "dist" / "patches" / "7.39.html")
    if html.exists():
        assert '<div class="ability-change-row">M</div><div class="ability-change-row">i</div>' not in html.read_text(
            encoding="utf-8")


def test_the_version_arrows_light_up_alike_without_a_jerk():
    # "если на стрелочку влево наводить … подсвечивается. если на правую, то дёргается"
    css = (ROOT / "src" / "css" / "version-nav.css").read_text(encoding="utf-8")
    assert ".version-nav-arrow.is-next:hover" not in css and ".version-nav-arrow.is-prev:hover" not in css


def test_legion_commanders_7_39_rework_counts_as_a_nerf_in_the_weights():
    # "оставить rework, но вообще стоило бы в весах учитывать и как нерф"
    from patch.weights import row_scores
    p739 = (ROOT / "content" / "p739.py").read_text(encoding="utf-8")
    assert ('now increases Health Restoration by 30/40/50/60%", t("REWORK"), covered=True, force_tag="rework nerf"))'
            in p739)
    net, vol = row_scores("Instead of increasing Healing by 50%, now increases Health Restoration by 30/40/50/60%",
                          {"rework", "nerf"})
    assert net < 0 < vol


def test_dragon_knights_shared_row_starts_with_the_icons():
    # "сначала иконки способностей подряд, потом Damage type changed to Physical"
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert '"Breathe Fire", "Dragon Tail", "Wyrm\'s Wrath", "Fireball")) + " Damage type changed to Physical"' in p738
