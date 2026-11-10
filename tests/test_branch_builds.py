"""The calendar's Test servers tab (2026-11-10): Valve's client versions of Experimental, Staging and the live game, the
muk-as log of them, and the page built from it. No network: the fetch functions get their input as arguments."""
import importlib.util
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from patch import branch_builds as bb

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("fetch_branch_builds", ROOT / "scripts" / "fetch" / "fetch_branch_builds.py")
fetch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fetch)

EXP, STG, PUB = 247040, 2305270, 570
HISTORY = [{"version": "7.41", "date": "01.06.2026"}, {"version": "7.41a", "date": "20.06.2026"}]
NOW = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)


def _raw(*rows):
    """rows: (branch, version, time) or (branch, version, time, timed)"""
    out = []
    for r in rows:
        out.append({"branch": r[0], "from": r[1] - 1, "version": r[1], "time": r[2], "source": "muk-as/DOTA2_WEB",
                    "timed": r[3] if len(r) > 3 else True})
    return {"builds": out}


def _load(tmp_path, raw):
    p = tmp_path / "bb.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    return bb.load_builds(p)


# ---------------------------------------------------------------- the poll and the log

def test_first_check_only_remembers_the_version():
    data = fetch.merge(fetch.empty_data(), {EXP: 100, STG: 200, PUB: 300}, "2026-11-10T12:00:00Z")
    assert data["builds"] == [] and data["checks"][str(EXP)]["version"] == 100


def test_a_new_version_is_a_build_in_the_window_since_the_last_check():
    d1 = fetch.merge(fetch.empty_data(), {EXP: 100, STG: 200, PUB: 300}, "2026-11-10T12:00:00Z")
    d2 = fetch.merge(d1, {EXP: 101, STG: 200, PUB: 300}, "2026-11-10T12:15:00Z")
    b = d2["builds"][-1]
    assert (b["branch"], b["from"], b["version"], b["after"], b["timed"]) == ("experimental", 100, 101, "2026-11-10T12:00:00Z", True)
    d3 = fetch.merge(d2, {EXP: 101, STG: 201, PUB: 300}, "2026-11-11T12:15:00Z")      # a day without checks
    assert d3["builds"][-1]["timed"] is False


def test_a_rollback_is_a_build_too():
    d1 = fetch.merge(fetch.empty_data(), {EXP: 100, STG: 200, PUB: 300}, "2026-11-10T12:00:00Z")
    d2 = fetch.merge(d1, {EXP: 99, STG: 200, PUB: 300}, "2026-11-10T12:15:00Z")
    assert (d2["builds"][-1]["from"], d2["builds"][-1]["version"]) == (100, 99)


LOG = """570 - Dota 2 | [v] None => 5925 | 2023-11-16 13:28:12 (UTC+3)
247040 - Dota 2 Experimental | [v] None => 6764 | 2023-11-16 13:28:12 (UTC+3)
247040 - Dota 2 Experimental SDR Config | [v] 1 => 2 | [s] 3 => 4 | [h] a => b | 2023-11-16 14:00:00 (UTC+3)
247040 - Dota 2 Experimental | [v] 6764 => 6765 | 2023-11-17 03:10:11 (UTC+3)
2305270 - Dota 2 Staging | [v] 3332 => 3338 | 2026-11-10 04:55:35 (UTC+3)
1422450 - Dota 2(?) Hidden | [v] 1 => 2 | 2023-11-16 13:28:12 (UTC+3)"""


def test_the_log_gives_version_changes_in_utc_and_skips_its_first_lines_and_other_apps():
    got = fetch.parse_history(LOG)
    assert [(b["branch"], b["from"], b["version"], b["time"]) for b in got] == [
        ("experimental", 6764, 6765, "2023-11-17T00:10:11Z"), ("staging", 3332, 3338, "2026-11-10T01:55:35Z")]


def test_the_log_and_the_poll_never_count_one_change_twice():
    d1 = fetch.merge(fetch.empty_data(), {EXP: 6764, STG: 3332, PUB: 1}, "2023-11-16T23:00:00Z")
    d2 = fetch.merge(d1, {EXP: 6765, STG: 3332, PUB: 1}, "2023-11-17T01:00:00Z")      # our poll saw it 50 min later
    d3 = fetch.merge_history(d2, fetch.parse_history(LOG))
    exp = [b for b in d3["builds"] if b["branch"] == "experimental"]
    assert len(exp) == 1 and exp[0]["time"] == "2023-11-17T00:10:11Z"                 # the earlier sighting wins
    again = fetch.merge_history(d3, fetch.parse_history(LOG))
    assert len(again["builds"]) == len(d3["builds"])


