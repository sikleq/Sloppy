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




def test_a_patch_older_than_the_log_gets_an_at_least_lead(tmp_path):
    builds = _load(tmp_path, _raw(("experimental", 1, "2026-05-10T10:00:00Z")))       # the log starts after 7.40-ish
    s = bb.group_stats(bb.group_by_patch(builds, bb.releases(HISTORY))[0], NOW)
    assert s["exp_lead_text"].startswith("≥ ")




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
    # A week keeps its counts and title; the script writes the table on hover (13 years of weeks stay light)
    weeks = re.findall(r'class="tb-hit tb-tip-target"[^>]*? data-c="(\d+),(\d+)" data-title="(Week of [^"]+)"', svg)
    assert weeks and ("1", "0", "Week of 25 May 2026") in weeks and "data-tooltip" not in svg.split("tb-patch-hit")[0]
    patch = re.search(r'class="tb-hit tb-patch-hit tb-tip-target" data-patch="7.41"[^>]*? data-tooltip="([^"]+)"', svg)
    text = html.unescape(patch[1])
    assert text == '<b>7.41</b><span class="tb-tip-sub">1 Jun 2026 21:30 UTC</span><table class="tb-tip-table"><tr class="tb-tip-key"><td>After the second-to-last Staging build</td><td>–</td></tr><tr class="tb-tip-key"><td>After the last Staging build</td><td>13 h</td></tr><tr class="tb-tip-staging"><td>First Staging build after the previous patch, before</td><td>13 h</td></tr><tr class="tb-tip-staging"><td>Staging builds</td><td>1</td></tr><tr class="tb-tip-experimental"><td>Experimental builds</td><td>1</td></tr></table>'




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






def test_hours_and_weekdays_have_the_switch_and_a_tooltip_per_column():
    series = {"experimental": [3, 0, 1], "staging": [1, 2, 0]}
    card = bb.when_card("Hour of day, UTC", series, ["00", "01", "02"], "hour", ["00:00", "01:00", "02:00"])
    assert re.findall(r'<svg class="tb-bars" data-chart="hour" data-series="(\w+)"', card) == ["both", "experimental", "staging"]
    assert card.count('class="tb-series-btn') == 0 and card.count("tb-series-btn") == 3
    staging = re.search(r'<svg class="tb-bars" data-chart="hour" data-series="staging".*?</svg>', card)[0]
    assert "tb-bar tb-experimental" not in staging
    tips = [html.unescape(t) for t in re.findall(r'class="tb-hit tb-tip-target"[^>]*? data-tooltip="([^"]+)"', card)]
    assert len(tips) == 9 and tips[0] == "<b>00:00</b>" + '<table class="tb-tip-table"><tr class="tb-tip-experimental"><td>Experimental</td><td>3</td></tr><tr class="tb-tip-staging"><td>Staging</td><td>1</td></tr></table>'   # a row per server


def test_a_one_server_weekly_chart_tells_only_that_server_on_hover(tmp_path):
    _, svg = _weekly(tmp_path, ("experimental", 1, "2026-06-01T10:00:00Z"), ("staging", 2, "2026-06-01T12:00:00Z"),
                     series="staging")
    hits = re.findall(r'<rect class="tb-hit tb-tip-target"[^>]*>', svg)
    assert hits and all('data-show="staging"' in h for h in hits)                   # the script shows that row only




def test_counts_by_year_split_the_hour_chart():
    t = lambda y, h: {"branch": "staging", "time": datetime(y, 1, 5, h, tzinfo=timezone.utc), "timed": True}  # noqa: E731
    got = bb.counts_by_year([t(2024, 3), t(2025, 3), t(2025, 4)], "staging", lambda x: x.hour, 24)
    assert got[2024][3] == 1 and got[2025][3] == 1 and got[2025][4] == 1 and bb._by_year_attr(got, 3) == "2024:1,2025:1"


