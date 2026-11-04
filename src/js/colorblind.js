
// ---- COLOUR-BLIND MODE: the header switch (builders/site_common.py CB_TOGGLE). html.cb-mode swaps green → blue and
// red → orange (styles.css, generated block); remembered in localStorage 'cbMode'. Scripts that paint colours
// themselves (the Materials heatmap) listen for 'cb-mode-changed' and repaint. ----
(function initCbMode() {
  const root = document.documentElement;
  const buttons = document.querySelectorAll('.cb-toggle');
  const sync = () => buttons.forEach(b => b.setAttribute('aria-pressed', String(root.classList.contains('cb-mode'))));
  sync();
  buttons.forEach(b => b.addEventListener('click', () => {
    const on = root.classList.toggle('cb-mode');
    try { localStorage.setItem('cbMode', on ? '1' : '0'); } catch (e) { /* private mode: this page only */ }
    sync();
    window.dispatchEvent(new Event('cb-mode-changed'));
  }));
})();
