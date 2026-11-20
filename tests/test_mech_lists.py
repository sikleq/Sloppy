"""General blocks that point at other notes get those notes as a table (owner 2026-11-20, 7.42)."""
import pytest

from tools.patchgen.post_mech_lists import (_postprocess_breakability_list, _postprocess_item_potency,
                                            _postprocess_spell_power_list)


def test_breakability_rows_become_one_row_with_the_innates_grouped_by_how():
    out = _postprocess_breakability_list([
        'W(plain_header("Spell Mechanics", new="Reworked mechanic"))', 'W(ul_open())',
        'W(li("Breakability rules of many innates updated", t("REWORK"), force_tag="rework misc"))',
        'W(li("Specifics for this changes can be found in the corresponding ability notes", t("REWORK"), force_tag="rework misc"))',
        'W(ul_close())',
        'W(hero_header("Leshrac"))', 'W(ability("Defilement", slug="leshrac_defilement", innate=True))', 'W(ul_open())',
        'W(li("Now fully disabled by Break", t("NERF")))', 'W(ul_close())',
        'W(hero_header("Techies"))', 'W(ability("M.A.D.", slug="techies_mad", innate=True))', 'W(ul_open())',
        'W(li("Now partially disabled by Break: disables the mana regen, but not the barrel on death", t("NERF")))',
        'W(ul_close())',
        'W(ability("Sticky Bomb", slug="techies_sticky_bomb"))', 'W(ul_open())',
        'W(li("Now fully disabled by Break", t("NERF")))', 'W(ul_close())'])
    assert not any("Specifics for" in ln for ln in out)               # the pointer row is gone
    row = out[2]
    assert row.startswith('W(li("Breakability rules of many innates updated", t("REWORK"), force_tag="rework nerf"')
    assert ("Leshrac's Defilement Fully disabled by Break<br>Techies's M.A.D. Partially disabled by Break "
            "(disables the mana regen, but not the barrel on death)") in row
    assert "Sticky Bomb" not in row                                     # not an innate


def test_breakability_row_without_any_innate_stops_the_generator():
    with pytest.raises(ValueError):
        _postprocess_breakability_list(['W(li("Breakability rules of many innates updated", t("REWORK")))'])


def test_spell_power_pointer_row_becomes_the_marked_changes_by_kind():
    mark = 'extra=inline_note("As a part of the comprehensive Spell Power Reduction")'
    out = _postprocess_spell_power_list([
        'W(plain_header("Spell Power Reduction", new="Reworked mechanic"))', 'W(ul_open())',
        'W(li("Decreased damage of the majority of Magic and Pure damage spells", t("REWORK")))',
        'W(li("Specifics for any of these changes can be found in the corresponding ability or item notes", t("REWORK")))',
        'W(ul_close())',
        'W(item_header("Aether Lens"))', 'W(ul_open())', f'W(li("Cast Range bonus decreased from +225 to +200", b(225, 200), {mark}))',
        'W(ul_close())',
        'W(hero_header("Bounty Hunter"))', 'W(ability("Track", slug="bounty_hunter_track"))', 'W(ul_open())',
        f'W(li("Damage Amplification decreased from 8/12/16% to 6/10/14%", b(1, 0), {mark}))', 'W(ul_close())',
        'W(hero_header("Lina"))', 'W(ability("Laguna Blade", slug="lina_laguna_blade"))', 'W(ul_open())',
        f'W(li("Damage decreased from 400/580/760 to 360/525/690", b(1, 0), {mark}))', 'W(ul_close())'])
    # Valve's rows of the block are not the known three: they stay, the table is a row of its own
    row = next(ln for ln in out if "marked_changes(" in ln)
    assert row.startswith('W(li("Changes marked as a part of it in this patch"')
    assert 'W(li("Decreased damage of the majority of Magic and Pure damage spells", t("REWORK")))' in out
    assert not any("Specifics for" in ln for ln in out)
    # "Damage Amplification" is an amplification, not damage: the first kind that matches wins
    assert ("('Spell and damage amplification', [('hero', 'Bounty Hunter', 'Track', 'Damage Amplification decreased "
            "from 8/12/16% to 6/10/14%')])") in row
    assert "('Area of effect and cast range', [('item', 'Aether Lens', None, 'Cast Range bonus" in row
    assert "('Damage', [('hero', 'Lina', 'Laguna Blade'," in row