def test_the_year_filter_script_redraws_with_the_same_steps_as_the_generator():
    js = (ROOT / "src" / "js" / "calendar-builds.js").read_text(encoding="utf-8")
    steps = re.search(r"const NICE = \[([\d, ]+)\]", js)[1]
    assert tuple(int(x) for x in steps.split(",")) == bb.NICE_STEPS
    assert bb._nice_top(900) == (250, 1000) and bb._nice_top(20000) == (5000, 20000)    # no list end to fall off
    for hook in ("tb-year-from", "tb-year-to", "text.tb-bar-val", "countTable", "svg.tb-weekly", "svg.tb-bars"):
        assert hook in js, hook


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






def test_staging_began_and_experimental_began_share_one_scale(tmp_path):
    _, _, every, whole = _groups(tmp_path)
    row = re.search(r'data-patch="7.41".*?</div>', bb.patch_card(every, NOW, whole))[0]
    shares = [float(x) for x in re.findall(r"--p:([\d.]+)", row)]
    assert shares[4] == 1.0 and abs(shares[3] - 2 / 31) < 0.01 and abs(shares[2] - 2 / 31) < 0.01   # one scale
    js = (ROOT / "src" / "js" / "calendar-builds.js").read_text(encoding="utf-8")
    assert ".tb-pr[data-year]" in js                                                   # Each patch follows From / To


def test_a_day_shows_a_dot_per_server_sized_by_its_builds():
    assert bb._dots({"experimental": 0, "staging": 0}) == ""
    assert bb._dots({"experimental": 5, "staging": 2}) == ('<span class="tb-dots"><i class="tb-dot-e tb-d3"></i>'
                                                           '<i class="tb-dot-s tb-d2"></i></span>')


def test_the_tab_is_laid_out_as_the_patches_view(tmp_path):
    # 2026-11-10, the owner: the year filter belongs to the charts (the calendar has its own year), the extra numbers
    # go under the calendar as on Patches, a day splits between the two servers
    builds, history, _, _ = _groups(tmp_path)
    page = bb.render_panel(builds, history, NOW)
    # The From / To years stand right under the calendar and cover the medians and Each patch too (owner 2026-11-10)
    order = [page.index(k) for k in ('class="cal-year-block is-current tb-calblock"', 'class="tb-years"',
                                     'class="cal-infographic tb-answer"', 'class="tb-plist" data-lag="major"',
                                     'class="tb-weekly"')]
    assert order == sorted(order)
    css = (ROOT / "src" / "css" / "calendar-builds.css").read_text(encoding="utf-8")
    assert ".tb-dot-e { background: #d0603a; }" in css and ".tb-d3 { width: 8px; height: 8px; }" in css
    assert re.search(r"\.tb-pr > \* \+ \* \{ border-left: 1px solid", css)           # Each patch: lines between cells


def test_patch_chips_stand_on_one_line_whatever_the_date():
    # 2026-11-10, the owner: chips moved with the length of the date beside them
    css = (ROOT / "src" / "css" / "calendar-builds.css").read_text(encoding="utf-8")
    rule = re.search(r"\.tb-pr-name \{(.*?)\}", css)[1]
    assert re.search(r"grid-template-columns: \d+px \d+px", rule)                  # two fixed columns, not content-sized


def test_the_two_view_tabs_are_one_width():
    # 2026-11-10: "Patches" and "Test servers" were each as wide as its word; the owner: no symmetry
    css = (ROOT / "src" / "css" / "calendar-builds.css").read_text(encoding="utf-8")
    rule = re.search(r"\.cal-view-tabs \{(.*?)\}", css, re.S)[1]
    assert "grid-auto-columns: 1fr" in rule and "grid-auto-flow: column" in rule


def test_the_calendar_page_carries_both_views_and_its_script():
    page = ROOT / "dist" / "calendar.html"
    if not page.exists():
        pytest.skip("the site is not built")
    html = page.read_text(encoding="utf-8")
    assert 'data-view="patches"' in html and 'data-view="test-servers"' in html
    assert 'class="tb-panel"' in html and "src/scripts-calendar.js" in html


