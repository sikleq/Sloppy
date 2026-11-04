
// ---------------------------------------------------------------------
// Table boxes (.creeps-scroll): no hover while scrolling. Cells sliding under a still
// cursor each fired their hover (Dynamics diamonds scale 2.5x with a transition, tooltips,
// row/column highlights) — every wheel frame repainted the table (heroes_dyn: paint
// 818 ms -> 91 ms per 30 wheel steps without it). Hover comes back 150 ms after the
// scroll stops.
// ---------------------------------------------------------------------
(function () {
  var QUIET_MS = 150;
  document.querySelectorAll('.creeps-scroll').forEach(function (box) {
    var t = null;
    box.addEventListener('scroll', function () {
      if (!t) box.classList.add('is-scrolling');
      else clearTimeout(t);
      t = setTimeout(function () { box.classList.remove('is-scrolling'); t = null; }, QUIET_MS);
    }, { passive: true });
  });
})();
