
// ---- Big Dynamics matrices: skip rendering off-screen rows ----
// The Hero / Item Dynamics tables are enormous (16k-44k nodes). content-visibility
// lets the browser lay out and paint only the rows near the viewport. Column
// widths are pinned first (on the always-rendered header cells) so auto
// table-layout cannot reflow them as off-screen rows are skipped.
(function() {
  const table = document.querySelector('.heroes-dyn-table');
  if (!table) return;
  try { if (!CSS || !CSS.supports || !CSS.supports('content-visibility', 'auto')) return; } catch (e) { return; }
  function pin() {
    // Freeze the current (fully-rendered) column widths onto the header cells so
    // they hold once rows start recycling. Every leaf column has a header cell in
    // the col-row; the identity column's header cell carries data-col="name".
    const heads = table.querySelectorAll('thead tr.col-row > *, thead [data-col="name"]');
    heads.forEach(function(h) {
      const w = Math.round(h.getBoundingClientRect().width);
      if (w > 0) { h.style.minWidth = w + 'px'; h.style.maxWidth = w + 'px'; }
    });
    table.style.width = Math.round(table.getBoundingClientRect().width) + 'px';
    table.classList.add('cv-rows');
  }
  function run() { pin(); }
  if (document.readyState === 'complete') setTimeout(run, 60);
  else window.addEventListener('load', function() { setTimeout(run, 60); });
})();
