
// ---- Shared "shop" picker body = the Item Changes index look ----
// panels: [{title, one?, neutral?, groups: [{title?, extra?, tiles: '<button…>…'}]}] (no title = no group heading)
// Panels → titled categories → icon cards (ec-igrid / ec-ipanel / ec-igroup / ec-card).
// Used by the Hero Changes item slots and the Hero Lab shop / enchantment pickers;
// each group also carries .hl-item-section so the pickers' search can hide it.
function ecShopMarkup(panels) {
  return `<div class="ec-igrid ec-shop" data-panels="${panels.length}">` + panels.map(p =>
    `<section class="ec-ipanel${p.neutral ? ' ec-ipanel-neutral' : ''}"><h3 class="ec-group-title ec-ipanel-title">${p.title}</h3>`
    + `<div class="ec-ipanel-body${p.one ? ' ec-ipanel-body-1' : ''}">`
    + p.groups.filter(g => g.tiles).map(g =>
      `<section class="ec-igroup hl-item-section">${g.title ? `<h4 class="ec-igroup-title">${g.title}${g.extra ? `<span class="ec-tier-time">${g.extra}</span>` : ''}</h4>` : ''}`
      + `<div class="ec-icards">${g.tiles}</div></section>`).join('')
    + '</div></section>').join('') + '</div>';
}

