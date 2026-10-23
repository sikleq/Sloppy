"""tools/liquipedia_cache.py: never two requests closer than the pause (across runs), never re-download an unchanged
page, stop at once on 429 (owner 2026-10-23: Liquipedia blocked us for request bursts)."""
import pytest

from tools import liquipedia_cache as lc


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(lc, "ROOT", str(tmp_path))
    return tmp_path


def test_throttle_waits_out_the_pause_left_by_an_earlier_run(root):
    clock = {"t": 100.0}
    slept = []
    lc._throttle(2.2, now=lambda: clock["t"], sleep=slept.append)          # first request: no wait
    clock["t"] = 101.0                                                    # next one 1 s later
    lc._throttle(2.2, now=lambda: clock["t"], sleep=slept.append)
    assert slept == [pytest.approx(1.2)]
    clock["t"] = 200.0
    lc._throttle(31.0, now=lambda: clock["t"], sleep=slept.append)         # long after: no wait
    assert len(slept) == 1


def test_only_new_or_changed_pages_are_downloaded():
    index = {"A/Changelogs": {"revid": 5}, "B": {"revid": 7}}
    remote = {"A/Changelogs": 5, "B": 8, "C": 1, "Gone": None}
    assert lc.stale(["A/Changelogs", "B", "C", "Gone"], remote, index) == ["B", "C"]


def test_sync_stores_text_and_skips_it_next_time(root, monkeypatch):
    calls = []

    def fake_request(params, pause=lc.QUERY_PAUSE):
        calls.append(params["prop"])
        titles = params["titles"].split("|")
        if params["prop"] == "info":
            return {"query": {"pages": {t: {"title": t, "lastrevid": 3} for t in titles}}}
        return {"query": {"pages": {t: {"title": t, "revisions": [{"revid": 3, "slots": {"main": {"*": "text " + t}}}]}
                                    for t in titles}}}

    monkeypatch.setattr(lc, "_request", fake_request)
    assert lc.sync(["Roshan"], log=lambda *_: None) == ["Roshan"]
    assert lc.read("wikitext", "Roshan") == "text Roshan"
    assert lc.sync(["Roshan"], log=lambda *_: None) == []                  # same revision: no download
    assert calls == ["info", "revisions", "info"]


def test_429_stops_the_run(root, monkeypatch):
    def blocked(params, pause=lc.QUERY_PAUSE):
        raise lc.Blocked("429")

    monkeypatch.setattr(lc, "_request", blocked)
    assert lc.main(["sync", "--title", "Roshan"]) == 2
