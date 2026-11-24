// Research mock-up: draws the Weights mode of heroes_dyn / items_dyn as ONE smooth curve per row
// over the site's own table. Variant chosen by the buttons it adds (or ?v=A|B|C). Not site code.
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const H = 28, MID = H / 2, AMP = MID - 3, MIN_SCALE = 1.5;
  const VARIANTS = {
    A: 'Cumulative',   // running total since the first visible patch
    B: 'Wave',         // per-patch value, smooth through zero between patches
  };
  let variant = (new URLSearchParams(location.search).get('v') || 'A').toUpperCase();
  if (!VARIANTS[variant]) variant = 'A';
  let lastSig = '';

  const mk = (tag, attrs) => {
    const el = document.createElementNS(NS, tag);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  };

  function smooth(pts) {   // Catmull-Rom through the points, as cubic Beziers
    let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(i - 1, 0)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(i + 2, pts.length - 1)];
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += ` C${c1[0].toFixed(1)},${c1[1].toFixed(1)} ${c2[0].toFixed(1)},${c2[1].toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
    }
    return d;
  }

  // strength -> colour: grey at 0, full site green / red at |w| >= 3
  function tint(w) {
    const a = Math.min(1, Math.sqrt(Math.abs(w) / 3));
    const base = [170, 165, 155], tgt = w > 0 ? [62, 178, 96] : [188, 92, 120];
    return `rgb(${base.map((b, i) => Math.round(b + (tgt[i] - b) * a)).join(',')})`;
  }

  function rowData(tr) {
    const tds = [...tr.children].filter(td => td.matches('td.hd-cell, td.he, td.ha') && !td.classList.contains('hd-spacer'))
      .filter(td => td.getClientRects().length > 0);
    return tds.map(td => {
      const c = td.querySelector('.w-line .dyn-cell');
      return { td, w: c ? (parseFloat(c.dataset.w) || 0) : 0, touched: !!c };
    });
  }

  function drawRow(tr, idx) {
    tr.querySelectorAll('svg.cm-curve').forEach(x => x.remove());
    const cells = rowData(tr);
    if (!cells.length) return;
    const first = cells[0].td, r0 = first.getBoundingClientRect();
    const xs = cells.map(c => { const r = c.td.getBoundingClientRect(); return r.left - r0.left + r.width / 2; });
    const width = cells[cells.length - 1].td.getBoundingClientRect().right - r0.left;
    let vals;
    if (variant === 'B') vals = cells.map(c => c.w);
    else { let acc = 0; vals = cells.map(c => (acc += c.w)); }
    const scale = Math.max(MIN_SCALE, ...vals.map(Math.abs));
    const y = v => MID - Math.max(-1, Math.min(1, v / scale)) * AMP;
    let pts = vals.map((v, i) => [xs[i], y(v)]);
    if (variant === 'B') pts = [[0, MID], ...pts, [width, MID]];
    else pts = [[0, pts[0][1]], ...pts, [width, pts[pts.length - 1][1]]];
    const path = smooth(pts);
    const id = 'cm' + idx;
    const svg = mk('svg', { class: 'cm-curve', width: width.toFixed(0), height: H, viewBox: `0 0 ${width.toFixed(0)} ${H}` });
    // ONE colour rule for every variant: colour = the change of THAT patch (green buff, red nerf).
    // Quiet stretches (no change) are a dim neutral line, no fill.
    svg.appendChild(mk('path', { d: path, class: 'cm-quiet' }));
    const half = cells.length > 1 ? (xs[1] - xs[0]) / 2 : 20;
    cells.forEach((c, i) => {
      if (!c.touched || !c.w) return;
      const side = c.w > 0 ? 'up' : 'down';
      // A: the rise / drop INTO this patch; B: the hump around this patch
      // B: a changed neighbour shares the border at the midpoint; a quiet neighbour lets the
      // coloured curve run all the way down to the axis at its centre, so nothing hangs in the air
      const busy = j => j >= 0 && j < cells.length && cells[j].touched && cells[j].w;
      const bx0 = i === 0 ? 0 : (busy(i - 1) ? xs[i] - half : xs[i - 1]);
      const bx1 = i === cells.length - 1 ? width : (busy(i + 1) ? xs[i] + half : xs[i + 1]);
      const x0 = variant === 'B' ? bx0 : (i ? xs[i - 1] : 0);
      const x1 = variant === 'B' ? bx1 : xs[i];
      const cp = mk('clipPath', { id: `${id}k${i}` });
      cp.appendChild(mk('rect', { x: x0.toFixed(1), y: -4, width: (x1 - x0).toFixed(1), height: H + 8 }));
      svg.appendChild(cp);
      if (variant === 'B') svg.appendChild(mk('path', { d: `${path} L${width},${MID} L0,${MID} Z`, class: 'cm-fill ' + side, 'clip-path': `url(#${id}k${i})` }));
      svg.appendChild(mk('path', { d: path, class: 'cm-line ' + side, 'clip-path': `url(#${id}k${i})` }));
      const yy = variant === 'B' ? y(c.w) : y(vals[i]);
      svg.appendChild(mk('circle', { cx: xs[i].toFixed(1), cy: yy.toFixed(1), r: 2.4, class: 'cm-dot ' + side }));
    });
    first.classList.add('cm-host');
    first.appendChild(svg);
  }

  function draw(force) {
    const table = document.querySelector('.heroes-dyn-table');
    if (!table) return;
    const on = table.classList.contains('w-mode');
    document.body.classList.toggle('cm-on', on);
    const sig = [variant, on, table.querySelectorAll('.w-line .dyn-cell').length,
      table.querySelectorAll('tbody tr').length, innerWidth, document.querySelectorAll('td:not([style*="none"])').length].join('|');
    if (!force && sig === lastSig) return;
    lastSig = sig;
    table.querySelectorAll('svg.cm-curve').forEach(x => x.remove());
    if (!on) return;
    [...table.querySelectorAll('tbody tr')].forEach((tr, i) => {
      if (tr.getClientRects().length) drawRow(tr, i);
    });
  }

  function addButtons() {
    const bar = document.createElement('div');
    bar.className = 'cm-bar';
    bar.innerHTML = '<span>Curve mock-up:</span>' + Object.entries(VARIANTS).map(([k, t]) =>
      `<button type="button" class="hs-attack-filter${k === variant ? ' active' : ''}" data-v="${k}">${k}. ${t}</button>`).join('');
    bar.addEventListener('click', e => {
      const b = e.target.closest('button[data-v]');
      if (!b) return;
      variant = b.dataset.v;
      bar.querySelectorAll('button').forEach(x => x.classList.toggle('active', x === b));
      const wb = document.getElementById('dyn-weights-btn');
      if (wb && !document.querySelector('.heroes-dyn-table.w-mode')) wb.click();
      draw(true);
    });
    document.body.prepend(bar);
  }

  const css = document.createElement('style');
  css.textContent = `
    .cm-bar{position:fixed;right:12px;bottom:12px;z-index:9999;display:flex;gap:6px;align-items:center;
      padding:6px 8px;background:#1b1712;border:1px solid #8a6d3b;font-size:12px;color:#e8c070}
    body.cm-on .heroes-dyn-table svg.dyn-wl:not(.cm-curve){visibility:hidden}
    td.cm-host{position:relative}
    svg.cm-curve{position:absolute;left:0;top:50%;margin-top:-${MID}px;pointer-events:none;overflow:visible;z-index:2}
    .cm-quiet{fill:none;stroke:rgba(205,199,187,.3);stroke-width:1}
    body.cm-on .heroes-dyn-table.w-mode td.hd-cell.hd-empty::after,
    body.cm-on .heroes-dyn-table.w-mode td.he::after{display:none}
    .cm-dot.up{fill:rgb(62,178,96)} .cm-dot.down{fill:rgb(188,92,120)}
    .cm-fill.up{fill:rgba(62,178,96,.22)} .cm-fill.down{fill:rgba(188,92,120,.22)}
    .cm-line{fill:none;stroke-width:2;stroke-linecap:round}
    .cm-line.up{stroke:rgb(62,178,96)} .cm-line.down{stroke:rgb(188,92,120)}`;
  document.head.appendChild(css);

  function start() {
    addButtons();
    const wb = document.getElementById('dyn-weights-btn');
    if (wb && !document.querySelector('.heroes-dyn-table.w-mode')) wb.click();
    setInterval(() => draw(false), 400);
    addEventListener('resize', () => draw(true));
  }
  if (document.readyState === 'complete') start(); else addEventListener('load', () => setTimeout(start, 300));
})();
