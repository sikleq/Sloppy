
// ---------------------------------------------------------------------
// Patch pages: the search sits behind the round loupe button in the corner stack.
// Click / "\" / "/" opens the field (slides out left of the button); the key again, Esc or a click
// outside closes it, picking a result closes it too (the jump itself lives in ENTITY SEARCH).
// The key is found by its PHYSICAL position (e.code "Backslash" / "Slash", "/" since 2026-10-24), so it
// works in any keyboard layout, and it is never typed into the field. English only: see INPUTS below.
// ---------------------------------------------------------------------
(function () {
  var fab = document.getElementById('search-fab');
  var pop = document.getElementById('search-pop');
  var input = document.getElementById('entity-search');
  if (!fab || !pop || !input) return;
  function open() {
    pop.hidden = false;
    fab.setAttribute('aria-expanded', 'true');
    input.focus();
  }
  function close() {
    pop.hidden = true;
    fab.setAttribute('aria-expanded', 'false');
    input.value = '';
    input.dispatchEvent(new Event('input'));
  }
  fab.addEventListener('click', function () { if (pop.hidden) open(); else close(); });
  document.addEventListener('keydown', function (e) {
    var t = e.target;
    var typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
    var hotkey = (e.code === 'Backslash' || e.code === 'Slash') && !e.ctrlKey && !e.altKey && !e.metaKey;
    if (hotkey && (!typing || t === input)) {       // never typed; toggles from the page or the field
      e.preventDefault();
      if (pop.hidden) open(); else close();
    }
    else if (e.key === 'Escape' && !pop.hidden) close();
  });
  document.addEventListener('mousedown', function (e) {
    if (!pop.hidden && !pop.contains(e.target) && e.target !== fab) close();
  });
  // a picked result (click or Enter) jumps and clears the field -> close the popover
  pop.addEventListener('click', function (e) {
    if (e.target.closest('.result-item')) setTimeout(close, 0);
  });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') setTimeout(function () { if (!input.value) close(); }, 0);
  });
})();
