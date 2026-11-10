"""The calendar's "Test servers" tab: Experimental and Staging builds against the gameplay patches (owner 2026-11-10).

Data: data/branch_builds.json (scripts/fetch/fetch_branch_builds.py): every change of the client version of Experimental
(247040), Staging (2305270) and the live game (570), with the time it was seen. Rules:
  * a patch came out at the first live-game build of its day (UTC), up to PATCH_DAY_SLACK_H hours into the next day; a
    patch day with no live build in the log falls back to noon UTC;
  * a test build belongs to the first patch that came out after it; builds after the newest patch wait for the next one;
  * a patch whose previous patch is older than the log only has a lower bound for its Experimental lead ("≥");
  * only timed builds (seen within a few hours of the change) go into the hour and weekday charts.
"""
import html as _html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

DATA = Path(__file__).resolve().parent.parent / "data" / "branch_builds.json"
BRANCHES = ("experimental", "staging")
LABELS = {"experimental": "Experimental", "staging": "Staging"}
TIMED_WINDOW_H = 3
PATCH_DAY_SLACK_H = 12
TIME_FMT = "%Y-%m-%dT%H:%M:%SZ"
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _t(s):
    return datetime.strptime(s, TIME_FMT).replace(tzinfo=timezone.utc)


def _midnight(d):
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def versions(old, new):
    """How many versions one update stands for (owner 2026-11-10: count the version numbers, 3332 => 3338 is 6): the
    step of the number; a rollback to a lower number or an unknown one is 1."""
    return new - old if isinstance(old, int) and isinstance(new, int) and new > old else 1


def nv(lst):
    """The versions of a list of updates."""
    return sum(b.get("n", 1) for b in lst)


def load_builds(path=DATA):
    """Every version change, oldest first: dicts with branch, from, version, time (datetime), timed (bool)."""
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for b in raw["builds"]:
        t = _t(b["time"])
        timed = b.get("timed")
        if timed is None:
            timed = bool(b.get("after")) and t - _t(b["after"]) <= timedelta(hours=TIMED_WINDOW_H)
        # A SteamDB event (before Oct 2021) has a changenumber, no version
        out.append({"branch": b["branch"], "from": b.get("from"), "version": b.get("version"), "time": t, "timed": timed,
                    "source": b.get("source"), "n": versions(b.get("from"), b.get("version"))})
    return sorted(out, key=lambda b: b["time"])


def releases(history):
    """(version, date) of the gameplay patches, oldest first, from RELEASE_HISTORY."""
    return sorted(((r["version"], datetime.strptime(r["date"], "%d.%m.%Y").date()) for r in history), key=lambda r: r[1])


def patch_moments(rels, builds):
    """{version: (datetime, exact)}: the first live-game build of the patch's day (or early next day), else noon."""
    public = [b["time"] for b in builds if b["branch"] == "public"]
    out = {}
    for v, d in rels:
        lo, hi = _midnight(d), _midnight(d) + timedelta(days=1, hours=PATCH_DAY_SLACK_H)
        hit = next((t for t in public if lo <= t < hi), None)
        out[v] = (hit, True) if hit else (lo + timedelta(hours=12), False)
    return out


def group_by_patch(builds, rels, moments=None):
    """One group per patch with test builds, oldest first, plus the not-yet-released next patch (version None)."""
    moments = moments or patch_moments(rels, builds)
    order = sorted(rels, key=lambda r: moments[r[0]][0])
    start = builds[0]["time"] if builds else None
    groups = {}
    for b in builds:
        if b["branch"] not in BRANCHES:
            continue
        rel = next((r for r in order if moments[r[0]][0] >= b["time"]), None)
        key = rel[0] if rel else None
        if key not in groups:
            idx = order.index(rel) if rel else len(order)
            prev = moments[order[idx - 1][0]][0] if idx > 0 else None
            groups[key] = {"version": key, "date": rel[1] if rel else None,
                           "moment": moments[key][0] if rel else None, "exact": moments[key][1] if rel else False,
                           "partial": prev is None or (start is not None and prev < start),
                           "experimental": [], "staging": []}
        groups[key][b["branch"]].append(b)
    ordered = [groups[v] for v, _ in order if v in groups]
    if None in groups:
        ordered.append(groups[None])
    # The patch just before each one, whole or letter, from every patch in `moments` (even when `rels` holds only the
    # whole ones): its first Staging build is counted from there
    every = sorted(t for t, _ in moments.values())
    for g in ordered:
        before = [t for t in every if g["moment"] is None or t < g["moment"]]
        g["after_patch"] = before[-1] if before else None
    return ordered


