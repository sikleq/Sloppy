"""Owner 2026-09-27: an item that has other changes shows its price change in the components card — the
recipe chip and "= total" coloured, the total's % at the end of the block — and the cost row under it is
hidden (still counted by tag filters and weights)."""
from patch import elements as el
from patch.state import _State


def _card(total_old, total_new, recipe_old, recipe_new, key="item|cost-test|7.41"):
    _State.current_entity_key, _State.current_patch_version = "item|cost-test", "7.41"
    return el.components_change(old=[("Javelin", 900)], new=[("Javelin", 900)],
                                total_old=total_old, total_new=total_new,
                                recipe_old=("Recipe", recipe_old), recipe_new=("Recipe", recipe_new))


def test_a_cost_row_whose_numbers_the_card_shows_is_hidden_and_the_card_gets_its_percent():
    saved = (_State.current_entity_key, _State.current_patch_version, _State.cost_card)
    try:
        slot = _card(4700, 5000, 600, 900)
        assert slot == "<!--COSTCARD:item|cost-test|7.41-->"
        assert el._cost_covered("Recipe cost increased from 600 to 900. Total cost increased from 4700g to 5000g")
        html = el.render_cost_card("item|cost-test|7.41")
        new = html.split("components-arrow")[1]
        assert 'component-price cost-nerf">900<' in new and 'class="cost-nerf">5000<' in new
        assert 'class="components-pct"' in new and "+6%" in new
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.cost_card = saved


def test_a_row_the_card_cannot_show_stays():
    saved = (_State.current_entity_key, _State.current_patch_version, _State.cost_card)
    try:
        _card(5200, 5900, 600, 1500)
        # Khanda 7.38: the notes' numbers differ from the game files the card is drawn from
        assert not el._cost_covered("Recipe cost increased from 500 to 1500. Total cost increased from 5100 to 5900")
        # Dagon 7.41: a total per level
        assert not el._cost_covered("Total cost increased from 5200/5300g to 5900/6000g")
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.cost_card = saved


def test_the_rows_reason_becomes_a_dotted_hint_on_the_total():
    saved = (_State.current_entity_key, _State.current_patch_version, _State.cost_card)
    try:
        _card(2250, 2250, 800, 1340)
        assert el._cost_covered("Recipe cost increased from 800 to 1340",
                                el.inline_note("Total cost unchanged at 2250 due to Iron Branch cost increase"))
        new = el.render_cost_card("item|cost-test|7.41").split("components-arrow")[1]
        assert 'data-tooltip="Total cost unchanged at 2250 due to Iron Branch cost increase">2250<' in new
        assert "components-pct" not in new                     # the total didn't change: no %
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.cost_card = saved


def test_generator_gives_a_components_card_only_to_an_item_with_other_changes():
    import generate_patch_code_v2 as g
    mkb = ['W(item_header("Monkey King Bar"))', 'W(properties_change(old=[], new=[("NEW", "+50 Attack Range")]))',
           "W(ul_open())", 'W(li("Recipe cost increased from 600 to 900. Total cost increased from 4700g to 5000g", '
           'b([600, 4700], [900, 5000], l=True, slash=True)))', "W(ul_close())"]
    out = g._postprocess_cost_components(mkb, "7.41")
    assert out[1] == 'W(auto_components_change("Monkey King Bar", "7.41"))'
    assert g._postprocess_cost_components(out, "7.41") == out                  # idempotent
    only_price = ['W(item_header("Daedalus"))', "W(ul_open())",
                  'W(li("Recipe cost increased from 900 to 1000. Total cost increased from 5100g to 5200g", '
                  'b([900, 5100], [1000, 5200], l=True, slash=True)))', "W(ul_close())"]
    assert g._postprocess_cost_components(only_price, "7.41f") == only_price  # the price is its only change
