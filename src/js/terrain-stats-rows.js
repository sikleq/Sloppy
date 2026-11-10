
// ---- TERRAIN STATS: click a row to frame it in gold, like the other table pages; again to clear. Links inside
// (the version, the map square) keep working and don't select. ----
(function() {
  const table = document.querySelector('.ts-table');
  if (!table) return;
  // the Map square opens its map over this page, not on Oldgrowth (owner 2026-11-08: "пусть открывается карта на этой же
  // странице"); Esc or a click closes it — the .tshot-lightbox of the terrain pictures
  let box = null;
  function lightbox() {
    if (box) return box;
    box = document.createElement('div');
    box.className = 'tshot-lightbox';
    box.innerHTML = '<img alt="">';
    box.addEventListener('click', () => box.classList.remove('is-open'));
    document.addEventListener('keydown', ev => {
      if (ev.key === 'Escape' && box.classList.contains('is-open')) box.classList.remove('is-open');
    });
    document.body.appendChild(box);
    return box;
  }
  table.addEventListener('click', e => {
    const thumb = e.target.closest('a.ts-thumb');
    if (thumb) {
      e.preventDefault();
      const b = lightbox();
      b.querySelector('img').src = thumb.href;
      b.querySelector('img').alt = thumb.getAttribute('aria-label') || '';
      b.classList.add('is-open');
      return;
    }
    if (e.target.closest('a')) return;
    const tr = e.target.closest('tbody tr');
    if (!tr || !table.contains(tr)) return;
    const was = tr.classList.contains('ts-row-selected');
    table.querySelectorAll('tr.ts-row-selected').forEach(r => r.classList.remove('ts-row-selected'));
    if (!was) tr.classList.add('ts-row-selected');
  });
})();
