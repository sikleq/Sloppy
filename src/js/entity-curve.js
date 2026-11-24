// ── Entity strength curve (owner 2026-11-24, variant A, layout 1) ──
// Hero / item page header: a running sum of the weights of the patches that changed it, smooth (monotone cubic, no
// overshoot), a dot per patch green = buff, red = nerf. A click on a dot scrolls to that patch; the dot of the patch on
// screen is lit. Data: data-curve on .ec-curve, written by builders/entity_changes.py (_curve_box).
(function () {
  const box = document.querySelector('.ec-curve[data-curve]');
  if (!box) return;
  let pts;
  try { pts = JSON.parse(box.dataset.curve); } catch (err) { console.error('entity curve: bad data-curve', err); return; }
  const NS = 'http://www.w3.org/2000/svg';
  const PHONE = 700;

  function el(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }

  // Fritsch-Carlson monotone cubic through [{x,y}].
  function monoPath(p) {
    const n = p.length, d = [], m = [];
    for (let i = 0; i < n - 1; i++) d.push((p[i + 1].y - p[i].y) / (p[i + 1].x - p[i].x));
    m[0] = d[0]; m[n - 1] = d[n - 2];
    for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2;
    for (let i = 0; i < n - 1; i++) {
      if (d[i] === 0) { m[i] = m[i + 1] = 0; continue; }
      const a = m[i] / d[i], b = m[i + 1] / d[i], s = a * a + b * b;
      if (s > 9) { const t = 3 / Math.sqrt(s); m[i] = t * a * d[i]; m[i + 1] = t * b * d[i]; }
    }
    let s = 'M' + p[0].x + ',' + p[0].y;
    for (let i = 0; i < n - 1; i++) {
      const h = (p[i + 1].x - p[i].x) / 3;
      s += 'C' + (p[i].x + h) + ',' + (p[i].y + m[i] * h) + ' ' + (p[i + 1].x - h) + ',' + (p[i + 1].y - m[i + 1] * h)
        + ' ' + p[i + 1].x + ',' + p[i + 1].y;
    }
    return s;
  }

  let sum = 0;
  const series = pts.map(([v, w]) => { sum += w; return { v, w, sum }; });

  function go(v) {
    const t = document.getElementById('p-' + v);
    if (t) window.scrollTo({ top: t.getBoundingClientRect().top + window.scrollY - 120, behavior: 'smooth' });
  }

  function draw() {
    box.innerHTML = '';
    const phone = window.innerWidth < PHONE;
    const W = box.clientWidth || 600, H = phone ? 120 : 150;
    const pad = { l: 10, r: 10, t: 14, b: 22 };
    // phone: a label on every 2nd or 3rd patch (they overlap otherwise), always on the newest one
    const every = phone ? Math.max(1, Math.ceil(series.length * 34 / W)) : 1;
    const svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, width: '100%', height: H, class: 'ec-curve-svg' }, box);
    const ys = series.map(p => p.sum).concat(0);
    const lo = Math.min(...ys), hi = Math.max(...ys), span = hi - lo || 1;
    const X = i => pad.l + (W - pad.l - pad.r) * i / (series.length - 1);
    const Y = v => pad.t + (H - pad.t - pad.b) * (1 - (v - lo) / span);
    el('line', { x1: pad.l, x2: W - pad.r, y1: Y(0), y2: Y(0), class: 'ec-curve-axis' }, svg);
    const xy = series.map((p, i) => ({ x: X(i), y: Y(p.sum) }));
    const line = monoPath(xy), last = xy[xy.length - 1];
    el('path', { d: line + 'L' + last.x + ',' + Y(0) + 'L' + xy[0].x + ',' + Y(0) + 'Z', class: 'ec-curve-area' }, svg);
    el('path', { d: line, class: 'ec-curve-line' }, svg);
    series.forEach((p, i) => {
      const g = el('g', { class: 'ec-curve-pt' + (p.w > 0 ? ' is-buff' : p.w < 0 ? ' is-nerf' : ''), 'data-v': p.v }, svg);
      el('circle', { cx: xy[i].x, cy: xy[i].y, r: 4, class: 'ec-curve-dot' }, g);
      el('circle', { cx: xy[i].x, cy: xy[i].y, r: 12, class: 'ec-curve-hit' }, g);
      if ((series.length - 1 - i) % every === 0) el('text', { x: xy[i].x, y: H - 6, class: 'ec-curve-lbl' }, g).textContent = p.v;
      g.addEventListener('click', () => go(p.v));
    });
    light();
  }

  const secs = Array.from(document.querySelectorAll('.ec-patch[id^="p-"]'));
  function light() {
    let cur = null;
    for (const s of secs) if (s.getBoundingClientRect().top < 200) cur = s;
    const v = cur ? cur.id.slice(2) : '';
    box.querySelectorAll('.ec-curve-pt').forEach(g => g.classList.toggle('is-cur', g.dataset.v === v));
  }

  draw();
  let rt = 0;
  window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(draw, 100); });
  window.addEventListener('scroll', light, { passive: true });
})();
