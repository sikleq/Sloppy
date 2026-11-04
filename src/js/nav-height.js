
// ---- SITE NAV HEIGHT → CSS variable (used by every sticky layer below) ----
// The toolbar / view / blurb on table pages all scroll away with the page;
// only the site nav + table category headers stay pinned. The thead pins
// directly under the nav, so all we need to publish is its live height.
(function() {
  const nav = document.querySelector('nav.top-nav');
  if (!nav) return;
  function recalc() {
    const navH = nav.getBoundingClientRect().height;
    const root = document.documentElement.style;
    root.setProperty('--site-nav-h', navH + 'px');
    root.setProperty('--mr-thead-top', navH + 'px');
  }
  recalc();
  window.addEventListener('resize', recalc, { passive: true });
  window.addEventListener('load', recalc);
})();
