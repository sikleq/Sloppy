
// ---- MANA REGEN TABLE: simple sortable ----
// Plain sort by data-sort attribute on each <td>. No row grouping / level
// collapse / ability merging — the table is flat, so the existing creeps
// sort would over-engineer it.
(function() {
  const tables = document.querySelectorAll('.mr-table');
  tables.forEach(table => {
    const tbody = table.querySelector('tbody');
    const headers = [...table.querySelectorAll('thead th.sortable')];
    if (!tbody || !headers.length) return;

    function cellVal(tr, colIdx) {
      const td = tr.children[colIdx];
      if (!td) return null;
      if (td.dataset.sort !== undefined && td.dataset.sort !== '') {
        const n = parseFloat(td.dataset.sort);
        return isNaN(n) ? td.dataset.sort.toLowerCase() : n;
      }
      const t = td.textContent.trim();
      if (!t) return null;
      const m = t.replace(',', '.').match(/-?\d+(?:\.\d+)?/);
      return m ? parseFloat(m[0]) : t.toLowerCase();
    }

    // Snapshot the server-rendered order so the neutral state can restore it.
    const originalOrder = [...tbody.querySelectorAll('tr')];
    // The default-sorted column is marked .sort-desc in the markup, so the
    // 3-state cycle starts already on that column at "descending".
    let sortCol = headers.findIndex(th =>
      th.classList.contains('sort-asc') || th.classList.contains('sort-desc'));
    if (sortCol === -1) sortCol = null;
    // sortState: 0 = neutral, 1 = descending, 2 = ascending.
    let sortState = sortCol !== null
      ? (headers[sortCol].classList.contains('sort-asc') ? 2 : 1)
      : 0;

    function sortBy(colIdx, dir) {
      const rows = [...tbody.querySelectorAll('tr')];
      rows.sort((a, b) => {
        const va = cellVal(a, colIdx);
        const vb = cellVal(b, colIdx);
        if (va == null && vb == null) return 0;
        if (va == null) return 1;          // empties sink
        if (vb == null) return -1;
        if (typeof va === 'number' && typeof vb === 'number') {
          return dir === 'asc' ? va - vb : vb - va;
        }
        const sa = String(va), sb = String(vb);
        return dir === 'asc' ? sa.localeCompare(sb) : sb.localeCompare(sa);
      });
      rows.forEach(r => tbody.appendChild(r));
    }

    headers.forEach((th, i) => {
      th.addEventListener('click', () => {
        // 3-state cycle per header: neutral → descending → ascending → neutral.
        if (sortCol === i) sortState = (sortState + 1) % 3;
        else { sortCol = i; sortState = 1; }   // first click = descending
        headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
        if (sortState === 0) {
          // Neutral — restore the original server-rendered order.
          sortCol = null;
          originalOrder.forEach(r => tbody.appendChild(r));
        } else {
          const dir = sortState === 1 ? 'desc' : 'asc';
          th.classList.add(dir === 'asc' ? 'sort-asc' : 'sort-desc');
          sortBy(i, dir);
        }
        // Heatmap follows the new row order / visible set.
        window.dispatchEvent(new CustomEvent('mr:filter-changed'));
      });
    });
  });
})();

// ---- MANA ITEMS: "Hide active" toggle ----
// Hides every <tr.mr-active-row> when checked. Heatmap recomputes via the
// shared `mr:filter-changed` channel so column gradients reflect the
// currently-visible row set.
(function() {
  const toggle = document.getElementById('mr-hide-active');
  if (!toggle) return;
  const apply = () => {
    document.querySelectorAll('.mr-active-row').forEach(tr => {
      tr.classList.toggle('mr-hide-active', toggle.checked);
    });
    window.dispatchEvent(new CustomEvent('mr:filter-changed'));
  };
  toggle.addEventListener('change', apply);
})();

