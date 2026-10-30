"""Proofread of 7.37 (2026-10-30) — the innate rework patch; each rule in the generator so the next patch gets it too."""
import pytest

import tools.generate_patch_code_v2 as g


@pytest.mark.parametrize("text, tag", [
    ("No longer an innate ability", "REWORK"),
    ("Starting from his second death, Roshan now always drops Roshan's Banner", "NEW"),
    ("The following are now Fully Disabled by Break", "NERF"),
    ("Fade no longer requires the target to remain still", "BUFF"),
    ("Returning as a Tier 1 Neutral item", "NEW"),
    ("Now is a Tier 3 Neutral item", "REWORK"),
    ("No longer procs Magic Stick", "BUFF"),
    ("Now procs Magic Stick", "NERF"),
    ("Illusory Orb: Now shows a preview of the orb trajectory", "QoL"),
    ("Can now be put on alt-cast to only pull Tusk towards his target ally", "NEW"),
    ("New Facet", "NEW"),
])
def test_7_37_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


def test_every_value_negative_compares_the_sizes():
    """"Armor Corruption decreased from -4 to -3": a weaker armor reduction — a nerf, as Valve's word says."""
    assert g._emit_badge("Level 20 Talent Armor Corruption decreased from -4 to -3") == "b(4, 3)"
    assert g._normalize_note_text("Level 20 Talent Armor Corruption decreased from -4 to -3")["tag"] == "nerf"


def test_a_row_without_from_still_has_its_badge():
    assert g._emit_badge("Damage increase per armor decreased 0.3% to 0.25%") == "b(0.3, 0.25)"
    assert g._emit_badge("Split Amount rescaled 80/85/90/95/100% to 85/90/95/100%") == \
        "b([80, 85, 90, 95, 100], [85, 90, 95, 100])"


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
    # levels 1–4 the same: a REWORK row with its why, not an empty badge (owner 2026-10-30: "кружок вместо тега")
    same = g._postprocess_innate_level0(
        ['W(hero_header("Anti-Mage"))', 'W(ability("Mana Break", slug="antimage_mana_break"))', 'W(ul_open())',
         'W(li("Max Mana Burned per hit rescaled from 0.8/1.6/2.4/3.2/4% to 1.6/2.4/3.2/4%", '
         'b([0.8, 1.6, 2.4, 3.2, 4], [1.6, 2.4, 3.2, 4])))', 'W(ul_close())'], "7.37")
    assert 't("REWORK"), extra=inline_note("Levels 1-4 unchanged; the 0.8 it had at level 0' in same[3]


def test_an_aghanims_rework_with_a_full_stop_is_a_card():
    """7.37 Anti-Mage "Aghanim's Scepter upgrade reworked. Reduces cooldown by 1s. …" — a full stop, not a colon; the
    old side is 7.36c's Scepter, which granted Blink Fragment (Mana Overload); the caption says "reworked"."""
    from pathlib import Path
    from patch.cards_aghs import _AGHS_REWORK_RE
    assert _AGHS_REWORK_RE.match("Aghanim's Scepter upgrade reworked. Reduces cooldown by 1s.")
    assert _AGHS_REWORK_RE.match("Aghanim's Shard reworked: Vendetta applies Break")
    page = Path(__file__).resolve().parents[1] / "dist" / "patches" / "7.37.html"
    if page.exists():
        html = page.read_text(encoding="utf-8")
        i = html.find("Blink Fragment")
        assert i > 0 and "Aghanim's Scepter reworked." in html[i - 700:i]


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


def test_general_rows_about_roshan_go_in_his_block():
    """Owner 2026-10-30: "Starting from his second death, Roshan now always drops Roshan's Banner" — in the Roshan
    block; "Teleport time to Roshan's outposts" stays a map row."""
    lines = ['W(section("General Updates"))', 'W(ul_open())',
             'W(li("Starting from his second death, Roshan now always drops Roshan\'s Banner", t("NEW")))',
             'W(li("Teleport time to Roshan\'s outposts decreased from 6s to 4s", b(6, 4)))', 'W(ul_close())', '',
             '# ===== NEUTRAL CREEP UPDATES =====', 'W(section("Neutral Creep Updates"))']
    out = g._postprocess_roshan_block(lines)
    k = out.index(g.ROSHAN_HEADER)
    assert "Roshan now always drops" in out[k + 2] and "outposts" not in "".join(out[k:])
    assert out.index('# ===== NEUTRAL CREEP UPDATES =====') > k


