
(function() {
  // ---- BACK TO TOP visibility ----
  // Guard for pages without the button (e.g. creeps.html). Without this
  // null-guard, updateBtt() throws at load and halts the whole script —
  // which silently broke the creep-icon copy handler below.
  const btt = document.querySelector('.back-to-top');
  if (btt) {
    // PERF: classList.toggle() still writes/dirties style even when the
    // value is unchanged, and this fires on every 'scroll' event (i.e. most
    // animation frames while scrolling). Track the last state and skip the
    // DOM write entirely once we're past the 400px threshold either way.
    let bttVisible = null;
    let bttAtTop = null;
    const updateBtt = () => {
      const shouldShow = window.scrollY > 400;
      // in the patch pages' corner panel it always has its place, grey while the page is at its top (owner
      // 2026-11-07: "кнопка «наверх» должна быть тусклой/серой, если я наверху страницы уже")
      const atTop = window.scrollY < 1;
      if (atTop !== bttAtTop) { bttAtTop = atTop; btt.classList.toggle('at-top', atTop); }
      if (shouldShow === bttVisible) return;
      bttVisible = shouldShow;
      btt.classList.toggle('visible', shouldShow);
    };
    window.addEventListener('scroll', updateBtt, { passive: true });
    // On a reload or back/forward the browser puts the page back where it was only after load: until then the
    // button shows no colour, not grey then gold (owner 2026-11-07: "при ctrl+f5 кнопка «наверх» на секунду серая,
    // потом уже золотая"). A fresh visit starts at the top and decides at once.
    const nav = (performance.getEntriesByType && performance.getEntriesByType('navigation')[0]) || {};
    const settle = () => { updateBtt(); btt.classList.remove('btt-wait'); };
    if (btt.classList.contains('btt-wait') && (nav.type === 'reload' || nav.type === 'back_forward')
        && document.readyState !== 'complete') {
      window.addEventListener('load', () => requestAnimationFrame(settle), { once: true });
    } else {
      settle();
    }
  }
})();
