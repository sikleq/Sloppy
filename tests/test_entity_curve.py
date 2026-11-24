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
