"""Sentinel: the GLOBAL data snapshots must cover the newest released patch.

Several site pieces read repo-wide snapshot files that are refreshed by hand,
outside the per-patch data/stats/<ver>/ folder (see docs/workflow.md Step 2b):
  - data/patchnotes_english.txt  -> generator section order, _info notes,
                                    calendar "major patch" counts, OLD-desc lifts
  - data/herolist.json           -> hero name resolution for the generator/audits

When a patch ships and these are NOT refreshed, the site silently keeps the old
text (e.g. 7.41e had 0 keys in patchnotes_english.txt for weeks). This test
fails loudly instead.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from patch.meta import _current_version, latest_stats_version  # noqa: E402


def _kv_version(v: str) -> str:
    """'7.41e' -> '7_41e' (the DOTA_Patch_<ver>_ key form)."""
    return v.replace(".", "_")


def test_patchnotes_cover_newest_patch():
    newest = _current_version()
    prefix = f"DOTA_Patch_{_kv_version(newest)}_"
    text = open(os.path.join(ROOT, "data", "patchnotes_english.txt"),
                encoding="utf-8-sig", errors="replace").read()
    n = text.count(prefix)
    assert n > 0, (
        f"data/patchnotes_english.txt has 0 '{prefix}*' keys but {newest} is the "
        f"newest patch in patch/meta.py. Refresh it: bump PATCH_VERSION in "
        f"scripts/fetch/extract_patchnotes.py to {newest} and run it "
        f"(docs/workflow.md Step 2b)."
    )


def test_herolist_covers_latest_stats_heroes():
    latest = latest_stats_version()
    heroes_json = json.load(open(os.path.join(ROOT, "data", "stats", latest, "heroes.json"),
                                 encoding="utf-8"))
    # KV ships non-playable placeholders (target_dummy) that never appear in
    # Valve's herolist API — they are not staleness, so skip them.
    _NON_PLAYABLE = ("_base", "target_dummy")
    in_stats = {k for k in heroes_json
                if k.startswith("npc_dota_hero_") and not any(t in k for t in _NON_PLAYABLE)}
    hl = json.load(open(os.path.join(ROOT, "data", "herolist.json"), encoding="utf-8"))
    in_herolist = {h["name"] for h in hl["result"]["data"]["heroes"]}
    missing = sorted(in_stats - in_herolist)
    assert not missing, (
        f"data/herolist.json is stale: {len(missing)} hero(es) exist in "
        f"data/stats/{latest}/heroes.json but not in herolist.json: {missing[:10]}. "
        f"Refresh herolist.json (docs/workflow.md Step 2b)."
    )


def test_latest_heroes_json_not_hollow():
    """7.41f regression: npc_heroes.txt became a `#base` include list and heroes.json
    was written as `{}` — Hero Lab then offered a single hero. Slim must resolve includes."""
    latest = latest_stats_version()
    heroes_json = json.load(open(os.path.join(ROOT, "data", "stats", latest, "heroes.json"),
                                 encoding="utf-8"))
    playable = [k for k, v in heroes_json.items()
                if k.startswith("npc_dota_hero_") and isinstance(v, dict) and v.get("AttributePrimary")]
    assert len(playable) >= 120, (
        f"data/stats/{latest}/heroes.json has only {len(playable)} playable heroes — "
        f"regenerate with `python tools/slim_from_kv.py {latest}` (it follows #base includes)."
    )
