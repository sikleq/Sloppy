
// ---- CALENDAR: Patches / Test servers views + the test servers' tables (patch/branch_builds.py, 2026-11-10) ----
// The two tabs swap the calendar and the .tb-panel; #test-servers in the address opens the second. Table headers sort in
// three steps: the column's own first direction (data-first), the other way, back to the built order.
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

  // A card's own switch buttons: one pressed at a time
  function press(btns, btn) {
    btns.forEach(b => {
      const on = b === btn;
      b.classList.toggle('active', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }
  // Both / Experimental / Staging: each card shows its chart of that name (weekly, hours, weekdays)
  panel.querySelectorAll('.tb-card').forEach(card => {
    const btns = [...card.querySelectorAll('.tb-series-btn')];
    btns.forEach(btn => btn.addEventListener('click', () => {
      press(btns, btn);
      // An <svg> has no .hidden property: the attribute itself must change
      card.querySelectorAll('svg[data-series]').forEach(svg => svg.toggleAttribute('hidden', svg.dataset.series !== btn.dataset.series));
    }));
  });
  // Before each patch: the list of every patch, or of whole patches only
  const lagBtns = [...panel.querySelectorAll('.tb-lag-btn')];
  lagBtns.forEach(btn => btn.addEventListener('click', () => {
    press(lagBtns, btn);
    panel.querySelectorAll('.tb-lag[data-lag]').forEach(l => l.toggleAttribute('hidden', l.dataset.lag !== btn.dataset.lag));
  }));

  // Pointing at a patch (its line, or its row in "Before each patch") lights the weeks that led to it. A row of the
  // whole-patches list lights by data-major: there a whole patch's run-up includes the letter patches before it.
  const charts = [...panel.querySelectorAll('.tb-weekly')];
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
    panel.querySelectorAll('.tb-lag-row[data-patch]').forEach(r => r.classList.toggle('is-on', !!patch && r.dataset.patch === patch));
  }
  panel.addEventListener('mouseover', e => {
    const t = e.target.closest('.tb-patch-hit, .tb-lag-row[data-patch]');
    const major = t && t.closest('.tb-lag[data-lag="major"]');
    light(t ? t.dataset.patch : null, major ? 'major' : 'patch');
  });
  panel.addEventListener('mouseleave', () => light(null));

  panel.querySelectorAll('.tb-table').forEach(table => {
    const body = table.tBodies[0];
    const rows = [...body.rows];
    rows.forEach((r, i) => { r.dataset.order = i; });
    const heads = [...table.querySelectorAll('th[data-sort]')];
    heads.forEach(th => th.addEventListener('click', () => {
      const first = th.dataset.first || 'desc';
      const now = th.classList.contains('sort-desc') ? 'desc' : th.classList.contains('sort-asc') ? 'asc' : '';
      const next = !now ? first : now === first ? (first === 'desc' ? 'asc' : 'desc') : '';
      heads.forEach(h => h.classList.remove('sort-desc', 'sort-asc'));
      const col = +th.dataset.sort;
      let sorted = rows.slice();
      if (next) {
        th.classList.add('sort-' + next);
        const val = r => {
          const v = r.cells[col].dataset.v;
          return v === '' ? null : (isNaN(+v) ? v : +v);
        };
        sorted.sort((a, b) => {
          const x = val(a), y = val(b);
          if (x === null || y === null) return (x === null) - (y === null);   // empty cells last both ways
          const c = x < y ? -1 : x > y ? 1 : 0;
          return next === 'asc' ? c : -c;
        });
      } else {
        sorted.sort((a, b) => a.dataset.order - b.dataset.order);
      }
      sorted.forEach(r => body.appendChild(r));
    }));
  });

  // ---- From / To years: every chart, tile, bar and row of the tab shows only those years ----
  // The page is built with the whole log; each element carries its time (data-t), value (data-v) or counts by year
  // ("2024:3,2025:5"), and this redoes the layout and the scales (the same nice steps as patch/branch_builds.py).
  const yFrom = panel.querySelector('.tb-year-from'), yTo = panel.querySelector('.tb-year-to');
  if (!yFrom || !yTo) return;
  const LBL = { experimental: 'Experimental', staging: 'Staging' };
  const NICE = [1, 2, 3, 4, 5, 10, 15, 20, 25, 50, 100, 200];
  const nice = m => { const st = NICE.find(s => s * 4 >= m) || Math.ceil(m / 4); return [st, st * 4]; };
  const span = s => { const h = Math.floor(s / 3600), d = Math.floor(h / 24); return d ? `${d} d ${h % 24} h` : `${h} h`; };
  const sumIn = (attr, y0, y1) => (attr || '').split(',').filter(Boolean)
    .reduce((a, p) => { const [y, c] = p.split(':').map(Number); return a + (y >= y0 && y <= y1 ? c : 0); }, 0);
  const DAY = 86400, WEEK = 7 * DAY;
  const jan1 = y => Date.UTC(y, 0, 1) / 1000;
  const monday = t => t - ((Math.floor(t / DAY) + 3) % 7) * DAY;      // 1 Jan 1970 was a Thursday
  const median = a => { if (!a.length) return null; a.sort((x, y) => x - y); const m = a.length >> 1; return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2; };

  function weekly(svg, y0, y1) {
    const hits = [...svg.querySelectorAll('.tb-hit:not(.tb-patch-hit)')];
    if (!hits.length) return;
    const weeks = hits.map(h => +h.dataset.t);
    const r0 = Math.max(monday(jan1(y0)), Math.min(...weeks)), r1 = Math.min(monday(jan1(y1 + 1)), Math.max(...weeks) + WEEK);
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
      h.setAttribute('data-tooltip', `<b>${h.dataset.name}</b>` + shown.map(br => `<br>${LBL[br]}: ${vals[i][br]}`).join(''));
    });
    svg.querySelectorAll('.cal-ig-ytick[data-k]').forEach(tk => { tk.textContent = step * tk.dataset.k; });
  }

  const tiles = [...panel.querySelectorAll('.tb-tile')];
  tiles.forEach(t => { t.dataset.caption = t.querySelector('span').textContent; });
  function applyYears() {
    let y0 = +yFrom.value, y1 = +yTo.value;
    if (y0 > y1) { [y0, y1] = [y1, y0]; yFrom.value = y0; yTo.value = y1; }
    const all = y0 === +yFrom.options[0].value && y1 === +yTo.options[yTo.options.length - 1].value;
    const inYears = y => +y >= y0 && +y <= y1;
    panel.querySelectorAll('svg.tb-weekly').forEach(svg => weekly(svg, y0, y1));
    panel.querySelectorAll('svg.tb-bars').forEach(svg => whenChart(svg, y0, y1));
    panel.querySelectorAll('tr[data-year], .tb-lag-row[data-year]').forEach(r => { r.hidden = !inYears(r.dataset.year); });
    panel.querySelectorAll('.tb-lag[data-lag]').forEach(list => {
      const rows = [...list.querySelectorAll('.tb-lag-row[data-year]')].filter(r => !r.hidden);
      const maxLead = Math.max(1, ...rows.map(r => +(r.dataset.lead || 0)));
      rows.forEach(r => {
        const b = r.querySelector('.tb-lag-bar.tb-experimental');
        if (b && r.dataset.lead) b.style.setProperty('--p', Math.min(r.dataset.lead / maxLead, 1).toFixed(3));
      });
    });
    const rows = [...panel.querySelectorAll('.tb-lag[data-lag="all"] .tb-lag-row[data-year]')].filter(r => !r.hidden);
    const years = y0 === y1 ? `in ${y0}` : `in ${y0} to ${y1}`;
    tiles.forEach(t => {
      const b = t.querySelector('b'), cap = t.querySelector('span');
      if (t.dataset.count !== undefined) {
        b.textContent = sumIn(t.dataset.count, y0, y1);
        cap.textContent = all ? t.dataset.caption : `${t.dataset.what} ${years}`;
      } else if (t.dataset.median) {
        const m = t.dataset.median === 'lead'
          ? median(rows.filter(r => r.dataset.lead && !r.dataset.partial).map(r => +r.dataset.lead))
          : median(rows.filter(r => r.dataset.lag).map(r => +r.dataset.lag));
        b.textContent = m === null ? '–' : span(m);
      }
    });
  }
  yFrom.addEventListener('change', applyYears);
  yTo.addEventListener('change', applyYears);
})();
