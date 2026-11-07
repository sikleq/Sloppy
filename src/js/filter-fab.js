// ---------------------------------------------------------------------
// Patch pages: the filters are a card at the page's right edge, in the middle of the screen's height, out from the
// start (owner 2026-11-07: "фильтры включены по умолчанию и давай их по правому краю", "центрировано на странице");
// the round button of the corner stack above the search puts them away and back ("иконку фильтров всё же вынеси
// сюда"), Esc puts them away. A window too narrow or too low to hold them beside the text and above the round
// buttons starts with them away, so they never cover the rows. While a tag or a section is on, the button glows: the
// page is filtered even with them away.
// ---------------------------------------------------------------------
(function () {
  var btn = document.getElementById('filter-fab');
  var rail = document.getElementById('filter-pop');
  if (!btn || !rail) return;
  function open() {
    rail.hidden = false;
    btn.setAttribute('aria-expanded', 'true');
  }
  function close() {
    rail.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
  }
  function covers() {
    // the card stands over the text column when it reaches past the card's left edge,
    // or reaches down onto the round buttons of the corner stack (a low window)
    var r = rail.getBoundingClientRect();
    var box = document.querySelector('.container');
    if (box && box.getBoundingClientRect().right > r.left) return true;
    return btn.getBoundingClientRect().top < r.bottom + 12;
  }
  function lit() {
    btn.classList.toggle('has-active', !!rail.querySelector('.filter-btn.active, .cat-filter-btn.active'));
  }
  btn.addEventListener('click', function () { if (rail.hidden) open(); else close(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !rail.hidden) close();
  });
  // the filters' own listeners (patch-page) run first and set .active; the button reads it after them
  rail.addEventListener('click', function () { setTimeout(lit, 0); });
  // the patch's own card above the filters, folded at first, opened by the tab on their top edge (owner 2026-11-07,
  // mock "Вариант 1")
  var tab = rail.querySelector('.pinfo-tab');
  var info = document.getElementById('pinfo-card');
  if (tab && info) tab.addEventListener('click', function (e) {
    e.stopPropagation();
    info.hidden = !info.hidden;
    tab.setAttribute('aria-expanded', info.hidden ? 'false' : 'true');
  });
  if (covers()) close();
})();