def test_a_general_subgroup_of_lists_is_a_mechanic_block():
    lines = ['W(section("General Updates"))', 'W(subgroup("Teleport Classification"))', 'W(ul_open())',
             'W(li("The following are considered a Teleport", t("MISC"), extra=inline_list("Twin Gates<br>Chen: Divine '
             'Favor")))', 'W(ul_close())', 'W(subgroup("Breakability Update"))', 'W(ul_open())',
             'W(li("The following are now Fully Disabled by Break", t("NERF"), extra=inline_list("Batrider: Smoldering '
             'Resin")))', 'W(ul_close())']
    out = g._postprocess_mechanic_lists(lines)
    # no tags in a mechanic block (owner 2026-10-30: "везде убрать теги")
    assert out[1] == 'W(plain_header("Teleport Classification", new="New mechanic", one_box=True))'
    assert out[5] == 'W(plain_header("Breakability Update", new="Reworked mechanic", one_box=True))'


def test_a_mechanic_blocks_plain_sentences_go_under_the_table_they_speak_of():
    """'"Breakable: Yes" … partially or fully …' → the Fully table; "… partially disabled … alt+tooltip …" → the
    Partially table; "The breakability rules … updated" → the first table. The rows themselves go."""
    lines = ['W(section("General Updates"))', 'W(subgroup("Breakability Update"))', 'W(ul_open())',
             'W(li("The following are now Fully Disabled by Break", t("NERF"), extra=inline_list("Batrider: Smoldering '
             'Resin")))',
             'W(li("The following are now Partially Disabled by Break", t("NERF"), extra=inline_list("Ember Spirit: '
             'Immolation")))',
             'W(li("The breakability rules have been updated", t("MISC")))',
             'W(li("\\"Breakable: Yes\\" has been added to all abilities that are partially or fully disabled", t("MISC")))',
             'W(li("All abilities that are partially disabled by Break have an alt+tooltip line", t("MISC")))',
             'W(ul_close())']
    out = g._postprocess_mechanic_lists(lines)
    fully = next(ln for ln in out if "Fully Disabled" in ln)
    part = next(ln for ln in out if "Partially Disabled" in ln)
    assert "rules have been updated" in fully and "Breakable: Yes" in fully and "alt+tooltip" in part
    # owner 2026-10-30: sentences about the game's tooltips are a "?" on the table's words, the rest a line of it
    assert 'pop-lead\\">The breakability rules' in fully and 'pop-tip\\">\\"Breakable: Yes' in fully
    assert 'pop-tip\\">All abilities that are partially' in part
    assert not any("t(\"MISC\")" in ln for ln in out)


def test_a_hero_ability_list_is_a_table_led_by_its_row_with_items_on_a_line_of_their_own():
    """Owner 2026-10-30: the row's words lead the table, items are not heroes, no "How" column (a "?" on the ability),
    a long list in two pairs of columns."""
    import patch.mech_abilities as ma
    from patch.state import _State
    keep = _State.current_patch_version
    _State.current_patch_version = "7.37"
    try:
        html, notes = ma.hero_ability_rows("Town Portal Scroll<br>Chen: Divine Favor<br>Visage: Summon Familiars "
                                           "recall (Faithful Followers)", row_text="The following are considered a "
                                           "Teleport")
        long_raw = "<br>".join(["Alchemist: Greevil's Greed", "Batrider: Smoldering Resin", "Bloodseeker: Thirst",
                                "Bounty Hunter: Jinada", "Chaos Knight: Reins of Chaos", "Clockwerk: Armor Power",
                                "Crystal Maiden: Cold Comfort", "Dark Seer: Heart of Battle", "Dark Willow: Pixie Dust",
                                "Death Prophet: Witchcraft", "Enigma: Gravity Well", "Faceless Void: Distortion Field"])
        long_html, _n = ma.hero_ability_rows(long_raw)
        # one row per hero, his abilities side by side (owner 2026-10-30: "не дублируй героя")
        oracle, _n = ma.hero_ability_rows("Oracle: Clairvoyant Curse<br>Oracle: Clairvoyant Cure")
    finally:
        _State.current_patch_version = keep
    assert "The following are considered a Teleport:" in html and "mech-captioned" in html
    # items are rows as heroes are (owner 2026-10-30), the header says both
    assert 'mech-hero mech-hero-item' in html and "Town Portal Scroll" in html and ">Hero or item<" in html
    assert ">How<" not in html and "info-tip" in html                 # Visage's "recall (Faithful Followers)"
    assert "mech-cols-hero4" in long_html
    assert oracle.count('class="mech-hero"') == 1 and "Clairvoyant Curse" in oracle and "Clairvoyant Cure" in oracle


