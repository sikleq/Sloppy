"""Guards the value tables of cards: tables of levels, formulas and scaling, values in brackets, upgrade tables,
the % on hover and the colours of changed numbers.
"""

import os
import pathlib
import pytest
import re
import sys
import tools.generate_patch_code_v2 as g
from patch import cards_item_abilities

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def _invoker_lines():
    return [
        '    W(hero_header("Invoker"))',
        '    W(ability("Quas", slug="invoker_quas"))',
        '    W(ability_group(("Cold Snap", "invoker_cold_snap"), ("Ice Wall", "invoker_ice_wall")))',
        '    W(li("Added values for levels 9 and 10", t("NEW"), extra=inline_note("Cold Snap: Duration (Quas) '
        '6.2/6.6s<br>Ice Wall: Movement Slow (Quas) 180/200%")))',
    ]


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


def test_a_new_number_finds_its_unmarked_old_one_by_its_label():
    # 7.38 Succubus: the old side's 12% / 18% were plain, the new 2% / 14% showed no % on hover
    from patch.elements import hl
    from patch.number_tips import _pair_number_tips
    old = "Lifesteal is high. Minimum lifesteal: 12%. Maximum lifesteal: 18%."
    new = (hl("All sources apply", "new") + ". Minimum lifesteal: " + hl("2%", "nerf") + ". Maximum lifesteal: "
           + hl("14%", "nerf") + ".")
    out = _pair_number_tips(old, new)
    assert out.count("iab-tip-pct") == 2 and "-83%" in out and "-22%" in out


def test_a_rows_own_badges_go_onto_its_new_number():
    from patch.badges import b
    from patch.cards_rows import _badges_into_number
    out = _badges_into_number("Base movement speed increased from 275 to 310 " + b(275, 310))
    assert 'class="iab-hl iab-hl-buff iab-hl-num"' in out and "badge-group" not in out.split("data-tooltip")[0]
    assert out.startswith("Base movement speed increased from 275 to <span")


def test_word_values_and_capital_labels_in_value_tables():
    from patch.value_tables import _split
    _, pairs, _ = _split("Heals. DISPEL TYPE: Basic Dispel. Cleanse heal: <b>450</b>.")
    assert pairs == [("Dispel type", "Basic Dispel"), ("Cleanse heal", "<b>450</b>")]


def test_added_values_for_levels_put_their_numbers_under_the_tip():
    # owner 2026-11-06, 7.38 E.M.P. / Sun Strike: "Added Mana Burned values for levels 9 and 10 of Wex: 700/775 - забыл
    # числа под [?]"
    from tools.patchgen.rows import _emit_li
    out = _emit_li("Added Mana Burned values for levels 9 and 10 of Wex: 700/775")
    assert out == ('W(li("Added values for levels 9 and 10", t("NEW"), '
                   'extra=inline_note("Mana Burned for levels 9 and 10 of Wex is 700/775")))')
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert "values for levels 9 and 10 of Wex: 700/775" not in p738
    # now in the row all of them share, drawn as one table of every level since 2026-11-08
    assert "('invoker_ice_wall', 'Ice Wall', 'Movement Slow', 'invoker_quas'" in p738


def test_the_damage_at_level_30_percent_is_coloured(monkeypatch):
    # "Тут -20% не окрашено почему-то" (7.38 Lycan)
    html = ROOT / "dist" / "patches" / "7.38.html"
    if not html.exists():
        pytest.skip("no build")
    text = html.read_text(encoding="utf-8")
    assert re.search(r'Damage at level 30: [^<]*\(<span class="pop-pct pop-pct-nerf">-20%</span>\)', text)
    assert not re.search(r"Damage at level 30: [^<]*\([+-]\d+%\)", text)


def test_new_level_values_become_one_table_of_every_level():
    # "может вот этот список сделать в виде formula table? он массивный" -> "Вариант B нравится"
    from patch import game_files
    if "7.38" not in game_files.versions():
        pytest.skip("no game files")
    from tools.patchgen.post_level_values import _postprocess_level_values
    out = _postprocess_level_values(_invoker_lines(), "7.38")[-1]
    assert out.startswith('    W(li_level_values("Added values for ", "levels 9 and 10", [')
    assert "('invoker_cold_snap', 'Cold Snap', 'Duration', 'invoker_quas', '3.0 3.4 3.8 4.2 4.6 5.0 5.4 5.8 6.2 6.6', 's')" in out
    # a slow is negative in the file, positive in the notes
    assert "'20 40 60 80 100 120 140 160 180 200', '%')" in out
    assert out.endswith("new_from=9, tag=t(\"NEW\")))")


