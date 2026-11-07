"""The owner's decisions of 2026-11-05 on the undecided rows of 7.38: tags, lost facets in one block, an innate's icon in a
facet's row, Pirate Hat's card, the page's search finding what a row names only by its icon."""
import importlib
import pathlib
import re
import sys

import pytest

from patch import elements, item_ability_text
from patch.api import facet_group
from patch.mech_abilities import ability_chip
from patch.state import _State, reset_page_state

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
tags = importlib.import_module("patchgen.tags")
rows = importlib.import_module("patchgen.rows")
post_cards = importlib.import_module("patchgen.post_cards")
post_facets = importlib.import_module("patchgen.post_facets")


@pytest.mark.parametrize("text, tag", [
    ("Death Pact: Now can be cast while rooted or leashed, but without teleporting Clinkz to the target location", "NEW"),
    ("Can now be cast while rooted, but will not knock Sniper back if he is under the effect of root", "NEW"),
    ("Release sub-ability can now be cast while silenced", "NEW"),
    ("Return Astral Spirit and Move Astral Spirit sub-abilities can now be used while Elder Titan is disabled", "NEW"),
    ("Death Pact: Added alt-cast mode which disables teleportation", "QoL"),
    ("Neutrals will autocast this ability only if the Ancient Prowler Shaman has less than 90% health at the start of the attack", "MISC"),
    ("Neutrals will cast this ability on a random ally that is below 50% health", "MISC"),   # owner 2026-11-06
    ("Now is a Point Targeted ability with 900 cast range", "REWORK"),
    ("Arena Of Blood: Now provides 50% of the bonuses to all allies that are in the arena when an enemy dies inside of it", "NEW"),
    ("Sprout: Allied Tangos provide double the heal duration when consuming a tree created by Sprout", "NEW"),
    ("Exorcism: If a hero dies during Exorcism, their spirit is now added to both the current Exorcism, and as a charge for the next one", "NEW"),
    ("No longer disabled by Silence", "NEW"),
    # toggles keep the owner's older decision (2026-09-27)
    ("Toggling is no longer disabled by silence", "MISC"),
    ("Now can be toggled while silenced", "MISC"),
    ("Can no longer be disabled by Silence", "NEW"),
    # the other half of the old rule stays: nothing changed for these
    ("Can no longer be cast while rooted", "DEL"),
    ("Can now be cast without a target", "BUFF"),
])
def test_the_owners_tag_for_a_row(text, tag):
    assert tags._guess_tag(text) == tag


@pytest.mark.parametrize("text", [
    "Aghanim's Shard now increases Summon Duration by 5s (from 25s to 30s)",
    "Aghanim's Shard now increases damage by 20% (from 80/160/240/320 to 96/192/288/384)",
    "Aghanim's Scepter now increases movement speed slow by 20% (from 30/40/50% to 50/60/70%)",
])
def test_a_new_property_of_an_upgrade_is_new_without_a_percent(text):
    assert tags._guess_tag(text) == "NEW"
    assert rows._NEW_UPGRADE_RE.search(text)


def test_a_multiplier_with_x_is_read_as_numbers():
    badge = rows._emit_badge("Treant Multiplier rescaled from x2/x3/x4/x5/x6 to x4")
    assert badge == "b([2, 3, 4, 5, 6], 4)"


def _hero_lines(*body):
    return ['W(hero_header("Arc Warden"))', *body, 'W(ability("Flux", slug="arc_warden_flux"))']


def _removed(slug, note=""):
    return [f'W(facet_header("{slug}"))', 'W(ul_open())', f'W(li("Removed", t("DEL"){note}))', 'W(ul_close())']


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


def test_two_heroes_are_not_mixed():
    lines = _hero_lines(*_removed("a_one")) + ['W(hero_header("Axe"))', *_removed("b_one")]
    assert post_facets._postprocess_removed_facet_groups(lines) == lines


@pytest.fixture
def page():
    reset_page_state()
    _State.current_patch_version = "7.38"
    yield
    reset_page_state()


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


def test_one_block_weighs_as_much_as_the_separate_ones(page):
    apart = _balance(("arc_warden_order", "arc_warden_disorder"))
    reset_page_state()
    _State.current_patch_version = "7.38"
    together = _balance("arc_warden_order", "arc_warden_disorder")
    assert together == apart


