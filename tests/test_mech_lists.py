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
    assert ('table=mech_table(["Attack", "Item Potency", mech_example("Desolator") + " Desolator armor reduction"], '
            '[[mech_example("Evolved Enchantment") + " Evolved Enchantment", \'<span class="pot-bar" style="--pot:100%">'
            '120%</span>\', "7.2"], ["Any Hero", \'<span class="pot-bar" style="--pot:83%">100%</span>\', "6"], '
            '[mech_example("Pangolier\'s Swashbuckle") + " Pangolier\'s Swashbuckle", \'<span class="pot-bar" '
            'style="--pot:50%">60%</span>\', "3.6"], ["Standard Illusion", \'<span class="pot-bar" style="--pot:17%">'
            '20%</span>\', "1.2"]], cls="mech-grid")))') in story


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
    assert "\"Illusions still don't apply: \" + icons_with_notes([('Skull Basher', 'Bash'), ('Abyssal Blade', 'Bash')" in story
    assert story.split("icons_with_notes(")[1].count("), (") == 15                # 16 items


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
    assert 'readonly' not in old and 'class="formula-input fx-mirror"' in new and 'readonly tabindex="-1"' in new
