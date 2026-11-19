

/* ---- Formula calculator (formula_change) ----
   Each `.formula-change[data-fx-old]` has a number input; on change we re-evaluate
   both formulas for every example row (the `fixed` variable = the input value,
   the `vary` variable = the row's data-h) and refresh the gold cell + Δ% badge.
   Patch pages only; mirrors b()/gradient_class colouring. */
(function () {
  const blocks = document.querySelectorAll('.formula-change[data-fx-old]:not(.formula-live)');
  if (!blocks.length) return;
  const fmt = (x) => (Math.round(x * 10) / 10).toString();
  function gradClass(mag, isBuff) {
    const p = isBuff ? 'buff' : 'nerf';
    if (mag <= 5) return p + '1';
    if (mag <= 10) return p + '2';
    if (mag <= 15) return p + '3';
    if (mag <= 20) return p + '4';
    if (mag <= 25) return p + '5';
    if (mag <= 33) return p + '6';
    if (mag <= 45) return p + '7';
    if (mag <= 60) return p + '8';
    if (mag <= 80) return p + '9';
    return p + '10';
  }
  function pctBadge(o, n, lower) {
    let inner;
    if (o === 0 || n === o) {
      inner = '<span class="badge neutral">0%</span>';
    } else {
      const raw = (n - o) / o * 100;
      const isBuff = lower ? (n < o) : (n > o);
      const disp = (n > o ? '+' : '-') + fmt(Math.abs(raw)) + '%';
      inner = '<span class="badge ' + gradClass(Math.abs(raw), isBuff) + '">' + disp + '</span>';
    }
    return '<span class="badge-group">' + inner + '</span>';   // plain text, no pill box
  }
  blocks.forEach((block) => {
    const input = block.querySelector('.formula-input');
    if (!input) return;
    const invar = block.dataset.fxInvar;
    const varyvar = block.dataset.fxVaryvar;
    const def = parseFloat(block.dataset.fxDefault);
    const lower = block.dataset.fxLower === '1';
    let fOld, fNew;
    // `^` = exponentiation (Valve writes x^2), not JS bitwise xor.
    const toJs = (e) => e.replace(/\^/g, '**');
    try {
      // Formulas are author-authored (data attributes we emit), so Function() is safe here.
      fOld = new Function(invar, varyvar, 'return (' + toJs(block.dataset.fxOld) + ');');
      fNew = new Function(invar, varyvar, 'return (' + toJs(block.dataset.fxNew) + ');');
    } catch (e) { return; }
    const rows = [...block.querySelectorAll('tr[data-h]')];
    function recalc() {
      let nv = parseFloat(input.value);
      if (!isFinite(nv)) nv = def;
      rows.forEach((tr) => {
        const h = parseFloat(tr.dataset.h);
        let o, n;
        try { o = fOld(nv, h); n = fNew(nv, h); } catch (e) { return; }
        const isOld = tr.closest('.formula-pane-old');
        const gold = tr.querySelector('.fx-gold');
        if (gold) gold.textContent = fmt(isOld ? o : n);
        const pc = tr.querySelector('.fx-pct');
        if (pc && !isOld) pc.innerHTML = pctBadge(o, n, lower);   // Δ% only in NEW pane
      });
    }
    input.addEventListener('input', recalc);
  });
})();

/* ---- Live formula (formula_change inputs= + chart=) ----
   `.formula-live` has a field for every variable (data-var / data-default), the OLD and NEW result
   (.fx-val-old / .fx-val-new + Δ%) and an SVG chart of both formulas over the chart variable
   (data-fx-chart, lo..hi). Every change redraws both. Pressing / dragging on the chart sets the
   chart variable. The geometry mirrors patch/formula_rows.py (FX_*): change both together. */
