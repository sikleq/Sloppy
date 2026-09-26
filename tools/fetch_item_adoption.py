# -*- coding: utf-8 -*-
"""How pros adopted an item after each patch: share of player-games that BOUGHT it, before vs after.

Source: DEMOS (our own replay parses, Tier 1-2 pro matches, 2024 onwards), table `purchases`
(match_id, slot, item, ts). A player-game "bought" an item when the item appears in its purchase log
at least once (a component bought for a different upgrade still counts: it is what pros spent on).
Windows: up to 21 days before and after the patch date, cut at the neighbouring patches.

Used by patch/weights.py for an item's REWORK rows (signal R): the direction of a reworked ability
cannot be read from the notes, Valve's pricing or Valve's follow-up patches (docs/weights.md
"Item reworks"), so it is measured the way talent replacements are (signal K).

Usage:  python tools/fetch_item_adoption.py      -> data/rules/item_adoption.json
"""
import collections
import datetime as dt
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from patch.meta import RELEASE_HISTORY  # noqa: E402

DEMOS_DB = os.environ.get("DEMOS_DB", "C:/Users/sikle/demos/data/demos.db")
OUT = os.path.join(HERE, "data", "rules", "item_adoption.json")
WINDOW_DAYS = 21
MIN_DAYS = 5                  # a window shorter than this (sub-patch two days later) is not used
MIN_GAMES = 200               # player-games per window


def _ts(d):
    return int(dt.datetime.strptime(d, "%d.%m.%Y").replace(tzinfo=dt.timezone.utc).timestamp())


def windows():
    rel = sorted(((_ts(r["date"]), r["version"]) for r in RELEASE_HISTORY if r.get("date")))
    day = 86400
    for i, (t, v) in enumerate(rel):
        lo = max(t - WINDOW_DAYS * day, rel[i - 1][0] if i else 0)
        hi = min(t + WINDOW_DAYS * day, rel[i + 1][0] if i + 1 < len(rel) else t + WINDOW_DAYS * day)
        if t - lo >= MIN_DAYS * day and hi - t >= MIN_DAYS * day:
            yield v, lo, t, hi


def counts(con, lo, hi):
    """(player-games, {item_slug: player-games that bought it}) for matches started in [lo, hi)."""
    games = con.execute("SELECT count(DISTINCT p.match_id || ':' || p.slot) FROM purchases p JOIN matches m "
                        "USING(match_id) WHERE m.start_time >= ? AND m.start_time < ?", (lo, hi)).fetchone()[0]
    cur = con.execute("SELECT p.item, count(DISTINCT p.match_id || ':' || p.slot) FROM purchases p JOIN matches m "
                      "USING(match_id) WHERE m.start_time >= ? AND m.start_time < ? GROUP BY p.item", (lo, hi))
    return games, {it[5:] if it.startswith("item_") else it: n for it, n in cur}


def main():
    if not os.path.exists(DEMOS_DB):
        print("DEMOS database not found, item_adoption.json kept as is:", DEMOS_DB)
        return 0
    con = sqlite3.connect("file:" + DEMOS_DB + "?mode=ro", uri=True)
    out = {}
    for v, lo, t, hi in windows():
        gb, cb = counts(con, lo, t)
        ga, ca = counts(con, t, hi)
        if min(gb, ga) < MIN_GAMES:
            continue
        out[v] = {"games": [gb, ga], "days": [round((t - lo) / 86400), round((hi - t) / 86400)],
                  "items": {it: [cb.get(it, 0), ca.get(it, 0)] for it in sorted(set(cb) | set(ca))
                            if cb.get(it, 0) + ca.get(it, 0) >= 20}}
    doc = __doc__.strip().split("\n\n")[0] + (" items: slug -> [player-games that bought it before, after]; "
                                                "games: all player-games in the two windows.")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("{\n \"_doc\": " + json.dumps(doc) + ",\n \"versions\": {\n")
        f.write(",\n".join(f"  {json.dumps(v)}: {json.dumps(x, sort_keys=True)}" for v, x in out.items()))
        f.write("\n }\n}\n")
    print(len(out), "patch windows ->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
