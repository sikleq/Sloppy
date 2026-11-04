
// ---- CREEPS TABLE: click icon → copy "-createhero <name> neutral" ----
(function() {
  const icons = document.querySelectorAll('.creep-copy[data-cmd]');
  if (!icons.length) return;

  // One reusable toast element appended to body.
  let toast = null;
  let hideTimer = null;
  function showToast(x, y) {
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'copy-toast';
      toast.textContent = 'Copied';
      document.body.appendChild(toast);
    }
    toast.style.left = x + 'px';
    toast.style.top = y + 'px';
    // restart the fade animation
    toast.classList.remove('is-visible');
    void toast.offsetWidth; // force reflow so re-adding the class re-triggers
    toast.classList.add('is-visible');
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => toast.classList.remove('is-visible'), 900);
  }

  async function copyCmd(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (e) {
      // Fallback for non-secure contexts (file://, http on some browsers)
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (_) {}
      document.body.removeChild(ta);
      return ok;
    }
  }

  icons.forEach(img => {
    img.style.cursor = 'pointer';
    img.addEventListener('click', async (e) => {
      const cmd = img.getAttribute('data-cmd');
      if (!cmd) return;
      const ok = await copyCmd(cmd);
      if (ok) {
        const r = img.getBoundingClientRect();
        showToast(r.left + r.width / 2, r.top - 6);
      }
    });
  });
})();

