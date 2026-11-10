"""The calendar's Test servers tab (2026-11-10): Valve's client versions of Experimental, Staging and the live game, the
muk-as log of them, and the page built from it. No network: the fetch functions get their input as arguments."""
import html
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


TG_PAGE = """<div class="tgme_widget_message" data-post="DOTA_DM_SPAM/2479">
<div class="tgme_widget_message_text">_dota2_db | 40 | <b>api_test_server_version_active</b> | <code>6424 =&gt; 6426</code><br/>
<b>api_test_server_version_deploy</b> | <code>6424 =&gt; 6426</code></div>
<time datetime="2021-12-09T01:58:55+00:00" class="time">01:58</time></div>
<div class="tgme_widget_message" data-post="DOTA_DM_SPAM/2483">
<div class="tgme_widget_message_text"><b>api_server_version_active</b> | <code>5111 =&gt; 5112</code></div>
<time datetime="2021-12-10T20:11:57+00:00" class="time">20:11</time></div>
<div class="tgme_widget_message" data-post="DOTA_DM_SPAM/6981">
<div class="tgme_widget_message_text">&#9679; <b>api_test_server_version_deploy [247060 - Dota 2 Test 2 Server]</b> | <code>6617 =&gt; 6618</code><br/>
&#9679; <b>api_test_server_version_active [247040 - Dota 2 Test 2]</b> | <code>6617 =&gt; 6618</code><br/>
&#9679; <b>api_server_version_active [1422450 - Dota 2(?) Hidden Test]</b> | <code>1 =&gt; 2</code></div>
<time datetime="2023-03-02T04:06:04+00:00" class="time">04:06</time></div>
<div class="tgme_widget_message" data-post="DOTA_DM_SPAM/8494">
<div class="tgme_widget_message_text">_dota2_db | 59 | &#9679; <b>2305270 - Dota 2 Staging</b> | <code>2702 =&gt; 2705</code></div>
<time datetime="2023-09-11T21:19:00+00:00" class="time">21:19</time></div>
<div class="tgme_widget_message" data-post="DOTA_DM_SPAM/8495">
<div class="tgme_widget_message_text">_dota2_db | 66 | &#9679; <b>2305290 - Dota 2 Staging Server</b> | <code>2705 =&gt; 2706</code><br/>
dota2_client_git | &#9679; 570 - Dota 2 | 5833 | 6a2c0bc7b8b87e60</div>
<time datetime="2023-09-11T21:46:00+00:00" class="time">21:46</time></div>"""


def test_the_telegram_posts_give_the_active_versions_of_both_formats():
    ids, rows = fetch.parse_telegram_page(TG_PAGE)
    assert ids == [2479, 2483, 6981, 8494, 8495]
    assert [(b["branch"], b["from"], b["version"], b["time"], b["source"]) for b in rows] == [
        ("experimental", 6424, 6426, "2021-12-09T01:58:55Z", "t.me/DOTA_DM_SPAM"),     # unnamed "test" = 247040
        ("public", 5111, 5112, "2021-12-10T20:11:57Z", "t.me/DOTA_DM_SPAM"),           # unnamed = the live game
        ("experimental", 6617, 6618, "2023-03-02T04:06:04Z", "t.me/DOTA_DM_SPAM"),     # deploy lines and other apps out
        ("staging", 2702, 2705, "2023-09-11T21:19:00Z", "t.me/DOTA_DM_SPAM")]          # "● app | a => b"; servers and git out


def test_the_telegram_walk_reads_cached_pages_and_stops_at_the_oldest(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch, "TG_CACHE", tmp_path)
    (tmp_path / "7000.html").write_text(TG_PAGE, encoding="utf-8")
    (tmp_path / "2479.html").write_text('<div data-post="DOTA_DM_SPAM/1">Channel created</div>', encoding="utf-8")
    monkeypatch.setattr(fetch.urllib.request, "urlopen", lambda *a, **k: pytest.fail("fetched a cached page"))
    rows = fetch.fetch_telegram(7000)
    assert len(rows) == 4


def test_validate_rejects_a_broken_file():
    bad = fetch.empty_data()
    bad["builds"].append({"branch": "beta", "from": 1, "version": 2, "time": "2026-11-10T12:00:00Z", "source": "valve-api"})
    with pytest.raises(ValueError):
        fetch.validate(bad)


