"""Guards facets and talents in hero blocks: lost facets, facet cards and rows, talent swaps.
"""

import glob
import importlib
import os
import pathlib
import pytest
import tools.generate_patch_code_v2 as g
from patch import ability_kv, cards_facets, elements, elements as el
from patch.api import facet_group
from patch.state import _State, reset_page_state

ROOT = pathlib.Path(__file__).resolve().parents[1]
NEW = ('<div class="ability-block facet-block"><h4 class="ability-title">{}</h4><ul class="changes ability-change-summary-ul">'
       '<li data-tag="new">New facet</li></ul><div class="ability-change unified-panes is-single-new" data-tag="new">'
       '<div class="ability-change-pane ability-change-new"><div class="ability-change-body"><div class="ability-change-row">'
       'Text</div></div></div></div></div>')


# ---- second review of 2026-11-08 (audit before 7.42) ----

def _page(v):
    html = ROOT / "dist" / "patches" / f"{v}.html"
    if not html.exists():
        pytest.skip("no build")
    return html.read_text(encoding="utf-8")


_ROOT_738 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _p738():
    with open(os.path.join(_ROOT_738, "content", "p738.py"), encoding="utf-8") as f:
        return f.read()


import sys  # noqa: E402
sys.path.insert(0, os.path.join(_ROOT_738, "tools"))       # the file alone finds the generator too, not only in a full run
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


def test_a_removed_ability_with_its_icon_and_a_reworked_facet_ability_as_a_card():
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    # Eject: Dismember's hidden sub-ability, its "Removed Aghanim's Shard." says it (owner 2026-11-06)
    assert 'W(ability("Eject"' not in text and "Removed Eject ability" not in text
    assert (ROOT / "icons" / "abilities" / "pudge_eject.png").exists()      # from Valve's CDN (fetch_icons.py)
    assert 'game_ability_pair("faceless_void_time_zone", "7.38")' in text
    for name, slug in (("Bad Juju", "dazzle_bad_juju"), ("Parting Shot", "muerta_parting_shot")):
        assert f'W(ability("{name}", slug="{slug}"))' in text and f"Removed {name} ability" not in text


def test_facet_cards_say_their_kind_and_keep_attribute_rows_out():
    from patch.number_tips import _facet_attr_rows
    from patch.cards_item_abilities import _pane_parts
    keep, rows = _facet_attr_rows(["Number of times +2 All Attributes can be skilled decreased from 7 to 6 <b>x</b>",
                                      "Increases the max level of Void to 5"])
    assert keep == ["Increases the max level of Void to 5"] and "Number of times +2 All Attributes" in rows
    h = _pane_parts(["Grants Chicken Fingers ability", "Passive. Attacking an enemy hero transforms them."], facet=True)[0]
    assert '<b class="iab-kind">Passive:</b> <span class="iab-name">Chicken Fingers</span>' in h
    text = (ROOT / "patch" / "cards_facets.py").read_text(encoding="utf-8")
    assert 'unified-panes is-in-place" data-tag="new del rework">\'\n        f\'<div class="ability-change-pane ability-change-old">\'\n        f\'{_ability_head' not in text