def fmt_span(td):
    """A duration as days and hours: '41 d 5 h', '7 h'."""
    hours = int(td.total_seconds() // 3600)
    d, h = divmod(max(hours, 0), 24)
    return f"{d} d {h} h" if d else f"{h} h"


def group_stats(g, now):
    """Per server, the run-up to the patch (run_up: its last builds without a long pause) and its count; how long the
    patch came after the last Staging build; when each run-up began (to now for the next patch, not out yet)."""
    end = g["moment"] or now
    s = {}
    for br in BRANCHES:
        lst = g[br]
        s[br] = {"count": len(lst), "first": lst[0] if lst else None, "last": lst[-1] if lst else None}
    last_st = s["staging"]["last"]
    s["staging_lag"] = end - last_st["time"] if last_st else None
    s["staging_lag_text"] = None if last_st is None else fmt_span(s["staging_lag"])
    # The second-to-last Staging build too (owner 2026-11-10): the last one often lands with the patch itself
    s["staging_lag2"] = end - g["staging"][-2]["time"] if len(g["staging"]) >= 2 else None
    # The first Staging build after the previous patch came out (owner 2026-11-10: every Staging build after patch X
    # until patch Y belongs to Y): the group's first, whatever pauses follow it
    after = g.get("after_patch")                          # the moment of the patch just before, whole or letter
    since = [b for b in g["staging"] if after is None or b["time"] > after]
    s["stg_first"] = end - since[0]["time"] if since else None
    # The Staging run-up stays after that patch too, so it is never longer than the first build after it
    s["exp_run"], s["stg_run"] = run_up(g["experimental"]), run_up(since)
    s["exp_lead"] = end - s["exp_run"][0]["time"] if s["exp_run"] else None
    s["stg_start"] = end - s["stg_run"][0]["time"] if s["stg_run"] else None
    # The run-up reaching back to the first build of a group older than the log: it may have begun earlier
    cut = g["partial"] and s["exp_run"] and s["exp_run"][0] is s["experimental"]["first"]
    s["exp_lead_text"] = None if s["exp_lead"] is None else ("≥ " if cut else "") + fmt_span(s["exp_lead"])
    s["exp_cut"] = bool(cut)
    return s


RUN_GAP_D = 7


def run_up(builds):
    """A server's run-up to a patch: its last builds with no pause longer than RUN_GAP_D days between them. Experimental
    runs almost all the time and a whole patch's group also holds the Staging of the letter patches before it, so the
    first build since the previous patch says little (owner 2026-11-10)."""
    staging = builds
    run = list(staging[-1:])
    for b in reversed(staging[:-1]):
        if run[0]["time"] - b["time"] > timedelta(days=RUN_GAP_D):
            break
        run.insert(0, b)
    return run


def fmt_short(td):
    """A duration read at a glance: whole days from 2 days on ('21 d'), hours below ('26 h', '2 h')."""
    hours = max(int(td.total_seconds() // 3600), 0)
    return f"{hours // 24} d" if hours >= 48 else f"{hours} h"


def hour_counts(builds, branch):
    c = [0] * 24
    for b in builds:
        if b["branch"] == branch and b["timed"]:
            c[b["time"].hour] += b.get("n", 1)
    return c


def weekday_counts(builds, branch):
    c = [0] * 7
    for b in builds:
        if b["branch"] == branch and b["timed"]:
            c[b["time"].weekday()] += b.get("n", 1)
    return c


def fmt_time(t):
    return f"{t.day} {MONTHS[t.month - 1]} {t.year} {t:%H:%M}"


def fmt_day(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


# ---------------------------------------------------------------- charts

NICE_STEPS = (1, 2, 3, 4, 5, 10, 15, 20, 25, 50, 100, 200, 250, 500, 1000, 2500)


def _nice_top(maxv):
    """A scale of 4 round steps over maxv. Past the list (13 years of builds by weekday run over 800) the step is
    maxv / 4 rounded up, so a chart never fails on a big count (2026-11-10)."""
    step = next((st for st in NICE_STEPS if st * 4 >= maxv), -(-int(maxv) // 4))
    return step, step * 4


def _by_year_attr(by_year, i):
    """"2024:3,2025:5": a column's count in each year, for the year filter."""
    return ",".join(f"{y}:{c[i]}" for y, c in sorted(by_year.items()) if c[i])


def bar_chart_svg(series, labels, uid, show="both", names=None, by_year=None):
    """One column per hour or weekday. show "both": stacked, Experimental at the bottom, Staging on top; one server: only
    its bars. series: {branch: counts}; names: the column's full name for its tooltip (default: its label); by_year:
    {branch: {year: counts}} for the year filter. Every column is a hover target with its counts."""
    n = len(labels)
    names = names or labels
    shown = BRANCHES if show == "both" else (show,)
    totals = [sum(series[br][i] for br in shown) for i in range(n)]
    step, top = _nice_top(max([1] + totals))
    view_w, pad_l, pad_r, pad_t, chart_h, label_h = 520, 26, 6, 10, 90, 16
    col = (view_w - pad_l - pad_r) / n
    bar = col * 0.62
    s = [f'<svg class="tb-bars" data-chart="{uid}" data-series="{show}" data-pt="{pad_t}" data-ch="{chart_h}" '
         f'viewBox="0 0 {view_w} {chart_h + label_h}" role="img"{"" if show == "both" else " hidden"}>']
    for k in range(5):
        gy = pad_t + (1 - k / 4) * (chart_h - pad_t)
        if 0 < k:
            s.append(f'<line class="cal-ig-grid" x1="{pad_l}" y1="{gy:.1f}" x2="{view_w - pad_r}" y2="{gy:.1f}"/>')
        s.append(f'<text class="cal-ig-ytick" data-k="{k}" x="{pad_l - 5}" y="{gy + 3:.1f}" text-anchor="end">{step * k}</text>')
    for i, lab in enumerate(labels):
        cx = pad_l + col * (i + 0.5)
        y = chart_h
        for br in shown:
            v = series[br][i]
            h = v / top * (chart_h - pad_t)
            y -= h
            s.append(f'<rect class="tb-bar tb-{br}" data-i="{i}" data-br="{br}" x="{cx - bar / 2:.1f}" y="{y:.1f}" '
                     f'width="{bar:.1f}" height="{h:.1f}"/>')
        tip = _counts_tip(_html.escape(names[i]), {br: series[br][i] for br in shown}, shown)
        years = "".join(f' data-c-{br}="{_by_year_attr(by_year[br], i)}"' for br in shown) if by_year else ""
        s.append(f'<rect class="tb-hit tb-tip-target" data-i="{i}" data-name="{_html.escape(names[i])}"{years} '
                 f'data-tooltip="{tip}" x="{pad_l + col * i:.1f}" y="{pad_t}" width="{col:.2f}" height="{chart_h - pad_t}"/>')
        if n <= 7 or i % 3 == 0:
            s.append(f'<text class="cal-ig-spark-lbl" x="{cx:.1f}" y="{chart_h + 12}" text-anchor="middle">{lab}</text>')
    s.append(f'<line class="cal-ig-axis is-base" x1="{pad_l}" y1="{chart_h}" x2="{view_w - pad_r}" y2="{chart_h}"/>')
    s.append('</svg>')
    return "".join(s)


def series_buttons():
    """Both / Experimental / Staging: calendar-builds.js shows the card's chart of that name."""
    return '<div class="tb-series">' + "".join(
        f'<button type="button" class="cat-filter-btn tb-series-btn{" active" if k == "both" else ""}" '
        f'data-series="{k}" aria-pressed="{"true" if k == "both" else "false"}">{SERIES_LABELS[k]}</button>'
        for k in SERIES) + '</div>'


WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def when_card(title, series, labels, uid, names, by_year=None):
    charts = "".join(bar_chart_svg(series, labels, uid, k, names, by_year) for k in SERIES)
    key = ''.join(f'<span class="tb-key"><span class="tb-dot tb-{br}"></span>{LABELS[br]}</span>' for br in BRANCHES)
    return (f'<div class="tb-card"><div class="tb-card-head"><div class="cal-ig-h">{title}</div>{series_buttons()}</div>'
            f'{charts}<div class="tb-keys">{key}</div></div>')


def _monday(d):
    return d - timedelta(days=d.weekday())


def _patch_of_build(groups):
    """{id(build): patch version or "next"} from the groups."""
    return {id(b): (g["version"] or "next") for g in groups for br in BRANCHES for b in g[br]}


def weekly_counts(builds, now, groups=None):
    """[(monday, experimental count, staging count, patch)] for every week from the first test build to now; patch =
    the patch the week's last build led to (None for an empty week)."""
    tests = [b for b in builds if b["branch"] in BRANCHES]
    if not tests:
        return []
    of = _patch_of_build(groups) if groups else {}
    first, last = _monday(tests[0]["time"].date()), _monday(now.date())
    weeks = {}
    for b in tests:
        w = weeks.setdefault(_monday(b["time"].date()), {"experimental": 0, "staging": 0, "patch": None})
        w[b["branch"]] += b.get("n", 1)
        w["patch"] = of.get(id(b))
    out, d = [], first
    while d <= last:
        w = weeks.get(d, {})
        out.append((d, w.get("experimental", 0), w.get("staging", 0), w.get("patch")))
        d += timedelta(days=7)
    return out


def _tip(*lines):
    """A data-tooltip value for the site's shared tooltip (tooltips.js renders it as HTML)."""
    return _html.escape("<br>".join(lines), quote=True)


def _count_table(counts, shown=BRANCHES):
    """The builds of a day, week or hour as a little table, a row per server in its own colour (owner 2026-11-10).
    calendar-builds.js writes the same markup after the year filter (countTable)."""
    rows = "".join(f'<tr class="tb-tip-{br}"><td>{LABELS[br]}</td><td>{counts.get(br, 0)}</td></tr>' for br in shown)
    return f'<table class="tb-tip-table">{rows}</table>'


def _counts_tip(title, counts, shown=BRANCHES):
    """A title line (or none) and the counts table."""
    return _html.escape((f"<b>{title}</b>" if title else "") + _count_table(counts, shown), quote=True)


def _patch_tip(g, s):
    """A patch line's tooltip: its moment and the answer, in three short lines."""
    return _row_tip(g, s)


SERIES = ("both", "experimental", "staging")
START_LABEL_ROOM = 64          # px of the weekly axis kept for the start label ("Oct 2021")
BAR_VALUE_MIN_COL = 14         # a week's column this wide (px) or wider shows its bars' numbers
SERIES_LABELS = {"both": "Both", "experimental": "Experimental", "staging": "Staging"}


def weekly_svg(builds, rels, now, moments=None, groups=None, series="both", major_groups=None):
    """The whole history on one wide chart, a column per week. "both": Experimental up from the middle line, Staging
    down; one server: its bars up from the bottom on the full height. A line where each patch came out (whole patches
    labelled). Every week and every patch line carries a tooltip; data-patch ties a patch to the weeks that led to it."""
    moments = moments or patch_moments(rels, builds)
    groups = groups if groups is not None else group_by_patch(builds, rels, moments)
    weeks = weekly_counts(builds, now, groups)
    majors = [w[3] for w in weekly_counts(builds, now, major_groups)] if major_groups else [None] * len(weeks)
    view_w, pad_l, pad_r, top, axis_h = 1300, 92, 10, 24, 26
    plot_h = 200
    h = top + plot_h + axis_h
    mid = top + plot_h / 2 if series == "both" else top + plot_h
    s = [f'<svg class="tb-weekly" data-series="{series}" data-pl="{pad_l}" data-pw="{view_w - pad_l - pad_r}" '
         f'data-mid="{mid}" data-half="{plot_h / 2 if series == "both" else plot_h}" viewBox="0 0 {view_w} {h}" role="img"'
         f'{"" if series == "both" else " hidden"}>']
    if not weeks:
        s.append('</svg>')
        return "".join(s)
    shown = BRANCHES if series == "both" else (series,)
    idx = {"experimental": 1, "staging": 2}
    step, scale = _nice_top(max(1, max(w[idx[br]] for w in weeks for br in shown)))
    half = plot_h / 2 if series == "both" else plot_h
    t0 = _midnight(weeks[0][0])
    t1 = _midnight(weeks[-1][0] + timedelta(days=7))
    s[0] = s[0].replace(' data-pl=', f' data-t0="{_ts(t0)}" data-t1="{_ts(t1)}" data-pl=', 1)   # the whole range, for the script
    plot_w = view_w - pad_l - pad_r

    def x_of(t):
        return pad_l + (t - t0).total_seconds() / (t1 - t0).total_seconds() * plot_w

    signs = (-1, 1) if series == "both" else (-1,)
    for k in (1, 2, 3, 4):
        for sign in signs:
            gy = mid + sign * k / 4 * half
            s.append(f'<line class="cal-ig-grid" x1="{pad_l}" y1="{gy:.1f}" x2="{view_w - pad_r}" y2="{gy:.1f}"/>')
            if k % 2 == 0:
                s.append(f'<text class="tb-ytick" data-k="{k}" x="{pad_l - 6}" y="{gy + 4:.1f}" text-anchor="end">{step * k}</text>')
    # The halves are named next to the middle line, where no tick number stands (ticks are at half and full height)
    if series == "both":
        s.append(f'<text class="tb-half-name tb-experimental" x="{pad_l - 6}" y="{mid - 8}" text-anchor="end">Experimental</text>')
        s.append(f'<text class="tb-half-name tb-staging" x="{pad_l - 6}" y="{mid + 18}" text-anchor="end">Staging</text>')
    else:
        s.append(f'<text class="tb-half-name tb-{series}" x="{pad_l - 6}" y="{mid - 8}" text-anchor="end">{LABELS[series]}</text>')
    # The left edge names where the log starts (Oct 2021), so the axis never begins without a year; calendar-builds.js
    # gives the first label of a filtered range its year the same way
    s.append(f'<text class="cal-ig-spark-lbl is-year is-start" data-t="{_ts(t0)}" x="{pad_l:.1f}" y="{h - 6}" '
             f'text-anchor="start">{MONTHS[weeks[0][0].month - 1]} {weeks[0][0].year}</text>')
    d = weeks[0][0].replace(day=1)
    carry = None                   # a year whose own label had to give way to the start label goes on the next one
    while d <= weeks[-1][0]:
        if d.month in (1, 4, 7, 10) and _midnight(d) >= t0:
            x = x_of(_midnight(d))
            dt = f' data-t="{_ts(_midnight(d))}" data-lab="{"" if d.month == 1 else MONTHS[d.month - 1]}"'
            s.append(f'<line class="tb-month-tick"{dt} x1="{x:.1f}" y1="{h - axis_h}" x2="{x:.1f}" y2="{h - axis_h + 4}"/>')
            near = x - pad_l < START_LABEL_ROOM                                         # the start label stands there
            lab = str(d.year) if d.month == 1 else MONTHS[d.month - 1] + (f" {carry}" if carry and not near else "")
            if not near:
                carry = None
            elif d.month == 1:
                carry = d.year
            s.append(f'<text class="cal-ig-spark-lbl{" is-year" if d.month == 1 else ""}"{dt}'
                     f'{" style=" + chr(34) + "display:none" + chr(34) if near else ""} x="{x:.1f}" y="{h - 6}" '
                     f'text-anchor="middle">{lab}</text>')
        d = (d + timedelta(days=32)).replace(day=1)
    col = plot_w / len(weeks)
    bar = max(1.0, col - 1.5)
    for i, (monday, e, st, patch) in enumerate(weeks):
        x = pad_l + col * i + (col - bar) / 2
        dp = (f' data-patch="{_html.escape(patch)}"' if patch else "") + (
            f' data-major="{_html.escape(majors[i])}"' if majors[i] else "") + f' data-t="{_ts(_midnight(monday))}"'
        for br, v in (("experimental", e), ("staging", st)):
            if not v or br not in shown:
                continue
            bh = v / scale * half
            y = mid - bh if (series != "both" or br == "experimental") else mid
            s.append(f'<rect class="tb-bar tb-{br}"{dp} data-v="{v}" x="{x:.1f}" y="{y:.1f}" width="{bar:.1f}" height="{bh:.1f}"/>')
        # A week with builds is a hover target; its tooltip is written on hover from data-c (calendar-builds.js), and
        # the bars' numbers too, once a week is wide enough: 13 years of weeks would weigh megabytes otherwise
        if not any({"experimental": e, "staging": st}[br] for br in shown):
            continue
        one = "" if series == "both" else f' data-show="{series}"'
        s.append(f'<rect class="tb-hit tb-tip-target"{dp} data-c="{e},{st}"{one} data-title="Week of {fmt_day(monday)}" '
                 f'x="{pad_l + col * i:.1f}" y="{top}" width="{col:.2f}" height="{plot_h}"/>')
    s.append(f'<line class="cal-ig-axis is-base" x1="{pad_l}" y1="{mid}" x2="{view_w - pad_r}" y2="{mid}"/>')
    stats = {g["version"]: group_stats(g, now) for g in groups if g["version"]}
    for v, _ in rels:
        t = moments[v][0]
        if not (t0 <= t <= t1):
            continue
        x = x_of(t)
        major = v[-1].isdigit()
        dt = f' data-t="{_ts(t)}"'
        s.append(f'<line class="tb-patch-line{"" if major else " is-letter"}"{dt} x1="{x:.1f}" y1="{top - (6 if major else 0)}" '
                 f'x2="{x:.1f}" y2="{top + plot_h}"/>')
        if major:
            s.append(f'<text class="tb-patch-lbl"{dt} x="{x:.1f}" y="{top - 9}" text-anchor="middle">{_html.escape(v)}</text>')
        g = next((g for g in groups if g["version"] == v), None)
        tip = _patch_tip(g, stats[v]) if g else _tip(f"<b>{_html.escape(v)}</b> came out {fmt_day(t.date())}",
                                                     "no test builds before it")
        s.append(f'<rect class="tb-hit tb-patch-hit tb-tip-target" data-patch="{_html.escape(v)}"{dt} data-tooltip="{tip}" '
                 f'x="{x - 4:.1f}" y="{top - 22 if major else top}" width="8" height="{plot_h + (22 if major else 0)}"/>')
    tx = x_of(now)
    dt = f' data-t="{_ts(now)}"'
    s.append(f'<line class="tb-today-line"{dt} x1="{tx:.1f}" y1="{top}" x2="{tx:.1f}" y2="{top + plot_h}"/>')
    s.append(f'<text class="tb-today-lbl"{dt} x="{tx:.1f}" y="{top - 9}" text-anchor="end">now</text>')
    s.append('</svg>')
    return "".join(s)


def weekly_card(builds, rels, now, moments, groups, major_groups=None):
    """The wide chart with its Both / Experimental / Staging switch (calendar-builds.js shows one of the three)."""
    charts = "".join(weekly_svg(builds, rels, now, moments, groups, k, major_groups) for k in SERIES)
    return (f'<div class="tb-card"><div class="tb-card-head"><div class="cal-ig-h">Versions per week</div>'
            f'{series_buttons()}</div><div class="tb-weekly-scroll">{charts}</div></div>')


LAG_STAGING_CAP_H = 48
LAG2_STAGING_CAP_H = 168          # the second-to-last Staging build's bar: up to 7 days


def major_releases(rels):
    """The whole patches (7.41, not 7.41a)."""
    return [r for r in rels if r[0][-1].isdigit()]


# ---------------------------------------------------------------- each patch: the answer, row by row

def _chip(version, cls=""):
    """A patch as the calendar draws it: whole patches orange, letter patches grey."""
    kind = "major" if version[-1].isdigit() else "sub"
    return f'<span class="tb-chip is-{kind}{cls}">{_html.escape(version)}</span>'


# The table's columns: a phone hides the header row and writes each cell's own label above it (data-label)
PR_COLUMNS = ("After the second-to-last Staging build", "After the last Staging build",
              "First Staging build after the previous patch", "Staging run-up began before", "Experimental began before",
              "Versions")


def _bar_cell(span, full, br, key=False, label=""):
    """A duration in big type with a thin bar under it (its share of the column's scale)."""
    lab = f' data-label="{label}"' if label else ""
    if span is None:
        return f'<span class="tb-pr-cell{" is-key" if key else ""}"{lab}><span class="ua-dash">–</span></span>'
    share = min(span.total_seconds() / full, 1) if full else 0
    over = " is-over" if span.total_seconds() > full else ""
    return (f'<span class="tb-pr-cell{" is-key" if key else ""}"{lab}><b>{fmt_short(span)}</b>'
            f'<i class="tb-pr-bar tb-{br}{over}" style="--p:{share:.3f}"></i></span>')


def _row_tip(g, s):
    """A patch's tooltip as a table (owner 2026-11-10): the patch and its moment on top, then the answer in gold and
    the run-up's builds in each server's colour."""
    when = fmt_time(g["moment"]) + " UTC" if g["exact"] else fmt_day(g["date"])
    lag = fmt_short(s["staging_lag"]) if s["staging_lag"] is not None else "–"
    lag2 = fmt_short(s["staging_lag2"]) if s["staging_lag2"] is not None else "–"
    rows = (f'<tr class="tb-tip-key"><td>After the second-to-last Staging build</td><td>{lag2}</td></tr>'
            f'<tr class="tb-tip-key"><td>After the last Staging build</td><td>{lag}</td></tr>'
            f'<tr class="tb-tip-staging"><td>First Staging build after the previous patch, before</td>'
            f'<td>{fmt_short(s["stg_first"]) if s["stg_first"] is not None else "–"}</td></tr>'
            f'<tr class="tb-tip-staging"><td>Staging versions</td><td>{nv(s["stg_run"])}</td></tr>'
            f'<tr class="tb-tip-experimental"><td>Experimental versions</td><td>{nv(s["exp_run"])}</td></tr>')
    return _html.escape(f'<b>{_html.escape(g["version"])}</b><span class="tb-tip-sub">{when}</span>'
                        f'<table class="tb-tip-table">{rows}</table>', quote=True)


def _patch_rows(groups, now):
    released = [g for g in reversed(groups) if g["version"]]
    stats = [group_stats(g, now) for g in released]
    longest = lambda key: max([s[key].total_seconds() for s in stats if s[key]] + [1])  # noqa: E731
    # Staging began and Experimental began share one scale of days, so their bars compare across the row
    full_stg = full_exp = max(longest("stg_start"), longest("exp_lead"), longest("stg_first"))
    rows = []
    for g, s in zip(released, stats):
        data = "".join(f' data-{k}="{int(v.total_seconds())}"' for k, v in
                       (("lag2", s["staging_lag2"]), ("lag", s["staging_lag"]), ("stg1", s["stg_first"]),
                        ("stg", s["stg_start"]),
                        ("lead", s["exp_lead"])) if v is not None)
        data += ' data-partial="1"' if s["exp_cut"] else ""
        n_stg, n_exp = nv(s["stg_run"]), nv(s["exp_run"])
        counts = (f'<span class="tb-pr-cell tb-pr-counts" data-label="{PR_COLUMNS[5]}"><span class="tb-count tb-staging" data-n="{n_stg}">{n_stg}</span>'
                  f'<span class="tb-count tb-experimental" data-n="{n_exp}">{n_exp}</span></span>')
        lead = _bar_cell(s["exp_lead"], full_exp, "experimental", label=PR_COLUMNS[4])
        if s["exp_cut"]:
            lead = lead.replace("<b>", "<b>≥ ", 1)
        rows.append(f'<div class="tb-pr tb-tip-target" data-patch="{_html.escape(g["version"])}" '
                    f'data-year="{g["moment"].year}"{data} data-tooltip="{_row_tip(g, s)}">'
                    f'<span class="tb-pr-name">{_chip(g["version"])}<span class="tb-sub">'
                    f'{fmt_day((g["moment"] if g["exact"] else _midnight(g["date"])).date())}</span></span>'
                    + _bar_cell(s["staging_lag2"], LAG2_STAGING_CAP_H * 3600, "staging", True, PR_COLUMNS[0])
                    + _bar_cell(s["staging_lag"], LAG_STAGING_CAP_H * 3600, "staging", True, PR_COLUMNS[1])
                    + _bar_cell(s["stg_first"], full_stg, "staging", label=PR_COLUMNS[2])
                    + _bar_cell(s["stg_start"], full_stg, "staging", label=PR_COLUMNS[3]) + lead + counts + '</div>')
    return "".join(rows) or _empty_row_div()


def patch_card(groups, now, major_groups):
    """Each patch, newest first: how long after the last Staging build it came out (the column that answers the
    question, in gold), when the Staging run-up began, when Experimental began, and the builds. Whole patches by default
    (owner 2026-11-10: the letter patches are noise here); a whole patch's run-up then includes the builds made under
    the letter patches before it."""
    head = ('<div class="tb-pr tb-pr-head"><span class="tb-pr-name">Patch</span>'
            '<span class="tb-pr-cell is-key">After the second-to-last Staging build</span>'
            '<span class="tb-pr-cell is-key">After the last Staging build</span>'
            '<span class="tb-pr-cell">First Staging build after the previous patch</span>'
            '<span class="tb-pr-cell">Staging run-up began before</span>'
            '<span class="tb-pr-cell">Experimental began before</span>'
            '<span class="tb-pr-cell tb-pr-counts">Versions</span></div>')
    modes = '<div class="tb-series">' + "".join(
        f'<button type="button" class="cat-filter-btn tb-lag-btn{" active" if k == "major" else ""}" data-lag="{k}" '
        f'aria-pressed="{"true" if k == "major" else "false"}">{label}</button>'
        for k, label in (("major", "Whole patches"), ("all", "All patches"))) + '</div>'
    none = '<div class="tb-empty tb-plist-none" hidden>No patches in these years</div>'   # the year filter shows it
    lists = (f'<div class="tb-plist" data-lag="major">{head}{_patch_rows(major_groups, now)}{none}</div>'
             f'<div class="tb-plist" data-lag="all" hidden>{head}{_patch_rows(groups, now)}{none}</div>')
    return (f'<div class="tb-card"><div class="tb-card-head"><div class="cal-ig-h">Each patch</div>{modes}</div>'
            f'{lists}</div>')


def _empty_row_div():
    return '<div class="tb-empty">No builds yet</div>'


# ---------------------------------------------------------------- the calendar of builds

def _dots(c):
    """A day's dots under its number: Experimental then Staging, sized by 1, 2, 3+ builds; none on an empty day."""
    dots = "".join(f'<i class="tb-dot-{k} tb-d{min(c[br], 3)}"></i>' for br, k in (("experimental", "e"), ("staging", "s"))
                   if c[br])
    return f'<span class="tb-dots">{dots}</span>' if dots else ""


def _day_counts(builds):
    out = {}
    for b in builds:
        if b["branch"] in BRANCHES:
            out.setdefault(b["time"].date(), {"experimental": 0, "staging": 0})[b["branch"]] += b.get("n", 1)
    return out


def _year_picker(years, chosen):
    """The Patches calendar's year picker, the same markup (calendar.py's page script drives every picker)."""
    opts = "".join(f'<li class="cal-year-opt{" is-selected" if y == chosen else ""}" role="option" data-year="{y}" '
                   f'aria-selected="{"true" if y == chosen else "false"}">{y}</li>' for y in years)
    return ('<div class="cal-year-picker"><button type="button" class="cal-year-current" aria-haspopup="listbox" '
            f'aria-expanded="false"><span class="cal-year-current-val">{chosen}</span>'
            '<span class="cal-year-caret" aria-hidden="true">▾</span></button>'
            f'<ul class="cal-year-menu" role="listbox" hidden>{opts}</ul></div>')


def builds_calendar(builds, rels, years, patch_pages=(), today=None, fix_switch=""):
    """The Patches calendar block, the same markup and look (owner 2026-11-10: "календари отличаются"): the year
    picker in its header (the key where Patches has Compact), one year's grid at a time, the year's numbers in the
    footer. In the grid a day with Experimental builds is filled in ember (darker for more), a day with Staging builds
    gets a gold frame, a patch day shows the patch as on Patches. Every day with something has a short tooltip."""
    from calendar import monthrange
    days = _day_counts(builds)
    patch_on = {d: v for v, d in rels}
    newest = sorted(years, reverse=True)
    key = ('<div class="tb-keys tb-cal-key">'
           '<span class="tb-key"><i class="tb-dot-e tb-d3"></i>Experimental</span>'
           '<span class="tb-key"><i class="tb-dot-s tb-d3"></i>Staging</span></div>')
    out = ['<div class="cal-year-block is-current tb-calblock" data-collapsed="false">',
           f'<div class="cal-year-label">{_year_picker(newest, newest[0]) if newest else ""}'
           f'<div class="tb-cal-right">{key}{fix_switch}</div></div>']
    for year in newest:
        cells = []
        for month in range(1, 13):
            cells.append(f'<div class="cal-full-month-name" data-month="{month}">{MONTHS[month - 1]}</div>')
            for day in range(1, 32):
                attrs = f' data-month="{month}" data-day="{day}"'
                if day > monthrange(year, month)[1]:
                    cells.append(f'<div class="cal-full-day no-day"{attrs}></div>')
                    continue
                d = datetime(year, month, day).date()
                c = days.get(d, {"experimental": 0, "staging": 0})
                v = patch_on.get(d)
                # A dot per server under the number, bigger for 2 and 3+ builds (owner 2026-11-10 chose "Dots" of nine)
                cls = ["cal-full-day", "tb-day"]
                if c["experimental"]:
                    cls.append(f'tb-e{min(c["experimental"], 3)}')
                if c["staging"]:
                    cls.append(f'tb-s{min(c["staging"], 3)}')
                if v:
                    cls += ["has-patch", "major" if v[-1].isdigit() else "sub"]
                if c["experimental"] or c["staging"]:
                    # The day itself is the cell: the tooltip is only its builds, a row per server
                    cls.append("tb-tip-target")
                    attrs += f' data-c="{c["experimental"]},{c["staging"]}"'     # the tooltip is written on hover
                text = (_html.escape(v) if v else str(day)) + _dots(c)
                tag, href = ("a", f' href="patches/{v}.html?from=calendar"') if v and v in patch_pages else ("div", "")
                cells.append(f'<{tag} class="{" ".join(cls)}"{href}{attrs}>{text}</{tag}>')
        n = {br: sum(c[br] for d, c in days.items() if d.year == year) for br in BRANCHES}
        n_patches = sum(1 for d in patch_on if d.year == year)
        out.append(f'<div class="cal-year-pane" data-year="{year}"{"" if year == newest[0] else " hidden"}>'
                   f'<div class="cal-mode-full"><div class="cal-full-grid">{"".join(cells)}</div></div>'
                   '<div class="cal-year-summary"><div class="cal-year-summary-left">'
                   f'<span class="cal-year-summary-key">Experimental versions:</span> '
                   f'<span class="cal-year-summary-val tb-sum-experimental">{n["experimental"]}</span>'
                   f'<span class="tb-sum-gap"></span><span class="cal-year-summary-key">Staging versions:</span> '
                   f'<span class="cal-year-summary-val tb-sum-staging">{n["staging"]}</span></div>'
                   # each "key: value" pair in its own item, as the Patches footer (its right side is a flex row)
                   f'<div class="cal-year-summary-right"><span class="cal-ys-item"><span class="cal-year-summary-key">'
                   f'Patches:</span> <span class="cal-year-summary-val">{n_patches}</span></span></div></div></div>')
    out.append('</div>')
    return "".join(out)


def _ts(t):
    return int(t.timestamp()) if t else None


def medians(groups, now):
    """Over the released patches: the median time after the last Staging build, since the Staging run-up began, and
    since the first Experimental build (only patches whose whole run-up is in the log)."""
    released = [g for g in groups if g["version"]]
    stats = [group_stats(g, now) for g in released]
    pick = lambda key, whole: [s[key] for g, s in zip(released, stats) if s[key] and (not whole or not s["exp_cut"])]  # noqa: E731
    return {k: (median(v) if v else None) for k, v in
            (("lag2", pick("staging_lag2", False)), ("lag", pick("staging_lag", False)), ("stg1", pick("stg_first", True)),
             ("stg", pick("stg_start", True)),
             ("lead", pick("exp_lead", True)))}


# ---------------------------------------------------------------- the tab

def year_filter(years):
    """From / To over everything under the calendar, which has its own year (owner 2026-11-10). calendar-builds.js
    recounts the medians strip from the rows of whole patches, hides the Each patch rows of other years and redraws the
    weekly, hour and weekday charts. Both default to the whole log."""
    def sel(cls, label, chosen):
        opts = "".join(f'<option value="{y}"{" selected" if y == chosen else ""}>{y}</option>' for y in years)
        return f'<label class="tb-year"><span>{label}</span><select class="cal-mode-select {cls}">{opts}</select></label>'
    return ('<div class="tb-years">' + sel("tb-year-from", "From", years[0]) + sel("tb-year-to", "To", years[-1])
            + '</div>') if years else ""


def counts_by_year(builds, branch, key, size):
    """{year: counts by hour or weekday} of one server's timed builds, for the year filter."""
    out = {}
    for b in builds:
        if b["branch"] == branch and b["timed"]:
            out.setdefault(b["time"].year, [0] * size)[key(b["time"])] += b.get("n", 1)
    return out


def answer_strip(m, since):
    """The answer in three numbers, under the calendar as the Patches calendar has its "Patch cadence" strip: the same
    .cal-infographic look (owner 2026-11-10: "вся доп информация где-то внизу, как на календаре патчей")."""
    def num(key, caption, cls=""):
        # One size for all three numbers, on one line, the caption under them (owner 2026-11-10); the answer stands
        # out by its gold and frame, not by size
        value = fmt_short(m[key]) if m[key] is not None else "–"
        return (f'<div class="cal-ig-panel tb-ig-num{cls}" data-median="{key}"><b>{value}</b>'
                f'<span>{caption}</span></div>')
    return ('<div class="cal-infographic tb-answer">'
            '<div class="cal-ig-panel cal-ig-lead"><div class="cal-ig-title">Before a whole patch</div>'
            f'<div class="cal-ig-sub">medians, <span class="tb-ig-since">{since}</span></div></div>'
            + num("lag2", "the patch comes out after the second-to-last Staging build", " is-key")
            + num("lag", "and after the last Staging build", " is-key")
            + num("stg1", "the first Staging build after the previous patch comes before it", " tb-staging-t")
            + num("stg", "the Staging run-up begins before it", " tb-staging-t")
            + num("lead", "Experimental begins before it", " tb-experimental-t")
            + '</div>')


FIX_WINDOW_H = 6


def staging_fixes(builds, moments):
    """The Staging builds that went to the live game as a fix: the next live build came within FIX_WINDOW_H hours and was
    not a patch coming out (owner 2026-11-10: Staging also carries the live game's fixes, which are not a run-up)."""
    patch_times = {t for t, exact in moments.values() if exact}
    live = sorted(b["time"] for b in builds if b["branch"] == "public")
    out = set()
    j = 0
    for b in sorted((b for b in builds if b["branch"] == "staging"), key=lambda b: b["time"]):
        while j < len(live) and live[j] < b["time"]:
            j += 1
        if j < len(live) and live[j] - b["time"] <= timedelta(hours=FIX_WINDOW_H) and live[j] not in patch_times:
            out.add(id(b))
    return out


def fix_toggle(hidden):
    """The switch in the calendar's header, where Patches has Compact (the same markup and look)."""
    return ('<label class="ua-upgrades-toggle cal-compact-toggle tb-fix-toggle">'
            '<span class="ua-upgrades-label">Hide Staging fixes</span>'
            f'<input type="checkbox" class="ua-switch-input tb-fix-input"{" checked" if hidden else ""}>'
            '<span class="ua-switch"></span></label>')


def _view(builds, rels, moments, years, now, patch_pages, hidden):
    """One Test servers view of these builds (all of them, or without the Staging fixes)."""
    groups = group_by_patch(builds, rels, moments)
    major_groups = group_by_patch(builds, major_releases(rels), moments)
    since = f"{years[0]} to now" if years else "no builds yet"
    p = [f'<div class="tb-view" data-fix="{"hide" if hidden else "all"}"{"" if hidden else " hidden"}>']
    p.append(builds_calendar(builds, rels, years, patch_pages, fix_switch=fix_toggle(hidden)))
    # From / To over everything under the calendar (owner 2026-11-10: the answer and Each patch follow the years too)
    p.append(year_filter(years))
    p.append(answer_strip(medians(major_groups, now), since))
    p.append(patch_card(groups, now, major_groups))
    p.append(weekly_card(builds, rels, now, moments, groups, major_groups))
    p.append('<div class="tb-charts">')
    p.append(when_card("Hour of day, UTC", {br: hour_counts(builds, br) for br in BRANCHES},
                       [f"{h:02d}" for h in range(24)], "hour", [f"{h:02d}:00 to {h:02d}:59 UTC" for h in range(24)],
                       {br: counts_by_year(builds, br, lambda t: t.hour, 24) for br in BRANCHES}))
    p.append(when_card("Day of week, UTC", {br: weekday_counts(builds, br) for br in BRANCHES},
                       list(WEEKDAYS), "weekday", list(WEEKDAY_NAMES),
                       {br: counts_by_year(builds, br, lambda t: t.weekday(), 7) for br in BRANCHES}))
    p.append('</div></div>')
    return "\n".join(p)


def since_staging(builds, history):
    """The tab covers the time Staging exists (owner 2026-11-10: the years before it, Experimental alone, were a mess):
    the builds from the first Staging build on, the patches released after it. No Staging build yet: everything."""
    staging = [b["time"] for b in builds if b["branch"] == "staging"]
    if not staging:
        return builds, history
    start = min(staging)
    kept = [r for r in history if datetime.strptime(r["date"], "%d.%m.%Y").date() >= start.date()]
    return [b for b in builds if b["time"] >= start], kept


def render_panel(builds, history, now=None, patch_pages=(), from_staging=False):
    """The whole tab's HTML, built as the Patches view: the calendar of builds on top, the answer in a strip under it
    (medians over whole patches), each patch's answer as a table; then the charts with their From / To years. Twice:
    without the Staging fixes (shown first, the switch on) and with every build; calendar-builds.js swaps them."""
    now = now or datetime.now(timezone.utc)
    if from_staging:                                      # the site's tab: Staging's time only (since_staging)
        builds, history = since_staging(builds, history)
    rels = releases(history)
    moments = patch_moments(rels, builds)                 # the live game's builds date the patches in both views
    fixes = staging_fixes(builds, moments)
    tests = [b for b in builds if b["branch"] in BRANCHES]
    years = list(range(tests[0]["time"].year, now.year + 1)) if tests else []
    clean = [b for b in builds if id(b) not in fixes]
    return "\n".join(['<section class="tb-panel" hidden>',
                      _view(clean, rels, moments, years, now, patch_pages, True),
                      _view(builds, rels, moments, years, now, patch_pages, False),
                      '</section>'])
