
// ---- TALENT TREE: light only the twigs of the talent rows a filter leaves visible ----
// Each talent row carries data-tt="20r 25r" (patch/talent_tree.py); each lit twig is one
// <use data-b> in its row's tag colour. Filters only toggle hide classes, so a class-change observer (hide classes only)
// re-syncs the trees once per frame.
(function() {
  const trees = document.querySelectorAll('svg.ttree');
  if (!trees.length) return;
  const HIDE = '.f-hide, .ec-scope-hide, .ec-aghs-hide, .is-hidden';
  const catOn = () => document.body.classList.contains('cat-filter-active');
  function sync() {
    const catActive = catOn();
    trees.forEach(svg => {
      const block = svg.closest('.talents-block');
      if (!block) return;
      const on = new Set();
      block.querySelectorAll('li[data-tt]').forEach(li => {
        if (li.closest(HIDE) || (catActive && li.closest('.cat-hide'))) return;
        li.dataset.tt.split(' ').forEach(b => on.add(b));
      });
      svg.querySelectorAll('[data-b]').forEach(img => {
        img.style.display = on.has(img.dataset.b) ? '' : 'none';
      });
      svg.classList.toggle('ttree-lit', on.size > 0);
    });
  }
  let queued = false;
  const HIDE_RE = /hide|hidden|filter-active/;
  new MutationObserver(records => {
    if (queued) return;
    if (!records.some(r => HIDE_RE.test(r.oldValue || '') || HIDE_RE.test(r.target.className || ''))) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; sync(); });
  }).observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'], attributeOldValue: true });
  sync();
})();
