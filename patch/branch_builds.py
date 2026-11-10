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
from datetime import date, datetime, timedelta, timezone
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
TIMELINE_PX_PER_DAY = 8
TIMELINE_MIN_DAYS = 45


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


def bar_chart_svg(series, labels, uid):
    """Grouped bars, one bar per server in each column (hour or weekday). series: {branch: counts}."""
    n = len(labels)
    maxv = max([1] + [v for vals in series.values() for v in vals])
    step, top = _nice_top(maxv)
    view_w, pad_l, pad_r, pad_t, chart_h, label_h = 520, 26, 6, 10, 90, 16
    col = (view_w - pad_l - pad_r) / n
    bar = max(2.0, col * 0.36)
    s = [f'<svg class="tb-bars" data-chart="{uid}" viewBox="0 0 {view_w} {chart_h + label_h}" role="img">']
    for k in range(5):
        gy = pad_t + (1 - k / 4) * (chart_h - pad_t)
        if 0 < k:
            s.append(f'<line class="cal-ig-grid" x1="{pad_l}" y1="{gy:.1f}" x2="{view_w - pad_r}" y2="{gy:.1f}"/>')
        s.append(f'<text class="cal-ig-ytick" x="{pad_l - 5}" y="{gy + 3:.1f}" text-anchor="end">{step * k}</text>')
    s.append(f'<line class="cal-ig-axis" x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{chart_h}"/>')
    for i, lab in enumerate(labels):
        cx = pad_l + col * (i + 0.5)
        for j, br in enumerate(BRANCHES):
            v = series[br][i]
            h = v / top * (chart_h - pad_t)
            x = cx - bar + j * bar
            s.append(f'<rect class="tb-bar tb-{br}" x="{x:.1f}" y="{chart_h - h:.1f}" width="{bar:.1f}" height="{h:.1f}">'
                     f'<title>{LABELS[br]}, {_html.escape(lab)}: {v}</title></rect>')
        if n <= 7 or i % 3 == 0:
            s.append(f'<text class="cal-ig-spark-lbl" x="{cx:.1f}" y="{chart_h + 12}" text-anchor="middle">{lab}</text>')
    s.append(f'<line class="cal-ig-axis is-base" x1="{pad_l}" y1="{chart_h}" x2="{view_w - pad_r}" y2="{chart_h}"/>')
    s.append('</svg>')
    return "".join(s)


def timeline_range(builds, now):
    """First and last day of the timeline: the first test build to a few days after now, at least TIMELINE_MIN_DAYS."""
    end = now.date() + timedelta(days=3)
    start = end - timedelta(days=TIMELINE_MIN_DAYS)
    tests = [b for b in builds if b["branch"] in BRANCHES]
    if tests:
        start = min(start, tests[0]["time"].date() - timedelta(days=3))
    return start, end


def timeline_svg(builds, rels, now, moments=None):
    """Rows Experimental, Staging and both together; one mark per build; a vertical line where each patch came out."""
    moments = moments or patch_moments(rels, builds)
    start, end = timeline_range(builds, now)
    w = (end - start).days * TIMELINE_PX_PER_DAY
    row_h, top, axis_h = 26, 22, 18
    rows = list(BRANCHES) + ["both"]
    h = top + row_h * len(rows) + axis_h
    t0 = _midnight(start)

    def x_of(t):
        return (t - t0).total_seconds() / 86400 * TIMELINE_PX_PER_DAY

    s = [f'<svg class="tb-timeline" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">']
    for i, _ in enumerate(rows):
        s.append(f'<rect class="tb-row-band{" is-alt" if i % 2 else ""}" x="0" y="{top + row_h * i}" width="{w}" height="{row_h}"/>')
    d = date(start.year, start.month, 1)
    while d <= end:
        if d >= start:
            x = x_of(_midnight(d))
            s.append(f'<line class="cal-ig-grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{h - axis_h}"/>')
            s.append(f'<text class="cal-ig-spark-lbl" x="{x + 3:.1f}" y="{h - 5}">{MONTHS[d.month - 1]} {d.year}</text>')
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    last_lbl = -1e9
    for v, _ in sorted(rels, key=lambda r: moments[r[0]][0]):
        t = moments[v][0]
        if not (t0 <= t <= _midnight(end)):
            continue
        x = x_of(t)
        major = v[-1].isdigit()
        s.append(f'<line class="tb-patch-line{"" if major else " is-letter"}" x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{h - axis_h}"/>')
        if x - last_lbl >= 34:                       # labels of patches days apart would overlap: the earlier one keeps its
            s.append(f'<text class="tb-patch-lbl" x="{x:.1f}" y="{top - 8}" text-anchor="middle">{_html.escape(v)}</text>')
            last_lbl = x
    tx = x_of(now)
    s.append(f'<line class="tb-today-line" x1="{tx:.1f}" y1="{top}" x2="{tx:.1f}" y2="{h - axis_h}"/>')
    for b in builds:
        if b["branch"] not in BRANCHES:
            continue
        x = x_of(b["time"])
        for i, row in enumerate(rows):
            if row not in (b["branch"], "both"):
                continue
            cls = f'tb-mark tb-{b["branch"]}{"" if b["timed"] else " is-untimed"}'
            s.append(f'<rect class="{cls}" x="{x - 1:.1f}" y="{top + row_h * i + 5}" width="2" height="{row_h - 10}">'
                     f'<title>{LABELS[b["branch"]]} {b["version"]}, {build_time_text(b)} UTC</title></rect>')
    s.append('</svg>')
    return "".join(s)


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


