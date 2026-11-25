"""Owner 2026-11-24: hero / item pages show the strength curve (running sum of patch weights) under the name;
hidden below 3 changed patches."""
import json

from builders import entity_changes as ec

DYN = {"patches": [{"version": "7.42"}, {"version": "7.41"}, {"version": "7.40"}, {"version": "7.39"}]}


def test_the_curve_lists_patches_old_to_new_with_their_weights():
    rec = {"patches": {"7.42": {"w": -1.5}, "7.40": {"w": 0.25}, "7.39": {"w": 2}}}
    html = ec._curve_box(rec, DYN)
    raw = html.split('data-curve="')[1].split('"')[0].replace("&quot;", '"')
    assert json.loads(raw) == [["7.39", 2.0], ["7.40", 0.25], ["7.42", -1.5]]


def test_no_curve_below_three_changed_patches():
    assert ec._curve_box({"patches": {"7.42": {"w": 1}, "7.39": {"w": 1}}}, DYN) == ""
    assert ec._curve_box({}, DYN) == ""


def test_martyrdom_is_a_current_chen_ability():
    # owner 2026-11-24: the Zealot gets Martyrdom from the game's code, it is not removed
    from patch.meta import latest_stats_version
    if not (ec._HERE / "data" / "stats" / latest_stats_version() / "heroes" / "npc_dota_hero_chen.txt").exists():
        return
    assert "Martyrdom" in ec._hero_kit("chen")


def test_picked_items_can_be_hidden():
    js = (ec._HERE / "src" / "js" / "changes-item-slots.js").read_text(encoding="utf-8")
    css = (ec._HERE / "src" / "css" / "pixel-skin-filters.css").read_text(encoding="utf-8")
    assert "ec-items-off" in js and "body.ec-items-off .ec-item-inject" in css


def test_hero_filters_sit_in_the_right_rail():
    # owner 2026-11-24: the patch pages' filter card; Shard / Scepter as plain boxes, abilities as an icon grid
    rail = ec._rail(ec._scope_btn("shard", "Shard"), '<div class="ec-ab-grid"></div>')
    assert 'class="filter-pop ec-rail" id="filter-pop"' in rail and 'data-filter="hidden"' in rail
    assert 'class="cat-filter-btn ec-scope-btn" data-ec-scope="shard"><span class="fp-word">Shard<' in rail
    assert "Aghanim" not in rail


def test_home_side_on_a_letter_patch_with_an_unchanged_map():
    # 7.42a shipped 7.42-v3's map: no mapdata_742a.json, the home jungle still comes from the newest map data
    assert ec._latest_home_side()
