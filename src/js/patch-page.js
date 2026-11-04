
(function() {
  // ---- RE-ANCHOR after load (patch pages) ----
  // Arriving with a #dyn-hero-… hash (from the Hero Dynamics matrix or another
  // patch's dynamics widget), the browser anchors immediately — but lazy hero/
  // item icons ABOVE the target then load and shift layout, leaving the target
  // scrolled off-screen. Re-scroll once everything has settled, offsetting for
  // the sticky nav so the heading isn't hidden behind it. Table pages run their
  // own centerHash(), so skip them.
  if (window.location.hash && !document.querySelector('.creeps-scroll')) {
    const reanchor = () => {
      const el = document.getElementById(
        decodeURIComponent(window.location.hash.slice(1)));
      if (!el) return;
      const navH = parseFloat(getComputedStyle(document.documentElement)
        .getPropertyValue('--site-nav-h')) || 70;
      const toolbarEl = document.querySelector('.toolbar');
      const toolbarH = toolbarEl ? toolbarEl.getBoundingClientRect().height : 0;
      const y = el.getBoundingClientRect().top + window.scrollY - navH - toolbarH - 8;
      window.scrollTo(0, Math.max(0, y));
    };
    // Several passes: the browser re-applies its own (nav-ignoring) hash scroll
    // around the load event, and late images shift layout — re-run after each so
    // the final position wins and accounts for the sticky nav.
    window.addEventListener('load', () => {
      reanchor();
      setTimeout(reanchor, 80);
      setTimeout(reanchor, 300);
    });
  }

  // ---- BACK TO TOP visibility ----
  // Guard for pages without the button (e.g. creeps.html). Without this
  // null-guard, updateBtt() throws at load and halts the whole script —
  // which silently broke the creep-icon copy handler below.
  const btt = document.querySelector('.back-to-top');
  if (btt) {
    // PERF: classList.toggle() still writes/dirties style even when the
    // value is unchanged, and this fires on every 'scroll' event (i.e. most
    // animation frames while scrolling). Track the last state and skip the
    // DOM write entirely once we're past the 400px threshold either way.
    let bttVisible = null;
    const updateBtt = () => {
      const shouldShow = window.scrollY > 400;
      if (shouldShow === bttVisible) return;
      bttVisible = shouldShow;
      btt.classList.toggle('visible', shouldShow);
    };
    window.addEventListener('scroll', updateBtt, { passive: true });
    updateBtt();
  }

  // ---- VERSION DROPDOWN toggle ----
  const dropdownBtn = document.querySelector('.version-dropdown .version');
  const dropdownMenu = document.querySelector('.version-dropdown .version-menu');
  if (dropdownBtn && dropdownMenu) {
    dropdownBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const open = dropdownMenu.classList.toggle('open');
      dropdownBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open) {
        const cur = dropdownMenu.querySelector('.version-item.current');
        if (cur) cur.scrollIntoView({ block: 'nearest' });
      }
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
    // Prevent scroll propagation to the page on Safari (overscroll-behavior
    // alone isn't enough on older WebKit builds).
    dropdownMenu.addEventListener('touchmove', (e) => { e.stopPropagation(); }, { passive: true });
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
  document.querySelectorAll('h4.ability-title').forEach(h => {
    const block = h.closest('.ability-block');
    const imgEl = block ? block.querySelector('.ability-icon-img') : null;
    const isInnate = block ? block.classList.contains('is-innate') : false;
    const innateUrl = '../icons/misc/innate_icon.png';
    const realIcon = imgEl ? imgEl.src : null;
    entities.push({
      name: h.textContent.trim(),
      element: h,
      icon: realIcon || (isInnate ? innateUrl : null),
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
    const y = target.element.getBoundingClientRect().top + window.scrollY - navH - toolbarH - 8;
    window.scrollTo({ top: Math.max(0, y), behavior: 'smooth' });
    target.element.style.transition = 'box-shadow 0.4s';
    target.element.style.boxShadow = '0 0 0 2px #e3c46a';
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
      path.setAttribute('d', connectorPath(blockRect, iconRect, paneRect));
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
  drawAbilityChangeConnectors();
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
  // Hues chosen so adjacent bands in DYN_TAG_ORDER below contrast — NEW
  // moves to gold (matching the .badge.new page color) so it stops getting
  // visually swallowed when it sits next to BUFF (green).
  // Stored as RGB tuples; alpha is computed at render time per band so
  // bands with more hits look more saturated (see dynColorFor).
  const DYN_TAG_RGB = {
    buff:   [93, 177, 78],   // green
    new:    [220, 175, 95],  // gold
    rework: [164, 114, 207], // purple
    swap:   [95, 176, 164],  // teal — a talent replaced (2026-09-26)
    misc:   [139, 144, 153], // grey
    qol:    [108, 171, 240], // blue
    del:    [190, 79, 79],   // red — removed (owner 2026-10-21: swapped with NERF)
    nerf:   [177, 78, 92],  // pink
  };
  // Map a tag's count → rgba alpha. Single-hit bands sit near the old
  // baseline (~0.50), heavy bands push toward fully-saturated 0.90 so
  // the visual difference between "1 buff" and "8 buffs" is obvious at
  // a glance. Wider range than before for a more expressive ramp.
  const DYN_ALPHA_BASE = 0.50;
  const DYN_ALPHA_STEP = 0.08;
  const DYN_ALPHA_MAX  = 0.90;
  // Colour-blind mode (header switch, html.cb-mode): every tag its own colour, apart for deutan / protan eyes too —
  // the same set as the badges (scripts/gen/gen_colorblind_css.py CB_TAGS; tests/test_colorblind.py keeps them equal).
  const DYN_TAG_RGB_CB = {
    buff:   [86, 180, 233],  // sky blue
    new:    [245, 225, 90],  // yellow
    rework: [204, 121, 167], // reddish purple
    swap:   [40, 150, 120],  // bluish green
    misc:   [200, 200, 200], // light grey
    qol:    [40, 80, 170],   // dark blue
    del:    [120, 40, 70],   // dark wine
    nerf:   [230, 110, 20],  // vermilion orange
  };
  function dynRgb(tag) {
    return (document.documentElement.classList.contains('cb-mode') && DYN_TAG_RGB_CB[tag]) || DYN_TAG_RGB[tag];
  }
  // The switch flips the mode on a built page: swap the buff / nerf colours inside every painted cell.
  window.addEventListener('cb-mode-changed', () => {
    const cb = document.documentElement.classList.contains('cb-mode');
    const pairs = Object.keys(DYN_TAG_RGB_CB).map(t => [DYN_TAG_RGB[t].join(', '), DYN_TAG_RGB_CB[t].join(', ')]);
    document.querySelectorAll('.dyn-cell').forEach(cell => {
      let bg = cell.style.getPropertyValue('--dyn-bg');
      if (!bg) return;
      pairs.forEach(([plain, safe]) => { bg = bg.split(cb ? plain : safe).join(cb ? safe : plain); });
      cell.style.setProperty('--dyn-bg', bg);
    });
  });
  function dynColorFor(tag, count) {
    const rgb = dynRgb(tag);
    // count=1 → BASE, then each additional hit adds STEP, clamped at MAX.
    const alpha = Math.min(
      DYN_ALPHA_MAX,
      DYN_ALPHA_BASE + Math.max(0, count - 1) * DYN_ALPHA_STEP
    );
    return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha.toFixed(2)})`;
  }
  const DYN_TAG_LABEL = {
    buff:'BUFF', nerf:'NERF', new:'NEW', del:'DEL',
    rework:'REWORK', swap:'SWAP', misc:'MISC', qol:'QoL',
  };
  // Tag id → page-badge css class. Matches the styles in styles.css so
  // tooltip badges look identical to the row badges everywhere else.
  const DYN_TAG_BADGE_CLASS = {
    buff:'buff-text', nerf:'nerf-text', new:'new', del:'del',
    rework:'rework', swap:'swap', misc:'misc', qol:'qol',
  };
  // Order is also the visual top→bottom band stack inside each pill, AND
  // the row order in the tooltip grid. Sequenced so neighbouring bands
  // change hue family (green → gold → purple → grey → blue → pink → red).
  const DYN_TAG_ORDER = ['buff','new','rework','swap','misc','qol','del','nerf'];
  const DYN_MAX_PATCHES = 12;
  // "Weights" mode: each cell shows the patch's summed weighted score (bucket key
  // "w", see patch/weights.py) instead of the tag gradient. Patch pages toggle it
  // with #dyn-weights-btn, the matrices with the #hd-weights switch.
  let dynWeightsOn = false;
  function dynFmtW(w) {
    const a = Math.abs(w);
    return (w < 0 ? '-' : '') + (a >= 10 ? a.toFixed(1) : a.toFixed(2));
  }
  // The mode is remembered across pages (patch pages <-> matrices) in localStorage.
  const DYN_W_KEY = 'sloppy-dyn-weights';
  function dynWeightsStored() { try { return localStorage.getItem(DYN_W_KEY) === '1'; } catch (e) { return false; } }
  function dynWeightsStore(on) { try { localStorage.setItem(DYN_W_KEY, on ? '1' : '0'); } catch (e) {} }
  function dynWeightTint(w) {
    const rgb = w > 0 ? dynRgb('buff') : (w < 0 ? dynRgb('nerf') : [110, 110, 110]);
    const alpha = Math.min(0.9, 0.25 + Math.min(Math.abs(w), 4) * 0.16);
    const c = `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha.toFixed(2)})`;
    return `linear-gradient(${c}, ${c})`;
  }

  function dynBuildPill(patch, counts, entityId, isCurrent, fromVersion, filePrefix, bnOnly, removed, debut, wMode) {
    // "Remove" tag filter (toolbar chips): zero out user-removed tags for the
    // CELL colouring. The hover tooltip below still uses the ORIGINAL counts, so
    // a removed tag stays visible on hover — it's only dropped from the diamond.
    const eff = (removed && removed.size)
      ? DYN_TAG_ORDER.reduce((o, t) => { o[t] = removed.has(t) ? 0 : (counts[t] || 0); return o; }, {})
      : counts;
    const origTotal = DYN_TAG_ORDER.reduce((s, t) => s + (counts[t] || 0), 0);
    const total = DYN_TAG_ORDER.reduce((s, t) => s + (eff[t] || 0), 0);   // effective → drives fill/empty
    const clickable = origTotal > 0 && patch.filename && !isCurrent;
    // Gradient source (over EFFECTIVE counts). Default = non-neutral tags vs the
    // full effective total (MISC/QoL leave a gap — patch-page look). "Buff/nerf
    // only" (bnOnly) collapses to TWO bands: buff+NEW (green), nerf+DEL (red).
    // `debut` = the item's introduction cell (data-debut): its NEW rows mean
    // "item now exists", so they must NOT fold into buff (items_dyn only).
    const gradCounts = bnOnly
      ? { buff: (eff.buff || 0) + (debut ? 0 : (eff.new || 0)),
          nerf: (eff.nerf || 0) + (eff.del || 0) }
      : eff;
    const gradTagSet = bnOnly
      ? ['buff', 'nerf']
      : DYN_TAG_ORDER;
    const coloredTotal = gradTagSet.reduce((s, t) => s + (gradCounts[t] || 0), 0);
    const denom = bnOnly ? coloredTotal : total;   // fill vs proportional-to-total
    const wrap = document.createElement(clickable ? 'a' : 'span');
    let wcls = 'dyn-cell-wrap';
    if (!origTotal) wcls += ' empty';
    if (isCurrent) wcls += ' current';
    if (origTotal && !patch.filename) wcls += ' no-page';
    // No colour left to show — bnOnly with no buff/nerf, OR every colour tag
    // removed via the toolbar chips. Render as a plain EMPTY cell (not a dark
    // glassy pill); it stays clickable + keeps its hover tooltip.
    if (origTotal > 0 && coloredTotal === 0) wcls += ' bn-empty';
    wrap.className = wcls;
    const cell = document.createElement('span');
    cell.className = 'dyn-cell';
    wrap.appendChild(cell);
    if (wMode && origTotal) {
      const w = counts.w || 0;
      if (filePrefix === 'patches/') {          // matrix: segment of the row's line chart
        wrap.classList.add('w-mode', 'w-line');
        cell.style.background = 'none';
        cell.dataset.w = String(w);
        cell.dataset.v = String(counts.v || 0);
      } else {                                  // patch page: the number
        wrap.classList.add('w-mode');
        cell.textContent = dynFmtW(w);
        cell.style.setProperty('--dyn-bg', dynWeightTint(w));
      }
    } else if (total) {
      // Build a vertical gradient where each tag occupies a band proportional
      // to its share. Instead of hard color-stops at the band boundaries we
      // leave a `bleed` zone on each side so adjacent colors interpolate
      // across it — this produces the soft "liquid floating at different
      // densities" look rather than crisp horizontal stripes. The bleed is
      // capped to half the band width to stay within the segment.
      //
      // MISC and QoL are intentionally EXCLUDED from the gradient — these
      // neutral bands dilute the pill's color signal without adding meaning.
      // The tags still surface in the tooltip grid below.
      const tags = gradTagSet.filter(t => gradCounts[t] > 0);
      // Bleed: % half-width of the soft transition zone between adjacent
      // bands. Zero = hard cuts between bands — no phantom mid-tones.
      const bleed = 0;
      let acc = 0;
      const stops = [];
      for (let i = 0; i < tags.length; i++) {
        const t = tags[i];
        const c = gradCounts[t];
        const start = (acc / denom) * 100;
        acc += c;
        const end = (acc / denom) * 100;
        const halfBand = (end - start) / 2;
        const localBleed = Math.min(bleed, halfBand);
        const solidStart = i === 0 ? start : start + localBleed;
        const solidEnd = i === tags.length - 1 ? end : end - localBleed;
        const color = dynColorFor(t, c);
        stops.push(`${color} ${solidStart.toFixed(1)}%`);
        stops.push(`${color} ${solidEnd.toFixed(1)}%`);
      }
      if (stops.length) {
        cell.style.setProperty('--dyn-bg', `linear-gradient(to bottom, ${stops.join(', ')})`);
      }
    }
    if (clickable) {
      // ?from=<version> lets the destination patch page show a back-arrow here.
      const qs = fromVersion ? '?from=' + fromVersion : '';
      wrap.href = (filePrefix || '') + patch.filename + qs + (entityId ? '#' + entityId : '');
    }
    // Lazy tooltip (built on first hover). Uses the ORIGINAL counts so removed/
    // filtered tags still list on hover even when dropped from the diamond.
    wrap._dynTipParams = origTotal
      ? [patch, counts, patch.filename ? null : '(no patch page yet)']
      : [patch, null, null];
    return wrap;
  }

  // Tooltip popup — a real DOM sibling of .dyn-cell (not a pseudo) so it
  // escapes the diamond's clip-path. Content:
  //   - Header: version + date.
  //   - Body: 2-column grid of tag badges (page-style) each followed by
  //           a small count chip, ordered by DYN_TAG_ORDER. When counts is
  //           null (empty cell) the body holds a single `note` line.
  function dynBuildTip(patch, counts, note) {
    const tip = document.createElement('span');
    tip.className = 'dyn-tip';
    const header = document.createElement('span');
    header.className = 'dyn-tip-header';
    header.textContent = `${patch.version}`;
    if (counts && (counts.w !== undefined || counts.v !== undefined)) {
      if (counts.w === undefined) counts.w = 0;
      header.classList.add('has-score');
      const sc = document.createElement('span');
      sc.className = 'dyn-tip-score ' + (counts.w > 0 ? 'pos' : (counts.w < 0 ? 'neg' : 'zero'));
      sc.textContent = (counts.w > 0 ? '+' : '') + counts.w.toFixed(2)
        + (counts.v !== undefined ? ' (' + counts.v.toFixed(2) + ')' : '');
      sc.title = 'net balance (volume of changes)';
      header.appendChild(sc);
    }
    tip.appendChild(header);
    if (counts) {
      const grid = document.createElement('span');
      grid.className = 'dyn-tip-grid';
      for (const t of DYN_TAG_ORDER) {
        const c = counts[t] || 0;
        if (!c) continue;
        const row = document.createElement('span');
        row.className = 'dyn-tip-row';
        const badge = document.createElement('span');
        badge.className = `badge ${DYN_TAG_BADGE_CLASS[t]}`;
        badge.textContent = DYN_TAG_LABEL[t];
        const count = document.createElement('span');
        count.className = 'dyn-tip-count';
        count.textContent = '×' + c;
        row.appendChild(badge);
        row.appendChild(count);
        grid.appendChild(row);
      }
      tip.appendChild(grid);
    }
    if (note) {
      const noteEl = document.createElement('span');
      noteEl.className = 'dyn-tip-note';
      noteEl.textContent = note;
      tip.appendChild(noteEl);
    }
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
  // in patch/elements.py. Ordered longest-first so "creep-hero" wins over "creep".
  const DYN_KINDS = ['creep-hero', 'hero', 'item', 'unit', 'plain', 'enchant'];

  // First offset of a row: the page's own patch sits in the middle of the strip (older on the left, newer on
  // the right), not always the newest 12 — on 7.38 the strip showed 7.39d-7.41f without 7.38 itself, on 7.08
  // Blink Dagger's was empty (owner 2026-10-06). No version (hero / item pages) -> 0 = the newest patches.
  function dynDefaultOffset(manifest, currentVersion, n) {
    const idx = currentVersion ? manifest.patches.findIndex(p => p.version === currentVersion) : -1;
    if (idx < 0) return 0;
    const size = n || DYN_MAX_PATCHES;
    const maxOff = Math.max(0, manifest.patches.length - size);
    return Math.min(maxOff, Math.max(0, idx - Math.floor(size / 2)));
  }

  function dynWindow(manifest, offset, n) {
    // manifest.patches is newest-first → slice from offset, reverse so the
    // oldest of the window is on the left in the rendered row.
    return manifest.patches.slice(offset, offset + (n || DYN_MAX_PATCHES)).reverse();
  }
  // How many cells a row shows: 12 on patch pages; on a Hero/Item Changes page the
  // head row stretches over the free width of its panel.
  function dynRowSize(entityDiv, manifest) {
    if (!entityDiv.closest('.ec-head')) return DYN_MAX_PATCHES;
    // the real width of what shares the line — icon, name (as long as it is: "Io" leaves room), the hero's
    // item slots — plus the gaps between them and room for the two nav arrows (owner 2026-09-28: a fixed
    // guess for the name cost patch squares)
    const gap = parseFloat(getComputedStyle(entityDiv).columnGap) || 18;
    const others = Array.from(entityDiv.children).filter(c => !c.classList.contains('dyn-row-wrap'));
    const used = others.reduce((s, c) => s + c.getBoundingClientRect().width, 0) + gap * others.length;
    const free = entityDiv.clientWidth - used - 14 - 18;   // the row's own left margin after the slots; the right arrow
    return Math.max(DYN_MAX_PATCHES, Math.min(manifest.patches.length, Math.floor(free / 28)));
  }

  function dynRenderRow(entityDiv, manifest, windowed, currentVersion, offset) {
    const id = entityDiv.id || '';
    if (!id.startsWith('dyn-')) return;
    const rest = id.slice(4);
    const kind = DYN_KINDS.find(k => rest === k || rest.startsWith(k + '-'));
    if (!kind) return;
    const slug = rest.slice(kind.length + 1);
    const key = kind + '|' + slug;
    const rec = manifest.entities[key];
    const perPatch = (rec && rec.patches) || {};
    const wrap = document.createElement('div');
    wrap.className = 'dyn-row-wrap';
    const canLeft  = offset + windowed.length < manifest.patches.length;
    const canRight = offset > 0;
    if (canLeft) {
      const btn = document.createElement('button');
      btn.className = 'dyn-nav-arrow dyn-nav-left';
      btn.setAttribute('aria-label', 'Show older patches');
      wrap.appendChild(btn);
    }
    const row = document.createElement('div');
    row.className = 'patch-dynamics';
    for (const p of windowed) {
      const counts = perPatch[p.version] || {};
      // Entity "Changes" pages live outside /patches/: <body data-dyn-prefix="../patches/">
      row.appendChild(dynBuildPill(p, counts, id, p.version === currentVersion,
                                   (document.body && document.body.dataset.dynFrom) || currentVersion,
                                   (document.body && document.body.dataset.dynPrefix) || undefined,
                                   false, null, false, dynWeightsOn));
    }
    wrap.appendChild(row);
    if (canRight) {
      const btn = document.createElement('button');
      btn.className = 'dyn-nav-arrow dyn-nav-right';
      btn.setAttribute('aria-label', 'Show newer patches');
      wrap.appendChild(btn);
    }
    entityDiv.appendChild(wrap);
  }

  // Fill / refill the heroes_dyn matrix's data cells with one pill each. Only
  // cells the builder marked with data-ver/data-hkey (the hero actually changed
  // that patch) are filled — untouched cells stay as the CSS empty diamond, so
  // runtime work scales with real data, not the full N×M grid. Re-runnable: it
  // clears any existing pill first, so the "Buff vs nerf" toggle can rebuild.
  function dynFillMatrix(table, manifest, bnOnly, removed, wMode) {
    const byVer = {};
    manifest.patches.forEach(p => { byVer[p.version] = p; });
    // Back-arrow token: 'heroes_dyn' or 'items_dyn' (set on <body data-dyn-from>),
    // so the destination patch page returns to the right matrix.
    const fromTok = (document.body && document.body.dataset.dynFrom) || 'heroes_dyn';
    table.querySelectorAll('td.hd-cell[data-ver]').forEach(td => {
      const prev = td.querySelector('.dyn-cell-wrap');
      if (prev) prev.remove();
      const patch = byVer[td.dataset.ver];
      if (!patch) return;
      const rec = manifest.entities[td.dataset.hkey];
      const counts = (rec && rec.patches && rec.patches[td.dataset.ver]) || {};
      if (!Object.keys(counts).length) return;
      // entityId anchors the click to the entity on the patch page; fromTok makes
      // that page show a back-arrow returning here; filePrefix 'patches/' because
      // the matrix lives at site root, patch pages under /patches.
      const debut = td.dataset.debut === '1';
      td.appendChild(dynBuildPill(patch, counts, td.dataset.eid, false, fromTok, 'patches/', bnOnly, removed, debut, wMode));
    });
    if (wMode) dynDrawRowLines(table);
    else table.querySelectorAll('td.he-seg').forEach(td => { td.classList.remove('he-seg'); td.querySelector('svg.dyn-wl')?.remove(); });
  }

  // Weights mode on the matrices: every row is ONE step line of the per-patch net
  // score, the row itself is the zero axis.
  //  - STEP line: a touched patch is a flat plateau across its whole cell (the value
  //    belongs to the patch, nothing is interpolated between patches); vertical
  //    risers at the cell edges join it to the neighbour (0 for an untouched patch).
  //  - Colour follows the SIDE of the axis, not the cell: everything above the axis
  //    is green, below is red; a riser that crosses the axis is split at the axis.
  //  - LINEAR scale per row, computed over the VISIBLE columns only ("Hide old"
  //    hides the rest), floor 1.5: a 2.0 is exactly twice as high as a 1.0.
  // Idempotent: called after every refill AND after every layout pass.
  const DYN_W_MIN_SCALE = 1.5;
  function dynDrawRowLines(table) {
    const NS = 'http://www.w3.org/2000/svg';
    const W = 40, H = 28, mid = H / 2, amp = mid - 2.5;
    const mk = (tag, attrs) => {
      const el = document.createElementNS(NS, tag);
      for (const k in attrs) el.setAttribute(k, attrs[k]);
      return el;
    };
    table.querySelectorAll('tbody tr').forEach(tr => {
      const all = [...tr.children];
      const tds = all.filter(td => td.matches('td.hd-cell, td.he, td.ha') && !td.classList.contains('hd-spacer'));
      tds.forEach(td => {
        td.querySelectorAll('svg.dyn-wl').forEach(x => x.remove());
        td.classList.remove('he-seg');
      });
      const vis = tds.map(td => td.getClientRects().length > 0);
      const vals = tds.map(td => {
        const c = td.querySelector('.w-line .dyn-cell');
        return c ? (parseFloat(c.dataset.w) || 0) : 0;
      });
      const scale = Math.max(DYN_W_MIN_SCALE, ...vals.filter((_, i) => vis[i]).map(Math.abs));
      const yOf = v => mid - Math.max(-1, Math.min(1, v / scale)) * amp;
      // a hidden ("Hide old") neighbour counts as the axis: its value is outside the row scale,
      // so the first visible cell must not start with a riser from an invisible, clipped level
      const at = j => (j < 0 || j >= vals.length || !vis[j]) ? 0 : vals[j];
      const cls = y => (y < mid - 0.05 ? 'up' : (y > mid + 0.05 ? 'down' : 'flat'));
      tds.forEach((td, i) => {
        if (!vis[i]) return;
        const v = vals[i], prev = at(i - 1);
        const c = td.querySelector('.w-line .dyn-cell');
        if (!c && (td.matches('td.ha') || (!v && !prev))) return;   // plain axis from CSS
        const svg = mk('svg', { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: 'none', class: 'dyn-wl' });
        svg.appendChild(mk('line', { x1: 0, x2: W, y1: mid, y2: mid, class: 'axis' }));
        const yv = yOf(v), yp = yOf(prev);
        // riser at the LEFT edge, from the previous patch's level to this one, split at the axis
        if (yp !== yv) {
          const seg = (y1, y2) => svg.appendChild(mk('line', {
            x1: 0, x2: 0, y1: y1.toFixed(1), y2: y2.toFixed(1), class: 'seg ' + cls((y1 + y2) / 2) }));
          if ((yp - mid) * (yv - mid) < 0) { seg(yp, mid); seg(mid, yv); } else seg(yp, yv);
        }
        // plateau across the whole cell
        if (v) svg.appendChild(mk('line', { x1: 0, x2: W, y1: yv.toFixed(1), y2: yv.toFixed(1), class: 'seg ' + cls(yv) }));
        if (c) {
          svg.appendChild(mk('circle', { cx: W / 2, cy: yv.toFixed(1), r: 2.4, class: 'pt ' + cls(yv) }));
          c.appendChild(svg);
        } else {
          td.classList.add('he-seg');
          td.appendChild(svg);
        }
      });
    });
  }


  // Single <style> whose rule hides the oldest patch columns. Editing one rule
  // is far cheaper than toggling display on thousands of cells (115 cols × 127
  // rows) every resize.
  let _dynFitStyle = null;
  function dynFitStyleEl() {
    if (!_dynFitStyle) {
      _dynFitStyle = document.createElement('style');
      document.head.appendChild(_dynFitStyle);
    }
    return _dynFitStyle;
  }

  // Lay out the matrix so the LATEST patch sits flush at the right edge.
  //  - Hero column auto-sizes to the longest name (+ icon + gap + zoom clearance).
  //  - "Hide old" ON (fit mode): show only the most-recent patches that fit the
  //    box width, sized to fill it exactly (latest flush right); hide the rest.
  //  - "Hide old" OFF: show every patch at the base column width and scroll, with
  //    the box scrolled to the right so the latest still ends at the right edge.
  const HD_MIN_COL = 40;            // base/min patch-column width (px) — fits the 12px version label
  // Right gutter kept clear of the last column so its 2.5× hover-pop isn't cut
  // off by the box edge / vertical scrollbar (the pop grows ~18px past the cell).
  const HD_RIGHT_GUTTER = 24;
  function dynLayoutMatrix(table, fit) {
    const scroller = table.closest('.creeps-scroll');
    if (!scroller) return;
    // Hero column width = longest name + icon + gap + padding. The names never
    // change, so measuring all ~170 rows' scrollWidth on EVERY layout (toggle /
    // resize) forced a costly reflow each time → lag. Measure once and cache on
    // the table; the `load` handler clears it once so fonts/icons settle first.
    let heroW = table._hdHeroW;
    if (heroW == null) {
      let maxName = 0;
      table.querySelectorAll('tbody td.hd-hero .hd-hero-name').forEach(s => {
        maxName = Math.max(maxName, s.scrollWidth);
      });
      heroW = Math.ceil(maxName) + 40 /*icon*/ + 22 /*gap*/ + 18 /*padding 6+12*/;
      table._hdHeroW = heroW;
    }
    table.style.setProperty('--hd-hero-w', heroW + 'px');

    const patchThs = table.querySelectorAll('thead th.hd-patch');
    const total = patchThs.length;
    const csPad = parseFloat(getComputedStyle(scroller).paddingLeft) || 0;
    const avail = scroller.clientWidth - csPad - heroW - HD_RIGHT_GUTTER;
    const style = dynFitStyleEl();
    if (fit && avail > HD_MIN_COL) {
      const n = Math.min(total, Math.max(1, Math.floor(avail / HD_MIN_COL)));
      const colW = avail / n;                 // fill exactly → latest flush right
      table.style.setProperty('--hd-col-w', colW.toFixed(2) + 'px');
      const hide = total - n;                 // hide the oldest `hide` columns
      // Patch columns are table children 2..(total+1); hero is child 1.
      style.textContent = hide > 0
        ? `.heroes-dyn-table thead .col-row th.hd-patch:nth-child(-n+${hide + 1}):nth-child(n+2),`
          // he / ha are short aliases for `.hd-cell.hd-empty` / `.hd-cell.hd-absent`
          // (see builders/dyn_matrix_common.py + the corresponding CSS block).
          // Match all three so Hide-old collapses placeholder columns too.
          + `.heroes-dyn-table tbody td.hd-cell:nth-child(-n+${hide + 1}):nth-child(n+2),`
          + `.heroes-dyn-table tbody td.he:nth-child(-n+${hide + 1}):nth-child(n+2),`
          + `.heroes-dyn-table tbody td.ha:nth-child(-n+${hide + 1}):nth-child(n+2)`
          + `{display:none}`
        : '';
      scroller.scrollLeft = 0;
    } else {
      table.style.setProperty('--hd-col-w', HD_MIN_COL + 'px');
      style.textContent = '';
      // Show-all: park the scroll near the right (latest in view) but SNAP to a
      // whole-column multiple so the left edge shows a FULL column, never a
      // clipped "..2c" sliver of the column hidden behind the sticky hero col.
      const maxS = scroller.scrollWidth - scroller.clientWidth;
      scroller.scrollLeft = Math.max(0, Math.floor(maxS / HD_MIN_COL) * HD_MIN_COL);
    }
    dynRecomputeSupercats(table);
  }

  // Super-category row (base version spanning its lettered variants). After the
  // fit-to-width hide, re-size each base header to the count of its VISIBLE leaf
  // columns; hide a base header whose columns are all hidden. Mirrors the
  // Neutral-Creeps recomputeCatColspans pattern.
  function dynRecomputeSupercats(table) {
    table.querySelectorAll('thead .hd-supercat[data-base]').forEach(head => {
      const base = head.dataset.base;
      let span = 0;
      table.querySelectorAll('thead .col-row th.hd-patch').forEach(th => {
        if (th.dataset.base === base && th.offsetParent !== null) span++;
      });
      if (span > 0) { head.colSpan = span; head.style.display = ''; }
      else { head.style.display = 'none'; }
    });
  }

  // Wire the heroes_dyn toolbar: Hide old (fit-to-width), Buff vs nerf,
  // the "Remove" tag chips, and the hero search box.
  // Multi-select dropdown controls (.hd-dd): a flat button opens a checkbox popover.
  // The popover is PORTALED to <body> (so .creeps-scroll's contain:paint doesn't clip
  // it and an empty table can't push a scrollbar) and positioned fixed under the
  // button. A top "All" checkbox toggles every option; the gold badge shows "all" when
  // all are selected, else the count. `onChange` re-runs the row filter.
  function initHdDropdowns(scope, onChange) {
    const dds = [...scope.querySelectorAll('.hd-dd')];
    if (!dds.length) return;
    const closeAll = (except) => dds.forEach(dd => {
      if (dd === except) return;
      if (dd._menu) dd._menu.hidden = true;
      dd.querySelector('.hd-dd-btn').setAttribute('aria-expanded', 'false');
    });
    dds.forEach(dd => {
      const btn = dd.querySelector('.hd-dd-btn');
      const menu = dd.querySelector('.hd-dd-menu');
      const badge = dd.querySelector('.hd-dd-badge');
      const allBox = menu.querySelector('input[data-dd-all]');
      const boxes = [...menu.querySelectorAll('input[type="checkbox"]')]
        .filter(b => b !== allBox);
      dd._menu = menu;
      // Portal the menu out to <body> once (escapes the scroll box's paint clip).
      document.body.appendChild(menu);
      menu.style.position = 'fixed';
      const place = () => {
        const r = btn.getBoundingClientRect();
        menu.style.top = (r.bottom + 6) + 'px';
        menu.style.left = r.left + 'px';
      };
      const sync = () => {
        const n = boxes.filter(b => b.checked).length;
        if (badge) badge.textContent = (n === boxes.length) ? 'all' : String(n);
        if (allBox) {
          allBox.checked = (n === boxes.length);
          allBox.indeterminate = (n > 0 && n < boxes.length);
        }
      };
      sync();
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const willOpen = menu.hidden;
        closeAll(dd);
        if (willOpen) place();
        menu.hidden = !willOpen;
        btn.setAttribute('aria-expanded', String(willOpen));
      });
      menu.addEventListener('click', (e) => e.stopPropagation());
      if (allBox) allBox.addEventListener('change', () => {
        boxes.forEach(b => { b.checked = allBox.checked; });
        sync(); onChange();
      });
      boxes.forEach(b => b.addEventListener('change', () => { sync(); onChange(); }));
    });
    document.addEventListener('click', () => closeAll(null));
    // Button moves with the page but a fixed menu doesn't — close on scroll/resize.
    window.addEventListener('scroll', () => closeAll(null), true);
    window.addEventListener('resize', () => closeAll(null));
  }

  function dynSetupMatrix(table, manifest) {
    const elOld = document.getElementById('hd-hide-old');
    const elBn = document.getElementById('hd-bn-only');
    const elW = document.getElementById('dyn-weights-btn');
    const removed = new Set();                 // tags the user toggled off (Remove chips)
    const chips = [...table.closest('.creeps-page').querySelectorAll('.hd-tag[data-tag]')];
    const layout = () => {
      dynLayoutMatrix(table, !elOld || elOld.checked);
      // the row scale depends on which columns are visible -> redraw after every layout
      if (table.classList.contains('w-mode')) dynDrawRowLines(table);
      // Column widths + horizontal overflow just changed → tell the sticky-frame
      // divider (a separate IIFE) to re-anchor after this layout pass.
      window.dispatchEvent(new CustomEvent('mr:filter-changed'));
    };
    if (elW && dynWeightsStored()) {
      elW.classList.add('active'); elW.setAttribute('aria-pressed', 'true'); table.classList.add('w-mode');
    }
    const refill = () => dynFillMatrix(table, manifest, !!(elBn && elBn.checked), removed, !!(elW && elW.classList.contains('active')));
    refill();
    if (elW) elW.addEventListener('click', () => {
      const on = elW.classList.toggle('active');
      elW.setAttribute('aria-pressed', on ? 'true' : 'false');
      table.classList.toggle('w-mode', on);
      dynWeightsStore(on);
      refill();
    });
    layout();
    if (elOld) elOld.addEventListener('change', layout);

    // "Buff vs nerf": collapse each cell to two bands — buff + NEW (green) vs
    // nerf + DEL (red); rework/misc/qol drop out of the colour (the hover tooltip
    // still lists every tag). dynBuildPill does the buff←NEW / nerf←DEL fold, so
    // this switch ONLY flips the bnOnly flag — the Remove chips stay an entirely
    // INDEPENDENT control (no longer auto-toggled by this switch).
    if (elBn) elBn.addEventListener('change', refill);

    // "Remove" tag chips — clicking toggles a tag off (sunken + grey) and drops
    // it from every dyn-cell's colouring (hover tooltip still lists it).
    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        const tag = chip.dataset.tag;
        if (removed.has(tag)) { removed.delete(tag); chip.classList.remove('removed'); }
        else { removed.add(tag); chip.classList.add('removed'); }
        refill();
      });
    });

    // Row filters — name search + (items_dyn only) item-class chips + "Show
    // deleted" toggle, all combined into ONE visibility pass so they don't fight
    // over tr.style.display. Search: comma-separated, partial ("anci,aba,brood").
    // Class chips / deleted toggle are absent on heroes_dyn → their predicates
    // are no-ops there. Row display only (never re-measures the hero width).
    const search = document.getElementById('hd-hero-search');
    const page = table.closest('.creeps-page');
    const delToggle = document.getElementById('hd-show-deleted');
    const attackBtns = [...document.querySelectorAll('.hs-attack-filter')];
    const attrBtns = [...document.querySelectorAll('.hs-attr-filter[data-attr-filter]')];
    const priceMin = document.getElementById('hd-price-min');
    const priceMax = document.getElementById('hd-price-max');
    const priceClear = document.getElementById('hd-price-clear');
    const rows = [...table.querySelectorAll('tbody tr')];
    let attackFilter = '';
    let attrFilter = '';
    const applyRowFilters = () => {
      const terms = search
        ? search.value.toLowerCase().split(',').map(s => s.trim()).filter(Boolean)
        : [];
      // Multi-select dropdowns (Type=class, Category): a row must satisfy EVERY
      // active dropdown — its data-<dd> value among that dropdown's checked options.
      // Menus are portaled to <body>, so find each by its data-dd (not by containment).
      const ddFilters = page
        ? [...page.querySelectorAll('.hd-dd[data-dd]')].map(dd => {
            const key = dd.dataset.dd;
            const menu = document.querySelector('.hd-dd-menu[data-dd="' + key + '"]');
            const checked = new Set(menu
              ? [...menu.querySelectorAll('input[data-' + key + ']:checked')]
                  .map(i => i.dataset[key])
              : []);
            return { key, checked };
          })
        : [];
      const showDeleted = !!(delToggle && delToggle.checked);
      const lo = priceMin ? parseFloat(priceMin.value) : NaN;
      const hi = priceMax ? parseFloat(priceMax.value) : NaN;
      const hasLo = !isNaN(lo), hasHi = !isNaN(hi);
      // Clear-X visible only when a bound is set.
      if (priceClear) priceClear.hidden = !(hasLo || hasHi);
      rows.forEach(tr => {
        const cell = tr.querySelector('td.hd-hero');
        const name = (cell?.dataset.sort || '').toLowerCase();
        // data-alias = abbreviations + acronym (aghs→Aghanim's Scepter, bkb→вЂ¦).
        const alias = (cell?.dataset.alias || '').toLowerCase();
        // data-slug = engine slug (e.g. "wisp" for Io, "furion" for Nature's Prophet).
        const slug = (cell?.dataset.slug || '').toLowerCase();
        const okSearch = !terms.length
          || terms.some(t => name.includes(t) || alias.includes(t) || slug.includes(t));
        // A row with no data-<dd> value is EXEMPT from that dropdown (e.g. neutrals/
        // enchants have no shop category → the Category filter never hides them).
        const okDd = ddFilters.every(f => {
          const v = tr.dataset[f.key];
          return v === undefined || f.checked.has(v);
        });
        // data-current="0" = removed from the game → shown only when "Show deleted".
        const okDel = showDeleted || tr.dataset.current !== '0';
        const okAttack = !attackFilter || tr.dataset.attackType === attackFilter;
        const okAttr = !attrFilter || tr.dataset.attrType === attrFilter;
        // Price: items without data-price (neutrals/enchants = free) are EXEMPT.
        let okPrice = true;
        const p = tr.dataset.price;
        if ((hasLo || hasHi) && p !== undefined) {
          const v = parseFloat(p);
          if (hasLo && v < lo) okPrice = false;
          if (hasHi && v > hi) okPrice = false;
        }
        tr.style.display = (okSearch && okDd && okDel && okAttack && okAttr && okPrice) ? '' : 'none';
      });
      attackBtns.forEach(btn => {
        const active = btn.dataset.attackFilter === attackFilter;
        btn.classList.toggle('active', active);
        btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
      attrBtns.forEach(btn => {
        const active = btn.dataset.attrFilter === attrFilter;
        btn.classList.toggle('active', active);
        btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      });
    };
    if (search) search.addEventListener('input', applyRowFilters);
    if (page) initHdDropdowns(page, applyRowFilters);
    if (delToggle) delToggle.addEventListener('change', applyRowFilters);
    attackBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const next = btn.dataset.attackFilter || '';
        attackFilter = attackFilter === next ? '' : next;
        applyRowFilters();
      });
    });
    attrBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const next = btn.dataset.attrFilter || '';
        attrFilter = attrFilter === next ? '' : next;
        applyRowFilters();
      });
    });
    if (priceMin) priceMin.addEventListener('input', applyRowFilters);
    if (priceMax) priceMax.addEventListener('input', applyRowFilters);
    if (priceClear) priceClear.addEventListener('click', () => {
      if (priceMin) priceMin.value = '';
      if (priceMax) priceMax.value = '';
      applyRowFilters();
    });
    applyRowFilters();   // initial pass (deleted hidden + only Items class by default)

    window.addEventListener('resize', layout, { passive: true });
    // On load, ONLY re-fit the columns to the (settled) box width — reuse the
    // cached identity-column width from setup. Do NOT re-measure it here: setup
    // measured it over ALL rows (before the default class/Deleted filters hid
    // some), so it's already complete + correct. Re-measuring now would see only
    // the VISIBLE rows (shorter names) → a smaller heroW → the column fit
    // (computed from it) would mismatch the real heroW and overflow the box with a
    // horizontal scrollbar (the items_dyn bug — heroes_dyn has no default filter so
    // it never showed). Names use the system font (no web-font reflow), so the
    // setup measure needs no font-settle correction.
    window.addEventListener('load', layout);
  }

  function dynInit() {
    const entities = document.querySelectorAll('.entity[id^="dyn-"]');
    const matrix = document.querySelector('.heroes-dyn-table');
    if (!entities.length && !matrix) return;
    const currentVersion = dynCurrentVersion();
    // Path differs by page location: patch pages sit under /patches/ (so ../),
    // root pages (heroes_dyn) read it directly. Builder sets data-dyn-path.
    const dynPath = (document.body && document.body.dataset.dynPath) || '../_dynamics.json';
    fetch(dynPath, { cache: 'no-cache' })
      .then(r => r.ok ? r.json() : null)
      .then(manifest => {
        if (!manifest) return;
        if (entities.length) {
          const buildRow = (e) => {
            if (e.dataset.dynBuilt) return;
            e.dataset.dynBuilt = '1';
            const n = dynRowSize(e, manifest);
            if (e.dataset.dynOffset === undefined) e.dataset.dynOffset = String(dynDefaultOffset(manifest, currentVersion, n));
            const off = parseInt(e.dataset.dynOffset, 10);
            dynRenderRow(e, manifest, dynWindow(manifest, off, n), currentVersion, off);
          };
          // Hero / Item Changes page: the head row is sized from the name's real width, which changes once the
          // pixel font arrives — size it again then (it was left a few squares short)
          const head = document.querySelector('.ec-head .entity[id^="dyn-"]');
          if (head && document.fonts && document.fonts.ready) document.fonts.ready.then(() => {
            if (!head.dataset.dynBuilt) return;
            const old = head.querySelector('.dyn-row-wrap');
            if (old) old.remove();
            const off = parseInt(head.dataset.dynOffset || '0', 10);
            dynRenderRow(head, manifest, dynWindow(manifest, off, dynRowSize(head, manifest)), dynCurrentVersion(), off);
          });
          // "Weights" toggle (toolbar): flip the mode and rebuild every row already built.
          const wBtn = document.getElementById('dyn-weights-btn');
          if (wBtn && dynWeightsStored()) {
            dynWeightsOn = true; wBtn.classList.add('active'); document.body.classList.add('dyn-weights');
          }
          if (wBtn) wBtn.addEventListener('click', () => {
            dynWeightsOn = wBtn.classList.toggle('active');
            dynWeightsStore(dynWeightsOn);
            document.body.classList.toggle('dyn-weights', dynWeightsOn);
            document.querySelectorAll('.entity[id^="dyn-"][data-dyn-built]').forEach(e => {
              const old = e.querySelector('.dyn-row-wrap');
              if (old) old.remove();
              const off = parseInt(e.dataset.dynOffset || '0', 10);
              dynRenderRow(e, manifest, dynWindow(manifest, off, dynRowSize(e, manifest)), dynCurrentVersion(), off);
            });
          });
          // Arrow navigation: per-entity offset stored in data-dyn-offset.
          // Each row navigates independently — clicking an arrow only rebuilds
          // the entity whose dyn-row-wrap contains that arrow.
          document.addEventListener('click', (ev) => {
            const arrow = ev.target.closest('.dyn-nav-arrow');
            if (!arrow) return;
            const entityDiv = arrow.closest('.entity[id^="dyn-"]');
            if (!entityDiv) return;
            const delta = arrow.classList.contains('dyn-nav-left') ? 1 : -1;
            const cur = parseInt(entityDiv.dataset.dynOffset || '0', 10);
            const newOff = cur + delta;
            const rowN = dynRowSize(entityDiv, manifest);
            if (newOff < 0 || newOff + rowN > manifest.patches.length) return;
            entityDiv.dataset.dynOffset = String(newOff);
            const cv = dynCurrentVersion();
            const old = entityDiv.querySelector('.dyn-row-wrap');
            if (old) old.remove();
            dynRenderRow(entityDiv, manifest, dynWindow(manifest, newOff, rowN), cv, newOff);
          });
          // Build each entity's cell row LAZILY as it nears the viewport — on a
          // 1800-change patch that's ~3200 gradient cells; creating them all on
          // load is the page's biggest cost. IntersectionObserver builds only
          // what's near view, then unobserves. Identical look, far less work.
          if ('IntersectionObserver' in window) {
            const io = new IntersectionObserver((obsEntries, obs) => {
              obsEntries.forEach(en => {
                if (en.isIntersecting) { buildRow(en.target); obs.unobserve(en.target); }
              });
            }, { rootMargin: '120% 0px' });   // ~1.2 screen-heights of lead, scales with resolution
            entities.forEach(e => io.observe(e));
            // PERF: also pre-build the remaining rows in idle time, a few per idle slice,
            // so they are not inserted DURING scrolling (each insertion mid-scroll cost
            // style + layout on a 20k-element patch page: p95 frame 33 ms on 7.41).
            // The observer above stays as the fast path for rows the user reaches first.
            const pending = [...entities];
            const idle = window.requestIdleCallback
              || (cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 50));
            const pump = deadline => {
              while (pending.length && deadline.timeRemaining() > 2) {
                const e = pending.shift();
                if (!e.dataset.dynBuilt) { buildRow(e); io.unobserve(e); }
              }
              if (pending.length) idle(pump);
            };
            idle(pump);
          } else {
            entities.forEach(buildRow);
          }
          // A #hash target must have its row built before we re-anchor (rows add
          // ~28px height). Force-build the target immediately, then re-anchor
          // (the getBoundingClientRect read forces layout first). Offset for nav.
          if (window.location.hash) {
            const _tgt = document.getElementById(
              decodeURIComponent(window.location.hash.slice(1)));
            if (_tgt && _tgt.matches('.entity[id^="dyn-"]')) buildRow(_tgt);
            const el = document.getElementById(
              decodeURIComponent(window.location.hash.slice(1)));
            if (el) {
              const navH = parseFloat(getComputedStyle(document.documentElement)
                .getPropertyValue('--site-nav-h')) || 70;
              const toolbarEl = document.querySelector('.toolbar');
              const toolbarH = toolbarEl ? toolbarEl.getBoundingClientRect().height : 0;
              const y = el.getBoundingClientRect().top + window.scrollY - navH - toolbarH - 8;
              window.scrollTo(0, Math.max(0, y));
            }
          }
        }
        if (matrix) dynSetupMatrix(matrix, manifest);
        dynAttachTooltipDelegation();
      })
      .catch(() => { /* silently fail — widget is an enhancement */ });
  }

  // Single shared tooltip lives on document.body (NOT inside any .dyn-cell-
  // wrap). Two reasons:
  //   1. Lazy: we only build the tooltip DOM once, then re-populate it on
  //      each hover. With 3000+ cells on big patches, per-cell pre-built
  //      tooltips were adding ~50k DOM nodes upfront.
  //   2. content-visibility:auto on .entity-block implies `contain: paint`
  //      which CLIPS any descendant — including tooltips that overflow
  //      above the block. Living on body escapes that clip.
  function dynAttachTooltipDelegation() {
    const shared = document.createElement('span');
    shared.className = 'dyn-tip dyn-tip-shared';
    document.body.appendChild(shared);
    let currentWrap = null;

    function show(wrap) {
      const params = wrap._dynTipParams;
      if (!params) return;
      // Rebuild children: clear previous and populate via the same helper.
      while (shared.firstChild) shared.removeChild(shared.firstChild);
      const built = dynBuildTip(params[0], params[1], params[2]);
      while (built.firstChild) shared.appendChild(built.firstChild);
      // Position-fix above the wrap. We avoid layout reads inside scroll
      // listeners; reading getBoundingClientRect once on hover is cheap.
      const r = wrap.getBoundingClientRect();
      // Show first (to measure tooltip height), then place.
      shared.style.left = '0px';
      shared.style.top = '0px';
      shared.classList.add('is-visible');
      const tipRect = shared.getBoundingClientRect();
      let left = r.left + r.width / 2 - tipRect.width / 2;
      left = Math.max(8, Math.min(left, window.innerWidth - tipRect.width - 8));
      // Cell scales to 2.5× on hover from its centre, so it grows ~18px
      // upward beyond the wrap's static bounding rect. Push the tooltip
      // 24px above r.top (18 expansion + 6 clearance) so it never sits on
      // the inflated cell.
      const top = r.top - tipRect.height - 24;
      shared.style.left = left + 'px';
      shared.style.top = top + 'px';
    }
    function hide() {
      shared.classList.remove('is-visible');
      currentWrap = null;
    }
    document.addEventListener('mouseover', (e) => {
      const wrap = e.target.closest && e.target.closest('.dyn-cell-wrap');
      if (wrap === currentWrap) return;
      if (wrap) { currentWrap = wrap; show(wrap); }
      else { hide(); }
    }, { capture: true, passive: true });
    document.addEventListener('mouseout', (e) => {
      // Only hide if the pointer left the wrap region entirely.
      const wrap = e.target.closest && e.target.closest('.dyn-cell-wrap');
      if (!wrap) return;
      const to = e.relatedTarget;
      if (!to || !wrap.contains(to)) hide();
    }, { capture: true, passive: true });
    window.addEventListener('scroll', hide, { passive: true });
  }

  dynInit();
})();
