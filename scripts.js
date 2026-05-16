
(function() {
  // ---- BACK-FROM-CALENDAR ----
  const params = new URLSearchParams(window.location.search);
  const back = document.querySelector('.nav-back-arrow');
  if (params.get('from') === 'calendar' && back) {
    back.classList.add('visible');
  }
  // Vertically center the back-arrow on the toolbar
  function alignBackArrow() {
    if (!back) return;
    const tb = document.querySelector('.toolbar');
    if (!tb) return;
    const r = tb.getBoundingClientRect();
    const center = r.top + r.height / 2;
    const top = Math.round(center - back.offsetHeight / 2);
    back.style.top = top + 'px';
  }
  alignBackArrow();
  window.addEventListener('resize', alignBackArrow, { passive: true });

  // ---- BACK TO TOP visibility ----
  const btt = document.querySelector('.back-to-top');
  function updateBtt() {
    btt.classList.toggle('visible', window.scrollY > 400);
  }
  window.addEventListener('scroll', updateBtt, { passive: true });
  updateBtt();

  // ---- VERSION DROPDOWN toggle ----
  const dropdownBtn = document.querySelector('.version-dropdown .version');
  const dropdownMenu = document.querySelector('.version-dropdown .version-menu');
  if (dropdownBtn && dropdownMenu) {
    dropdownBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const open = dropdownMenu.classList.toggle('open');
      dropdownBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', (e) => {
      if (!dropdownMenu.contains(e.target) && !dropdownBtn.contains(e.target)) {
        dropdownMenu.classList.remove('open');
        dropdownBtn.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        dropdownMenu.classList.remove('open');
        dropdownBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ---- HIDE ABSENT TAGS from toolbar ----
  // The .legend-tags container is set to visibility: hidden by default in
  // styles.css so the user doesn't see all 7 buttons appear and then watch
  // the absent one(s) (e.g. QoL on a patch without QoL rows) disappear on
  // Ctrl+F5. We compute presence, hide the absent buttons, THEN flip the
  // container to visible — a single resolved render, no flash.
  const presentTags = new Set();
  document.querySelectorAll('[data-tag]').forEach(el => {
    (el.dataset.tag || '').split(' ').filter(Boolean).forEach(t => presentTags.add(t));
  });
  // Recipe-changed items count as REWORK even if none of their explicit rows
  // carry t("REWORK") — keep the filter button discoverable on those pages.
  if (document.querySelector('.entity-block.is-changed')) presentTags.add('rework');
  document.querySelectorAll('.filter-btn').forEach(btn => {
    if (!presentTags.has(btn.dataset.filter)) {
      btn.style.display = 'none';
    }
  });
  document.querySelectorAll('.legend-tags').forEach(bar => {
    bar.style.visibility = 'visible';
  });

  // ---- BOLD NUMBERS AND VERSION IN PATCH-AGE ----
  const ageEl = document.querySelector('.patch-age');
  if (ageEl) {
    const text = ageEl.textContent;
    const html = text
      .replace(/\b(\d+\.\d+[a-z]?)\b/g, '<strong>$1</strong>')   // version like 7.41b
      .replace(/\b(\d+)\b(?=\s+days?)/g, '<strong>$1</strong>')   // numbers before "days"
      .replace(/·/g, '<span class="age-sep">·</span>');
    ageEl.innerHTML = html;
  }

  // ---- TAG FILTERING (multi-select, OR semantics) ----
  const buttons = document.querySelectorAll('.filter-btn');
  const activeFilters = new Set();
  function applyFilter() {
    const isActive = activeFilters.size > 0;
    document.body.classList.toggle('filter-active', isActive);
    document.querySelectorAll('.f-hide').forEach(el => el.classList.remove('f-hide'));
    if (!isActive) return;
    document.querySelectorAll('ul.changes > li').forEach(li => {
      const tags = (li.dataset.tag || '').split(' ').filter(Boolean);
      // Items whose recipe changed (entity-block.is-changed) count as REWORK
      // so the REWORK filter keeps their rows visible too.
      if (li.closest('.entity-block.is-changed')) tags.push('rework');
      const matches = tags.some(t => activeFilters.has(t));
      if (!matches) li.classList.add('f-hide');
    });
    // Block-level swap visuals (ability_change) carry their own data-tag and
    // sit outside ul.changes — hide them when none of their tags is active.
    document.querySelectorAll('.ability-change[data-tag]').forEach(block => {
      const tags = (block.dataset.tag || '').split(' ').filter(Boolean);
      if (!tags.some(t => activeFilters.has(t))) block.classList.add('f-hide');
    });
    document.querySelectorAll('ul.changes').forEach(ul => {
      const hasVisible = Array.from(ul.children).some(c => !c.classList.contains('f-hide'));
      if (!hasVisible) ul.classList.add('f-hide');
    });
    document.querySelectorAll('h4.ability-title').forEach(h => {
      let nx = h.nextElementSibling;
      while (nx && nx.tagName !== 'UL') nx = nx.nextElementSibling;
      if (!nx || nx.classList.contains('f-hide')) h.classList.add('f-hide');
    });
    // Hide the entire ability-block (icon + title + ul) if its ul is hidden,
    // otherwise the floating icon stays visible without any text.
    document.querySelectorAll('.ability-block').forEach(block => {
      const ul = block.querySelector('ul.changes');
      if (!ul || ul.classList.contains('f-hide')) {
        block.classList.add('f-hide');
      }
    });
    document.querySelectorAll('.entity-block').forEach(block => {
      const visibleLi    = block.querySelectorAll('ul.changes > li:not(.f-hide)').length;
      const visibleSwaps = block.querySelectorAll('.ability-change:not(.f-hide)').length;
      if (!visibleLi && !visibleSwaps) block.classList.add('f-hide');
    });
  }
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tag = btn.dataset.filter;
      if (activeFilters.has(tag)) {
        activeFilters.delete(tag);
        btn.classList.remove('active');
      } else {
        activeFilters.add(tag);
        btn.classList.add('active');
      }
      applyFilter();
    });
  });

  // ---- CATEGORIES FILTER ----
  // Tag every element between adjacent <h2 class="section"> headers with the
  // preceding section's slug so the buttons can hide non-matching siblings.
  (function indexSections() {
    const headers = document.querySelectorAll('h2.section[data-section]');
    headers.forEach(h => {
      const slug = h.dataset.section;
      let nx = h.nextElementSibling;
      while (nx && !(nx.tagName === 'H2' && nx.classList.contains('section'))) {
        if (!nx.dataset.section) nx.dataset.section = slug;
        nx = nx.nextElementSibling;
      }
    });
  })();
  const catButtons = document.querySelectorAll('.cat-filter-btn');
  const activeCats = new Set();
  function applyCatFilter() {
    const on = activeCats.size > 0;
    document.body.classList.toggle('cat-filter-active', on);
    document.querySelectorAll('[data-section]').forEach(el => {
      el.classList.remove('cat-hide');
      if (on && !activeCats.has(el.dataset.section)) el.classList.add('cat-hide');
    });
  }
  catButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const cat = btn.dataset.category;
      if (activeCats.has(cat)) { activeCats.delete(cat); btn.classList.remove('active'); }
      else { activeCats.add(cat); btn.classList.add('active'); }
      applyCatFilter();
    });
  });

  // ---- FORMULA TABLES (click pill to toggle table) ----
  document.querySelectorAll('.formula-trigger').forEach(trig => {
    trig.addEventListener('click', () => {
      const id = trig.dataset.formula;
      const table = document.getElementById(id);
      if (!table) return;
      const wasHidden = table.hasAttribute('hidden');
      if (wasHidden) {
        table.removeAttribute('hidden');
        trig.classList.add('active');
      } else {
        table.setAttribute('hidden', '');
        trig.classList.remove('active');
      }
    });
  });

  // ---- ENTITY SEARCH ----
  const searchInput = document.getElementById('entity-search');
  const resultsBox = document.getElementById('search-results');
  const entities = [];
  document.querySelectorAll('.entity').forEach(entity => {
    const nameEl = entity.querySelector('.entity-name');
    const imgEl = entity.querySelector('.entity-icon img');
    if (!nameEl) return;
    // Strip the "New X Item" / "Returning Tier N Artifact" / "Recipe changed"
    // labels so the search index uses just the entity name itself.
    const nameClone = nameEl.cloneNode(true);
    nameClone.querySelectorAll('.entity-new-type, .entity-changed-type').forEach(n => n.remove());
    let kind = 'mechanic';
    if (entity.classList.contains('hero-entity')) kind = 'hero';
    else if (entity.classList.contains('unit-entity')) kind = 'creep';
    else if (entity.classList.contains('item-entity')) kind = 'item';
    if (entity.dataset && entity.dataset.kind) kind = entity.dataset.kind;
    entities.push({
      name: nameClone.textContent.trim().replace(/\s+/g, ' '),
      element: entity,
      icon: imgEl ? imgEl.src : null,
      kind: kind
    });
  });
  // Also index ability titles (h4.ability-title) — pull icon from the .ability-block
  // wrapper so search results show the same picture as the ability heading.
  // For innate abilities, Valve doesn't expose icons on the React CDN; the
  // canonical image is the innate marker, so use that directly in search.
  document.querySelectorAll('h4.ability-title').forEach(h => {
    const block = h.closest('.ability-block');
    const imgEl = block ? block.querySelector('.ability-icon-img') : null;
    const isInnate = block ? block.classList.contains('is-innate') : false;
    const innateUrl = '../icons/misc/innate_icon.png';
    entities.push({
      name: h.textContent.trim(),
      element: h,
      icon: isInnate ? innateUrl : (imgEl ? imgEl.src : null),
      kind: 'ability'
    });
  });

  function escapeHtml(s) { return s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
  function highlight(name, q) {
    const idx = name.toLowerCase().indexOf(q.toLowerCase());
    if (idx === -1) return escapeHtml(name);
    return escapeHtml(name.slice(0, idx)) +
           '<mark>' + escapeHtml(name.slice(idx, idx + q.length)) + '</mark>' +
           escapeHtml(name.slice(idx + q.length));
  }

  let activeIdx = -1;

  function render(query) {
    if (!query) {
      resultsBox.classList.remove('show');
      resultsBox.innerHTML = '';
      activeIdx = -1;
      return;
    }
    const q = query.toLowerCase();
    const matches = entities.filter(e => e.name.toLowerCase().includes(q)).slice(0, 12);
    if (matches.length === 0) {
      resultsBox.innerHTML = '<div class="empty">no matches</div>';
      resultsBox.classList.add('show');
      activeIdx = -1;
      return;
    }
    resultsBox.innerHTML = matches.map((m, i) =>
      `<div class="result-item" data-idx="${i}">${
        m.icon
          ? `<img src="${m.icon}" alt="" onerror="this.onerror=null;this.src='../icons/misc/missing.svg';">`
          : '<span style="width:32px;display:inline-block"></span>'
      }<span>${highlight(m.name, query)}</span><span class="kind">${m.kind}</span></div>`
    ).join('');
    resultsBox.classList.add('show');
    activeIdx = -1;

    resultsBox.querySelectorAll('.result-item').forEach((el, i) => {
      el.addEventListener('mouseenter', () => { setActive(i); });
      el.addEventListener('click', () => { jumpTo(matches[i]); });
    });
    window._currentMatches = matches;
  }

  function setActive(i) {
    activeIdx = i;
    resultsBox.querySelectorAll('.result-item').forEach((el, idx) => {
      el.classList.toggle('active', idx === i);
    });
  }

  function jumpTo(target) {
    if (!target) return;
    target.element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    target.element.style.transition = 'box-shadow 0.4s';
    target.element.style.boxShadow = '0 0 0 2px #58a6ff';
    setTimeout(() => target.element.style.boxShadow = '', 1400);
    searchInput.value = '';
    resultsBox.classList.remove('show');
    resultsBox.innerHTML = '';
  }

  searchInput.addEventListener('input', () => render(searchInput.value));
  searchInput.addEventListener('keydown', (e) => {
    const items = resultsBox.querySelectorAll('.result-item');
    if (!items.length) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((activeIdx + 1) % items.length); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((activeIdx - 1 + items.length) % items.length); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      const idx = activeIdx >= 0 ? activeIdx : 0;
      if (window._currentMatches && window._currentMatches[idx]) jumpTo(window._currentMatches[idx]);
    }
    else if (e.key === 'Escape') {
      searchInput.value = '';
      render('');
    }
  });
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !resultsBox.contains(e.target)) {
      resultsBox.classList.remove('show');
    }
  });

  // ---- ABILITY-CHANGE CONNECTOR ----
  // Draws a thin dashed curve from each ability-change-block's icon
  // bottom-center down-right to the centre of the LEFT BORDER of the OLD
  // pane. Recomputed on load and on resize so the line tracks the actual
  // layout (icon position, pane geometry).
  function drawAbilityChangeConnectors() {
    const blocks = document.querySelectorAll('.ability-change-block');
    blocks.forEach((block) => {
      const svg = block.querySelector(':scope > .ability-change-connector');
      const path = svg && svg.querySelector('path');
      const icon = block.querySelector(':scope > .ability-icon-wrap');
      const oldPane = block.querySelector(
        ':scope > .ability-change > .ability-change-pane.ability-change-old'
      );
      if (!svg || !path || !icon || !oldPane) return;
      const blockRect = block.getBoundingClientRect();
      const iconRect = icon.getBoundingClientRect();
      const paneRect = oldPane.getBoundingClientRect();
      if (!blockRect.width || !paneRect.width) return;
      // Cover the whole block so we have a global coordinate system for
      // the path; absolute positioning relative to block (which is
      // position: relative).
      svg.setAttribute('width', blockRect.width);
      svg.setAttribute('height', blockRect.height);
      svg.setAttribute('viewBox', '0 0 ' + blockRect.width + ' ' + blockRect.height);
      svg.style.left = '0px';
      svg.style.top = '0px';
      svg.style.width = blockRect.width + 'px';
      svg.style.height = blockRect.height + 'px';
      // Start: bottom-center of icon
      const x1 = iconRect.left - blockRect.left + iconRect.width / 2;
      const y1 = iconRect.bottom - blockRect.top;
      // End: centre of left border of old pane
      const x2 = paneRect.left - blockRect.left;
      const y2 = paneRect.top - blockRect.top + paneRect.height / 2;
      // L-shape with a right-angle elbow: vertical segment down from the
      // icon, then horizontal segment right to the pane's left edge.
      const d = 'M ' + x1 + ' ' + y1 + ' L ' + x1 + ' ' + y2 + ' L ' + x2 + ' ' + y2;
      path.setAttribute('d', d);
    });
  }
  drawAbilityChangeConnectors();
  window.addEventListener('resize', drawAbilityChangeConnectors);
  // Also re-run after fonts/images settle so the layout has its final
  // dimensions (icon images may load late and shift the icon position).
  window.addEventListener('load', drawAbilityChangeConnectors);

  // ---------------------------------------------------------------------
  // PATCH DYNAMICS WIDGET
  // ---------------------------------------------------------------------
  // For every .entity on the page, fetch _dynamics.json once, derive the
  // entity's (kind, slug) from its DOM id ("dyn-<kind>-<slug>"), and append
  // a row of diamond pills — one per recent patch. Each pill shows a
  // proportional gradient of tag colors; untouched pills are dark/glassy.
  // Click on a touched pill navigates to that patch HTML, scrolling to the
  // same entity anchor when present.
  // Tag colors rendered with alpha so the fluid layer reads as translucent
  // liquid sitting inside a recessed glass diamond rather than a solid pill.
  const DYN_TAG_COLORS = {
    buff:   'rgba(93, 177, 78, 0.78)',
    nerf:   'rgba(209, 75, 75, 0.78)',
    new:    'rgba(78, 201, 176, 0.78)',
    del:    'rgba(177, 78, 107, 0.78)',
    rework: 'rgba(164, 114, 207, 0.78)',
    misc:   'rgba(139, 144, 153, 0.78)',
    qol:    'rgba(108, 171, 240, 0.78)',
  };
  const DYN_TAG_LABEL = {
    buff:'BUFF', nerf:'NERF', new:'NEW', del:'DEL',
    rework:'REWORK', misc:'MISC', qol:'QoL',
  };
  const DYN_TAG_ORDER = ['buff','new','rework','qol','misc','del','nerf'];
  const DYN_MAX_PATCHES = 12;

  function dynBuildPill(patch, counts, entityId, isCurrent) {
    const total = DYN_TAG_ORDER.reduce((s, t) => s + (counts[t] || 0), 0);
    const clickable = total > 0 && patch.filename && !isCurrent;
    // Wrapper holds the diamond (.dyn-cell) AND the tooltip (.dyn-tip) as
    // siblings. The diamond uses clip-path which would clip any tooltip
    // pseudo-element, so the tooltip must live outside that clipped subtree.
    const wrap = document.createElement(clickable ? 'a' : 'span');
    let wcls = 'dyn-cell-wrap';
    if (!total) wcls += ' empty';
    if (isCurrent) wcls += ' current';
    if (total && !patch.filename) wcls += ' no-page';
    wrap.className = wcls;
    const cell = document.createElement('span');
    cell.className = 'dyn-cell';
    wrap.appendChild(cell);
    if (total) {
      // Build a vertical gradient where each tag occupies a band proportional
      // to its share. Instead of hard color-stops at the band boundaries we
      // leave a `bleed` zone on each side so adjacent colors interpolate
      // across it — this produces the soft "liquid floating at different
      // densities" look rather than crisp horizontal stripes. The bleed is
      // capped to half the band width to stay within the segment.
      const tags = DYN_TAG_ORDER.filter(t => counts[t] > 0);
      const bleed = 7;  // % half-width of the smoothing zone between bands
      let acc = 0;
      const stops = [];
      for (let i = 0; i < tags.length; i++) {
        const t = tags[i];
        const c = counts[t];
        const start = (acc / total) * 100;
        acc += c;
        const end = (acc / total) * 100;
        const halfBand = (end - start) / 2;
        const localBleed = Math.min(bleed, halfBand);
        const solidStart = i === 0 ? start : start + localBleed;
        const solidEnd = i === tags.length - 1 ? end : end - localBleed;
        stops.push(`${DYN_TAG_COLORS[t]} ${solidStart.toFixed(1)}%`);
        stops.push(`${DYN_TAG_COLORS[t]} ${solidEnd.toFixed(1)}%`);
      }
      cell.style.setProperty('--dyn-bg', `linear-gradient(to bottom, ${stops.join(', ')})`);
      if (clickable) {
        wrap.href = patch.filename + (entityId ? '#' + entityId : '');
      }
      const lines = DYN_TAG_ORDER
        .filter(t => counts[t])
        .map(t => `${DYN_TAG_LABEL[t]}: ${counts[t]}`);
      const suffix = isCurrent ? '\n(current patch)'
                   : patch.filename ? ''
                   : '\n(no patch page yet)';
      wrap.appendChild(dynBuildTip(
        `${patch.version} (${patch.date})\n${lines.join('  ·  ')}${suffix}`));
    } else {
      wrap.appendChild(dynBuildTip(
        `${patch.version} (${patch.date})\nnot touched` + (isCurrent ? '\n(current patch)' : '')));
    }
    return wrap;
  }

  // Tooltip popup — a real DOM sibling of .dyn-cell (not a pseudo) so it
  // escapes the diamond's clip-path. Multi-line text preserved via pre-line.
  function dynBuildTip(text) {
    const tip = document.createElement('span');
    tip.className = 'dyn-tip';
    tip.textContent = text;
    return tip;
  }

  // Read current patch version from the version-picker button in the top nav.
  // Falls back to the document title ("Dota Patch Notes - 7.41a") if needed.
  function dynCurrentVersion() {
    const btn = document.querySelector('.version-picker .version');
    if (btn) {
      const m = btn.textContent.match(/(\d+\.\d+[a-z]?)/);
      if (m) return m[1];
    }
    const t = document.title.match(/(\d+\.\d+[a-z]?)\s*$/);
    return t ? t[1] : null;
  }

  // Known entity kinds — must match the strings emitted by _register_entity()
  // in build_patch.py. Ordered longest-first so "creep-hero" wins over "creep".
  const DYN_KINDS = ['creep-hero', 'hero', 'item', 'unit', 'plain', 'enchant'];

  // Cache the per-page patches window so we compute it once, not 250+ times.
  // Pure function of manifest + current version → ordered patches array.
  function dynWindow(manifest, currentVersion) {
    // manifest.patches is newest-first per RELEASE_HISTORY. Find current
    // patch index; window 12 entries starting AT it (current + 11 older).
    // Then reverse so oldest is on the left in the rendered row.
    const all = manifest.patches;
    let idx = all.findIndex(p => p.version === currentVersion);
    if (idx < 0) idx = 0;  // unknown version → start at newest
    return all.slice(idx, idx + 12).reverse();
  }

  function dynRenderRow(entityDiv, manifest, windowed, currentVersion) {
    const id = entityDiv.id || '';
    if (!id.startsWith('dyn-')) return;
    const rest = id.slice(4);
    const kind = DYN_KINDS.find(k => rest === k || rest.startsWith(k + '-'));
    if (!kind) return;
    const slug = rest.slice(kind.length + 1);
    const key = kind + '|' + slug;
    const rec = manifest.entities[key];
    const perPatch = (rec && rec.patches) || {};
    const row = document.createElement('div');
    row.className = 'patch-dynamics';
    for (const p of windowed) {
      const counts = perPatch[p.version] || {};
      row.appendChild(dynBuildPill(p, counts, id, p.version === currentVersion));
    }
    entityDiv.appendChild(row);
  }

  function dynInit() {
    const entities = document.querySelectorAll('.entity[id^="dyn-"]');
    if (!entities.length) return;
    const currentVersion = dynCurrentVersion();
    fetch('../_dynamics.json', { cache: 'no-cache' })
      .then(r => r.ok ? r.json() : null)
      .then(manifest => {
        if (!manifest) return;
        const windowed = dynWindow(manifest, currentVersion);
        entities.forEach(e => dynRenderRow(e, manifest, windowed, currentVersion));
      })
      .catch(() => { /* silently fail — widget is an enhancement */ });
  }
  dynInit();
})();

