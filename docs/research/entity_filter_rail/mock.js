// Mock-up only (owner 2026-11-24): the hero page filters as the patch pages' framed rail at the right edge.
// Builds the rail from the page's own toolbar buttons and forwards clicks to them, so the filtering is real.
// ?v=list (default): abilities as rows, icon as the tick box + name; ?v=grid: abilities as an icon grid.
(function () {
  const V = new URLSearchParams(location.search).get('v') || 'list';
  const bar = document.querySelector('.toolbar');
  if (!bar) return;
  const trees = {};
  (window.SLOPPY_ABILITY_TREES || []).forEach(t => t.children.forEach(c => { trees[c] = t.parent; }));
  const pop = document.createElement('div');
  pop.className = 'filter-pop mock-rail mock-' + V;
  const rail = document.createElement('div');
  rail.className = 'filter-rail';
  pop.appendChild(rail);
  const sec = cls => { const d = document.createElement('div'); d.className = cls; rail.appendChild(d); return d; };
  const mirror = (src, el) => {
    el.addEventListener('click', () => { src.click(); el.classList.toggle('active', src.classList.contains('active')); });
    return el;
  };
  const tags = sec('legend-tags');
  bar.querySelectorAll('.filter-btn[data-filter]').forEach(b => {
    const n = document.createElement('button');
    n.type = 'button'; n.className = b.className.replace(/\bactive\b/, ''); n.dataset.filter = b.dataset.filter;
    n.innerHTML = '<span class="fp-word">' + b.textContent.trim() + '</span>';
    tags.appendChild(mirror(b, n));
  });
  const cats = sec('legend-categories');
  bar.querySelectorAll('.ec-scope-btn').forEach(b => {
    const n = document.createElement('button');
    n.type = 'button'; n.className = 'cat-filter-btn';
    const img = b.querySelector('img');
    n.innerHTML = (img ? '<img class="mock-ico" src="' + img.src + '" alt="">' : '')
      + '<span class="fp-word">' + (b.dataset.tooltip || b.textContent.trim() || b.dataset.ecScope) + '</span>';
    if (img) n.classList.add('mock-aghs');
    cats.appendChild(mirror(b, n));
  });
  const abs = sec('legend-categories mock-abs');
  bar.querySelectorAll('.ec-ab-btn').forEach(b => {
    const img = b.querySelector('img');
    const name = b.dataset.ecAbility;
    const n = document.createElement('button');
    n.type = 'button';
    n.className = 'mock-ab' + (b.classList.contains('ec-ab-old') ? ' is-old' : '');
    n.title = V === 'grid' ? name : '';
    n.innerHTML = (img ? '<img src="' + img.src + '" alt="">' : '<i></i>') + (V === 'list' ? '<span class="fp-word">' + name + '</span>' : '');
    if (b.classList.contains('ec-ab-old') && !abs.querySelector('.mock-sep')) {
      const s = document.createElement('div'); s.className = 'mock-sep'; s.textContent = 'Removed'; abs.appendChild(s);
    }
    abs.appendChild(mirror(b, n));
  });
  bar.style.display = 'none';
  document.body.appendChild(pop);
})();
