"""7.38 "Touched up the map in general. Slightly adjusted neutral camps, trees, and cliffs": a picture under each word
(owner 2026-10-28: "neutral camps — their own pictures, trees too, cliffs too; the other changes apart"), not one
whole map."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "gen"))
from patch import elements  # noqa: E402
from patch.state import reset_page_state  # noqa: E402
import terrain_hotspots as th  # noqa: E402

ROW = "Touched up the map in general. Slightly adjusted neutral camps, trees, and cliffs"


def test_every_word_opens_its_own_pictures():
    reset_page_state()
    phrases, html = elements.terrain_note("7.38", ROW)
    assert phrases == ("the map", "neutral camps", "trees", "cliffs")
    assert all(f'class="tshots" data-part="{k}" hidden' in html for k in range(4))
    row = elements.terrain_button(ROW, phrases)
    assert row.count('class="tshots-btn"') == 4
    assert '<button type="button" class="tshots-btn" data-part="3" aria-expanded="false">cliffs</button>' in row


def test_a_row_without_parts_still_has_one_button():
    reset_page_state()
    phrase, html = elements.terrain_note("7.38", "Roshan is back in the river, with one pit located near each sidelane")
    assert phrase == "back in the river" and "data-part" not in html


def test_cliffs_are_lines_gone_and_new_not_a_stream_bank():
    pytest.importorskip("PIL")                  # cliff_changes reads the map's pictures; CI installs no imaging libraries
    removed, added = th.cliff_changes("737e", "738")
    assert removed and added
    # a stream's bank (river level on one side) is never a cliff
    assert th._edges({(0, 0): 0, (1, 0): 1}) == set() and th._edges({(0, 0): 2, (1, 0): 1}) == {(0, 0)}
    # a redrawn cliff in the same place is not a change: the same map against itself has none
    assert th.cliff_changes("738", "738") == ([], [])


def test_hotspots_merge_neighbours_and_size_by_extent():
    pts = [(100, 100)] * 5 + [(1100, 100)] * 5 + [(9000, 9000)]
    spots = th.hotspots(pts, 3)
    assert len(spots) == 1 and spots[0][3] == 10 and th.R_MIN <= spots[0][2] <= th.R_MAX
