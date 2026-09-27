"""2026-09-27: data/stats/<v>/items.json must be that patch's items.txt, not a copy of the previous patch's
(7.41 was 7.40c byte for byte; 7.37e kept Khanda's 7.37d recipe). Checked against the per-patch items.txt
history where it exists locally; skipped elsewhere (CI)."""
import importlib.util
import json
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
HIST = pathlib.Path(os.path.expanduser("~")) / "outputs" / "valve-revealed-weights-20260915" / "items_history"
FETCH_STATS = pathlib.Path(r"D:\Sloppy Patches\fetch_stats.py")


@pytest.mark.skipif(not (HIST.exists() and FETCH_STATS.exists()), reason="items.txt history not on this machine")
def test_item_snapshots_equal_their_patch_items_txt():
    spec = importlib.util.spec_from_file_location("fetch_stats", FETCH_STATS)
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)
    stale = []
    for vdir in sorted((ROOT / "data" / "stats").iterdir()):
        slim, raw = vdir / "items.json", HIST / vdir.name / "items.txt"
        if slim.exists() and raw.exists():
            truth = fs.extract_items(fs.parse_kv(raw.read_text(encoding="utf-8", errors="replace")))
            if json.loads(slim.read_text(encoding="utf-8")) != truth:
                stale.append(vdir.name)
    assert not stale, f"stale items.json (run tools/resync_item_snapshots.py --write): {stale}"