def test_a_facets_rows_go_in_the_heros_order_each_ability_with_its_aghanims_rows():
    # owner 2026-11-06, 7.38 Invoker's facets: "Active: Wex/Exort/Quas ставить в начале списка", "небольшой отступ
    # внутри карточки перед каждой способностью"; Tornado's Scepter row stood under Alacrity's head
    from patch.cards_item_abilities import _pane_parts
    from patch.state import _State
    keep = (_State.current_hero, _State.current_patch_version)
    _State.current_hero, _State.current_patch_version = "invoker", "7.38"
    try:
        _, body = _pane_parts(["E.M.P.: Can be upgraded with Aghanim's Shard. Increases Burn Damage",
                               "Wex: When Invoker reaches level 6, he gains a bonus level of Wex",
                               "Wex: Aghanim's Scepter grants 1 additional current level",
                               "Alacrity: Grants bonus attack range",
                               "Tornado: Can be upgraded with Aghanim's Scepter. Tornado creates smaller twisters"],
                              facet=True)
    finally:
        _State.current_hero, _State.current_patch_version = keep
    order = [body.index(w) for w in ("bonus level of Wex", "additional current", "Grants bonus attack range",
                                     "creates smaller", "Increases Burn")]
    # the orb with its Scepter row, then what the facet improves, then Scepter, then Shard (owner 2026-11-06: three
    # facets side by side say the same thing on one line)
    assert order == sorted(order)
    from patch.card_sections import card_sections
    out = card_sections('<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
                        + body + "</div></div>", "7.38")
    # an Aghanim's row of another ability gets its own head, the stripe kept on its row
    assert '<span class="iab-name">Tornado</span>' in out and '<span class="iab-name">E.M.P.</span>' in out
    assert out.count('<span class="iab-name">Wex</span>') == 1        # Wex's Scepter row stays under Wex's head
    assert 'class="ability-change-row acr-sec acr-sec-headed"' in out
    from patch.css_bundle import read_css
    css = read_css()
    assert ".ability-change-row.acr-sec-headed { margin-top: 8px; }" in css
    # the head right on its Aghanim's row, no room or line between them ("шапка идёт отдельно от способности")
    assert 'acr-sec-headed acr-sec-only"><div class="iab-head acr-sec-head">' in out
    assert ".ability-change-row.acr-sec.acr-sec-only + .ability-change-row { border-top: 0; }" in css
    assert ".ability-change-row.acr-sec-only > .acr-sec-head { margin-bottom: 0; }" in css
    # ... over the rows' gap, folded or not; every Aghanim's row edge to edge (Quas' Scepter row had a gap on its right)
    assert ".ability-change-row.acr-sec-only { padding-bottom: 0; margin-bottom: -4px; }" in css
    assert ".acr-fold-body { display: flex; flex-direction: column; gap: 4px;" in css
    assert out.count("acr-wide") == out.count("acr-aghs") > 0


def test_a_lost_facet_and_the_new_one_stand_side_by_side():
    # owner 2026-11-06: "просто поставить слева «аспект удалён», а справа уже добавить новый" (7.38 Meepo, PA)
    from patch.card_pairs import pair_replaced_facets
    gone = ('<div class="ability-block facet-block"><h4 class="ability-title">Pack Rat</h4>\n<ul class="changes">\n'
            '<li data-tag="del nerf"><span class="badge del" data-tag="del" data-overall="nerf">DEL</span>'
            '<span class="row-text">Removed</span></li>\n</ul>\n</div>')
    other = ('<div class="ability-block facet-block"><h4 class="ability-title">More Meepo</h4><ul class="changes">'
             '<li data-tag="nerf">Row</li></ul></div>')
    new = NEW.format("Codependent").replace('<li data-tag="new">New facet</li>',
                                            '<li data-tag="new"><span class="row-text">New facet</span></li>')
    html = '<div class="entity-block">' + gone + other + new + "</div>"
    out = pair_replaced_facets(html, "7.38")
    # the new one first ("меняй местами новый и удалённый … в новом информация")
    assert out.index('<div class="card-pair facet-swap">') < out.index("Codependent") < out.index("Pack Rat") < out.index("More Meepo")
    two_new = html.replace(other, new.replace("Codependent", "Other"))
    assert pair_replaced_facets(two_new, "7.38") == two_new                 # two new facets: no swap pair


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


def test_a_facet_text_of_one_string_stays_one_text():
    # "карточки сломались?" — 7.39 Malignant Mist's card showed one row per letter
    from patch.number_tips import _facet_attr_rows
    assert _facet_attr_rows("Mist Coil also deals 40% attack damage") == ("Mist Coil also deals 40% attack damage", "")
    html = (ROOT / "dist" / "patches" / "7.39.html")
    if html.exists():
        assert '<div class="ability-change-row">M</div><div class="ability-change-row">i</div>' not in html.read_text(
            encoding="utf-8")


