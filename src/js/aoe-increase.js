
// ---- AOE INCREASE (aoe_increase.html): item + upgrade filter recompute ----
// Each .aoe-line carries data-base / data-talent / data-scepter / data-shard
// (per-level radius + upgrade deltas). Upgrade toggles add their deltas (and
// reveal gated radii whose base is 0); an AoE item then scales the result:
//   radius  = base + (talent? + scepter? + shard?)         [if its toggle is on]
//   shown   = (radius + flat) * (1 + pct/100)               [if an item is on]
// e.g. base 400 + Chasm Stone (+40) + Dezun (+20%) = (440)*1.2 = 528.
(function () {
  const table = document.querySelector('.aoe-table');
  if (!table) return;
  const itemBtns = [...document.querySelectorAll('.aoe-item-btn')];
  const upBtns = [...document.querySelectorAll('.aoe-up-btn')];
  if (!itemBtns.length && !upBtns.length) return;
  const rows = [...table.querySelectorAll('tbody tr')];

  const nums = s => { const t = (s || '').trim(); return t ? t.split(/\s+/).map(Number).filter(n => !isNaN(n)) : []; };
  // Per-value (not per-line) so a line can hold two radii (AA Ice Blast min/max).
  const vals = [...table.querySelectorAll('.aoe-val')].map(el => ({
    el,
    line: el.closest('.aoe-line'),
    base: nums(el.dataset.base),
    talent: nums(el.dataset.talent),
    scepter: nums(el.dataset.scepter),
    shard: nums(el.dataset.shard),
    talentGlobal: nums(el.dataset.talentGlobal),
    // Absolute overrides ("=800") — when the upgrade is on, REPLACE base.
    talentSet: nums(el.dataset.talentSet),
    scepterSet: nums(el.dataset.scepterSet),
    shardSet: nums(el.dataset.shardSet),
  }));
  const linesSet = [...table.querySelectorAll('.aoe-line')].map(line => ({
    line,
    vals: [...line.querySelectorAll('.aoe-val')],
  }));
  const abilities = [...table.querySelectorAll('.aoe-ability')].map(ab => ({
    ab,
    cell: ab.closest('td.aoe-cell'),
    dash: ab.closest('td.aoe-cell')?.querySelector('.aoe-cell-dash') || null,
    lines: [...ab.querySelectorAll('.aoe-line')],
    marks: {
      talent: ab.querySelector('.aoe-mark-talent'),
      scepter: ab.querySelector('.aoe-mark-scepter'),
      shard: ab.querySelector('.aoe-mark-shard'),
    },
  }));

  let flat = 0, pct = 0;
  const up = { talent: false, scepter: false, shard: false };

  // base[] + delta[] elementwise (delta broadcasts a single value over levels).
  function add(arr, delta) {
    if (!delta.length) return arr;
    if (delta.length === 1) return arr.map(b => b + delta[0]);
    const n = Math.max(arr.length, delta.length);
    const out = [];
    for (let i = 0; i < n; i++) out.push((arr[i] ?? arr[arr.length - 1]) + (delta[i] ?? delta[delta.length - 1]));
    return out;
  }
  function fmt(levels) {
    let r = levels.map(n => Math.round(n));
    // Strip leading zeros (e.g. DK Dragon Form splash 0/275/275/350 → 275/275/350).
    const first = r.findIndex(n => n !== 0);
    if (first > 0) r = r.slice(first);
    return r.every(n => n === r[0]) ? String(r[0]) : r.join('/');
  }

  function markVisibleEdgeRows() {
    rows.forEach(tr => {
      tr.classList.remove('aoe-visible-first', 'aoe-visible-last');
    });
    const visible = rows.filter(tr => !tr.classList.contains('mr-search-out'));
    if (!visible.length) return;
    visible[0].classList.add('aoe-visible-first');
    visible[visible.length - 1].classList.add('aoe-visible-last');
  }

  function recompute(opts = {}) {
    vals.forEach(V => {
      if (!V.base.length) return;
      // An upgrade with an absolute override ("=N") REPLACES the radius;
      // otherwise its delta is added. Talent / Scepter / Shard apply in turn.
      let radius = V.base;
      if (up.talent)  radius = V.talentSet.length  ? V.talentSet  : add(radius, V.talent);
      if (up.scepter) radius = V.scepterSet.length ? V.scepterSet : add(radius, V.scepter);
      if (up.shard)   radius = V.shardSet.length   ? V.shardSet   : add(radius, V.shard);
      const visible = Math.max(...radius) > 0;
      // Generic +AoE talents (special_bonus_spell_aoe_N) affect every real
      // AoE radius, but they must not reveal zero-base upgrade-only modes.
      if (visible && up.talent && V.talentGlobal.length) radius = add(radius, V.talentGlobal);
      V.el.hidden = !visible;
      if (!visible) return;
      const shown = (flat || pct) ? radius.map(r => (r + flat) * (1 + pct / 100)) : radius;
      V.el.textContent = fmt(shown);
      // Gold means a visible value changed. A zero-base line revealed by a
      // Talent/Scepter/Shard is a newly enabled AoE mode, not a changed value.
      const baseVisible = Math.max(...V.base) > 0;
      const upgradedUp = baseVisible && (
        (up.talent  && (V.talent.some(n => n)  || V.talentSet.length || V.talentGlobal.length))  ||
        (up.scepter && (V.scepter.some(n => n) || V.scepterSet.length)) ||
        (up.shard   && (V.shard.some(n => n)   || V.shardSet.length))
      );
      V.el.classList.toggle('aoe-val-up', !!(flat || pct || upgradedUp));
    });
    // Hide a line whose every value is hidden, then an ability with no visible
    // line; surface the active-upgrade mini-markers the ability carries.
    linesSet.forEach(L => {
      const anyVal = L.vals.some(v => !v.hidden);
      L.line.hidden = !anyVal;
    });
    abilities.forEach(A => {
      const ab = A.ab;
      const cell = A.cell;
      const dash = A.dash;
      const granted = ab.dataset.grantedBy;
      const grantedHidden = granted && !up[granted];
      const anyVisible = !grantedHidden && A.lines.some(l => !l.hidden);
      if (cell && !opts.measure) cell.classList.toggle('aoe-cell-placeholder', !anyVisible);
      if (dash) dash.hidden = anyVisible;
      ['talent', 'scepter', 'shard'].forEach(t => {
        const mark = A.marks[t];
        if (mark) mark.hidden = !(up[t] && ab.dataset['has' + t[0].toUpperCase() + t.slice(1)] === '1' && anyVisible);
      });
    });
    // Hero rows are always visible — empty/filter-hidden slots show dashes.

    // After show/hide, force Chrome to repaint sticky cell borders at new position.
    // translateZ(0) promotes the cell to a GPU compositing layer for one frame,
    // then the rAF clears it — this is cheaper than explicit height sync and avoids
    // the height-mismatch bug it caused.
    if (!opts.measure) requestAnimationFrame(() => {
      table.querySelectorAll('td.aoe-name').forEach(td => {
        td.style.transform = 'translateZ(0)';
      });
      requestAnimationFrame(() => {
        table.querySelectorAll('td.aoe-name').forEach(td => {
          td.style.transform = '';
        });
      });
    });
    if (!opts.measure) markVisibleEdgeRows();
  }

  itemBtns.forEach(btn => btn.addEventListener('click', () => {
    const kind = btn.dataset.aoeKind;
    const amount = Number(btn.dataset.aoeAmount) || 0;
    const on = btn.getAttribute('aria-pressed') === 'true';
    if (kind === 'flat') {
      itemBtns.filter(b => b.dataset.aoeKind === 'flat')
        .forEach(b => b.setAttribute('aria-pressed', 'false'));
      flat = on ? 0 : amount;
      if (!on) btn.setAttribute('aria-pressed', 'true');
    } else {
      pct = on ? 0 : amount;
      btn.setAttribute('aria-pressed', on ? 'false' : 'true');
    }
    recompute();
  }));

  upBtns.forEach(btn => btn.addEventListener('click', () => {
    const key = btn.dataset.aoeUpgrade;
    const on = btn.getAttribute('aria-pressed') === 'true';
    up[key] = !on;
    btn.setAttribute('aria-pressed', on ? 'false' : 'true');
    recompute();
  }));

  recompute();   // initial render: upgrades OFF by default
  window.addEventListener('mr:filter-changed', markVisibleEdgeRows);
  // Freeze column widths after first render so ability cells appearing/disappearing
  // (shard/scepter/talent toggle) cannot cause horizontal layout shift.
  requestAnimationFrame(() => {
    let total = 0;
    table.querySelectorAll('thead th').forEach(th => {
      const w = th.offsetWidth;
      total += w;
      th.style.width = w + 'px';
      th.style.minWidth = w + 'px';
      th.style.maxWidth = w + 'px';
    });
    table.style.width = total + 'px';
    table.style.tableLayout = 'fixed';
  });

  // Pin the filter toolbar at the top of the scroll box and drop the table
  // header just below it (exception to the usual "toolbar scrolls away" rule).
  const toolbar = document.querySelector('.aoe-toolbar');
  if (toolbar) {
    const heads = [...table.querySelectorAll('thead th')];
    const offsetHead = () => {
      const h = Math.round(toolbar.getBoundingClientRect().height);
      heads.forEach(th => { th.style.top = h + 'px'; });
    };
    offsetHead();
    window.addEventListener('resize', offsetHead, { passive: true });
  }
})();