def test_spell_power_known_rows_become_one_sentence_with_the_table():
    mark = 'extra=inline_note("As a part of the comprehensive Spell Power Reduction")'
    out = _postprocess_spell_power_list([
        'W(plain_header("Spell Power Reduction", new="Reworked mechanic"))', 'W(ul_open())',
        'W(li("Decreased most item contributions to ability scaling, including Spell Amplification, Area of Effect, and '
        'Cast Range", t("REWORK")))',
        'W(li("Decreased damage of the majority of Magic and Pure damage spells", t("REWORK")))',
        'W(li("Decreased duration of some long duration slows", t("REWORK")))',
        'W(li("Specifics for any of these changes can be found in the corresponding ability or item notes", t("REWORK")))',
        'W(ul_close())',
        'W(hero_header("Lina"))', 'W(ability("Laguna Blade", slug="lina_laguna_blade"))', 'W(ul_open())',
        f'W(li("Damage decreased from 400/580/760 to 360/525/690", b(1, 0), {mark}))', 'W(ul_close())'])
    assert out[2].startswith('W(li("Decreased most item contributions to ability scaling (Spell Amplification, Area '
                             'of Effect and Cast Range), the damage of most Magic and Pure damage spells and the '
                             'duration of some long slows", t("REWORK"), force_tag="rework nerf", extra=marked_changes(')
    assert out[3] == 'W(ul_close())'


def test_marked_changes_one_icon_per_ability_its_changes_and_their_pct_on_hover():
    from patch.mech_marked import marked_changes
    html = marked_changes([("Damage", [("hero", "Timbersaw", "Chakram", "Pass Damage decreased from 75/150/225 to 70/140/210"),
                                       ("hero", "Timbersaw", "Chakram", "Damage per second decreased from 50/75/100 to 50/70/90"),
                                       ("hero", "Kunkka", "Talents", "Level 25 Talent Spell Area of Effect decreased")])])
    assert html.count('aria-label="Chakram"') == 1                              # two changes, one icon
    assert "Pass Damage decreased" in html and "Damage per second decreased" in html
    from patch.mech_marked import _pct_html
    assert "−25% per level" in _pct_html("Max Damage/Heal Amp decreased from 4% + 0.4% per level to 4% + 0.3% per level")
    assert "−20%" in _pct_html("Cold Attack slow decreased from 25/50% (melee/ranged) to 20/40% (melee/ranged)")
    # a little table: the change left, its % right; the name over it set apart
    assert 'tip-head' in html and 'tb-tip-table' in html and "&lt;td&gt;Pass Damage decreased" in html
    assert "−7%" in html and "iab-nerf" in html                                 # 75 → 70: its % coloured
    assert "<b>" not in html.split("Damage</span>")[0]                           # no count after the kind
    assert 'href="#dyn-hero-timbersaw"' in html and "talents.svg" in html       # a talent of no one ability: the tree
    with pytest.raises(ValueError):                                              # no icon: no silent hole in the count
        marked_changes([("Damage", [("item", "No Such Item", None, "x")])])


