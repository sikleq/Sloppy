"""Every map objective a patch's map file moved, added or removed has a picture on that patch's page (owner
2026-10-28: 7.38 "Shrines of Wisdom are located …", "Tormentor spawns repositioned to the corners of the map", "Roshan
is back in the river" showed no picture; "in new patches, if these objectives move, catch where to — even when the
note is not under Terrain Changes"). The picture comes from an entry of data/terrain_spots.json whose keys draw that
object (its 'show', else the first object word of its 'match'); the entry matches the row by its words, in any section.
A shift under MIN_MOVE game units (7.39b: a watcher 22 units, no note) is not a move."""
import json
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from patch import map_versions as mv  # noqa: E402
from patch import terrain_index  # noqa: E402
from patch.terrain_notes import show_keys  # noqa: E402

OBJECTIVES = ("roshan", "tormentors", "wisdom", "wisdomRunes", "outposts", "twinGates", "lotus", "watchers", "bounty")
MIN_MOVE = 100


def _changed(old, new):
    """True when a point of one side has no point of the other within MIN_MOVE (moved, added or removed)."""
    def far(a, b):
        return any(min((math.dist(p, q) for q in b), default=math.inf) > MIN_MOVE for p in a)
    return far(old, new) or far(new, old)


def _missing():
    with open(os.path.join(ROOT, "data", "terrain_spots.json"), encoding="utf-8") as f:
        spots = json.load(f)
    out = []
    for step in mv.steps():
        try:
            diff = terrain_index._load_diff(step.patch)
        except (OSError, ValueError, KeyError):
            continue
        drawn = set()
        for e in spots.get(step.patch, []):
            drawn |= set(e["show"]) if "show" in e else set(show_keys(e["match"]))
        for key in OBJECTIVES:
            v = (diff.get("entities") or {}).get(key) or {}
            if _changed(v.get("old", []), v.get("new", [])) and key not in drawn:
                out.append(f"{step.patch} {key}")
    return out


def test_every_moved_objective_has_a_picture():
    if not mv.steps():
        pytest.skip("no map steps")
    assert _missing() == []


def test_a_tiny_shift_is_not_a_move():
    assert not _changed([(6592, -6272)], [(6614, -6272)])
    assert _changed([(7872, -7808)], [(2966, -2967)])
    assert _changed([], [(8340, -1008)])