def test_a_list_the_files_do_not_confirm_stays_as_it_was():
    from tools.patchgen.post_level_values import _postprocess_level_values
    lines = _invoker_lines()
    lines[-1] = lines[-1].replace("6.2/6.6s", "61/66s")
    assert _postprocess_level_values(lines, "7.38") == lines


def test_the_table_marks_the_new_levels_gold():
    from patch.level_values import level_values_table
    html = level_values_table([("invoker_emp", "E.M.P.", "Mana Burned", "invoker_wex", "100 175 700 775", "")],
                              3, "f1")
    assert '<th class=lv-new>3</th><th class=lv-new>4</th>' in html
    assert "<td>100</td><td>175</td><td class=lv-new>700</td><td class=lv-new>775</td>" in html
    assert 'rowspan="1"' in html and "invoker_wex.png" in html
    # a phone squeezed the orb column to 4px and the orb to 0 (Sonnet review 2026-11-08)
    css = (ROOT / "src" / "css" / "patch-formula-tables.css").read_text(encoding="utf-8")
    assert ".formula-table.lv-values td.lv-scale { width: 22px; min-width: 22px;" in css
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert 'W(li_level_values("Added values for ", "levels 9 and 10"' in p738
    assert "Cold Snap: Duration (Quas) 6.2/6.6s" not in p738


def test_an_upgrade_table_lists_the_bare_numbers_of_its_text():
    # 7.39e Spirit Link's Scepter: only Cooldown and Mana cost were in the table
    from patch import game_files
    if "7.39e" not in game_files.versions():
        pytest.skip("no game files")
    from patch.aghs_text import aghs_text
    from patch.cards_aghs import _aghs_inline
    text = _aghs_inline(aghs_text("lone_druid_spirit_link", "scepter", "7.39e"))
    # the text says 20s and 35% too; the table lists them anyway ("@", not dropped as "said already")
    assert text.endswith("Cooldown: 40s. Mana cost: 50. Duration: 20s. Armor sharing and attack speed increase: 35%.")
    text = _page("7.40")
    # its name as the values card writes it (data/rules/value_labels.json: five words were one too many)
    assert 'Armor and attack speed share</div><div class="vt-v"><b class="iab-num">35%</b>' in text


def test_a_stats_card_row_with_a_percent_has_the_hover_ruler():
    # 7.40 Spirit Bear: "в правой карточке не хватает пунктирной линейки при наведении на строки"
    text = _page("7.40")
    assert '<span class="property-text pt-bg" style="grid-row:1;grid-column:2">Base Health: 1500</span>' in text
    css = (ROOT / "src" / "css" / "pixel-skin-filters.css").read_text(encoding="utf-8")
    assert ".properties-change .property-text.pt-bg:hover::after {" in css


def test_the_new_levels_table_lists_the_values_the_notes_left_out():
    # 7.38 Ice Wall: "нет строки damage per second"
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert ("('invoker_ice_wall', 'Ice Wall', 'Damage per second', 'invoker_exort', "
            "'8 16 24 32 40 48 56 64 72 80', '')") in p738
    assert "'Mana regeneration'" not in p738          # the same numbers under a second key: once


def test_entangle_lists_its_numbers_for_the_side_table():
    # 7.40 Entangle: "Да, карточку справа"
    text = _page("7.40")
    i = text.index('alt="Entangle"')
    assert "has-vt-side" in text[i:i + 6000]


def test_an_upgrade_value_named_by_its_tooltip_key_drops_the_word_tooltip():
    # Sonnet 2026-11-09, 7.38 Slithereen Crush's Scepter: "Scepter puddle radius tooltip" in the values card
    from patch.aghs_text import _placeholder_lines
    block = {"AbilityValues": {"scepter_puddle_radius_tooltip": "300", "duration": "4"}}
    lines = _placeholder_lines("Leaves a puddle of %scepter_puddle_radius_tooltip% radius for %duration%s.", block, [])
    assert lines == ["Scepter puddle radius: @300.", "Duration: @4s."]


def test_an_upgrade_text_says_to_with_the_total_not_the_bonus():
    # Sonnet 2026-11-09: the game writes "Decreases cooldown to %AbilityCooldown%s" and keeps the Shard's -3 there:
    # 7.40 Earth Spirit's Geomagnetic Grip read "to 3s" (13 - 3 = 10, its table 10s), 7.39 Chen's Hand of God "to 40s"
    from patch.aghs_text import _totals_after_to
    block = {"AbilityValues": {"AbilityCooldown": {"value": "150 130 110", "special_bonus_scepter": "-40"},
                               "AbilityChannelTime": {"special_bonus_scepter": "=6"}}}
    desc = "Decreases the cooldown to %AbilityCooldown%s, lasts up to %AbilityChannelTime% seconds; by %AbilityCooldown%s."
    assert _totals_after_to(desc, block, "scepter") == (
        "Decreases the cooldown to 110/90/70s, lasts up to %AbilityChannelTime% seconds; by %AbilityCooldown%s.")