// ---- MANA ITEMS: per-column conditional formatting ----
// For every column whose <th data-direction> is set, scan all visible cells
// and paint a faint pastel gradient — green at the "good" end, red at the
// "bad" end. Pure visual aid; doesn't alter values or sort order.
(function() {
  const table = document.querySelector('.mr-table');
  if (!table) return;
  const headRow = table.querySelector('thead tr.col-row') || table.querySelector('thead tr');
  const headers = headRow ? [...headRow.querySelectorAll('th')] : [];

  function applyHeatmap() {
    // Respect the on-page Heatmap switch — when off, all cells stay flat.
    // (The toggle IIFE separately strips any inline backgrounds we set.)
    const toggle = document.getElementById('mr-heatmap-toggle');
    if (toggle && !toggle.checked) return;
    const rows = [...table.querySelectorAll('tbody tr')];
    headers.forEach((th, colIdx) => {
      const direction = th.dataset.direction;
      if (!direction) return;
      // Gather numeric data-sort values for visible non-dash cells. Rows
      // hidden by the price filter (.mr-filtered-out) are also excluded so
      // colours always reflect the current visible set.
      const cells = [];
      rows.forEach(tr => {
        if (tr.hasAttribute('hidden')) return;
        if (tr.classList.contains('mr-filtered-out')) return;
        if (tr.classList.contains('mr-search-out')) return;
        if (tr.classList.contains('mr-attack-out')) return;
        if (tr.classList.contains('mr-hide-active')) return;
        const td = tr.children[colIdx];
        if (!td) return;
        td.style.backgroundColor = '';        // reset previous paint
        if (td.querySelector('.ua-dash')) return;
        const v = parseFloat(td.dataset.sort);
        if (isNaN(v) || v === 0) return;
        cells.push({ td, v });
      });
      if (cells.length < 2) return;
      // Rank-percentile mapping: each cell's colour is decided by its rank
      // within the column, not its raw value. Eliminates the previous problem
      // where a single outlier (Dagon 5's 25.5k cost-per-regen) compressed
      // every other value into the same green band — now mid-tier rows get
      // mid-tier colours regardless of how far the worst outlier sits.
      // Rank over UNIQUE values so ties share one colour — otherwise a
      // column of identical numbers (hero Vision: 1800 everywhere) painted
      // a meaningless green→red gradient purely by row order.
      const uniq = [...new Set(cells.map(c => c.v))].sort((a, b) => a - b);
      if (uniq.length < 2) {
        cells.forEach(c => { c.td.style.backgroundColor = ''; });
        return;
      }
      const rankMap = new Map(uniq.map((v, i) => [v, i]));
      const last = uniq.length - 1;
      cells.forEach(c => {
        let t = rankMap.get(c.v) / last;   // [0, 1] by unique-value rank
        if (direction === 'lower') t = 1 - t;
        // Olive (better) ↔ brick (worse), both pulled toward yellow so they sit with the
        // site's gold; the middle 20 % of ranks stays uncoloured and the tint grows toward
        // the ends (max alpha 0.32). The old red→amber→green put a yellow band mid-table.
        const d = t - 0.5;
        const alpha = (Math.max(0, Math.abs(d) - 0.1) / 0.4 * 0.32).toFixed(3);
        c.td.style.backgroundColor = alpha === '0.000' ? ''
          : (d > 0 ? `rgba(150, 170, 70, ${alpha})` : `rgba(190, 85, 55, ${alpha})`);
      });
    });
  }
  applyHeatmap();
  // Filter / sort events from sibling IIFEs trigger a recompute.
  window.addEventListener('mr:filter-changed', applyHeatmap);
})();

// ---- MANA ITEMS: click row to highlight (yellow). Click again to deselect. ----
(function() {
  const table = document.querySelector('.mr-table');
  if (!table) return;
  table.addEventListener('click', e => {
    const tr = e.target.closest('tbody tr');
    if (!tr || !table.contains(tr)) return;
    const was = tr.classList.contains('mr-row-selected');
    table.querySelectorAll('tr.mr-row-selected').forEach(r =>
      r.classList.remove('mr-row-selected'));
    if (!was) tr.classList.add('mr-row-selected');
  });
})();
