
// ---- A FOLD THAT HIDES ALMOST NOTHING STAYS OPEN (owner 2026-11-08, 7.40 Liquid Courage: "тут так мало прячется, что
// будто и не нужно сворачивать"). The build folds by the text's length; only the page knows the lines it really hides
// at this width: under two lines, the whole text shows and the strip goes (.acr-fold.fold-off). ----
(function() {
  const LINES = 2;
  function check() {
    document.querySelectorAll('.acr-fold:not(.is-open):not(.fold-off)').forEach((fold) => {
      const body = fold.querySelector(':scope > .acr-fold-body');
      if (!body || !body.clientHeight) return;            // hidden (a filter): measured another time
      const line = parseFloat(getComputedStyle(body).lineHeight) || 20;
      if (body.scrollHeight - body.clientHeight < LINES * line) {
        fold.classList.add('is-open', 'fold-off');
        fold.dispatchEvent(new Event('toggle'));          // the card's lines follow its new height
      }
    });
  }
  check();
  window.addEventListener('load', check);
  window.sloppyFoldSmall = check;                         // a deck's card shown later (card-deck.js)
})();
