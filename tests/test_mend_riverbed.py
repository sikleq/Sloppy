"""mend_riverbed.py: a pale riverbed patch with a straight edge in the water (7.42 mid, the Dire riverbed's missing
corner) is taken out — no step across the edge any more, the water's fine detail kept, nothing outside the box
touched; a map file without a fix comes back unchanged."""
import os
import sys

import pytest

np = pytest.importorskip("numpy")              # map tools run locally; CI installs no imaging libraries
pytest.importorskip("scipy")
pytest.importorskip("PIL")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
import mend_riverbed  # noqa: E402

RECT = (0.0, 400.0, 0.0, 400.0)          # x0, x1, y_bottom, y_top: 2 units per px -> 200 x 200
BOX = (100.0, 200.0, 100.0, 300.0, "rt")  # world: columns 50..100, rows 50..150; sharp right and top


def _scene():
    rng = np.random.default_rng(742)
    water = np.full((200, 200, 3), (20, 26, 34), np.float32) + rng.normal(0, 2.0, (200, 200, 3))
    pale = np.zeros((200, 200, 3), np.float32)
    ramp = np.linspace(0, 1, 50, dtype=np.float32)               # brighter towards the sharp right side
    pale[50:150, 50:100] = ramp[None, :, None] * np.array([4, 9, 14], np.float32)
    return water, np.clip(water + pale + 0.5, 0, 255).astype(np.uint8)


def _step(img):
    """Mean brightness just inside minus just outside the right edge (column 100), rows 70..130."""
    a = img.astype(np.float32)
    return float(a[70:130, 95:100].mean() - a[70:130, 100:105].mean())


def test_the_pale_corner_goes_away(monkeypatch):
    monkeypatch.setitem(mend_riverbed.FIXES, "test0000", [BOX])
    water, bad = _scene()
    assert _step(bad) > 6                                         # the edge is there before
    out = mend_riverbed.mend(bad, "test0000", rect=RECT)
    assert abs(_step(out)) < 1.5                                  # and gone after
    from scipy import ndimage
    inside = (slice(60, 140), slice(55, 95), 2)

    def detail(a):                                                # the fine ripples: minus their own blur
        f = a.astype(np.float32)
        return (f - ndimage.gaussian_filter(f, (3, 3, 0)))[inside].ravel()
    assert np.corrcoef(detail(bad), detail(out))[0, 1] > 0.9      # ripples kept
    far = np.ones((200, 200), bool)
    far[50 - mend_riverbed.MARGIN:150 + mend_riverbed.MARGIN, 50 - mend_riverbed.MARGIN:100 + mend_riverbed.MARGIN] = False
    assert (out[far] == bad[far]).all()                           # nothing touched away from the box


def test_a_map_without_a_fix_is_left_alone():
    _water, bad = _scene()
    assert mend_riverbed.mend(bad, "deadbeef", rect=RECT) is bad
    assert {"118cfcea", "0d7217cc", "51dc118a"} <= set(mend_riverbed.FIXES)      # 7.42, -v2, -v3