def test_the_committed_file_is_valid_and_starts_with_the_log():
    data = fetch.validate(fetch.load())
    assert set(data["apps"].values()) == {"experimental", "staging", "public"}
    assert data["builds"][0]["time"] < "2022-01-01"                                    # the channel reaches 2021
    staging = [b for b in data["builds"] if b["branch"] == "staging"]
    assert staging and staging[0]["time"] >= "2023-01-31"                              # Staging was born then


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


def _weekly(tmp_path, *rows, now=datetime(2026, 7, 1, tzinfo=timezone.utc), history=HISTORY, series="both"):
    builds = _load(tmp_path, _raw(*rows))
    return builds, bb.weekly_svg(builds, bb.releases(history), now, series=series)


_BAR = r'class="tb-bar tb-{}"[^>]*? x="[\d.]+" y="([\d.]+)" width="[\d.]+" height="([\d.]+)"'


def test_weekly_counts_cover_every_week_and_name_the_patch_it_led_to(tmp_path):
    builds = _load(tmp_path, _raw(("public", 9, "2026-06-01T21:30:00Z"),
                                  ("experimental", 1, "2026-05-25T10:00:00Z"), ("experimental", 2, "2026-05-27T10:00:00Z"),
                                  ("staging", 3, "2026-06-09T10:00:00Z")))
    groups = bb.group_by_patch(builds, bb.releases(HISTORY))
    weeks = bb.weekly_counts(builds, datetime(2026, 6, 23, tzinfo=timezone.utc), groups)
    assert [(str(m), e, s, p) for m, e, s, p in weeks] == [
        ("2026-05-25", 2, 0, "7.41"), ("2026-06-01", 0, 0, None), ("2026-06-08", 0, 1, "7.41a"), ("2026-06-15", 0, 0, None),
        ("2026-06-22", 0, 0, None)]


def test_the_wide_chart_draws_experimental_up_and_staging_down(tmp_path):
    _, svg = _weekly(tmp_path, ("experimental", 1, "2026-06-01T10:00:00Z"), ("staging", 2, "2026-06-01T12:00:00Z"))
    mid = float(re.search(r'class="cal-ig-axis is-base" x1="[\d.]+" y1="([\d.]+)"', svg)[1])
    exp = re.search(_BAR.format("experimental"), svg)
    stg = re.search(_BAR.format("staging"), svg)
    assert abs(float(exp[1]) + float(exp[2]) - mid) < 0.2                              # up from the middle line
    assert abs(float(stg[1]) - mid) < 0.2                                              # down from it
    assert "viewBox=\"0 0 1300" in svg and "tb-weekly" in svg                          # one wide chart


def test_one_server_alone_rises_from_the_bottom_on_the_full_height(tmp_path):
    _, svg = _weekly(tmp_path, ("experimental", 1, "2026-06-01T10:00:00Z"), ("staging", 2, "2026-06-01T12:00:00Z"),
                     series="staging")
    base = float(re.search(r'class="cal-ig-axis is-base" x1="[\d.]+" y1="([\d.]+)"', svg)[1])
    stg = re.search(_BAR.format("staging"), svg)
    assert "tb-bar tb-experimental" not in svg and " hidden" in svg.split(">")[0]      # hidden until its button
    _, both = _weekly(tmp_path, ("experimental", 1, "2026-06-01T10:00:00Z"), ("staging", 2, "2026-06-01T12:00:00Z"))
    stg_both = re.search(_BAR.format("staging"), both)
    assert abs(float(stg[1]) + float(stg[2]) - base) < 0.2                             # up from the bottom line
    assert abs(float(stg[2]) - 2 * float(stg_both[2])) < 0.2                           # twice as tall as in "both"


def test_the_card_has_three_charts_and_a_switch(tmp_path):
    builds = _load(tmp_path, _raw(("experimental", 1, "2026-06-01T10:00:00Z")))
    rels = bb.releases(HISTORY)
    m = bb.patch_moments(rels, builds)
    card = bb.weekly_card(builds, rels, NOW, m, bb.group_by_patch(builds, rels, m))
    assert re.findall(r'<svg class="tb-weekly" data-series="(\w+)"', card) == ["both", "experimental", "staging"]
    assert re.findall(r'tb-series-btn[^"]*" data-series="(\w+)" aria-pressed="(\w+)"', card) == [
        ("both", "true"), ("experimental", "false"), ("staging", "false")]