def test_an_innates_chip_in_a_facets_row_has_the_innate_mark(page):
    elements.hero_header("Nature's Prophet")
    elements.facet_header("furion_ironwood_treant")
    row = elements.li("Spirit of the Forest: Treant Multiplier rescaled from x2/x3/x4/x5/x6 to x4",
                      '<span class="badge del" data-tag="del">DEL</span>')
    assert 'aria-label="Spirit of the Forest"' in row and 'class="chip-innate-marker"' in row
    assert "Spirit of the Forest:" not in row


def test_a_basic_abilitys_chip_and_the_generic_icon_have_no_mark():
    assert "chip-innate-marker" not in ability_chip("Defense Matrix", "x/tinker_defense_matrix.png")
    assert "chip-innate-marker" not in ability_chip("Something", elements.INNATE_ICON_URL)


def test_an_innate_without_art_has_the_generic_icon_in_a_facets_row(page, monkeypatch):
    monkeypatch.setattr(elements, "_LOCAL_ABIL_ICONS", set())
    elements.hero_header("Nature's Prophet")
    elements.facet_header("furion_ironwood_treant")
    row = elements.li("Spirit of the Forest: Treant Multiplier", '<span class="badge del" data-tag="del">DEL</span>')
    assert f'<img src="{elements.INNATE_ICON_URL}"' in row and "Spirit of the Forest:" not in row


def test_a_tooltip_may_name_the_blocks_channel_time():
    assert item_ability_text._values({"AbilityChannelTime": "1"})["abilitychanneltime"] == "1"
    assert item_ability_text._fill("Channel for %abilitychanneltime% second.", {"abilitychanneltime": "1"}) == "Channel for 1 second."


def test_the_card_takes_over_the_rows_of_a_brand_new_ability():
    names = {"plunder"}
    assert item_ability_text._restates('W(li("Passive: Plunder. Steals 150 gold from heroes", t("NEW")))', names)
    assert not item_ability_text._restates('W(li("Passive: Dig. Finds a rune", t("DEL")))', names)
    assert not item_ability_text._restates('W(li("Now a Tier 5 Artifact", t("REWORK")))', names)


def test_pirate_hat_is_reworked_with_a_card_and_a_row():
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    block = text[text.index('W(item_header("Pirate Hat"'):text.index('W(item_header("Spider Legs"')]
    assert 'changed="Reworked Tier 5 Artifact"' in block and "Active: Dig." in block and "Passive: Plunder." in block
    assert "W(li(" not in block


def test_the_generator_writes_pirate_hats_header_itself():
    src = (ROOT / "tools" / "patchgen" / "entities.py").read_text(encoding="utf-8")
    assert """changed="Reworked {tier.group(1)} Artifact\"""" in src


def test_scaling_reworked_says_no_more():
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    # the generator's scaling_rework() says "Scaling reworked" itself (owner 2026-11-06)
    assert text.count("W(scaling_rework(") == 2 and "number of deaths &rarr; game time" not in text
    from patch.scaling_card import scaling_rework
    assert "Scaling reworked</span>" in scaling_rework("R", "x.png", "a", "b", [("Damage", "1 + (2 per death)", "1 + (2 per minute)")])


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


def test_a_new_items_price_stands_on_its_icon():
    reset_page_state()
    _State.current_patch_version = "7.38"
    html = elements.item_header("Orb of Frost", new="New Basic Equipment Item", cost=250)
    reset_page_state()
    icon = html[html.index('class="entity-icon'):html.index('class="entity-name"')]
    assert '<span class="item-icon-cost" aria-label="Cost 250">250</span>' in icon


def test_the_generator_writes_the_price_into_the_header():
    from patch.api import components
    assert components                                                      # priced by parts: that stays under the header
    post_items = importlib.import_module("patchgen.post_items")
    lines = ['W(item_header("Shawl", new="New Miscellaneous Item"))', 'W(ul_open())',
             'W(li("Costs 450 gold", t("MISC")))', 'W(li("Passive: Warm. Keeps you warm", t("MISC")))', 'W(ul_close())']
    out = post_items._postprocess_new_item_card(lines)
    assert out[0] == 'W(item_header("Shawl", new="New Miscellaneous Item", cost=450))'
    assert not any("Costs 450" in ln for ln in out)


def test_the_old_price_box_is_gone_everywhere():
    assert not hasattr(elements, "item_cost")
    for folder, pattern in (("content", "p*.py"), ("src/css", "*.css"), ("tools/patchgen", "*.py")):
        for found in (ROOT / folder).glob(pattern):
            text = found.read_text(encoding="utf-8")
            assert "item-cost-box" not in text and "W(item_cost(" not in text, found.name


