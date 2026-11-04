
// ---- HERO STATS: vertical frozen-pane divider after the pinned Hero column ----
// The hs-table is mr-table-based (not creeps-table), so it doesn't get the
// creeps sticky-frame overlay. This positions a thin vertical line at the
// right edge of the sticky Hero column, drawn in the non-scrolling
// .creeps-page so it keeps repainting during horizontal scroll, shown only
// once the box is scrolled sideways (same convention as Neutral Creeps).
(function() {
  const table = document.querySelector('.hs-table');
  if (!table) return;
  const scroller = table.closest('.creeps-scroll');
  const page = table.closest('.creeps-page');
  const frame = page && page.querySelector('.hs-sticky-frame');
  if (!scroller || !page || !frame) return;

  function position() {
    const nameCell = table.querySelector('thead th.hs-name')
      || table.querySelector('tbody td.hs-name');
    if (!nameCell) return;
    const pageR = page.getBoundingClientRect();
    const scrR = scroller.getBoundingClientRect();
    const tableR = table.getBoundingClientRect();
    const nameR = nameCell.getBoundingClientRect();
    // Anchor the divider top to the pinned header's bottom (thead th is
    // sticky:top, so its rect tracks the visible pinned position).
    const headCell = table.querySelector('thead th.hs-name') || nameCell;
    const headBottom = headCell.getBoundingClientRect().bottom;
    const bottom = Math.min(scrR.bottom, tableR.bottom);
    frame.style.left = (nameR.right - pageR.left) + 'px';
    frame.style.top = (headBottom - pageR.top) + 'px';
    frame.style.height = Math.max(0, bottom - headBottom) + 'px';
    frame.style.width = '0px';
  }

  let posTicking = false;
  const positionRaf = () => {
    if (posTicking) return;
    posTicking = true;
    requestAnimationFrame(() => {
      position();
      frame.classList.toggle('visible', scroller.scrollLeft > 0);
      posTicking = false;
    });
  };
  // Scrolling happens INSIDE .creeps-scroll (the page body is locked), so the
  // divider must be repositioned on the BOX scroll — both vertical (the table's
  // bounding bottom that clamps the divider height moves as content scrolls) and
  // horizontal (visibility). Window scroll never fires here; resize + filter
  // changes also re-anchor (left/height from new column widths + row count).
  scroller.addEventListener('scroll', positionRaf, { passive: true });
  window.addEventListener('resize', positionRaf, { passive: true });
  window.addEventListener('mr:filter-changed', positionRaf);
  position();
})();
