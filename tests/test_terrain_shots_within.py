"""Owner 2026-11-22: the three 7.42 mid notes (trees where the mid lanes meet, by the Radiant Tier 1, by the Dire
Tier 1) showed one and the same picture with every changed tree of the area outlined. A spot's `within` circles keep
only that note's own changes."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "gen"))
import terrain_shots as ts  # noqa: E402

GROUPS = {"trees": {"added": [(0, 0), (1000, 1000)], "removed": [(-1000, 0)],
                    "moved": [((5000, 5000), (100, 0)), ((6000, 6000), (7000, 7000))]}}


def test_within_keeps_only_the_changes_inside_its_circles():
    out = ts.only_within(GROUPS, [[0, 0, 200]])
    assert out["trees"]["added"] == [(0, 0)]
    assert out["trees"]["removed"] == []
    assert out["trees"]["moved"] == [((5000, 5000), (100, 0))]      # either end inside counts


def test_no_within_keeps_every_change():
    assert ts.only_within(GROUPS, None) is GROUPS


def test_the_three_742_mid_notes_outline_different_areas():
    with open(os.path.join(ROOT, "data", "terrain_spots.json"), encoding="utf-8") as f:
        spots = json.load(f)["7.42"]
    mid = [e for e in spots if e["match"].startswith(("Added some trees to the sides of Mid lane",
                                                      "Added more trees to the north of Radiant Tier",
                                                      "Cleaned up the trees by Dire Mid Tier 1"))]
    assert len(mid) == 3
    assert all(e.get("within") for e in mid)
    assert len({tuple(e["spots"][0]) for e in mid}) == 3
