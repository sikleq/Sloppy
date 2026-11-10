

// ---- Pinnable body-level tooltip (shared by the "?" families below) ----
// Click on a badge matching `sel` pins its tooltip: it stays on screen (hover elsewhere
// doesn't hide it), follows the badge on scroll and becomes selectable. A second click on
// the same badge, a click anywhere else or Escape unpins and hides it.
function ecPinnableTip(tip, show, hide, sel) {
  let anchor = null, raf = 0;
  // A pinned tip is laid out in PAGE coordinates (position:absolute, .is-pinned) so it
  // scrolls with the page natively — re-placing a fixed tip on every scroll event lagged
  // a frame behind and made it jitter. Only scrolls of an inner box re-place it (in rAF).
  const place = () => {
    show(anchor);
    tip.style.left = (parseFloat(tip.style.left) + window.scrollX) + 'px';
    tip.style.top = (parseFloat(tip.style.top) + window.scrollY) + 'px';
  };
  const unpin = () => { anchor = null; tip.classList.remove('is-pinned'); hide(); };
  document.addEventListener('click', e => {
    const t = e.target.closest(sel);
    if (t) {
      e.preventDefault();
      if (anchor === t) { unpin(); return; }
      anchor = t;
      tip.classList.add('is-pinned');
      place();
      return;
    }
    if (anchor && !tip.contains(e.target)) unpin();
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && anchor) unpin(); });
  return {
    pinned: () => !!anchor,
    follow: e => {
      if (!anchor) return;
      if (!anchor.isConnected) { unpin(); return; }
      if (!e || e.target === document || e.target === document.documentElement) return;   // page scroll: moves by itself
      if (!raf) raf = requestAnimationFrame(() => { raf = 0; if (anchor) place(); });
    },
  };
}

// ---- Body-level tooltip for `.qhint` badges ----
// CSS `::after` tooltips are clipped by .creeps-scroll's overflow:auto and by
// the sticky header. Render a single shared <div> at <body> level, positioned
// via fixed coordinates relative to the hovered badge.
(function() {
  const tip = document.createElement('div');
  tip.className = 'qhint-tip';
  tip.setAttribute('role', 'tooltip');
  document.body.appendChild(tip);

  function show(target) {
    const text = target.getAttribute('data-tooltip') || '';
    if (!text) return;
    // Tooltip content is author-written (UA_HEAD_HINTS / ABIL_MANUAL) — using
    // innerHTML lets header tooltips include coloured legend spans.
    // Wrap %placeholder% variables (Valve description macros — values aren't
    // resolved here) in a styled span so they read as "this is a variable
    // name" rather than mystery raw text.
    tip.innerHTML = text.replace(
      /%([A-Za-z0-9_]+)%/g,
      '<span class="abil-var">$1</span>');
    tip.classList.add('is-visible');
    // Position above the badge; flip below if it would overflow the viewport top.
    const r = target.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();
    let left = r.left + r.width / 2 - tipRect.width / 2;
    left = Math.max(6, Math.min(left, window.innerWidth - tipRect.width - 6));
    let top = r.top - tipRect.height - 8;
    if (top < 6) top = r.bottom + 8;            // not enough room above → drop below
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }
  function hide() { tip.classList.remove('is-visible'); }

  // Selector matches the original `?` badge plus any element that just opts
  // into the body-level tooltip via `.abil-ico-hint` (currently used on
  // ability icons in the Unit Abilities table).
  // + the Terrain fullscreen panel's compact change chips (icon + "7/28", the word hidden — the owner 2026-10-05):
  // the tooltip says what changed
  // + the calendar's Test servers charts (weeks, patch lines, the rows of "Before each patch")
  const TIP_SEL = '.qhint, .abil-ico-hint, .hd-patch[data-tooltip], .tc-fsp-chips .tf-chip[data-tooltip], .tb-tip-target[data-tooltip]';
  // Click pins the tooltip (read it at leisure, select text); a click anywhere else unpins.
  const pin = ecPinnableTip(tip, show, hide, '.qhint');
  document.addEventListener('mouseover', (e) => {
    const t = e.target.closest(TIP_SEL);
    if (t && !pin.pinned()) show(t);
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest(TIP_SEL) && !pin.pinned()) hide();
  });
  document.addEventListener('focusin', (e) => {
    const t = e.target.closest(TIP_SEL);
    if (t && !pin.pinned()) show(t);
  });
  document.addEventListener('focusout', (e) => {
    if (e.target.closest(TIP_SEL) && !pin.pinned()) hide();
  });
  // Scroll: an unpinned tip hides (the badge's coords change); a pinned one follows its badge.
  window.addEventListener('scroll', e => { if (pin.pinned()) pin.follow(e); else hide(); }, true);
})();