def test_every_week_and_patch_line_has_a_tooltip_and_its_patch(tmp_path):
    _, svg = _weekly(tmp_path, ("public", 11, "2026-06-01T21:30:00Z"), ("experimental", 1, "2026-05-25T10:00:00Z"),
                     ("staging", 2, "2026-06-01T08:00:00Z"))
    weeks = re.findall(r'class="tb-hit tb-tip-target"([^>]*?) data-tooltip="([^"]+)"', svg)
    assert weeks and all("Week of" in t for _, t in weeks)
    patch = re.search(r'class="tb-hit tb-patch-hit tb-tip-target" data-patch="7.41"[^>]*? data-tooltip="([^"]+)"', svg)
    text = html.unescape(patch[1])
    assert "came out 1 Jun 2026 21:30 UTC" in text and "Staging: 1 build, 13 h before" in text
    assert "Experimental: 1 build," in text


def test_the_patch_tooltip_tells_when_staging_began_and_ended():
    t = datetime(2026, 6, 1, 21, 30, tzinfo=timezone.utc)
    b = lambda h: {"branch": "staging", "time": t - timedelta(hours=h), "timed": True, "version": 1, "from": 0}  # noqa: E731
    g = {"version": "7.41", "moment": t, "date": t.date(), "exact": True, "partial": False,
         "experimental": [], "staging": [b(50), b(2)]}
    text = html.unescape(bb._patch_tip(g, bb.group_stats(g, NOW)))
    assert "Staging: 2 builds, the first 2 d 2 h and the last 2 h before" in text and "Experimental: 0 builds" in text


def test_only_whole_patches_are_labelled_on_the_wide_chart(tmp_path):
    _, svg = _weekly(tmp_path, ("public", 11, "2026-06-01T21:30:00Z"), ("public", 12, "2026-06-20T20:00:00Z"),
                     ("experimental", 1, "2026-05-01T10:00:00Z"))
    assert svg.count('class="tb-patch-line"') == 1 and svg.count('class="tb-patch-line is-letter"') == 1
    assert re.findall(r'class="tb-patch-lbl"[^>]*>([^<]+)<', svg) == ["7.41"]


def test_the_half_names_stand_by_the_middle_line_clear_of_the_tick_numbers(tmp_path):
    _, svg = _weekly(tmp_path, ("experimental", 1, "2026-06-01T10:00:00Z"))
    mid = float(re.search(r'class="cal-ig-axis is-base" x1="[\d.]+" y1="([\d.]+)"', svg)[1])
    ticks = [float(y) for y in re.findall(r'class="tb-ytick" x="[\d.]+" y="([\d.]+)"', svg)]
    names = [float(y) for y in re.findall(r'class="tb-half-name[^"]*" x="[\d.]+" y="([\d.]+)"', svg)]
    assert len(names) == 2 and all(abs(n - mid) < 25 for n in names)
    assert all(abs(n - t) >= 14 for n in names for t in ticks)                         # 12px text never touches a tick
    assert '<div class="tb-weekly-scroll">' in bb.render_panel([], HISTORY, NOW)       # a phone scrolls it sideways


def test_before_each_patch_shows_both_spans_with_their_numbers(tmp_path):
    builds = _load(tmp_path, _raw(("public", 9, "2026-03-01T00:00:00Z"), ("public", 11, "2026-06-01T21:30:00Z"),
                                  ("experimental", 1, "2026-05-10T10:00:00Z"), ("staging", 3, "2026-05-28T21:30:00Z")))
    history = [{"version": "7.40", "date": "01.04.2026"}] + HISTORY
    card = bb.lag_card(bb.group_by_patch(builds, bb.releases(history)), NOW)
    row = re.search(r'<div class="tb-lag-row tb-tip-target" data-patch="7.41".*?</div>', card)[0]
    assert "22 d 11 h" in row and "4 d 0 h" in row
    shares = [float(w) for w in re.findall(r'--p:([\d.]+)', row)]
    assert shares[0] == 1.0                                                            # the longest lead fills its column
    assert shares[1] == 1.0 and "is-over" in row                                       # 96 h is over the 48 h scale
    assert re.search(r'tb-lag-bar[^>]*></span><span class="tb-lag-val">', row)         # the number right after its bar