def test_item_potency_title_links_its_page_and_examples_become_a_table():
    out = _postprocess_item_potency([
        'W(plain_header("Item Potency", new="Reworked mechanic"))', 'W(ul_open())',
        'W(mech_story(["Attacks … now have an attribute called Item Potency.", "The default Item Potency value for an '
        'attack is 100%. For example: any hero … (6 × 120%); attacks from … (6 × 60%). Illusions have a default Item '
        'Potency of 20% and can now apply most item on hit effects (excluding X and a few other items. Specific details '
        'can be found in the associated item and ability changes)."], tags=("rework",)))',
        'W(li("The default Item Potency value for an attack is 100%", t("REWORK"), covered=True))',
        'W(li("Any hero attacking with a Tier 4 Evolved Enchantment has +20% Item Potency, so if they have a Desolator '
        'the attack would reduce armor by 7.2", t("REWORK"), extra=inline_note("6 * 120%"), covered=True))',
        'W(li("Attacks from Pangolier’s Swashbuckle now have 60% Item Potency, so if he has a Desolator the strikes would '
        'reduce armor by 3.6", t("REWORK"), extra=inline_note("6 * 60%"), covered=True))',
        'W(li("Illusions have a default Item Potency of 20% and can now apply most item on hit effects", t("REWORK"), covered=True))',
        'W(ul_close())'])
    assert out[0] == 'W(plain_header("Item Potency", new="Reworked mechanic", page="item_potency.html"))'
    story = out[2]
    assert "For example" not in story and "Specific details" not in story and "(excluding X and a few other items)." in story
    # the defaults first, then own potency, then a bonus; the item named alone in the head; how potencies add up last
    assert ('table=mech_table(["Attack", "Item Potency", "Desolator armor reduction"], '
            '[["Any Hero", \'<span class="pot-bar" style="--pot:83%">100%</span>\', "6"], '
            '["Standard Illusion", \'<span class="pot-bar" style="--pot:17%">20%</span>\', "1.2"], '
            '[mech_example("Pangolier\'s Swashbuckle") + " Swashbuckle", \'<span class="pot-bar" '
            'style="--pot:50%">60%</span>\', "3.6"], '
            '[mech_example("Evolved Enchantment") + " Evolved Enchantment", \'<span class="pot-bar" style="--pot:100%">'
            '120%</span>\', "7.2"]], cls="mech-grid") + mech_table(["How Item Potency adds up"], '
            '[mech_formula(\'Own * (100 + Bonuses) / 100\')])))') in story


def test_item_potency_names_every_item_illusions_still_dont_apply():
    # Valve: "(excluding Skull Basher and a few other items …)"; the game's code names all 16 (data/rules)
    out = _postprocess_item_potency([
        'W(plain_header("Item Potency", new="Reworked mechanic"))', 'W(ul_open())',
        'W(mech_story(["… now have an attribute called Item Potency.", "Illusions have a default Item Potency of 20% '
        'and can now apply most item on hit effects (excluding " + mech_example("Skull Basher", label="Skull Basher") '
        '+ " and a few other items. Specific details can be found in the associated item and ability changes)."], '
        'tags=("rework",)))',
        'W(li("Any hero attacking with a Tier 4 Evolved Enchantment has +20% Item Potency, so if they have a Desolator '
        'the attack would reduce armor by 7.2", t("REWORK"), extra=inline_note("6 * 120%"), covered=True))',
        'W(ul_close())'], "7.42")
    story = out[2]
    assert "can now apply most item on hit effects.\"]" in story and "excluding" not in story
    assert "illusion_excluded_table([('Skull Basher', 'Bash', 'item'), ('Abyssal Blade', 'Bash', 'item')" in story
    assert story.split("illusion_excluded_table(")[1].count("), (") == 15         # 16 items
    assert "('Mind Breaker', 'Silence Strike and its magic damage', 'neutral')" in story


def test_illusion_excluded_table_puts_items_and_neutral_items_in_two_columns_under_its_caption():
    from patch.mech_marked import illusion_excluded_table
    html = illusion_excluded_table([("Skull Basher", "Bash", "item"), ("Maelstrom", "Chain Lightning", "item"),
                                    ("Heavy Blade", "Subjugate", "neutral")])
    assert 0 <= html.find("Illusions still don") < html.find(">Items<")           # the caption over the titles
    assert ">Neutral items<" in html and html.count('class="mech-abil-row"') == 2   # caption + one row of icons
    assert "mech-abil-name" not in html                                         # icons only, names on hover