def test_a_run_up_is_the_last_builds_without_a_long_pause(tmp_path):
    builds = _load(tmp_path, _raw(("public", 9, "2026-03-01T00:00:00Z"), ("public", 11, "2026-06-01T21:30:00Z"),
                                  ("experimental", 1, "2026-05-10T10:00:00Z"),      # 10 days before the next: cut off
                                  ("experimental", 2, "2026-05-20T10:00:00Z"),
                                  ("experimental", 3, "2026-05-25T10:00:00Z"),
                                  ("staging", 4, "2026-05-01T08:00:00Z"),           # a month earlier: another run
                                  ("staging", 5, "2026-05-28T08:00:00Z"), ("staging", 6, "2026-06-01T08:00:00Z")))
    history = [{"version": "7.40", "date": "01.04.2026"}] + HISTORY
    g = bb.group_by_patch(builds, bb.releases(history))[0]
    s = bb.group_stats(g, NOW)
    assert (len(s["exp_run"]), bb.fmt_short(s["exp_lead"])) == (2, "12 d")
    assert (len(s["stg_run"]), bb.fmt_short(s["stg_start"]), bb.fmt_short(s["staging_lag"])) == (2, "4 d", "13 h")


def test_the_second_to_last_staging_build_is_counted_too(tmp_path):
    # 2026-11-10, the owner: the last Staging build often comes with the patch; the one before it says more
    _, _, every, whole = _groups(tmp_path)
    s = bb.group_stats(whole[-1], NOW)
    assert (bb.fmt_short(s["staging_lag2"]), bb.fmt_short(s["staging_lag"])) == ("2 d", "2 h")
    one = {"version": "7.41", "moment": datetime(2026, 6, 1, tzinfo=timezone.utc), "partial": False, "experimental": [],
           "staging": [{"time": datetime(2026, 5, 31, tzinfo=timezone.utc)}]}
    assert bb.group_stats(one, NOW)["staging_lag2"] is None


def test_fmt_short_reads_at_a_glance():
    assert bb.fmt_short(timedelta(days=21, hours=7)) == "21 d"
    assert bb.fmt_short(timedelta(hours=26)) == "26 h" and bb.fmt_short(timedelta(hours=2, minutes=40)) == "2 h"


def _first_view(page):
    """The panel's first view (without the Staging fixes)."""
    return page.split('<div class="tb-view" data-fix="all"')[0]


def _groups(tmp_path):
    history = [{"version": "7.40", "date": "01.03.2026"}, {"version": "7.40b", "date": "01.04.2026"},
               {"version": "7.41", "date": "01.06.2026"}]
    builds = _load(tmp_path, _raw(("public", 9, "2026-03-01T20:00:00Z"), ("public", 10, "2026-04-01T20:00:00Z"),
                                  ("public", 11, "2026-06-01T20:00:00Z"),
                                  ("experimental", 1, "2026-03-28T10:00:00Z"),
                                  ("staging", 2, "2026-03-31T10:00:00Z"),           # for 7.40b
                                  ("experimental", 3, "2026-05-01T10:00:00Z"),
                                  ("staging", 4, "2026-05-30T20:00:00Z"), ("staging", 5, "2026-06-01T18:00:00Z")))
    rels = bb.releases(history)
    m = bb.patch_moments(rels, builds)
    return builds, history, bb.group_by_patch(builds, rels, m), bb.group_by_patch(builds, bb.major_releases(rels), m)


def test_each_patch_leads_with_the_time_after_the_last_staging_build(tmp_path):
    _, _, every, whole = _groups(tmp_path)
    card = bb.patch_card(every, NOW, whole)
    lists = re.findall(r'<div class="tb-plist" data-lag="(\w+)"( hidden)?>', card)
    assert lists == [("major", ""), ("all", " hidden")]                                # whole patches by default
    major = card.split('<div class="tb-plist" data-lag="all"')[0]
    row = re.search(r'<div class="tb-pr tb-tip-target" data-patch="7.41".*?</div>', major)[0]
    cells = re.findall(r'<span class="tb-pr-cell( is-key)?" data-label="[^"]+"><b>([^<]+)</b>', row)   # labelled for phones
    assert cells[0] == (" is-key", "2 d") and cells[1] == (" is-key", "2 h")           # second-to-last, last Staging
    assert [c[1] for c in cells[2:5]] == ["2 d", "2 d", "31 d"]                        # first Staging, its run, Experimental
    assert re.findall(r'class="tb-count tb-(\w+)" data-n="(\d+)"', row) == [("staging", "2"), ("experimental", "1")]
    assert '<span class="tb-chip is-major">7.41</span>' in row
    assert re.search(r'data-lag2="172800" data-lag="7200" data-stg1="\d+" data-stg="\d+" data-lead="\d+"', row)