def test_a_sentence_with_a_colon_is_no_value_row():
    # Sonnet 2026-11-09, 7.41 Venomancer: "Imbues Venomancer's attacks with poison: 9 + 1 per level damage per second and
    # a flat 10% movement slow." made a table row named by the half sentence
    from patch.value_tables import _split
    row = ("Imbues Venomancer's attacks with poison: <b>9 + 1 per level</b> damage per second and a flat "
           "<b>10% movement slow</b>.")
    assert _split(row, 1) is None
    assert _split("Duration: <b>4s</b>. Damage: <b>12% + 0.5% per level</b>.", 1)[1][1][0] == "Damage"


def test_a_values_card_tip_colours_say_what_the_change_means():
    # Sonnet 2026-11-09: 7.41 Lich Sacrifice's gold "Cooldown 120" (from 60) showed its +100% green; 7.38 Demonic
    # Cleanse's heal, turned green by its BUFF row, kept the card's tip with the colours the other way
    from patch.deck_values import _tip, _unhint
    up = _tip("60", '<b class="iab-num">120</b>', "new", "cooldown")
    assert "nerf" in up and "buff" not in up.split("iab-tip-pct")[1][:200]
    more = _tip("10%", '<b class="iab-num">20%</b>', "new", "slow")
    assert "buff" in more.split("iab-tip-pct")[1][:200]
    hinted = '<span class="iab-hint abil-ico-hint" data-tooltip="x"><span class="formula-trigger">450</span></span>'
    assert _unhint(hinted) == '<span class="formula-trigger">450</span>'


def test_a_formula_value_gets_no_per_level_percent():
    # Sonnet 2026-11-09, 7.41 Marci "245s - 5s per level" vs a flat 240s read +2% / -98%; Dazzle "6.9 + 0.1 per level"
    from patch.deck_values import _tip
    assert _tip("240s", '<b class="iab-num">245s</b> - <b class="iab-num">5s</b> per level', "new", "cooldown") is None
    assert _tip("8", '<b class="iab-num">6.9</b> + <b class="iab-num">0.1</b> per level', "nerf", "duration") is None
    assert _tip("8", '<b class="iab-num">6</b>', "nerf", "duration")
    # ... nor keeps the one its card gave it
    from patch.deck_values import mark_new_values
    lit = ('<div class="value-table"><div class="vt-l">Duration</div><div class="vt-v"><span class="iab-hl iab-hl-nerf '
           'iab-hl-num"><span class="iab-hint abil-ico-hint" data-tooltip="&lt;span class=&quot;iab-tip-pct&quot;&gt;">'
           '<b class="iab-num">6.9</b> + <b class="iab-num">0.1</b> per level</span></span></div></div>')
    assert "iab-tip-pct" not in mark_new_values(lit, "", []) and "iab-hl-nerf" in mark_new_values(lit, "", [])


def test_a_card_row_with_its_own_badges_gets_the_hover_ruler_class():
    """Owner 2026-10-29 (7.38 Ice Breaker): a card row's % sit at its right edge and the row has the list rows' dashed
    hover ruler — a build-time class, no CSS :has() on patch pages."""
    from patch.static_has import add_static_has_classes
    html = ('<div class="ability-change-row">Path Duration <span class="badge-group"><span class="badge">+1</span>'
            '</span></div><div class="ability-change-row">no badges</div>')
    out = add_static_has_classes(html)
    assert out.count("acr-bg") == 1 and out.startswith('<div class="ability-change-row acr-bg">')


def test_precision_aura_is_a_table_by_hero_level():
    src = _p738()
    assert 'li_formula("Self Agility percentage bonus rescaled", "2% per hero level", "4/8/12/16% + 1% per level"' in src
    assert 'li_formula("Self Agility percentage bonus rescaled", "2% per hero level", "4/8/12/16% + 1% per level"' in g.generate("7.38")
    assert "tag_levels=range(1, 31)" in src and "tag_levels=range(1, 31)" in g.generate("7.38")


def test_every_damage_at_level_30_range_row_shows_its_percent():
    bare = re.findall(r'li\("Damage at level 30 [^"]*\(from \d+-\d+ to \d+-\d+\)", t\(', _p738())
    assert not bare


