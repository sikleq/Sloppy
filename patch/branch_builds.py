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
        out.append({"branch": b["branch"], "from": b.get("from"), "version": b["version"], "time": t, "timed": timed})
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
    return ordered


def fmt_span(td):
    """A duration as days and hours: '41 d 5 h', '7 h'."""
    hours = int(td.total_seconds() // 3600)
    d, h = divmod(max(hours, 0), 24)
    return f"{d} d {h} h" if d else f"{h} h"


def group_stats(g, now):
    """Counts, first and last build per server; time from the first Experimental build and from the last Staging build
    to the patch (to now for the next patch, which is not out yet)."""
    end = g["moment"] or now
    s = {}
    for br in BRANCHES:
        lst = g[br]
        s[br] = {"count": len(lst), "first": lst[0] if lst else None, "last": lst[-1] if lst else None}
    first_exp, last_st = s["experimental"]["first"], s["staging"]["last"]
    s["exp_lead"] = end - first_exp["time"] if first_exp else None
    s["staging_lag"] = end - last_st["time"] if last_st else None
    s["exp_lead_text"] = None if first_exp is None else ("≥ " if g["partial"] else "") + fmt_span(s["exp_lead"])
    s["staging_lag_text"] = None if last_st is None else fmt_span(s["staging_lag"])
    return s


def hour_counts(builds, branch):
    c = [0] * 24
    for b in builds:
        if b["branch"] == branch and b["timed"]:
            c[b["time"].hour] += 1
    return c


def weekday_counts(builds, branch):
    c = [0] * 7
    for b in builds:
        if b["branch"] == branch and b["timed"]:
            c[b["time"].weekday()] += 1
    return c


def fmt_time(t):
    return f"{t.day} {MONTHS[t.month - 1]} {t.year} {t:%H:%M}"


def fmt_day(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def build_time_text(b):
    """A timed build: its minute. An untimed one: "by" the moment it was first seen."""
    return fmt_time(b["time"]) if b["timed"] else f"by {fmt_time(b['time'])}"


# ---------------------------------------------------------------- charts

def _nice_top(maxv):
    step = next(st for st in (1, 2, 3, 4, 5, 10, 15, 20, 25, 50, 100, 200) if st * 4 >= maxv)
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
        tip = _tip(f"<b>{_html.escape(names[i])}</b>", *(f"{LABELS[br]}: {series[br][i]}" for br in shown))
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
        w[b["branch"]] += 1
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


def _patch_tip(g, s):
    when = fmt_time(g["moment"]) + " UTC" if g["exact"] else fmt_day(g["date"])
    lines = [f'<b>{_html.escape(g["version"])}</b> came out {when}']
    ex, st = s["experimental"], s["staging"]
    lines.append(f'Experimental: {ex["count"]} build{"" if ex["count"] == 1 else "s"}'
                 + (f', the first {s["exp_lead_text"]} before' if ex["first"] else ""))
    if st["last"]:
        first = fmt_span(g["moment"] - st["first"]["time"]) if g["moment"] else None
        lines.append(f'Staging: {st["count"]} builds, the first {first} and the last {s["staging_lag_text"]} before'
                     if first and st["count"] > 1 else f'Staging: {st["count"]} build, {s["staging_lag_text"]} before')
    else:
        lines.append('Staging: no builds')
    return _tip(*lines)


SERIES = ("both", "experimental", "staging")
START_LABEL_ROOM = 64          # px of the weekly axis kept for the start label ("Oct 2021")
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
        leads = ("the next patch" if patch == "next" else patch) if patch else None
        counts = {"experimental": e, "staging": st}
        tip = _tip(f"<b>Week of {fmt_day(monday)}</b>", *(f"{LABELS[br]}: {counts[br]}" for br in shown),
                   *([f"Led to {_html.escape(leads)}"] if leads else []))
        s.append(f'<rect class="tb-hit tb-tip-target"{dp} data-tooltip="{tip}" x="{pad_l + col * i:.1f}" y="{top}" '
                 f'width="{col:.2f}" height="{plot_h}"/>')
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
    return (f'<div class="tb-card"><div class="tb-card-head"><div class="cal-ig-h">Builds per week</div>'
            f'{series_buttons()}</div><div class="tb-weekly-scroll">{charts}</div></div>')


LAG_STAGING_CAP_H = 48


def _lag_rows(groups, now):
    """The rows of one "Before each patch" list, newest first."""
    released = [g for g in reversed(groups) if g["version"]]
    stats = [group_stats(g, now) for g in released]
    max_lead = max([s["exp_lead"].total_seconds() for s in stats if s["exp_lead"]] + [1])
    cap = LAG_STAGING_CAP_H * 3600
    rows = []
    for g, s in zip(released, stats):
        tip = _patch_tip(g, s)
        cells = []
        for br, span, text, full in (("experimental", s["exp_lead"], s["exp_lead_text"], max_lead),
                                     ("staging", s["staging_lag"], s["staging_lag_text"], cap)):
            if span is None:
                cells.append('<span class="tb-lag-cell"><span class="ua-dash">–</span></span>')
                continue
            share = min(span.total_seconds() / full, 1)
            over = " is-over" if span.total_seconds() > full else ""
            cells.append(f'<span class="tb-lag-cell"><span class="tb-lag-bar tb-{br}{over}" style="--p:{share:.3f}"></span>'
                         f'<span class="tb-lag-val">{text}</span></span>')
        spans = "".join(f' data-{k}="{int(v.total_seconds())}"' for k, v in (("lead", s["exp_lead"]), ("lag", s["staging_lag"]))
                        if v is not None) + (' data-partial="1"' if g["partial"] else "")
        rows.append(f'<div class="tb-lag-row tb-tip-target" data-patch="{_html.escape(g["version"])}" '
                    f'data-year="{g["moment"].year}"{spans} data-tooltip="{tip}">'
                    f'<span class="tb-lag-name">{_html.escape(g["version"])}</span>{"".join(cells)}</div>')
    return "".join(rows) or _empty_row_div()


def major_releases(rels):
    """The whole patches (7.41, not 7.41a)."""
    return [r for r in rels if r[0][-1].isdigit()]


def lag_card(groups, now, major_groups=None):
    """Before each patch: how long from the first Experimental build, and from the last Staging build, to the patch. Two
    bars per patch on their own scales (Experimental in days; Staging capped at LAG_STAGING_CAP_H: a longer bar ends
    in a cut and keeps its number). Two lists: every patch, and whole patches only (owner 2026-11-10), where a build
    belongs to the next whole patch, so a whole patch's run-up includes what came out under the letter patches before."""
    head = ('<div class="tb-lag-row tb-lag-head"><span class="tb-lag-name">Patch</span>'
            '<span class="tb-lag-cell tb-experimental-h">First Experimental build to patch</span>'
            f'<span class="tb-lag-cell tb-staging-h">Last Staging build to patch, bars up to {LAG_STAGING_CAP_H} h</span></div>')
    modes = '<div class="tb-series">' + "".join(
        f'<button type="button" class="cat-filter-btn tb-lag-btn{" active" if k == "all" else ""}" data-lag="{k}" '
        f'aria-pressed="{"true" if k == "all" else "false"}">{label}</button>'
        for k, label in (("all", "All patches"), ("major", "Whole patches only"))) + '</div>'
    lists = (f'<div class="tb-lag" data-lag="all">{head}{_lag_rows(groups, now)}</div>'
             f'<div class="tb-lag" data-lag="major" hidden>{head}{_lag_rows(major_groups or [], now)}</div>')
    return (f'<div class="tb-card"><div class="tb-card-head"><div class="cal-ig-h">Before each patch</div>{modes}</div>'
            f'{lists}</div>')


def _empty_row_div():
    return '<div class="tb-empty">No builds yet</div>'


# ---------------------------------------------------------------- tables

def _th(label, key, first="desc", extra=""):
    return (f'<th class="sortable" data-sort="{key}" data-first="{first}"{extra}><span class="th-label">{label}</span>'
            '<span class="sort-ind" aria-hidden="true"></span></th>')


def _td(text, value, cls=""):
    v = "" if value is None else value
    shown = text if text is not None else '<span class="ua-dash">–</span>'
    return f'<td data-v="{v}"{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>{shown}</td>'


def _ts(t):
    return int(t.timestamp()) if t else None


def _empty_row(cols):
    return f'<tr><td colspan="{cols}" class="tb-empty">No builds yet</td></tr>'


def _patch_name(g):
    if not g["version"]:
        return 'Next patch<span class="tb-sub">not out yet</span>'
    when = fmt_time(g["moment"]) if g["exact"] else fmt_day(g["date"])
    return f'{_html.escape(g["version"])}<span class="tb-sub">{when}</span>'


def _span_cell(text, span, b):
    """A duration with the build it counts from in a small line under it."""
    if b is None:
        return _td(None, None)
    return _td(f'{text}<span class="tb-sub">{fmt_day(b["time"].date())}</span>', int(span.total_seconds()))


def summary_table(groups, now):
    head = ('<thead><tr>' + _th("Patch", 0, extra=' rowspan="2"')
            + '<th colspan="2" class="tb-experimental-h">Experimental</th>'
            '<th colspan="2" class="tb-staging-h">Staging</th></tr><tr>'
            + _th("Builds", 1) + _th("First build to patch", 2)
            + _th("Builds", 3) + _th("Last build to patch", 4, first="asc")
            + '</tr></thead>')
    rows = []
    for g in reversed(groups):
        s = group_stats(g, now)
        rows.append(f'<tr data-year="{(g["moment"] or now).year}">'
                    + _td(_patch_name(g), _ts(g["moment"]) if g["moment"] else 2 ** 40, "tb-patch")
                    + _td(str(s["experimental"]["count"]), s["experimental"]["count"])
                    + _span_cell(s["exp_lead_text"], s["exp_lead"], s["experimental"]["first"])
                    + _td(str(s["staging"]["count"]), s["staging"]["count"])
                    + _span_cell(s["staging_lag_text"], s["staging_lag"], s["staging"]["last"]) + '</tr>')
    return f'<table class="tb-table tb-summary">{head}<tbody>{"".join(rows) or _empty_row(5)}</tbody></table>'


def builds_table(groups, now):
    head = ('<thead><tr>' + _th("Time, UTC", 0) + _th("Server", 1, first="asc") + _th("Version", 2)
            + _th("Patch", 3) + _th("To patch", 4, first="asc") + '</tr></thead>')
    rows = []
    for g in reversed(groups):
        end = g["moment"] or now
        order = _ts(g["moment"]) if g["moment"] else 2 ** 40
        patch = _html.escape(g["version"]) if g["version"] else "Next patch"
        for b in sorted(g["experimental"] + g["staging"], key=lambda b: b["time"], reverse=True):
            to_patch = end - b["time"]
            ver = f'{b["from"]} → {b["version"]}' if b["from"] is not None else str(b["version"])
            rows.append(f'<tr data-year="{b["time"].year}">' + _td(build_time_text(b), _ts(b["time"]))
                        + _td(f'<span class="tb-dot tb-{b["branch"]}"></span>{LABELS[b["branch"]]}', b["branch"])
                        + _td(ver, b["version"]) + _td(patch, order)
                        + _td(fmt_span(to_patch), int(to_patch.total_seconds())) + '</tr>')
    return f'<table class="tb-table tb-builds">{head}<tbody>{"".join(rows) or _empty_row(5)}</tbody></table>'


def medians(groups, now):
    """Median Experimental lead and Staging lag over the released patches whose whole lead is in the log."""
    released = [g for g in groups if g["version"]]
    stats = [group_stats(g, now) for g in released]
    leads = [s["exp_lead"] for g, s in zip(released, stats) if s["exp_lead"] and not g["partial"]]
    lags = [s["staging_lag"] for s in stats if s["staging_lag"]]
    return (median(leads) if leads else None), (median(lags) if lags else None)


# ---------------------------------------------------------------- the tab

def _tile(value, caption, cls="", attrs=""):
    return f'<div class="tb-tile{cls}"{attrs}><b>{value}</b><span>{caption}</span></div>'


def year_filter(years):
    """From / To: the years the whole tab shows (calendar-builds.js redraws the charts, the tiles and the bars, and hides
    the rows outside). Both default to the whole log."""
    def sel(cls, label, chosen):
        opts = "".join(f'<option value="{y}"{" selected" if y == chosen else ""}>{y}</option>' for y in years)
        return f'<label class="tb-year"><span>{label}</span><select class="cal-mode-select {cls}">{opts}</select></label>'
    return ('<div class="tb-years">' + sel("tb-year-from", "From", years[0]) + sel("tb-year-to", "To", years[-1])
            + '</div>') if years else ""


def _per_year(builds, branch):
    out = {}
    for b in builds:
        if b["branch"] == branch:
            out[b["time"].year] = out.get(b["time"].year, 0) + 1
    return ",".join(f"{y}:{c}" for y, c in sorted(out.items()))


def counts_by_year(builds, branch, key, size):
    """{year: counts by hour or weekday} of one server's timed builds, for the year filter."""
    out = {}
    for b in builds:
        if b["branch"] == branch and b["timed"]:
            out.setdefault(b["time"].year, [0] * size)[key(b["time"])] += 1
    return out


def render_panel(builds, history, now=None):
    """The whole tab's HTML: four numbers, the run-up chart, when Valve push, the table by patch, every build folded."""
    now = now or datetime.now(timezone.utc)
    rels = releases(history)
    moments = patch_moments(rels, builds)
    groups = group_by_patch(builds, rels, moments)
    tests = [b for b in builds if b["branch"] in BRANCHES]
    lead, lag = medians(groups, now)
    since = ("since " + fmt_day(builds[0]["time"].date())) if builds else "no builds yet"
    years = list(range(tests[0]["time"].year, now.year + 1)) if tests else []
    p = ['<section class="tb-panel" hidden>']
    p.append(year_filter(years))
    p.append('<div class="tb-tiles">'
             + _tile(sum(1 for b in tests if b["branch"] == "experimental"), f"Experimental builds {since}", " tb-experimental-t",
                     f' data-count="{_per_year(tests, "experimental")}" data-what="Experimental builds"')
             + _tile(sum(1 for b in tests if b["branch"] == "staging"), f"Staging builds {since}", " tb-staging-t",
                     f' data-count="{_per_year(tests, "staging")}" data-what="Staging builds"')
             + _tile(fmt_span(lead) if lead is not None else "–", "median from the first Experimental build to the patch",
                     "", ' data-median="lead"')
             + _tile(fmt_span(lag) if lag is not None else "–", "median from the last Staging build to the patch",
                     "", ' data-median="lag"')
             + '</div>')
    major_groups = group_by_patch(builds, major_releases(rels), moments)
    p.append(weekly_card(builds, rels, now, moments, groups, major_groups))
    p.append(lag_card(groups, now, major_groups))
    p.append('<div class="tb-charts">')
    p.append(when_card("Hour of day, UTC", {br: hour_counts(builds, br) for br in BRANCHES},
                       [f"{h:02d}" for h in range(24)], "hour", [f"{h:02d}:00 to {h:02d}:59 UTC" for h in range(24)],
                       {br: counts_by_year(builds, br, lambda t: t.hour, 24) for br in BRANCHES}))
    p.append(when_card("Day of week, UTC", {br: weekday_counts(builds, br) for br in BRANCHES},
                       list(WEEKDAYS), "weekday", list(WEEKDAY_NAMES),
                       {br: counts_by_year(builds, br, lambda t: t.weekday(), 7) for br in BRANCHES}))
    p.append('</div>')
    p.append('<div class="tb-card"><div class="cal-ig-h">By patch</div><div class="tb-table-scroll">'
             + summary_table(groups, now) + '</div></div>')
    p.append(f'<details class="tb-card tb-more"><summary class="cal-ig-h">All builds ({len(tests)})</summary>'
             '<div class="tb-table-scroll tb-builds-scroll">' + builds_table(groups, now) + '</div></details>')
    p.append('</section>')
    return "\n".join(p)