def test_roshans_drops_link_to_their_changes_pages():
    row = ('W(li("Starting from his third death Roshan now drops Refresher Shard and Cheese during daytime or '
           'Aghanim\'s Blessing during night", t("REWORK")))')
    out = g._link_items(row)
    assert out.count("item_link(") == 3 and 'item_link("Aghanim\'s Blessing")' in out
    from patch.item_links import item_page
    assert item_page("Aghanim's Blessing") == "ultimate-scepter-2" and item_page("Refresher Shard") == "refresher-shard"


@pytest.mark.parametrize("line, label", [
    ("Chen: Divine Favor", "Chen: Divine Favor"),                     # Valve's 7.37 form "Hero: Ability"
    ("Twin Gates", "Twin Gates"),                                     # a map object among items
    ("Town Portal Scroll", "Town Portal Scroll"),
    ("Batrider: Smoldering Resin", "Batrider: Smoldering Resin"),     # a 7.37 innate gone since: the patch's files
    ("Dark Seer: Heart of Battle", "Dark Seer: Heart of Battle"),     # a facet's ability: the facet's icon
    ("Rubick: Might and Magus", "Rubick: Might and Magus"),           # "and" inside a name
    ("Beastmaster: Call of the Wild Hawk Dive Bomb", "Beastmaster: Call of the Wild Hawk"),
    ("Lone Druid: Spirit Bear's Return", "Lone Druid: Spirit Bear's Return"),
])
def test_7_37_list_lines_get_an_icon(line, label):
    import patch.mech_abilities as ma
    from patch.state import _State
    keep = _State.current_patch_version
    _State.current_patch_version = "7.37"
    try:
        parsed = ma._parse_line(line)
    finally:
        _State.current_patch_version = keep
    assert parsed and parsed[0] == label and parsed[1]


def test_an_item_that_trades_one_stat_for_another_gets_its_stats_card():
    """Owner 2026-10-30, 7.37 Bracer: "Now provides +50/100 Health" + "No longer provides +3/6 Damage" — a card."""
    lines = ['W(item_header("Bracer"))', 'W(ul_open())', 'W(li("Now provides +50/100 Health", t("NEW")))',
             'W(li("No longer provides +3/6 Damage", t("DEL")))', 'W(ul_close())']
    out = g._postprocess_properties_change(lines)
    assert out[1] == 'W(properties_change(old=[("DEL", "+3/6 Damage")], new=[("NEW", "+50/100 Health")]))'


def test_a_returning_neutral_item_is_labelled_in_its_header_and_described_as_new():
    """Owner 2026-10-30 ("смотри примеры в 7.38"): "Returning as a Tier 1 Neutral item" → the header's label, the
    description rows NEW."""
    lines = ['W(item_header("Ironwood Tree", new="Returning Tier 1 Neutral Item"))', 'W(ul_open())',
             'W(li("Provides +5 to All Attributes. Use: Plant Tree", t("MISC")))', 'W(ul_close())',
             'W(item_header("Vambrace"))', 'W(ul_open())', 'W(li("Something", t("MISC")))', 'W(ul_close())']
    out = g._postprocess_returning_rows(lines)
    assert 't("NEW")' in out[3] and 't("MISC")' in out[7]          # out[1]: its provides() line