(function () {
  const blocks = document.querySelectorAll('.formula-live[data-fx-vars]');
  if (!blocks.length) return;
  const W = 480, H = 190, PL = 44, PR = 14, PT = 22, PB = 40;
  const fmt = (x) => (Math.round(x * 10) / 10).toString();
  const r1 = (x) => Math.round(x * 10) / 10;
  // the stretches where one curve stays above the other, split where they cross: [sign, [[x, old, new] …]]
  function gapPieces(xs, po, pn) {
    const pieces = [];
    for (let i = 0; i < xs.length - 1; i++) {
      const a0 = [xs[i], po[i], pn[i]], b1 = [xs[i + 1], po[i + 1], pn[i + 1]];
      const d0 = a0[2] - a0[1], d1 = b1[2] - b1[1];
      let segs = [[a0, b1]];
      if (d0 * d1 < 0) {
        const t = d0 / (d0 - d1), xc = a0[0] + t * (b1[0] - a0[0]), yc = a0[1] + t * (b1[1] - a0[1]);
        const c = [xc, yc, yc];
        segs = [[a0, c], [c, b1]];
      }
      segs.forEach(([a, b]) => {
        const mid = (a[2] - a[1]) + (b[2] - b[1]);
        const sign = (mid > 0) - (mid < 0);
        if (!sign) return;
        const last = pieces[pieces.length - 1];
        if (last && last[0] === sign && last[1][last[1].length - 1] === a) last[1].push(b);
        else pieces.push([sign, [a, b]]);
      });
    }
    return pieces;
  }
  // the ruler, a dot on each curve and its number (upper number above its dot, lower one below)
  function marker(cxRaw, yo, yn, o, n, base) {
    const cx = r1(cxRaw);
    const right = cx < W - PR - 70;
    const tx = right ? cx + 7 : cx - 7, anchor = right ? 'start' : 'end';
    const newUp = yn <= yo;
    const lab = (cls, y, v, up) => '<text class="fx-mark fx-mark-' + cls + '" x="' + tx + '" y="' +
      r1(y + (up ? -6 : 12)) + '" text-anchor="' + anchor + '">' + fmt(v) + '</text>';
    return '<line class="fx-ruler" x1="' + cx + '" x2="' + cx + '" y1="' + PT + '" y2="' + base + '"/>' +
      '<rect class="fx-dot fx-dot-old" x="' + r1(cx - 3) + '" y="' + r1(r1(yo) - 3) + '" width="6" height="6"/>' +
      '<rect class="fx-dot fx-dot-new" x="' + r1(cx - 3) + '" y="' + r1(r1(yn) - 3) + '" width="6" height="6"/>' +
      lab('old', yo, o, !newUp) + lab('new', yn, n, newUp);
  }
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  function nice(lo, hi, n) {
    if (hi <= lo) hi = lo + 1;
    const raw = (hi - lo) / n;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw);
    return [Math.floor(lo / step) * step, Math.ceil(hi / step) * step, step];
  }
  function xticks(lo, hi) {
    const out = [];
    if (hi - lo <= 10) { for (let v = lo; v <= hi; v++) out.push(v); return out; }
    const every = hi - lo <= 60 ? 5 : 10;
    out.push(lo);
    for (let v = lo + 1; v <= hi; v++) if (v % every === 0) out.push(v);
    return out;
  }
  function gradClass(mag, isBuff) {
    const caps = [5, 10, 15, 20, 25, 33, 45, 60, 80];
    const i = caps.findIndex((c) => mag <= c);
    return (isBuff ? 'buff' : 'nerf') + (i < 0 ? 10 : i + 1);
  }
  function pctBadge(o, n, lower) {
    let inner;
    if (o === 0 || n === o) inner = '<span class="badge neutral">0%</span>';
    else {
      const raw = (n - o) / o * 100;
      const isBuff = lower ? (n < o) : (n > o);
      inner = '<span class="badge ' + gradClass(Math.abs(raw), isBuff) + '">' +
        (n > o ? '+' : '-') + fmt(Math.abs(raw)) + '%</span>';
    }
    return '<span class="badge-group">' + inner + '</span>';   // plain text, no pill box
  }
  blocks.forEach((block) => {
    const ds = block.dataset;
    const vars = ds.fxVars.split(',');
    const lower = ds.fxLower === '1';
    const toJs = (e) => e.replace(/\^/g, '**');   // `^` = exponentiation (Valve writes x^2)
    let fOld, fNew;
    try {
      // Formulas are author-authored (data attributes we emit), so Function() is safe here.
      fOld = new Function(...vars, 'return (' + toJs(ds.fxOld) + ');');
      fNew = new Function(...vars, 'return (' + toJs(ds.fxNew) + ');');
    } catch (e) { return; }
    const inputs = [...block.querySelectorAll('.formula-input[data-var]')];
    const valOld = block.querySelector('.fx-val-old');
    const valNew = block.querySelector('.fx-val-new');
    const svg = block.querySelector('.fx-svg');
    const cv = ds.fxChart, lo = parseInt(ds.fxLo, 10), hi = parseInt(ds.fxHi, 10);
    function env() {
      const e = {};
      inputs.forEach((i) => {
        if (i.dataset.var in e) return;            // a variable's field is in both panes: they hold the same value
        const v = parseFloat(i.value);
        e[i.dataset.var] = isFinite(v) ? v : parseFloat(i.dataset.default);
      });
      return e;
    }
    // a field typed into: its twin in the other pane follows (owner 2026-11-19: the fields inside the formulas)
    function sync(src) {
      inputs.forEach((i) => { if (i !== src && i.dataset.var === src.dataset.var) i.value = src.value; });
    }
    const call = (f, e) => f(...vars.map((v) => e[v]));
    function draw(e) {
      const xs = [], po = [], pn = [];
      for (let x = lo; x <= hi; x++) {
        const ex = Object.assign({}, e, { [cv]: x });
        xs.push(x); po.push(call(fOld, ex)); pn.push(call(fNew, ex));
      }
      const all = po.concat(pn);
      const [y0, y1, step] = nice(Math.min(...all), Math.max(...all), 4);
      const pw = W - PL - PR, ph = H - PT - PB, base = H - PB;
      const sx = (x) => PL + (x - lo) / (hi - lo) * pw;
      const sy = (y) => PT + (y1 - y) / (y1 - y0) * ph;
      let s = '';
      for (let y = y0; y <= y1 + step / 2; y += step) {
        const yy = r1(sy(y));
        s += '<line class="fx-grid" x1="' + PL + '" x2="' + (W - PR) + '" y1="' + yy + '" y2="' + yy + '"/>' +
          '<text class="fx-tick fx-tick-y" x="' + (PL - 6) + '" y="' + yy + '">' + fmt(y) + '</text>';
      }
      xticks(lo, hi).forEach((x) => {
        const xx = r1(sx(x));
        s += '<line class="fx-grid" x1="' + xx + '" x2="' + xx + '" y1="' + PT + '" y2="' + base + '"/>' +
          '<text class="fx-tick fx-tick-x" x="' + xx + '" y="' + (base + 14) + '">' + x + '</text>';
      });
      s += '<text class="fx-axis" x="' + (PL + pw / 2) + '" y="' + (H - 4) + '">' + esc(ds.fxLabel || '') + '</text>';
      if (ds.fxUnit) s += '<text class="fx-axis fx-axis-y" x="' + (PL - 6) + '" y="' + (PT - 10) + '">' + esc(ds.fxUnit) + '</text>';
      const p = (x, y) => r1(sx(x)) + ',' + r1(sy(y));
      gapPieces(xs, po, pn).forEach(([sign, seg]) => {   // the gap between the curves: green better, red worse
        const better = lower ? sign < 0 : sign > 0;
        const ring = seg.map((q) => p(q[0], q[2])).concat(seg.slice().reverse().map((q) => p(q[0], q[1])));
        s += '<polygon class="fx-gap ' + (better ? 'fx-gain' : 'fx-loss') + '" points="' + ring.join(' ') + '"/>';
      });
      s += '<polyline class="fx-line fx-line-old" points="' + xs.map((x, i) => p(x, po[i])).join(' ') + '"/>';
      s += '<polyline class="fx-line fx-line-new" points="' + xs.map((x, i) => p(x, pn[i])).join(' ') + '"/>';
      const cur = e[cv];
      if (cur >= lo && cur <= hi) {
        const o = call(fOld, e), n = call(fNew, e);
        s += marker(sx(cur), sy(o), sy(n), o, n, base);
      }
      svg.innerHTML = s;
    }
    function recalc(over) {      // over: a level shown while the mouse is on the chart, the field untouched
      const e = env();
      if (over !== undefined) e[cv] = over;
      let o, n;
      try { o = call(fOld, e); n = call(fNew, e); } catch (err) { return; }
      if (valOld) valOld.textContent = fmt(o);
      if (valNew) {
        valNew.textContent = fmt(n);
        const pct = valNew.parentNode.querySelector('.badge-group');
        if (pct) pct.outerHTML = pctBadge(o, n, lower);
      }
      if (svg && cv) draw(e);
    }
    inputs.forEach((i) => i.addEventListener('input', () => { sync(i); recalc(); }));
    if (!svg || !cv) return;
    const cvInput = inputs.find((i) => i.dataset.var === cv);
    function levelAt(ev) {   // the chart's x under the pointer -> a value of the chart variable
      const r = svg.getBoundingClientRect();
      const scale = Math.min(r.width / W, r.height / H);
      const x = (ev.clientX - r.left - (r.width - W * scale) / 2) / scale;
      return Math.max(lo, Math.min(hi, Math.round(lo + (x - PL) / (W - PL - PR) * (hi - lo))));
    }
    function pick(ev) {
      const c = levelAt(ev);
      if (cvInput && String(c) !== cvInput.value) { cvInput.value = c; sync(cvInput); recalc(); }
    }
    let down = false, shown = null;
    svg.addEventListener('pointerdown', (ev) => { down = true; shown = null; svg.setPointerCapture(ev.pointerId); pick(ev); });
    svg.addEventListener('pointermove', (ev) => {
      if (down) { pick(ev); return; }
      if (ev.pointerType !== 'mouse') return;
      const c = levelAt(ev);                     // a mouse over the chart shows that level until it leaves
      if (c !== shown) { shown = c; recalc(c); }
    });
    svg.addEventListener('pointerup', () => { down = false; });
    svg.addEventListener('pointercancel', () => { down = false; });
    svg.addEventListener('pointerleave', () => { if (!down && shown !== null) { shown = null; recalc(); } });
  });
})();