def test_the_patch_tooltip_is_a_table(tmp_path):
    _, _, every, whole = _groups(tmp_path)
    g = whole[-1]
    text = html.unescape(bb._row_tip(g, bb.group_stats(g, NOW)))
    assert text == '<b>7.41</b><span class="tb-tip-sub">1 Jun 2026 20:00 UTC</span><table class="tb-tip-table"><tr class="tb-tip-key"><td>After the second-to-last Staging build</td><td>2 d</td></tr><tr class="tb-tip-key"><td>After the last Staging build</td><td>2 h</td></tr><tr class="tb-tip-staging"><td>First Staging build after the previous patch, before</td><td>2 d</td></tr><tr class="tb-tip-staging"><td>Staging builds</td><td>2</td></tr><tr class="tb-tip-experimental"><td>Experimental builds</td><td>1</td></tr></table>'


def test_the_answer_tiles_are_medians_over_whole_patches(tmp_path):
    builds, history, _, _ = _groups(tmp_path)
    page = _first_view(bb.render_panel(builds, history, NOW))
    tiles = re.findall(r'<div class="cal-ig-panel tb-ig-num([^"]*)" data-median="(\w+)"><b>([^<]+)</b>', page)
    assert [(k, v) for _, k, v in tiles] == [("lag2", "2 d"), ("lag", "2 h"), ("stg1", "2 d"), ("stg", "2 d"),
                                               ("lead", "31 d")]
    assert "is-key" in tiles[0][0]


def test_the_year_filter_recounts_the_medians_as_the_generator(tmp_path):
    # The script recounts the strip from the whole-patch rows: the same keys, the same "whole run-up only" choice
    # (medians() skips patches cut by the log's start for stg1, stg, lead), the same rounding as fmt_short
    builds, history, _, _ = _groups(tmp_path)
    page = _first_view(bb.render_panel(builds, history, NOW))
    js = (ROOT / "src" / "js" / "calendar-builds.js").read_text(encoding="utf-8")
    whole = dict(re.findall(r"(\w+): (true|false)", re.search(r"const WHOLE_ONLY = \{([^}]+)\}", js)[1]))
    assert whole == {"lag2": "false", "lag": "false", "stg1": "true", "stg": "true", "lead": "true"}
    assert list(whole) == re.findall(r'data-median="(\w+)"', page)
    assert "h >= 48 ? `${Math.floor(h / 24)} d` : `${h} h`" in js
    assert re.search(r'medians, <span class="tb-ig-since">\d{4} to now</span>', page)  # the script rewrites it
    assert page.count('<div class="tb-empty tb-plist-none" hidden>') == 2
    css = (ROOT / "src" / "css" / "calendar-builds.css").read_text(encoding="utf-8")
    assert ".tb-pr[hidden] { display: none; }" in css                                  # the grid would show it


def test_the_first_staging_build_counts_from_the_previous_patch_of_any_kind(tmp_path):
    # Owner 2026-11-10: patch X out, every Staging build after it until patch Y belongs to Y. The first one may sit
    # weeks before a pause; the run-up is the builds after the last pause over a week, both after X only.
    history = [{"version": "7.40", "date": "01.03.2026"}, {"version": "7.40b", "date": "01.04.2026"},
               {"version": "7.41", "date": "01.06.2026"}]
    builds = _load(tmp_path, _raw(("public", 9, "2026-03-01T20:00:00Z"), ("public", 10, "2026-04-01T20:00:00Z"),
                                  ("public", 11, "2026-06-01T20:00:00Z"),
                                  ("staging", 1, "2026-03-20T20:00:00Z"),           # before 7.40b: 7.40b's
                                  ("staging", 2, "2026-04-11T20:00:00Z"),           # first after 7.40b
                                  ("staging", 3, "2026-05-30T20:00:00Z"), ("staging", 4, "2026-06-01T18:00:00Z")))
    rels = bb.releases(history)
    m = bb.patch_moments(rels, builds)
    g = bb.group_by_patch(builds, bb.major_releases(rels), m)[-1]
    s = bb.group_stats(g, NOW)
    assert g["version"] == "7.41" and g["after_patch"] == m["7.40b"][0]
    assert bb.fmt_short(s["stg_first"]) == "51 d" and bb.fmt_short(s["stg_start"]) == "2 d"
    assert [b["version"] for b in s["stg_run"]] == [3, 4]