def test_scaling_reworked_says_no_more():
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    # the generator's scaling_rework() says "Scaling reworked" itself (owner 2026-11-06)
    assert text.count("W(scaling_rework(") == 2 and "number of deaths &rarr; game time" not in text
    from patch.scaling_card import scaling_rework
    assert "Scaling reworked</span>" in scaling_rework("R", "x.png", "a", "b", [("Damage", "1 + (2 per death)", "1 + (2 per minute)")])


def test_formula_start_is_the_tables_first_column():
    from patch.badges import bf
    # 7.41 twister: the table starts at Wex level 2, so does "start"
    _, badge, _ = bf(lambda w: 40 + 10 * w, lambda w: 30 + 10 * w, "30 + 10 x Wex Level", levels=list(range(2, 12)))
    assert badge.index(">-17%<") < badge.index(">start<")
    # a caller's own headline column is named, not called "start" (Wisdom Shrine #2)
    _, badge, _ = bf(lambda n: 280 * n, lambda n: 200 + 300 * (n - 1), "x", levels=[1, 2, 3], headline_level=2,
                     level_fmt=lambda n: f"#{n}")
    assert ">#2<" in badge and ">start<" not in badge


def test_nerf_formula_with_green_endpoints_shows_its_worst_level():
    """7.41 Monkey King Mischief: 0% at L1 and -21% (green) at L30 under a NERF tag; L20 is +21% (red)."""
    from patch.badges import bf, rank_step
    _, badge, _ = bf(rank_step([24.0, 20.0, 16.0, 12.0]), lambda L: 24.5 - 0.5 * L, "24.5s - 0.5s per level", l=True)
    assert 'data-force-left="nerf"' in badge
    assert '<span class="badge nerf5">+21%</span><span class="formula-endpoint-label">L20</span>' in badge


def test_per_level_formula_becomes_a_pill_with_its_table():
    head, body = cards_item_abilities._pane_parts(["Passive.", "Explode radius: 400. Base damage: 17 + 3 per level."])
    assert 'class="formula-trigger"' in body and ">17 + 3 per level</span>" in re.sub(r'<b class="iab-num">|</b>', "", body)
    assert '<table class="formula-table' in body
    # the level table: 17 + 3 * L
    assert "<td>20</td>" in body and "<td>107</td>" in body


def test_percent_and_bold_formulas_and_decimals():
    _, body = cards_item_abilities._pane_parts(["Passive.", "Damage (1.5% + 0.05% per level) for every 100 units."])
    assert "<td>1.55%</td>" in body
    _, body = cards_item_abilities._pane_parts(["Passive.", "Restore percentage is equal to <b>10% + 2%</b> per hero level."])
    assert body.count('class="formula-trigger"') == 1 and "<td>12%</td>" in body


def test_an_existing_pill_and_per_level_up_are_left_alone():
    trig = '<span class="formula-trigger" data-formula="f9">9 + 1 per level</span>'
    _, body = cards_item_abilities._pane_parts(["Passive.", f"Deals <b>{trig}</b> damage."])
    assert body.count("formula-trigger") == 1
    html, tables = cards_item_abilities._pill_formulas("Heal changed from 1.5% + 1.5% per level up")
    assert "formula-trigger" not in html and not tables


def test_header_value_gets_its_percent_on_hover():
    cards_item_abilities._CARD_CONFIRMED.add((991, "manacost"))
    html = cards_item_abilities.resolve_chip_marks("<!--CHIPMARK:991:manacost:buff:200/300/400-->200/250/300<!--/CHIPMARK-->")
    assert "iab-hl-num" in html and "iab-tip-pct" in html and "-17%" in html
    old = cards_item_abilities.resolve_chip_marks("<!--CHIPMARK:991:manacost:nerf:-->200/300/400<!--/CHIPMARK-->")
    assert "iab-tip-pct" not in old and "iab-hl-nerf" in old
    assert cards_item_abilities.resolve_chip_marks("<!--CHIPMARK:992:manacost:buff:1-->2<!--/CHIPMARK-->") == "2"


def test_quick_wit_card_highlights_the_new_attack_speed():
    import pytest
    page = ROOT / "dist" / "patches" / "7.41.html"
    if not page.exists():
        pytest.skip("site not built")
    html = page.read_text(encoding="utf-8")
    # in a card only numbers are coloured now (owner 2026-10-25, 2026-11-06): the sentence stays, plain
    assert "Also provides Dark Seer with" in html and '<span class="iab-hl iab-hl-new">Also provides Dark Seer' not in html
    assert "Aggrandize renamed to Quick Wit" not in html