def test_validate_rejects_a_broken_file():
    bad = fetch.empty_data()
    bad["builds"].append({"branch": "beta", "from": 1, "version": 2, "time": "2026-11-10T12:00:00Z", "source": "valve-api"})
    with pytest.raises(ValueError):
        fetch.validate(bad)


def test_the_committed_file_is_valid_and_starts_with_the_log():
    data = fetch.validate(fetch.load())
    assert set(data["apps"].values()) == {"experimental", "staging", "public"}
    assert data["builds"][0]["time"] < "2023-12-01"                                    # the log reaches back to 7.35


def test_the_state_file_keeps_the_checks_between_commits():
    committed = fetch.merge(fetch.empty_data(), {EXP: 100, STG: 200, PUB: 300}, "2026-11-10T12:00:00Z")
    state = {str(EXP): {"version": 100, "checked": "2026-11-12T09:00:00Z"}, "999": {"version": 1, "checked": "2026-11-12T09:00:00Z"}}
    data = fetch.newer_checks(committed, state)
    assert data["checks"][str(EXP)]["checked"] == "2026-11-12T09:00:00Z" and "999" not in data["checks"]
    new = fetch.merge(data, {EXP: 101, STG: 200, PUB: 300}, "2026-11-12T09:15:00Z")["builds"][-1]
    assert new["timed"] is True


def test_offline_mode_never_touches_the_network(monkeypatch, tmp_path):
    path = tmp_path / "bb.json"
    fetch.save(fetch.merge(fetch.empty_data(), {EXP: 1, STG: 2, PUB: 3}, "2026-11-10T12:00:00Z"), path)
    monkeypatch.setattr(fetch, "DATA", path)
    monkeypatch.setattr(fetch, "poll_app", lambda app: pytest.fail("polled in --offline"))
    monkeypatch.setattr(fetch, "fetch_history", lambda: pytest.fail("read the log in --offline"))
    real = ROOT / "data" / "branch_builds.json"
    before = real.read_bytes() if real.exists() else None
    assert fetch.main(["--offline"]) == 0
    assert json.loads(path.read_text(encoding="utf-8"))["checks"]                      # wrote the temporary file
    assert (real.read_bytes() if real.exists() else None) == before                    # and never the real one


def test_save_writes_one_build_per_line_and_stays_json(tmp_path):
    path = tmp_path / "bb.json"
    data = fetch.merge_history(fetch.empty_data(), fetch.parse_history(LOG))
    fetch.save(data, path)
    text = path.read_text(encoding="utf-8")
    assert json.loads(text) == data
    assert sum(1 for ln in text.splitlines() if ln.strip().startswith('{"branch"')) == 2


def test_the_job_polls_often_and_reads_the_log_daily():
    wf = (ROOT / ".github" / "workflows" / "branch-builds.yml").read_text(encoding="utf-8")
    assert 'cron: "*/15 * * * *"' in wf and "--history" in wf
    assert "--state .cache/branch_builds_state.json" in wf and "actions/cache/save" in wf


# ---------------------------------------------------------------- the page

def test_a_patch_came_out_at_the_first_live_build_of_its_day(tmp_path):
    builds = _load(tmp_path, _raw(("public", 10, "2026-05-31T20:00:00Z"), ("public", 11, "2026-06-01T21:30:00Z"),
                                  ("public", 12, "2026-06-01T23:00:00Z")))
    m = bb.patch_moments(bb.releases(HISTORY), builds)
    assert m["7.41"] == (datetime(2026, 6, 1, 21, 30, tzinfo=timezone.utc), True)
    assert m["7.41a"] == (datetime(2026, 6, 20, 12, tzinfo=timezone.utc), False)        # no live build: noon


def test_a_build_belongs_to_the_first_patch_after_it(tmp_path):
    builds = _load(tmp_path, _raw(("public", 11, "2026-06-01T21:30:00Z"),
                                  ("experimental", 1, "2026-05-10T10:00:00Z"),
                                  ("staging", 2, "2026-06-01T08:00:00Z"),
                                  ("staging", 3, "2026-06-01T22:00:00Z"),           # after 7.41 came out, same day
                                  ("experimental", 4, "2026-07-01T08:00:00Z")))
    groups = bb.group_by_patch(builds, bb.releases(HISTORY))
    assert [(g["version"], len(g["experimental"]), len(g["staging"])) for g in groups] == [
        ("7.41", 1, 1), ("7.41a", 0, 1), (None, 1, 0)]