def test_no_line_from_a_facet_to_its_orbs_spells():
    # 7.40 Mind of Tornarus joined to Alacrity: "почему тут стрелочкой соединен"
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    body = js[js.index("function drawAbilityTreeIn"):]
    assert "if (parentImg.closest('.facet-icon-wrap')) return;" in body[:body.index("const childImgs")]


# ---- third review of 2026-11-08 ----

def test_talents_of_no_facet_go_under_the_facets_talents():
    # 7.38 Wraith King: "+40% Cleave replaced with +60 Attack Speed ... выбивается, т.к он не относится к аспектам"
    text = _page("7.38")
    assert text.index("+40% Cleave") > text.index("+5 Bone Guard Skeletons Spawned")


def test_a_removed_facet_with_a_note_pairs_with_the_new_one():
    # 7.38 Spirit Breaker: Imbalanced "Removed [?]" beside Bull's Hit
    text = _page("7.38")
    i = text.index("Imbalanced</h4>")
    k = text.rfind('<div class="card-pair facet-swap">', 0, i)
    assert k > 0 and "Hit</h4>" in text[k:i]


def test_a_new_facet_row_becomes_the_new_facet_card():
    lines = ['W(facet_header("medusa_slow_attacks"))', 'W(ul_open())', 'W(li("New Facet", t("NEW")))',
             'W(li("Medusa applies a poison to every fifth attack", t("MISC")))', 'W(ul_close())']
    assert g._postprocess_new_facet_rows(lines) == [
        'W(new_facet("medusa_slow_attacks", desc=["Medusa applies a poison to every fifth attack"]))']


def test_a_reworked_facets_old_pane_is_its_text_of_the_patch_before():
    """7.37 Ferocity / Voidblades: the card's old side said "TODO" — the visual check saw it on the page. The facet's
    text of 7.36c with its number ({s:bonus_roared_bonus_aoe_pct} = 10)."""
    from patch.aghs_text import facet_text
    assert facet_text("primal_beast_ferocity", "7.36c") == \
        "When activated, Uproar provides 10% increased area of effect per stack."
    card = "\n".join(g._facet_card("primal_beast_ferocity", "hero_facet ReworkedFacet",
                                   ['W(li("Pulverize: Now provides 20% AoE increase", t("NEW")))'], "7.37"))
    assert "TODO" not in card and "Uproar provides 10% increased area" in card


def test_no_page_keeps_the_old_facet_placeholder():
    from pathlib import Path
    pages = Path(__file__).resolve().parents[1].glob("content/p*.py")
    left = [p.name for p in pages if "TODO: the facet as it was in the previous patch" in p.read_text(encoding="utf-8")]
    assert left == []


def test_removed_facets_are_facet_blocks_and_a_removed_innate_is_its_own_block():
    """Owner 2026-10-29 (7.38 Invoker, "где картинки фасетов? Mastermind вообще innate"): each removed facet is its own
    block (icon, name, "Removed" row) before the hero's new facets, as 7.39 does; a removed innate is its block first in
    Abilities; a GENERAL list left empty goes. Names from the game files of 7.37e."""
    ul = ['W(ul_open())', 'W(li("Removed", t("DEL")))', 'W(ul_close())']
    lines = [
        'W(hero_header("Invoker"))', 'W(ul_open())', 'W(li("Base Intelligence increased from 19 to 20", b(19, 20)))',
        'W(li("Removed Mastermind ability", t("DEL")))', 'W(li("Removed Agnostic and Elitist Facets", t("DEL")))',
        'W(ul_close())', 'W(new_facet("invoker_quas_focus", desc=[]))', 'W(ability("Quas", slug="invoker_quas"))',
        'W(hero_header("Chaos Knight"))', 'W(ul_open())', 'W(li("Removed Phantasmagoria Facet", t("DEL")))',
        'W(ul_close())', 'W(ability("Chaos Bolt", slug="chaos_knight_chaos_bolt"))',
    ]
    out = g._postprocess_removed_facets(lines, "7.38")
    assert out == [
        'W(hero_header("Invoker"))', 'W(ul_open())', 'W(li("Base Intelligence increased from 19 to 20", b(19, 20)))',
        'W(ul_close())', 'W(facet_header("invoker_agnostic"))', *ul, 'W(facet_header("invoker_elitist"))', *ul,
        'W(new_facet("invoker_quas_focus", desc=[]))',
        'W(ability("Mastermind", slug="invoker_mastermind", innate=True))', *ul,
        'W(ability("Quas", slug="invoker_quas"))',
        # a facet that grants an ability is named by it: Phantasmagoria = chaos_knight_strong_illusions
        'W(hero_header("Chaos Knight"))', 'W(facet_header("chaos_knight_strong_illusions"))', *ul,
        'W(ability("Chaos Bolt", slug="chaos_knight_chaos_bolt"))',
    ]


