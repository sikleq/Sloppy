
// ---- CALENDAR: Patches / Test servers views + the test servers' charts (patch/branch_builds.py, 2026-11-10) ----
// The two tabs swap the calendar and the .tb-panel; #test-servers in the address opens the second. The panel holds the
// Test servers view twice (.tb-view): without the Staging builds that went to the live game as fixes, and with them;
// the "Hide Staging fixes" switch in the calendar's header swaps them. Each view's controls work on that view only.
(function() {
  const panel = document.querySelector('.tb-panel');
  const tabs = [...document.querySelectorAll('.cal-view-tab')];
  if (!panel || !tabs.length) return;
  const cal = document.querySelector('.calendar');

  function show(view) {
    const builds = view === 'test-servers';
    tabs.forEach(t => {
      const on = t.dataset.view === view;
      t.classList.toggle('is-active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    if (cal) cal.hidden = builds;
    panel.hidden = !builds;
  }
  tabs.forEach(t => t.addEventListener('click', () => {
    show(t.dataset.view);
    history.replaceState(null, '', t.dataset.view === 'test-servers' ? '#test-servers' : location.pathname + location.search);
  }));
  if (location.hash === '#test-servers') show('test-servers');
  // A link to #test-servers on this same page (no reload) opens it too
  window.addEventListener('hashchange', () => show(location.hash === '#test-servers' ? 'test-servers' : 'patches'));

  // A card's own switch buttons: one pressed at a time
  function press(btns, btn) {
    btns.forEach(b => {
      const on = b === btn;
      b.classList.toggle('active', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  // ---- the charts' From / To years: helpers ----
  // The page is built with the whole log; each element carries its time (data-t), value (data-v) or counts by year
  // ("2024:3,2025:5"), and this redoes the layout and the scales (the same nice steps as patch/branch_builds.py).
  const LBL = { experimental: 'Experimental', staging: 'Staging' };
  // The same little table as patch/branch_builds.py _count_table: a row per server in its colour
  const countTable = (counts, shown) => '<table class="tb-tip-table">' + shown.map(br =>
    `<tr class="tb-tip-${br}"><td>${LBL[br]}</td><td>${counts[br] || 0}</td></tr>`).join('') + '</table>';
  const NICE = [1, 2, 3, 4, 5, 10, 15, 20, 25, 50, 100, 200, 250, 500, 1000, 2500];
  const nice = m => { const st = NICE.find(s => s * 4 >= m) || Math.ceil(m / 4); return [st, st * 4]; };
  const sumIn = (attr, y0, y1) => (attr || '').split(',').filter(Boolean)
    .reduce((a, p) => { const [y, c] = p.split(':').map(Number); return a + (y >= y0 && y <= y1 ? c : 0); }, 0);
  const DAY = 86400, WEEK = 7 * DAY;
  const jan1 = y => Date.UTC(y, 0, 1) / 1000;
  const monday = t => t - ((Math.floor(t / DAY) + 3) % 7) * DAY;      // 1 Jan 1970 was a Thursday

  function weekly(svg, y0, y1) {
    const hits = [...svg.querySelectorAll('.tb-hit:not(.tb-patch-hit)')];
    if (!svg.dataset.t0) return;
    const r0 = Math.max(monday(jan1(y0)), +svg.dataset.t0), r1 = Math.min(monday(jan1(y1 + 1)), +svg.dataset.t1);
    const pl = +svg.dataset.pl, pw = +svg.dataset.pw, mid = +svg.dataset.mid, half = +svg.dataset.half;
    const single = svg.dataset.series !== 'both';
    const x = t => pl + (t - r0) / (r1 - r0) * pw;
    const colw = WEEK / (r1 - r0) * pw, bar = Math.max(1, colw - 1.5);
    const bars = [...svg.querySelectorAll('.tb-bar')];
    let max = 1;
    bars.forEach(b => { const on = +b.dataset.t >= r0 && +b.dataset.t < r1; b.style.display = on ? '' : 'none'; if (on) max = Math.max(max, +b.dataset.v); });
    const top = nice(max)[1], step = nice(max)[0];
    bars.forEach(b => {
      if (b.style.display) return;
      const h = b.dataset.v / top * half;
      b.setAttribute('x', x(+b.dataset.t) + (colw - bar) / 2);
      b.setAttribute('width', bar);
      b.setAttribute('height', h);
      b.setAttribute('y', single || b.classList.contains('tb-experimental') ? mid - h : mid);
    });
    hits.forEach(r => { const t = +r.dataset.t, on = t >= r0 && t < r1; r.style.display = on ? '' : 'none'; if (on) { r.setAttribute('x', x(t)); r.setAttribute('width', colw); } });
    // The bars' numbers once a week's column is BAR_VALUE_MIN_COL px or wider (patch/branch_builds.py): written here,
    // not in the page, so 13 years of weeks stay light
    svg.querySelectorAll('text.tb-bar-val').forEach(v => v.remove());
    if (colw >= 14) {
      const NS = 'http://www.w3.org/2000/svg';
      bars.forEach(b => {
        if (b.style.display) return;
        const t = +b.dataset.t, h = b.dataset.v / top * half, below = !single && b.classList.contains('tb-staging');
        const v = document.createElementNS(NS, 'text');
        v.setAttribute('class', 'tb-bar-val ' + (b.classList.contains('tb-staging') ? 'tb-staging' : 'tb-experimental'));
        v.setAttribute('x', x(t) + colw / 2);
        v.setAttribute('y', below ? mid + h + 11 : mid - h - 3);
        v.setAttribute('text-anchor', 'middle');
        v.textContent = b.dataset.v;
        svg.appendChild(v);
      });
    }
    svg.querySelectorAll('.tb-ytick[data-k]').forEach(tk => { tk.textContent = step * tk.dataset.k; });
    // Points in time: month marks, patch lines and labels, their hover strips, "now"
    svg.querySelectorAll('line[data-t], text[data-t]:not(.is-start), .tb-patch-hit').forEach(el => {
      const t = +el.dataset.t, on = t >= r0 && t <= r1;
      el.style.display = on ? '' : 'none';
      if (!on) return;
      if (el.tagName === 'line') { el.setAttribute('x1', x(t)); el.setAttribute('x2', x(t)); }
      else el.setAttribute('x', el.tagName === 'text' ? x(t) : x(t) - 4);
      // The start label owns the axis's first START_LABEL_ROOM px (patch/branch_builds.py)
      if (el.classList.contains('cal-ig-spark-lbl') && x(t) - pl < 64) el.style.display = 'none';
    });
    // A year whose label gave way goes on the next shown month ("Apr 2022"); the other months keep their bare name
    let carry = null;
    [...svg.querySelectorAll('text.cal-ig-spark-lbl[data-t]:not(.is-start)')].sort((a, b) => a.dataset.t - b.dataset.t).forEach(el => {
      const year = new Date(el.dataset.t * 1000).getUTCFullYear();
      const isYear = el.classList.contains('is-year'), hidden = el.style.display === 'none';
      if (!isYear) el.textContent = el.dataset.lab + (carry && !hidden ? ' ' + carry : '');
      if (!hidden) carry = null;
      else if (isYear && +el.dataset.t >= r0) carry = year;
    });
    const start = svg.querySelector('text.is-start');
    if (start) {
      const d = new Date(r0 * 1000);
      start.textContent = d.toLocaleString('en-GB', { month: 'short', timeZone: 'UTC' }) + ' ' + d.getUTCFullYear();
    }
  }

  function whenChart(svg, y0, y1) {
    const pt = +svg.dataset.pt, ch = +svg.dataset.ch;
    const shown = svg.dataset.series === 'both' ? ['experimental', 'staging'] : [svg.dataset.series];
    const key = br => 'c' + br[0].toUpperCase() + br.slice(1);
    const hits = [...svg.querySelectorAll('.tb-hit')];
    const vals = hits.map(h => Object.fromEntries(shown.map(br => [br, sumIn(h.dataset[key(br)], y0, y1)])));
    const [step, top] = nice(Math.max(1, ...vals.map(v => shown.reduce((a, br) => a + v[br], 0))));
    hits.forEach((h, i) => {
      let y = ch;
      shown.forEach(br => {
        const r = svg.querySelector(`.tb-bar[data-i="${h.dataset.i}"][data-br="${br}"]`);
        const hh = vals[i][br] / top * (ch - pt);
        y -= hh;
        if (r) { r.setAttribute('y', y); r.setAttribute('height', hh); }
      });
      h.setAttribute('data-tooltip', `<b>${h.dataset.name}</b>` + countTable(vals[i], shown));
    });
    svg.querySelectorAll('.cal-ig-ytick[data-k]').forEach(tk => { tk.textContent = step * tk.dataset.k; });
  }

  // ---- one Test servers view: its switches, its patch lighting, its charts' years ----
  // The medians of the whole patches shown, as medians() and fmt_short in branch_builds.py: the time after the last
  // Staging builds over every patch, the run-ups only over patches whose whole run-up is in the log (no data-partial)
  const WHOLE_ONLY = { lag2: false, lag: false, stg1: true, stg: true, lead: true };
  function median(xs) {
    const s = xs.slice().sort((a, b) => a - b), m = s.length >> 1;
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  }
  function fmtShort(sec) {
    const h = Math.max(Math.floor(sec / 3600), 0);
    return h >= 48 ? `${Math.floor(h / 24)} d` : `${h} h`;
  }
  function medianStripOf(view) {
    return (y0, y1, toNow) => {
      const rows = [...view.querySelectorAll('.tb-plist[data-lag="major"] .tb-pr[data-year]')]
        .filter(r => +r.dataset.year >= y0 && +r.dataset.year <= y1);
      view.querySelectorAll('.tb-answer [data-median]').forEach(panel => {
        const key = panel.dataset.median;
        const xs = rows.filter(r => r.dataset[key] !== undefined && !(WHOLE_ONLY[key] && r.dataset.partial))
          .map(r => +r.dataset[key]);
        panel.querySelector('b').textContent = xs.length ? fmtShort(median(xs)) : '–';
      });
      const since = view.querySelector('.tb-ig-since');
      if (since) since.textContent = toNow ? `${y0} to now` : (y0 === y1 ? `${y0}` : `${y0} to ${y1}`);
    };
  }

  function initView(view) {
    const medianStrip = medianStripOf(view);
    // Both / Experimental / Staging: each card shows its chart of that name (weekly, hours, weekdays)
    view.querySelectorAll('.tb-card').forEach(card => {
      const btns = [...card.querySelectorAll('.tb-series-btn')];
      btns.forEach(btn => btn.addEventListener('click', () => {
        press(btns, btn);
        // An <svg> has no .hidden property: the attribute itself must change
        card.querySelectorAll('svg[data-series]').forEach(svg => svg.toggleAttribute('hidden', svg.dataset.series !== btn.dataset.series));
      }));
    });
    // Each patch: whole patches (the default) or every patch
    const lagBtns = [...view.querySelectorAll('.tb-lag-btn')];
    lagBtns.forEach(btn => btn.addEventListener('click', () => {
      press(lagBtns, btn);
      view.querySelectorAll('.tb-plist[data-lag]').forEach(l => l.toggleAttribute('hidden', l.dataset.lag !== btn.dataset.lag));
    }));

    // Pointing at a patch (its line, or its row in "Each patch") lights the weeks that led to it. A row of the
    // whole-patches list lights by data-major: there a whole patch's run-up includes the letter patches before it.
    const charts = [...view.querySelectorAll('.tb-weekly')];
    let lit = null;
    function light(patch, key) {
      const id = patch ? key + ':' + patch : null;
      if (id === lit) return;
      lit = id;
      charts.forEach(svg => {
        svg.classList.toggle('is-focus', !!patch);
        svg.querySelectorAll('.tb-bar').forEach(r => r.classList.toggle('is-on', !!patch && r.dataset[key] === patch));
        svg.querySelectorAll('.tb-patch-hit').forEach(r => r.classList.toggle('is-on', !!patch && r.dataset.patch === patch));
      });
      view.querySelectorAll('.tb-pr[data-patch]').forEach(r => r.classList.toggle('is-on', !!patch && r.dataset.patch === patch));
    }
    view.addEventListener('mouseover', e => {
      // A day or week keeps only its counts (data-c "experimental,staging"); its tooltip table is written on the first
      // hover, before tooltips.js (listening on the document) reads it
      const lazy = e.target.closest('[data-c]');
      if (lazy && !lazy.dataset.tooltip) {
        const [ce, cs] = lazy.dataset.c.split(',').map(Number);
        const shown = lazy.dataset.show ? [lazy.dataset.show] : ['experimental', 'staging'];
        lazy.dataset.tooltip = (lazy.dataset.title ? `<b>${lazy.dataset.title}</b>` : '')
          + countTable({ experimental: ce, staging: cs }, shown);
      }
      const t = e.target.closest('.tb-patch-hit, .tb-pr[data-patch]');
      const major = t && t.closest('.tb-plist[data-lag="major"]');
      light(t ? t.dataset.patch : null, major ? 'major' : 'patch');
    });
    view.addEventListener('mouseleave', () => light(null));

    // From / To cover everything under the calendar, which has its own year (owner 2026-11-10): the medians strip,
    // the Each patch rows and the charts
    const yFrom = view.querySelector('.tb-year-from'), yTo = view.querySelector('.tb-year-to');
    if (!yFrom || !yTo) return;
    function applyYears() {
      let y0 = +yFrom.value, y1 = +yTo.value;
      if (y0 > y1) { [y0, y1] = [y1, y0]; yFrom.value = y0; yTo.value = y1; }
      view.querySelectorAll('.tb-plist').forEach(list => {
        const rows = [...list.querySelectorAll('.tb-pr[data-year]')];
        rows.forEach(r => { r.hidden = +r.dataset.year < y0 || +r.dataset.year > y1; });
        const none = list.querySelector('.tb-plist-none');
        if (none) none.hidden = rows.some(r => !r.hidden);
      });
      medianStrip(y0, y1, y1 === +yTo.options[yTo.options.length - 1].value);
      view.querySelectorAll('svg.tb-weekly').forEach(svg => weekly(svg, y0, y1));
      view.querySelectorAll('svg.tb-bars').forEach(svg => whenChart(svg, y0, y1));
    }
    yFrom.addEventListener('change', applyYears);
    yTo.addEventListener('change', applyYears);
    view.querySelectorAll('svg.tb-weekly').forEach(svg => weekly(svg, +yFrom.value, +yTo.value));   // the bars' numbers
  }
  const views = [...panel.querySelectorAll('.tb-view')];
  views.forEach(initView);

  // ---- Hide Staging fixes: swap the two views, keeping the calendar's year and the charts' years ----
  panel.querySelectorAll('.tb-fix-input').forEach(input => input.addEventListener('change', () => {
    const from = views.find(v => !v.hidden), to = views.find(v => v.dataset.fix === (input.checked ? 'hide' : 'all'));
    if (!from || !to || from === to) return;
    views.forEach(v => { v.hidden = v !== to; });
    panel.querySelectorAll('.tb-fix-input').forEach(i => { i.checked = input.checked; });
    const year = from.querySelector('.cal-year-current-val');
    const opt = year && to.querySelector(`.cal-year-opt[data-year="${year.textContent}"]`);
    if (opt) opt.click();
    ['.tb-year-from', '.tb-year-to'].forEach(sel => {
      const a = from.querySelector(sel), b = to.querySelector(sel);
      if (a && b && a.value !== b.value) { b.value = a.value; b.dispatchEvent(new Event('change')); }
    });
  }));
})();
