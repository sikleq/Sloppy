"""mend_map.py: an object drawn pink (missing material) is replaced by a donor render's ground — only the object, its
rim and shadow; the ground around it stays the mended render's own (7.39b painted grass where 7.39's portal stood)."""
import os
import sys

import pytest

np = pytest.importorskip("numpy")              # map tools run locally; CI installs no imaging libraries
pytest.importorskip("scipy")
pytest.importorskip("PIL")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
import mend_map  # noqa: E402

RECT = (0.0, 400.0, 0.0, 400.0)          # x0, x1, y_bottom, y_top: 2 units per px -> 200 x 200


def _scene():
    bad = np.full((200, 200, 3), (120, 100, 60), np.uint8)               # sand
    yy, xx = np.ogrid[:200, :200]
    disc = (xx - 100) ** 2 + (yy - 100) ** 2 <= 20 ** 2
    bad[disc] = (230, 90, 160)                                           # the pink object
    bad[60, 140] = (230, 90, 160)                                        # a pink flower 36 px from the object
    donor = np.full((200, 200, 3), (120, 100, 60), np.uint8)
    donor[(xx - 100) ** 2 + (yy - 100) ** 2 <= 35 ** 2] = (70, 140, 60)  # grass, wider than the object
    donor[150:160, 20:30] = (0, 0, 255)                                  # render noise far away
    return bad, donor, disc


def test_pink_is_the_missing_material_colour():
    px = np.array([[[230, 90, 160], [150, 60, 100], [120, 100, 60], [70, 140, 60], [200, 40, 40]]], np.uint8)
    assert mend_map.pink(px).tolist() == [[True, True, False, False, False]]


def test_the_object_goes_and_the_ground_around_it_stays():
    bad, donor, disc = _scene()
    out = mend_map.mend(bad, donor, [(200.0, 200.0)], RECT, upp=2.0, radius=180.0)
    assert not mend_map.pink(out[disc]).any()
    assert (out[100, 100] == donor[100, 100]).all()                      # the middle comes from the donor
    assert (out[100, 132] == bad[100, 132]).all()                        # 12 px out: still the sand, not the grass
    assert (out[150:160, 20:30] == bad[150:160, 20:30]).all()            # the donor's noise is not copied
    assert (out[60, 140] == bad[60, 140]).all()                          # nor is a pink flower nearby touched


def test_a_spike_that_broke_off_goes_with_the_object():
    bad, donor, _disc = _scene()
    bad[100, 118:126] = (230, 90, 160)                                   # a spike 18-25 px from the middle
    bad[100, 121] = (120, 100, 60)                                       # ... with a gap
    out = mend_map.mend(bad, donor, [(200.0, 200.0)], RECT, upp=2.0, radius=180.0)
    assert not mend_map.pink(out[100:101, 110:130]).any()
