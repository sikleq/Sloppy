"""Our top-down map picture from Source Filmmaker frames (scripts/gen/stitch_sfm.py; the owner 2026-10-01: "can we
do it through SFM?"): frames placed by the session's camera path, borders cross-faded."""
import os
import sys

import pytest

np = pytest.importorskip("numpy")              # map tools run locally; CI installs no imaging libraries
Image = pytest.importorskip("PIL.Image")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
import stitch_sfm as ss  # noqa: E402

SESSION_QUAT = [-0.4964516461, 0.5035233498, 0.5035233498, 0.4964516461]     # the session camera: 0.81 deg off


def test_the_tilted_session_camera_looks_3400_units_west_of_itself():
    (centre, right, up, upp), = ss.footprints([np.array([-6000.0, -9793.1, 240000.0])], SESSION_QUAT, 1.0, 3840)
    assert abs(centre[0] - (-9392.9)) < 2 and abs(centre[1] - (-9793.1)) < 0.1
    assert np.allclose(right, [1, 0], atol=1e-3) and np.allclose(up, [0, 1], atol=1e-3)
    assert abs(upp - 1.0904) < 1e-3


def test_the_cross_fade_weights_of_two_neighbours_add_up_to_one():
    pos = np.linspace(-50, 50, 101)
    a = ss._ramp(pos, -100, 0, 20, False, True)                 # the cell left of the border at 0
    b = ss._ramp(pos, 0, 100, 20, True, False)                  # the cell right of it
    assert np.allclose(a + b, 1)
    assert a[0] == 1 and b[-1] == 1


def test_a_render_must_cover_the_picture_and_hold_the_whole_map():
    text = ss.session_text(os.path.join(_ROOT, "tests", "fixtures", "sfm_session_text.dmx")) \
        if os.path.exists(os.path.join(_ROOT, "tests", "fixtures", "sfm_session_text.dmx")) else None
    frames = [np.array([x, y, 240000.0]) for y in (-9793.1 + 2000 * j for j in range(11))
              for x in (-6000 + 3600 * i for i in range(6))]
    prints = ss.footprints(frames, SESSION_QUAT, 1.0, 3840)
    rect = (-10014, 9984, -10750, 10101)                          # the site's picture rectangle
    assert ss.check_fits(prints, 3840, 2160, rect, [(-8704, -9088), (8960, 8704)]) == []      # 7.41's extent
    assert ss.check_fits(prints, 3840, 2160, rect, [(-7680, -7168), (7680, 7424)]) == []      # a pre-7.33 map
    big = ss.check_fits(prints, 3840, 2160, rect, [(-9900, 0)])                               # a bigger map
    assert len(big) == 1 and "closer than" in big[0]
    short = ss.check_fits(prints[:-6], 3840, 2160, rect)                                      # top row missing
    assert len(short) == 1 and "not the whole picture" in short[0]


def test_black_void_paints_only_the_empty_corner_and_sfm_grey_rim():
    rng = np.random.default_rng(9)
    pic = np.clip(np.array([90, 150, 60]) + rng.normal(0, 6, (900, 900, 3)), 0, 255).round()
    pic[600:, 600:] = 3                                          # the near-black void, touching the corner
    pic[-12:, :] = 64                                            # SFM's flat grey background along the edge
    out = np.asarray(ss.black_void(Image.fromarray(pic.astype(np.uint8))), np.float32)
    assert np.array_equal(out[:580, :580], pic[:580, :580].astype(np.float32))                 # the map is untouched
    assert out[620:880, 620:880].max() == 0 and out[-6:, 100:500].max() == 0


def test_a_thin_grey_strip_along_the_edge_goes_black_too():
    """The owner 2026-10-02: a white line at the map's left edge when zoomed in — 5-6 px of SFM's grey (55) where
    the outer frames stop short of the picture's edge, too thin for the void's opening."""
    rng = np.random.default_rng(3)
    pic = np.clip(np.array([90, 150, 60]) + rng.normal(0, 6, (900, 900, 3)), 0, 255).round()
    pic[:, 700:] = 0                                             # the void along the right side
    pic[:, :5] = 55                                              # the strip on the left, beside the map
    pic[:, -5:] = 55                                             # and one inside the void
    out = np.asarray(ss.black_void(Image.fromarray(pic.astype(np.uint8))), np.float32)
    assert out[:, -5:].max() == 0 and out[:, :5].max() == 0
    assert np.array_equal(out[:, 40:600], pic[:, 40:600].astype(np.float32))                   # the map untouched


def test_the_seam_runs_where_the_two_patches_differ_least():
    err = np.full((20, 10), 9.0)
    err[:, 6] = 0                                                # a free column
    mask = ss._min_cut(err)
    assert (mask[:, 6:] == 1).all() and (mask[:, :6] == 0).all()


def test_the_void_gets_plain_ground_and_the_map_is_left_alone():
    rng = np.random.default_rng(5)
    grass = np.clip(np.array([90, 150, 60]) + rng.normal(0, 6, (900, 900, 3)), 0, 255).round()
    grass[100:140, 100:140] = [250, 250, 250]                     # an object: must not be copied
    pic = grass.copy()
    pic[600:, 600:] = 0                                          # the void, touching the picture's corner
    out = np.asarray(ss.fill_void(Image.fromarray(pic.astype(np.uint8))), np.float32)
    assert np.array_equal(out[:590, :590], pic[:590, :590].astype(np.float32))
    filled = out[620:, 620:]
    assert filled.mean() > 40                                    # not black any more
    assert (filled.max(axis=2) < 200).all()                      # no copied white object
    assert filled[..., 1].mean() > filled[..., 0].mean()         # green, like the ground around it


def test_frames_cut_from_a_picture_stitch_back_into_it(tmp_path):
    rng = np.random.default_rng(3)
    small = rng.uniform(0, 255, size=(40, 40, 3)).astype(np.uint8)
    world = np.asarray(Image.fromarray(small).resize((800, 800), Image.BICUBIC), np.float32)   # 1 unit = 1 px, y up
    centres = [(250.0, 250.0), (550.0, 250.0), (250.0, 550.0), (550.0, 550.0)]
    files, prints = [], []
    for k, (cx, cy) in enumerate(centres):                       # frames 400 x 400 units, upp 1, image up = +y
        rows = slice(800 - int(cy) - 200, 800 - int(cy) + 200)
        cols = slice(int(cx) - 200, int(cx) + 200)
        path = tmp_path / f"{k:06d}.png"
        Image.fromarray(world[rows, cols].astype(np.uint8)).save(path)
        files.append(str(path))
        prints.append((np.array([cx, cy]), np.array([1.0, 0.0]), np.array([0.0, 1.0]), 1.0))
    out = np.asarray(ss.stitch(files, prints, 1.0, (100, 700, 100, 700), blend_px=20), np.float32)
    assert out.shape == (600, 600, 3)
    assert np.abs(out - world[100:700, 100:700]).mean() < 3
