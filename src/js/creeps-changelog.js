
// ---- CREEPS TABLE: per-stat changelog tooltip (HP / Armor / Mana / Magres) ----
(function() {
  const cells = document.querySelectorAll('td[data-hist], td[data-name]');
  if (!cells.length) return;

  let tip = null;
  function ensureTip() {
    if (!tip) {
      tip = document.createElement('div');
      tip.className = 'stat-hist-tip';
      document.body.appendChild(tip);
    }
    return tip;
  }

  // "23.02.2022" -> "23.02.22"
  function shortDate(d) {
    const p = (d || '').split('.');
    if (p.length === 3 && p[2].length === 4) p[2] = p[2].slice(2);
    return p.join('.');
  }
  // Mean of a slash/space value ("40/36/32/26" -> 33.5, "12.0" -> 12).
  function meanOf(s) {
    const nums = String(s).split(/[\/\s]+/)
      .map(x => parseFloat(x.replace(',', '.'))).filter(isFinite);
    return nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : NaN;
  }
  // Colour reflects buff/nerf, not raw direction: for lower-is-better stats
  // (cooldown, mana, BAT) a DROP is the buff (green). The % keeps its real sign.
  function pctHtml(ov, nv, lowerBetter) {
    const o = meanOf(ov), n = meanOf(nv);
    if (!isFinite(o) || !isFinite(n) || o === 0) return '';
    // Divide by |o| so a negative baseline keeps the real direction:
    // armor -1 → 0 is a +100% gain (a buff), not -100%.
    const pct = (n - o) / Math.abs(o) * 100;
    const good = lowerBetter ? pct < 0 : pct > 0;
    const cls = pct === 0 ? 'flat' : (good ? 'up' : 'down');
    const sign = pct > 0 ? '+' : '';
    let num = pct.toFixed(1);
    if (num.endsWith('.0')) num = num.slice(0, -2);  // 50.0 → 50, 1900.0 → 1900
    return ' <span class="stat-pct ' + cls + '">' + sign + num + '%</span>';
  }
  // One history entry → its old/new values (display + numeric) + polarity, or
  // null for non-value markers (A added / R removed / P replaced) which carry
  // no comparable value. 'C' computed cells carry pretty display (p3/p4) AND
  // raw numerics (p5/p6) so the % isn't skewed by thousands formatting.
  function valEntry(p) {
    const k = p[2];
    if (k === 'V') return { dispOld: p[3], dispNew: p[4], numOld: p[3], numNew: p[4], lb: p[5] === 'lo' };
    if (k === 'F') return { dispOld: p[4], dispNew: p[5], numOld: p[4], numNew: p[5], lb: p[6] === 'lo' };
    if (k === 'C') return { dispOld: p[3], dispNew: p[4], numOld: p[5], numNew: p[6], lb: p[7] === 'lo' };
    if (k === 'N') return { dispOld: p[3], dispNew: p[4], numOld: p[3], numNew: p[4], lb: false };
    return null;
  }
  // Overall first-observed → today summary, shown at the TOP of the tooltip
  // (above the newest patch) with a divider below. Needs >1 value change;
  // scans past A/R/P markers to the first & last real value entries.
  function netSummary(entries) {
    const vals = entries.map(e => valEntry(e.split('|'))).filter(Boolean);
    if (vals.length < 2) return '';
    const first = vals[0], last = vals[vals.length - 1];
    const o = meanOf(first.numOld), n = meanOf(last.numNew);
    if (!isFinite(o) || !isFinite(n) || o === 0) return '';
    const pct = (n - o) / Math.abs(o) * 100;
    // Net 0% (value drifted then returned to its start) is still shown — flat.
    const cls = pct === 0 ? 'flat' : ((last.lb ? pct < 0 : pct > 0) ? 'up' : 'down');
    const sign = pct > 0 ? '+' : '';
    let num = pct.toFixed(1);
    if (num.endsWith('.0')) num = num.slice(0, -2);
    return '<div class="stat-net"><span class="stat-net-label">overall</span>'
         + first.dispOld + ' → ' + last.dispNew
         + ' <span class="stat-pct ' + cls + '">' + sign + num + '%</span></div>';
  }
  // Parse one entry → { patch, date, line }. Format: patch|date|kind|...parts
  //   V old new pol          stat value change
  //   F label old new pol    ability value change
  //   A name / R name / P old new  ability added / removed / replaced
  function entryParts(e) {
    const p = e.split('|');
    const patch = p[0], date = p[1], kind = p[2];
    let line;
    if (kind === 'A') {
      line = p[3] + ' <span class="chg-tag added">ADDED</span>';
    } else if (kind === 'R') {
      line = p[3] + ' <span class="chg-tag removed">REMOVED</span>';
    } else if (kind === 'P') {
      line = p[3] + ' <span class="chg-cycle">⇄</span> ' + p[4]
           + ' <span class="chg-tag replaced">REPLACED</span>';
    } else if (kind === 'F') {
      line = '<span class="chg-label">' + p[3] + ':</span> ' + p[4] + ' → '
           + p[5] + pctHtml(p[4], p[5], p[6] === 'lo');
    } else if (kind === 'N') {
      // No-percentage value change (computed columns): show old → new only.
      line = p[3] + ' → ' + p[4];
    } else if (kind === 'C') {
      // Computed column: pretty short display (p3→p4) with a % delta derived
      // from the raw values (p5, p6) so scaling never skews it. p7 = polarity.
      line = p[3] + ' → ' + p[4] + pctHtml(p[5], p[6], p[7] === 'lo');
    } else {
      // 'V' stat value (patch|date|V|old|new|pol), or legacy patch|date|old|new
      const isV = kind === 'V';
      const ov = isV ? p[3] : p[2];
      const nv = isV ? p[4] : p[3];
      line = ov + ' → ' + nv + pctHtml(ov, nv, isV && p[5] === 'lo');
    }
    return { patch: patch, date: date, line: line };
  }

  function show(td) {
    const entries = (td.dataset.hist || '').split(';').filter(Boolean);
    const name = td.dataset.name || '';
    if (!entries.length && !name) return;
    const el = ensureTip();
    // Group changes from the same patch under one header.
    const groups = [];
    entries.forEach(e => {
      const ep = entryParts(e);
      const g = groups[groups.length - 1];
      if (g && g.patch === ep.patch) g.lines.push(ep.line);
      else groups.push({ patch: ep.patch, date: ep.date, lines: [ep.line] });
    });
    groups.reverse();  // newest patch on top, oldest at the bottom
    // Ability name as a centered header above the changelog (if any).
    const nameHtml = name ? '<div class="abil-tip-name">' + name + '</div>' : '';
    // Net first→today summary at the very top (gold test: cells flagged data-net).
    const netHtml = (td.dataset.net !== undefined) ? netSummary(entries) : '';
    // One row per change: patch · old → new % · date, aligned in columns — half the height of a header line
    // over each change (owner 2026-10-25: Guardian Greaves' price history was too long a list)
    el.innerHTML = nameHtml + netHtml + '<div class="stat-chg-grid">' + groups.map((g, gi) =>
      g.lines.map((l, i) => {
        const sep = (gi && !i) ? ' grp-start' : '';       // a thin line above every patch but the newest
        return '<span class="chg-patch' + sep + '">' + (i ? '' : g.patch) + '</span>'
          + '<span class="stat-chg-line' + sep + '">' + l + '</span>'
          + '<span class="chg-date' + sep + '">' + (i ? '' : shortDate(g.date)) + '</span>';
      }).join('')
    ).join('') + '</div>';
    el.classList.add('is-visible');
    const r = td.getBoundingClientRect();
    const tr = el.getBoundingClientRect();
    let left = r.left + r.width / 2 - tr.width / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tr.width - 8));
    el.style.left = left + 'px';
    // Vertical placement: prefer above the cell, flip below if it would clip
    // the top. For tall tooltips (taller than the space on either side —
    // e.g. Guardian Greaves' long changelog) clamp into the viewport so the
    // box never runs off-screen; the CSS max-height + overflow lets the
    // overflow scroll. Always keep an 8px margin top and bottom.
    const margin = 8;
    const spaceAbove = r.top - margin;
    const spaceBelow = window.innerHeight - r.bottom - margin;
    let top;
    if (tr.height <= spaceAbove) {
      top = r.top - tr.height - margin;            // fits above
    } else if (tr.height <= spaceBelow) {
      top = r.bottom + margin;                     // fits below
    } else {
      // Doesn't fit either side — pin to whichever side has more room and
      // let it clamp to the viewport edge (CSS caps its height).
      top = spaceAbove >= spaceBelow ? margin : (r.bottom + margin);
    }
    top = Math.max(margin, Math.min(top, window.innerHeight - tr.height - margin));
    if (top < margin) top = margin;                // last-resort clamp
    el.style.top = top + 'px';
  }
  function hide() { if (tip) tip.classList.remove('is-visible'); }

  // Event delegation (not per-cell binding): cells can be removed/re-inserted
  // by the ability-merge logic, so listeners bound at load would be lost on
  // the restored cells. Delegation on the table covers any current cell.
  // th[data-hist]: Hero Stats STR / AGI / INT / Attr headers — what one point gave by patch (2026-10-22)
  const SEL = 'td[data-hist], td[data-name], th[data-hist], .mr-const[data-hist]';
  // Bind to every table OR standalone history-chip that may carry data-hist:
  // creeps-table (neutral creeps), mr-table (mana items), and the constants
  // chips in the page blurb.
  const targets = [
    ...document.querySelectorAll('.creeps-table, .mr-table'),
    ...document.querySelectorAll('.mr-const[data-hist]'),
  ];
  let curTd = null;
  targets.forEach(tbl => {
    tbl.addEventListener('mouseover', e => {
      // A `?` qhint badge inside a history cell has its own tooltip — let it
      // win and suppress the cell's changelog popup while hovering it.
      if (e.target.closest('.qhint')) { if (curTd) { curTd = null; hide(); } return; }
      const td = e.target.closest(SEL);
      if (td && td !== curTd) { curTd = td; show(td); }
    });
    tbl.addEventListener('mouseout', e => {
      const td = e.target.closest(SEL);
      if (!td) return;
      const to = e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest(SEL);
      if (to !== td) { curTd = null; hide(); }
    });
  });
  window.addEventListener('scroll', hide, { passive: true });
})();
