"""Guards item cards: stats cards, prices, returning and moved neutral items, enchantment tables, recipes.
"""

import importlib
import os
import pytest
import re
import sys
import tools.generate_patch_code_v2 as g
from patch import elements
from patch.css_bundle import read_css
from patch.js_bundle import read_js
from patch.state import _State, reset_page_state
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ---- second review of 2026-11-08 (audit before 7.42) ----

def _page(v):
    html = ROOT / "dist" / "patches" / f"{v}.html"
    if not html.exists():
        pytest.skip("no build")
    return html.read_text(encoding="utf-8")


sys.path.insert(0, str(ROOT / "tools"))
_ROOT_card_fixes_1026 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_a_recipe_side_stays_on_one_line():
    # owner 2026-11-06, 7.38 Battle Fury: "часть с рецептом в новой карточке уехала на другую строчку"
    from patch.css_bundle import read_css
    css = read_css()
    assert "  .components-change .components-row { flex-wrap: nowrap; min-width: 0; }" in css
    assert "  .components-change .component img { max-width: 100%; height: auto; aspect-ratio: 4 / 3; }" in css


def test_an_item_card_that_hides_no_row_is_not_drawn():
    # owner 2026-11-07, 7.38 Bloodthorn: "излишне тут карточки, т.к предмет особо не менялся"
    from patch.page import drop_cards_hiding_nothing
    block = '<div class="entity-block item-block">'
    shown = '<li data-tag="nerf"><span class="row-text">x</span></li>'
    hidden = '<li data-tag="nerf" class="iab-covered covered-iab"><span class="row-text">y</span></li>'
    page = (f'{block}<!--IABCARD:a--><ul class="changes">{shown}</ul></div>'
            f'{block}<!--IABCARD:b--><ul class="changes">{shown}{hidden}</ul></div>')
    out = drop_cards_hiding_nothing(page)
    assert "<!--IABCARD:a-->" not in out and "<!--IABCARD:b-->" in out


def test_a_qol_row_of_an_item_stays_shown_under_its_card():
    # 7.38 Bloodthorn: "Soul Rend silence visual … tinted red" was hidden as if the card said it ("забыл строку")
    import pytest
    page = ROOT / "dist" / "patches" / "7.38.html"
    if not page.exists():
        pytest.skip("the site is not built")
    html = page.read_text(encoding="utf-8")
    row = html[:html.index("Soul Rend silence visual above affected targets")]
    assert "iab-covered" not in row[row.rindex("<li"):]
    block = html[html.index('id="dyn-item-bloodthorn"'):]
    assert "iab-change" not in block[:block.index('<div class="entity-block')]


def test_the_enchantment_table_has_lines_at_both_ends_and_between_bonuses():
    # "в ней не хватает разделителей … по правилам построения таблиц они должны быть"
    css = (ROOT / "src" / "css" / "patch-new-items.css").read_text(encoding="utf-8")
    block = css[css.index("body.patch-page .enchant-list-head .ench-tiers {") - 400:]
    assert "border-left: 1px solid rgba(254, 247, 232, 0.10);" in block
    assert "border-right: 1px solid rgba(254, 247, 232, 0.10);" in block
    assert ".enchant-list-row .ench-tiers > .ench-v + .ench-stat ~ .ench-v { border-top:" in css


def test_a_short_enchant_label_hides_its_row_under_the_card():
    # 7.41e Greedy: "GPM Bonus decreased from +75/100 to +65/90" stood as a row under the card showing it
    text = _page("7.41e")
    i = text.index("GPM Bonus decreased from +75/100 to +65/90")
    li_open = text.rfind("<li", 0, i)
    assert "iab-covered" in text[li_open:i]


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


def test_an_item_moved_to_another_tier_gets_its_cards():
    """Owner 2026-10-30, 7.37 Vambrace / Ogre Seal Totem "Now a Tier N Neutral Item": cards as any item's."""
    lines = ['W(item_header("Vambrace", new="Now a Tier 3 Neutral Item"))', 'W(ul_open())',
             'W(li("Main Attribute bonus increased from +8 to +10", b(8, 10)))',
             'W(li("Strength Magic Resistance bonus increased from +8% to +10%", b(8, 10)))', 'W(ul_close())']
    out = g._postprocess_properties_change(lines, version="7.37")
    assert out[1].startswith('W(properties_change(old=[("BUFF", "+8 Main Attribute"), ("BUFF", "+8% Strength Magic')
    assert g._guess_tag("Now has 750 charges, and depletes a charge every time it grants gold to the owner") == "REWORK"


