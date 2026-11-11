"""tools/fetch_pro_drafts.py: old pro drafts from Valve's Web API (no network here: the API is faked)."""
import io
import json
import os
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import fetch_pro_drafts as F  # noqa: E402


class FakeApi:
    def __init__(self, history, records):
        self.history, self.records, self.calls = history, records, []

    def get(self, method, **p):
        self.calls.append((method, p))
        if method == "GetMatchHistory":
            ms = [m for m in self.history if "start_at_match_id" not in p or m["match_id"] <= p["start_at_match_id"]][:2]
            left = len([m for m in self.history if ms and m["match_id"] < ms[-1]["match_id"]])
            return {"result": {"matches": ms, "results_remaining": left}}
        rec = self.records.get(p["start_at_match_seq_num"])
        return {"result": {"matches": [rec] if rec else []}}


def _rec(mid, win=True, draft=True):
    pb = [{"is_pick": False, "hero_id": 1, "team": 0, "order": 0}, {"is_pick": True, "hero_id": 2, "team": 1, "order": 1}]
    return {"match_id": mid, "start_time": 1000 + mid, "radiant_win": win, "lobby_type": 1, "game_mode": 2,
            "picks_bans": pb if draft else []}


def test_fetch_league_pages_history_and_stores_drafts(tmp_path):
    hist = [{"match_id": m, "match_seq_num": 100 + m, "start_time": 1000 + m} for m in (30, 20, 10)]
    api = FakeApi(hist, {130: _rec(30), 120: _rec(20, draft=False), 110: _rec(10, win=False)})
    con = F.connect(str(tmp_path / "d.sqlite"))
    got = F.fetch_league(api, con, 7, 0, 10 ** 9, log=lambda *a: None)
    assert got == 2                                                    # the match without a draft is not stored
    assert sum(1 for m, _ in api.calls if m == "GetMatchHistory") == 2  # two pages of history
    assert con.execute("SELECT match_id, radiant_win FROM matches ORDER BY 1").fetchall() == [(10, 0), (30, 1)]
    assert con.execute("SELECT count(*) FROM draft_actions WHERE is_pick = 0").fetchone()[0] == 2
    assert con.execute("SELECT reason FROM missing").fetchall() == [("no draft",)]
    # a second run skips the league's known matches
    api.calls.clear()
    F.fetch_league(api, con, 7, 0, 10 ** 9, log=lambda *a: None)
    assert all(m == "GetMatchHistory" for m, _ in api.calls)


def test_fetch_league_gives_up_on_a_league_without_drafts(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "GIVE_UP", 3)
    hist = [{"match_id": m, "match_seq_num": 100 + m, "start_time": 1000 + m} for m in range(10, 0, -1)]
    api = FakeApi(hist, {100 + m: _rec(m, draft=False) for m in range(1, 11)})
    con = F.connect(str(tmp_path / "d.sqlite"))
    assert F.fetch_league(api, con, 7, 0, 10 ** 9, log=lambda *a: None) == 0
    assert sum(1 for m, _ in api.calls if m == "GetMatchHistoryBySequenceNum") == 3


def test_fetch_league_skips_a_match_valve_keeps_failing(tmp_path):
    hist = [{"match_id": m, "match_seq_num": 100 + m, "start_time": 1000 + m} for m in (2, 1)]
    api = FakeApi(hist, {101: _rec(1)})
    real = api.get

    def get(method, **p):
        if p.get("start_at_match_seq_num") == 102:
            raise urllib.error.HTTPError("u", 500, "err", {}, io.BytesIO(b""))
        return real(method, **p)
    api.get = get
    con = F.connect(str(tmp_path / "d.sqlite"))
    assert F.fetch_league(api, con, 7, 0, 10 ** 9, log=lambda *a: None) == 1
    assert con.execute("SELECT match_id, reason FROM missing").fetchall() == [(2, "http 500")]


def test_retry_missing_recovers_server_errors_but_not_matches_without_a_draft(tmp_path):
    hist = [{"match_id": m, "match_seq_num": 100 + m, "start_time": 1000 + m} for m in (4, 3, 2, 1)]
    api = FakeApi(hist, {101: _rec(1), 102: _rec(2), 104: _rec(4)})
    con = F.connect(str(tmp_path / "d.sqlite"))
    F.store_match(con, _rec(1), 7)
    F.store_match(con, _rec(4), 7)
    con.executemany("INSERT INTO missing VALUES (?, ?)", [(2, "http 500"), (3, "no draft")])
    assert F.retry_missing(api, con, log=lambda *a: None) == 1
    assert con.execute("SELECT match_id FROM missing").fetchall() == [(3,)]
    asked = [p["start_at_match_seq_num"] for m, p in api.calls if m == "GetMatchHistoryBySequenceNum"]
    assert asked == [102]                                              # "no draft" is never asked again


def test_fetch_league_keeps_only_the_date_range(tmp_path):
    hist = [{"match_id": m, "match_seq_num": 100 + m, "start_time": t} for m, t in ((2, 5000), (1, 50))]
    api = FakeApi(hist, {102: _rec(2), 101: _rec(1)})
    con = F.connect(str(tmp_path / "d.sqlite"))
    assert F.fetch_league(api, con, 7, 0, 1000, log=lambda *a: None) == 1


def test_api_stops_on_rate_limit_and_never_puts_the_key_in_output(capsys):
    def opener(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many", {}, io.BytesIO(b""))
    api = F.Api("SECRETKEY", 10, opener=opener, sleep=lambda s: None)
    with pytest.raises(F.Stop) as e:
        api.get("GetMatchHistory", league_id=1)
    assert "SECRETKEY" not in str(e.value) and "429" in str(e.value)


def test_api_retries_a_server_error_then_succeeds():
    calls = []

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def opener(req, timeout):
        calls.append(1)
        if len(calls) == 1:
            raise urllib.error.HTTPError(req.full_url, 500, "err", {}, io.BytesIO(b""))
        return Resp(json.dumps({"result": {"ok": 1}}).encode())
    api = F.Api("K", 10, opener=opener, sleep=lambda s: None)
    assert api.get("X") == {"result": {"ok": 1}} and len(calls) == 2


def test_api_budget_stops_the_run():
    api = F.Api("K", 0, sleep=lambda s: None)
    with pytest.raises(F.Stop):
        api.get("X")
