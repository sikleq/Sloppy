
// ---- CREEPS / UNIT ABILITIES: size the scroll box to fit the viewport ----
// The table lives in a height-capped .creeps-scroll box (the page is locked so
// only this box scrolls — one scrollbar). CSS sets the box max-height; this only
// measures the category row's rendered height into --cat-row-h, which the
// two-row sticky header offset (col-row top: calc(--cat-row-h - 2px)) needs —
// CSS calc can't read it.
(function() {
  const box = document.querySelector('.creeps-page .creeps-scroll');
  if (!box) return;
  const catRow = box.querySelector('table thead tr.cat-row');
  function size() {
    // CSS handles the box's max-height now: `calc(100vh - var(--site-nav-h)
    // - 12px)` keeps it sized to fit the viewport regardless of scroll
    // position, in concert with `position: sticky; top: var(--site-nav-h)`
    // on the box itself. JS only updates --cat-row-h (which CSS calc can't
    // measure — it depends on the rendered text height of the category row).
    //
    // Two-row sticky header (Neutral Creeps): pin the column row exactly
    // under the category row. Use the fractional rect height (rounded) for an
    // accurate offset; the col-row CSS also pulls up 1px to mask any seam.
    // Unit Abilities has no .cat-row → 0 so its single header row pins flush.
    // Math.floor (not round): pairs with the col-row's -2px pull-up so the
    // col-row always starts at least 2px BEFORE the cat-row's true bottom,
    // guaranteeing the two sticky rows overlap regardless of fractional
    // heights — kills the scroll-time gap where body cells showed through.
    document.documentElement.style.setProperty(
      '--cat-row-h',
      (catRow ? Math.floor(catRow.getBoundingClientRect().height) : 0) + 'px');
  }
  size();
  window.addEventListener('resize', size, { passive: true });
  // Recompute after images (the helmet logo grows the nav) finish loading —
  // an early measurement underestimates the nav height and lets the box run
  // past the viewport, which makes the page scroll and the toolbar drift.
  window.addEventListener('load', size);
  const logo = document.querySelector('.nav-brand-logo');
  if (logo && !logo.complete) logo.addEventListener('load', size);
})();
