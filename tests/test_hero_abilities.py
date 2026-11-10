"""Guards hero blocks apart from facets: innates, ability icons, new and removed abilities, the two selves of Arc Warden.
"""

import ast
import importlib
import importlib.util
import os
import pathlib
import pytest
import re
import sys
import tools.generate_patch_code_v2 as g
from patch import ability_kv, elements, elements as el, item_ability_text
from patch.api import facet_group
from patch.mech_abilities import ability_chip
from patch.state import _State, reset_page_state

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def _script():
    pytest.importorskip("PIL")
    spec = importlib.util.spec_from_file_location("boss_icons", ROOT / "scripts" / "fetch" / "extract_vpk_boss_icons.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _as_hero(hero, fn, *args):
    from patch.state import _State
    keep = _State.current_hero
    _State.current_hero = hero
    try:
        return fn(*args)
    finally:
        _State.current_hero = keep


_ROOT_738 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _p738():
    with open(os.path.join(_ROOT_738, "content", "p738.py"), encoding="utf-8") as f:
        return f.read()


post_cards = importlib.import_module("patchgen.post_cards")
post_facets = importlib.import_module("patchgen.post_facets")


def _hero_lines(*body):
    return ['W(hero_header("Arc Warden"))', *body, 'W(ability("Flux", slug="arc_warden_flux"))']


def _removed(slug, note=""):
    return [f'W(facet_header("{slug}"))', 'W(ul_open())', f'W(li("Removed", t("DEL"){note}))', 'W(ul_close())']


@pytest.fixture
def page():
    reset_page_state()
    _State.current_patch_version = "7.38"
    yield
    reset_page_state()


def _balance(*facets):
    """(del rows, net, volume) of a hero after his lost facets, separately or as one block."""
    elements.hero_header("Arc Warden")
    key = _State.current_entity_key
    if len(facets) == 1:
        elements.facet_header(facets[0][0])
        elements.ul_open()
        elements.li("Removed", '<span class="badge del" data-tag="del">DEL</span>')
        elements.ul_close()
        elements.facet_header(facets[0][1])
    else:
        facet_group(*facets)
    elements.ul_open()
    elements.li("Removed", '<span class="badge del" data-tag="del">DEL</span>')
    elements.ul_close()
    return dict(_State.dynamics[key])


def _calls(path, name):
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    lines = src.split("\n")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name:
            yield node, lines


def _kw(node, name):
    return next((k.value for k in node.keywords if k.arg == name), None)


def _rows_after(node, lines):
    """The li() lines of the list right under a card."""
    k = node.end_lineno
    while k < len(lines) and lines[k].strip() in ("))", ")", ""):
        k += 1
    if k >= len(lines) or "ul_open" not in lines[k]:
        return []
    out = []
    k += 1
    while k < len(lines) and "ul_close" not in lines[k]:
        out.append(lines[k])
        k += 1
    return out


def _name(side):
    if isinstance(side, ast.Call):
        v = _kw(side, "name")
        if isinstance(v, ast.Constant):
            return v.value
    return None


def test_a_renamed_ability_is_one_ability_and_a_replaced_one_is_not():
    # 7.41 Call of the Wild Hawk -> Summon Raptors: one icon, % on hover (owner 2026-11-06); Tinker's Defense Matrix ->
    # Deploy Turrets stays two abilities
    import pytest
    from patch.cards_ability_change import renamed
    from patch.ability_kv import _hero_blocks
    if "beastmaster_summon_raptor" not in _hero_blocks("7.41"):
        pytest.skip("no game files here")
    assert renamed("beastmaster_call_of_the_wild_hawk", "beastmaster_summon_raptor", "7.41")
    assert not renamed("tinker_defense_matrix", "tinker_deploy_turrets", "7.41")
    assert not renamed("lich_death_charge", "lich_death_charge", "7.41")


def test_a_general_block_shows_the_icons_of_all_its_stats():
    from patch.page import _swap_single_row_other_icons
    block = ('<div class="ability-block other-block"><div class="ability-icon-wrap"><img src="../icons/other.svg" alt="" '
             'class="ability-icon-img"></div><ul class="changes">{}</ul>')
    li = lambda text: f'<li data-tag="buff"><span class="row-text">{text}</span></li>'
    one = _swap_single_row_other_icons(block.format(li("Base Agility increased") + li("Agility gain increased")))
    assert 'src="../icons/agility.webp"' in one and "stat-mosaic" not in one
    three = _swap_single_row_other_icons(block.format(li("Base Movement Speed increased") + li("Strength gain decreased")
                                                      + li("Agility gain decreased")))
    assert 'class="ability-icon-img stat-mosaic n3"' in three and "other.svg" not in three
    assert three.index("move_speed.png") < three.index("strength.webp") < three.index("agility.webp")
    regen = _swap_single_row_other_icons(block.format(li("Base health regen increased") + li("Base mana regen increased")))
    assert "health_regen.svg" in regen and "mana_regen.svg" in regen
    seven = "".join(li(t) for t in ("Base damage", "Base armor", "Strength gain", "Agility gain", "Intelligence gain",
                                     "Movement speed", "Attack range"))
    many = _swap_single_row_other_icons(block.format(seven))
    # more than four stats: the General icon, as before (owner 2026-11-06: ">4 (не =4) … иконку General как раньше")
    assert "stat-mosaic" not in many and "other.svg" in many
    four = "".join(li(t) for t in ("Base damage", "Base armor", "Strength gain", "Agility gain"))
    assert 'stat-mosaic n4' in _swap_single_row_other_icons(block.format(four))
    assert three.count('<span class="sm-cell"><img') == 3          # each icon in a cell, lines between (CSS gap)
    assert (ROOT / "icons" / "health_regen.svg").exists() and (ROOT / "icons" / "mana_regen.svg").exists()


def test_a_section_heads_icon_carries_no_innate_star_and_both_kinds_are_said():
    from patch.card_sections import card_sections
    from patch.cards_item_abilities import _pane_parts
    pane = ('<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
            '<div class="ability-change-row"><span class="acr-lead-chips"><span class="ability-chip" data-tooltip="Runic '
            'Infusion" role="img"><img src="../icons/_t/abilities/arc_warden_runic_infusion.webp" alt=""><img src="x" '
            'class="chip-innate-marker"></span></span>Gains stats.</div><div class="ability-change-row"><span class="acr-lead-'
            'chips"><span class="ability-chip" data-tooltip="Magnetic Field" role="img"><img src="../icons/_t/abilities/arc_'
            'warden_magnetic_field.webp" alt=""></span></span>Pulls.</div></div></div>')
    out = card_sections(pane, "7.38")
    head = out[out.index('acr-sec-head'):out.index("</div>", out.index('acr-sec-head'))]
    assert "chip-innate-marker" not in head and "ability-chip" not in head       # words only (owner 2026-11-06)
    h = _pane_parts(["Passive and active components. Improves with game's time.", "A Zealot joins."], {"kind": "Active"})[0]
    assert '<b class="iab-kind">Active / Passive</b> <span class="iab-scale">– scales with game time</span>' in h


def test_a_removed_part_or_sub_ability_finds_its_home():
    from tools.patchgen.post_facets import _removed_ability_home, _slug_dname
    from patch.ability_kv import _hero_blocks
    import pytest
    if "pudge_eject" not in _hero_blocks("7.37e"):
        pytest.skip("no game files here")
    assert _slug_dname("muerta_parting_shot", "7.37e") == "Parting Shot"         # gone from today's list
    span = ['    W(ability("Dismember", slug="pudge_dismember"))', "    W(ul_open())",
            '    W(li("No longer upgraded with Aghanim\'s Shard", t("DEL")))', "    W(ul_close())"]
    assert _removed_ability_home("pudge", "Eject", span, "7.37e") == "said"
    morph = ['    W(ability("Adaptive Strike", slug="morphling_adaptive_strike_agi"))', "    W(ul_open())"]
    assert _removed_ability_home("morphling", "Adaptive Strike (Strength)", morph, "7.37e") == "Adaptive Strike"
    assert _removed_ability_home("muerta", "Parting Shot", [], "7.37e") is None


def test_a_list_of_the_heros_abilities_gets_their_icons():
    from patch.mech_abilities import ability_list_chips
    from patch.ability_kv import _hero_blocks
    import pytest
    if "ringmaster_crystal_ball" not in _hero_blocks("7.38") and "ringmaster_summon_unicycle" not in _hero_blocks("7.38"):
        pytest.skip("no game files here")
    out = ability_list_chips("Sets Dark Carnival Souvenirs to Crystal Ball, Unicycle and Weighted Pie", "ringmaster", "7.38")
    # the icons alone, the names on hover (owner 2026-11-06)
    assert out.count('class="ability-chip chip-word"') == 3 and "Weighted Pie<" not in out.replace('"Weighted Pie"', "")
    assert out.startswith("Sets Dark Carnival Souvenirs to <span") and "</span>, <span" in out
    assert ability_list_chips("Increases damage to 5 and Burns to 10", "ringmaster", "7.38") == \
        "Increases damage to 5 and Burns to 10"


def test_the_main_attribute_row_stands_first_on_the_page_too():
    # owner 2026-11-06: "Если герой меняет атрибут … всегда ставим вверху списка general" — the stats card's damage
    # rows were drawn above it
    from patch.general_rows import attr_row_first
    attr = ('<li data-tag="rework"><span class="badge rework">R</span><span class="row-text">Main attribute changed from '
            '<b class="attr-chip is-uni">Universal</b></span></li>')
    dmg = '<li data-tag="nerf"><span class="row-text">Starting damage decreased</span></li>'
    out = attr_row_first('<ul class="changes">' + dmg + "<!--x-->" + attr + "</ul>")
    assert out == '<ul class="changes">' + attr + dmg + "<!--x--></ul>"


def test_one_row_of_several_abilities_with_their_own_notes_stands_once():
    # owner 2026-11-06, 7.38 Tornado, E.M.P. …: "имеют общий текст, поэтому их можно в одну строку, а иконки по
    # аналогии с Attribute Shift"; each [?] under its ability's name in one
    from tools.patchgen.notes import _postprocess_same_change_abilities
    lines = ['    W(ability("Tornado", slug="invoker_tornado"))', "    W(ul_open())",
             '    W(li("Added values for levels 9 and 10", t("NEW"), extra=inline_note("Damage for levels 9 and 10 of '
             'Wex is 405/450")))', "    W(ul_close())",
             '    W(ability("E.M.P.", slug="invoker_emp"))', "    W(ul_open())",
             '    W(li("Added values for levels 9 and 10", t("NEW"), extra=inline_note("Mana Burned for levels 9 and 10 '
             'of Wex is 700/775")))', "    W(ul_close())"]
    out = _postprocess_same_change_abilities(lines)
    assert out[0] == '    W(ability_group(("Tornado", "invoker_tornado"), ("E.M.P.", "invoker_emp")))'
    assert 'inline_note("Tornado: Damage (Wex) 405/450<br>E.M.P.: Mana Burned (Wex) 700/775")' in out[2]
    assert len(out) == 4


def test_one_row_three_abilities_share_stands_once_after_the_orbs():
    # owner 2026-11-06, 7.38 Invoker: "все способности можно указать и убрать соответствующую строку у каждой из них.
    # Те способности, что получали ещё изменения оставить … Поставить строку со всеми способностями после Exort блока"
    from tools.patchgen.post_shared import _postprocess_shared_row_group
    row = '    W(li("Added values for levels 9 and 10", t("NEW"), extra=inline_note("{} for levels 9 and 10 of Wex is 1/2")))'
    lines = ['    W(hero_header("Invoker"))',
             '    W(ability("Exort", slug="invoker_exort"))', "    W(ul_open())", '    W(li("Orb", t("NEW")))', "    W(ul_close())",
             '    W(ability("Cold Snap", slug="invoker_cold_snap"))', "    W(ul_open())", row.format("Duration"),
             '    W(li("No longer heals", t("DEL")))', "    W(ul_close())",
             '    W(ability("Tornado", slug="invoker_tornado"))', "    W(ul_open())", row.format("Damage"), "    W(ul_close())",
             '    W(ability("E.M.P.", slug="invoker_emp"))', "    W(ul_open())", row.format("Mana"), "    W(ul_close())"]
    out = _postprocess_shared_row_group(lines)
    text = "|".join(out)
    assert out[5].startswith('    W(ability_group(("Cold Snap", "invoker_cold_snap"), ("Tornado", "invoker_tornado"), ("E.M.P."')
    assert text.count("Added values") == 1 and "Cold Snap: Duration (Wex) 1/2<br>Tornado: Damage (Wex) 1/2" in text
    assert 'W(ability("Cold Snap"' in text and "No longer heals" in text        # its other change stays
    assert 'W(ability("Tornado"' not in text                                    # a block left empty goes


def test_strength_of_the_immortal_has_the_games_placeholder_until_it_gets_a_picture():
    # "лучше не с ликвипедии брать и похожую иконку, а на плейсхолдер"
    mod = _script()
    assert mod.PLACEHOLDER == "empty" and "roshan_devotion" in mod.ABILITIES
    p739 = (ROOT / "content" / "p739.py").read_text(encoding="utf-8")
    assert 'ability("Strength of the Immortal", icon_url="../icons/abilities/roshan_devotion.png")' in p739
    assert "roshan_halloween_levels" not in p739


def test_dragon_knights_shared_row_starts_with_the_icons():
    # "сначала иконки способностей подряд, потом Damage type changed to Physical"
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert '"Breathe Fire", "Dragon Tail", "Wyrm\'s Wrath", "Fireball")) + " Damage type changed to Physical"' in p738


def test_a_new_innate_block_becomes_the_old_to_new_card_and_the_removed_block_goes():
    lines = ['W(hero_header("Abaddon"))',
             'W(ability("Font of Avernus", slug="abaddon_font_of_avernus", innate=True))', 'W(ul_open())',
             'W(li("Ability removed", t("DEL")))', 'W(ul_close())',
             'W(ability("Withering Mist", slug="abaddon_withering_mist", innate=True))', 'W(ul_open())',
             'W(li("New Innate ability. Passive, can\'t be leveled up", t("MISC")))', 'W(ul_close())']
    out = "\n".join(g._postprocess_new_innate_cards(lines, "7.37"))
    assert 'old=dict(name="Font of Avernus", slug="abaddon_font_of_avernus"' in out
    assert 'new=dict(name="Withering Mist", slug="abaddon_withering_mist", innate=True' in out
    assert 'summary="New innate ability."' in out and 'tag="new"' in out
    assert "Ability removed" not in out and "covered=True" in out


def test_a_new_basic_ability_block_becomes_the_new_ability_card():
    lines = ['W(hero_header("Medusa"))', 'W(ability("Gorgon\'s Grasp", slug="medusa_gorgon_grasp"))', 'W(ul_open())',
             'W(li("New basic ability.", t("MISC")))', 'W(ul_close())']
    out = g._postprocess_new_innate_cards(lines, "7.37")
    assert out[1] == 'W(new_ability("Gorgon\'s Grasp", "medusa_gorgon_grasp", version="7.37"))'


def test_an_old_innates_level_0_value_leaves_the_comparison():
    """7.36 innates had a value at level 0 (5 values); as a basic ability in 7.37 they have 4 levels."""
    lines = ['W(hero_header("Anti-Mage"))', 'W(ability("Mana Break", slug="antimage_mana_break"))', 'W(ul_open())',
             'W(li("Mana Burned per hit rescaled from 16/23/30/37/44 to 25/30/35/40", '
             'b([16, 23, 30, 37, 44], [25, 30, 35, 40])))', 'W(ul_close())']
    out = g._postprocess_innate_level0(lines, "7.37")
    assert "b([23, 30, 37, 44], [25, 30, 35, 40])" in out[3]
    # levels 1–4 the same: a NERF row with its why, not an empty badge (owner 2026-10-30: "кружок вместо тега"; then
    # "rework везде вместо buff/nerf")
    same = g._postprocess_innate_level0(
        ['W(hero_header("Anti-Mage"))', 'W(ability("Mana Break", slug="antimage_mana_break"))', 'W(ul_open())',
         'W(li("Max Mana Burned per hit rescaled from 0.8/1.6/2.4/3.2/4% to 1.6/2.4/3.2/4%", '
         'b([0.8, 1.6, 2.4, 3.2, 4], [1.6, 2.4, 3.2, 4])))', 'W(ul_close())'], "7.37")
    assert 't("NERF"), extra=inline_note("Levels 1-4 unchanged; the 0.8 it had at level 0' in same[3]


def test_a_new_innates_rows_hide_under_its_card_their_note_in_its_question_mark():
    """Owner 2026-10-30 (Persecutor: "дубль того, что уже в карточке"): the description row with its own note is hidden
    too, the note ("Illusions cause full effect") goes into the card's "?"."""
    lines = ['W(hero_header("Anti-Mage"))', 'W(ability("Persecutor", slug="antimage_persectur", innate=True))',
             'W(ul_open())', 'W(li("New innate ability. Passive, scales with Mana Void", t("MISC")))',
             'W(li("Attacks slow enemies based on how much mana they are missing", t("MISC"), '
             'extra=inline_note("Illusions cause full effect")))', 'W(ul_close())']
    out = "\n".join(g._postprocess_new_innate_cards(lines, "7.37"))
    assert 'game_ability_desc("antimage_persectur", "7.37", note="Illusions cause full effect")' in out
    assert out.count("covered=True") == 2


def test_no_longer_an_innate_leads_its_level_0_row():
    """Owner 2026-10-30: "No longer an innate ability" at the start of "Max Mana Burned per hit rescaled …" — one row."""
    lines = ['W(ul_open())', 'W(li("No longer an innate ability", t("REWORK")))',
             'W(li("Max Mana Burned per hit rescaled from 0.8/1.6 to 1.6", t("REWORK"), extra=inline_note("Levels 1-4 '
             'unchanged; the 0.8 it had at level 0 as an innate is gone (now a basic ability)")))', 'W(ul_close())']
    out = g._merge_no_longer_innate(lines)
    assert len(out) == 3 and out[1].startswith('W(li("No longer an innate ability. Max Mana Burned per hit')


def test_a_from_row_that_is_the_new_innates_whole_text_goes_under_its_card():
    """7.37 Beastmaster: "… damage block chance is increased from 50% to 100% versus non-hero units" is Rugged's
    description word for word — under the card, hidden; a "from" row that only shares some words stays."""
    out = ['W(hero_header("Beastmaster"))', 'W(ul_open())',
           'W(li("Beastmaster\'s melee hero damage block chance is increased from 50% to 100% versus non-hero units", b(50, 100)))',
           'W(li("Base armor increased from 2 to 3 for melee hero damage versus units", b(2, 3)))', 'W(ul_close())']
    taken = g._take_innate_text_rows(out, "beastmaster_rugged", "7.37")
    assert len(taken) == 1 and "damage block chance" in taken[0]
    assert any("Base armor" in ln for ln in out)
    from pathlib import Path
    src = (Path(g._HERE) / "content" / "p737.py").read_text(encoding="utf-8")
    row = next(ln for ln in src.splitlines() if "damage block chance is increased" in ln)
    assert "covered=True" in row


def test_a_card_row_opening_with_a_heros_ability_shows_its_icon_and_the_text():
    """Owner 2026-10-30 (7.38 Invoker's new facets): "его способности заменить на иконки"; after the icon the text, with
    no colon or dash ("убрать тире всё-таки после иконок"); a word that is no ability of the hero's stays."""
    from patch.cards_item_abilities import _pane_parts
    _, body = _as_hero("invoker", _pane_parts, ["Quas: When Invoker reaches level 6, he gains a bonus level",
                                                 "Passive: Grants armor.", "Unknown Thing: does a thing."])
    assert 'class="ability-chip" data-tooltip="Quas"' in body and "invoker_quas.png" in body
    assert '</span></span>When Invoker reaches' in body and ">Quas:" not in body
    assert "acr-lead-colon" not in body and "acr-lead-dash" not in body and ">Unknown Thing: does" in body


def test_card_rows_saying_the_same_of_several_abilities_merge_into_one_with_their_icons():
    """Owner 2026-10-30, 7.38 Dark Carnival Barker: three "Made exclusive to Carny Classics Facet" rows → one row,
    three icons side by side."""
    from patch.cards_item_abilities import _pane_parts
    _, body = _as_hero("ringmaster", _pane_parts, [
        "Dark Carnival Barker: Sets Dark Carnival Souvenirs to Funhouse Mirror",
        "Funhouse Mirror: Made exclusive to Carny Classics Facet",
        "Strongman Tonic: Made exclusive to Carny Classics Facet",
        "Whoopee Cushion: Made exclusive to Carny Classics Facet"])
    assert body.count("Made exclusive to Carny Classics Facet") == 1
    chips = body.split("Made exclusive")[0].rsplit('<div class="ability-change-row">', 1)[1]
    assert all(f'data-tooltip="{n}"' in chips for n in ("Funhouse Mirror", "Strongman Tonic", "Whoopee Cushion"))


def test_hero_rows_about_all_of_a_blocks_abilities_go_to_that_block():
    """Owner 2026-10-30, 7.38 Jakiro: "Both Liquid Fire and Liquid Frost …" and "… Liquid Frost is always applied with
    the first attack, Liquid Fire - with the second" → the Liquid Fire / Frost block, above its Shard row."""
    lines = ['W(hero_header("Jakiro"))', 'W(ul_open())', 'W(li("Now always attacks with his ice head first", t("NEW")))',
             'W(li("Both Liquid Fire and Liquid Frost abilities are now available", t("REWORK")))',
             'W(li("Liquid Frost first, Liquid Fire second", t("REWORK")))', 'W(ul_close())',
             'W(ability_group(("Liquid Fire", "jakiro_liquid_fire"), ("Liquid Frost", "jakiro_liquid_ice")))',
             'W(ul_open())', 'W(li("Aghanim\'s Shard reworked: not share cooldowns", t("REWORK")))', 'W(ul_close())']
    out = g._postprocess_group_rows_home(lines)
    k = next(i for i, x in enumerate(out) if "ability_group" in x)
    assert out[:4] == lines[:3] + ['W(ul_close())']
    assert out[k + 2:k + 5] == [lines[3], lines[4], lines[8]]


def test_an_ability_innate_in_its_own_patch_is_marked_innate():
    """7.37b Viper's Predator and Ursa's Maul were innates (KV "Innate" "1" of that build); the block said nothing."""
    out = "\n".join(g._render_hero({"hero_id": 47, "abilities": [{"ability_id": next(
        k for k, v in g.ABILS.items() if v[1] == "viper_predator"), "ability_notes": [
        {"indent_level": 1, "note": "Bonus damage is now decreased by the illusion damage reduction amount"}]}]},
        version="7.37b"))
    assert 'W(ability("Predator", slug="viper_predator", innate=True))' in out


def test_succubus_card_says_the_old_numbers_and_shows_the_new_ones():
    src = _p738()
    assert "Minimum lifesteal: 12%. Maximum lifesteal: 18%." in src
    assert 'hl("2%", "nerf")' in src and 'hl("14%", "nerf")' in src
    assert 'li("Spell Lifesteal decreased from 12-18% to 2-14%", br(12, 18, 2, 14), covered=True)' in src
    assert 'desc=game_ability_desc("queenofpain_succubus"' not in src


def test_the_generator_covers_a_row_its_innate_card_shows():
    src = g.generate("7.38")
    assert re.search(r'li\("Spell Lifesteal decreased from 12-18% to 2-14%".*covered=True\)', src)
    assert "TODO[old-values]" in src
    assert g._row_values_in_text('W(li("Damage increased from 5 to 9", t("BUFF")))', "Deals 3 damage") is False


def test_a_row_about_an_ability_whose_slug_its_name_does_not_spell_gets_the_icon():
    from patch.cards_rows import _lead_ability_chip
    from patch.state import _State
    _State.current_hero, _State.current_patch_version = "ringmaster", "7.38"
    chips, rest = _lead_ability_chip("Unicycle: After a 0.5s preparation, Ringmaster mounts a speedy unicycle")
    assert "ringmaster_summon_unicycle.png" in chips[0] and rest.startswith("After a 0.5s")


def test_runes_named_in_a_card_row_get_their_icons():
    from patch.mech_abilities import rune_name_chips
    out = rune_name_chips("Level 3 - Invisibility, Arcane and Haste Runes")
    for key in ("invisibility", "arcane", "haste"):
        assert f"icons/runes/{key}.png" in out
    # a list: the icons alone by commas, the names on hover (owner 2026-11-06)
    assert "Runes" not in out.replace('Rune"', "") and out.count("</span>, <span") == 2
    assert 'data-tooltip="Haste Rune"' in out
    one = rune_name_chips("Level 1 - Invisibility Rune")
    assert one.startswith("Level 1 - <span") and one.endswith("</span>")
    # inside a sentence too (owner 2026-11-06, 7.41 Runic Infusion); "or" stays, "and" is a comma
    inside = rune_name_chips("Infused with the bonuses of Power Runes for 10s")
    assert "icons/runes/power.png" in inside and inside.endswith("</span> for 10s") and "Power Runes" not in inside
    either = rune_name_chips("Duration is reduced by 33% for activating Bounty or Water Runes.")
    assert "</span> or <span" in either and either.endswith("</span>.") and "Water Runes" not in either
    assert rune_name_chips(inside) == inside                              # a second pass changes nothing
    buff = rune_name_chips("Arc Warden gains the Regeneration Rune buff for 4s")
    assert 'data-tooltip="Regeneration Rune"' in buff and "</span> buff for 4s" in buff
    plain = "Tornado pulls enemies. Any rune nearby"
    assert rune_name_chips(plain) == plain
    note = "Text<!--TIP-->Automatic Regeneration Rune effect<!--/TIP-->"
    assert rune_name_chips(note) == note


def test_a_basic_ability_turned_innate_is_a_card():
    src = _p738()
    assert 'summary="Now is an innate ability."' in src
    assert 'li("Now is an innate ability", t("REWORK"), covered=True)' in src


def test_two_heroes_are_not_mixed():
    lines = _hero_lines(*_removed("a_one")) + ['W(hero_header("Axe"))', *_removed("b_one")]
    assert post_facets._postprocess_removed_facet_groups(lines) == lines


def test_one_block_weighs_as_much_as_the_separate_ones(page):
    apart = _balance(("arc_warden_order", "arc_warden_disorder"))
    reset_page_state()
    _State.current_patch_version = "7.38"
    together = _balance("arc_warden_order", "arc_warden_disorder")
    assert together == apart


def test_a_basic_abilitys_chip_and_the_generic_icon_have_no_mark():
    assert "chip-innate-marker" not in ability_chip("Defense Matrix", "x/tinker_defense_matrix.png")
    assert "chip-innate-marker" not in ability_chip("Something", elements.INNATE_ICON_URL)


def test_the_card_takes_over_the_rows_of_a_brand_new_ability():
    names = {"plunder"}
    assert item_ability_text._restates('W(li("Passive: Plunder. Steals 150 gold from heroes", t("NEW")))', names)
    assert not item_ability_text._restates('W(li("Passive: Dig. Finds a rune", t("DEL")))', names)
    assert not item_ability_text._restates('W(li("Now a Tier 5 Artifact", t("REWORK")))', names)


def test_new_abilities_rise_beside_stats_that_all_left():
    from patch.cards_item_abilities import raise_abilities_beside_gone_stats
    from patch.cards_item_stats import properties_change
    stats = properties_change(old=[("DEL", "+150 Attack Speed"), ("DEL", "+15 Movement Speed")], new=[])
    card = ('<div class="properties-change iab-change" style="grid-template-rows:repeat(2,auto)">'
            '<div class="properties-pane pane-old"><div class="iab-card">Dig</div><div class="iab-none"></div></div>'
            '<span class="properties-arrow" style="grid-row:1 / 2">→</span>'
            '<div class="properties-pane pane-new"><div class="iab-card">Plunder</div><div class="iab-card">Buried</div></div></div>')
    html = raise_abilities_beside_gone_stats(stats + "\n" + card)
    assert 'class="properties-change iab-change iab-raised"' in html and "old-only" not in html
    old_col = html[html.index('class="iab-old-col"'):html.index('class="properties-pane pane-new"')]
    assert "+150 Attack Speed" in old_col and "Dig" in old_col and "Plunder" not in old_col
    assert "repeat(2,auto)" not in html


def test_a_stats_card_with_kept_stats_or_no_card_under_it_is_left_alone():
    from patch.cards_item_abilities import raise_abilities_beside_gone_stats
    from patch.cards_item_stats import properties_change
    stats = properties_change(old=[("DEL", "+6 Health Regen")], new=[])
    assert raise_abilities_beside_gone_stats(stats) == stats
    two_sides = properties_change(old=[("DEL", "+6 Regen")], new=[("NEW", "+6 Armor")])
    card = '<div class="properties-change iab-change"><div class="properties-pane pane-old">x</div>'
    assert raise_abilities_beside_gone_stats(two_sides + card) == two_sides + card


def test_the_generator_makes_the_card_from_valves_previous_values(monkeypatch):
    from patch import aghs_text
    monkeypatch.setattr(aghs_text, "ability_text", lambda slug, version, kind="base": f"Text of {slug} in {version}.")
    row = ('W(li("Now has the same effect for both Arc Warden and Tempest Double", t("REWORK"), extra=inline_note("Deals 15 '
           '<span class=\\"pop-note\\">(Previous values: Arc Warden: Deals 10. Tempest Double: Deals 20)</span>")))')
    upgrade = 'W(li("Aghanim\'s Shard: Does more", t("NEW")))'
    lines = ['W(ability("Flux", slug="arc_warden_flux"))', 'W(ul_open())', upgrade, row, 'W(li("Other", t("NEW")))', 'W(ul_close())']
    out = post_cards._postprocess_two_selves_cards(lines, "7.38")
    assert out[0].startswith('W(two_selves_change("Flux", "arc_warden_flux", old_desc="Text of arc_warden_flux in 7.37e.", ')
    assert 'hero="Deals 10", double="Deals 20"' in out[0] and 'both="Deals 15"' in out[0]
    assert out[0].endswith(', rows_first=lambda: [li("Other", t("NEW"))]))')
    assert out[1:] == ['W(ul_open())', upgrade, 'W(ul_close())']


def test_an_innate_with_nothing_to_cast_is_passive():
    assert ability_kv._kind("DOTA_ABILITY_BEHAVIOR_NOT_LEARNABLE", innate=True) == "Passive"
    assert ability_kv._kind("DOTA_ABILITY_BEHAVIOR_NOT_LEARNABLE") == ""
    assert ability_kv._kind("DOTA_ABILITY_BEHAVIOR_NO_TARGET", innate=True) == "Active"


def test_removed_innate_without_an_icon_gets_the_fallback_directly():
    """14 removed innates (Aggrandize, Gift Bearer, Sight Seer…) had a 404 src that onerror swapped later."""
    from patch.elements import INNATE_ICON_URL
    from patch.cards_ability_change import ability_change
    from patch.images import _LOCAL_ABIL_ICONS
    assert "dark_seer_aggrandize" not in _LOCAL_ABIL_ICONS
    html = ability_change(old=dict(name="Aggrandize", slug="dark_seer_aggrandize", innate=True, desc=["Passive."]),
                          new=dict(name="Normal Punch", slug="dark_seer_normal_punch", innate=True, desc=["Passive."]))
    assert "dark_seer_aggrandize.png" not in html
    assert INNATE_ICON_URL in html


def test_innate_row_under_its_card_is_hidden():
    _State.card_innate = "Poison Sting"
    try:
        row = el.li("Poison Sting is now an innate ability (previously a basic ability)", "")
        assert "iab-covered" in row
        row = el.li("Silent as the Grave is now an innate ability (previously granted by Aghanim's Scepter)", "")
        assert "iab-covered" not in row
    finally:
        _State.card_innate = None


def test_a_renamed_ability_shows_old_arrow_new_in_its_header():
    html = el.ability("Summon Razorback", slug="beastmaster_summon_razorback", old_title="Call of the Wild Boar")
    assert ('<span class="ability-title-old">Call of the Wild Boar</span><span class="ability-title-arrow">→</span>'
            '<span class="ability-title-new">Summon Razorback</span>') in html


def test_sub_ability_shows_the_ability_icon_and_name():
    html = el.sub_ability("rattletrap_jetpack", "Jetpack")
    assert 'src="../icons/abilities/rattletrap_jetpack.png"' in html and ">Jetpack</b>" in html


def test_game_checked_move_overrides_the_text_guess():
    # Rubick 7.41: the notes never say where Telekinesis Landing Damage went; the game files put it on Level 20
    from patch import talent_marks as tm
    from patch.state import _State
    tm._content_file = lambda: "w"
    tm._cache["w"] = {}
    _State.current_patch_version = "7.41"
    try:
        fate = tm.mark("Level 10 Talent: +165 Telekinesis Landing Damage replaced with -2s Telekinesis Cooldown", "Rubick")
        # "10 → 20" in the Level column, the new level coloured (2026-11-07)
        assert fate[0] == "moved" and '<span class="tm-c">10 → ' in fate[2] and ">20</span>" in fate[2]
    finally:
        del tm._content_file
        import importlib
        importlib.reload(tm)


def test_no_summary_names_the_replaced_ability():
    # Beastmaster 7.41 "Inner Beast is now the innate ability (replaces Rugged)."
    bad = []
    for f in sorted((ROOT / "content").glob("p*.py")):
        for node, _ in _calls(f, "ability_change"):
            s = _kw(node, "summary")
            if isinstance(s, ast.Constant) and ("replaces" in s.value or "removed;" in s.value):
                bad.append(f"{f.name}:{node.lineno} {s.value}")
    assert not bad, bad


def test_no_rename_row_under_an_arrow_header():
    # Dark Seer 7.41 "Aggrandize renamed to Quick Wit" under the Aggrandize -> Quick Wit card
    bad = []
    for f in sorted((ROOT / "content").glob("p*.py")):
        for node, lines in _calls(f, "ability_change"):
            old, new = _name(_kw(node, "old")), _name(_kw(node, "new"))
            if old and new and old != new:
                bad += [f"{f.name}: {r.strip()}" for r in _rows_after(node, lines) if "renamed to" in r]
        for node, lines in _calls(f, "ability"):
            if _kw(node, "old_title") is not None:
                bad += [f"{f.name}: {r.strip()}" for r in _rows_after(node, lines) if "renamed to" in r]
        # a renamed item gets the arrow too (owner 2026-10-22, Blight Stone -> Orb of Blight 7.38)
        for node, lines in _calls(f, "item_header"):
            name = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) else None
            bad += [f"{f.name}: {r.strip()}" for r in _rows_after(node, lines) if name and f"renamed to {name}" in r]
    assert not bad, bad