def test_primal_split_rows_of_one_brewling_go_to_its_block():
    from tools.patchgen.post_summons import _postprocess_brewlings
    out = _postprocess_brewlings([
        'W(ability("Primal Split", slug="brewmaster_primal_split"))', 'W(ul_open())',
        'W(li("Earth\'s Health decreased from 1400 to 1300", b(1400, 1300)))',
        'W(li("Fire now has Cinder Dash ability", t("NEW")))', 'W(ul_close())'])
    assert out == ['W(ability("Primal Split", slug="brewmaster_primal_split"))',
                   'W(ability("Earth Brewling", slug="brewmaster_earth_unit", '
                   'icon_url="../icons/units/brewmaster_earth_unit.png"))', 'W(ul_open())',
                   'W(li("Health decreased from 1400 to 1300", b(1400, 1300)))', 'W(ul_close())',
                   'W(ability("Fire Brewling", slug="brewmaster_fire_unit", '
                   'icon_url="../icons/units/brewmaster_fire_unit.png"))', 'W(ul_open())',
                   'W(li("Now has Cinder Dash ability", t("NEW")))', 'W(ul_close())']


def test_a_narrower_damage_spread_is_better():
    import sys
    sys.path.insert(0, "tools")
    from patch.elements import _pop_hint_value
    from patchgen.tags import _is_lower_better
    assert _is_lower_better("Damage spread decreased from 20 to 10")
    assert "iab-hl-buff" in _pop_hint_value("Damage spread decreased from 20 to 10")


def test_owner_tags_of_2026_11_20():
    from tools.patchgen.tags import _guess_tag
    assert _guess_tag("Now applies only from attack and ability damage") == "REWORK"
    assert _guess_tag("No longer has a separate health threshold at which it takes effect") == "DEL"
    assert _guess_tag("Buff is now undispellable") == "NEW"                     # the bare row (Alchemist)
    assert _guess_tag("Shield is now undispellable") == "BUFF"                  # the canon stays


def test_neutral_tiers_parse_and_table_before_after():
    from tools.patchgen.post_mech_lists import _tier_table, neutral_tiers
    old = ('"neutral_items"\n{\n\t"madstone_limits"\n\t{\n\t\t"madstone_no_limit_time"\t"70:00"\n\t}\n\t"neutral_tiers"\n\t{\n'
           '\t\t"1"\n\t\t{\n\t\t\t"start_time"\t"0:00"\n\t\t\t"craft_cost"\t"6"\n\t\t\t"items"\n\t\t\t{\n\t\t\t\t"item_a"\t"1"\n'
           '\t\t\t}\n\t\t}\n\t\t"2"\n\t\t{\n\t\t\t"start_time"\t"60:00"\n\t\t\t"craft_cost"\t"10"\n\t\t\t"recraft_cost"\t"10"\n'
           '\t\t}\n\t}\n}\n')
    tiers, free = neutral_tiers(old)
    assert tiers == {1: {"start_time": "0:00", "craft_cost": "6"},
                     2: {"start_time": "60:00", "craft_cost": "10", "recraft_cost": "10"}} and free == "70:00"
    table = _tier_table((tiers, free), ({1: {"start_time": "0:00", "craft_cost": "6"}}, "65:00"))
    assert "*mech_change_cells('60:00', '—', l=True)" in table                # a tier gone
    assert '["Infinite Madstone", *mech_change_cells(\'70:00\', \'65:00\', l=True)' in table
    assert 'mech_example("Madstone Bundle") + " Madstone cost"' in table and "mech-change-grid" in table


def test_one_rule_in_several_rows_becomes_one_sentence_with_its_table():
    from tools.patchgen.post_mech_lists import _postprocess_one_sentence_blocks
    out = _postprocess_one_sentence_blocks([
        'W(ul_open())',
        'W(li("Options for a tier are no longer randomly rolled amongst all the items available for a tier", t("MISC")))',
        'W(li("Each tier is now separated into multiple pools of Artifacts, and 1 Artifact is chosen per pool", t("MISC"), '
        'extra=artifact_pools([])))',
        'W(li("All options for every tier are now decided at the beginning of the game", t("MISC"), '
        'extra=inline_note("Neutral Options can be seen in the Neutrals tab in the shop")))',
        'W(ul_close())'])
    assert len(out) == 3 and out[1].startswith('W(li("Each tier is now separated into multiple pools of Artifacts and 1 '
                                               'Artifact is chosen per pool, instead of a random roll')
    assert 't("REWORK"), extra=artifact_pools([]) + inline_note("Neutral Options can be seen' in out[1]