def test_a_multiplier_in_an_item_card_is_marked():
    """7.37 Bloodpact "by 2.5x" → "by 4x": the card's new number takes its row's colour, as a plain number does."""
    import re
    src = open(g.__file__.replace("tools", "patch").replace("generate_patch_code_v2.py", "cards_item_abilities.py"),
               encoding="utf-8").read()
    assert re.search(r"\(\?:%\|s\|x\)\?\)</b>'", src)


def test_pirate_hat_is_reworked_with_a_card_and_a_row():
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    block = text[text.index('W(item_header("Pirate Hat"'):text.index('W(item_header("Spider Legs"')]
    assert 'changed="Reworked Tier 5 Artifact"' in block and "Active: Dig." in block and "Passive: Plunder." in block
    assert "W(li(" not in block


def test_the_generator_writes_pirate_hats_header_itself():
    src = (ROOT / "tools" / "patchgen" / "entities.py").read_text(encoding="utf-8")
    assert """changed="Reworked {tier.group(1)} Artifact\"""" in src


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


def test_ringmasters_souvenir_rows():
    assert g._guess_tag("If Ringmaster does not have a Souvenir, he will be granted one upon death (instead of upon "
                        "respawn)") == "NEW"
    assert g._guess_tag("Ringmaster will no longer be granted a Souvenir if he has no Souvenirs and dies to a Neutral "
                        "Creep or Roshan") == "DEL"


def test_removed_items_grey_aghs_panes_on_top_and_a_gone_enchant_value_struck():
    css = read_css()
    # an item taken out of the game: icon and name greyed (the label and the patch strip keep their colours)
    assert re.search(r"\.entity-block\.is-removed \.entity-icon img \{[^}]*grayscale", css)
    assert re.search(r"\.entity-block\.is-removed \.entity-name > \.entity-link", css)
    # Aghanim's card panes top-anchored: the caption stays by the card (7.41 Techies)
    rule = re.search(r"\.ability-change-block \.ability-change\.unified-panes\.aghs-change > \.ability-change-pane"
                     r"\s*\{([^}]*)\}", css)
    assert "align-self: start" in rule.group(1)
    # a bonus an enchantment lost: its old value struck, no "→ —" (7.41 Mystical Cast Range)
    assert '" → —"' not in css
    assert re.search(r"\.ench-tiers\.ench-change \.iab-lv\.iab-del \{[^}]*line-through", css)
    # ... and its name struck too, no cross before it; "was" and "now" one size (owner, the same day, 7.39 Alert)
    assert not re.search(r"\.ench-gone::before \{[^}]*content", css)
    assert re.search(r"\.ench-change \.ench-stat\.ench-gone \{[^}]*line-through", css)
    assert re.search(r"\.ench-change \.ench-was \{[^}]*font-size: inherit", css)
    # the arrow of a top-anchored card stands at its shorter side's middle (7.41 Techies; 2026-11-07 any such card)
    js = read_js()
    assert ".ability-change.unified-panes" in js and "arrow.style.marginTop" in js


def test_older_enchant_tables_take_the_patchs_own_labels_and_tiers():
    import json
    have = json.load(open(os.path.join(_ROOT_card_fixes_1026, "data", "rules", "enchant_tables.json"), encoding="utf-8"))
    mystical = {s["label"]: s for s in have["7.39"]["Mystical"]["stats"]}
    # 7.39's third value is Cast Range (today's text says Mana Cost/Loss Reduction there)
    assert mystical["Cast Range"]["new"]["4"] == "+100" and "Mana Cost/Loss Reduction" not in mystical
    assert have["7.39"]["Vampiric"]["tiers_new"] == [2, 3, 4]        # from neutral_items.txt, no tier boxes on the page


def test_enchant_change_table_heads_its_stats_column():
    import re
    from pathlib import Path
    import pytest
    page = Path(__file__).resolve().parents[1] / "dist" / "patches" / "7.41.html"
    if not page.exists():
        pytest.skip("site not built")
    html = page.read_text(encoding="utf-8")
    assert re.search(r'class="ench-tiers ench-change"><span class="ench-row-h"><span class="ench-stat-h">Stats</span>',
                     html)


def test_renamed_item_header_shows_old_arrow_new():
    from patch import elements as el
    html = el.item_header("Orb of Blight", old_title="Blight Stone")
    assert ('<span class="ability-title-old">Blight Stone</span><span class="ability-title-arrow">→</span>'
            '<a class="entity-link"') in html
