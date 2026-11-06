
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
    const updateBtt = () => {
      const shouldShow = window.scrollY > 400;
      if (shouldShow === bttVisible) return;
      bttVisible = shouldShow;
      btt.classList.toggle('visible', shouldShow);
    };
    window.addEventListener('scroll', updateBtt, { passive: true });
    updateBtt();
  }
})();