def test_lead_and_lag_count_days_and_hours_to_the_patch(tmp_path):
    builds = _load(tmp_path, _raw(("public", 9, "2026-03-01T00:00:00Z"), ("public", 11, "2026-06-01T21:30:00Z"),
                                  ("experimental", 1, "2026-05-10T10:00:00Z"),
                                  ("experimental", 2, "2026-05-20T10:00:00Z"),
                                  ("staging", 3, "2026-06-01T08:00:00Z")))
    history = [{"version": "7.40", "date": "01.04.2026"}] + HISTORY                    # the log covers all of 7.41's run-up
    g = bb.group_by_patch(builds, bb.releases(history))[0]
    assert (g["version"], g["partial"]) == ("7.41", False)
    s = bb.group_stats(g, NOW)
    assert (s["experimental"]["count"], s["exp_lead_text"], s["staging_lag_text"]) == (2, "22 d 11 h", "13 h")


def test_a_patch_older_than_the_log_gets_an_at_least_lead(tmp_path):
    builds = _load(tmp_path, _raw(("experimental", 1, "2026-05-10T10:00:00Z")))       # the log starts after 7.40-ish
    s = bb.group_stats(bb.group_by_patch(builds, bb.releases(HISTORY))[0], NOW)
    assert s["exp_lead_text"].startswith("≥ ")


def test_fmt_span():
    assert bb.fmt_span(timedelta(days=41, hours=5, minutes=59)) == "41 d 5 h"
    assert bb.fmt_span(timedelta(hours=7)) == "7 h"


def test_only_timed_test_builds_go_into_the_hour_charts(tmp_path):
    builds = _load(tmp_path, _raw(("staging", 1, "2026-05-11T10:30:00Z"),            # Monday
                                  ("staging", 2, "2026-05-12T10:30:00Z", False),
                                  ("public", 3, "2026-05-12T10:30:00Z")))
    assert bb.hour_counts(builds, "staging")[10] == 1
    assert bb.weekday_counts(builds, "staging") == [1, 0, 0, 0, 0, 0, 0]


def test_the_timeline_has_three_rows_and_a_line_per_patch_in_range(tmp_path):
    builds = _load(tmp_path, _raw(("public", 11, "2026-06-01T21:30:00Z"), ("experimental", 1, "2026-05-10T10:00:00Z"),
                                  ("staging", 2, "2026-06-15T10:00:00Z")))
    svg = bb.timeline_svg(builds, bb.releases(HISTORY), datetime(2026, 7, 1, tzinfo=timezone.utc))
    assert svg.count('class="tb-row-band') == 3
    assert svg.count('class="tb-patch-line') == 2
    assert svg.count('class="tb-mark tb-experimental"') == 2                           # its own row and "Together"
    assert "tb-mark tb-public" not in svg                                              # the live game is not drawn


def test_patch_labels_too_close_together_are_not_all_written():
    rels = [("7.50", datetime(2026, 6, 1).date()), ("7.50a", datetime(2026, 6, 2).date())]
    svg = bb.timeline_svg([], rels, datetime(2026, 6, 20, tzinfo=timezone.utc))
    assert svg.count('class="tb-patch-line') == 2 and svg.count('class="tb-patch-lbl"') == 1


def test_the_panel_tables_are_sortable_and_follow_the_table_rules(tmp_path):
    builds = _load(tmp_path, _raw(("experimental", 1, "2026-05-10T10:00:00Z")))
    html = bb.render_panel(builds, HISTORY, NOW)
    assert html.count('<table class="tb-table') == 2
    heads = re.findall(r'<th class="sortable" data-sort="(\d+)" data-first="(asc|desc)"', html)
    assert len(heads) == 9 + 5
    for body in html.split("<tbody>")[1:]:
        for row in re.findall(r"<tr>(.*?)</tr>", body.split("</tbody>")[0]):
            assert all("data-v=" in td for td in re.findall(r"<td[^>]*>", row))


def test_an_empty_file_still_renders_the_tab():
    html = bb.render_panel([], HISTORY, NOW)
    assert "no builds yet" in html and html.count("No builds yet") == 2


def test_the_calendar_page_carries_both_views_and_its_script():
    page = ROOT / "dist" / "calendar.html"
    if not page.exists():
        pytest.skip("the site is not built")
    html = page.read_text(encoding="utf-8")
    assert 'data-view="patches"' in html and 'data-view="test-servers"' in html
    assert 'class="tb-panel"' in html and "src/scripts-calendar.js" in html
