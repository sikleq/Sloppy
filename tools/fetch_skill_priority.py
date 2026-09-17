# -*- coding: utf-8 -*-
"""Objective "how central is this ability" prior from how pros actually skill it.

Source: OpenDota explorer (public SQL over professional matches). For every hero we count the
skill points put into each ability within the FIRST 10 ability upgrades over the last N days.
An ability that is maxed first holds ~4 of those points, a "one point wonder" ~1.

    share(ability)   = its points / points in the hero's basic abilities (ultimates/talents excluded)
    multiplier       = clamp(1 + 1.5 * (share - 1/n_basic), 0.7, 1.3)

so an evenly-skilled kit gives 1.0 everywhere, the maxed-first ability ~1.15-1.3, the value point
~0.7-0.8. Ultimates keep the fixed context multiplier (valve_weights.json "context.ultimate");
innates/facets are not skilled and stay 1.0.

Usage:  python tools/fetch_skill_priority.py [days=365] [auto|demos|opendota]
        -> data/rules/ability_priority.json
Default "auto": DEMOS (our own replay parses, Tier 1-2) for every hero it covers, OpenDota only for heroes DEMOS has no builds for.
"""
import sys, os, re, json, glob, time, urllib.request, urllib.parse, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from patch.meta import latest_stats_version  # noqa: E402
from patch.weights import ultimates          # noqa: E402

SQL = ("SELECT t.hero_id, t.ability, count(*) AS n FROM (SELECT pm.hero_id, a.ability, a.ord "
       "FROM player_matches pm JOIN matches m USING(match_id), "
       "unnest(pm.ability_upgrades_arr) WITH ORDINALITY a(ability, ord) "
       "WHERE m.start_time > extract(epoch from now() - interval '{days} days') AND a.ord <= 10) t "
       "GROUP BY 1,2")


DEMOS_DB = "C:/Users/sikle/demos/data/demos.db"


def rows_from_demos(days):
    """Same counts from OUR OWN replay parses (DEMOS, Tier 1-2 pro matches): table ability_builds
    holds every ability level-up with a timestamp. The first block of rows of a player (all at the
    minimal ts) is the kit registration, not skill points; linked abilities level together at the
    same ts, so only the first row of a timestamp counts. Returns [(hero_id, ability_slug, n)]."""
    import sqlite3
    con = sqlite3.connect("file:" + DEMOS_DB + "?mode=ro", uri=True)
    cur = con.execute(
        "SELECT ab.match_id, ab.slot, mp.hero_id, ab.ability, ab.ts FROM ability_builds ab "
        "JOIN matches m USING(match_id) JOIN match_players mp ON mp.match_id = ab.match_id AND mp.slot = ab.slot "
        "WHERE m.start_time > strftime('%s','now', ?) ORDER BY ab.match_id, ab.slot, ab.lvl", (f"-{int(days)} days",))
    counts, key, t0, seen_ts, n_up = collections.Counter(), None, None, set(), 0
    for mid, slot, hero, ab, ts in cur:
        if (mid, slot) != key:
            key, t0, seen_ts, n_up = (mid, slot), ts, set(), 0
        if ts == t0 or ab.startswith("special_bonus") or ts in seen_ts or n_up >= 10:
            continue
        seen_ts.add(ts); n_up += 1
        counts[(hero, ab)] += 1
    return [(h, a, n) for (h, a), n in counts.items()]


def main(days=120, source="auto"):
    ver = latest_stats_version()
    ids = json.load(open(os.path.join(HERE, "data", "stats", ver, "ability_ids.json"), encoding="utf-8"))
    hl = json.load(open(os.path.join(HERE, "data", "herolist.json"), encoding="utf-8"))["result"]["data"]["heroes"]
    hero_slug = {h["id"]: h["name"] for h in hl}
    def opendota_rows():
        url = "https://api.opendota.com/api/explorer?sql=" + urllib.parse.quote(SQL.format(days=min(int(days), 180)))
        return json.load(urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "sloppy-skill-priority"}), timeout=180))["rows"]

    if source == "auto" and not os.path.exists(DEMOS_DB):
        source = "opendota"
    if source in ("auto", "demos"):
        rows = [{"hero_id": h, "slug": a, "n": n} for h, a, n in rows_from_demos(days)]
        have = {r["hero_id"] for r in rows}
        if source == "auto":
            # DEMOS currently records skill builds for ~97 of 127 heroes (parser gap, tracked
            # separately) — the missing heroes are topped up from OpenDota until that is fixed.
            extra = [r for r in opendota_rows() if r["hero_id"] not in have]
            rows += extra
            source = "demos" if not extra else f"demos + opendota for {len({r['hero_id'] for r in extra})} heroes missing in DEMOS"
    else:
        rows = opendota_rows()
    ults = ultimates()
    # abilities that belong to the hero's own kit (KV), so stolen/duplicated ids are ignored
    kit = {}
    for f in glob.glob(os.path.join(HERE, "data", "stats", ver, "heroes", "npc_dota_hero_*.txt")):
        t = open(f, encoding="utf-8", errors="replace").read()
        kit[os.path.basename(f)[:-4]] = {a for _, a in re.findall(r'"Ability(\d+)"\s+"([a-z_0-9]+)"', t)
                                         if not a.startswith("special_bonus")}
    pts = collections.defaultdict(dict)
    for r in rows:
        slug = r.get("slug") or ids.get(str(r.get("ability")))
        hero = hero_slug.get(r["hero_id"])
        if not slug or not hero or slug not in kit.get(hero, ()) or slug in ults:
            continue
        pts[hero][slug] = pts[hero].get(slug, 0) + int(r["n"])
    out = {}
    for hero, d in pts.items():
        d = {a: n for a, n in d.items() if n >= 0.03 * sum(d.values())}     # drop noise ids
        tot, nb = sum(d.values()), len(d)
        if tot < 200 or nb < 2:                                           # too few pro games
            continue
        for a, n in d.items():
            share = n / tot
            out[a] = {"share": round(share, 3),
                      "mult": round(min(1.3, max(0.7, 1 + 1.5 * (share - 1.0 / nb))), 3)}
    doc = {"_doc": __doc__.strip().split("\n\n")[0] + " See tools/fetch_skill_priority.py.",
           "source": source, "window_days": int(days),
           "fetched": time.strftime("%Y-%m-%d"), "stats_version": ver, "abilities": dict(sorted(out.items()))}
    p = os.path.join(HERE, "data", "rules", "ability_priority.json")
    json.dump(doc, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{p}: {len(out)} abilities, {len(pts)} heroes")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 365, sys.argv[2] if len(sys.argv) > 2 else "auto")
