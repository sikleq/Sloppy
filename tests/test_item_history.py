"""tools/item_history.py: flattening, field diff, shop sections and the previous-patch lookup (no git needed)."""
from tools.item_history import diff, flatten, previous_version, shop_sections


def test_flatten_nested_ability_values():
    node = {"ItemCost": "5300", "AbilityValues": {"cold_slow_melee": "-20", "bonus_mana": {"value": "150"}}}
    assert flatten(node) == {"ItemCost": "5300", "AbilityValues.cold_slow_melee": "-20",
                             "AbilityValues.bonus_mana.value": "150"}


def test_diff_lists_changed_added_removed_fields():
    old = {"a": "1", "b": "2", "gone": "x"}
    new = {"a": "1", "b": "3", "added": "y"}
    assert diff(old, new) == ["added: None -> 'y'", "b: '2' -> '3'", "gone: 'x' -> None"]


def test_shop_sections_keeps_every_repeated_item_key():
    text = '"dota_shops"\n{\n\t"consumables"\n\t{\n\t\t"item"\t\t"item_tango"\n\t\t"item"\t\t"item_clarity"\n\t}\n' \
           '\t"defense"\n\t{\n\t\t"item"\t\t"item_skadi" // comment\n\t\t"item"\t\t"item_tango"\n\t}\n}\n'
    assert shop_sections(text) == {"item_tango": ["consumables", "defense"], "item_clarity": ["consumables"],
                                   "item_skadi": ["defense"]}


def test_previous_version_is_next_entry_of_newest_first_history():
    history = [{"version": "7.38b"}, {"version": "7.38"}, {"version": "7.37e"}]
    assert previous_version("7.38b", history) == "7.38"
    assert previous_version("7.37e", history) is None
