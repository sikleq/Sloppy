# -*- coding: utf-8 -*-
"""How pros adopted an item after each patch: share of player-games that BOUGHT it, before vs after.

Source: DEMOS (our own replay parses, Tier 1-2 pro matches, 2024 onwards), table `purchases`
(match_id, slot, item, ts). A player-game "bought" an item when the item appears in its purchase log
at least once (a component bought for a different upgrade still counts: it is what pros spent on).
Windows: up to 21 days before and after the patch date, cut at the neighbouring patches.

Heroes (same windows, -> data/rules/hero_adoption.json): share of player-games that PLAYED the hero
(match_players.hero_id; ids -> npc names from data/stats/<latest>/heroes/*.txt "HeroID").

Used by patch/weights.py for an item's / a hero's REWORK rows (signal R): the direction of a reworked ability
cannot be read from the notes, Valve's pricing or Valve's follow-up patches (docs/weights.md
"Item reworks"), so it is measured the way talent replacements are (signal K).

Usage:  python tools/fetch_item_adoption.py      -> data/rules/item_adoption.json, hero_adoption.json
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
OUT_HEROES = os.path.join(HERE, "data", "rules", "hero_adoption.json")
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


def hero_names():
    """HeroID -> npc name without the prefix ("abyssal_underlord"), from the newest per-hero KV files."""
    import glob
    import re
    from patch.meta import latest_stats_version
    out = {}
    for f in glob.glob(os.path.join(HERE, "data", "stats", latest_stats_version(), "heroes", "npc_dota_hero_*.txt")):
        m = re.search(r'"HeroID"\s+"(\d+)"', open(f, encoding="utf-8", errors="replace").read())
        if m:
            out[int(m.group(1))] = os.path.basename(f)[len("npc_dota_hero_"):-4]
    return out


def hero_counts(con, lo, hi, names):
    games = con.execute("SELECT count(*) FROM match_players mp JOIN matches m USING(match_id) "
                        "WHERE m.start_time >= ? AND m.start_time < ?", (lo, hi)).fetchone()[0]
    cur = con.execute("SELECT mp.hero_id, count(*) FROM match_players mp JOIN matches m USING(match_id) "
                      "WHERE m.start_time >= ? AND m.start_time < ? GROUP BY mp.hero_id", (lo, hi))
    return games, {names[h]: n for h, n in cur if h in names}


def write(path, doc, out):
    with open(path, "w", encoding="utf-8") as f:
        f.write("{\n \"_doc\": " + json.dumps(doc) + ",\n \"versions\": {\n")
        f.write(",\n".join(f"  {json.dumps(v)}: {json.dumps(x, sort_keys=True)}" for v, x in out.items()))
        f.write("\n }\n}\n")


def main():
    if not os.path.exists(DEMOS_DB):
        print("DEMOS database not found, item_adoption.json kept as is:", DEMOS_DB)
        return 0
    con = sqlite3.connect("file:" + DEMOS_DB + "?mode=ro", uri=True)
    out, out_h, names = {}, {}, hero_names()
    for v, lo, t, hi in windows():
        gb, cb = counts(con, lo, t)
        ga, ca = counts(con, t, hi)
        if min(gb, ga) < MIN_GAMES:
            continue
        out[v] = {"games": [gb, ga], "days": [round((t - lo) / 86400), round((hi - t) / 86400)],
                  "items": {it: [cb.get(it, 0), ca.get(it, 0)] for it in sorted(set(cb) | set(ca))
                            if cb.get(it, 0) + ca.get(it, 0) >= 20}}
        hb, pb = hero_counts(con, lo, t, names)
        ha, pa = hero_counts(con, t, hi, names)
        out_h[v] = {"games": [hb, ha], "days": out[v]["days"],
                    "heroes": {h: [pb.get(h, 0), pa.get(h, 0)] for h in sorted(set(pb) | set(pa))}}
    doc = __doc__.strip().split("\n\n")[0] + (" items: slug -> [player-games that bought it before, after]; "
                                                "games: all player-games in the two windows.")
    write(OUT, doc, out)
    write(OUT_HEROES, "Tier 1-2 pro pick counts per hero, before/after every patch (DEMOS, tools/fetch_item_adoption.py). "
          "heroes: npc name -> [player-games on the hero before, after]; games: all player-games.", out_h)
    print(len(out), "patch windows ->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
