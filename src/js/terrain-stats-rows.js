
// ---- TERRAIN STATS: click a row to frame it in gold, like the other table pages; again to clear. Links inside
// (the version, the map square) keep working and don't select. ----
(function() {
  const table = document.querySelector('.ts-table');
  if (!table) return;
  table.addEventListener('click', e => {
    if (e.target.closest('a')) return;
    const tr = e.target.closest('tbody tr');
    if (!tr || !table.contains(tr)) return;
    const was = tr.classList.contains('ts-row-selected');
    table.querySelectorAll('tr.ts-row-selected').forEach(r => r.classList.remove('ts-row-selected'));
    if (!was) tr.classList.add('ts-row-selected');
  });
})();
