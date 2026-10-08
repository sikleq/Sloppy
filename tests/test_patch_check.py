"""tools/patch_check.py — the new-patch routine checked step by step (the owner 2026-10-08)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)

import patch_check as pc  # noqa: E402


def test_the_newest_patch_misses_no_step():
    from patch.meta import RELEASE_HISTORY
    rows = pc.run(RELEASE_HISTORY[0]["version"])
    missing = [r for r in rows if r[2][0] == "MISSING"]
    assert not missing, missing                     # files only on the owner's PC (datafeed, Oldgrowth) only WARN


def test_an_unregistered_patch_is_reported_missing():
    rows = pc.run("9.99")
    assert ("Registration", "RELEASE_HISTORY (patch/meta.py)") in [(g, w) for g, w, (s, _n) in rows if s == "MISSING"]
    assert any(w.startswith("data/stats/") and s == "MISSING" for _g, w, (s, _n) in rows)


def test_older_patches_only_warn_about_what_ci_needs_from_the_newest():
    """The full file set and the normalized JSON are required of the newest patch only (7.40 has neither)."""
    rows = pc.run("7.40")
    assert not [r for r in rows if r[2][0] == "MISSING"], rows
