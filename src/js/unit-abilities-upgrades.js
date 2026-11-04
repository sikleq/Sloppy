
// ---- UNIT ABILITIES: collapsed upgrade cells ("40…26") expand on click into a
// floating popover with the full per-tier list. Fixed-positioned, clamped to the
// viewport, so the column width never changes. ----
(function() {
  const table = document.querySelector('.unit-abilities-table');
  if (!table) return;
  let pop = null, openBtn = null;
  function ensurePop() {
    if (!pop) {
      pop = document.createElement('div');
      pop.className = 'lvl-popover';
      pop.setAttribute('aria-hidden', 'true');
      document.body.appendChild(pop);
    }
    return pop;
  }
  function close() {
    if (pop) pop.classList.remove('show');
    if (openBtn) { openBtn.setAttribute('aria-expanded', 'false'); openBtn = null; }
  }
  function open(btn) {
    const p = ensurePop();
    p.textContent = btn.dataset.full || btn.textContent;
    p.classList.add('show');
    const r = btn.getBoundingClientRect();
    const pr = p.getBoundingClientRect();
    let left = r.left + r.width / 2 - pr.width / 2;
    left = Math.max(6, Math.min(left, window.innerWidth - pr.width - 6));
    let top = r.top - pr.height - 6;            // prefer above
    if (top < 6) top = r.bottom + 6;            // flip below if no room
    p.style.left = left + 'px';
    p.style.top = top + 'px';
    btn.setAttribute('aria-expanded', 'true');
    openBtn = btn;
  }
  table.addEventListener('click', (e) => {
    const btn = e.target.closest('.lvl-toggle');
    if (!btn) return;
    e.preventDefault();
    if (openBtn === btn) close(); else { close(); open(btn); }
  });
  document.addEventListener('click', (e) => {
    if (openBtn && !e.target.closest('.lvl-toggle')) close();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
  // The table scrolls inside its own box → close on any scroll so the popover
  // never detaches from its cell.
  window.addEventListener('scroll', close, true);
  window.addEventListener('resize', close);
})();