// ---- Body-level tooltip for `.info-tip` "?" badges (patch pages) ----
// CSS-driven `.info-pop` (position:absolute) overflows the viewport when the
// badge is near a screen edge. A single body-level div is positioned via JS
// so it stays clamped inside the viewport on both axes.
(function() {
  const tip = document.createElement('div');
  tip.className = 'info-pop-body';
  document.body.appendChild(tip);

  function show(target) {
    const pop = target.querySelector('.info-pop');
    if (!pop) return;
    tip.innerHTML = pop.innerHTML;
    tip.classList.add('is-visible');
    const r = target.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();
    let left = r.left + r.width / 2 - tipRect.width / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tipRect.width - 8));
    let top = r.top - tipRect.height - 8;
    if (top < 8) top = r.bottom + 8;
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }
  function hide() { tip.classList.remove('is-visible'); }

  // Click pins the "?" popup (read it at leisure, select text); a click anywhere else unpins.
  const pin = ecPinnableTip(tip, show, hide, '.info-tip');
  document.addEventListener('mouseover', e => {
    const t = e.target.closest('.info-tip');
    if (t && !pin.pinned()) show(t);
  });
  document.addEventListener('mouseout', e => {
    if (e.target.closest('.info-tip') && !pin.pinned()) hide();
  });
  document.addEventListener('focusin', e => {
    const t = e.target.closest('.info-tip');
    if (t && !pin.pinned()) show(t);
  });
  document.addEventListener('focusout', e => {
    if (e.target.closest('.info-tip') && !pin.pinned()) hide();
  });
  window.addEventListener('scroll', e => { if (pin.pinned()) pin.follow(e); else hide(); }, true);
})();

// ---- Centre the row jumped to via #anchor (cross-page or same-page) ----
// The Tables pages have an inner `.creeps-scroll` overflow box AND the page
// itself scrolls — `el.scrollIntoView({block:'center'})` only centres within
// the immediate scroll parent (usually the inner box), leaving the row near
// the top of the viewport. Manually centre on BOTH axes: scroll the inner
// container so the row is mid-box, then scroll the window so the box's
// mid-point aligns with the viewport centre.
(function() {
  function centerHash() {
    const h = location.hash.slice(1);
    if (!h) return;
    const el = document.getElementById(decodeURIComponent(h));
    if (!el) return;
    // Give the jumped-to row the SAME selected style as a manual row click
    // (gold frame), replacing the old yellow :target flash. Single-select:
    // clear any previously marked row in the same table first.
    if (el.tagName === 'TR') {
      const tb = el.closest('tbody');
      if (tb) tb.querySelectorAll('tr.row-marked').forEach(r =>
        r.classList.remove('row-marked', 'row-flash'));
      el.classList.add('row-marked');
    }
    // Double rAF: lets table layout, sticky header, and any view-toggle
    // reorderings settle before measuring rects.
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const inner = el.closest('.creeps-scroll');
      if (inner) {
        const ir = inner.getBoundingClientRect();
        const er = el.getBoundingClientRect();
        // Account for the sticky <thead> overlapping the inner box's top —
        // subtract its height so the row centres in the VISIBLE area below
        // the frozen header, not in the raw box.
        const thead = inner.querySelector('thead');
        const headH = thead ? thead.getBoundingClientRect().height : 0;
        const visibleTop = ir.top + headH;
        const visibleCenter = visibleTop + (ir.bottom - visibleTop) / 2;
        const elCenter = er.top + er.height / 2;
        inner.scrollTop += (elCenter - visibleCenter);
      }
      // Now align the row with the window viewport centre (page-level scroll).
      const er2 = el.getBoundingClientRect();
      const targetY = er2.top + er2.height / 2;
      window.scrollBy({
        top: targetY - window.innerHeight / 2,
        behavior: 'smooth',
      });
    }));
  }
  window.addEventListener('hashchange', centerHash);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', centerHash);
  } else {
    centerHash();
  }

  // ---- CROSS-HIGHLIGHT FOR ALL <table> ELEMENTS ----
  // On hover of any <td>, light up the entire row + the entire column the
  // cell sits in (visual "+" through the table, like Liquipedia crosstable).
  // Attaches to every <table> on the page after DOM ready.
  function wireCrossHover(table) {
    if (table.dataset.crossWired === '1') return;
    // Dynamics matrices can be 350 rows x 116 patch columns. Column cross-hover
    // mutates one cell per row on every mouse move, which is cheap for normal
    // tables but makes items_dyn heavy when "Hide old" is off. Row click,
    // dyn-cell hover tooltips, sorting and filters stay intact without it.
    if (table.classList.contains('heroes-dyn-table')) return;
    table.dataset.crossWired = '1';
    let activeRow = null;
    const colCells = [];
    const clear = () => {
      if (activeRow) {
        activeRow.classList.remove('cross-row');
        activeRow = null;
      }
      colCells.forEach(c => c.classList.remove('cross-col'));
      colCells.length = 0;
    };
    table.addEventListener('mouseover', e => {
      // Only TD cells trigger / receive the cross-highlight. Hovering a TH
      // (header) shouldn't sweep the row beneath it and shouldn't paint
      // the column band — the heatmap on data cells is the only visual
      // intent there.
      const cell = e.target.closest('td');
      if (!cell || !table.contains(cell)) return;
      const row = cell.parentElement;
      if (row.tagName !== 'TR') return;
      const idx = cell.cellIndex;
      if (row === activeRow &&
          colCells.length && colCells[0].cellIndex === idx) return;
      clear();
      activeRow = row;
      row.classList.add('cross-row');
      // Walk only TBODY rows — TH cells in thead never get cross-col.
      table.querySelectorAll('tbody tr').forEach(tr => {
        const c = tr.cells && tr.cells[idx];
        if (c) {
          c.classList.add('cross-col');
          colCells.push(c);
        }
      });
    });
    table.addEventListener('mouseleave', clear);
  }
  function wireAllTables() {
    document.querySelectorAll('table').forEach(wireCrossHover);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wireAllTables);
  } else {
    wireAllTables();
  }
})();
