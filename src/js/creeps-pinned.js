
// ---- CREEPS TABLE: pin identity columns on horizontal scroll ----
(function() {
  const table = document.querySelector('.creeps-table');
  if (!table) return;
  const firstRow = table.querySelector('tbody tr');
  if (!firstRow) return;

  // Pin sticky-column widths to their FULL-roster initial measurement so the
  // attack-type filter (display:none on hidden rows) can't reshape the lvl /
  // icon / name columns when the visible roster changes. With table-layout:
  // auto, min-width alone only sets a floor — the browser can still GROW
  // pinned columns when other (non-sticky) columns shrink and the table's
  // `min-width:100%` forces it back to container width. Pin min + max + width
  // on the col-row sticky <th>s, AND pin icon col individually via every
  // body row's .creep-icon-cell (the Юнит th's colspan=2 only pins the
  // icon+name SUM, not their internal ratio). Run once on init, before any
  // filter has a chance to fire.
  (function pinStickyCols() {
    if (table.classList.contains('heroes-dyn-table')) return;
    const tds = [...firstRow.children];
    if (tds.length < 3) return;
    const wLvl  = Math.ceil(tds[0].getBoundingClientRect().width);
    const wIcon = Math.ceil(tds[1].getBoundingClientRect().width);
    const wName = Math.ceil(tds[2].getBoundingClientRect().width);
    const pin = (el, w) => {
      el.style.minWidth = w + 'px';
      el.style.maxWidth = w + 'px';
      el.style.width    = w + 'px';
    };
    const headStickies = table.querySelectorAll('thead tr.col-row th.sticky-col');
    // Two head shapes share this IIFE:
    //   • Neutral Stats (.creeps-table.mode-standard): 2 sticky <th>s — lvl
    //     and "Юнит" (colspan=2 over icon+name). Second th gets wIcon+wName.
    //   • Unit Abilities (.unit-abilities-table): 3 sticky <th>s — lvl, unit,
    //     ability, all individual. Each th gets its own body-cell width.
    // Differentiator = sticky-th count, not table class — keeps the code
    // ready for any future creeps-table variant.
    if (headStickies.length === 2) {
      pin(headStickies[0], wLvl);
      pin(headStickies[1], wIcon + wName);   // colspan'd Юнит
    } else if (headStickies.length >= 3) {
      pin(headStickies[0], wLvl);
      pin(headStickies[1], wIcon);
      pin(headStickies[2], wName);
    }
    // Pin icon AND name cols individually on every body row. The Юнит th's
    // colspan=2 only pins the icon+name SUM — max-width on a colspan'd cell
    // doesn't enforce per-column limits in auto layout, so the name col can
    // still grow/shrink with its widest visible content (Forest Troll
    // Berserker disappearing on melee filter was the trigger). Pinning both
    // body cols freezes the internal split. Covers both tables — the
    // selectors match Neutral Stats (.col-name) and UA (.ua-ability) cells.
    table.querySelectorAll('tbody tr > td.creep-icon-cell.sticky-col')
      .forEach(td => pin(td, wIcon));
    table.querySelectorAll('tbody tr > td.col-name.sticky-col, tbody tr > td.ua-ability.sticky-col')
      .forEach(td => pin(td, wName));
  })();

  // Body identity cells are the first three: lvl(0), icon(1), name(2).
  // The header has only two cells over them: lvl th(0) + Юнит th(1,
  // colspan=2). Compute cumulative left offsets from the body widths and
  // apply them to both the body sticky cells and the header sticky cells.
  function applyLeftOffsets() {
    // Use the first VISIBLE row — once attack-type filter is applied, the
    // cached firstRow may be display:none, making its getBoundingClientRect
    // collapse to zero and breaking sticky lefts.
    const measureRow = [...table.querySelectorAll('tbody tr')]
      .find(tr => tr.offsetParent !== null) || firstRow;
    const tds = [...measureRow.children];
    if (tds.length < 3) return;
    const wLvl  = tds[0].getBoundingClientRect().width;
    const wIcon = tds[1].getBoundingClientRect().width;
    const lefts = [0, wLvl, wLvl + wIcon];           // lvl, icon, name

    // Body rows. Most rows have all 3 sticky identity cells (lvl, icon, name).
    // On the Unit Abilities page, a multi-ability unit rowspans its lvl+icon
    // cells, so continuation rows carry ONLY the ability sticky cell — which
    // belongs at the 3rd offset. Assign by how many sticky cells the row has.
    table.querySelectorAll('tbody tr').forEach(tr => {
      const sc = [...tr.children].filter(c => c.classList.contains('sticky-col'));
      // Creeps: 3 sticky cells (lvl, icon, name). Unit Abilities: 2 (lvl, unit).
      // UA continuation rows (rowspanned lvl+unit) have 0 → nothing to pin.
      sc.forEach((cell, i) => { cell.style.left = lefts[i] + 'px'; });
    });
    // Header sticky cells. heroes_dyn has ONE frozen column (hero) but TWO
    // header rows over it (super-category + version), so BOTH header sticky
    // cells pin at left:0 — not the creeps lvl(0)+unit(wLvl) two-column layout.
    const headStickies = table.querySelectorAll('thead th.sticky-col');
    if (table.classList.contains('heroes-dyn-table')) {
      headStickies.forEach(th => { th.style.left = '0px'; });
    } else {
      if (headStickies[0]) headStickies[0].style.left = '0px';
      if (headStickies[1]) headStickies[1].style.left = wLvl + 'px';
    }
  }

  applyLeftOffsets();
  window.addEventListener('resize', applyLeftOffsets, { passive: true });

  // Click a cell to mark its row (single-select, no animation). Clicking
  // another row moves the mark; clicking the marked row again clears it.
  // Matches the simpler highlight behaviour used by the Mana Items table —
  // multi-select + fade-flash earlier here was hard to read once a few
  // rows were marked.
  const tbody = table.querySelector('tbody');
  if (tbody) {
    tbody.addEventListener('click', e => {
      if (e.target.closest('a, img')) return;
      const tr = e.target.closest('tr');
      if (!tr) return;
      const was = tr.classList.contains('row-marked');
      tbody.querySelectorAll('tr.row-marked').forEach(r =>
        r.classList.remove('row-marked', 'row-flash'));
      if (!was) tr.classList.add('row-marked');
    });
  }

  // Overlay frame around the pinned identity block, shown while scrolled.
  // It lives in .creeps-page (non-scrolling), so its border + shadow keep
  // repainting during scroll — unlike box-shadow on the sticky cells,
  // which Chrome drops mid-scroll.
  const scroller = table.closest('.creeps-scroll');
  const page = table.closest('.creeps-page');
  const frame = page && page.querySelector('.sticky-frame');       // vertical

  function positionFrames() {
    if (!scroller || !page) return;
    const firstTds = [...firstRow.children];
    if (firstTds.length < 3) return;
    const pageR  = page.getBoundingClientRect();
    const scrR   = scroller.getBoundingClientRect();
    const tableR = table.getBoundingClientRect();
    // Right edge of the frozen identity block = right edge of the LAST sticky
    // column in the row. Creeps/UA pin 2-3 columns; the heroes_dyn matrix pins
    // just one (the hero name) — measuring the last sticky cell keeps the
    // divider correct for any number of frozen columns (hardcoding firstTds[2]
    // put the divider 2 columns too far right on the single-column matrix).
    const stickyCells = firstRow.querySelectorAll('.sticky-col');
    const lastSticky = table.classList.contains('heroes-dyn-table')
      ? (table.querySelector('thead th.hd-hero.sticky-col')
          || table.querySelector('thead th.hd-hero')
          || stickyCells[stickyCells.length - 1]
          || firstTds[2])
      : (stickyCells[stickyCells.length - 1] || firstTds[2]);
    const nameR  = lastSticky.getBoundingClientRect();  // right edge of pinned block
    // Anchor the divider's top to the VISIBLE (pinned) header bottom. The
    // <thead> element itself is position:static — only its <th> cells are
    // position:sticky — so once the box scrolls down, the thead's own rect
    // scrolls up (its bottom goes negative) while the column headers stay
    // pinned at the box top. Measuring table.tHead therefore made the divider's
    // top climb ABOVE the visible header (the bright line poked past the
    // category header on vertical+horizontal scroll). Anchor instead to a
    // PINNED header cell (the col-row's sticky-col <th>): its bottom tracks the
    // real visible header bottom both at rest (natural position below the blurb)
    // and once pinned under the nav.
    const headCell = table.querySelector('thead tr.col-row th.sticky-col')
      || table.querySelector('thead tr.col-row th')
      || table.tHead;
    const headBottom = headCell
      ? headCell.getBoundingClientRect().bottom
      : scrR.top;
    // Vertical divider: at the right edge of the frozen lvl/unit columns,
    // starting BELOW the sticky column header and spanning the rest of height.
    if (frame) {
      const bottom = Math.min(scrR.bottom, tableR.bottom);
      frame.style.left   = (nameR.right - pageR.left) + 'px';
      frame.style.top    = (headBottom - pageR.top) + 'px';
      frame.style.height = Math.max(0, bottom - headBottom) + 'px';
      frame.style.width  = '0px';
    }
  }

  if (scroller) {
    const syncFrameVisibility = () => {
      const hasOverflowX = scroller.scrollWidth - scroller.clientWidth > 1;
      const sx = hasOverflowX && scroller.scrollLeft > 0;
      scroller.classList.toggle('scrolled', sx);
      if (frame) frame.classList.toggle('visible', sx);
    };
    // The frozen-pane divider's geometry depends on layout, not on the scroll
    // position inside the box: sticky columns and sticky headers keep the same
    // screen-space edges while the tbody scrolls underneath. Re-reading layout
    // on every scroll frame was wasted work on the widest tables.
    let ticking = false;
    const positionFramesRaf = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        try {
          positionFrames();
          syncFrameVisibility();
        } finally { ticking = false; }
      });
    };
    // The page body is locked — vertical + horizontal scrolling both happen
    // INSIDE .creeps-scroll, not on the window. The sticky header pins to the
    // box top while the tbody scrolls under it, and the table's bounding rect
    // (used to clamp the divider's bottom) moves as the content scrolls — so the
    // divider's top/height must be RE-COMPUTED on every box-scroll frame, not
    // just its visibility. raf-throttled, so it's cheap even on the wide matrix.
    scroller.addEventListener('scroll', positionFramesRaf, { passive: true });
    window.addEventListener('resize', positionFramesRaf, { passive: true });
    // Layout-changing toggles (hide-old / filters) broadcast this so the divider
    // re-anchors to the new column widths + table height.
    window.addEventListener('mr:filter-changed', positionFramesRaf);

    // Super-category header colspans must equal the number of CURRENTLY
    // visible leaf columns in each category — otherwise the static (Expanded)
    // colspans misalign with the collapsed columns in Standard view.
    function recomputeCatColspans() {
      document.querySelectorAll('.cat-head[data-cat]').forEach(head => {
        let span = 0;
        document.querySelectorAll('.col-row th[data-cat="' + head.dataset.cat + '"]')
          .forEach(th => { if (th.offsetParent !== null) span += th.colSpan || 1; });
        head.colSpan = span || 1;
      });
    }

    // View toggle (Standard / Expanded) via the calendar-style select.
    const viewSel = document.getElementById('view-mode');
    if (viewSel) {
      const applyView = () => {
        const expanded = viewSel.value === 'expanded';
        table.classList.toggle('mode-standard', !expanded);
        table.classList.toggle('mode-expanded', expanded);
        recomputeCatColspans();
        applyLeftOffsets();   // column widths changed → recompute pinned offsets
        positionFramesRaf();
      };
      viewSel.addEventListener('change', applyView);
      applyView();            // initial pass (Standard)
    } else {
      recomputeCatColspans();
    }

    // Attack-type filters on Neutral Stats. Uses the same toolbar button
    // markup/style as Hero Stats, but operates on the creeps-table rows.
    const attackBtns = [...document.querySelectorAll('.hs-attack-filter')];
    if (attackBtns.length && table.querySelector('tbody tr[data-attack-type]')) {
      let attackFilter = '';
      const applyAttackFilter = () => {
        table.querySelectorAll('tbody tr[data-attack-type]').forEach(tr => {
          tr.classList.toggle(
            'mr-attack-out',
            !!attackFilter && tr.dataset.attackType !== attackFilter
          );
        });
        attackBtns.forEach(btn => {
          const active = btn.dataset.attackFilter === attackFilter;
          btn.classList.toggle('active', active);
          btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
        // Re-collapse level labels over the now-visible row subset (else
        // hidden "first of group" rows blank the next visible row's lvl).
        if (table._groupRows) {
          table._groupRows([...table.querySelectorAll('tbody tr')]);
        }
        applyLeftOffsets();
      };
      attackBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const next = btn.dataset.attackFilter || '';
          attackFilter = attackFilter === next ? '' : next;
          applyAttackFilter();
        });
      });
      applyAttackFilter();
    }
    positionFramesRaf();
  }
})();
