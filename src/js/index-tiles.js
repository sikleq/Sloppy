
// ---- INVENTORY SUB-PANELS: a tile with [data-panel-open="<name>"] opens its
// sub-panel ([data-panel="<name>"]) IN PLACE of the inventory grid instead of
// redirecting (Support → Telegram/Donation; Dynamics → Heroes/Items). The back
// arrow (or Escape) returns to the grid. Generic over any number of panels. ----
(function () {
  const book = document.querySelector('.inv-book');
  if (!book) return;
  const openers = [...book.querySelectorAll('[data-panel-open]')];
  const panels = [...book.querySelectorAll('[data-panel]')];
  if (!openers.length || !panels.length) return;
  const names = panels.map(p => p.dataset.panel);
  let lastOpener = null;
  const setOpen = (name) => {
    names.forEach(n => book.classList.toggle(n + '-open', n === name));
    panels.forEach(p => p.setAttribute('aria-hidden', p.dataset.panel === name ? 'false' : 'true'));
    openers.forEach(o => o.setAttribute('aria-expanded', o.dataset.panelOpen === name ? 'true' : 'false'));
    if (name) {
      const back = book.querySelector('.support-back');
      if (back) back.focus();
    } else if (lastOpener) {
      lastOpener.focus();
    }
  };
  openers.forEach(o => o.addEventListener('click', (e) => {
    e.preventDefault();
    lastOpener = o;
    setOpen(o.dataset.panelOpen);
  }));
  book.querySelectorAll('[data-panel-close]').forEach(
    (b) => b.addEventListener('click', () => setOpen(null)));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && names.some(n => book.classList.contains(n + '-open'))) {
      setOpen(null);
    }
  });
})();

// ---- CALENDAR tile: hover burns the date page (gold pixel fire) and loops 1→31.
// JS src-swap (not CSS content:url) with a one-time cache-bust, because the
// calendar GIF filename predates the other tile GIFs and browsers/CDN cached the
// old number-cycle version — the `?v=` forces the new burning GIF to load.
(function () {
  const tile = document.querySelector('.inv-cell-calendar');
  if (!tile) return;
  const img = tile.querySelector('.inv-icon');
  if (!img) return;
  const PNG = img.getAttribute('src');
  const GIF = 'icons/ui/gothic/icon_calendar.gif?v=' + Date.now();
  tile.addEventListener('mouseenter', () => { img.src = GIF; });
  tile.addEventListener('mouseleave', () => { img.src = PNG; });
})();

// ---- ITEMS tile: hover plays a one-shot chest-OPEN intro (key flies in → lid
// opens → gold beam + treasure), then LOOPS the open chest with the beam + gold
// glints twinkling for as long as it's hovered. Two APNGs swapped via JS (a
// single animation can't play an intro once then loop only its tail — same
// pattern as the mana fill+wave). The ?v= cache-bust forces each to restart
// from frame 0. Reverts to the closed PNG on mouse-out. Skipped under
// prefers-reduced-motion (stays closed). INTRO_MS must match the generator's
// printed intro duration (scripts/gen_chest_icon.py).
(function () {
  const tile = document.querySelector('.inv-cell-items');
  if (!tile) return;
  const img = tile.querySelector('.inv-icon');
  if (!img) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const PNG = img.getAttribute('src');
  const OPEN = 'icons/ui/gothic/icon_chest_open.png';   // intro, plays once
  const LOOP = 'icons/ui/gothic/icon_chest_loop.png';   // open + glints, loops
  const INTRO_MS = 1044;
  // Preload + decode both APNGs so swapping src mid-hover is instant — without
  // this the browser fetches the loop on first swap and the beam visibly stalls.
  [OPEN, LOOP].forEach(s => { const p = new Image(); p.src = s; });
  let timer = null;
  tile.addEventListener('mouseenter', () => {
    clearTimeout(timer);
    img.src = ''; img.src = OPEN;
    timer = setTimeout(() => { img.src = ''; img.src = LOOP; }, INTRO_MS);
  });
  tile.addEventListener('mouseleave', () => {
    clearTimeout(timer);
    img.src = PNG;
  });
})();

// ---- MANA ITEMS tile: hover plays a one-shot FILL (empty→half), then loops the
// wave at that level. Two GIFs swapped via JS — a single GIF can't play an intro
// once and then loop only its tail. Reverts to the static bottle on mouse-out.
(function () {
  // The mana icon now lives on the "Mana" button inside the Items sub-panel
  // (it used to be a top-level tile). querySelectorAll keeps this robust no
  // matter where `.inv-cell-mana` sits.
  const FILL = 'icons/ui/gothic/icon_mana_fill.gif';
  const WAVE = 'icons/ui/gothic/icon_mana.gif';
  const FILL_MS = 11 * 150;            // fill GIF: 11 frames × 150ms
  document.querySelectorAll('.inv-cell-mana').forEach((tile) => {
    const img = tile.querySelector('.inv-icon');
    if (!img) return;
    const PNG = img.getAttribute('src');
    let timer = null;
    tile.addEventListener('mouseenter', () => {
      clearTimeout(timer);
      img.src = FILL + '?' + Date.now();  // cache-bust forces the fill to replay
      timer = setTimeout(() => { img.src = WAVE; }, FILL_MS);
    });
    tile.addEventListener('mouseleave', () => {
      clearTimeout(timer);
      img.src = PNG;
    });
  });
})();

// ---- Ko-Fi gold stack: hover plays the sparkle APNG, reverts on mouse-out.
//      Skipped under prefers-reduced-motion.
(function () {
  const btn = document.querySelector('.support-kofi');
  if (!btn) return;
  const img = btn.querySelector('.inv-icon');
  if (!img) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const PNG      = img.getAttribute('src');
  const SPARKLE  = 'icons/ui/gothic/gold_stack_sparkle.png';
  btn.addEventListener('mouseenter', () => { img.src = SPARKLE + '?' + Date.now(); });
  btn.addEventListener('mouseleave', () => { img.src = PNG; });
})();
