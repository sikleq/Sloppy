
// ---------------------------------------------------------------------
// Info-tip (i) popup positioning — keep the bubble inside the viewport.
// CSS centers it above the (i); this nudges it horizontally so it never
// runs off-screen, and flips it below when there isn't room above.
// Event-delegated so it covers every (i) without per-element listeners.
// ---------------------------------------------------------------------
(function () {
  var MARGIN = 8;
  function place(tip) {
    var pop = tip.querySelector('.info-pop');
    if (!pop) return;
    // Reset so we measure the natural size, then position explicitly.
    pop.style.left = '0';
    pop.style.right = 'auto';
    pop.style.transform = 'none';
    var tr = tip.getBoundingClientRect();
    var pw = pop.offsetWidth;
    var ph = pop.offsetHeight;
    var vw = document.documentElement.clientWidth;
    // Horizontal: center over the (i), then clamp into the viewport.
    var vpLeft = tr.left + tr.width / 2 - pw / 2;
    vpLeft = Math.max(MARGIN, Math.min(vpLeft, vw - pw - MARGIN));
    pop.style.left = (vpLeft - tr.left) + 'px';
    // Vertical: prefer above; flip below if it would clip the top.
    if (tr.top - ph - 10 < MARGIN) {
      pop.style.top = 'calc(100% + 8px)';
      pop.style.bottom = 'auto';
    } else {
      pop.style.bottom = 'calc(100% + 8px)';
      pop.style.top = 'auto';
    }
  }
  function handler(e) {
    var t = e.target;
    if (!t || !t.closest) return;
    var tip = t.closest('.info-tip');
    if (tip) place(tip);
  }
  document.addEventListener('mouseover', handler, true);
  document.addEventListener('focusin', handler, true);
})();