def _build_cell(b):
    if b is None:
        return _td(None, None)
    return _td(f'{build_time_text(b)}<span class="tb-sub">{b["version"]}</span>', _ts(b["time"]))


def _patch_name(g):
    if not g["version"]:
        return 'Next patch<span class="tb-sub">not out yet</span>'
    when = fmt_time(g["moment"]) if g["exact"] else fmt_day(g["date"])
    return f'{_html.escape(g["version"])}<span class="tb-sub">{when}</span>'


def summary_table(groups, now):
    head = ('<thead><tr>' + _th("Patch", 0, extra=' rowspan="2"')
            + '<th colspan="4" class="tb-experimental-h">Experimental</th>'
            '<th colspan="4" class="tb-staging-h">Staging</th></tr><tr>'
            + _th("Builds", 1) + _th("First", 2) + _th("Last", 3) + _th("First to patch", 4)
            + _th("Builds", 5) + _th("First", 6) + _th("Last", 7) + _th("Last to patch", 8, first="asc")
            + '</tr></thead>')
    rows = []
    for g in reversed(groups):
        s = group_stats(g, now)
        cells = [_td(_patch_name(g), _ts(g["moment"]) if g["moment"] else 2 ** 40, "tb-patch")]
        for br, text, span in (("experimental", s["exp_lead_text"], s["exp_lead"]),
                               ("staging", s["staging_lag_text"], s["staging_lag"])):
            x = s[br]
            cells += [_td(str(x["count"]), x["count"]), _build_cell(x["first"]), _build_cell(x["last"]),
                      _td(text, None if span is None else int(span.total_seconds()))]
        rows.append('<tr>' + "".join(cells) + '</tr>')
    return f'<table class="tb-table tb-summary">{head}<tbody>{"".join(rows) or _empty_row(9)}</tbody></table>'


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
            rows.append('<tr>' + _td(build_time_text(b), _ts(b["time"]))
                        + _td(f'<span class="tb-dot tb-{b["branch"]}"></span>{LABELS[b["branch"]]}', b["branch"])
                        + _td(ver, b["version"]) + _td(patch, order)
                        + _td(fmt_span(to_patch), int(to_patch.total_seconds())) + '</tr>')
    return f'<table class="tb-table tb-builds">{head}<tbody>{"".join(rows) or _empty_row(5)}</tbody></table>'


def medians(groups, now):
    """Median Experimental lead and Staging lag over the released patches whose whole lead is in the log."""
    done = [group_stats(g, now) for g in groups if g["version"]]
    leads = [s["exp_lead"] for g, s in zip([g for g in groups if g["version"]], done) if s["exp_lead"] and not g["partial"]]
    lags = [s["staging_lag"] for s in done if s["staging_lag"]]
    return (median(leads) if leads else None), (median(lags) if lags else None)


# ---------------------------------------------------------------- the tab

def render_panel(builds, history, now=None):
    """The whole tab's HTML."""
    now = now or datetime.now(timezone.utc)
    rels = releases(history)
    moments = patch_moments(rels, builds)
    groups = group_by_patch(builds, rels, moments)
    tests = [b for b in builds if b["branch"] in BRANCHES]
    lead, lag = medians(groups, now)
    key = ''.join(f'<span class="tb-key"><span class="tb-dot tb-{br}"></span>{LABELS[br]}</span>' for br in BRANCHES)
    stat = ''.join(f'<span><b>{sum(1 for b in tests if b["branch"] == br)}</b> {LABELS[br]} builds</span>' for br in BRANCHES)
    if lead is not None:
        stat += f'<span><b>{fmt_span(lead)}</b> median from the first Experimental build to the patch</span>'
    if lag is not None:
        stat += f'<span><b>{fmt_span(lag)}</b> median from the last Staging build to the patch</span>'
    p = ['<section class="tb-panel" hidden>']
    p.append('<div class="tb-card tb-lead"><div class="cal-ig-title">Test servers</div>'
             f'<div class="cal-ig-sub">{("since " + fmt_day(builds[0]["time"].date())) if builds else "no builds yet"}</div>'
             f'<div class="cal-ig-statline">{stat}</div></div>')
    p.append('<div class="tb-card"><div class="cal-ig-h">Timeline</div>'
             '<div class="tb-timeline-wrap"><div class="tb-row-names">'
             + ''.join(f'<span>{n}</span>' for n in ("Experimental", "Staging", "Together"))
             + '</div><div class="tb-timeline-scroll">' + timeline_svg(builds, rels, now, moments) + '</div></div></div>')
    p.append('<div class="tb-charts">')
    p.append('<div class="tb-card"><div class="cal-ig-h">Hour of day, UTC</div>'
             + bar_chart_svg({br: hour_counts(builds, br) for br in BRANCHES}, [f"{h:02d}" for h in range(24)], "hour")
             + f'<div class="tb-keys">{key}</div></div>')
    p.append('<div class="tb-card"><div class="cal-ig-h">Day of week, UTC</div>'
             + bar_chart_svg({br: weekday_counts(builds, br) for br in BRANCHES}, list(WEEKDAYS), "weekday")
             + f'<div class="tb-keys">{key}</div></div>')
    p.append('</div>')
    p.append('<div class="tb-card"><div class="cal-ig-h">By patch</div><div class="tb-table-scroll">'
             + summary_table(groups, now) + '</div></div>')
    p.append('<div class="tb-card"><div class="cal-ig-h">Builds</div><div class="tb-table-scroll tb-builds-scroll">'
             + builds_table(groups, now) + '</div></div>')
    p.append('</section>')
    return "\n".join(p)
