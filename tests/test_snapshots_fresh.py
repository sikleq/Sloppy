"""Sentinel: the GLOBAL data snapshots must cover the newest released patch.

Several site pieces read repo-wide snapshot files that are refreshed by hand,
outside the per-patch data/stats/<ver>/ folder (see docs/workflow.md Step 2b):
  - data/patchnotes_english.txt  -> generator section order, _info notes,
                                    calendar "major patch" counts, OLD-desc lifts
  - data/herolist.json           -> hero name resolution for the generator/audits
  - data/abilities_slim.json     -> ability names, innate markers, slug audit
  - data/itemlist.json, data/shops.txt -> item names, neutral pool, shop categories

When a patch ships and these are NOT refreshed, the site silently keeps the old
text (e.g. 7.41e had 0 keys in patchnotes_english.txt for weeks). This test
fails loudly instead.
"""
import json
import os
import re
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


# ── the shared files rebuilt from the newest snapshot (tools/new_patch.py runs the writers) ──────────────────────

def test_abilities_slim_matches_latest_snapshot():
    """Every ability of the newest data/stats/<v>/ (npc_abilities.txt + heroes/) is in data/abilities_slim.json with
    the name and innate flag the game files give it. Stale = a new/renamed ability fails the slug audit and loses
    its innate marker. Fix: python tools/build_abilities_slim.py"""
    from tools import build_abilities_slim as bas
    latest = latest_stats_version()
    with open(bas.OUT, encoding="utf-8") as f:
        current = json.load(f)
    diff = bas.changes(current, bas.build(os.path.join(ROOT, "data", "stats", latest), bas.load_loc(), current))
    assert not diff, (f"data/abilities_slim.json is stale against data/stats/{latest}: {len(diff)} row(s), e.g. "
                      f"{diff[:3]}. Run: python tools/build_abilities_slim.py")


def test_herolist_matches_latest_snapshot():
    """data/herolist.json is exactly what the newest snapshot's hero files + abilities_english.txt give.
    Fix: python tools/build_herolist.py"""
    from tools import build_herolist as bh
    from tools.build_abilities_slim import load_loc
    latest = latest_stats_version()
    fresh = bh.build(os.path.join(ROOT, "data", "stats", latest), load_loc())
    with open(bh.OUT, encoding="utf-8") as f:
        text = f.read()
    diff = bh.changes(json.loads(text), fresh)
    assert not diff, (f"data/herolist.json is stale against data/stats/{latest}: {diff[:3]}. "
                      f"Run: python tools/build_herolist.py")
    assert text == bh.dumps(fresh), "data/herolist.json: same heroes, other order/layout — run tools/build_herolist.py"


def _latest_item_slugs():
    latest = latest_stats_version()
    with open(os.path.join(ROOT, "data", "stats", latest, "items.txt"), encoding="utf-8", errors="replace") as f:
        return latest, set(re.findall(r'^\t"(item_[a-z0-9_]+)"', f.read(), re.M))


def test_itemlist_names_every_item_of_latest_snapshot():
    """data/itemlist.json (Valve datafeed) lists exactly the items of the newest items.txt.
    Fix: python scripts/fetch/fetch_itemlist.py"""
    latest, kv = _latest_item_slugs()
    with open(os.path.join(ROOT, "data", "itemlist.json"), encoding="utf-8") as f:
        listed = {i["name"] for i in json.load(f)["result"]["data"]["itemabilities"]}
    assert not kv - listed, (f"data/itemlist.json misses {sorted(kv - listed)[:8]} of data/stats/{latest}/items.txt "
                             f"— run python scripts/fetch/fetch_itemlist.py")
    assert not listed - kv, (f"data/itemlist.json lists {sorted(listed - kv)[:8]}, gone from data/stats/{latest}/"
                             f"items.txt — run python scripts/fetch/fetch_itemlist.py")


def test_shops_list_only_items_of_latest_snapshot():
    """data/shops.txt (the game's shop layout) names no item the newest items.txt lacks.
    Fix: python scripts/fetch/extract_shops.py"""
    latest, kv = _latest_item_slugs()
    with open(os.path.join(ROOT, "data", "shops.txt"), encoding="utf-8") as f:
        shop = set(re.findall(r'"item"\s+"(item_[a-z0-9_]+)"', f.read()))
    assert not shop - kv, (f"data/shops.txt lists {sorted(shop - kv)[:8]}, not in data/stats/{latest}/items.txt — "
                           f"run python scripts/fetch/extract_shops.py")
