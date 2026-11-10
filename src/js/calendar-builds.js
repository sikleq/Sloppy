
// ---- CALENDAR: Patches / Test servers views + the test servers' tables (patch/branch_builds.py, 2026-11-10) ----
// The two tabs swap the calendar and the .tb-panel; #test-servers in the address opens the second. Table headers sort in
// three steps: the column's own first direction (data-first), the other way, back to the built order.
(function() {
  const panel = document.querySelector('.tb-panel');
  const tabs = [...document.querySelectorAll('.cal-view-tab')];
  if (!panel || !tabs.length) return;
  const cal = document.querySelector('.calendar');
  let scrolled = false;

  function show(view) {
    const builds = view === 'test-servers';
    tabs.forEach(t => {
      const on = t.dataset.view === view;
      t.classList.toggle('is-active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    if (cal) cal.hidden = builds;
    panel.hidden = !builds;
    if (builds && !scrolled) {
      // The timeline opens on its newest end: today and the coming patch
      const box = panel.querySelector('.tb-timeline-scroll');
      if (box) box.scrollLeft = box.scrollWidth;
      scrolled = true;
    }
  }
  tabs.forEach(t => t.addEventListener('click', () => {
    show(t.dataset.view);
    history.replaceState(null, '', t.dataset.view === 'test-servers' ? '#test-servers' : location.pathname + location.search);
  }));
  if (location.hash === '#test-servers') show('test-servers');

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
})();
