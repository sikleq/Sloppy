"""tools/fetch_stats.py picks the patch's own build: the first one that carries its patch notes (2026-10-21: the
first build of the release day was a build before the patch for 14 patches — 7.41 got 6726 instead of 6728)."""
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import fetch_stats as fs  # noqa: E402


def _c(sha, day):
    return {"sha": sha, "date": datetime.fromisoformat(day).replace(tzinfo=timezone.utc), "message": sha}


COMMITS = [_c("6730", "2026-03-26"), _c("6728", "2026-03-25"), _c("6726", "2026-03-24"), _c("6720", "2026-03-20")]


def test_the_first_build_with_its_notes_is_taken(monkeypatch):
    notes = {"6726": b'"DOTA_Patch_7_40c_x" "y"', "6728": b'"DOTA_Patch_7_41_General" "x"',
             "6730": b'"DOTA_Patch_7_41_General" "x"'}
    monkeypatch.setattr(fs, "download_raw", lambda _s, sha, _p: notes.get(sha))
    assert fs.find_patch_build(None, COMMITS, "7.41", "24.03.2026")["sha"] == "6728"
    assert fs.find_commit_for_patch(COMMITS, "24.03.2026")["sha"] == "6726"      # the old rule, kept for reference


def test_no_build_with_notes_nearby_skips_the_patch(monkeypatch):
    monkeypatch.setattr(fs, "download_raw", lambda _s, _sha, _p: b'"DOTA_Patch_7_40c_x" "y"')
    assert fs.find_patch_build(None, COMMITS, "7.41", "24.03.2026") is None
    assert fs.has_patch_notes(b'"DOTA_Patch_7_41b_A" "x"', "7.41b") and not fs.has_patch_notes(None, "7.41")