def test_whole_patches_only_gives_a_whole_patch_the_run_up_of_its_letter_patches(tmp_path):
    history = [{"version": "7.40", "date": "01.03.2026"}, {"version": "7.40b", "date": "01.04.2026"},
               {"version": "7.41", "date": "01.06.2026"}]
    builds = _load(tmp_path, _raw(("public", 9, "2026-03-01T20:00:00Z"), ("public", 10, "2026-04-01T20:00:00Z"),
                                  ("public", 11, "2026-06-01T20:00:00Z"),
                                  ("experimental", 1, "2026-03-20T10:00:00Z"),      # under 7.40b, already for 7.41
                                  ("experimental", 2, "2026-05-01T10:00:00Z")))
    rels = bb.releases(history)
    m = bb.patch_moments(rels, builds)
    every = bb.group_by_patch(builds, rels, m)
    whole = bb.group_by_patch(builds, bb.major_releases(rels), m)
    assert [g["version"] for g in every] == ["7.40b", "7.41"] and [g["version"] for g in whole] == ["7.41"]
    assert len(whole[0]["experimental"]) == 2
    card = bb.lag_card(every, NOW, whole)
    lists = re.findall(r'<div class="tb-lag" data-lag="(\w+)"( hidden)?>(.*?)</div></div>(?=<div class="tb-lag"|</div>$)', card)
    assert [(k, bool(h)) for k, h, _ in lists] == [("all", False), ("major", True)]
    assert "tb-lag-btn active\" data-lag=\"all\"" in card and 'data-lag="major" aria-pressed="false"' in card
    assert "73 d 10 h" in lists[1][2]                                                  # 20 Mar 10:00 → 1 Jun 20:00


def test_hours_and_weekdays_have_the_switch_and_a_tooltip_per_column():
    series = {"experimental": [3, 0, 1], "staging": [1, 2, 0]}
    card = bb.when_card("Hour of day, UTC", series, ["00", "01", "02"], "hour", ["00:00", "01:00", "02:00"])
    assert re.findall(r'<svg class="tb-bars" data-chart="hour" data-series="(\w+)"', card) == ["both", "experimental", "staging"]
    assert card.count('class="tb-series-btn') == 0 and card.count("tb-series-btn") == 3
    staging = re.search(r'<svg class="tb-bars" data-chart="hour" data-series="staging".*?</svg>', card)[0]
    assert "tb-bar tb-experimental" not in staging
    tips = [html.unescape(t) for t in re.findall(r'class="tb-hit tb-tip-target"[^>]*? data-tooltip="([^"]+)"', card)]
    assert len(tips) == 9 and tips[0] == "<b>00:00</b><br>Experimental: 3<br>Staging: 1"


def test_a_one_server_weekly_chart_tells_only_that_server_on_hover(tmp_path):
    _, svg = _weekly(tmp_path, ("experimental", 1, "2026-06-01T10:00:00Z"), ("staging", 2, "2026-06-01T12:00:00Z"),
                     series="staging")
    tips = [html.unescape(t) for t in re.findall(r'class="tb-hit tb-tip-target"[^>]*data-tooltip="([^"]+)"', svg)]
    assert tips and all("Staging:" in t and "Experimental" not in t for t in tips)


def test_the_year_filter_spans_the_log_and_every_piece_carries_its_year(tmp_path):
    builds = _load(tmp_path, _raw(("public", 11, "2026-06-01T21:30:00Z"), ("experimental", 1, "2025-05-10T10:00:00Z"),
                                  ("staging", 2, "2026-05-30T10:00:00Z")))
    page = bb.render_panel(builds, HISTORY, NOW)
    assert re.findall(r'<select class="cal-mode-select tb-year-(\w+)">(.*?)</select>', page) == [
        ("from", '<option value="2025" selected>2025</option><option value="2026">2026</option>'),
        ("to", '<option value="2025">2025</option><option value="2026" selected>2026</option>')]
    assert 'data-count="2025:1" data-what="Experimental builds"' in page and 'data-median="lead"' in page
    assert re.search(r'<div class="tb-lag-row tb-tip-target" data-patch="7.41" data-year="2026" data-lead="\d+" data-lag="\d+"', page)
    assert all(re.search(r'<tr data-year="\d{4}">', t) for t in re.findall(r"<tbody>(<tr.*?)</tbody>", page))
    assert re.search(r'class="tb-bar tb-experimental"[^>]* data-t="\d+" data-v="1"', page)        # weekly: time and value
    assert re.search(r'class="tb-hit tb-tip-target" data-i="10" data-name="10:00 to 10:59 UTC" '
                     r'data-c-experimental="2025:1" data-c-staging="2026:1"', page)                 # hours: counts by year


