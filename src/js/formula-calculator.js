

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
  const W = 480, H = 190, PL = 44, PR = 14, PT = 10, PB = 40;
  const fmt = (x) => (Math.round(x * 10) / 10).toString();
  const r1 = (x) => Math.round(x * 10) / 10;
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
        const v = parseFloat(i.value);
        e[i.dataset.var] = isFinite(v) ? v : parseFloat(i.dataset.default);
      });
      return e;
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
      const pts = (vals) => xs.map((x, i) => r1(sx(x)) + ',' + r1(sy(vals[i]))).join(' ');
      s += '<polyline class="fx-line fx-line-old" points="' + pts(po) + '"/>';
      s += '<polyline class="fx-line fx-line-new" points="' + pts(pn) + '"/>';
      const cur = e[cv];
      if (cur >= lo && cur <= hi) {
        const cx = r1(sx(cur));
        s += '<line class="fx-ruler" x1="' + cx + '" x2="' + cx + '" y1="' + PT + '" y2="' + base + '"/>' +
          '<rect class="fx-dot fx-dot-old" x="' + (cx - 3) + '" y="' + r1(r1(sy(call(fOld, e))) - 3) + '" width="6" height="6"/>' +
          '<rect class="fx-dot fx-dot-new" x="' + (cx - 3) + '" y="' + r1(r1(sy(call(fNew, e))) - 3) + '" width="6" height="6"/>';
      }
      svg.innerHTML = s;
    }
    function recalc() {
      const e = env();
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
    inputs.forEach((i) => i.addEventListener('input', recalc));
    if (!svg || !cv) return;
    const cvInput = inputs.find((i) => i.dataset.var === cv);
    function pick(ev) {      // the chart's x under the pointer -> the chart variable
      const r = svg.getBoundingClientRect();
      const scale = Math.min(r.width / W, r.height / H);
      const x = (ev.clientX - r.left - (r.width - W * scale) / 2) / scale;
      const c = Math.max(lo, Math.min(hi, Math.round(lo + (x - PL) / (W - PL - PR) * (hi - lo))));
      if (cvInput && String(c) !== cvInput.value) { cvInput.value = c; recalc(); }
    }
    let down = false;
    svg.addEventListener('pointerdown', (ev) => { down = true; svg.setPointerCapture(ev.pointerId); pick(ev); });
    svg.addEventListener('pointermove', (ev) => { if (down) pick(ev); });
    svg.addEventListener('pointerup', () => { down = false; });
    svg.addEventListener('pointercancel', () => { down = false; });
  });
})();
