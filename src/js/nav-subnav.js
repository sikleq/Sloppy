
// ---- MATERIALS SUB-NAV: tap-to-open submenu on touch devices ----
// On hover-capable devices (mouse) the .nav-submenu opens on hover — fine. On
// touch devices the group trigger is an <a href=...> so the first tap fires
// navigation immediately, and the submenu never gets a chance to appear (only
// long-press emulates :hover, which the user shouldn't have to know about).
// Fix: on tap-only devices, the FIRST tap on a group trigger opens its
// submenu instead of navigating; a SECOND tap on the same trigger (or on
// anywhere outside) lets the navigation happen normally. Active item picks
// continue to navigate on first tap (so users CAN reach the group's own page
// — by tapping it twice). Touch detection uses the `(hover: none)` media
// query so plain laptops aren't affected.
(function() {
  const mq = window.matchMedia && window.matchMedia('(hover: none)');
  if (!mq || !mq.matches) return;
  const groups = document.querySelectorAll('.materials-subnav .nav-subgroup');
  if (!groups.length) return;
  let openGroup = null;
  function closeOpen() {
    if (openGroup) {
      openGroup.classList.remove('is-open');
      openGroup = null;
    }
  }
  groups.forEach(group => {
    const trigger = group.querySelector(':scope > .nav-subtab-group, :scope > .nav-subitem-parent');
    if (!trigger) return;
    trigger.addEventListener('click', (e) => {
      if (group === openGroup) {
        // Second tap on the same group — let the link follow through.
        return;
      }
      // First tap — open the submenu instead of navigating.
      e.preventDefault();
      closeOpen();
      group.classList.add('is-open');
      openGroup = group;
    });
  });
  // Tap outside any group closes the open one.
  document.addEventListener('click', (e) => {
    if (openGroup && !openGroup.contains(e.target)) closeOpen();
  });
})();
