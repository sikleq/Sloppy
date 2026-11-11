# -*- coding: utf-8 -*-
"""Pro drafts and winners of older Tier 1-2 leagues from Valve's Web API -> .cache/pro_drafts.sqlite (not in git).

Why: the match database behind signal R starts in 2024 (7.35b), so the weights can be checked against what pros did
after a patch on 27 windows only. Picks, bans and the winner of every league match back to 7.08 (2018) give ~80 more.

    python tools/fetch_pro_drafts.py LEAGUES.json [--from 2017-12-01] [--to 2024-01-04] [--max-calls 50000]
    python tools/fetch_pro_drafts.py LEAGUES.json --retry-missing   # matches skipped on a Valve error, once more

LEAGUES.json: [{"league_id": 10749, "tier": "1", ...}, ...] (league ids of Tier 1-2 tournaments, e.g. from Liquipedia
infoboxes). Key: env STEAM_API_KEY, never printed or stored.

Valve's GetMatchDetails answers HTTP 500 for most old matches, so a match's full record is read with
GetMatchHistoryBySequenceNum(start_at_match_seq_num = its seq num, 1 match). One call per match plus one per 100 matches
of a league's history; paced (PAUSE s), resumable (done leagues and matches are skipped), stops on 403 / 429.
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, ".cache", "pro_drafts.sqlite")
BASE = "https://api.steampowered.com/IDOTA2Match_570/"
UA = "SloppyResearch/1.0 (https://github.com/sikleq/Sloppy)"
PAUSE = 1.05                  # seconds between calls (Valve: 100 000 calls a day per key)
RETRIES = 4
CAPTAINS_MODE = 2
GIVE_UP = 30                  # a league with no draft in its first 30 matches is not captains-mode play (an open
                              # qualifier of ESL One Katowice 2018: 8 drafts in 500 matches), the rest is skipped

SCHEMA = """
CREATE TABLE IF NOT EXISTS leagues_done (league_id INTEGER PRIMARY KEY, matches INTEGER, done_at INTEGER);
CREATE TABLE IF NOT EXISTS matches (match_id INTEGER PRIMARY KEY, league_id INTEGER, start_time INTEGER,
                                    radiant_win INTEGER, lobby_type INTEGER, game_mode INTEGER);
CREATE TABLE IF NOT EXISTS draft_actions (match_id INTEGER, ord INTEGER, team_side INTEGER, is_pick INTEGER,
                                          hero_id INTEGER, PRIMARY KEY (match_id, ord));
