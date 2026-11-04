

/* ---- STAR SKY + WALL OF SIGNATURES (index) ----
   A few dim, lightly/independently twinkling pixel "stars" form the backdrop.
   The member names start HIDDEN (nothing painted at load → light first paint);
   a gold laser from the Premium star reveals them ONE per shot and they stay
   lit, so the wall fills up over time. Stars and names are laid out so they
   never overlap (they may sit very close). Re-runs on resize. Index-only. */
(function () {
  const layer = document.querySelector('.inv-signatures');
  if (!layer) return;
  // A name is "blank" if it has no visible char (only whitespace / zero-width),
  // so a beam never flies to an empty-looking name (blank names can still have a
  // nonzero render width, which is why offsetWidth alone doesn't catch them).
  function hasVisible(s) {
    const t = s.textContent;
    for (let i = 0; i < t.length; i++) {
      if (t[i].trim() === '') continue;                       // whitespace
      const c = t.charCodeAt(i);
      // zero-width chars + blank "filler" letters used as empty usernames:
      // Hangul fillers (115F/1160/3164/FFA0), Braille blank (2800), Mongolian sep.
      if (c === 0x200B || c === 0x200C || c === 0x200D || c === 0x2060 || c === 0xFEFF ||
          c === 0x115F || c === 0x1160 || c === 0x3164 || c === 0xFFA0 ||
          c === 0x2800 || c === 0x180E || c === 0x3000) continue;
      return true;
    }
    return false;
  }
  const sigs = [...layer.querySelectorAll('.inv-sig')].filter(hasVisible);
  if (!sigs.length) return;

  const overlap = (a, b) => !(a.r <= b.l || a.l >= b.r || a.b <= b.t || a.t >= b.b);

  // Dedicated star-sky layer behind everything.
  let sky = document.querySelector('.star-sky');
  if (!sky) {
    sky = document.createElement('div');
    sky.className = 'star-sky';
    sky.setAttribute('aria-hidden', 'true');
    document.body.appendChild(sky);
  }

  let pos = [];          // computed name positions {x,y,cx,cy,rot} (null if dropped)
  let starRects = [];    // star bounding rects, so names avoid them

  function forbiddenZones(W, H, M) {
    const zones = [];
    const book = document.querySelector('.inv-book');
    if (book) {
      const br = book.getBoundingClientRect();
      zones.push({ l: br.left - M, t: br.top - M, r: br.right + M, b: br.bottom + M });
    }
    const nav = document.querySelector('nav.top-nav');
    if (nav) {
      const nr = nav.getBoundingClientRect();
      zones.push({ l: 0, t: 0, r: W, b: nr.bottom + M });
    }
    return zones;
  }

  // A handful of dim pixel stars, avoiding the book/nav and each other.
  function placeStars(W, H) {
    sky.textContent = '';
    starRects = [];
    const forbidden = forbiddenZones(W, H, 4);
    const COUNT = Math.round(Math.min(92, Math.max(46, (W * H) / 13000)));  // +15% more (incl. smaller ones)
    const SM = 3;                                  // min gap between stars
    const twinkleCenters = [];                     // keep twinkling stars spread apart
    for (let i = 0; i < COUNT; i++) {
      for (let tryN = 0; tryN < 40; tryN++) {
        const sr = Math.random();
        const sz = sr < 0.12 ? 1 : sr < 0.30 ? 2 : sr < 0.78 ? 3 : 4;   // ~30% small (1–2px), rest 3–4px
        const x = 5 + Math.random() * (W - 10);
        const y = 5 + Math.random() * (H - 10);
        const r = { l: x - SM, t: y - SM, r: x + sz + SM, b: y + sz + SM };
        if (forbidden.some(f => overlap(r, f))) continue;
        if (starRects.some(s => overlap(r, s))) continue;
        const star = document.createElement('i');
        star.className = 'star';
        star.style.left = x.toFixed(1) + 'px';
        star.style.top = y.toFixed(1) + 'px';
        star.style.width = star.style.height = sz + 'px';
        // Three brightness tiers: most dim, ~22% bright, ~10% extra-bright (brighter still).
        const roll = Math.random();
        let lo, hi, staticOp;
        // Wide low→high swing so the twinkle is clearly visible (dims to nearly
        // nothing, then brightens to a clear peak).
        if (roll < 0.10) {
          lo = 0.35; hi = 1.0; staticOp = 0.78;
          star.style.boxShadow = '0 0 4px rgba(236,228,205,0.78)';
        } else if (roll < 0.32) {
          lo = 0.2; hi = 0.9; staticOp = 0.52;
          star.style.boxShadow = '0 0 3px rgba(232,224,200,0.5)';
        } else {
          lo = 0.08; hi = 0.5; staticOp = 0.3;
        }
        // Only ~22% twinkle (extra-bright lean toward it), and never too close to
        // another twinkling star — so few flicker at once and they stay spread out.
        const cx = x + sz / 2, cy = y + sz / 2;
        const spaced = !twinkleCenters.some(c => Math.hypot(c.x - cx, c.y - cy) < 55);
        const wantTwinkle = roll < 0.10 ? Math.random() < 0.6 : Math.random() < 0.22;
        if (wantTwinkle && spaced) {
          star.style.setProperty('--lo', lo);
          star.style.setProperty('--hi', hi);
          star.style.opacity = lo;
          const durN = 3 + Math.random() * 3.5;               // faster cadence → more noticeable
          // NEGATIVE delay = start already partway through the cycle, at a random
          // phase, so stars never twinkle in sync (positive delays would just
          // stagger the start but keep them aligned early on).
          const del = (-Math.random() * durN).toFixed(2);
          star.style.animation = 'starTwinkle ' + durN.toFixed(1) + 's ease-in-out ' + del + 's infinite';
          twinkleCenters.push({ x: cx, y: cy });
        } else {
          star.style.opacity = staticOp;
        }
        sky.appendChild(star);
        starRects.push(r);
        break;
      }
    }
  }

  // Place every name (avoiding book/nav, stars, and each other) but keep them
  // HIDDEN — they reveal only when a beam reaches them. Strict read/write phases
  // so the browser lays out ~twice (no per-name reflow). is-lit is preserved
  // across re-layout so already-revealed names stay visible.
  function placeNames(W, H) {
    const M = Math.max(2, Math.round(11 - sigs.length * 0.05));
    const FONT_MIN = 11, FONT_MAX = 22;
    const crowd = Math.max(0, Math.min(1, (sigs.length - 120) / 240));
    const fontTop = Math.round(FONT_MAX - (FONT_MAX - FONT_MIN) * crowd);
    const fontBot = Math.max(FONT_MIN, fontTop - 6);
    const EDGE = 6;
    const forbidden = forbiddenZones(W, H, M).concat(starRects);   // also dodge stars
    const n = sigs.length;
    // (1) write font sizes
    for (let i = 0; i < n; i++) {
      sigs[i].style.display = '';
      sigs[i].style.fontSize = (fontBot + Math.floor(Math.random() * (fontTop - fontBot + 1))) + 'px';
    }
    // (2) measure once
    const ws = new Array(n), hs = new Array(n);
    for (let i = 0; i < n; i++) { ws[i] = sigs[i].offsetWidth; hs[i] = sigs[i].offsetHeight; }
    // (3) pure-JS placement
    const placed = [];
    pos = new Array(n);
    for (let i = 0; i < n; i++) {
      const w0 = ws[i], h0 = hs[i];
      if (!w0 || !h0) { pos[i] = null; continue; }
      const rot = Math.random() * 14 - 7;
      const rad = Math.abs(rot) * Math.PI / 180;
      const bw = w0 * Math.cos(rad) + h0 * Math.sin(rad);
      const bh = w0 * Math.sin(rad) + h0 * Math.cos(rad);
      const cxMin = EDGE + bw / 2, cxMax = W - EDGE - bw / 2;
      const cyMin = EDGE + bh / 2, cyMax = H - EDGE - bh / 2;
      if (cxMax <= cxMin || cyMax <= cyMin) { pos[i] = null; continue; }
      let done = false;
      for (let k = 0; k < 60 && !done; k++) {
        const cx = cxMin + Math.random() * (cxMax - cxMin);
        const cy = cyMin + Math.random() * (cyMax - cyMin);
        const r = { l: cx - bw / 2 - M, t: cy - bh / 2 - M, r: cx + bw / 2 + M, b: cy + bh / 2 + M };
        let bad = false;
        for (let f = 0; f < forbidden.length; f++) { if (overlap(r, forbidden[f])) { bad = true; break; } }
        if (bad) continue;
        for (let p = 0; p < placed.length; p++) { if (overlap(r, placed[p])) { bad = true; break; } }
        if (bad) continue;
        pos[i] = { x: cx - w0 / 2, y: cy - h0 / 2, cx: cx, cy: cy, rot: rot };
        placed.push(r);
        done = true;
      }
      if (!done) pos[i] = null;
    }
    // (4) write transforms; do NOT reveal — names stay hidden until a beam hits.
    for (let i = 0; i < n; i++) {
      const s = sigs[i], p = pos[i];
      if (!p) { s.style.display = 'none'; continue; }
      s.style.transform = 'translate(' + p.x.toFixed(1) + 'px,' + p.y.toFixed(1) + 'px) rotate(' + p.rot.toFixed(1) + 'deg)';
    }
    layer.style.opacity = '1';     // layer is up; individual names hidden via CSS
  }

  function layout() {
    const W = document.documentElement.clientWidth;
    const H = document.documentElement.clientHeight;
    placeStars(W, H);
    placeNames(W, H);
  }

  function run() {
    // Wait for the wall font (Handjet) so widths measure right, capped at 300ms.
    const fontReady = (document.fonts && document.fonts.load)
      ? document.fonts.load('20px "Handjet"').catch(() => {})
      : Promise.resolve();
    Promise.race([
      Promise.resolve(fontReady),
      new Promise(r => setTimeout(r, 300)),
    ]).then(() => requestAnimationFrame(layout));   // defer off the first paint
  }
  if (document.readyState !== 'loading') run();
  else document.addEventListener('DOMContentLoaded', run);
  let t;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(layout, 200); }, { passive: true });

  // Premium-star laser: reveals one not-yet-lit name per shot; it then stays lit.
  const star = document.querySelector('.inv-cell-star .inv-icon')
            || document.querySelector('.inv-cell-star');
  let fx = null;                       // shared overlay for beams + dust
  function fxLayer() {
    if (!fx) {
      fx = document.createElement('div');
      fx.className = 'sig-beam-layer';
      fx.setAttribute('aria-hidden', 'true');
      document.body.appendChild(fx);
    }
    return fx;
  }
  function shootBeam(ox, oy, tx, ty) {
    if (!star) return;
    const beamLayer = fxLayer();
    const dx = tx - ox, dy = ty - oy;
    const dist = Math.hypot(dx, dy);
    const ang = Math.atan2(dy, dx) * 180 / Math.PI;
    const beam = document.createElement('div');
    beam.className = 'sig-beam';
    beam.style.left = ox + 'px';
    beam.style.top = oy + 'px';
    beam.style.width = dist + 'px';
    const tr = 'rotate(' + ang + 'deg)';
    const anim = beam.animate([
      { transform: tr + ' scaleX(0)', opacity: 0 },
      { transform: tr + ' scaleX(1)', opacity: 0.6, offset: 0.4 },
      { transform: tr + ' scaleX(1)', opacity: 0 },
    ], { duration: 600, easing: 'ease-out', fill: 'forwards' });
    beamLayer.appendChild(beam);
    anim.onfinish = () => beam.remove();
  }
  // VIP-name forge sparks: a small azure burst when a beam lights a VIP name,
  // as if it were just struck on an anvil. Specks shoot up + out, then gravity
  // arcs them down past the start and they fade. Same azure as .inv-sig-vip.
  function forgeSparks(sig) {
    const r = sig.getBoundingClientRect();
    const fxl = fxLayer();
    const N = 10 + Math.floor(Math.random() * 5);     // 10–14 sparks
    for (let k = 0; k < N; k++) {
      const p = document.createElement('i');
      p.className = 'sig-spark';
      const sz = Math.random() < 0.6 ? 2 : 3;
      p.style.width = p.style.height = sz + 'px';
      p.style.left = (r.left + Math.random() * r.width).toFixed(1) + 'px';
      p.style.top = (r.top + r.height * (0.3 + Math.random() * 0.5)).toFixed(1) + 'px';
      const ang = -Math.PI / 2 + (Math.random() - 0.5) * 1.9;   // fan around "up"
      const rad = 14 + Math.random() * 26;
      const dx = Math.cos(ang) * rad;
      const up = Math.sin(ang) * rad;                  // negative = upward
      const fall = 10 + Math.random() * 18;
      const a = p.animate([
        { transform: 'translate(0,0)', opacity: 1, offset: 0 },
        { transform: 'translate(' + (dx * 0.6).toFixed(1) + 'px,' + up.toFixed(1) + 'px)', opacity: 1, offset: 0.45 },
        { transform: 'translate(' + dx.toFixed(1) + 'px,' + (up + fall).toFixed(1) + 'px)', opacity: 0, offset: 1 },
      ], { duration: 600 + Math.random() * 500, easing: 'cubic-bezier(0.25,0.6,0.4,1)', fill: 'forwards' });
      fxl.appendChild(p);
      a.onfinish = () => p.remove();
    }
  }
  function lightUp(s) {
    s.classList.add('is-lit');
    if (s.classList.contains('inv-sig-vip')) forgeSparks(s);
  }
  function fireBeam(i) {
    const s = sigs[i];
    if (star) {
      const sr = star.getBoundingClientRect();
      shootBeam(sr.left + sr.width / 2, sr.top + sr.height / 2, pos[i].cx, pos[i].cy);
      setTimeout(() => lightUp(s), 220);   // light as the beam lands
    } else {
      lightUp(s);
    }
  }
  function spotlightOnce() {
    if (document.hidden || !pos.length) return;
    const pool = [];
    for (let i = 0; i < sigs.length; i++) {
      if (pos[i] && !sigs[i].classList.contains('is-lit')) pool.push(i);
    }
    if (!pool.length) { clearInterval(beamInterval); return; }
    // Usually one beam, but sometimes a volley: 20% chance of 2 beams at once,
    // 10% chance of 3 (each lights a different name).
    const roll = Math.random();
    let count = roll < 0.10 ? 3 : roll < 0.30 ? 2 : 1;
    count = Math.min(count, pool.length);
    for (let k = 0; k < count; k++) {
      const j = Math.floor(Math.random() * pool.length);
      fireBeam(pool.splice(j, 1)[0]);          // distinct name each beam
    }
  }
  setTimeout(spotlightOnce, 5000);              // first beam ~5s after load
  const beamInterval = setInterval(spotlightOnce, 2500);

  document.addEventListener('visibilitychange', () => {
    sky.classList.toggle('paused', document.hidden);
  });

  // Click a lit name → it "disintegrates" into pixel gold dust and returns to the
  // unlit pool, so a later beam can re-light it.
  function disintegrate(sig) {
    const r = sig.getBoundingClientRect();
    const fxl = fxLayer();
    const N = 16 + Math.floor(Math.random() * 10);   // 16–25 specks
    // Per-click randomisation so no two bursts disperse the same way.
    const spreadF = 0.8 + Math.random() * 0.7;       // this cloud's overall size
    const durBase = 3300 + Math.random() * 1800;     // this cloud's tempo (slow)
    const drift = Math.random() * Math.PI * 2;       // slight directional lean
    const driftAmt = Math.random() * 12;
    const vip = sig.classList.contains('inv-sig-vip');
    for (let k = 0; k < N; k++) {
      const p = document.createElement('i');
      p.className = vip ? 'sig-dust sig-dust-vip' : 'sig-dust';
      const sz = Math.random() < 0.5 ? 2 : 3;        // clear little squares (2–3px)
      p.style.width = p.style.height = sz + 'px';
      p.style.left = (r.left + Math.random() * r.width).toFixed(1) + 'px';
      p.style.top = (r.top + Math.random() * r.height).toFixed(1) + 'px';
      // Puff outward in all directions, spread wide so specks end up further apart,
      // + a gentle downward settle and this burst's directional lean.
      const ang = Math.random() * Math.PI * 2;
      const rad = (26 + Math.random() * 50) * spreadF;
      const dx = Math.cos(ang) * rad + Math.cos(drift) * driftAmt;
      const dy = Math.sin(ang) * rad * 0.6 + Math.sin(drift) * driftAmt + (5 + Math.random() * 16);
      const a = p.animate([
        { transform: 'translate(0,0)', opacity: 1, offset: 0 },
        { opacity: 1, offset: 0.5 },                 // linger visible longer before fading
        { transform: 'translate(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px)', opacity: 0, offset: 1 },
      ], { duration: durBase + Math.random() * 1400,  // ~10% slower dispersal, longer-lived
           easing: 'cubic-bezier(0.14,0.7,0.28,1)', fill: 'forwards' });
      fxl.appendChild(p);
      a.onfinish = () => p.remove();
    }
    sig.classList.remove('is-lit');                // fades out; rejoins the unlit pool
  }
  layer.addEventListener('click', (e) => {
    const sig = e.target.closest && e.target.closest('.inv-sig');
    if (sig && sig.classList.contains('is-lit')) disintegrate(sig);
  });
})();
