"""Calendar page generator."""

import os
import html as _html

import site_common as _site

from .meta import PATCHES, RELEASE_HISTORY, _parse_date, _current_version, _render_top_nav
from .page import _ASSET_VERSION


def save_calendar_html():
    """Generate calendar.html — both modes inside a shared collapsible year block."""
    from datetime import datetime
    from calendar import monthrange
    import re as _re

    patches = []
    for r in RELEASE_HISTORY:
        d = datetime.strptime(r['date'], '%d.%m.%Y').date()
        patches.append({
            'version': r['version'], 'date': r['date'],
            'year': d.year, 'month': d.month, 'day': d.day,
        })

    by_month = {}
    for p in patches:
        by_month.setdefault((p['year'], p['month']), []).append(p)
    for k in by_month:
        by_month[k].sort(key=lambda p: p['day'])

    by_day = {(p['year'], p['month'], p['day']): p for p in patches}
    current_v = _current_version()
    years = sorted({p['year'] for p in patches}, reverse=True)

    # Per-patch lifespan: days between this release and the next release in
    # RELEASE_HISTORY (history is sorted newest-first there). Latest patch
    # uses today as the right edge. Then per-year longest/shortest.
    from datetime import datetime as _dt, date as _date
    today = _date.today()
    sorted_by_date = sorted(patches, key=lambda p: _dt.strptime(p['date'], '%d.%m.%Y').date())
    spans = {}  # version → days_running
    for i, p in enumerate(sorted_by_date):
        d = _dt.strptime(p['date'], '%d.%m.%Y').date()
        if i + 1 < len(sorted_by_date):
            nd = _dt.strptime(sorted_by_date[i+1]['date'], '%d.%m.%Y').date()
        else:
            nd = today
        spans[p['version']] = max(0, (nd - d).days)

    def year_summary(year_patches):
        if not year_patches:
            return None
        ranked = sorted(year_patches, key=lambda p: spans.get(p['version'], 0))
        min_days = spans.get(ranked[0]['version'], 0)
        max_days = spans.get(ranked[-1]['version'], 0)
        shortest_vers = [p['version'] for p in ranked if spans.get(p['version'], 0) == min_days]
        longest_vers  = [p['version'] for p in ranked if spans.get(p['version'], 0) == max_days]
        return {
            'total': len(year_patches),
            'shortest': (shortest_vers, min_days),
            'longest':  (longest_vers,  max_days),
        }
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    has_html = {p['version'] for p in PATCHES}
    expanded_years = {years[0]} if years else set()  # only current (newest) year expanded by default

    def patch_class(v):
        if _re.search(r'[a-z]$', v):
            return 'sub'
        return 'major'

    def chip_tag(v):
        if v in has_html:
            return ('a', f' href="patches/{v}.html?from=calendar"')
        return ('span', '')

    body = []
    body.append('<div class="calendar mode-full">')

    # Single year block. Year selector replaces per-year collapsible headers;
    # all years' grids are rendered in panes and only the selected pane is
    # visible at a time. The Compact toggle lives in this block's top-right
    # corner (added after the picker, below).
    body.append('<div class="cal-year-block is-current" data-collapsed="false">')
    body.append('<div class="cal-year-label">')
    default_year = years[0] if years else None
    body.append('<div class="cal-year-picker">')
    body.append(
        '<button type="button" class="cal-year-current" '
        'aria-haspopup="listbox" aria-expanded="false">'
        f'<span class="cal-year-current-val">{default_year}</span>'
        '<span class="cal-year-caret" aria-hidden="true">▾</span>'
        '</button>'
    )
    body.append('<ul class="cal-year-menu" role="listbox" hidden>')
    for year in years:
        sel = ' is-selected' if year == default_year else ''
        asel = 'true' if year == default_year else 'false'
        body.append(
            f'<li class="cal-year-opt{sel}" role="option" '
            f'data-year="{year}" aria-selected="{asel}">{year}</li>'
        )
    body.append('</ul>')
    body.append('</div>')  # cal-year-picker
    # Compact toggle — top-right corner of the calendar block, styled to match
    # the year-picker button (see .cal-compact-toggle in styles.css).
    body.append(
        '<label class="ua-upgrades-toggle cal-compact-toggle" '
        'title="Compact view">'
        '<span class="ua-upgrades-label">Compact</span>'
        '<input type="checkbox" class="ua-switch-input cal-compact-input">'
        '<span class="ua-switch"></span>'
        '</label>'
    )
    body.append('</div>')  # cal-year-label

    for year in years:
        hidden = '' if year == default_year else ' hidden'
        body.append(f'<div class="cal-year-pane" data-year="{year}"{hidden}>')

        # ---- MODE FULL ----
        body.append('<div class="cal-mode-full">')
        body.append('<div class="cal-full-grid">')
        for month in range(1, 13):
            body.append(
                f'<div class="cal-full-month-name" data-month="{month}">'
                f'{months[month-1]}</div>'
            )
            days_in_m = monthrange(year, month)[1]
            for d in range(1, 32):
                if d > days_in_m:
                    body.append(
                        f'<div class="cal-full-day no-day" '
                        f'data-month="{month}" data-day="{d}"></div>')
                    continue
                p = by_day.get((year, month, d))
                attrs = f' data-month="{month}" data-day="{d}"'
                if p:
                    cls = patch_class(p['version'])
                    tag, href = chip_tag(p['version'])
                    cur = " current" if p['version'] == current_v else ""
                    body.append(f'<{tag} class="cal-full-day has-patch {cls}{cur}"{href}{attrs}>{p["version"]}</{tag}>')
                else:
                    body.append(f'<div class="cal-full-day"{attrs}>{d}</div>')
        body.append('</div></div>')

        # ---- MODE COMPACT ----
        body.append('<div class="cal-mode-compact">')
        body.append('<div class="cal-grid">')
        for mi, mname in enumerate(months, 1):
            body.append('<div class="cal-month">')
            body.append(f'<div class="cal-month-name">{mname}</div>')
            body.append('<div class="cal-month-cells">')
            for p in by_month.get((year, mi), []):
                v = p['version']
                cls = patch_class(v)
                tag, href = chip_tag(v)
                cur = " current" if v == current_v else ""
                body.append(
                    f'<{tag} class="cal-patch {cls}{cur}"{href}>'
                    f'<span class="cal-version">{v}</span>'
                    f'<span class="cal-day">{p["day"]:02d}</span>'
                    f'</{tag}>'
                )
            body.append('</div></div>')
        body.append('</div></div>')

        # ---- YEAR SUMMARY ----
        ys = year_summary([p for p in patches if p['year'] == year])
        if ys:
            body.append(
                '<div class="cal-year-summary">'
                '<div class="cal-year-summary-left">'
                f'<span class="cal-year-summary-key">Total count:</span> '
                f'<span class="cal-year-summary-val">{ys["total"]}</span>'
                '</div>'
                '<div class="cal-year-summary-right">'
                f'<span class="cal-year-summary-key">Longest:</span> '
                f'<span class="cal-year-summary-val">{" &amp; ".join(ys["longest"][0])}</span>'
                f' <span class="cal-year-summary-meta">({ys["longest"][1]} days)</span>'
                f' &middot; '
                f'<span class="cal-year-summary-key">Shortest:</span> '
                f'<span class="cal-year-summary-val">{" &amp; ".join(ys["shortest"][0])}</span>'
                f' <span class="cal-year-summary-meta">({ys["shortest"][1]} days)</span>'
                '</div>'
                '</div>'
            )

        body.append('</div>')  # cal-year-pane

    body.append('</div>')  # cal-year-block

    # ---- INFOGRAPHIC: patch cadence (compact card under the calendar) ----
    year_counts = {}
    for p in patches:
        year_counts[p['year']] = year_counts.get(p['year'], 0) + 1
    month_counts = [0] * 12
    for p in patches:
        month_counts[p['month'] - 1] += 1
    total_patches = len(patches)
    years_tracked = len(year_counts)
    avg_per_year = (total_patches / years_tracked) if years_tracked else 0
    span_vals = sorted(spans.values())
    if span_vals:
        n = len(span_vals)
        median_span = (span_vals[n // 2] if n % 2
                       else (span_vals[n // 2 - 1] + span_vals[n // 2]) // 2)
    else:
        median_span = 0
    max_year_count = max(year_counts.values()) if year_counts else 1
    max_month_count = max(month_counts) if month_counts else 1

    min_year = min(year_counts) if year_counts else None

    def _spark_svg(values, labels, tips, uid):
        """Smooth (Catmull-Rom) sparkline with: gradient area fill, faint
        horizontal gridlines, a left y-axis (with min/max ticks), an x-axis
        baseline separating the category labels from the plot, point dots and a
        per-point value that appears on hover. Crisp SVG, scales via CSS."""
        n = len(values)
        maxv = max(values) if values and max(values) > 0 else 1
        # "Nice" axis top: round the data max UP to a clean 5-step scale, so the
        # axis reads e.g. 0..25 (step 5) when the real max is 21 — the peak sits
        # below the top tick instead of pinned to it.
        nice_step = next(st for st in (1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 50, 100, 200, 500)
                         if st * 5 >= maxv)
        nice_max = nice_step * 5
        viewW, padL, padR, padTop, chartH, labelH = 520, 32, 14, 12, 86, 18
        totalH = chartH + labelH
        x0p, x1p = padL, viewW - padR
        step = (x1p - x0p) / (n - 1) if n > 1 else 0
        pts = [(x0p + i * step,
                padTop + (1 - v / nice_max) * (chartH - padTop)) for i, v in enumerate(values)]

        def pt(i):
            return pts[min(max(i, 0), n - 1)]
        d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
        for i in range(1, n):
            x0, y0 = pt(i - 2)
            x1, y1 = pt(i - 1)
            x2, y2 = pt(i)
            x3, y3 = pt(i + 1)
            c1x, c1y = x1 + (x2 - x0) / 6, y1 + (y2 - y0) / 6
            c2x, c2y = x2 - (x3 - x1) / 6, y2 - (y3 - y1) / 6
            d += f" C {c1x:.1f} {c1y:.1f} {c2x:.1f} {c2y:.1f} {x2:.1f} {y2:.1f}"
        area = d + f" L {pts[-1][0]:.1f} {chartH} L {pts[0][0]:.1f} {chartH} Z"

        s = [f'<svg class="cal-ig-spark" viewBox="0 0 {viewW} {totalH}" role="img">']
        s.append(f'<defs><linearGradient id="sg-{uid}" x1="0" y1="0" x2="0" y2="1">'
                 '<stop offset="0" stop-color="#79c0ff" stop-opacity="0.28"/>'
                 '<stop offset="1" stop-color="#79c0ff" stop-opacity="0"/>'
                 '</linearGradient></defs>')
        # Horizontal gridlines + y-axis ticks on the 5-step nice scale.
        for k in range(6):                       # 0,1,2,3,4,5 → 0..nice_max
            gy = padTop + (1 - k / 5) * (chartH - padTop)
            if 0 < k < 5:
                s.append(f'<line class="cal-ig-grid" x1="{x0p}" y1="{gy:.1f}" x2="{x1p}" y2="{gy:.1f}"/>')
            s.append(f'<text class="cal-ig-ytick" x="{x0p - 6}" y="{gy + 3:.1f}" '
                     f'text-anchor="end">{nice_step * k}</text>')
        # Vertical minor gridlines — one per category (skip the first, it sits on
        # the y-axis).
        for vx, _vy in pts[1:]:
            s.append(f'<line class="cal-ig-grid cal-ig-grid-v" x1="{vx:.1f}" y1="{padTop}" '
                     f'x2="{vx:.1f}" y2="{chartH}"/>')
        # y-axis (left).
        s.append(f'<line class="cal-ig-axis" x1="{x0p}" y1="{padTop}" x2="{x0p}" y2="{chartH}"/>')
        # area + line.
        s.append(f'<path d="{area}" fill="url(#sg-{uid})"/>')
        s.append(f'<path d="{d}" fill="none" stroke="#58a6ff" stroke-width="2.4" '
                 'stroke-linecap="round" stroke-linejoin="round"/>')
        # x-axis baseline — separates the plot from the category labels below.
        s.append(f'<line class="cal-ig-axis is-base" x1="{x0p}" y1="{chartH}" x2="{x1p}" y2="{chartH}"/>')
        # Points: each in a hover group (wide invisible hit rect → value pops).
        for i, (x, y) in enumerate(pts):
            hx = x - (step / 2 if step else 14)
            hw = step if step else 28
            s.append(f'<g class="cal-ig-pt"><title>{_html.escape(tips[i])}</title>')
            s.append(f'<rect class="cal-ig-hit" x="{hx:.1f}" y="{padTop}" '
                     f'width="{hw:.1f}" height="{chartH - padTop:.1f}"/>')
            s.append(f'<circle class="cal-ig-dot" cx="{x:.1f}" cy="{y:.1f}" '
                     f'fill="#79c0ff" stroke="#0d1117" stroke-width="1.4"/>')
            s.append(f'<text class="cal-ig-pt-val" x="{x:.1f}" y="{y - 8:.1f}" '
                     f'text-anchor="middle">{values[i]}</text>')
            s.append('</g>')
            s.append(f'<text x="{x:.1f}" y="{chartH + 13}" text-anchor="middle" '
                     f'class="cal-ig-spark-lbl">{labels[i]}</text>')
        s.append('</svg>')
        return ''.join(s)

    # Whole (major, e.g. 7.41) vs lettered (sub, e.g. 7.41a) patch counts.
    major_count = sum(1 for p in patches if not _re.search(r'[a-z]$', p['version']))
    sub_count = total_patches - major_count

    ig = ['<div class="cal-infographic">']

    # Lead panel: title + inline key stats (compact, no big chips).
    ig.append('<div class="cal-ig-panel cal-ig-lead">')
    ig.append('<div class="cal-ig-title">Patch cadence</div>')
    ig.append(f'<div class="cal-ig-sub">{min_year} – now</div>')
    ig.append('<div class="cal-ig-statline">'
              f'<span><b>{total_patches}</b> patches:</span>'
              '<span class="cal-ig-rule"></span>'
              f'<span><b class="cal-ig-major">{major_count}</b> major</span>'
              f'<span><b>{sub_count}</b> letter</span>'
              '<span class="cal-ig-rule"></span>'
              f'<span><b>{avg_per_year:.1f}</b> / year</span>'
              f'<span><b>{median_span}</b>d median life</span>'
              '</div>')
    ig.append('</div>')

    # Per-year sparkline (chronological left→right).
    yrs = sorted(year_counts)
    ig.append('<div class="cal-ig-panel">')
    ig.append('<div class="cal-ig-h">Per year</div>')
    ig.append(_spark_svg(
        [year_counts[y] for y in yrs],
        [str(y)[2:] for y in yrs],
        [f"{y}: {year_counts[y]} patch(es)" for y in yrs],
        'yr'))
    ig.append('</div>')

    # Per-month sparkline (all years combined).
    ig.append('<div class="cal-ig-panel">')
    ig.append('<div class="cal-ig-h">Per month</div>')
    ig.append(_spark_svg(
        month_counts,
        [months[mi][0] for mi in range(12)],
        [f"{months[mi]}: {month_counts[mi]} patch(es)" for mi in range(12)],
        'mo'))
    ig.append('</div>')
    ig.append('</div>')  # cal-infographic
    body.append('\n'.join(ig))

    body.append('</div>')  # .calendar

    toggle_script = '''<script>
(function() {
  const cal = document.querySelector('.calendar');
  const compact = document.querySelector('.cal-compact-input');
  if (compact) {
    compact.addEventListener('change', () => {
      cal.classList.remove('mode-full', 'mode-compact');
      cal.classList.add(compact.checked ? 'mode-compact' : 'mode-full');
    });
  }
  const picker = document.querySelector('.cal-year-picker');
  if (picker) {
    const btn  = picker.querySelector('.cal-year-current');
    const menu = picker.querySelector('.cal-year-menu');
    const valEl = picker.querySelector('.cal-year-current-val');
    const opts = [...menu.querySelectorAll('.cal-year-opt')];
    const open  = () => { menu.hidden = false; picker.classList.add('is-open'); btn.setAttribute('aria-expanded', 'true'); };
    const close = () => { menu.hidden = true;  picker.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false'); };
    const selectYear = (year) => {
      valEl.textContent = year;
      opts.forEach(o => {
        const on = o.dataset.year === year;
        o.classList.toggle('is-selected', on);
        o.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      document.querySelectorAll('.cal-year-pane').forEach(p => {
        p.hidden = (p.dataset.year !== year);
      });
    };
    btn.addEventListener('click', e => { e.stopPropagation(); menu.hidden ? open() : close(); });
    opts.forEach(o => o.addEventListener('click', () => { selectYear(o.dataset.year); close(); }));
    document.addEventListener('click', e => { if (!picker.contains(e.target)) close(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  }
  // Row + column cross-highlight on the Full grid. Event-delegated so it
  // works across all year panes (only one is visible at a time).
  document.querySelectorAll('.cal-full-grid').forEach(grid => {
    let activeRow = null, activeCol = null;
    const clear = () => {
      grid.querySelectorAll('.cross-row,.cross-col').forEach(el => {
        el.classList.remove('cross-row', 'cross-col');
      });
      activeRow = activeCol = null;
    };
    grid.addEventListener('mouseover', e => {
      const cell = e.target.closest('[data-day],[data-month]');
      if (!cell || !grid.contains(cell)) return;
      const m = cell.dataset.month, d = cell.dataset.day;
      if (m === activeRow && d === activeCol) return;
      clear();
      activeRow = m; activeCol = d;
      if (m) grid.querySelectorAll(`[data-month="${m}"]`).forEach(
        el => el.classList.add('cross-row'));
      if (d) grid.querySelectorAll(`[data-day="${d}"]`).forEach(
        el => el.classList.add('cross-col'));
    });
    grid.addEventListener('mouseleave', clear);
  });
})();
</script>'''

    cur_v = _current_version()
    cur_date = next((r["date"] for r in RELEASE_HISTORY if r["version"] == cur_v), None)
    nav = _render_top_nav(active="calendar", current_version=cur_v, date=cur_date)
    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<title>SIKLE | Calendar</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={_ASSET_VERSION}">\n'
        '</head>\n<body>\n\n'
        + nav
        + '\n<div class="container calendar-page">\n'
        + '\n'.join(body)
        + '\n</div>\n\n'
        + f'<script src="scripts.js?v={_ASSET_VERSION}"></script>\n'
        + toggle_script + '\n'
        + '</body>\n</html>\n'
    )
    with open('calendar.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  → calendar.html: {len(html):,} bytes")