def test_a_hero_has_his_facets_then_his_abilities_on_every_page():
    # owner 2026-11-02, 7.38 Morphling: "сначала способность, потом фасеты, потом опять способности. Это неправильно"
    for path in glob.glob(os.path.join(_ROOT_738, "content", "p7*.py")):
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        assert g._postprocess_facets_first(lines) == lines, path


def test_the_generator_writes_a_heroes_facets_before_his_innate_block():
    src = g.generate("7.38")
    morphling = src[src.index('hero_header("Morphling")'):]
    assert morphling.index('facet_header("morphling_agi")') < morphling.index('ability("Accumulation"')


def test_facets_first_keeps_the_rest_in_order_and_leaves_owned_abilities_alone():
    lines = ['W(hero_header("X"))', 'W(ul_open())', 'W(ul_close())', 'W(ability("Innate", slug="x_i", innate=True))', 'W(ul_open())',
             'W(ul_close())', 'W(facet_header("x_f"))', 'W(ul_open())', 'W(ul_close())', 'W(ability("Q", slug="x_q"))',
             'W(subgroup("Talents"))', '# Y', 'W(hero_header("Y"))']
    out = g._postprocess_facets_first(lines)
    order = [ln for ln in out if "facet_header" in ln or "W(ability" in ln]
    assert order == ['W(facet_header("x_f"))', 'W(ability("Innate", slug="x_i", innate=True))', 'W(ability("Q", slug="x_q"))']
    assert out[-3:] == lines[-3:]
    owned = ['W(hero_header("I"))', 'W(ability("Q", slug="q", sub=True))', 'W(facet_header("f"))', 'W(hero_header("J"))']
    assert g._postprocess_facets_first(owned) == owned


def test_a_facet_improving_an_ability_is_one_row():
    lines = ['W(li("Now is a facet that improves Succubus", t("NEW")))',
             'W(li("Succubus: Now also makes Spell Lifesteal apply", t("MISC"), extra=inline_note("x")))']
    assert g._postprocess_facet_improves_row(lines) == [
        'W(li("Now is a facet that improves Succubus: also makes Spell Lifesteal apply", t("NEW"), extra=inline_note("x")))']
    assert "Now is a facet that improves Succubus: also makes" in _p738()


def test_two_lost_facets_become_one_block_where_the_first_stood():
    out = post_facets._postprocess_removed_facet_groups(
        _hero_lines(*_removed("a_one"), 'W(new_facet("a_new", desc=[]))', *_removed("a_two")))
    assert out == _hero_lines('W(facet_group("a_one", "a_two"))', 'W(ul_open())', 'W(li("Removed", t("DEL")))', 'W(ul_close())',
                              'W(new_facet("a_new", desc=[]))')


def test_the_note_of_one_lost_facet_stays_on_the_shared_row():
    note = ', extra=inline_note("Rage remains")'
    out = post_facets._postprocess_removed_facet_groups(_hero_lines(*_removed("a_one"), *_removed("a_two", note)))
    assert f'W(li("Removed", t("DEL"){note}))' in out and sum("facet_group" in x for x in out) == 1


