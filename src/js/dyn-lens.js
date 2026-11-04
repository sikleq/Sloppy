
// ---- DYNAMICS MATRICES: one hover "lens" instead of popping the cells (owner 2026-09-26) ----
// Scaling the hovered cell itself either jumped (no transition) or repainted every passing cell
// (with one). Here the cells never change: a single fixed lens holding a copy of the hovered pill
// grows over it and glides from cell to cell — one composited layer, transform/opacity only.
(function() {
  const table = document.querySelector('.heroes-dyn-table');
  if (!table) return;
  const lens = document.createElement('div');
  lens.className = 'dyn-lens';
  lens.setAttribute('aria-hidden', 'true');
  document.body.appendChild(lens);
  let cur = null;
  let shown = false;
  function place(wrap, scale) {
    const r = wrap.getBoundingClientRect();
    lens.style.transform = `translate(${r.left}px, ${r.top}px) scale(${scale})`;
  }
  function show(wrap) {
    const cell = wrap.querySelector('.dyn-cell');
    if (!cell) return;
    lens.classList.toggle('current', wrap.classList.contains('current'));
    lens.replaceChildren(cell.cloneNode(true));
    if (!shown) {                       // appear on the cell at its own size, then grow
      lens.classList.add('no-anim');
      place(wrap, 1);
      void lens.offsetWidth;
      lens.classList.remove('no-anim');
      lens.classList.add('is-on');
      shown = true;
    }
    place(wrap, 2.5);
  }
  function hide() {
    if (!shown) return;
    shown = false;
    cur = null;
    lens.classList.remove('is-on');
  }
  table.addEventListener('mouseover', e => {
    const wrap = e.target.closest('.dyn-cell-wrap');
    if (wrap === cur) return;
    const ok = wrap && !wrap.matches('.empty, .bn-empty, .w-line');
    if (!ok) { hide(); return; }
    cur = wrap;
    show(wrap);
  }, { passive: true });
  table.addEventListener('mouseleave', hide);
  document.addEventListener('scroll', hide, { capture: true, passive: true });
  window.addEventListener('resize', hide);
})();
