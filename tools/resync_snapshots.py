# -*- coding: utf-8 -*-
r"""Re-extract data/stats/<version>/{items,heroes,units}.json from the patch's own game files, where they differ.

The authority is our store of the game's plain-text files (private repo dota-patch-files, one commit per patch tagged
with the version; its tools/builds.py chooses each patch's own build: first build with the patch's notes and without
the next patch's, plus release-night fixes). History: until 2026-09-27 fetch_stats took the first d2vpkr commit dated
on the patch day (often before the patch: items.json 7.41 = 7.40c); until 2026-10-23 a d2vpkr history ("last commit
<= release + 4 days") held a neighbouring patch's state in 52 files (7.13 armor and speed from 7.13b, 7.33d/7.33e/
7.34d heroes from before the patch, ...). The extraction is fetch_stats' own (same shape as tools/slim_from_kv.py).
A version whose raw KV sits in data/stats/<v>/ (slim_from_kv's input, taken from the live VPK) is left alone.

Usage:  python tools/resync_snapshots.py            # dry run: what would change
        python tools/resync_snapshots.py --write    # rewrite the stale files
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FETCH_STATS = os.path.join(HERE, "tools", "fetch_stats.py")
KINDS = (  # slim file, raw file under scripts/npc/, extractor name
    ("items.json", "items.txt", "extract_items"),
    ("heroes.json", "npc_heroes.txt", "extract_heroes"),
    ("units.json", "npc_units.txt", "extract_units"),
)   # abilities.json is read by no page: not resynced


class StoreSource:
    """scripts/npc/<raw file> of the patch in the store (tools/game_files.py)."""

    def __init__(self):
        sys.path.insert(0, HERE)
        from tools import game_files
        self.gf = game_files

    def text(self, v, raw_name):
        return self.gf.npc(v, raw_name) if v in self.gf.versions() else None


def stale_snapshots(fs, source=None):
    """[(version, slim file, items differing, extracted truth)] for every slim JSON that differs."""
    source = source or StoreSource()
    stats = os.path.join(HERE, "data", "stats")
    out = []
    for slim_name, raw_name, fn in KINDS:
        for v in sorted(os.listdir(stats)):
            slim = os.path.join(stats, v, slim_name)
            if not os.path.exists(slim) or os.path.exists(os.path.join(stats, v, raw_name)):
                continue
            text = source.text(v, raw_name)
            if text is None or "#base" in text:
                continue                                   # an include list (7.41f+): slim_from_kv's job
            truth = getattr(fs, fn)(fs.parse_kv(text))
            have = json.load(open(slim, encoding="utf-8"))
            if truth != have:
                out.append((v, slim_name, sum(1 for k in set(truth) | set(have) if truth.get(k) != have.get(k)), truth))
    return out


def load_fetch_stats():
    spec = importlib.util.spec_from_file_location("fetch_stats", FETCH_STATS)
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)
    return fs


def main(write):
    stale = stale_snapshots(load_fetch_stats())
    for v, slim_name, n, truth in stale:
        if write:
            with open(os.path.join(HERE, "data", "stats", v, slim_name), "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(truth, ensure_ascii=False, indent=2))
        print(f"  {v} {slim_name}: {n} entries {'rewritten' if write else 'differ'}")
    print(f"{len(stale)} snapshots {'rewritten' if write else 'to rewrite'}")


if __name__ == "__main__":
    main("--write" in sys.argv)
