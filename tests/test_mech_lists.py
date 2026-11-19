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
    row = out[3]
    assert row.startswith('W(li("Changes marked as a part of it in this patch"')
    # "Damage Amplification" is an amplification, not damage: the first kind that matches wins
    assert ("('Spell and damage amplification', [('hero', 'Bounty Hunter', 'Track', 'Damage Amplification decreased "
            "from 8/12/16% to 6/10/14%')])") in row
    assert "('Area of effect and cast range', [('item', 'Aether Lens', None, 'Cast Range bonus" in row
    assert "('Damage', [('hero', 'Lina', 'Laguna Blade'," in row


def test_marked_changes_table_counts_and_links_each_change():
    from patch.mech_marked import marked_changes
    html = marked_changes([("Damage", [("hero", "Lina", "Laguna Blade", "Damage decreased"),
                                       ("hero", "Kunkka", "Talents", "Level 25 Talent Spell Area of Effect decreased")])])
    assert "Damage <b>2</b>" in html
    assert 'href="#dyn-hero-lina"' in html and "talents.svg" in html          # a talent of no one ability: the tree
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
    assert ('table=mech_table(["Attack", "Item Potency", item_icon("Desolator") + " armor reduction"], '
            '[["Hero with Tier 4 " + mech_example("Evolved Enchantment") + " Evolved Enchantment", "120%", "7.2"], '
            '["Hero", "100%", "6"], [mech_example("Pangolier\'s Swashbuckle") + " Pangolier\'s Swashbuckle", "60%", "3.6"], '
            '["Illusion", "20%", "1.2"]], cls="mech-grid")))') in story
