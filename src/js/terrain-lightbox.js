
// ---------------------------------------------------------------------
// Terrain note pictures (patch pages + Terrain pages, patch/elements.py terrain_note): the words naming the note's
// object ("tier 1 safe lane towers" — the owner 2026-10-03: "the screenshot opens from the objective's name") open its
// old | new micro-screenshots below (hidden until then, so they load on demand); a click on one opens its large copy
// (data-large) over the page — Esc or a click closes it (the owner 2026-10-03: "the picture grows in quality, it
// doesn't take you to Terrain"). Delegated, one listener for every note.
// ---------------------------------------------------------------------
(function() {
  let box = null;
  function lightbox() {
    if (box) return box;
    box = document.createElement('div');
    box.className = 'tshot-lightbox';
    box.innerHTML = '<img alt="">';
    box.addEventListener('click', function() { box.classList.remove('is-open'); });
    document.addEventListener('keydown', function(ev) {
      if (ev.key === 'Escape' && box.classList.contains('is-open')) box.classList.remove('is-open');
    });
    document.body.appendChild(box);
    return box;
  }
  document.addEventListener('click', function(ev) {
    const btn = ev.target.closest && ev.target.closest('.tshots-btn');
    if (btn) {
      const row = btn.closest('li');
      // a row with a picture under each of its words (7.38 "neutral camps, trees, and cliffs"): the box of its number
      const part = btn.getAttribute('data-part');
      const pics = row && row.querySelector(part === null ? ':scope > .tshots'
                                                          : ':scope > .tshots[data-part="' + part + '"]');
      const open = btn.getAttribute('aria-expanded') !== 'true';
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (pics) pics.hidden = !open;
      return;
    }
    const img = ev.target.closest && ev.target.closest('.tshots img[data-large]');
    if (!img) return;
    const b = lightbox();
    b.querySelector('img').src = img.dataset.large;
    b.classList.add('is-open');
  });
})();