// ---- HERO CHANGES page: 10 item slots next to the hero name ----
// A picked item's own change blocks (from items/<slug>.html) are added to the
// hero's patch sections, so e.g. Anti-Mage + Battle Fury shows both in 7.41f.
// A patch where only the item changed gets its own section in version order.
// The picks are remembered per hero in this browser (localStorage).
(function() {
  const box = document.querySelector('.ec-islots[data-ec-hero]');
  if (!box) return;
  const KEY = 'ec-hero-items:' + box.dataset.ecHero;
  const slots = [...box.querySelectorAll('[data-ec-islot]')];
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; } };
  const save = v => { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) {} };
  let picks = load().slice(0, slots.length);
  let catalog = null;                              // {panels, by: {slug: [slug, name, icon, current]}}, loaded on first use
  const pages = {};                                // slug -> Promise<Document>

  const getCatalog = () => catalog || (catalog = fetch('../items/picker.json')
    .then(r => { if (!r.ok) throw new Error('picker.json ' + r.status); return r.json(); })
    .then(d => { const by = {}; d.panels.forEach(p => p.groups.forEach(g => g.items.forEach(it => { by[it[0]] = it; }))); return { panels: d.panels, by }; }));
  const getPage = slug => pages[slug] || (pages[slug] = fetch('../items/' + encodeURIComponent(slug) + '.html')
    .then(r => { if (!r.ok) throw new Error(slug + ' ' + r.status); return r.text(); })
    .then(t => new DOMParser().parseFromString(t, 'text/html')));

  // "7.41f" -> comparable [7, 41, 6]; newer patches sort first on the page
  const verKey = v => { const m = /^(\d+)\.(\d+)([a-z]?)$/.exec(v) || []; return [+m[1] || 0, +m[2] || 0, m[3] ? m[3].charCodeAt(0) - 96 : 0]; };
  const newer = (a, b) => { const x = verKey(a), y = verKey(b); for (let i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] > y[i]; return false; };

  function renderSlots(cat) {
    slots.forEach((el, i) => {
      const it = picks[i] && cat && cat.by[picks[i]];
      el.classList.toggle('is-empty', !it);
      el.innerHTML = it ? `<img src="../${esc(it[2])}" alt="${esc(it[1])}"><span class="hl-slot-clear" data-ec-iclear role="button" aria-label="Remove item">x</span>` : '';
    });
  }

  function itemBlock(slug, it, src) {
    const blk = src.querySelector('.entity-block');
    if (!blk) return null;
    const href = '../items/' + encodeURIComponent(slug) + '.html';
    const out = document.createElement('div');
    out.className = blk.className + ' ec-item-inject';
    out.dataset.ecItem = slug;
    out.innerHTML = `<div class="entity item-entity"><div class="entity-icon item-icon"><a class="entity-link" href="${href}"><img src="../${esc(it[2])}" alt="${esc(it[1])}"></a></div>`
      + `<div class="entity-name"><a class="entity-link" href="${href}">${esc(it[1])}</a></div></div>` + blk.innerHTML;
    // the item's own weighted score (the banner above is the hero's, so it is not merged there)
    const score = src.querySelector('h2.ec-ver .ec-score');
    if (score) out.querySelector('.entity').appendChild(score.cloneNode(true));
    return out;
  }

  function sectionFor(ver, src) {
    const id = 'p-' + ver;
    let sec = document.getElementById(id);
    if (sec) return sec;
    sec = document.createElement('section');
    sec.className = 'cat-panel ec-patch ec-item-only';
    sec.id = id;
    const h2 = src.querySelector('h2.ec-ver').cloneNode(true);
    h2.querySelectorAll('.ec-score, .ec-ver-label').forEach(x => x.remove());
    sec.appendChild(h2);
    const all = [...document.querySelectorAll('section.ec-patch')];
    const before = all.find(s => newer(ver, s.id.slice(2)));
    if (before) before.parentNode.insertBefore(sec, before);
    else if (all.length) all[all.length - 1].after(sec);
    else document.querySelector('.container').appendChild(sec);
    return sec;
  }

  let applying = 0;
  async function apply() {
    const run = ++applying;
    const cat = await getCatalog();
    renderSlots(cat);
    const docs = await Promise.all(picks.map(s => s && cat.by[s] ? getPage(s).catch(() => null) : null));
    if (run !== applying) return;                  // a newer pick superseded this one
    document.querySelectorAll('.ec-item-inject').forEach(x => x.remove());
    document.querySelectorAll('section.ec-item-only').forEach(x => x.remove());
    docs.forEach((doc, i) => {
      if (!doc) return;
      const slug = picks[i], it = cat.by[slug];
      doc.querySelectorAll('section.ec-patch[id^="p-"]').forEach(src => {
        const blk = itemBlock(slug, it, src);
        if (blk) sectionFor(src.id.slice(2), src).appendChild(blk);
      });
    });
  }

  // picker: the Hero Lab shop overlay look (hl-* classes), filtered by a search box
  const overlay = document.createElement('div');
  overlay.className = 'hl-overlay ec-ipicker-overlay';
  overlay.hidden = true;
  document.body.appendChild(overlay);
  let activeSlot = -1;
  const close = () => { overlay.hidden = true; overlay.classList.remove('is-open'); activeSlot = -1; };

  // Built once (≈350 lazy icons), then only the selection / search are reset on open.
  let built = false;
  function buildPicker(cat) {
    // the Item Changes index: current roster; an item without a Changes page greyed and not pickable
    const tile = it => {
      const img = `<img src="../${esc(it[2])}" alt="${esc(it[1])}" loading="lazy" decoding="async">`;
      const attrs = `data-name="${esc(it[1].toLowerCase())}" aria-label="${esc(it[1])}"`;
      return it[4]
        ? `<button type="button" class="ec-card ec-card-item hl-item-tile" data-ec-ipick="${esc(it[0])}" ${attrs}>${img}</button>`
        : `<span class="ec-card ec-card-item ec-nopage hl-item-tile" ${attrs}>${img}</span>`;
    };
    const panels = cat.panels.map(p => ({ ...p, title: esc(p.title), groups: p.groups.map(g => ({
      title: esc(g.title), extra: g.extra && esc(g.extra), tiles: g.items.filter(it => it[3]).map(tile).join('') })) }));
    overlay.innerHTML = `<div class="hl-picker-card hl-item-picker-card ec-shop-card is-wide" role="dialog" aria-modal="true" aria-label="Choose item">
      <div class="ec-picker-top"><input type="text" class="hl-picker-search" data-ec-isearch placeholder="Search item..." aria-label="Search item" autocomplete="off">
      <button type="button" class="hl-picker-close" data-ec-iclose aria-label="Close"></button></div>
      <div class="hl-shop-body">${ecShopMarkup(panels)}</div></div>`;
    const input = overlay.querySelector('[data-ec-isearch]');
    input.addEventListener('input', () => {
      const q = input.value.trim().toLowerCase();
      overlay.querySelectorAll('.hl-item-section').forEach(sec => {
        let any = false;
        sec.querySelectorAll('.hl-item-tile').forEach(t => { const ok = !q || t.dataset.name.includes(q); t.classList.toggle('is-hidden', !ok); any = any || ok; });
        sec.classList.toggle('is-hidden', !any);
      });
    });
    built = true;
  }

  async function openPicker(i) {
    activeSlot = i;
    const cat = await getCatalog();
    if (!built) buildPicker(cat);
    overlay.querySelectorAll('.hl-item-tile').forEach(t => {
      t.classList.remove('is-hidden');
      t.classList.toggle('is-selected', !!picks[i] && t.dataset.ecIpick === picks[i]);
    });
    overlay.querySelectorAll('.hl-item-section').forEach(sec => sec.classList.remove('is-hidden'));
    overlay.hidden = false;
    overlay.classList.add('is-open');
    const input = overlay.querySelector('[data-ec-isearch]');
    input.value = '';
    input.focus();
  }

  overlay.addEventListener('click', e => {
    const pick = e.target.closest('[data-ec-ipick]');
    if (pick && activeSlot >= 0) {
      const slug = pick.dataset.ecIpick;
      picks = picks.map(s => (s === slug ? null : s));          // the same item never sits in two slots
      picks[activeSlot] = slug;
      save(picks);
      close();
      apply();
      return;
    }
    if (e.target === overlay || e.target.closest('[data-ec-iclose]')) close();
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !overlay.hidden) close(); });
  slots.forEach((el, i) => el.addEventListener('click', e => {
    if (e.target.closest('[data-ec-iclear]')) {
      picks[i] = null;
      save(picks);
      apply();
      return;
    }
    openPicker(i).catch(err => console.error('item picker:', err));
  }));
  if (picks.some(Boolean)) apply().catch(err => console.error('item slots:', err));
})();