// ---- CREEPS TABLE: sortable columns ----
(function() {
  const table = document.querySelector('.creeps-table');
  if (!table) return;
  const tbody = table.querySelector('tbody');
  const headers = [...table.querySelectorAll('thead th.sortable')];
  if (!tbody || !headers.length) return;

  // Map column key → body-cell index. data-idx is authored server-side so
  // it stays correct despite the colspan=2 on the Юнит header (which makes
  // DOM th position diverge from cell index).
  const colIndex = {};
  headers.forEach(th => {
    if (th.dataset.col) colIndex[th.dataset.col] = parseInt(th.dataset.idx, 10);
  });

  // Sort value for a cell: prefer the numeric data-lvl on the level
  // column (its text gets blanked by collapseLevels), else parse the
  // first number out of the text (handles "240", "+0,5", "3-5",
  // "1400/800", "0%", "Ближняя (100)"), else fall back to lowercased
  // text. Empty cells return null and always sink to the bottom.
  function cellVal(tr, idx) {
    const td = tr.children[idx];
    if (!td) return null;
    if (td.dataset.lvl !== undefined && td.dataset.lvl !== '') {
      return parseFloat(td.dataset.lvl);
    }
    // Icon-only columns carry a data-sort value: a number (rank) for flag
    // columns (dash 0 < No 1 < Yes 2), or a string (e.g. the Unit name).
    if (td.dataset.sort !== undefined) {
      const s = td.dataset.sort;
      const n = parseFloat(s);
      return isNaN(n) ? s.toLowerCase() : n;
    }
    const t = td.textContent.trim();
    if (!t || t === ' ') return null;
    if (t === '-') return 0;   // explicit "no mana" — sorts as the minimum, not last
    const m = t.replace(',', '.').match(/-?\d+(?:\.\d+)?/);
    return m ? parseFloat(m[0]) : t.toLowerCase();
  }

  // Show the level number once per consecutive run; blank the repeats and
  // draw the group divider (tier-break) at each run start. Works in any
  // row order, so the grouped look survives sorting by level. Visibility-
  // aware: rows hidden by filter (mr-attack-out / mr-filtered-out /
  // mr-search-out → display:none) don't participate in run tracking — else
  // a hidden "first of group" row would leave the next visible row blank
  // (the bug behind the ranged filter losing all level labels).
  function collapseLevels(rows) {
    let prev = null;
    rows.forEach(tr => {
      const cell = tr.querySelector('.lvl-cell');
      if (!cell) return;
      if (tr.classList.contains('mr-attack-out')
          || tr.classList.contains('mr-filtered-out')
          || tr.classList.contains('mr-search-out')) return;
      const lvl = cell.dataset.lvl;
      if (lvl !== prev) { cell.textContent = lvl; tr.classList.add('tier-break'); }
      else { cell.textContent = ''; tr.classList.remove('tier-break'); }
      prev = lvl;
    });
  }

  // Unit Abilities: group consecutive rows of the SAME unit — show the Lvl +
  // Unit icon only on the first row of each run, hide on the rest (cells stay
  // for alignment). Recomputed after every sort so it works in any order.
  const isUA = table.classList.contains('unit-abilities-table');
  function groupByUnit(rows) {
    let prevUnit = null, prevLvl = null;
    rows.forEach(tr => {
      const u = tr.dataset.unit;
      const lvlCell = tr.querySelector('.ua-lvl');
      const lvl = lvlCell ? lvlCell.dataset.lvl : null;
      // Level grouping — show the number once per level run + the horizontal
      // tier divider at each level change (mirrors the Neutral Creeps table).
      if (lvl !== prevLvl) {
        if (lvlCell) lvlCell.textContent = lvl;
        tr.classList.add('tier-break');
      } else {
        if (lvlCell) lvlCell.textContent = '';
        tr.classList.remove('tier-break');
      }
      // Unit-icon dedup — show the icon only on the first row of each unit run.
      if (u !== prevUnit) tr.classList.remove('ua-dup');
      else tr.classList.add('ua-dup');
      prevUnit = u; prevLvl = lvl;
    });
  }
  const groupRows = isUA ? groupByUnit : collapseLevels;
  // Expose to the attack-type filter (lives in a sibling IIFE) so it can
  // re-run grouping after hiding rows — else hidden "first of run" rows
  // leave the next visible row with a blank lvl cell.
  table._groupRows = groupRows;

  // Merge consecutive identical ability cells into one rowspanned cell (only
  // in the default order — sorting reads cells by column index, so we un-merge
  // first). Process columns right-to-left so removals don't shift earlier idx.
  let abilMerges = [];
  function unmergeAbilityRuns() {
    for (let i = abilMerges.length - 1; i >= 0; i--) {
      abilMerges[i].tr.insertBefore(abilMerges[i].td, abilMerges[i].next);
    }
    abilMerges = [];
    tbody.querySelectorAll('td').forEach(td => {
      if (td.rowSpan > 1 && /\bcol-ability/.test(td.className)) td.rowSpan = 1;
    });
  }
  function mergeAbilityRuns(rows) {
    ['ability3', 'ability2', 'ability1'].forEach(col => {
      const idx = colIndex[col];
      if (idx == null) return;
      let i = 0;
      while (i < rows.length) {
        const td = rows[i].children[idx];
        const name = td && td.dataset.name;
        if (!name) { i++; continue; }
        // Shared auras stay per-unit: each frog keeps its own cell so a row
        // click highlights it (merging would rowspan 4 frogs into one block).
        if (name === 'Riverborn Aura') { i++; continue; }
        let j = i + 1;
        while (j < rows.length && rows[j].children[idx] &&
               rows[j].children[idx].dataset.name === name) j++;
        if (j - i > 1) {
          td.rowSpan = j - i;
          for (let k = i + 1; k < j; k++) {
            const rm = rows[k].children[idx];
            abilMerges.push({ tr: rows[k], td: rm, next: rm.nextSibling });
            rm.remove();
          }
        }
        i = j;
      }
    });
  }

  let sortCol = null, sortState = 0;  // 0 = neutral, 1 = descending, 2 = ascending
  const originalOrder = [...tbody.querySelectorAll('tr')];

  // Moving rows in the DOM resets CSS animations to t=0. Snapshot currentTime
  // for every animated element before the move, restore it after so running
  // animations continue without restarting.
  function snapAnims(rows) {
    const map = new Map();
    rows.forEach(tr => {
      tr.querySelectorAll('[style*="animation"]').forEach(el => {
        const anims = el.getAnimations();
        if (anims.length) map.set(el, anims.map(a => a.currentTime));
      });
    });
    return map;
  }
  function restoreAnims(map) {
    map.forEach((times, el) => {
      el.getAnimations().forEach((a, i) => { if (times[i] != null) a.currentTime = times[i]; });
    });
  }

  function applySort(col, dir) {
    unmergeAbilityRuns();             // restore full cells before index-based sort
    const idx = colIndex[col];
    const rows = [...tbody.querySelectorAll('tr')];
    rows.sort((a, b) => {
      const va = cellVal(a, idx), vb = cellVal(b, idx);
      if (va === null && vb === null) return 0;
      if (va === null) return 1;          // empties always last
      if (vb === null) return -1;
      if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    });
    const snap = snapAnims(rows);
    rows.forEach(tr => tbody.appendChild(tr));
    restoreAnims(snap);
    groupRows(rows);
  }

  headers.forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      // 3-state cycle: neutral → descending → ascending → neutral.
      if (sortCol === col) sortState = (sortState + 1) % 3;
      else { sortCol = col; sortState = 1; }     // first click = descending (largest first)
      headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
      if (sortState === 0) {
        // Back to neutral: restore the default level-grouped order, dim ↕ returns.
        sortCol = null;
        unmergeAbilityRuns();
        const snap0 = snapAnims(originalOrder);
        originalOrder.forEach(tr => tbody.appendChild(tr));
        restoreAnims(snap0);
        groupRows(originalOrder);
        mergeAbilityRuns(originalOrder);   // re-merge in default order
      } else {
        const dir = sortState === 1 ? -1 : 1;
        th.classList.add(dir === 1 ? 'sort-asc' : 'sort-desc');
        applySort(col, dir);
      }
    });
  });

  // Initial pass: collapse/group the default order + merge ability runs.
  groupRows([...tbody.querySelectorAll('tr')]);
  mergeAbilityRuns([...tbody.querySelectorAll('tr')]);

  // Unit Abilities VIEW filter (Standard | Only Auras). Toggles a class on
  // the table; CSS hides non-aura rows. Also reorders columns: in "Only Auras"
  // the visible order is Lvl/Unit/Ability | Radius/Duration | Aura Stack/Through
  // BKB/AS Effect/MS Effect | Effect 1-3 — grouped so the category header (kept
  // in Auras view too) spans contiguous columns.
  const uaView = document.getElementById('ua-view-mode');
  if (uaView) {
    const STD_ORDER = ['lvl', 'unit', 'ability', 'type', 'damage',
      'manacost', 'cooldown', 'duration', 'cast_range', 'aoe', 'stackable',
      'dispel', 'through_bkb', 'as_effect', 'ms_effect',
      'effect', 'effect2', 'effect3'];
    // Auras view: VISIBLE columns first, grouped by category (Basic | Essentials
    // = Radius,Duration | Extra | Effects), then the hidden-by-CSS columns
    // (type/damage/manacost/cooldown/cast_range/dispel) at the end so the DOM
    // child count stays in sync.
    const AURA_ORDER = ['lvl', 'unit', 'ability', 'aoe', 'duration',
      'stackable', 'through_bkb', 'as_effect', 'ms_effect',
      'effect', 'effect2', 'effect3',
      'type', 'damage', 'manacost', 'cooldown', 'cast_range', 'dispel'];
    const headRow = table.querySelector('thead .col-row')
      || table.querySelector('thead tr');
    // Resize each category cell to its currently-visible leaf columns (Auras
    // hides some), so the category header lines up in both views.
    function recomputeUaCats() {
      table.querySelectorAll('thead tr.cat-row th.cat-head[data-cat]').forEach(head => {
        let span = 0;
        table.querySelectorAll('thead tr.col-row th[data-cat="' + head.dataset.cat + '"]')
          .forEach(th => { if (th.offsetParent !== null) span += th.colSpan || 1; });
        head.colSpan = span || 1;
      });
    }

    function reorderCells(order) {
      const reorderOne = (parent) => {
        order.forEach(k => {
          const cell = [...parent.children].find(c => c.dataset.col === k);
          if (cell) parent.appendChild(cell);
        });
      };
      if (headRow) reorderOne(headRow);
      tbody.querySelectorAll('tr').forEach(reorderOne);
      // Refresh colIndex (used by cellVal) for the new column positions.
      Object.keys(colIndex).forEach(k => delete colIndex[k]);
      if (headRow) {
        [...headRow.children].forEach((th, i) => {
          if (th.dataset.col) colIndex[th.dataset.col] = i;
        });
      }
    }

    // Vertical category dividers: left border on the first VISIBLE column of each
    // category (after the first), on the header col-row AND every body cell so the
    // line runs the full height. Driven by data-cat so it tracks the Auras reorder.
    // AURA_HIDDEN mirrors the columns hidden by .filter-auras in styles.css.
    const AURA_HIDDEN = new Set(['type', 'damage', 'manacost', 'cooldown', 'cast_range', 'dispel']);
    function markCatEdges(auras) {
      const hidden = auras ? AURA_HIDDEN : null;
      const rows = [headRow, ...tbody.querySelectorAll('tr')];
      rows.forEach(row => {
        if (!row) return;
        let prevCat = null;
        [...row.children].forEach(cell => {
          cell.classList.remove('cat-edge');
          const col = cell.dataset.col, cat = cell.dataset.cat;
          if (!col || (hidden && hidden.has(col))) return;   // skip hidden columns
          if (prevCat !== null && cat && cat !== prevCat) cell.classList.add('cat-edge');
          if (cat) prevCat = cat;
        });
      });
    }

    const applyUaView = () => {
      const auras = uaView.value === 'auras';
      table.classList.toggle('filter-auras', auras);
      reorderCells(auras ? AURA_ORDER : STD_ORDER);
      recomputeUaCats();          // category header spans the now-visible columns
      markCatEdges(auras);        // category dividers track the visible columns
      groupRows(auras
        ? [...tbody.querySelectorAll('tr.ua-row-aura')]
        : [...tbody.querySelectorAll('tr')]);
    };
    uaView.addEventListener('change', applyUaView);
    markCatEdges(false);          // initial Standard-view dividers
  }

  // Upgrades — binary switch. Toggles `.show-upgrades` on the UA table;
  // CSS draws a soft rounded outline + faint fill on every `td.leveled`.
  const uaUpg = document.getElementById('ua-upgrades-mode');
  if (uaUpg && table) {
    const apply = () => table.classList.toggle('show-upgrades', uaUpg.checked);
    uaUpg.addEventListener('change', apply);
    apply();
  }
})();