def test_two_notes_do_not_fit_one_row_and_one_lost_facet_has_nothing_to_join():
    note = ', extra=inline_note("x")'
    two_notes = _hero_lines(*_removed("a_one", note), *_removed("a_two", note))
    assert post_facets._postprocess_removed_facet_groups(two_notes) == two_notes
    single = _hero_lines(*_removed("a_one"))
    assert post_facets._postprocess_removed_facet_groups(single) == single


def test_the_group_draws_each_facet_on_its_colour_with_one_title(page):
    elements.hero_header("Arc Warden")
    html = facet_group("arc_warden_order", "arc_warden_disorder")
    assert 'class="ability-block facet-block has-icon-stack"' in html
    assert '<h4 class="ability-title">Order, Disorder</h4>' in html
    assert html.count('class="stack-facet-tile" style="background-image:') == 2
    assert 'aria-label="Order"' in html and 'aria-label="Disorder"' in html
    assert html.count('<h4 class="subgroup">Facets</h4>') == 1


def test_the_group_needs_two_facets_and_says_which_it_does_not_know(page):
    elements.hero_header("Arc Warden")
    assert "unknown slugs ['no_such_facet']" in facet_group("arc_warden_order", "no_such_facet")
    with pytest.raises(ValueError):
        facet_group("arc_warden_order")


def test_every_lost_facet_of_the_built_pages_was_found():
    for version in ("7.38", "7.39", "7.40"):
        built = ROOT / "dist" / "patches" / f"{version}.html"
        if built.exists():
            assert "facet_group: unknown" not in built.read_text(encoding="utf-8"), version


def test_an_innates_chip_in_a_facets_row_has_the_innate_mark(page):
    elements.hero_header("Nature's Prophet")
    elements.facet_header("furion_ironwood_treant")
    row = elements.li("Spirit of the Forest: Treant Multiplier rescaled from x2/x3/x4/x5/x6 to x4",
                      '<span class="badge del" data-tag="del">DEL</span>')
    assert 'aria-label="Spirit of the Forest"' in row and 'class="chip-innate-marker"' in row
    assert "Spirit of the Forest:" not in row


def test_an_innate_without_art_has_the_generic_icon_in_a_facets_row(page, monkeypatch):
    monkeypatch.setattr(elements, "_LOCAL_ABIL_ICONS", set())
    elements.hero_header("Nature's Prophet")
    elements.facet_header("furion_ironwood_treant")
    row = elements.li("Spirit of the Forest: Treant Multiplier", '<span class="badge del" data-tag="del">DEL</span>')
    assert f'<img src="{elements.INNATE_ICON_URL}"' in row and "Spirit of the Forest:" not in row


def test_a_facet_card_takes_the_kind_of_the_ability_it_changes(monkeypatch):
    blocks = {"disruptor_electromagnetic_repulsion": {"Innate": "1", "AbilityBehavior": "DOTA_ABILITY_BEHAVIOR_NOT_LEARNABLE",
                                                      "AbilityValues": {"x": {"special_bonus_facet_disruptor_conduit": "1"}}},
              "disruptor_thunder_strike": {"AbilityBehavior": "DOTA_ABILITY_BEHAVIOR_UNIT_TARGET"}}
    monkeypatch.setattr(ability_kv, "_hero_blocks", lambda v: blocks)
    assert ability_kv.facet_ability("disruptor_conduit", "7.39") == "disruptor_electromagnetic_repulsion"
    monkeypatch.setattr("patch.aghs_text.ability_name", lambda s, v: "Electromagnetic Repulsion")
    head, _ = cards_facets._facet_pane(["Increases the max level of Electromagnetic Repulsion to 4."], "disruptor_conduit",
                                   "7.39")
    # the kind and the name of the ability the facet changes (owner 2026-10-27, Old Blood: "Active: Bloodrage")
    assert '<b class="iab-kind">Passive:</b> <span class="iab-name">Electromagnetic Repulsion</span>' in head
    # the text's own kind wins
    head, _ = cards_facets._facet_pane(["Active. Pushes enemies away."], "disruptor_conduit", "7.39")
    assert '<b class="iab-kind">Active:</b>' in head and "Passive" not in head