def test_the_builds_calendar_is_the_patches_grid_with_builds_per_day(tmp_path):
    builds, history, _, _ = _groups(tmp_path)
    cal = bb.builds_calendar(builds, bb.releases(history), [2025, 2026], patch_pages={"7.41"})
    assert cal.count('class="cal-full-month-name"') == 24 and cal.count('<div class="cal-full-grid">') == 2
    day = re.search(r'<div class="cal-full-day tb-day tb-e1 tb-tip-target" data-month="5" data-day="1" '
                    r'data-c="(\d+),(\d+)">1<span class="tb-dots"><i class="tb-dot-e tb-d1"></i></span></div>', cal)
    assert day and (day[1], day[2]) == ("1", "0")                                     # no date, only the builds
    patch = re.search(r'<a class="cal-full-day tb-day tb-s1 has-patch major tb-tip-target" '
                      r'href="patches/7.41.html\?from=calendar" data-month="6" data-day="1"', cal)
    assert patch                                                                       # Staging that day, and 7.41


def test_the_builds_calendar_is_the_patches_block_itself(tmp_path):
    # 2026-11-10, the owner: "календари отличаются" — the same block, picker, one year at a time, footer
    builds, history, _, _ = _groups(tmp_path)
    cal = bb.builds_calendar(builds, bb.releases(history), [2025, 2026])
    assert cal.startswith('<div class="cal-year-block is-current tb-calblock" data-collapsed="false">'
                          '<div class="cal-year-label"><div class="cal-year-picker">')
    assert re.findall(r'class="cal-year-opt[^"]*" role="option" data-year="(\d+)"', cal) == ["2026", "2025"]
    assert re.findall(r'<div class="cal-year-pane" data-year="(\d+)"( hidden)?>', cal) == [("2026", ""), ("2025", " hidden")]
    assert cal.count('<div class="cal-mode-full">') == 2 and cal.count('class="cal-year-summary"') == 2
    page = (ROOT / "patch" / "calendar.py").read_text(encoding="utf-8")
    assert "document.querySelectorAll('.cal-year-picker').forEach" in page               # every picker, its own panes
    assert "block.querySelectorAll('.cal-year-pane')" in page


def test_whole_patches_take_the_builds_of_their_letter_patches(tmp_path):
    _, _, every, whole = _groups(tmp_path)
    assert [g["version"] for g in every] == ["7.40b", "7.41"] and [g["version"] for g in whole] == ["7.41"]
    assert len(whole[0]["experimental"]) == 2 and len(whole[0]["staging"]) == 3


def test_every_piece_carries_its_year_for_the_filter(tmp_path):
    builds, history, _, _ = _groups(tmp_path)
    page = _first_view(bb.render_panel(builds, history, NOW))
    assert re.findall(r'<select class="cal-mode-select tb-year-(\w+)">', page) == ["from", "to"]
    assert all(re.search(r'data-year="20\d\d"', r) for r in re.findall(r'<div class="tb-pr tb-tip-target[^>]*>', page))
    assert re.search(r'class="tb-bar tb-experimental"[^>]* data-t="\d+" data-v="1"', page)
    assert re.search(r'class="tb-hit tb-tip-target" data-i="10" data-name="10:00 to 10:59 UTC" '
                     r'data-c-experimental="2026:2"', page)


def test_an_empty_file_still_renders_the_tab():
    html_ = bb.render_panel([], HISTORY, NOW)
    assert html_.count("No builds yet") == 4 and 'data-median="lag"><b>–</b>' in html_   # two views, two lists each


