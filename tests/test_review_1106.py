"""Owner's review of 2026-11-06: pairs of new cards, a bonus said in brackets, plain phrases in cards, runes as icons,
Arc Warden's two-selves columns and "Scaling reworked" in the generator."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

NEW = ('<div class="ability-block facet-block"><h4 class="ability-title">{}</h4><ul class="changes ability-change-summary-ul">'
       '<li data-tag="new">New facet</li></ul><div class="ability-change unified-panes is-single-new" data-tag="new">'
       '<div class="ability-change-pane ability-change-new"><div class="ability-change-body"><div class="ability-change-row">'
       'Text</div></div></div></div></div>')


def test_two_new_cards_in_a_row_stand_as_a_pair_and_three_in_one_line():
    from patch.card_pairs import pair_new_cards
    two = NEW.format("A") + "\n" + NEW.format("B")
    out = pair_new_cards(two, "7.38")
    assert out.count('<div class="card-pair">') == 1
    assert out.index('class="card-pair"') < out.index(">A<") < out.index(">B<")
    # every patch after the 7.38 trial (owner 2026-11-06: "Одиночные карточки для всех патчей включи")
    assert pair_new_cards(two, "7.41").count('<div class="card-pair">') == 1
    # exactly three: one line of three (owner 2026-11-06, 7.38 Invoker: "как ты аспекта эти 3 рядом расположил")
    three = two + "\n" + NEW.format("C")
    out = pair_new_cards(three, "7.38")
    assert out.count('<div class="card-pair card-trio">') == 1 and '<div class="card-pair">' not in out
    assert out.index("card-trio") < out.index(">A<") < out.index(">B<") < out.index(">C<")
    four = pair_new_cards(three + "\n" + NEW.format("D"), "7.38")      # four: two pairs
    assert four.count('<div class="card-pair">') == 2 and "card-trio" not in four


def test_a_block_with_rows_of_its_own_or_two_cards_does_not_pair():
    from patch.card_pairs import pair_new_cards
    rows = NEW.format("A").replace("</div></div></div></div></div>",
                                   '</div></div></div></div><ul class="changes"><li data-tag="buff">Row</li></ul></div>')
    assert pair_new_cards(rows + NEW.format("B"), "7.38") == rows + NEW.format("B")
    covered = rows.replace('<li data-tag="buff">', '<li data-tag="buff" class="iab-covered covered-card">')
    assert '<div class="card-pair">' in pair_new_cards(covered + NEW.format("B"), "7.38")


def test_a_lone_new_card_stands_right_of_its_block_and_a_pair_stays_a_pair():
    from patch.card_pairs import pair_new_cards, single_cards_right
    rows = NEW.format("A").replace("</div></div></div></div></div>",
                                   '</div></div></div></div><ul class="changes"><li data-tag="buff">Row</li></ul></div>')
    out = single_cards_right(rows, "7.38")
    assert out.startswith('<div class="single-right"><div class="ability-block facet-block">')
    assert out.index("Row</li>") < out.index('<span class="sr-line"') < out.index('<div class="ability-change ')
    paired = pair_new_cards(NEW.format("B") + NEW.format("C"), "7.38")
    assert single_cards_right(paired, "7.38") == paired
    assert single_cards_right(rows, "7.41").startswith('<div class="single-right">')     # every patch now


def test_rows_led_by_ability_icons_are_sections_with_their_own_heads():
    from patch.card_sections import card_sections
    chip = lambda name, slug: (f'<span class="acr-lead-chips"><span class="ability-chip" data-tooltip="{name}" role="img">'
                               f'<img src="../icons/_t/abilities/{slug}.webp" alt=""></span></span>')
    pane = ('<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
            '<div class="ability-change-row">' + chip("Runic Infusion", "arc_warden_runic_infusion") + "Gains stats.</div>"
            '<div class="ability-change-row">' + chip("Magnetic Field", "arc_warden_magnetic_field") + "Pulls runes.</div>"
            "</div></div>")
    out = card_sections(pane, "7.38")
    # the head is the strip of a card's own head (owner 2026-11-06: "Шапка Power Capture не такая, как везде")
    assert out.count('class="ability-change-row acr-sec') == 2 and out.count('class="iab-head acr-sec-head"') == 2
    assert out.count("acr-sec-top") == 1                           # the first head on the pane's top edge
    assert '<span class="iab-name">Magnetic Field</span>' in out and 'class="iab-kind">Active:</b>' in out
    one = pane.replace("Runic Infusion", "Magnetic Field").replace("arc_warden_runic_infusion", "arc_warden_magnetic_field")
    assert "acr-sec-head" not in card_sections(one, "7.38")       # one ability: lines, no heads


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


def test_a_removed_upgrade_ability_gets_its_own_block():
    from tools.patchgen.post_facets import _removed_innate_block
    out = _removed_innate_block("bloodseeker", "Blood Mist", None, "7.37e", "    ")
    assert out[0] == '    W(ability("Blood Mist", slug="bloodseeker_blood_mist"))' and 'li("Removed", t("DEL"))' in out[2]
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert "Removed Blood Mist ability" not in text and 'W(ability("Blood Mist", slug="bloodseeker_blood_mist"))' in text


def test_a_bonus_said_after_the_total_goes_in_brackets_and_a_per_win_bonus_stays_alone():
    from patch.cards_aghs import _aghs_inline
    # 7.41 Nyx Assassin: "Decreases cooldown to 70/60/50s by 10s" (owner 2026-11-06: "by 10s … в скобках как факт")
    assert _aghs_inline("Decreases cooldown by 10s.\nCooldown: =70/60/50s.") == "Decreases cooldown to 70/60/50s (by 10s)."
    # 7.41 Legion Commander: "Increases Duel damage to 15/25/35 by 5 per win" read wrong — the total fits no word there
    assert _aghs_inline("Increases Duel damage by 5 per win.\nDamage: =15/25/35.") == "Increases Duel damage by 5 per win."


def test_a_number_put_in_brackets_goes_back_to_the_table_under_it():
    # 7.37 Flayed Flare: one side "dealing damage (150)" and one value, the other side a table — the card makes both tables
    from patch import cards_aghs
    from patch.value_tables import value_tables
    cards_aghs.INLINED["damage (150)"] = "Damage"
    side = lambda row: ('<div class="ability-change-pane"><div class="ability-change-body"><div class="ability-change-row">'
                        + row + "</div></div></div>")
    card = ('<div class="ability-change unified-panes">' + side('Throws a flare, dealing damage (<b class="iab-num">150</b>). '
            'Range reduction: <b class="iab-num">40%</b>.') + side("Damage: 150. Range reduction: 40%. Duration: 2.") + "</div>")
    out = value_tables(card)
    assert "dealing damage." in out and "(<b" not in out
    assert out.index('class="vt-l vt-first">Damage<') < out.index(">Range reduction<")


def test_a_phrase_in_a_card_is_never_coloured_a_number_is():
    from patch.value_tables import plain_phrases_in_cards
    card = ('<div class="ability-change unified-panes"><div class="ability-change-row"><span class="iab-hl iab-hl-del">Muerta '
            'gains <b class="iab-num">30%</b> Spell Lifesteal</span> and <span class="iab-hl iab-hl-buff">+20</span>.</div></div>')
    out = plain_phrases_in_cards(card)
    assert "iab-hl-del" not in out and "Muerta gains" in out and '<span class="iab-hl iab-hl-buff">+20</span>' in out
    swap = '<li><span class="iab-hl iab-hl-del">+20 Damage</span></li>'          # a talent swap row outside a card
    assert plain_phrases_in_cards(swap) == swap


def test_the_two_selves_columns_are_the_games_labels():
    from tools.patchgen.post_cards import _selves_columns
    kv = ("Summons a Spark Wraith.\nActivation delay: 2. Damage: 100/180/260/340. Wraith speed: 400. Slow duration: "
          "0.6/0.8/1/1.2. Activation delay: 1. Damage: 75/140/205/270. Wraith speed: 725. Slow duration: 0.4/0.5/0.6/0.7.")
    cols = _selves_columns("Spark Wraith", kv,
                           "Spark activates in 2 seconds, flies at a speed of 400, slows enemy for 0.6/0.8/1/1.2s, deals 100/180/260/340 damage",
                           "Spark activates in 1 second, flies at a speed of 725, slows enemy for 0.4/0.5/0.6/0.7s and deals 75/140/205/270 damage",
                           "Spark activates in 1.5 seconds, flies at a speed of 550, slows enemy for 0.5/0.6/0.7/0.8s and deals 100/170/240/310 damage")
    assert cols[0] == ("Activation delay", "Speed", "Slow duration", "Damage")
    assert cols[1] == ("2s", "400", "0.6/0.8/1/1.2s", "100/180/260/340") and cols[3][0] == "1.5s"
    # the double's numbers are other values of the game (7.38 Magnetic Field): no shared columns
    mf = "Field.\nAttack speed bonus: 30/60/90/120. Evasion bonus: 100%. Bonus attack range: 150. Bonus attack damage: 20/40/60/80."
    assert _selves_columns("Magnetic Field", mf, "100% evasion, 30/60/90/120 bonus attack speed",
                           "150 bonus attack range, 20/40/60/80 base attack damage", "100% evasion, 30/60/90/120 bonus attack speed") is None


def test_a_formula_on_another_variable_is_scaling_reworked():
    from patch.scaling_card import variable
    from tools.patchgen.post_items import _scaling_cards
    assert variable("1900 + (20 per minute of game time)") == "minute" and variable("2500 + (200 per death)") == "death"
    assert variable("Increased by 5") is None
    icons = {"Reflect": "../icons/abilities/miniboss_reflect.png"}
    out = _scaling_cards([("Reflect", "Reflect: Damage percentage rescaled from 90 + (20 per death) to 50 + (2 per minute of game time)")],
                         icons, "7.38")
    assert len(out) == 1 and out[0].startswith('W(scaling_rework("Reflect", "../icons/abilities/miniboss_reflect.png", "Reflects')
    assert "('Damage percentage', '90 + (20 per death)', '50 + (2 per minute of game time)')" in out[0]
    same = _scaling_cards([("Reflect", "Reflect: Damage rescaled from 90 + (20 per death) to 50 + (25 per death)")], icons, "7.38")
    assert same[0].startswith("# v2-todo")


def test_the_scaling_card_tables_run_on_each_formulas_own_axis(monkeypatch):
    from patch.scaling_card import scaling_rework
    from patch.state import _State
    monkeypatch.setattr(_State, "current_patch_version", "7.38")     # the header's kind comes from that patch's files
    html = scaling_rework("Reflect", "../icons/abilities/miniboss_reflect.png", "Reflects damage.", "Reflects damage.",
                          [("Damage percentage", "90 + (20 per death)", "50 + (2 per minute of game time)")])
    plain = html.replace('<b class="iab-num">', "").replace("</b>", "")
    assert "Scaling reworked" in plain and "90% + 20% per death" in plain and "50% + 2% per minute</span>" in plain
    assert "<th>60:00</th>" in html and "<td>170%</td>" in html            # 50 + 2 * 60; deaths 0..6: 90 + 20 * 4
    # what each side grows with is in its header (owner 2026-11-06: "scales with game's time / scales with X")
    assert '<span class="iab-scale">– scales with its deaths</span>' in html
    assert '<span class="iab-scale">– scales with game time</span>' in html and "Scales with" not in plain


def test_what_an_ability_scales_with_goes_to_its_header_however_the_text_says_it():
    from patch.cards_item_abilities import _pane_parts
    head = lambda desc: _pane_parts(desc, {"kind": "Passive"})[0]
    # 7.37 Death Prophet: the sentence without a full stop at the end of the text
    assert "– scales with Exorcism" in head(["Delays damage over 5 seconds. Scales with Exorcism"])
    # 7.41 Tiny: in brackets
    assert "– scales with Grow" in head(["Decreases attack damage by 2% per stack (levels with Grow). Max Stacks: 10."])
    # 7.38 Summon Convert: what a part depends on; the text keeps the part
    h, body = _pane_parts(["Summoned unit depends on the level of Holy Persuasion: Marshmage (levels 2-4)"],
                          {"kind": "Active"})
    assert "– scales with Holy Persuasion" in h and "Summoned unit: Marshmage" in body
    # a formula on game time or on hero level, no words for it
    assert "– scales with game time" in head(["Damage: 200 + 0.5% per minute of game time."])
    assert "– scales with level" in head(["Restore percentage = 10% + 1.5% per hero level."])
    assert "scales with" not in head(["Armor increases by 3.6% + 0.4% per level of his bonus movement speed."])
    # no kind for the pane (7.37 Lone Druid): the text's own words still go up, a formula guess doesn't
    no_kind = _pane_parts(["Gets 50/60/70/80% bonus stats from them. Scales with True Form"], {})[0]
    assert '<span class="iab-scale">Scales with True Form</span>' in no_kind
    assert _pane_parts(["Damage: 200 + 0.5% per minute of game time."], {})[0] == ""


def test_a_sub_ability_named_in_the_text_gets_a_line_above_it():
    from patch.card_sections import card_sections
    pane = ('<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
            '<div class="ability-change-row">A creep with the Martyrdom ability. Respawn time: 60s.</div>'
            '<div class="ability-change-row"><b>Martyrdom:</b> sacrifices itself.</div>'
            '<div class="ability-change-row"><b>Cast Point:</b> 0.3s.</div></div></div>')
    out = card_sections(pane, "7.41")
    assert '<div class="ability-change-row acr-sec"><b>Martyrdom:</b>' in out
    assert '<div class="ability-change-row"><b>Cast Point:</b>' in out          # a value's label is no sub-ability


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


def test_a_row_going_on_with_the_rework_above_joins_it():
    from tools.patchgen.post_general import _postprocess_rework_continuation
    lines = ['    W(li("Both are now available. They have a shared cooldown", t("REWORK")))',
             '    W(li("This results in swapping special attacks: Frost first", t("REWORK")))',
             '    W(li("As a result of the changes, X", t("REWORK")))']
    out = _postprocess_rework_continuation(lines)
    assert out[0] == ('    W(li("Both are now available. They have a shared cooldown. This results in swapping special '
                      'attacks: Frost first", t("REWORK")))') and len(out) == 2
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert 'W(li("This results in swapping' not in text


def test_head_icons_line_up_with_the_digits_and_tails_never_break():
    from patch.css_bundle import read_css
    from patch.cards_rows import _glue_tail
    assert "position: relative; top: -1px; }" in read_css().split(".iab-ico {", 1)[1].split("\n", 1)[0]
    chip = '<span class="ability-chip chip-word" data-tooltip="Power Rune" role="img"><img src="p.png"></span>'
    out = _glue_tail("upon activating any " + chip + ' <!--TIP--><span class="info-tip">?</span><!--/TIP-->')
    assert out.startswith('upon activating <span class="li-tail">any ' + chip)


def test_aghanim_rows_stay_by_their_ability_without_saying_so():
    # owner 2026-11-06, 7.38 Invoker: the "Aghanim's Scepter" / "Aghanim's Shard" heads over the upgrade rows were
    # "лишнее, надо сделать как везде с подсветкой скипетра/шарда, ну как до этого"
    import patch.cards_rows as cards_rows
    from patch.cards_rows import _card_row, _row_html
    assert not hasattr(cards_rows, "group_aghs_rows")
    row = _card_row(("<g>",), "Can be upgraded with Aghanim's Scepter. Applies to allies.")
    html = _row_html(row)
    assert "Can be upgraded" not in html and '</span>Applies to <span class="li-tail">allies.' in html
    assert 'class="ability-change-row aghanim-scepter acr-aghs"' in html and "aghanim-marker scepter" in html


def test_tags_as_tiles_run_on_every_page():
    from patch import page
    from patch.css_bundle import read_css
    assert page.TAG_MARK_PAGES is None
    css = read_css()
    for tag in ("buff", "nerf", "new", "del", "swap", "rework"):
        assert (f'.tag-marks .badge[data-tag~="{tag}"], .filter-btn[data-filter="{tag}"] '
                f'{{ --tm: url("data:image/svg+xml,') in css
    assert css.index('[data-tag~="nerf"]') < css.index('[data-tag~="del"], ')     # "del nerf" shows the cross


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


def test_a_removed_ability_with_its_icon_and_a_reworked_facet_ability_as_a_card():
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    # Eject: Dismember's hidden sub-ability, its "Removed Aghanim's Shard." says it (owner 2026-11-06)
    assert 'W(ability("Eject"' not in text and "Removed Eject ability" not in text
    assert (ROOT / "icons" / "abilities" / "pudge_eject.png").exists()      # from Valve's CDN (fetch_icons.py)
    assert 'game_ability_pair("faceless_void_time_zone", "7.38")' in text
    for name, slug in (("Bad Juju", "dazzle_bad_juju"), ("Parting Shot", "muerta_parting_shot")):
        assert f'W(ability("{name}", slug="{slug}"))' in text and f"Removed {name} ability" not in text


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


def test_a_new_number_finds_its_unmarked_old_one_by_its_label():
    # 7.38 Succubus: the old side's 12% / 18% were plain, the new 2% / 14% showed no % on hover
    from patch.elements import hl
    from patch.number_tips import _pair_number_tips
    old = "Lifesteal is high. Minimum lifesteal: 12%. Maximum lifesteal: 18%."
    new = (hl("All sources apply", "new") + ". Minimum lifesteal: " + hl("2%", "nerf") + ". Maximum lifesteal: "
           + hl("14%", "nerf") + ".")
    out = _pair_number_tips(old, new)
    assert out.count("iab-tip-pct") == 2 and "-83%" in out and "-22%" in out


def test_an_aghanim_row_its_card_shows_is_hidden():
    from patch.card_sections import hide_rows_the_aghs_card_says
    row = ('<ul class="changes"><li data-tag="buff" class="aghanim-scepter li-bg"><span class="badge">BUFF</span><span '
           'class="row-text">Aghanim\'s Scepter Cooldown decreased from 100/95/90s to 90/85/80s</span></li></ul>')
    card = ('<div class="ability-change unified-panes aghs-change"><div class="ability-change-pane ability-change-old">'
            'Reduces cooldown to <b>100/95/90s</b>.</div><div class="ability-change-pane ability-change-new">Reduces '
            'cooldown to <b>90/85/80s</b>.</div></div>')
    assert 'class="iab-covered covered-card aghanim-scepter li-bg"' in hide_rows_the_aghs_card_says(row + card)
    other = card.replace("90/85/80s", "70s")
    assert "iab-covered" not in hide_rows_the_aghs_card_says(row + other)


def test_a_rows_own_badges_go_onto_its_new_number():
    from patch.badges import b
    from patch.cards_rows import _badges_into_number
    out = _badges_into_number("Base movement speed increased from 275 to 310 " + b(275, 310))
    assert 'class="iab-hl iab-hl-buff iab-hl-num"' in out and "badge-group" not in out.split("data-tooltip")[0]
    assert out.startswith("Base movement speed increased from 275 to <span")


def test_search_jumps_at_once_and_lights_the_block():
    from patch.js_bundle import read_js
    from patch.css_bundle import read_css
    js = read_js()
    assert "behavior: 'instant'" in js and "hit.classList.add('search-hit')" in js
    assert ".ability-change-pane .iab-head .iab-name" in js                  # Tree Dance in a facet's card head
    assert "@keyframes search-hit" in read_css()


def test_word_values_and_capital_labels_in_value_tables():
    from patch.value_tables import _split
    _, pairs, _ = _split("Heals. DISPEL TYPE: Basic Dispel. Cleanse heal: <b>450</b>.")
    assert pairs == [("Dispel type", "Basic Dispel"), ("Cleanse heal", "<b>450</b>")]


def test_regen_icons_are_heart_and_drop_with_a_plus():
    # the up arrow misled on a decrease; the plus in the corner (owner 2026-11-06, variant 5)
    for name in ("health_regen.svg", "mana_regen.svg"):
        svg = (ROOT / "icons" / name).read_text(encoding="utf-8")
        assert '<circle cx="194" cy="194" r="62"' in svg and "translate(146 146) scale(0.375)" in svg
        assert "H140v76" in svg and "l96-96" not in svg                     # the plus, not the arrow


def test_a_long_side_with_no_short_intro_folds_whole():
    from patch.cards_rows import fold_long_rows
    long_first = '<div class="ability-change-row">' + "word " * 150 + "</div>"
    rest = '<div class="ability-change-row">' + "more " * 30 + "</div>"
    out = fold_long_rows([long_first, rest])
    assert out[0].startswith('<div class="acr-fold acr-fold-whole">')
    # 7.38 Roshan's Throw, ~700 characters in one long row: stays open (owner 2026-10-30)
    short = '<div class="ability-change-row">' + "word " * 125 + "</div>"
    assert fold_long_rows([short, '<div class="ability-change-row">x y</div>'])[0] == short


def test_a_cards_upgrade_row_the_aghanim_card_below_shows_goes():
    from patch.card_sections import drop_upgrade_rows_said_below
    html = ('<div class="ability-block"><div class="ability-change unified-panes is-single-new"><div class="ability-change-'
            'pane ability-change-new"><div class="ability-change-body"><div class="ability-change-row">Text.</div>'
            '<div class="ability-change-row aghanim-shard">Allows casting while disabled.</div></div></div></div>'
            '<div class="ability-change unified-panes aghs-change"><div class="ability-change-pane ability-change-new">'
            '<div class="ability-change-row aghanim-shard">Can be cast while disabled.</div></div></div></div>')
    out = drop_upgrade_rows_said_below(html)
    assert "Allows casting while disabled" not in out and "Can be cast while disabled" in out and "Text." in out


def test_tag_marks_run_on_every_patch_page():
    # the trial on 7.41f + 7.38 rolled out to all patches (owner 2026-11-07)
    from patch import page
    assert page.TAG_MARK_PAGES is None


def test_a_head_never_moves_its_values_to_another_line():
    from patch.css_bundle import read_css
    css = read_css()
    assert "line-height: 18px; flex-wrap: nowrap;" in css
    assert ".iab-head { display: flex; align-items: flex-start;" in css     # values on the title's first line
    assert ".iab-title { white-space: normal; flex: 1 1 auto; min-width: 0; }" in css


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


def test_an_aghanims_card_row_reaches_alike_both_ways_and_says_no_label():
    # owner 2026-11-06: "Найди подобные проблемы в других местах, может ещё где подводку скипетра/шарда не так строится"
    # — the stripe reached 6px left only (7.38 Dark Willow, 7.39 Invoker: -1px left, 5px right), past a narrow card's
    # edge; 7.39 Invoker's rows said "Aghanim's Shard:" beside the glyph
    from patch.cards_rows import _card_row, _row_html
    from patch.css_bundle import read_css
    css = read_css()
    assert (".ability-change-row.acr-aghs { --agr: min(6px, var(--px, 6px)); margin-left: calc(-1 * var(--agr));\n"
            "  margin-right: calc(-1 * var(--agr)); padding-left: var(--agr); padding-right: calc(8px + var(--agr)); }") in css
    html = _row_html(_card_row((), "Aghanim's Shard: Enemy heroes that stay in Ice Wall freeze"))
    assert "Aghanim's Shard:" not in html and ">Enemy heroes" in html and "aghanim-marker shard" in html


def test_three_cards_in_a_line_start_their_parts_on_one_line_and_do_not_fold():
    # owner 2026-11-06, 7.38 Invoker: "Сделай на сайте как ты аспекта эти 3 рядом расположил"
    from patch.css_bundle import read_css
    from patch.js_bundle import JS_PARTS, read_js
    css, js = read_css(), read_js()
    assert ".card-pair.card-trio { grid-template-columns: repeat(3, minmax(0, 1fr)); column-gap: 18px; }" in css
    # each folds on its own, no heights evened (owner 2026-11-06: "Лучше дать возможность сворачивать/разворачивать
    # карточки по отдельности … не обязательно одинаковой высоты")
    assert ".card-trio .acr-fold-toggle" not in css and ".card-trio .acr-fold > .acr-fold-body" not in css
    assert "card-trio" not in JS_PARTS and ".card-trio" not in js
    assert ".card-pair, .card-pair.card-trio { grid-template-columns: minmax(0, 1fr); }" in css     # a phone
    # a card open beside two folded ones folds too, after its first row ("в свёрнутом состоянии одинаковые")
    from patch.card_pairs import pair_new_cards
    folded = NEW.format("A").replace('<div class="ability-change-row">Text</div>',
                                     '<div class="ability-change-row">One</div><div class="acr-fold"><div class="acr-fold-body">'
                                     '<div class="ability-change-row">Two</div></div></div>')
    open_ = NEW.format("C").replace('<div class="ability-change-row">Text</div>',
                                    '<div class="ability-change-row">One</div><div class="ability-change-row">Two</div>')
    out = pair_new_cards(folded + folded.replace(">A<", ">B<") + open_, "7.38")
    assert out.count('<div class="acr-fold">') == 3 and out.count("acr-fold-toggle") == 1


def test_added_values_for_levels_put_their_numbers_under_the_tip():
    # owner 2026-11-06, 7.38 E.M.P. / Sun Strike: "Added Mana Burned values for levels 9 and 10 of Wex: 700/775 - забыл
    # числа под [?]"
    from tools.patchgen.rows import _emit_li
    out = _emit_li("Added Mana Burned values for levels 9 and 10 of Wex: 700/775")
    assert out == ('W(li("Added values for levels 9 and 10", t("NEW"), '
                   'extra=inline_note("Mana Burned for levels 9 and 10 of Wex is 700/775")))')
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert "values for levels 9 and 10 of Wex: 700/775" not in p738
    assert "Ice Wall: Movement Slow (Quas) 180/200%" in p738                 # now in the row all of them share


def test_a_shard_row_after_the_same_abilitys_scepter_row_gets_its_own_head():
    # 7.38 Agent of Gallaron: Sun Strike's Scepter (Cataclysm) and Shard (Forge Spirit) are two parts of the trio
    from patch.card_sections import card_sections
    chip = ('<span class="acr-lead-chips"><span class="ability-chip" data-tooltip="{0}" role="img">'
            '<img src="../icons/_t/abilities/{1}.webp" alt=""></span></span>')
    row = '<div class="ability-change-row{0}">{1}{2}</div>'
    pane = ('<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
            + row.format("", chip.format("Exort", "invoker_exort"), "Bonus level.")
            + row.format(" aghanim-scepter acr-aghs", chip.format("Sun Strike", "invoker_sun_strike"), "Cataclysm.")
            + row.format(" aghanim-shard acr-aghs", chip.format("Sun Strike", "invoker_sun_strike"), "Forge Spirit.")
            + "</div></div>")
    out = card_sections(pane, "7.38")
    assert out.count('<span class="iab-name">Sun Strike</span>') == 2


def test_generator_hero_rules_of_2026_11_06():
    # owner 2026-11-06: a new main attribute first in General; "Added three orb-centered facets…" hidden under the
    # facet cards; an ability gaining an active part -> old > new card (7.38 Special Delivery); Dauntless REWORK
    from tools.patchgen.post_hero import _postprocess_attr_change_first, _postprocess_facets_summary_covered
    from tools.patchgen.tags import _guess_tag
    lines = ['    W(hero_header("X"))', "    W(ul_open())", "    W(hero_stat_card())", '    W(li("Base damage", t("BUFF")))',
             '    W(li(attr_change("Universal", "Intelligence"), t("REWORK")))', "    W(ul_close())"]
    out = _postprocess_attr_change_first(lines)
    assert out[3].strip().startswith("W(li(attr_change(") and out[4].strip().startswith('W(li("Base damage"')
    lines = ['    W(hero_header("Invoker"))', '    W(li("Added three orb-centered facets. Each provides", t("NEW")))',
             '    W(new_facet("a", desc=[]))', '    W(new_facet("b", desc=[]))']
    assert _postprocess_facets_summary_covered(lines)[1].endswith(', t("NEW"), covered=True))')
    chosen = lines[:2] + ['    W(li("Aghanim\'s Scepter also provides a level to the orb of the chosen facet", t("BUFF")))'] + lines[2:]
    assert _postprocess_facets_summary_covered(chosen)[2].endswith("covered=True))")
    assert _guess_tag("Now affects only Mars himself") == "REWORK"
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert 'old=dict(name="Special Delivery", slug="marci_special_delivery", desc=game_ability_desc(' in p738
    assert 'Cast point: 1s", t("NEW"), covered=True))' in p738


def test_the_main_attribute_row_stands_first_on_the_page_too():
    # owner 2026-11-06: "Если герой меняет атрибут … всегда ставим вверху списка general" — the stats card's damage
    # rows were drawn above it
    from patch.general_rows import attr_row_first
    attr = ('<li data-tag="rework"><span class="badge rework">R</span><span class="row-text">Main attribute changed from '
            '<b class="attr-chip is-uni">Universal</b></span></li>')
    dmg = '<li data-tag="nerf"><span class="row-text">Starting damage decreased</span></li>'
    out = attr_row_first('<ul class="changes">' + dmg + "<!--x-->" + attr + "</ul>")
    assert out == '<ul class="changes">' + attr + dmg + "<!--x--></ul>"


def test_a_lone_cards_block_rows_go_under_the_card():
    # owner 2026-11-06, 7.38 Voidbringer: "Number of times +2 All Attributes … надо ниже карточки поставить, чтобы -14%
    # не стояло в центре"
    from patch.card_pairs import single_cards_right
    block = ('<div class="ability-block facet-block"><h4 class="ability-title">V</h4>'
             '<ul class="changes ability-change-summary-ul"><li data-tag="new"><span class="row-text">New facet</span></li>'
             '<li data-tag="nerf"><span class="row-text">Number of times decreased</span></li>'
             '<li data-tag="buff" class="iab-covered covered-card"><span class="row-text">Hidden</span></li></ul>'
             '<div class="ability-change unified-panes is-single-new" data-tag="new"><div class="ability-change-pane">'
             '</div></div></div>')
    out = single_cards_right(block, "7.38")
    assert out.index("New facet") < out.index('<div class="ability-change ') < out.index("Number of times")
    assert '<div class="ability-block sr-under"><ul class="changes"><li data-tag="nerf">' in out
    assert out.index("Hidden") < out.index('<div class="ability-change ')        # a hidden row stays


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