def test_an_items_page_keeps_the_price_beside_the_patchs_label():
    src = (ROOT / "builders" / "entity_changes.py").read_text(encoding="utf-8")
    assert "item-icon-cost" in src


def test_the_innate_mark_stays_on_the_grown_icon():
    css = (ROOT / "src" / "css" / "patch-new-entity-rows.css").read_text(encoding="utf-8")
    rule = css[css.index(".ability-chip:hover > .chip-innate-marker {"):]
    rule = rule[:rule.index("}")]
    assert "display: none" not in rule and "scale(2)" in rule


def test_the_search_knows_facets_and_abilities_a_row_names_by_its_icon():
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert ".ability-chip[aria-label], .facet-chip[aria-label]" in js      # 7.38 Exorcism has rows and no block
    assert "kind: isFacet ? 'facet' : 'ability'" in js                     # 7.38 Ebb read "ability"
    assert 'class="result-facet"' in js                                    # ... with an empty picture
    assert ".stack-icon" in js                                             # each of a block's icons by its own name


def test_two_selves_card_shows_each_self_before_and_their_one_line_after(page):
    from patch.api import two_selves_change
    elements.hero_header("Arc Warden")
    html = two_selves_change("Flux", "arc_warden_flux", old_desc="Old text.", hero="15 damage", double="20 damage",
                             new_desc="New text.", both="15 damage, 14% slow")
    assert "Now has the same effect for both Arc Warden and Tempest Double" in html and 'data-tag="rework"' in html
    assert html.count('aria-label="Arc Warden"') == 2 and html.count('aria-label="Tempest Double"') == 2
    assert "Disorder facet" in html
    plain = re.sub(r"<[^>]+>", "", html)
    assert plain.index("20 damage") < plain.index("New text.") < plain.index("15 damage, 14% slow")


def test_arc_wardens_three_abilities_are_cards_on_the_page():
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    for name in ("Flux", "Magnetic Field", "Spark Wraith"):
        assert f'W(two_selves_change("{name}", ' in text and f'W(ability("{name}", slug="arc_warden_' not in text
    assert "Now has the same effect for both" not in text


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


def test_the_rows_come_before_the_caption_and_the_card(page):
    from patch.api import ability_change, li, t
    elements.hero_header("Arc Warden")
    html = ability_change(old=dict(name="Flux", slug="arc_warden_flux", desc=["Old."]),
                          new=dict(name="Flux", slug="arc_warden_flux", desc=["New."]),
                          summary="Ability reworked", tag="rework",
                          rows_first=lambda: [li("First row", t("DEL")), li("Second row", t("NEW"))])
    assert html.index("First row") < html.index("Second row") < html.index("Ability reworked") < html.index('class="ability-change')
    assert "ROWSFIRST" not in html
    plain = ability_change(old=dict(name="Flux", slug="arc_warden_flux", desc=["Old."]),
                           new=dict(name="Flux", slug="arc_warden_flux", desc=["New."]), summary="Ability reworked", tag="rework")
    assert "ROWSFIRST" not in plain


def test_arc_wardens_rows_stand_above_their_cards():
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    block = text[text.index('W(hero_header("Arc Warden"))'):text.index('W(hero_header("Axe"))')]
    field = block[block.index('two_selves_change("Magnetic Field"'):block.index('two_selves_change("Spark Wraith"')]
    assert field.index("rows_first=lambda") < field.index("No longer upgraded with Aghanim's Shard") < field.index("Now is a Point Targeted")
    assert "W(li(" not in field
    double = block[block.index('game_ability_pair("arc_warden_tempest_double"'):block.index('W(subgroup("Talents"))')]
    assert "rows_first=lambda" in double and "W(li(" not in double


def test_without_the_games_text_the_row_stays(monkeypatch):
    from patch import aghs_text
    monkeypatch.setattr(aghs_text, "ability_text", lambda slug, version, kind="base": None)
    row = ('W(li("Now has the same effect for both Arc Warden and Tempest Double", t("REWORK"), extra=inline_note("Deals 15 '
           '<span class=\\"pop-note\\">(Previous values: Arc Warden: Deals 10. Tempest Double: Deals 20)</span>")))')
    lines = ['W(ability("Flux", slug="arc_warden_flux"))', 'W(ul_open())', row, 'W(ul_close())']
    assert post_cards._postprocess_two_selves_cards(lines, "7.38") == lines