def test_talent_swap_marks_removed_new_and_moved_talents():
    # Batrider 7.41: Smoldering Resin moved L20 +4s -> L10 +1s; the rest are removed / brand-new talents
    from patch import talent_marks as tm
    swaps = [(10, "+50 Flamebreak Knockback Distance", "+1s Smoldering Resin Duration"),
             (20, "+4s Smoldering Resin Duration", "Attacks apply 1 Stack of Sticky Napalm")]
    tm._cache["x"] = {"Batrider": swaps}
    tm._content_file = lambda: "x"
    try:
        assert tm.mark("Level 10 Talent: +50 Flamebreak Knockback Distance replaced with +1s Smoldering Resin Duration",
                       "Batrider")[:2] == ("gone", "moved")
        assert tm.mark("Level 20 Talent: +4s Smoldering Resin Duration replaced with Attacks apply 1 Stack of Sticky Napalm",
                       "Batrider")[:2] == ("moved", "fresh")
    finally:
        del tm._content_file
        import importlib
        importlib.reload(tm)


def test_a_brand_new_talent_is_gold_but_the_row_stays_swap():
    # as NEW the swap scored as a buff: 7.38's net went +54 -> +86
    from patch import talent_marks as tm
    from patch.badges import t
    from patch.state import _State
    tm._content_file = lambda: "z"
    tm._cache["z"] = {"Batrider": [(15, "+20 Movement Speed", "+30 Firefly Damage Per Second")]}
    _State.current_hero_title = "Batrider"
    try:
        text, badge, _ = el._mark_talent_swap("Level 15 Talent: +20 Movement Speed replaced with +30 Firefly Damage Per Second",
                                              t("SWAP"), "")
        assert 'iab-hl-new' in text and 'iab-hl-del' in text and 'data-tag="swap"' in badge
    finally:
        del tm._content_file
        import importlib
        importlib.reload(tm)


def test_same_talent_in_another_form_is_neither_removed_nor_new():
    # Arc Warden 7.41 "+50% Spark Wraith Damage -> +200 Spark Wraith Damage", Viper "+30 -> +20/40 Nethertoxin"
    from patch import talent_marks as tm
    tm._content_file = lambda: "y"
    tm._cache["y"] = {}
    try:
        assert tm.mark("Level 15 Talent: +30 Nethertoxin Min/Max Damage replaced with +20/40 Nethertoxin Min/Max Damage",
                       "Viper") == ("same", "same", "")
    finally:
        del tm._content_file
        import importlib
        importlib.reload(tm)


def test_plural_talent_is_the_same_talent():
    from patch import talent_marks as tm
    assert tm.key("+1 Acorn Shot Bounce") == tm.key("+2 Acorn Shot Bounces")


def test_facet_named_talent_row_is_a_swap():
    from patch import talent_marks as tm
    assert tm.SWAP_RE.match("Old Blood: Level 10 Talent +15% Bloodrage Spell Amplification replaced with +15% Amp")


def test_a_renamed_facet_shows_old_to_new_in_its_header():
    """7.37 Corpse Eater -> Rage: "мы обычно убираем такие строки и делаем стрелочку от названия"."""
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
    from patchgen.post_facets import _postprocess_renamed_facets
    lines = ['    W(facet_header("life_stealer_rage"))', "    W(ul_open())",
             '    W(li("Renamed from Corpse Eater to Rage", t("MISC")))', '    W(li("No longer gains HP", t("MISC")))']
    assert _postprocess_renamed_facets(lines) == ['    W(facet_header("life_stealer_rage", old_title="Corpse Eater"))',
                                                  "    W(ul_open())", '    W(li("No longer gains HP", t("MISC")))']
    from patch.elements import facet_header
    from patch.state import _State
    _State.current_hero = None
    html = facet_header("life_stealer_rage", old_title="Corpse Eater")
    assert '<span class="ability-title-old">Corpse Eater</span><span class="ability-title-arrow">→</span>' in html
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content", "p737.py"),
               encoding="utf-8").read()
    assert "Renamed from" not in src