def test_a_staging_build_followed_by_a_live_fix_within_six_hours_is_a_fix(tmp_path):
    # 2026-11-10, the owner: Staging also carries the live game's fixes; they are not a run-up to a patch
    builds = _load(tmp_path, _raw(("public", 10, "2026-06-01T20:00:00Z"),               # 7.41 comes out
                                  ("staging", 1, "2026-05-10T10:00:00Z"), ("public", 5, "2026-05-10T15:00:00Z"),
                                  ("staging", 2, "2026-05-20T10:00:00Z"), ("public", 6, "2026-05-21T10:00:00Z"),
                                  ("staging", 3, "2026-06-01T18:00:00Z")))
    m = bb.patch_moments(bb.releases(HISTORY), builds)
    fixes = bb.staging_fixes(builds, m)
    assert [b["version"] for b in builds if id(b) in fixes] == [1]    # 5 h to a live fix; 24 h is not; the patch is not
    assert bb.FIX_WINDOW_H == 6


def test_the_switch_shows_the_tab_without_the_staging_fixes_first(tmp_path):
    builds = _load(tmp_path, _raw(("public", 10, "2026-06-01T20:00:00Z"),
                                  ("staging", 1, "2026-05-10T10:00:00Z"), ("public", 5, "2026-05-10T15:00:00Z"),
                                  ("staging", 3, "2026-06-01T18:00:00Z")))
    page = bb.render_panel(builds, HISTORY, NOW)
    assert re.findall(r'<div class="tb-view" data-fix="(\w+)"( hidden)?>', page) == [("hide", ""), ("all", " hidden")]
    assert re.findall(r'class="ua-switch-input tb-fix-input"( checked)?>', page) == [" checked", ""]
    hide, every = page.split('<div class="tb-view" data-fix="all"')
    assert "Staging builds:</span> <span class=\"cal-year-summary-val tb-sum-staging\">1<" in hide
    assert "Staging builds:</span> <span class=\"cal-year-summary-val tb-sum-staging\">2<" in every
    js = (ROOT / "src" / "js" / "calendar-builds.js").read_text(encoding="utf-8")
    assert "panel.querySelectorAll('.tb-view')" in js and ".tb-fix-input" in js


def test_the_script_writes_the_lazy_tooltips_and_bar_numbers():
    # 2026-11-10: with 13 years of history the page kept tables per day and week; now numbers only, written on hover
    js = (ROOT / "src" / "js" / "calendar-builds.js").read_text(encoding="utf-8")
    assert "e.target.closest('[data-c]')" in js and "lazy.dataset.tooltip =" in js
    assert "createElementNS(NS, 'text')" in js and "svg.dataset.t0" in js


def test_the_tab_starts_with_the_first_staging_build(tmp_path):
    # 2026-11-10, the owner: years of Experimental alone (SteamDB back to 2013) were a mess; the tab covers Staging's time
    history = [{"version": "7.32", "date": "01.01.2023"}, {"version": "7.33", "date": "20.04.2023"}]
    builds = _load(tmp_path, _raw(("experimental", 1, "2022-12-01T10:00:00Z"), ("public", 2, "2022-12-30T10:00:00Z"),
                                  ("staging", 3, "2023-03-01T07:00:00Z"), ("experimental", 4, "2023-03-05T10:00:00Z"),
                                  ("public", 5, "2023-04-20T23:00:00Z")))
    kept, rels = bb.since_staging(builds, history)
    assert [b["version"] for b in kept] == [3, 4, 5] and [r["version"] for r in rels] == ["7.33"]
    page = bb.render_panel(builds, history, NOW, from_staging=True)
    panes = re.findall(r'<div class="cal-year-pane" data-year="(\d+)"', page)
    assert panes and min(panes) == "2023" and 'data-year="2022"' not in page
    assert "from_staging=True" in (ROOT / "patch" / "calendar.py").read_text(encoding="utf-8")   # the site's tab
    assert bb.since_staging(builds[:2], history) == (builds[:2], history)                # no Staging yet: everything

