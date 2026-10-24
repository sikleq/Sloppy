"""tools/item_history.py: flattening, field diff, shop sections, patch/archive/build choice (no git needed)."""
from datetime import date, datetime, timedelta, timezone

from tools.item_history import (Clone, diff, flatten, old_notes_file, pick_archive, previous_version,
                                shop_sections)


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


def test_old_notes_file_name_before_7_19():
    assert old_notes_file("7.08").endswith("/patch_708.txt")
    assert old_notes_file("7.13b").endswith("/patch_713b.txt")


def test_pick_archive_newest_that_covers_the_day():
    starts = [date(2023, 3, 22), date(2016, 12, 11)]        # DOTA2_CLIENT, GameTracking
    assert pick_archive(date(2024, 1, 1), starts) == (0, False)
    assert pick_archive(date(2023, 3, 7), starts) == (1, False)     # 7.32e: GameTracking first, then the other
    assert pick_archive(date(2010, 1, 1), starts) == (1, True)


def _clone_with_notes(builds, notes):
    """A Clone without git: builds = [(sha, hours after start)], notes = {sha: {versions with notes}}."""
    c = Clone.__new__(Clone)
    t0 = datetime(2020, 6, 28, 23, 0, tzinfo=timezone.utc)
    c.commits = [(sha, t0 + timedelta(hours=h)) for sha, h in builds]
    c.item_commits = list(c.commits)
    c.has_notes = lambda sha, v: v in notes.get(sha, set())
    return c


def test_build_is_last_release_night_fix_not_first_notes_build():
    # 7.27: 4313 has the notes but old values, 4316 three hours later has the noted values
    c = _clone_with_notes([("pre", -2), ("4313", 0), ("4316", 3), ("4321", 13)],
                          {"4313": {"7.27"}, "4316": {"7.27"}, "4321": {"7.27"}})
    assert c.find_build("7.27", date(2020, 6, 28), None, "7.27a") == ("4316", "notes")


def test_build_never_takes_the_next_patchs_build():
    # 7.20b notes reached the game only together with 7.20c: no own build -> first items change of its day
    c = _clone_with_notes([("b1", 0), ("b2", 30), ("c1", 120)], {"c1": {"7.20b", "7.20c"}})
    assert c.find_build("7.20b", date(2020, 6, 28), date(2020, 7, 2), "7.20c") == ("b1", "date")
