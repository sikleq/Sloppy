
(function() {
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

  // ---- TAG FILTERING (multi-select, OR semantics) ----
  const buttons = document.querySelectorAll('.filter-btn');
  const activeFilters = new Set();
  function elementVisible(el) {
    return !!el && !el.classList.contains('f-hide') && !el.classList.contains('cat-hide');
  }
  // A row an item card already shows (li.iab-covered, CSS-hidden) still carries its tag for the filters, but
  // it is never what keeps a block on screen: its card is (owner 2026-09-27, Witch Blade under BUFF showed a
  // bare header).
  function rowOnScreen(li) {
    return elementVisible(li) && !li.classList.contains('iab-covered');
  }
  // A card is shown under a non-REWORK filter when it holds a chip of an active tag, or took over a hidden
  // row that matches: covered-cost -> the components card, covered-iab -> the abilities card.
  function panelMatches(el) {
    const hit = node => (node.dataset.tag || '').split(' ').some(t => activeFilters.has(t));
    if (hit(el) || Array.from(el.querySelectorAll('[data-tag]')).some(hit)) return true;
    const block = el.closest('.entity-block');
    const kind = el.classList.contains('iab-change') ? 'covered-iab'
      : el.classList.contains('components-change') ? 'covered-cost'
      : el.classList.contains('ench-change') ? 'covered-ench' : null;   // an enchantment's tier table (7.41)
    return !!(block && kind && block.querySelector(`ul.changes > li.${kind}:not(.f-hide):not(.cat-hide)`));
  }
  function refreshPatchFilterLayout() {
    document.querySelectorAll('ul.changes').forEach(ul => {
      const hasVisible = Array.from(ul.children).some(rowOnScreen);
      ul.classList.toggle('f-hide', !hasVisible);
    });
    document.querySelectorAll('h4.ability-title').forEach(h => {
      let nx = h.nextElementSibling;
      while (nx && nx.tagName !== 'UL') nx = nx.nextElementSibling;
      if (nx) h.classList.toggle('f-hide', !elementVisible(nx));
    });
    // A header-only ability (Primal Split above its Brewlings, ab-empty) has no rows of its own: it follows the
    // ability blocks right under it. Hiding it as "no visible rows" kept it hidden for good after a category
    // filter was switched off (owner 2026-10-21, Brewmaster 7.41).
    const tagFiltering = activeFilters.size > 0;
    const headerOnly = [];
    document.querySelectorAll('.ability-block').forEach(block => {
      const ul = block.querySelector('ul.changes');
      if (!ul) { headerOnly.push(block); return; }
      block.classList.toggle('f-hide', !elementVisible(ul));
    });
    headerOnly.forEach(block => {
      const h = block.querySelector('h4.ability-title');
      let nx = block.nextElementSibling;
      let shown = !tagFiltering || !!block.querySelector('.ability-change:not(.f-hide):not(.cat-hide)');
      while (!shown && nx && nx.classList.contains('ability-block') && !nx.classList.contains('ab-empty')) {
        if (elementVisible(nx)) shown = true;
        nx = nx.nextElementSibling;
      }
      block.classList.toggle('f-hide', !shown);
      if (h) h.classList.toggle('f-hide', !shown);
    });
    // Component/stat panels (.properties-change, .components-change, etc.) belong to the REWORK filter;
    // under any other filter a panel stays only when it holds a matching tag (panelMatches), so items with
    // recipe changes don't bleed through QoL/BUFF/etc. filters.
    const reworkOnly = activeFilters.size > 0 && !activeFilters.has('rework');
    // top-level panels only: a components card's own two panes are .components-box too (hiding them left a
    // bare arrow under a filter, owner 2026-09-28)
    const PANELS = ':scope > .components-box, :scope > .components-change, :scope > .provides-box, :scope > .properties-change, :scope > .ench-tiers';   // .ench-tiers: an enchantment table row (7.38)
    document.querySelectorAll('.entity-block').forEach(block => {
      block.querySelectorAll(PANELS).forEach(el => {
        if (reworkOnly && !panelMatches(el)) el.classList.add('f-hide');
      });
    });
    const filtering = activeFilters.size > 0;
    document.querySelectorAll('.entity-block').forEach(block => {
      if (block.classList.contains('ec-head')) return;   // Changes-page header: never filtered
      // no tag filter on: every block shows (a sub-category label or a block without rows stayed hidden
      // after a filter was switched off, owner 2026-09-28)
      if (!filtering) { block.classList.remove('f-hide'); return; }
      if (block.classList.contains('label-only') || block.classList.contains('enchant-list-head')) return;  // decided below, from the blocks under it
      const visibleLi = block.querySelectorAll('ul.changes > li:not(.f-hide):not(.cat-hide):not(.iab-covered)').length;
      const visibleSwaps = block.querySelectorAll('.ability-change:not(.f-hide):not(.cat-hide)').length;
      const visiblePanels = Array.from(block.children).some(child =>
        child.matches('.components-box, .components-change, .provides-box, .properties-change, .ench-tiers') &&
        elementVisible(child)
      );
      block.classList.toggle('f-hide', !visibleLi && !visibleSwaps && !visiblePanels);
    });
    // A sub-category label ("List of Neutral Artifacts") shows while any block under it (up to the next
    // label or category) is visible.
    if (filtering) document.querySelectorAll('.entity-block.label-only, .entity-block.enchant-list-head').forEach(label => {
      let nx = label.nextElementSibling, shown = false;
      while (nx && !nx.classList.contains('label-only') && !nx.matches('h2.section')) {
        if (nx.classList.contains('entity-block') && elementVisible(nx)) { shown = true; break; }
        nx = nx.nextElementSibling;
      }
      label.classList.toggle('f-hide', !shown);
    });
    document.querySelectorAll('h4.subgroup').forEach(h => {
      let nx = h.nextElementSibling;
      let hasVisibleContent = false;
      while (nx && !nx.matches('h4.subgroup')) {
        if (elementVisible(nx)) {
          hasVisibleContent = true;
          break;
        }
        nx = nx.nextElementSibling;
      }
      h.classList.toggle('f-hide', !hasVisibleContent);
    });
    // Collapse a whole category section (section.cat-panel, incl. its h2.section
    // header + slab) when every entity inside it was filtered out — otherwise an
    // emptied section leaves a bare slab strip between two visible sections.
    // Runs AFTER the entity-block pass above so each block's f-hide is settled.
    document.querySelectorAll('section.cat-panel').forEach(panel => {
      if (panel.classList.contains('ec-head-panel')) return;
      const hasVisible = panel.querySelector('.entity-block:not(.f-hide):not(.cat-hide)');
      panel.classList.toggle('f-hide', !hasVisible);
    });
    // The entity-block top hairline is suppressed on the section's FIRST block
    // (`h2.section + .entity-block`), but once filtering hides earlier blocks the
    // first SURVIVING block isn't that one anymore → an orphan line appears under
    // the category header. Re-mark the first visible block per section so CSS can
    // drop its top border.
    document.querySelectorAll('.entity-block.first-visible')
      .forEach(b => b.classList.remove('first-visible'));
    document.querySelectorAll('section.cat-panel:not(.f-hide)').forEach(panel => {
      const first = panel.querySelector('.entity-block:not(.f-hide):not(.cat-hide)');
      if (first) first.classList.add('first-visible');
    });
    drawBrewlingConnectors();
  }
  function applyFilter() {
    const isActive = activeFilters.size > 0;
    document.body.classList.toggle('filter-active', isActive);
    document.querySelectorAll('.f-hide').forEach(el => el.classList.remove('f-hide'));
    if (!isActive) {
      refreshPatchFilterLayout();
      return;
    }
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
    refreshPatchFilterLayout();
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
    refreshPatchFilterLayout();
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
      requestAnimationFrame(drawBrewlingConnectors);
    });
  });

  // ---- ENTITY SEARCH ----
  // Guard: pages without the search box (e.g. creeps.html) skip this whole
  // block. Without the guard, searchInput.addEventListener below throws on
  // null and halts the script — which silently broke later handlers.
  const searchInput = document.getElementById('entity-search');
  const resultsBox = document.getElementById('search-results');
  if (searchInput && resultsBox) {
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
  // Innate abilities that have their own icon (e.g. Invoker's Invoke =
  // invoker_invoke.png + small innate marker overlay) should still use that
  // icon in search results; only fall back to the generic innate marker when
  // Valve doesn't expose a dedicated icon on the React CDN.
  // A facet's picture is an icon on its colour, so a result needs both.
  const facetLook = (wrap) => wrap ? {
    iconBg: wrap.style.backgroundImage,
    icon: (wrap.querySelector('img') || {}).src || null
  } : null;
  document.querySelectorAll('h4.ability-title').forEach(h => {
    const block = h.closest('.ability-block');
    if (!block) return;
    const isFacet = block.classList.contains('facet-block');
    // Several abilities or facets in one block: each is found by its own name, with its own picture.
    const tiles = block.querySelectorAll(':scope > .ability-icon-stack > .stack-icon');
    if (tiles.length) {
      tiles.forEach(tile => {
        const img = tile.querySelector('img');
        const look = facetLook(tile.querySelector('.stack-facet-tile'));
        entities.push(Object.assign({
          name: tile.getAttribute('aria-label'),
          element: h,
          icon: img ? img.src : null,
          kind: isFacet ? 'facet' : 'ability'
        }, look));
      });
      return;
    }
    const imgEl = block.querySelector('.ability-icon-img');
    const isInnate = block.classList.contains('is-innate');
    const innateUrl = '../icons/misc/innate_icon.png';
    const realIcon = imgEl ? imgEl.src : null;
    const look = facetLook(block.querySelector(':scope > .facet-icon-wrap, :scope > .ability-icon-wrap > .facet-ability-icon'));
    // a renamed ability ("Call of the Wild Hawk → Summon Raptors") is found by each name, shown as that name alone
    // (owner 2026-11-06: "в поиске пишется вместе со стрелочкой и другим названием")
    const oldEl = h.querySelector('.ability-title-old'), newEl = h.querySelector('.ability-title-new');
    const names = newEl ? [newEl.textContent.trim()].concat(oldEl ? [oldEl.textContent.trim()] : []) : [h.textContent.trim()];
    names.forEach(name => entities.push(Object.assign({
      name: name,
      element: h,
      icon: realIcon || (isInnate ? innateUrl : null),
      kind: isFacet ? 'facet' : 'ability'
    }, look)));
  });
  // An ability named only by its small icon in a row (a facet's "Exorcism: …"): once per name, unless a block has it.
  const indexed = new Set(entities.map(e => e.name.toLowerCase()));
  document.querySelectorAll('.ability-chip[aria-label], .facet-chip[aria-label]').forEach(chip => {
    const name = chip.getAttribute('aria-label');
    if (indexed.has(name.toLowerCase()) || chip.closest('[hidden], details:not([open])')) return;
    indexed.add(name.toLowerCase());
    const isFacet = chip.classList.contains('facet-chip');
    const img = chip.querySelector('img');
    entities.push(Object.assign({
      name: name,
      element: chip.closest('li') || chip,
      icon: img ? img.src : null,
      kind: isFacet ? 'facet' : 'ability'
    }, isFacet ? facetLook(chip) : null));
  });

  // An ability named only in a card's head ("Active: Tree Dance" in 7.38 Simian Stride's card): found too, with the
  // head's own icon or its block's (owner 2026-11-06: "Tree dance … перестал искаться через поиск")
  document.querySelectorAll('.ability-change-pane .iab-head .iab-name').forEach(nameEl => {
    const name = nameEl.textContent.trim();
    if (!name || /^Aghanim's /.test(name) || indexed.has(name.toLowerCase())) return;
    indexed.add(name.toLowerCase());
    const head = nameEl.closest('.iab-head');
    const block = head.closest('.ability-block');
    const img = head.querySelector('.ability-chip img') || (block && block.querySelector('.ability-icon-wrap img'));
    const isFacet = !!(block && block.classList.contains('facet-block'));
    entities.push(Object.assign({
      name: name,
      element: head,
      icon: img ? img.src : null,
      kind: 'ability'
    }, isFacet && !head.querySelector('.ability-chip') ? facetLook(block.querySelector(':scope > .facet-icon-wrap')) : null));
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
        m.iconBg
          ? `<span class="result-facet" style="background-image:${m.iconBg.replace(/"/g, "'")}">${
              m.icon ? `<img src="${m.icon}" alt="">` : ''}</span>`
          : m.icon
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
    // If active filters are hiding the target, reset them so it becomes visible.
    if (target.element.closest('.f-hide, .cat-hide')) {
      activeFilters.clear();
      buttons.forEach(b => b.classList.remove('active'));
      activeCats.clear();
      catButtons.forEach(b => b.classList.remove('active'));
      applyFilter();
      applyCatFilter();
    }
    // Offset for the sticky nav so the heading lands just BELOW it. Plain
    // scrollIntoView({block:'start'}) parks the heading at viewport top, hidden
    // behind the nav — so you see the rows under it and it reads as "jumped
    // past / below the result". Mirror the re-anchor offset used on load.
    const navH = parseFloat(getComputedStyle(document.documentElement)
      .getPropertyValue('--site-nav-h')) || 70;
    const toolbarEl = document.querySelector('.toolbar');
    const toolbarH = toolbarEl ? toolbarEl.getBoundingClientRect().height : 0;
    // straight there, as Ctrl+F does, and the found block lit for a moment so the eye knows where it stopped (owner
    // 2026-11-06: "тебя буквально физически переносит по странице … непонятно, где остановился поиск")
    const y = target.element.getBoundingClientRect().top + window.scrollY - navH - toolbarH - 8;
    window.scrollTo({ top: Math.max(0, y), behavior: 'instant' });
    const hit = target.element.closest('.ability-block, .entity, li') || target.element;
    hit.classList.remove('search-hit');
    void hit.offsetWidth;                                       // restart the flash on a second jump to the same block
    hit.classList.add('search-hit');
    setTimeout(() => hit.classList.remove('search-hit'), 2600);
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
  // Prevent scroll propagation to the page on Safari.
  if (resultsBox) {
    resultsBox.addEventListener('touchmove', (e) => { e.stopPropagation(); }, { passive: true });
  }
  } // end if (searchInput && resultsBox)

  // ---- ABILITY-CHANGE CONNECTOR ----
  // Draws a thin solid line from the bottom of each ability block's icon straight down into its card: the card starts
  // under the icon's left edge, so the line stays over it (owner 2026-11-04, variant 1 of the mock, instead of a dashed
  // line round the icon). With rows between them it runs through the empty place under the icon.
  // Recomputed on load and on resize so the line tracks the actual layout.
  function connectorPath(blockRect, iconRect, paneRect) {
    const x = iconRect.left - blockRect.left + iconRect.width / 2;
    return 'M ' + x + ' ' + (iconRect.bottom - blockRect.top) + ' L ' + x + ' ' + (paneRect.top - blockRect.top);
  }
  function drawAbilityChangeConnectors() {
    const blocks = document.querySelectorAll('.ability-change-block');
    blocks.forEach((block) => {
      const svg = block.querySelector(':scope > .ability-change-connector:not(.under-rows-connector)');
      const path = svg && svg.querySelector('path');
      const icon = block.querySelector(':scope > .ability-icon-wrap');
      // a card of a new ability has only its new pane
      const oldPane = block.querySelector(
        ':scope > .ability-change > .ability-change-old, :scope > .ability-change > .ability-change-new'
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
      path.setAttribute('d', connectorPath(blockRect, iconRect, paneRect));
    });
    // An old -> new card under an ability's rows (Aghanim's upgrade, what it scales with — 2026-10-25): the same
    // line from the ability's icon to that card's old pane; the svg sits right before the card's caption.
    document.querySelectorAll('.ability-block > svg.under-rows-connector').forEach((svg) => {
      const block = svg.parentElement;
      const path = svg.querySelector('path');
      const icon = block.querySelector(':scope > .ability-icon-wrap');
      let card = svg.nextElementSibling;
      while (card && !card.classList.contains('ability-change') && !card.classList.contains('ability-card-rows')) {
        card = card.nextElementSibling;
      }
      // a one-sided card (an upgrade added / removed) has only its new or old pane; a new creep's ability, its box
      const oldPane = card && card.querySelector(':scope > .ability-change-old, :scope > .ability-change-new, :scope > li');
      if (!path || !icon || !oldPane) return;
      const blockRect = block.getBoundingClientRect();
      const iconRect = icon.getBoundingClientRect();
      const paneRect = oldPane.getBoundingClientRect();
      if (!blockRect.width || !paneRect.width) return;
      svg.setAttribute('viewBox', '0 0 ' + blockRect.width + ' ' + blockRect.height);
      svg.style.width = blockRect.width + 'px';
      svg.style.height = blockRect.height + 'px';
      // another card between the icon and this one (7.38 Flux: its own card, then the Scepter's): the line starts under
      // that card, it does not run through it (owner 2026-11-05)
      let before = svg.previousElementSibling;
      while (before && !before.classList.contains('ability-change')) before = before.previousElementSibling;
      const start = before ? { left: iconRect.left, width: iconRect.width, bottom: before.getBoundingClientRect().bottom } : iconRect;
      path.setAttribute('d', connectorPath(blockRect, start, paneRect));
    });
    // Aghanim's cards are top-anchored (styles.css, 2026-10-26): the arrow stands at the middle of the OLD pane, not of
    // the taller new side (owner, 7.41 Techies: "стрелочка теперь не соотносится к левой карточке"). On a phone the
    // panes stack and the arrow sits between them: no shift.
    document.querySelectorAll('.ability-change.aghs-change').forEach((card) => {
      const arrow = card.querySelector(':scope > .ability-change-arrow');
      const oldPane = card.querySelector(':scope > .ability-change-old');
      if (!arrow || !oldPane) return;
      arrow.style.marginTop = '';
      const a = arrow.getBoundingClientRect();
      const p = oldPane.getBoundingClientRect();
      if (!p.height || a.top >= p.bottom) return;              // stacked layout
      arrow.style.marginTop = Math.max(0, p.top - a.top + (p.height - a.height) / 2) + 'px';
    });
  }
  // A lone one-sided card to the right of its block (owner 2026-11-06, patch/card_pairs.py): a line from the end of its
  // caption's words ("Added Aghanim's Scepter.", "New facet") straight to the card's left edge. None when they stack.
  function drawSingleRightLines() {
    document.querySelectorAll('.single-right').forEach((box) => {
      const line = box.querySelector(':scope > .sr-line');
      const card = box.querySelector(':scope > .ability-change');
      const caps = box.querySelectorAll(':scope > .ability-block > ul.ability-change-summary-ul li .row-text');
      const cap = caps[caps.length - 1];
      if (!line || !card || !cap) return;
      const range = document.createRange();
      range.selectNodeContents(cap);
      const t = range.getBoundingClientRect();
      const c = card.getBoundingClientRect();
      const b = box.getBoundingClientRect();
      if (!c.width || !t.width || c.left <= t.right || card.offsetParent === null) { line.style.display = 'none'; return; }
      line.style.display = '';
      line.style.left = (t.right - b.left + 8) + 'px';
      line.style.top = Math.round(t.top - b.top + t.height / 2) + 'px';
      line.style.width = Math.max(0, c.left - t.right - 8) + 'px';
    });
  }
  drawAbilityChangeConnectors();
  drawSingleRightLines();
  window.addEventListener('resize', drawSingleRightLines);
  window.addEventListener('load', drawSingleRightLines);

  window.addEventListener('resize', drawAbilityChangeConnectors);
  // Also re-run after fonts/images settle so the layout has its final
  // dimensions (icon images may load late and shift the icon position).
  window.addEventListener('load', drawAbilityChangeConnectors);
  // Re-run when an inline formula table toggles open/closed inside an
  // ability_change block — the block's height changes, so the SVG canvas
  // dimensions (which cover blockRect.height) must be recalculated.
  document.addEventListener('toggle', (e) => {
    if (e.target && e.target.closest && e.target.closest('.ability-change-block')) {
      drawAbilityChangeConnectors();
    }
  }, true);

  // ---------------------------------------------------------------------
  // Brewling connector — dashed lines from Primal Split icon down to each
  // of the four brewling ability blocks (Earth / Storm / Fire / Void).
  // Same dashed style as the ability_change-connector (.ability-change-
  // connector path), but a single SVG attached to <body> overlays multiple
  // ability blocks via document-level coordinates.
  // ---------------------------------------------------------------------
  // Ability-tree groups: a parent ability icon dashed-linked down to its
  // child blocks. Used for Brewmaster's Primal Split → brewlings and
  // Drunken Brawler → stances (same visual concept).
  const ABILITY_TREES = [
    {
      parent: 'brewmaster_primal_split',
      children: [
        'brewmaster_earth_unit',
        'brewmaster_storm_unit',
        'brewmaster_fire_unit',
        'brewmaster_void_unit',
      ],
    },
    {
      parent: 'brewmaster_drunken_brawler',
      children: [
        'brewmaster_drunken_brawler_earth',
        'brewmaster_drunken_brawler_storm',
        'brewmaster_drunken_brawler_fire',
        'brewmaster_drunken_brawler_void',
      ],
    },
    {
      parent: 'invoker_quas_focus',
      children: [
        'invoker_quas',
        'invoker_cold_snap',
        'invoker_ice_wall',
        'invoker_ghost_walk',
      ],
    },
    {
      parent: 'invoker_wex_focus',
      children: [
        'invoker_wex',
        'invoker_alacrity',
        'invoker_tornado',
      ],
    },
    {
      parent: 'invoker_exort_focus',
      children: [
        'invoker_exort',
        'invoker_chaos_meteor',
        'invoker_sun_strike',
      ],
    },
    {
      parent: 'ringmaster_sideshow_secrets',
      children: [
        'ringmaster_crystal_ball',
        'ringmaster_summon_unicycle',
        'ringmaster_weighted_pie',
      ],
    },
  ];
  window.SLOPPY_ABILITY_TREES = ABILITY_TREES;      // the Changes-page filters show a parent's children

  function drawBrewlingConnectors() {
    // Remove any existing SVGs so we can redraw fresh on each call.
    document.querySelectorAll('svg.brewling-connector').forEach((s) => s.remove());
    ABILITY_TREES.forEach((tree) => drawAbilityTree(tree.parent, tree.children));
  }

  // Resolve the anchor element for connector lines: always use the
  // .ability-icon-wrap (48×48 column) rather than the img itself, so
  // ability_change children (which have 128×128 icons in a different layout)
  // are anchored at the same position as regular ability blocks.
  function resolveAnchor(img) {
    const wrap = img.closest('.ability-icon-wrap, .facet-icon-wrap');
    return wrap || img;
  }

  // A hero Changes page stacks many patches: parent and children are looked up inside ONE patch
  // section (or one entity block on a patch page), else Cold Snap in 7.41f was joined to a Quas block
  // several patches below by a dashed line across the whole screen (owner 2026-09-26).
  function drawAbilityTree(parentSlug, childSlugs) {
    document.querySelectorAll('img[data-slug="' + parentSlug + '"]').forEach(function (img) {
      const scope = img.closest('section.ec-patch') || img.closest('.entity-block') || document;
      drawAbilityTreeIn(scope, img, childSlugs);
    });
  }

  function drawAbilityTreeIn(scope, parentImg, childSlugs) {
    if (parentImg.closest('.f-hide, .cat-hide, .ec-scope-hide')) return;
    const childImgs = childSlugs
      .map((s) => scope.querySelector('img[data-slug="' + s + '"]'))
      .filter(Boolean)
      .filter(img => !img.closest('.f-hide, .cat-hide, .ec-scope-hide'));
    if (!childImgs.length) return;

    // Use document-level coordinates so the SVG can span multiple
    // ability-blocks regardless of their containing scrollable parents.
    const docY = (rect) => rect.top + window.scrollY;
    const docX = (rect) => rect.left + window.scrollX;
    const parentRect = resolveAnchor(parentImg).getBoundingClientRect();
    const childRects = childImgs.map((i) => resolveAnchor(i).getBoundingClientRect());

    // Trunk: vertical line in the left gutter just outside the parent icon's
    // left edge — visually "comes out" of the Primal Split icon.
    // Trunk runs in the left gutter; parent connects from its left-center.
    const parentLeftX = docX(parentRect);
    const parentMidY  = docY(parentRect) + parentRect.height / 2;
    const trunkX = parentLeftX - 12;
    const lastChild = childRects[childRects.length - 1];
    const endY = docY(lastChild) + lastChild.height / 2;
    const minX = Math.min(trunkX, ...childRects.map(docX));
    const maxX = Math.max(parentLeftX, ...childRects.map((r) => docX(r) + r.width));

    const top    = Math.min(parentMidY, ...childRects.map(docY));
    const bottom = endY + 4;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'brewling-connector');
    svg.style.left = minX - 4 + 'px';
    svg.style.top  = top + 'px';
    svg.style.width  = (maxX - minX + 8) + 'px';
    svg.style.height = (bottom - top + 4) + 'px';
    svg.setAttribute('viewBox',
      '0 0 ' + (maxX - minX + 8) + ' ' + (bottom - top + 4));

    // Coordinate transform: subtract SVG origin from each point.
    const tx = (x) => x - (minX - 4);
    const ty = (y) => y - top;

    // Left-center of parent → horizontal stub to trunk → down to last child.
    let d = 'M ' + tx(parentLeftX) + ' ' + ty(parentMidY)
          + ' L ' + tx(trunkX)     + ' ' + ty(parentMidY)
          + ' L ' + tx(trunkX)     + ' ' + ty(endY);
    // Branch from trunk to each brewling icon's left-center.
    for (const r of childRects) {
      const cy = docY(r) + r.height / 2;
      const cx = docX(r);
      d += ' M ' + tx(trunkX) + ' ' + ty(cy)
         + ' L ' + tx(cx) + ' ' + ty(cy);
    }
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', d);
    svg.appendChild(path);
    document.body.appendChild(svg);
  }
  drawBrewlingConnectors();
  window.addEventListener('resize', drawBrewlingConnectors);
  window.addEventListener('load', drawBrewlingConnectors);
  // a card's folded text (.acr-fold, patch/cards_item_abilities._fold_named_parts): its chevron button opens and
  // closes it, a click on the faded text opens it; the card's connectors and the dashed tree below follow the card's
  // new height ('toggle' listeners above)
  function setFold(fold, open) {
    if (fold.classList.contains('is-open') === open) return;
    fold.classList.toggle('is-open', open);
    const btn = fold.querySelector('.acr-fold-toggle');
    if (btn) {
      btn.setAttribute('aria-expanded', String(open));
      btn.setAttribute('aria-label', open ? 'Fold the text' : 'Show the whole text');
    }
    fold.dispatchEvent(new Event('toggle'));
  }
  document.addEventListener('click', (e) => {
    if (!e.target.closest) return;
    const btn = e.target.closest('.acr-fold-toggle');
    if (btn) {
      const fold = btn.closest('.acr-fold');
      setFold(fold, !fold.classList.contains('is-open'));
      return;
    }
    const body = e.target.closest('.acr-fold-body');
    if (body) setFold(body.closest('.acr-fold'), true);
  });
  document.addEventListener('toggle', drawBrewlingConnectors, true);
})();
