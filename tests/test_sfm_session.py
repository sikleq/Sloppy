"""The SFM session template in the repo (the owner 2026-10-02: "if you made your own, they'd be handy in the repo")."""
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
import sfm_session  # noqa: E402


def test_the_template_holds_no_local_path():
    with open(sfm_session.TEMPLATE, encoding="utf-8") as f:
        s = f.read()
    assert s.startswith("<!-- dmx encoding keyvalues2")
    assert s.count(sfm_session.PLACEHOLDER) == 1 and "Users" not in s


def test_the_export_folder_is_filled_in_as_keyvalues2_wants_it():
    s = sfm_session.session_text("D:/maps/frames_x")
    assert sfm_session.PLACEHOLDER not in s
    assert '"D:' + "\\\\" + "maps" + "\\\\" + "frames_x" + "\\\\" + '"' in s


def test_the_camera_flies_the_serpentine_stitch_sfm_reads():
    pytest.importorskip("numpy")                # stitch_sfm needs it; CI installs no imaging libraries
    import stitch_sfm
    frames, _quat, fov, width, height = stitch_sfm.camera_path(sfm_session.session_text("D:/f"))
    assert len(frames) == 66 and round(fov, 3) == 1.0 and (width, height) == (3840, 2160)
