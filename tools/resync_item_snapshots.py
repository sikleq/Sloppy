# -*- coding: utf-8 -*-
r"""Re-extract data/stats/<version>/items.json from the per-patch items.txt history, where they differ.

Why (2026-09-27): several slim items.json were stale — 7.41 was a byte-for-byte copy of 7.40c (the whole
7.41 item overhaul sat in 7.41a), 7.37e still had Khanda's 7.37d recipe (600, not 500), 7.37d / 7.39c /
7.33b / 7.36b missed their patch's price changes, and 7.27–7.32 lacked recipes and fields such as
Arcane Blink's +25 Intelligence. The per-patch items.txt history is the authority; the extraction is
fetch_stats' own (same shape as tools/slim_from_kv.py).

Usage:  python tools/resync_item_snapshots.py            # dry run: what would change
        python tools/resync_item_snapshots.py --write    # rewrite the stale files
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(os.path.expanduser("~"), "outputs", "valve-revealed-weights-20260915", "items_history")
FETCH_STATS = r"D:\Sloppy Patches\fetch_stats.py"


def main(write):
    spec = importlib.util.spec_from_file_location("fetch_stats", FETCH_STATS)
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)
    stats = os.path.join(HERE, "data", "stats")
    changed = []
    for v in sorted(os.listdir(stats)):
        slim, raw = os.path.join(stats, v, "items.json"), os.path.join(HIST, v, "items.txt")
        if not (os.path.exists(slim) and os.path.exists(raw)):
            continue
        truth = fs.extract_items(fs.parse_kv(open(raw, encoding="utf-8", errors="replace").read()))
        have = json.load(open(slim, encoding="utf-8"))
        if truth == have:
            continue
        diff = sum(1 for k in set(truth) | set(have) if truth.get(k) != have.get(k))
        changed.append((v, diff))
        if write:
            with open(slim, "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(truth, ensure_ascii=False, indent=2))
    for v, n in changed:
        print(f"  {v}: {n} items {'rewritten' if write else 'differ'}")
    print(f"{len(changed)} snapshots {'rewritten' if write else 'to rewrite'}")


if __name__ == "__main__":
    main("--write" in sys.argv)