def test_pip_buttons_stand_over_every_table_of_the_story(monkeypatch):
    from patch.api import mech_story, mech_table, pip_story_list
    from patch.state import _State
    monkeypatch.setattr(_State, "current_patch_version", "7.42")
    html = mech_story(["Pips."], tags=("rework",),
                      table=mech_table(["Attacks from", "Damage per attack"], [["Heroes", "1 full pip"]])
                      + pip_story_list("Couriers<br>Observer Wards<br>Zeus: Nimbus"))
    assert html.index('class="pip-bar"') < html.index(">Attacks from<") < html.index("pip-table")
    assert 'class="mech-story-table pip-block"' in html and html.count("pip-block") == 1


def test_pip_story_base_rules_are_a_table_and_a_bracket_of_listed_names_goes():
    from tools.patchgen.general import _story_of
    group = [{"note": "All units are now able to damage units with health bar pips", "indent_level": 1,
              "info": "* Couriers<br>* Zeus: Nimbus"},
             {"note": "Attacks from heroes, Roshan, towers, and the fountain deal 1 full pip per attack", "indent_level": 2},
             {"note": "Attacks from illusions and creeps deal 1/4 pip per attack", "indent_level": 2},
             {"note": "Some units have a Fragile debuff", "indent_level": 1, "info": "Courier, Zeus's Nimbus"}]
    out = _story_of(group, "REWORK")
    assert "All units are now able to damage units with health bar pips." in out and "deal 1 full pip" not in out
    assert ('mech_table(["Attacks from", "Damage per attack"], [["Heroes, Roshan, towers, and the fountain", '
            '"1 full pip"], ["Illusions and creeps", "1/4 pip"]]) + pip_story_list(') in out
    assert "Some units have a Fragile debuff." in out and "(Courier" not in out


def test_icons_with_notes_names_each_item_and_its_note_on_hover():
    from patch.mech_marked import icons_with_notes
    html = icons_with_notes([("Skull Basher", "Bash"), ("Audacious Enchantment", "Bonus magic damage on attack")])
    assert html.count('class="ability-chip abil-ico-hint"') == 2 and "&lt;br&gt;Bash" in html
    with pytest.raises(ValueError):
        icons_with_notes([("No Such Item", "x")])


def test_a_generic_innate_chip_shows_its_heros_face_and_its_own_words_on_hover(monkeypatch):
    from patch.mech_abilities import ability_list_rows
    from patch.state import _State
    monkeypatch.setattr(_State, "current_patch_version", "7.42")
    html, _notes = ability_list_rows("Leshrac's Defilement Fully disabled by Break<br>Techies's M.A.D. Partially "
                                     "disabled by Break (disables the mana regen)", least=1)
    assert "chip-hero-mini" in html                                              # Defilement has no icon of its own
    assert 'data-tooltip="&lt;b&gt;M.A.D.&lt;/b&gt;&lt;br&gt;Disables the mana regen"' in html
    assert "qhint" not in html                                                   # no "?" after the sentence


def test_the_second_pane_of_a_live_formula_mirrors_its_fields():
    from patch.formula_rows import formula_change
    html = formula_change("Hero kill bounty", "125 + 8 * VictimLevel", "100 + 10 * VictimLevel",
                          inputs={"VictimLevel": 10})
    old, new = html.split('formula-pane-new')
    # the second pane: the value as text, no field to click into (owner 2026-11-20)
    assert '<input' in old and '<input' not in new and 'class="fx-mirror" data-var="VictimLevel"' in new