def test_counts_by_year_split_the_hour_chart():
    t = lambda y, h: {"branch": "staging", "time": datetime(y, 1, 5, h, tzinfo=timezone.utc), "timed": True}  # noqa: E731
    got = bb.counts_by_year([t(2024, 3), t(2025, 3), t(2025, 4)], "staging", lambda x: x.hour, 24)
    assert got[2024][3] == 1 and got[2025][3] == 1 and got[2025][4] == 1 and bb._by_year_attr(got, 3) == "2024:1,2025:1"


def test_the_year_filter_script_redraws_with_the_same_steps_as_the_generator():
    js = (ROOT / "src" / "js" / "calendar-builds.js").read_text(encoding="utf-8")
    steps = re.search(r"const NICE = \[([\d, ]+)\]", js)[1]
    py = __import__("inspect").getsource(bb._nice_top)
    assert f"({steps})" in py.replace(" ", "").replace(",", ", ") or steps.replace(" ", "") in py.replace(" ", "")
    for hook in ("tb-year-from", "tb-year-to", "data-lead", "dataset.count", "dataset.median"):
        assert hook.split(".")[-1].replace("data-", "") in js


def test_the_series_switch_changes_the_svg_attribute_not_a_property():
    # 2026-11-10: `svg.hidden = …` did nothing (an <svg> has no .hidden property), the switch looked dead
    js = (ROOT / "src" / "js" / "calendar-builds.js").read_text(encoding="utf-8")
    assert "toggleAttribute('hidden'" in js and not re.search(r"svg\.hidden\s*=", js)


def test_the_weekly_axis_starts_with_its_month_and_year(tmp_path):
    _, svg = _weekly(tmp_path, ("experimental", 1, "2025-12-29T10:00:00Z"), now=datetime(2026, 9, 1, tzinfo=timezone.utc))
    assert re.search(r'class="cal-ig-spark-lbl is-year is-start"[^>]*>Dec 2025<', svg)
    jan = re.search(r'class="cal-ig-spark-lbl is-year"[^>]*?( style="display:none")? x', svg)
    assert jan and jan[1]                                                              # "2026" a few days in: hidden
    assert re.search(r'class="cal-ig-spark-lbl"[^>]*>Apr 2026<', svg)                  # its year goes on the next label
    assert re.search(r'class="cal-ig-spark-lbl"[^>]*>Jul<', svg)


def test_an_empty_history_gives_an_empty_chart():
    assert bb.weekly_svg([], bb.releases(HISTORY), NOW).endswith("</svg>")


def test_hour_bars_are_stacked_in_one_column():
    svg = bb.bar_chart_svg({"experimental": [2, 0], "staging": [1, 0]}, ["00", "01"], "t")
    rects = re.findall(r'<rect class="tb-bar tb-(\w+)"[^>]*? x="([\d.]+)" y="([\d.]+)" width="[\d.]+" height="([\d.]+)"', svg)
    exp, stg = rects[0], rects[1]
    assert exp[1] == stg[1]                                                            # same column
    assert abs(float(stg[2]) + float(stg[3]) - float(exp[2])) < 0.2                    # Staging sits on Experimental


def test_the_panel_tables_are_sortable_and_follow_the_table_rules(tmp_path):
    builds = _load(tmp_path, _raw(("experimental", 1, "2026-05-10T10:00:00Z")))
    html = bb.render_panel(builds, HISTORY, NOW)
    assert html.count('<table class="tb-table') == 2
    heads = re.findall(r'<th class="sortable" data-sort="(\d+)" data-first="(asc|desc)"', html)
    assert len(heads) == 5 + 5
    assert '<details class="tb-card tb-more">' in html                                 # the long list is folded
    for body in html.split("<tbody>")[1:]:
        for row in re.findall(r"<tr>(.*?)</tr>", body.split("</tbody>")[0]):
            assert all("data-v=" in td for td in re.findall(r"<td[^>]*>", row))


def test_an_empty_file_still_renders_the_tab():
    html = bb.render_panel([], HISTORY, NOW)
    assert "no builds yet" in html and html.count("No builds yet") == 4                # both lag lists and both tables


def test_the_calendar_page_carries_both_views_and_its_script():
    page = ROOT / "dist" / "calendar.html"
    if not page.exists():
        pytest.skip("the site is not built")
    html = page.read_text(encoding="utf-8")
    assert 'data-view="patches"' in html and 'data-view="test-servers"' in html
    assert 'class="tb-panel"' in html and "src/scripts-calendar.js" in html
