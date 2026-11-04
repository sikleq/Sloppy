

/* ---- Formula calculator (formula_change) ----
   Each `.formula-change[data-fx-old]` has a number input; on change we re-evaluate
   both formulas for every example row (the `fixed` variable = the input value,
   the `vary` variable = the row's data-h) and refresh the gold cell + Δ% badge.
   Patch pages only; mirrors b()/gradient_class colouring. */
(function () {
  const blocks = document.querySelectorAll('.formula-change[data-fx-old]');
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
