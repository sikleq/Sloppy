
// ---- MANA ITEMS: Price min/max filter ----
(function() {
  const table = document.querySelector('.mr-table');
  if (!table) return;
  const minIn = document.getElementById('mr-price-min');
  const maxIn = document.getElementById('mr-price-max');
  const clear = document.getElementById('mr-price-clear');
  if (!minIn || !maxIn) return;
  // Find the Price column index from the header (data-col="cost").
  const headers = [...table.querySelectorAll('thead th')];
  const priceIdx = headers.findIndex(th => th.dataset.col === 'cost');
  if (priceIdx < 0) return;

  function applyFilter() {
    const lo = parseFloat(minIn.value);
    const hi = parseFloat(maxIn.value);
    const hasLo = !isNaN(lo);
    const hasHi = !isNaN(hi);
    // Show the X only when at least one bound is set — otherwise the
    // combo widget reads as a simple "Price from–to" placeholder pair.
    clear.hidden = !(hasLo || hasHi);
    table.querySelectorAll('tbody tr').forEach(tr => {
      const td = tr.children[priceIdx];
      const v = td ? parseFloat(td.dataset.sort) : NaN;
      let keep = true;
      if (!isNaN(v)) {
        if (hasLo && v < lo) keep = false;
        if (hasHi && v > hi) keep = false;
      }
      tr.classList.toggle('mr-filtered-out', !keep);
    });
    // Heatmap re-applies over the new visible set.
    window.dispatchEvent(new CustomEvent('mr:filter-changed'));
  }
  minIn.addEventListener('input', applyFilter);
  maxIn.addEventListener('input', applyFilter);
  clear.addEventListener('click', () => {
    minIn.value = '';
    maxIn.value = '';
    applyFilter();
  });
})();

// ---- MANA ITEMS: name search ----
// Independent of the price/hide-active filters (each uses its own display:none
// class, so any one hiding a row wins). Comma-separated, partial, like the
// dynamics search. Re-fires mr:filter-changed so the heatmap recomputes.
(function() {
  const table = document.querySelector('.mr-table');
  const search = document.getElementById('mr-search');
  if (!table || !search) return;
  const rows = [...table.querySelectorAll('tbody tr')];
  const apply = () => {
    const terms = search.value.toLowerCase().split(',').map(s => s.trim()).filter(Boolean);
    rows.forEach(tr => {
      const name = (tr.querySelector('.mr-name-text')?.textContent || '').toLowerCase();
      const slug = (tr.dataset.slug || '').toLowerCase();
      const hit = !terms.length || terms.some(t => name.includes(t) || slug.includes(t));
      tr.classList.toggle('mr-search-out', !hit);
    });
    window.dispatchEvent(new CustomEvent('mr:filter-changed'));
  };
  search.addEventListener('input', apply);
})();