CREATE TABLE IF NOT EXISTS missing (match_id INTEGER PRIMARY KEY, reason TEXT);
"""


class Stop(RuntimeError):
    """Valve refused the key or the rate (403 / 429): stop the run, keep what is stored."""


def connect(path=OUT):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    return con


def _ts(day):
    return int(dt.datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())


class Api:
    def __init__(self, key, max_calls, pause=PAUSE, opener=urllib.request.urlopen, sleep=time.sleep):
        self.key, self.left, self.pause, self.open, self.sleep = key, max_calls, pause, opener, sleep

    def get(self, method, **params):
        if self.left <= 0:
            raise Stop("call budget used up")
        url = BASE + method + "/v1/?" + urllib.parse.urlencode({"key": self.key, **params})
        for attempt in range(RETRIES):
            self.left -= 1
            self.sleep(self.pause)
            try:
                with self.open(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code in (401, 403, 429):
                    raise Stop(f"HTTP {e.code} from {method}") from None
                if attempt == RETRIES - 1:
                    raise
            except (urllib.error.URLError, TimeoutError):
                if attempt == RETRIES - 1:
                    raise
            self.sleep(self.pause * 4 * (attempt + 1))
        raise RuntimeError("unreachable")


def league_matches(api, league_id):
    """[(match_id, match_seq_num, start_time)] of a league, newest first, all pages."""
    out, start = [], None
    while True:
        p = {"league_id": league_id, "matches_requested": 100}
        if start:
            p["start_at_match_id"] = start
        res = api.get("GetMatchHistory", **p).get("result", {})
        ms = res.get("matches") or []
        out += [(m["match_id"], m["match_seq_num"], m["start_time"]) for m in ms]
        if not ms or not res.get("results_remaining"):
            return out
        start = ms[-1]["match_id"] - 1


def store_match(con, rec, league_id):
    """Write one match's record (from GetMatchHistoryBySequenceNum); False when it is not a Captains Mode draft
    (Captains Draft 16 and other modes also list bans, but are not what pros play)."""
    pb = rec.get("picks_bans") or []
    if not pb or rec.get("radiant_win") is None or rec.get("game_mode") != CAPTAINS_MODE:
        return False
    con.execute("INSERT OR REPLACE INTO matches VALUES (?, ?, ?, ?, ?, ?)",
                (rec["match_id"], league_id, rec.get("start_time"), int(bool(rec["radiant_win"])),
                 rec.get("lobby_type"), rec.get("game_mode")))
    con.executemany("INSERT OR REPLACE INTO draft_actions VALUES (?, ?, ?, ?, ?)",
                    [(rec["match_id"], x.get("order", i), x["team"], int(bool(x["is_pick"])), x["hero_id"])
                     for i, x in enumerate(pb)])
    return True


def fetch_league(api, con, league_id, lo, hi, log=print):
    known = {r[0] for r in con.execute("SELECT match_id FROM matches UNION SELECT match_id FROM missing")}
    todo = [m for m in league_matches(api, league_id) if lo <= m[2] < hi and m[0] not in known]
    got = 0
    for i, (match_id, seq, _) in enumerate(todo):
        if i == GIVE_UP and not got:
            log(f"league {league_id}: no drafts in the first {GIVE_UP} matches, skipped")
            break
        try:
            res = api.get("GetMatchHistoryBySequenceNum", start_at_match_seq_num=seq, matches_requested=1)
        except urllib.error.HTTPError as e:   # Valve keeps answering 500 for a few records: skip that match only
            con.execute("INSERT OR REPLACE INTO missing VALUES (?, ?)", (match_id, f"http {e.code}"))
            con.commit()
            continue
        res = res.get("result", {})
        rec = next((m for m in res.get("matches") or [] if m.get("match_id") == match_id), None)
        if rec and store_match(con, rec, league_id):
            got += 1
        else:
            con.execute("INSERT OR REPLACE INTO missing VALUES (?, ?)", (match_id, "no record" if not rec else "no draft"))
        con.commit()
    con.execute("INSERT OR REPLACE INTO leagues_done VALUES (?, ?, ?)", (league_id, got, int(time.time())))
    con.commit()
    log(f"league {league_id}: {got} drafts of {len(todo)} matches in range")
    return got


RETRY_REASONS = ("http %", "no record")   # "no draft" is a real record without captains-mode picks: never retried


def retry_missing(api, con, league_matches_of=None, log=print):
    """Ask Valve again for matches skipped on a server error or an empty answer; returns how many were recovered.

    The seq num is not stored, so the history of each league whose stored match ids span a skipped one is re-read
    (one call per 100 matches)."""
    where = " OR ".join("reason LIKE ?" for _ in RETRY_REASONS)
    ids = {r[0] for r in con.execute(f"SELECT match_id FROM missing WHERE {where}", RETRY_REASONS)}
    if not ids:
        return 0
    spans = con.execute("SELECT league_id, min(match_id), max(match_id) FROM matches GROUP BY league_id").fetchall()
    leagues = [lg for lg, lo, hi in spans if any(lo <= i <= hi for i in ids)]
    got = 0
    for lg in leagues:
        for match_id, seq, _ in (league_matches_of or league_matches)(api, lg):
            if match_id not in ids:
                continue
            ids.discard(match_id)
            try:
                res = api.get("GetMatchHistoryBySequenceNum", start_at_match_seq_num=seq, matches_requested=1)
            except urllib.error.HTTPError:
                continue
            rec = next((m for m in res.get("result", {}).get("matches") or [] if m.get("match_id") == match_id), None)
            if rec and store_match(con, rec, lg):
                con.execute("DELETE FROM missing WHERE match_id = ?", (match_id,))
                got += 1
            con.commit()
        if not ids:
            break
    log(f"retry: {got} recovered, {len(ids)} still missing")
    return got


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("leagues")
    ap.add_argument("--from", dest="lo", default="2017-12-01")
    ap.add_argument("--to", dest="hi", default="2024-01-04")
    ap.add_argument("--max-calls", type=int, default=50000)
    ap.add_argument("--retry-missing", action="store_true",
                    help="only ask again for matches skipped on a server error or an empty answer")
    a = ap.parse_args(argv)
    key = os.environ.get("STEAM_API_KEY")
    if not key:
        print("STEAM_API_KEY is not set")
        return 2
    leagues = json.load(open(a.leagues, encoding="utf-8"))
    con, api = connect(), Api(key, a.max_calls)
    done = {r[0] for r in con.execute("SELECT league_id FROM leagues_done")}
    lo, hi = _ts(a.lo), _ts(a.hi)
    try:
        if a.retry_missing:
            retry_missing(api, con)
            leagues = []
        for lg in leagues:
            if lg["league_id"] not in done:
                try:
                    fetch_league(api, con, lg["league_id"], lo, hi)
                except (urllib.error.URLError, TimeoutError) as e:   # history pages failed: next run retries it
                    print(f"league {lg['league_id']}: {getattr(e, 'code', e)}, left for the next run")
    except Stop as e:
        print("stopped:", e)
    n = con.execute("SELECT count(*) FROM matches").fetchone()[0]
    print(f"{n} matches with drafts in {OUT}; calls left {api.left}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
