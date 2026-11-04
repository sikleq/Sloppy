
// ---- MANA ITEMS: Heatmap on/off toggle + recompute on filter change ----
(function() {
  const table = document.querySelector('.mr-table');
  const toggle = document.getElementById('mr-heatmap-toggle');
  if (!table || !toggle) return;
  function applyOrClear() {
    if (toggle.checked) {
      // Recompute by dispatching a synthetic event the heatmap IIFE
      // listens to. (The heatmap IIFE re-runs its applyHeatmap each
      // time a filter/sort changes — we route through it here too.)
      window.dispatchEvent(new CustomEvent('mr:filter-changed'));
    } else {
      // Strip all backgroundColor inline styles set by the heatmap.
      table.querySelectorAll('tbody td').forEach(td => {
        td.style.backgroundColor = '';
      });
    }
  }
  toggle.addEventListener('change', applyOrClear);
})();