def test_tempest_double_is_a_card_from_the_games_files(page):
    from patch.api import game_ability_pair
    old, new = game_ability_pair("arc_warden_tempest_double", "7.38")
    old_text, new_text = re.sub(r"<[^>]+>", "", " ".join(old)), re.sub(r"<[^>]+>", "", " ".join(new))
    assert "cooldown is restarted" in old_text and "cooldown is restarted" not in new_text
    assert "fractures over time" in new_text and "35%" in new_text and "too far away" in old_text
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert 'game_ability_pair("arc_warden_tempest_double", "7.38")' in text
    assert 'W(ability("Tempest Double", slug="arc_warden_tempest_double"))' not in text


def test_the_line_to_a_second_card_starts_under_the_first():
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    part = js[js.index("svg.under-rows-connector"):js.index("Two sides standing from one top edge")]
    assert "before.classList.contains('ability-change')" in part and "connectorPath(blockRect, start, paneRect)" in part


def test_a_self_table_keeps_the_same_columns_for_both_selves(page):
    from patch.api import two_selves_change
    elements.hero_header("Arc Warden")
    html = two_selves_change("Spark Wraith", "arc_warden_spark_wraith", old_desc="Old.", new_desc="New.",
                             columns=("Damage", "Speed"), hero=("100", "400"), double=("75", "725"), both=("90", "550"))
    assert html.count('class="selves-table"') == 2 and "--cols:2" in html
    assert html.count('class="selves-head"') == 4
    plain = re.sub(r"<[^>]+>", " ", html)
    assert plain.index("725") < plain.index("New.") < plain.index("550")


def test_a_dotted_number_stays_on_its_icons_centre():
    # 2026-11-06: measured by ink, the icon goes up 1px instead (Radiance's digits sit above their line's middle); the
    # 11-05 empty line over a dotted number pushed it 1px under the icon's centre once the icon moved
    css = (ROOT / "src" / "css" / "pixel-skin-filters.css").read_text(encoding="utf-8")
    assert "border-top: 1px solid transparent; }" not in css.split(".iab-hint {", 1)[1].split("/* ---- Silent", 1)[0]
    assert "display: block; position: relative; top: -1px; }" in css


def test_the_note_stands_in_the_doubles_last_cell(page):
    from patch.api import two_selves_change
    elements.hero_header("Arc Warden")
    html = two_selves_change("Spark Wraith", "arc_warden_spark_wraith", old_desc="Old.", new_desc="New.",
                             columns=("Damage", "Speed"), hero=("100", "400"), double=("75", "725"), both=("90", "550"))
    table = html[html.index('class="selves-table"'):html.index("New.")]
    assert table.index("725") < table.index("Disorder facet") < table.rindex("</span></span>")


def test_the_self_table_has_lines_and_centred_cells():
    css = (ROOT / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    rule = css[css.index(".selves-table > span {"):]
    rule = rule[:rule.index("}")]
    assert "justify-content: center" in rule and "border-left: 1px solid var(--line-soft)" in rule
    assert "border-top: 1px solid var(--line-soft)" in rule


def test_the_pass_moves_plain_rows_comments_and_formulas_above_the_card():
    lines = ['W(ability_change(', '    old=dict(name="A"), new=dict(name="A"),', '    summary="Ability reworked", tag="rework",', '))',
             'W(ul_open())', '# from the files', 'W(li("Cooldown decreased", b(5, 4, l=True)))  # a note',
             'W(li_formula("Damage rescaled", "1", "2", f, g))', "W(li(\"Aghanim's Shard: More\", t(\"NEW\")))", 'W(ul_close())']
    out = post_cards._postprocess_rows_first(lines)
    text = "\n".join(out)
    first = text[text.index("rows_first=lambda"):text.index("]))")]
    assert "# from the files" in first and 'li("Cooldown decreased", b(5, 4, l=True)),  # a note' in first
    assert 'li_formula("Damage rescaled", "1", "2", f, g),' in first and "Aghanim" not in first
    assert out[-3:] == ["W(ul_open())", "W(li(\"Aghanim's Shard: More\", t(\"NEW\")))", "W(ul_close())"]


def test_a_list_with_anything_else_stays_as_written():
    lines = ['W(ability_change(old=dict(name="A"), new=dict(name="A"), summary="x", tag="rework"))', 'W(ul_open())',
             '_pill = scale_pill("x")', 'W(li("Row", t("NEW")))', 'W(ul_close())']
    assert post_cards._postprocess_rows_first(lines) == lines
