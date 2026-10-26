"""2026-09-27: data/stats/<v>/{items,heroes,abilities}.json must be that patch's KV, not a copy of the previous
patch's (items.json 7.41 was 7.40c byte for byte; 7.37e kept Khanda's 7.37d recipe; heroes.json 7.41 was
7.40c). Checked against the patch's own game files in the store (dota-patch-files; since 2026-10-24, before that
the d2vpkr history in outputs/) where it exists locally; skipped elsewhere (CI)."""
import importlib.util
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("resync_snapshots", ROOT / "tools" / "resync_snapshots.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)


def _store_here():
    sys.path.insert(0, str(ROOT))
    from tools import game_files
    return game_files.available() and len(game_files.versions()) > 100


@pytest.mark.slow
@pytest.mark.skipif(not _store_here(), reason="the game-files store (dota-patch-files) is not on this machine")
def test_snapshots_equal_their_patch_kv():
    stale = [(v, name) for v, name, _, _ in rs.stale_snapshots(rs.load_fetch_stats())]
    assert not stale, f"stale snapshots (run tools/resync_snapshots.py --write): {stale}"