def test_a_returning_items_provides_row_is_its_stats_and_its_ability_card():
    """Owner 2026-10-30 (7.38 Pyrrhic Cloak / Fallen Sky, 7.41 new items): "Provides +5 to All Attributes. Use: Plant
    Tree. …" → provides('+5 All Attributes') under the header and the row "Active: Plant Tree. …" (the ability card)."""
    lines = ['W(item_header("Ironwood Tree", new="Returning Tier 1 Neutral Item"))', 'W(ul_open())',
             'W(li("Provides +5 to All Attributes. Use: Plant Tree. Plants a happy little tree. Cooldown: 15s", '
             't("MISC")))', 'W(ul_close())',
             'W(item_header("Iron Talon", new="Returning Tier 2 Neutral Item"))', 'W(ul_open())',
             'W(li("Provides +20 Attack Speed and +4 Armor. Active: Chop. Removes 80% HP", t("MISC")))', 'W(ul_close())']
    out = g._postprocess_returning_rows(lines)
    assert out[1] == 'W(provides("+5 All Attributes"))'
    assert out[3] == 'W(li("Active: Plant Tree. Plants a happy little tree. Cooldown: 15s", t("NEW")))'
    assert 'W(provides("+20 Attack Speed, +4 Armor"))' in out and any(ln.startswith('W(li("Active: Chop.') for ln in out)


def test_two_stat_sentences_in_one_row_and_a_stat_that_was_there():
    """7.37 Spirit Vessel "No longer provides +6 All Attributes. Now provides +375 Health": one stat gone, and Health it
    had (+125) grew — "+125 Health" → "+375 Health", not both stats gone (owner 2026-10-30: "не хватает других ха-к")."""
    lines = ['W(item_header("Spirit Vessel", changed=True))', 'W(auto_components_change("Spirit Vessel", "7.37"))',
             'W(ul_open())', 'W(li("No longer provides +6 All Attributes. Now provides +375 Health", t("DEL")))',
             'W(ul_close())']
    out = g._postprocess_properties_change(lines, version="7.37")
    card = next(ln for ln in out if ln.startswith("W(properties_change("))
    assert card == ('W(properties_change(old=[("BUFF", "+125 Health"), ("DEL", "+6 All Attributes")], '
                    'new=[("", "+375 Health", b(125, 375))]))')


def test_a_multiplier_in_an_item_card_is_marked():
    """7.37 Bloodpact "by 2.5x" → "by 4x": the card's new number takes its row's colour, as a plain number does."""
    import re
    src = open(g.__file__.replace("tools", "patch").replace("generate_patch_code_v2.py", "cards_item_abilities.py"),
               encoding="utf-8").read()
    assert re.search(r"\(\?:%\|s\|x\)\?\)</b>'", src)


def test_a_rows_known_fact_stays_after_a_rewrap():
    lines = ['W(li("Teleport time to Roshan\'s outposts decreased from 6s to 4s", b(6, 4)))']
    assert "corner outposts" in g._postprocess_row_notes(lines)[0]


def test_no_page_keeps_the_old_facet_placeholder():
    from pathlib import Path
    pages = Path(__file__).resolve().parents[1].glob("content/p*.py")
    left = [p.name for p in pages if "TODO: the facet as it was in the previous patch" in p.read_text(encoding="utf-8")]
    assert left == []


def test_two_lists_back_to_back_become_one():
    lines = ['W(ul_open())', 'W(li("a"))', 'W(ul_close())', 'W(ul_open())', 'W(li("b"))', 'W(ul_close())']
    assert g._merge_adjacent_lists(lines) == ['W(ul_open())', 'W(li("a"))', 'W(li("b"))', 'W(ul_close())']


def test_a_facet_prefix_with_the_word_facet_and_an_old_abilitys_real_slug():
    """"Cold Comfort Facet: Blueheart Floe: …" is the facet Cold Comfort; "Selemene's Favor: Ability removed" is the
    7.36 innate luna_selemenes_favor (from the files), not a made-up luna_selemene_s_favor."""
    cm = "\n".join(g._render_hero({"hero_id": 5, "hero_notes": [{"indent_level": 1, "note":
         "Cold Comfort Facet: Blueheart Floe: Now also increases mana regen amplification from 50% to 75%"}]},
         version="7.37"))
    assert 'facet_header("crystal_maiden_cold_comfort")' in cm and "Cold Comfort Facet" not in cm
    luna = "\n".join(g._render_hero({"hero_id": 48, "hero_notes": [
        {"indent_level": 1, "note": "Selemene's Favor: Ability removed"}]}, version="7.37"))
    assert 'slug="luna_selemenes_favor"' in luna
