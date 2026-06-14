
// ---- MATERIALS SUB-NAV: tap-to-open submenu on touch devices ----
// On hover-capable devices (mouse) the .nav-submenu opens on hover — fine. On
// touch devices the group trigger is an <a href=...> so the first tap fires
// navigation immediately, and the submenu never gets a chance to appear (only
// long-press emulates :hover, which the user shouldn't have to know about).
// Fix: on tap-only devices, the FIRST tap on a group trigger opens its
// submenu instead of navigating; a SECOND tap on the same trigger (or on
// anywhere outside) lets the navigation happen normally. Active item picks
// continue to navigate on first tap (so users CAN reach the group's own page
// — by tapping it twice). Touch detection uses the `(hover: none)` media
// query so plain laptops aren't affected.
(function() {
  const mq = window.matchMedia && window.matchMedia('(hover: none)');
  if (!mq || !mq.matches) return;
  const groups = document.querySelectorAll('.materials-subnav .nav-subgroup');
  if (!groups.length) return;
  let openGroup = null;
  function closeOpen() {
    if (openGroup) {
      openGroup.classList.remove('is-open');
      openGroup = null;
    }
  }
  groups.forEach(group => {
    const trigger = group.querySelector(':scope > .nav-subtab-group, :scope > .nav-subitem-parent');
    if (!trigger) return;
    trigger.addEventListener('click', (e) => {
      if (group === openGroup) {
        // Second tap on the same group — let the link follow through.
        return;
      }
      // First tap — open the submenu instead of navigating.
      e.preventDefault();
      closeOpen();
      group.classList.add('is-open');
      openGroup = group;
    });
  });
  // Tap outside any group closes the open one.
  document.addEventListener('click', (e) => {
    if (openGroup && !openGroup.contains(e.target)) closeOpen();
  });
})();

(function() {
  // ---- BACK-FROM-CALENDAR / BACK-FROM-PATCH ----
  // The back arrow normally points to the calendar (rendered in HTML).
  // Two trigger paths:
  //   ?from=calendar           → show arrow, default href is fine
  //   ?from=<patch-version>    → user navigated here from another patch via
  //                              the dynamics widget; rewrite the arrow's
  //                              href + label to point back to that patch.
  const params = new URLSearchParams(window.location.search);
  const back = document.querySelector('.nav-back-arrow');
  const fromParam = params.get('from');
  if (back && fromParam === 'calendar') {
    back.classList.add('visible');
  } else if (back && (fromParam === 'heroes_dyn' || fromParam === 'items_dyn')) {
    // Arrived from a Dynamics matrix (root page) via a dyn-cell. Point the back
    // arrow at it. Same fixed bottom-left button + styling as the calendar/patch
    // back-arrow; patch pages live under /patches/ so ../.
    const label = fromParam === 'items_dyn' ? 'Item Dynamics' : 'Hero Dynamics';
    back.href = '../' + fromParam + '.html';
    back.title = 'Back to ' + label;
    back.setAttribute('aria-label', 'Back to ' + label);
    back.classList.add('visible');
  } else if (back && fromParam && /^\d+\.\d+[a-z]?$/.test(fromParam)) {
    // Came from another patch via the dynamics widget. The dyn-cell href
    // also carries an entity anchor (#dyn-hero-...) so the destination page
    // scrolls to that entity — the SAME entity was visible on the origin
    // page, so reusing the current hash on the back-link restores the
    // user's scroll position on return.
    back.href = fromParam + '.html' + (window.location.hash || '');
    back.title = 'Back to ' + fromParam;
    back.setAttribute('aria-label', 'Back to patch ' + fromParam);
    back.classList.add('visible');
  }
  // The back arrow is a fixed button in the BOTTOM-LEFT corner (CSS), so it no
  // longer needs JS to vertically align it on the toolbar (that inline top:
  // override was what made it overlap the tag block).
})();

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
    const updateBtt = () => btt.classList.toggle('visible', window.scrollY > 400);
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
  function elementVisible(el) {
    return !!el && !el.classList.contains('f-hide') && !el.classList.contains('cat-hide');
  }
  function refreshPatchFilterLayout() {
    document.querySelectorAll('ul.changes').forEach(ul => {
      const hasVisible = Array.from(ul.children).some(elementVisible);
      ul.classList.toggle('f-hide', !hasVisible);
    });
    document.querySelectorAll('h4.ability-title').forEach(h => {
      let nx = h.nextElementSibling;
      while (nx && nx.tagName !== 'UL') nx = nx.nextElementSibling;
      h.classList.toggle('f-hide', !elementVisible(nx));
    });
    document.querySelectorAll('.ability-block').forEach(block => {
      const ul = block.querySelector('ul.changes');
      block.classList.toggle('f-hide', !elementVisible(ul));
    });
    document.querySelectorAll('.entity-block').forEach(block => {
      const visibleLi = block.querySelectorAll('ul.changes > li:not(.f-hide):not(.cat-hide)').length;
      const visibleSwaps = block.querySelectorAll('.ability-change:not(.f-hide):not(.cat-hide)').length;
      const visiblePanels = Array.from(block.children).some(child =>
        child.matches('.components-box, .components-change, .provides-box, .properties-change') &&
        elementVisible(child)
      );
      block.classList.toggle('f-hide', !visibleLi && !visibleSwaps && !visiblePanels);
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
  // Prevent scroll propagation to the page on Safari.
  if (resultsBox) {
    resultsBox.addEventListener('touchmove', (e) => { e.stopPropagation(); }, { passive: true });
  }
  } // end if (searchInput && resultsBox)

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
        'brewmaster_drunken_brawler_fire',
        'brewmaster_drunken_brawler_void',
      ],
    },
  ];

  function drawBrewlingConnectors() {
    // Remove any existing SVGs so we can redraw fresh on each call.
    document.querySelectorAll('svg.brewling-connector').forEach((s) => s.remove());
    ABILITY_TREES.forEach((tree) => drawAbilityTree(tree.parent, tree.children));
  }

  function drawAbilityTree(parentSlug, childSlugs) {
    const parentImg = document.querySelector('img[data-slug="' + parentSlug + '"]');
    if (!parentImg) return;
    if (parentImg.closest('.f-hide, .cat-hide')) return;
    const childImgs = childSlugs
      .map((s) => document.querySelector('img[data-slug="' + s + '"]'))
      .filter(Boolean);
    if (!childImgs.length) return;

    // Use document-level coordinates so the SVG can span multiple
    // ability-blocks regardless of their containing scrollable parents.
    const docY = (rect) => rect.top + window.scrollY;
    const docX = (rect) => rect.left + window.scrollX;
    const parentRect = parentImg.getBoundingClientRect();
    const childRects = childImgs.map((i) => i.getBoundingClientRect());

    // Trunk: vertical line in the left gutter just outside the parent icon's
    // left edge — visually "comes out" of the Primal Split icon.
    const trunkX = docX(parentRect) - 12;
    const startY = docY(parentRect) + parentRect.height / 2;
    const lastChild = childRects[childRects.length - 1];
    const endY = docY(lastChild) + lastChild.height / 2;
    const minX = Math.min(trunkX, ...childRects.map(docX));
    const maxX = Math.max(docX(parentRect) + parentRect.width / 2,
                          ...childRects.map((r) => docX(r) + r.width));
    const top = Math.min(startY, ...childRects.map(docY));
    const bottom = endY + 4;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'brewling-connector');
    svg.style.left = minX - 4 + 'px';
    svg.style.top = top + 'px';
    svg.style.width = (maxX - minX + 8) + 'px';
    svg.style.height = (bottom - top + 4) + 'px';
    svg.setAttribute('viewBox',
      '0 0 ' + (maxX - minX + 8) + ' ' + (bottom - top + 4));

    // Coordinate transform: subtract (minX-4, top) from each point.
    const tx = (x) => x - (minX - 4);
    const ty = (y) => y - top;

    // Parent icon bottom-center connects via short stub down to the trunk.
    const parentBottomX = docX(parentRect) + parentRect.width / 2;
    const parentBottomY = docY(parentRect) + parentRect.height;
    let d = 'M ' + tx(parentBottomX) + ' ' + ty(parentBottomY)
          + ' L ' + tx(parentBottomX) + ' ' + ty(startY + 6)
          + ' L ' + tx(trunkX) + ' ' + ty(startY + 6)
          + ' L ' + tx(trunkX) + ' ' + ty(endY);
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
    misc:   [139, 144, 153], // grey
    qol:    [108, 171, 240], // blue
    del:    [177, 78, 107],  // pink
    nerf:   [209, 75, 75],   // red
  };
  // Map a tag's count → rgba alpha. Single-hit bands sit near the old
  // baseline (~0.50), heavy bands push toward fully-saturated 0.90 so
  // the visual difference between "1 buff" and "8 buffs" is obvious at
  // a glance. Wider range than before for a more expressive ramp.
  const DYN_ALPHA_BASE = 0.50;
  const DYN_ALPHA_STEP = 0.08;
  const DYN_ALPHA_MAX  = 0.90;
  function dynColorFor(tag, count) {
    const rgb = DYN_TAG_RGB[tag];
    // count=1 → BASE, then each additional hit adds STEP, clamped at MAX.
    const alpha = Math.min(
      DYN_ALPHA_MAX,
      DYN_ALPHA_BASE + Math.max(0, count - 1) * DYN_ALPHA_STEP
    );
    return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha.toFixed(2)})`;
  }
  const DYN_TAG_LABEL = {
    buff:'BUFF', nerf:'NERF', new:'NEW', del:'DEL',
    rework:'REWORK', misc:'MISC', qol:'QoL',
  };
  // Tag id → page-badge css class. Matches the styles in styles.css so
  // tooltip badges look identical to the row badges everywhere else.
  const DYN_TAG_BADGE_CLASS = {
    buff:'buff-text', nerf:'nerf-text', new:'new', del:'del',
    rework:'rework', misc:'misc', qol:'qol',
  };
  // Order is also the visual top→bottom band stack inside each pill, AND
  // the row order in the tooltip grid. Sequenced so neighbouring bands
  // change hue family (green → gold → purple → grey → blue → pink → red).
  const DYN_TAG_ORDER = ['buff','new','rework','misc','qol','del','nerf'];
  // Tags kept OUT of the dyn-cell colored gradient. Now EMPTY — MISC (grey)
  // and QoL (blue) are coloured bands like every other tag (user request), so
  // they contribute to the diamond's fill on both patch pages and heroes_dyn.
  // The "misc-only" dimmed-fallback path below is now effectively dead (kept
  // harmless: with no neutral tags, coloredTotal === total whenever total > 0).
  const DYN_NEUTRAL_TAGS = [];
  const DYN_MAX_PATCHES = 12;

  function dynBuildPill(patch, counts, entityId, isCurrent, fromVersion, filePrefix, bnOnly, removed, debut) {
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
      : DYN_TAG_ORDER.filter(t => !DYN_NEUTRAL_TAGS.includes(t));
    const coloredTotal = gradTagSet.reduce((s, t) => s + (gradCounts[t] || 0), 0);
    const denom = bnOnly ? coloredTotal : total;   // fill vs proportional-to-total
    // Dim "misc/qol-only" fallback only in the DEFAULT view (not bnOnly).
    const miscOnly = total > 0 && coloredTotal === 0 && !bnOnly;
    const wrap = document.createElement(clickable ? 'a' : 'span');
    let wcls = 'dyn-cell-wrap';
    if (!origTotal) wcls += ' empty';
    if (isCurrent) wcls += ' current';
    if (origTotal && !patch.filename) wcls += ' no-page';
    if (miscOnly) wcls += ' misc-only';
    // No colour left to show — bnOnly with no buff/nerf, OR every colour tag
    // removed via the toolbar chips. Render as a plain EMPTY cell (not a dark
    // glassy pill); it stays clickable + keeps its hover tooltip.
    if (origTotal > 0 && coloredTotal === 0 && !miscOnly) wcls += ' bn-empty';
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
      // If every tag was neutral (misc/qol), the colored-tags `stops` array
      // is empty; fall back to a solid dimmed fill so the cell still reads as
      // "this patch touched the entity, just with no buff/nerf/etc." The CSS
      // .misc-only class drops the cell to 50% opacity so it's visibly
      // dimmed vs. a fully-colored cell.
      if (stops.length) {
        cell.style.setProperty('--dyn-bg', `linear-gradient(to bottom, ${stops.join(', ')})`);
      } else if (miscOnly) {
        // Flat-gradient wrapper instead of a raw color so the value always
        // parses as `background-image` — keeps the bg-color slot free for
        // the hover-time opaque backdrop layer. Alpha is halved here to
        // preserve the dimmed-out neutral-only look. Uses EFFECTIVE counts so a
        // removed neutral tag doesn't pick the fill colour.
        const domNeutral = DYN_NEUTRAL_TAGS
          .reduce((a, b) => ((eff[b] || 0) > (eff[a] || 0) ? b : a));
        const m = dynColorFor(domNeutral, eff[domNeutral] || 1)
          .replace(/, ([\d.]+)\)$/, (_, a) => `, ${(parseFloat(a) * 0.5).toFixed(2)})`);
        cell.style.setProperty('--dyn-bg', `linear-gradient(${m}, ${m})`);
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
  // in build_patch.py. Ordered longest-first so "creep-hero" wins over "creep".
  const DYN_KINDS = ['creep-hero', 'hero', 'item', 'unit', 'plain', 'enchant'];

  function dynWindow(manifest, offset) {
    // manifest.patches is newest-first → slice from offset, reverse so the
    // oldest of the window is on the left in the rendered row.
    return manifest.patches.slice(offset, offset + 12).reverse();
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
    const canLeft  = offset + 12 < manifest.patches.length;
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
      row.appendChild(dynBuildPill(p, counts, id, p.version === currentVersion, currentVersion));
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
  function dynFillMatrix(table, manifest, bnOnly, removed) {
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
      td.appendChild(dynBuildPill(patch, counts, td.dataset.eid, false, fromTok, 'patches/', bnOnly, removed, debut));
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
          + `.heroes-dyn-table tbody td.hd-cell:nth-child(-n+${hide + 1}):nth-child(n+2)`
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
    const removed = new Set();                 // tags the user toggled off (Remove chips)
    const chips = [...table.closest('.creeps-page').querySelectorAll('.hd-tag[data-tag]')];
    const layout = () => {
      dynLayoutMatrix(table, !elOld || elOld.checked);
      // Column widths + horizontal overflow just changed → tell the sticky-frame
      // divider (a separate IIFE) to re-anchor after this layout pass.
      window.dispatchEvent(new CustomEvent('mr:filter-changed'));
    };
    const refill = () => dynFillMatrix(table, manifest, !!(elBn && elBn.checked), removed);
    refill();
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
    const attrBtns = [...document.querySelectorAll('.hs-attr-filter')];
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
        // data-alias = abbreviations + acronym (aghs→Aghanim's Scepter, bkb→…).
        const alias = (cell?.dataset.alias || '').toLowerCase();
        const okSearch = !terms.length
          || terms.some(t => name.includes(t) || alias.includes(t));
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
            const off = parseInt(e.dataset.dynOffset || '0', 10);
            dynRenderRow(e, manifest, dynWindow(manifest, off), currentVersion, off);
          };
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
            if (newOff < 0 || newOff + 12 > manifest.patches.length) return;
            entityDiv.dataset.dynOffset = String(newOff);
            const cv = dynCurrentVersion();
            const old = entityDiv.querySelector('.dyn-row-wrap');
            if (old) old.remove();
            dynRenderRow(entityDiv, manifest, dynWindow(manifest, newOff), cv, newOff);
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

// ---- CREEPS TABLE: click icon → copy "-createhero <name> neutral" ----
(function() {
  const icons = document.querySelectorAll('.creep-copy[data-cmd]');
  if (!icons.length) return;

  // One reusable toast element appended to body.
  let toast = null;
  let hideTimer = null;
  function showToast(x, y) {
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'copy-toast';
      toast.textContent = 'Copied';
      document.body.appendChild(toast);
    }
    toast.style.left = x + 'px';
    toast.style.top = y + 'px';
    // restart the fade animation
    toast.classList.remove('is-visible');
    void toast.offsetWidth; // force reflow so re-adding the class re-triggers
    toast.classList.add('is-visible');
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => toast.classList.remove('is-visible'), 900);
  }

  async function copyCmd(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (e) {
      // Fallback for non-secure contexts (file://, http on some browsers)
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (_) {}
      document.body.removeChild(ta);
      return ok;
    }
  }

  icons.forEach(img => {
    img.style.cursor = 'pointer';
    img.addEventListener('click', async (e) => {
      const cmd = img.getAttribute('data-cmd');
      if (!cmd) return;
      const ok = await copyCmd(cmd);
      if (ok) {
        const r = img.getBoundingClientRect();
        showToast(r.left + r.width / 2, r.top - 6);
      }
    });
  });
})();

// ---- CREEPS TABLE: sortable columns ----
(function() {
  const table = document.querySelector('.creeps-table');
  if (!table) return;
  const tbody = table.querySelector('tbody');
  const headers = [...table.querySelectorAll('thead th.sortable')];
  if (!tbody || !headers.length) return;

  // Map column key → body-cell index. data-idx is authored server-side so
  // it stays correct despite the colspan=2 on the Юнит header (which makes
  // DOM th position diverge from cell index).
  const colIndex = {};
  headers.forEach(th => {
    if (th.dataset.col) colIndex[th.dataset.col] = parseInt(th.dataset.idx, 10);
  });

  // Sort value for a cell: prefer the numeric data-lvl on the level
  // column (its text gets blanked by collapseLevels), else parse the
  // first number out of the text (handles "240", "+0,5", "3-5",
  // "1400/800", "0%", "Ближняя (100)"), else fall back to lowercased
  // text. Empty cells return null and always sink to the bottom.
  function cellVal(tr, idx) {
    const td = tr.children[idx];
    if (!td) return null;
    if (td.dataset.lvl !== undefined && td.dataset.lvl !== '') {
      return parseFloat(td.dataset.lvl);
    }
    // Icon-only columns carry a data-sort value: a number (rank) for flag
    // columns (dash 0 < No 1 < Yes 2), or a string (e.g. the Unit name).
    if (td.dataset.sort !== undefined) {
      const s = td.dataset.sort;
      const n = parseFloat(s);
      return isNaN(n) ? s.toLowerCase() : n;
    }
    const t = td.textContent.trim();
    if (!t || t === ' ') return null;
    if (t === '-') return 0;   // explicit "no mana" — sorts as the minimum, not last
    const m = t.replace(',', '.').match(/-?\d+(?:\.\d+)?/);
    return m ? parseFloat(m[0]) : t.toLowerCase();
  }

  // Show the level number once per consecutive run; blank the repeats and
  // draw the group divider (tier-break) at each run start. Works in any
  // row order, so the grouped look survives sorting by level. Visibility-
  // aware: rows hidden by filter (mr-attack-out / mr-filtered-out /
  // mr-search-out → display:none) don't participate in run tracking — else
  // a hidden "first of group" row would leave the next visible row blank
  // (the bug behind the ranged filter losing all level labels).
  function collapseLevels(rows) {
    let prev = null;
    rows.forEach(tr => {
      const cell = tr.querySelector('.lvl-cell');
      if (!cell) return;
      if (tr.classList.contains('mr-attack-out')
          || tr.classList.contains('mr-filtered-out')
          || tr.classList.contains('mr-search-out')) return;
      const lvl = cell.dataset.lvl;
      if (lvl !== prev) { cell.textContent = lvl; tr.classList.add('tier-break'); }
      else { cell.textContent = ''; tr.classList.remove('tier-break'); }
      prev = lvl;
    });
  }

  // Unit Abilities: group consecutive rows of the SAME unit — show the Lvl +
  // Unit icon only on the first row of each run, hide on the rest (cells stay
  // for alignment). Recomputed after every sort so it works in any order.
  const isUA = table.classList.contains('unit-abilities-table');
  function groupByUnit(rows) {
    let prevUnit = null, prevLvl = null;
    rows.forEach(tr => {
      const u = tr.dataset.unit;
      const lvlCell = tr.querySelector('.ua-lvl');
      const lvl = lvlCell ? lvlCell.dataset.lvl : null;
      // Level grouping — show the number once per level run + the horizontal
      // tier divider at each level change (mirrors the Neutral Creeps table).
      if (lvl !== prevLvl) {
        if (lvlCell) lvlCell.textContent = lvl;
        tr.classList.add('tier-break');
      } else {
        if (lvlCell) lvlCell.textContent = '';
        tr.classList.remove('tier-break');
      }
      // Unit-icon dedup — show the icon only on the first row of each unit run.
      if (u !== prevUnit) tr.classList.remove('ua-dup');
      else tr.classList.add('ua-dup');
      prevUnit = u; prevLvl = lvl;
    });
  }
  const groupRows = isUA ? groupByUnit : collapseLevels;
  // Expose to the attack-type filter (lives in a sibling IIFE) so it can
  // re-run grouping after hiding rows — else hidden "first of run" rows
  // leave the next visible row with a blank lvl cell.
  table._groupRows = groupRows;

  // Merge consecutive identical ability cells into one rowspanned cell (only
  // in the default order — sorting reads cells by column index, so we un-merge
  // first). Process columns right-to-left so removals don't shift earlier idx.
  let abilMerges = [];
  function unmergeAbilityRuns() {
    for (let i = abilMerges.length - 1; i >= 0; i--) {
      abilMerges[i].tr.insertBefore(abilMerges[i].td, abilMerges[i].next);
    }
    abilMerges = [];
    tbody.querySelectorAll('td').forEach(td => {
      if (td.rowSpan > 1 && /\bcol-ability/.test(td.className)) td.rowSpan = 1;
    });
  }
  function mergeAbilityRuns(rows) {
    ['ability3', 'ability2', 'ability1'].forEach(col => {
      const idx = colIndex[col];
      if (idx == null) return;
      let i = 0;
      while (i < rows.length) {
        const td = rows[i].children[idx];
        const name = td && td.dataset.name;
        if (!name) { i++; continue; }
        // Shared auras stay per-unit: each frog keeps its own cell so a row
        // click highlights it (merging would rowspan 4 frogs into one block).
        if (name === 'Riverborn Aura') { i++; continue; }
        let j = i + 1;
        while (j < rows.length && rows[j].children[idx] &&
               rows[j].children[idx].dataset.name === name) j++;
        if (j - i > 1) {
          td.rowSpan = j - i;
          for (let k = i + 1; k < j; k++) {
            const rm = rows[k].children[idx];
            abilMerges.push({ tr: rows[k], td: rm, next: rm.nextSibling });
            rm.remove();
          }
        }
        i = j;
      }
    });
  }

  let sortCol = null, sortState = 0;  // 0 = neutral, 1 = descending, 2 = ascending
  const originalOrder = [...tbody.querySelectorAll('tr')];

  // Moving rows in the DOM resets CSS animations to t=0. Snapshot currentTime
  // for every animated element before the move, restore it after so the
  // autocast-snake comet continues without restarting.
  function snapAnims(rows) {
    const map = new Map();
    rows.forEach(tr => {
      tr.querySelectorAll('[style*="animation"], .autocast-snake rect').forEach(el => {
        const anims = el.getAnimations();
        if (anims.length) map.set(el, anims.map(a => a.currentTime));
      });
    });
    return map;
  }
  function restoreAnims(map) {
    map.forEach((times, el) => {
      el.getAnimations().forEach((a, i) => { if (times[i] != null) a.currentTime = times[i]; });
    });
  }

  function applySort(col, dir) {
    unmergeAbilityRuns();             // restore full cells before index-based sort
    const idx = colIndex[col];
    const rows = [...tbody.querySelectorAll('tr')];
    rows.sort((a, b) => {
      const va = cellVal(a, idx), vb = cellVal(b, idx);
      if (va === null && vb === null) return 0;
      if (va === null) return 1;          // empties always last
      if (vb === null) return -1;
      if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    });
    const snap = snapAnims(rows);
    rows.forEach(tr => tbody.appendChild(tr));
    restoreAnims(snap);
    groupRows(rows);
  }

  headers.forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      // 3-state cycle: neutral → descending → ascending → neutral.
      if (sortCol === col) sortState = (sortState + 1) % 3;
      else { sortCol = col; sortState = 1; }     // first click = descending (largest first)
      headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
      if (sortState === 0) {
        // Back to neutral: restore the default level-grouped order, dim ↕ returns.
        sortCol = null;
        unmergeAbilityRuns();
        const snap0 = snapAnims(originalOrder);
        originalOrder.forEach(tr => tbody.appendChild(tr));
        restoreAnims(snap0);
        groupRows(originalOrder);
        mergeAbilityRuns(originalOrder);   // re-merge in default order
      } else {
        const dir = sortState === 1 ? -1 : 1;
        th.classList.add(dir === 1 ? 'sort-asc' : 'sort-desc');
        applySort(col, dir);
      }
    });
  });

  // Initial pass: collapse/group the default order + merge ability runs.
  groupRows([...tbody.querySelectorAll('tr')]);
  mergeAbilityRuns([...tbody.querySelectorAll('tr')]);

  // Unit Abilities VIEW filter (Standard | Only Auras). Toggles a class on
  // the table; CSS hides non-aura rows. Also reorders columns: in "Only Auras"
  // the visible order is Lvl/Unit/Ability | Radius/Duration | Aura Stack/Through
  // BKB/AS Effect/MS Effect | Effect 1-3 — grouped so the category header (kept
  // in Auras view too) spans contiguous columns.
  const uaView = document.getElementById('ua-view-mode');
  if (uaView) {
    const STD_ORDER = ['lvl', 'unit', 'ability', 'type', 'damage',
      'manacost', 'cooldown', 'duration', 'cast_range', 'aoe', 'stackable',
      'dispel', 'through_bkb', 'as_effect', 'ms_effect',
      'effect', 'effect2', 'effect3'];
    // Auras view: VISIBLE columns first, grouped by category (Basic | Essentials
    // = Radius,Duration | Extra | Effects), then the hidden-by-CSS columns
    // (type/damage/manacost/cooldown/cast_range/dispel) at the end so the DOM
    // child count stays in sync.
    const AURA_ORDER = ['lvl', 'unit', 'ability', 'aoe', 'duration',
      'stackable', 'through_bkb', 'as_effect', 'ms_effect',
      'effect', 'effect2', 'effect3',
      'type', 'damage', 'manacost', 'cooldown', 'cast_range', 'dispel'];
    const headRow = table.querySelector('thead .col-row')
      || table.querySelector('thead tr');
    // Resize each category cell to its currently-visible leaf columns (Auras
    // hides some), so the category header lines up in both views.
    function recomputeUaCats() {
      table.querySelectorAll('thead tr.cat-row th.cat-head[data-cat]').forEach(head => {
        let span = 0;
        table.querySelectorAll('thead tr.col-row th[data-cat="' + head.dataset.cat + '"]')
          .forEach(th => { if (th.offsetParent !== null) span += th.colSpan || 1; });
        head.colSpan = span || 1;
      });
    }

    function reorderCells(order) {
      const reorderOne = (parent) => {
        order.forEach(k => {
          const cell = [...parent.children].find(c => c.dataset.col === k);
          if (cell) parent.appendChild(cell);
        });
      };
      if (headRow) reorderOne(headRow);
      tbody.querySelectorAll('tr').forEach(reorderOne);
      // Refresh colIndex (used by cellVal) for the new column positions.
      Object.keys(colIndex).forEach(k => delete colIndex[k]);
      if (headRow) {
        [...headRow.children].forEach((th, i) => {
          if (th.dataset.col) colIndex[th.dataset.col] = i;
        });
      }
    }

    // Vertical category dividers: left border on the first VISIBLE column of each
    // category (after the first), on the header col-row AND every body cell so the
    // line runs the full height. Driven by data-cat so it tracks the Auras reorder.
    // AURA_HIDDEN mirrors the columns hidden by .filter-auras in styles.css.
    const AURA_HIDDEN = new Set(['type', 'damage', 'manacost', 'cooldown', 'cast_range', 'dispel']);
    function markCatEdges(auras) {
      const hidden = auras ? AURA_HIDDEN : null;
      const rows = [headRow, ...tbody.querySelectorAll('tr')];
      rows.forEach(row => {
        if (!row) return;
        let prevCat = null;
        [...row.children].forEach(cell => {
          cell.classList.remove('cat-edge');
          const col = cell.dataset.col, cat = cell.dataset.cat;
          if (!col || (hidden && hidden.has(col))) return;   // skip hidden columns
          if (prevCat !== null && cat && cat !== prevCat) cell.classList.add('cat-edge');
          if (cat) prevCat = cat;
        });
      });
    }

    const applyUaView = () => {
      const auras = uaView.value === 'auras';
      table.classList.toggle('filter-auras', auras);
      reorderCells(auras ? AURA_ORDER : STD_ORDER);
      recomputeUaCats();          // category header spans the now-visible columns
      markCatEdges(auras);        // category dividers track the visible columns
      groupRows(auras
        ? [...tbody.querySelectorAll('tr.ua-row-aura')]
        : [...tbody.querySelectorAll('tr')]);
    };
    uaView.addEventListener('change', applyUaView);
    markCatEdges(false);          // initial Standard-view dividers
  }

  // Upgrades — binary switch. Toggles `.show-upgrades` on the UA table;
  // CSS draws a soft rounded outline + faint fill on every `td.leveled`.
  const uaUpg = document.getElementById('ua-upgrades-mode');
  if (uaUpg && table) {
    const apply = () => table.classList.toggle('show-upgrades', uaUpg.checked);
    uaUpg.addEventListener('change', apply);
    apply();
  }
})();

// ---- UNIT ABILITIES: collapsed upgrade cells ("40…26") expand on click into a
// floating popover with the full per-tier list. Fixed-positioned, clamped to the
// viewport, so the column width never changes. ----
(function() {
  const table = document.querySelector('.unit-abilities-table');
  if (!table) return;
  let pop = null, openBtn = null;
  function ensurePop() {
    if (!pop) {
      pop = document.createElement('div');
      pop.className = 'lvl-popover';
      pop.setAttribute('aria-hidden', 'true');
      document.body.appendChild(pop);
    }
    return pop;
  }
  function close() {
    if (pop) pop.classList.remove('show');
    if (openBtn) { openBtn.setAttribute('aria-expanded', 'false'); openBtn = null; }
  }
  function open(btn) {
    const p = ensurePop();
    p.textContent = btn.dataset.full || btn.textContent;
    p.classList.add('show');
    const r = btn.getBoundingClientRect();
    const pr = p.getBoundingClientRect();
    let left = r.left + r.width / 2 - pr.width / 2;
    left = Math.max(6, Math.min(left, window.innerWidth - pr.width - 6));
    let top = r.top - pr.height - 6;            // prefer above
    if (top < 6) top = r.bottom + 6;            // flip below if no room
    p.style.left = left + 'px';
    p.style.top = top + 'px';
    btn.setAttribute('aria-expanded', 'true');
    openBtn = btn;
  }
  table.addEventListener('click', (e) => {
    const btn = e.target.closest('.lvl-toggle');
    if (!btn) return;
    e.preventDefault();
    if (openBtn === btn) close(); else { close(); open(btn); }
  });
  document.addEventListener('click', (e) => {
    if (openBtn && !e.target.closest('.lvl-toggle')) close();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
  // The table scrolls inside its own box → close on any scroll so the popover
  // never detaches from its cell.
  window.addEventListener('scroll', close, true);
  window.addEventListener('resize', close);
})();

// ---- CREEPS TABLE: per-stat changelog tooltip (HP / Armor / Mana / Magres) ----
(function() {
  const cells = document.querySelectorAll('td[data-hist], td[data-name]');
  if (!cells.length) return;

  let tip = null;
  function ensureTip() {
    if (!tip) {
      tip = document.createElement('div');
      tip.className = 'stat-hist-tip';
      document.body.appendChild(tip);
    }
    return tip;
  }

  // "23.02.2022" -> "23.02.22"
  function shortDate(d) {
    const p = (d || '').split('.');
    if (p.length === 3 && p[2].length === 4) p[2] = p[2].slice(2);
    return p.join('.');
  }
  // Mean of a slash/space value ("40/36/32/26" -> 33.5, "12.0" -> 12).
  function meanOf(s) {
    const nums = String(s).split(/[\/\s]+/)
      .map(x => parseFloat(x.replace(',', '.'))).filter(isFinite);
    return nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : NaN;
  }
  // Colour reflects buff/nerf, not raw direction: for lower-is-better stats
  // (cooldown, mana, BAT) a DROP is the buff (green). The % keeps its real sign.
  function pctHtml(ov, nv, lowerBetter) {
    const o = meanOf(ov), n = meanOf(nv);
    if (!isFinite(o) || !isFinite(n) || o === 0) return '';
    // Divide by |o| so a negative baseline keeps the real direction:
    // armor -1 → 0 is a +100% gain (a buff), not -100%.
    const pct = (n - o) / Math.abs(o) * 100;
    const good = lowerBetter ? pct < 0 : pct > 0;
    const cls = pct === 0 ? 'flat' : (good ? 'up' : 'down');
    const sign = pct > 0 ? '+' : '';
    let num = pct.toFixed(1);
    if (num.endsWith('.0')) num = num.slice(0, -2);  // 50.0 → 50, 1900.0 → 1900
    return ' <span class="stat-pct ' + cls + '">' + sign + num + '%</span>';
  }
  function chgHead(patch, date) {
    return '<div class="stat-chg-head"><span class="chg-patch">' + patch
         + '</span><span class="chg-date">' + shortDate(date) + '</span></div>';
  }
  // One history entry → its old/new values (display + numeric) + polarity, or
  // null for non-value markers (A added / R removed / P replaced) which carry
  // no comparable value. 'C' computed cells carry pretty display (p3/p4) AND
  // raw numerics (p5/p6) so the % isn't skewed by thousands formatting.
  function valEntry(p) {
    const k = p[2];
    if (k === 'V') return { dispOld: p[3], dispNew: p[4], numOld: p[3], numNew: p[4], lb: p[5] === 'lo' };
    if (k === 'F') return { dispOld: p[4], dispNew: p[5], numOld: p[4], numNew: p[5], lb: p[6] === 'lo' };
    if (k === 'C') return { dispOld: p[3], dispNew: p[4], numOld: p[5], numNew: p[6], lb: p[7] === 'lo' };
    if (k === 'N') return { dispOld: p[3], dispNew: p[4], numOld: p[3], numNew: p[4], lb: false };
    return null;
  }
  // Overall first-observed → today summary, shown at the TOP of the tooltip
  // (above the newest patch) with a divider below. Needs >1 value change;
  // scans past A/R/P markers to the first & last real value entries.
  function netSummary(entries) {
    const vals = entries.map(e => valEntry(e.split('|'))).filter(Boolean);
    if (vals.length < 2) return '';
    const first = vals[0], last = vals[vals.length - 1];
    const o = meanOf(first.numOld), n = meanOf(last.numNew);
    if (!isFinite(o) || !isFinite(n) || o === 0) return '';
    const pct = (n - o) / Math.abs(o) * 100;
    // Net 0% (value drifted then returned to its start) is still shown — flat.
    const cls = pct === 0 ? 'flat' : ((last.lb ? pct < 0 : pct > 0) ? 'up' : 'down');
    const sign = pct > 0 ? '+' : '';
    let num = pct.toFixed(1);
    if (num.endsWith('.0')) num = num.slice(0, -2);
    return '<div class="stat-net"><span class="stat-net-label">overall</span>'
         + first.dispOld + ' → ' + last.dispNew
         + ' <span class="stat-pct ' + cls + '">' + sign + num + '%</span></div>';
  }
  // Parse one entry → { patch, date, line }. Format: patch|date|kind|...parts
  //   V old new pol          stat value change
  //   F label old new pol    ability value change
  //   A name / R name / P old new  ability added / removed / replaced
  function entryParts(e) {
    const p = e.split('|');
    const patch = p[0], date = p[1], kind = p[2];
    let line;
    if (kind === 'A') {
      line = p[3] + ' <span class="chg-tag added">ADDED</span>';
    } else if (kind === 'R') {
      line = p[3] + ' <span class="chg-tag removed">REMOVED</span>';
    } else if (kind === 'P') {
      line = p[3] + ' <span class="chg-cycle">⇄</span> ' + p[4]
           + ' <span class="chg-tag replaced">REPLACED</span>';
    } else if (kind === 'F') {
      line = '<span class="chg-label">' + p[3] + ':</span> ' + p[4] + ' → '
           + p[5] + pctHtml(p[4], p[5], p[6] === 'lo');
    } else if (kind === 'N') {
      // No-percentage value change (computed columns): show old → new only.
      line = p[3] + ' → ' + p[4];
    } else if (kind === 'C') {
      // Computed column: pretty short display (p3→p4) with a % delta derived
      // from the raw values (p5, p6) so scaling never skews it. p7 = polarity.
      line = p[3] + ' → ' + p[4] + pctHtml(p[5], p[6], p[7] === 'lo');
    } else {
      // 'V' stat value (patch|date|V|old|new|pol), or legacy patch|date|old|new
      const isV = kind === 'V';
      const ov = isV ? p[3] : p[2];
      const nv = isV ? p[4] : p[3];
      line = ov + ' → ' + nv + pctHtml(ov, nv, isV && p[5] === 'lo');
    }
    return { patch: patch, date: date, line: line };
  }

  function show(td) {
    const entries = (td.dataset.hist || '').split(';').filter(Boolean);
    const name = td.dataset.name || '';
    if (!entries.length && !name) return;
    const el = ensureTip();
    // Group changes from the same patch under one header.
    const groups = [];
    entries.forEach(e => {
      const ep = entryParts(e);
      const g = groups[groups.length - 1];
      if (g && g.patch === ep.patch) g.lines.push(ep.line);
      else groups.push({ patch: ep.patch, date: ep.date, lines: [ep.line] });
    });
    groups.reverse();  // newest patch on top, oldest at the bottom
    // Ability name as a centered header above the changelog (if any).
    const nameHtml = name ? '<div class="abil-tip-name">' + name + '</div>' : '';
    // Net first→today summary at the very top (gold test: cells flagged data-net).
    const netHtml = (td.dataset.net !== undefined) ? netSummary(entries) : '';
    el.innerHTML = nameHtml + netHtml + groups.map(g =>
      '<div class="stat-chg">' + chgHead(g.patch, g.date)
      + g.lines.map(l => '<div class="stat-chg-line">' + l + '</div>').join('')
      + '</div>'
    ).join('');
    el.classList.add('is-visible');
    const r = td.getBoundingClientRect();
    const tr = el.getBoundingClientRect();
    let left = r.left + r.width / 2 - tr.width / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tr.width - 8));
    el.style.left = left + 'px';
    // Vertical placement: prefer above the cell, flip below if it would clip
    // the top. For tall tooltips (taller than the space on either side —
    // e.g. Guardian Greaves' long changelog) clamp into the viewport so the
    // box never runs off-screen; the CSS max-height + overflow lets the
    // overflow scroll. Always keep an 8px margin top and bottom.
    const margin = 8;
    const spaceAbove = r.top - margin;
    const spaceBelow = window.innerHeight - r.bottom - margin;
    let top;
    if (tr.height <= spaceAbove) {
      top = r.top - tr.height - margin;            // fits above
    } else if (tr.height <= spaceBelow) {
      top = r.bottom + margin;                     // fits below
    } else {
      // Doesn't fit either side — pin to whichever side has more room and
      // let it clamp to the viewport edge (CSS caps its height).
      top = spaceAbove >= spaceBelow ? margin : (r.bottom + margin);
    }
    top = Math.max(margin, Math.min(top, window.innerHeight - tr.height - margin));
    if (top < margin) top = margin;                // last-resort clamp
    el.style.top = top + 'px';
  }
  function hide() { if (tip) tip.classList.remove('is-visible'); }

  // Event delegation (not per-cell binding): cells can be removed/re-inserted
  // by the ability-merge logic, so listeners bound at load would be lost on
  // the restored cells. Delegation on the table covers any current cell.
  const SEL = 'td[data-hist], td[data-name], .mr-const[data-hist]';
  // Bind to every table OR standalone history-chip that may carry data-hist:
  // creeps-table (neutral creeps), mr-table (mana items), and the constants
  // chips in the page blurb.
  const targets = [
    ...document.querySelectorAll('.creeps-table, .mr-table'),
    ...document.querySelectorAll('.mr-const[data-hist]'),
  ];
  let curTd = null;
  targets.forEach(tbl => {
    tbl.addEventListener('mouseover', e => {
      // A `?` qhint badge inside a history cell has its own tooltip — let it
      // win and suppress the cell's changelog popup while hovering it.
      if (e.target.closest('.qhint')) { if (curTd) { curTd = null; hide(); } return; }
      const td = e.target.closest(SEL);
      if (td && td !== curTd) { curTd = td; show(td); }
    });
    tbl.addEventListener('mouseout', e => {
      const td = e.target.closest(SEL);
      if (!td) return;
      const to = e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest(SEL);
      if (to !== td) { curTd = null; hide(); }
    });
  });
  window.addEventListener('scroll', hide, { passive: true });
})();

// ---- CREEPS / UNIT ABILITIES: size the scroll box to fit the viewport ----
// The table lives in a height-capped .creeps-scroll box (the page is locked so
// only this box scrolls — one scrollbar). CSS sets the box max-height; this only
// measures the category row's rendered height into --cat-row-h, which the
// two-row sticky header offset (col-row top: calc(--cat-row-h - 2px)) needs —
// CSS calc can't read it.
(function() {
  const box = document.querySelector('.creeps-page .creeps-scroll');
  if (!box) return;
  const catRow = box.querySelector('table thead tr.cat-row');
  function size() {
    // CSS handles the box's max-height now: `calc(100vh - var(--site-nav-h)
    // - 12px)` keeps it sized to fit the viewport regardless of scroll
    // position, in concert with `position: sticky; top: var(--site-nav-h)`
    // on the box itself. JS only updates --cat-row-h (which CSS calc can't
    // measure — it depends on the rendered text height of the category row).
    //
    // Two-row sticky header (Neutral Creeps): pin the column row exactly
    // under the category row. Use the fractional rect height (rounded) for an
    // accurate offset; the col-row CSS also pulls up 1px to mask any seam.
    // Unit Abilities has no .cat-row → 0 so its single header row pins flush.
    // Math.floor (not round): pairs with the col-row's -2px pull-up so the
    // col-row always starts at least 2px BEFORE the cat-row's true bottom,
    // guaranteeing the two sticky rows overlap regardless of fractional
    // heights — kills the scroll-time gap where body cells showed through.
    document.documentElement.style.setProperty(
      '--cat-row-h',
      (catRow ? Math.floor(catRow.getBoundingClientRect().height) : 0) + 'px');
  }
  size();
  window.addEventListener('resize', size, { passive: true });
  // Recompute after images (the helmet logo grows the nav) finish loading —
  // an early measurement underestimates the nav height and lets the box run
  // past the viewport, which makes the page scroll and the toolbar drift.
  window.addEventListener('load', size);
  const logo = document.querySelector('.nav-brand-logo');
  if (logo && !logo.complete) logo.addEventListener('load', size);
})();

// ---- CREEPS TABLE: pin identity columns on horizontal scroll ----
(function() {
  const table = document.querySelector('.creeps-table');
  if (!table) return;
  const firstRow = table.querySelector('tbody tr');
  if (!firstRow) return;

  // Pin sticky-column widths to their FULL-roster initial measurement so the
  // attack-type filter (display:none on hidden rows) can't reshape the lvl /
  // icon / name columns when the visible roster changes. With table-layout:
  // auto, min-width alone only sets a floor — the browser can still GROW
  // pinned columns when other (non-sticky) columns shrink and the table's
  // `min-width:100%` forces it back to container width. Pin min + max + width
  // on the col-row sticky <th>s, AND pin icon col individually via every
  // body row's .creep-icon-cell (the Юнит th's colspan=2 only pins the
  // icon+name SUM, not their internal ratio). Run once on init, before any
  // filter has a chance to fire.
  (function pinStickyCols() {
    if (table.classList.contains('heroes-dyn-table')) return;
    const tds = [...firstRow.children];
    if (tds.length < 3) return;
    const wLvl  = Math.ceil(tds[0].getBoundingClientRect().width);
    const wIcon = Math.ceil(tds[1].getBoundingClientRect().width);
    const wName = Math.ceil(tds[2].getBoundingClientRect().width);
    const pin = (el, w) => {
      el.style.minWidth = w + 'px';
      el.style.maxWidth = w + 'px';
      el.style.width    = w + 'px';
    };
    const headStickies = table.querySelectorAll('thead tr.col-row th.sticky-col');
    // Two head shapes share this IIFE:
    //   • Neutral Stats (.creeps-table.mode-standard): 2 sticky <th>s — lvl
    //     and "Юнит" (colspan=2 over icon+name). Second th gets wIcon+wName.
    //   • Unit Abilities (.unit-abilities-table): 3 sticky <th>s — lvl, unit,
    //     ability, all individual. Each th gets its own body-cell width.
    // Differentiator = sticky-th count, not table class — keeps the code
    // ready for any future creeps-table variant.
    if (headStickies.length === 2) {
      pin(headStickies[0], wLvl);
      pin(headStickies[1], wIcon + wName);   // colspan'd Юнит
    } else if (headStickies.length >= 3) {
      pin(headStickies[0], wLvl);
      pin(headStickies[1], wIcon);
      pin(headStickies[2], wName);
    }
    // Pin icon AND name cols individually on every body row. The Юнит th's
    // colspan=2 only pins the icon+name SUM — max-width on a colspan'd cell
    // doesn't enforce per-column limits in auto layout, so the name col can
    // still grow/shrink with its widest visible content (Forest Troll
    // Berserker disappearing on melee filter was the trigger). Pinning both
    // body cols freezes the internal split. Covers both tables — the
    // selectors match Neutral Stats (.col-name) and UA (.ua-ability) cells.
    table.querySelectorAll('tbody tr > td.creep-icon-cell.sticky-col')
      .forEach(td => pin(td, wIcon));
    table.querySelectorAll('tbody tr > td.col-name.sticky-col, tbody tr > td.ua-ability.sticky-col')
      .forEach(td => pin(td, wName));
  })();

  // Body identity cells are the first three: lvl(0), icon(1), name(2).
  // The header has only two cells over them: lvl th(0) + Юнит th(1,
  // colspan=2). Compute cumulative left offsets from the body widths and
  // apply them to both the body sticky cells and the header sticky cells.
  function applyLeftOffsets() {
    // Use the first VISIBLE row — once attack-type filter is applied, the
    // cached firstRow may be display:none, making its getBoundingClientRect
    // collapse to zero and breaking sticky lefts.
    const measureRow = [...table.querySelectorAll('tbody tr')]
      .find(tr => tr.offsetParent !== null) || firstRow;
    const tds = [...measureRow.children];
    if (tds.length < 3) return;
    const wLvl  = tds[0].getBoundingClientRect().width;
    const wIcon = tds[1].getBoundingClientRect().width;
    const lefts = [0, wLvl, wLvl + wIcon];           // lvl, icon, name

    // Body rows. Most rows have all 3 sticky identity cells (lvl, icon, name).
    // On the Unit Abilities page, a multi-ability unit rowspans its lvl+icon
    // cells, so continuation rows carry ONLY the ability sticky cell — which
    // belongs at the 3rd offset. Assign by how many sticky cells the row has.
    table.querySelectorAll('tbody tr').forEach(tr => {
      const sc = [...tr.children].filter(c => c.classList.contains('sticky-col'));
      // Creeps: 3 sticky cells (lvl, icon, name). Unit Abilities: 2 (lvl, unit).
      // UA continuation rows (rowspanned lvl+unit) have 0 → nothing to pin.
      sc.forEach((cell, i) => { cell.style.left = lefts[i] + 'px'; });
    });
    // Header sticky cells. heroes_dyn has ONE frozen column (hero) but TWO
    // header rows over it (super-category + version), so BOTH header sticky
    // cells pin at left:0 — not the creeps lvl(0)+unit(wLvl) two-column layout.
    const headStickies = table.querySelectorAll('thead th.sticky-col');
    if (table.classList.contains('heroes-dyn-table')) {
      headStickies.forEach(th => { th.style.left = '0px'; });
    } else {
      if (headStickies[0]) headStickies[0].style.left = '0px';
      if (headStickies[1]) headStickies[1].style.left = wLvl + 'px';
    }
  }

  applyLeftOffsets();
  window.addEventListener('resize', applyLeftOffsets, { passive: true });

  // Click a cell to mark its row (single-select, no animation). Clicking
  // another row moves the mark; clicking the marked row again clears it.
  // Matches the simpler highlight behaviour used by the Mana Items table —
  // multi-select + fade-flash earlier here was hard to read once a few
  // rows were marked.
  const tbody = table.querySelector('tbody');
  if (tbody) {
    tbody.addEventListener('click', e => {
      if (e.target.closest('a, img')) return;
      const tr = e.target.closest('tr');
      if (!tr) return;
      const was = tr.classList.contains('row-marked');
      tbody.querySelectorAll('tr.row-marked').forEach(r =>
        r.classList.remove('row-marked', 'row-flash'));
      if (!was) tr.classList.add('row-marked');
    });
  }

  // Overlay frame around the pinned identity block, shown while scrolled.
  // It lives in .creeps-page (non-scrolling), so its border + shadow keep
  // repainting during scroll — unlike box-shadow on the sticky cells,
  // which Chrome drops mid-scroll.
  const scroller = table.closest('.creeps-scroll');
  const page = table.closest('.creeps-page');
  const frame = page && page.querySelector('.sticky-frame');       // vertical

  function positionFrames() {
    if (!scroller || !page) return;
    const firstTds = [...firstRow.children];
    if (firstTds.length < 3) return;
    const pageR  = page.getBoundingClientRect();
    const scrR   = scroller.getBoundingClientRect();
    const tableR = table.getBoundingClientRect();
    // Right edge of the frozen identity block = right edge of the LAST sticky
    // column in the row. Creeps/UA pin 2-3 columns; the heroes_dyn matrix pins
    // just one (the hero name) — measuring the last sticky cell keeps the
    // divider correct for any number of frozen columns (hardcoding firstTds[2]
    // put the divider 2 columns too far right on the single-column matrix).
    const stickyCells = firstRow.querySelectorAll('.sticky-col');
    const lastSticky = table.classList.contains('heroes-dyn-table')
      ? (table.querySelector('thead th.hd-hero.sticky-col')
          || table.querySelector('thead th.hd-hero')
          || stickyCells[stickyCells.length - 1]
          || firstTds[2])
      : (stickyCells[stickyCells.length - 1] || firstTds[2]);
    const nameR  = lastSticky.getBoundingClientRect();  // right edge of pinned block
    // Anchor the divider's top to the VISIBLE (pinned) header bottom. The
    // <thead> element itself is position:static — only its <th> cells are
    // position:sticky — so once the box scrolls down, the thead's own rect
    // scrolls up (its bottom goes negative) while the column headers stay
    // pinned at the box top. Measuring table.tHead therefore made the divider's
    // top climb ABOVE the visible header (the bright line poked past the
    // category header on vertical+horizontal scroll). Anchor instead to a
    // PINNED header cell (the col-row's sticky-col <th>): its bottom tracks the
    // real visible header bottom both at rest (natural position below the blurb)
    // and once pinned under the nav.
    const headCell = table.querySelector('thead tr.col-row th.sticky-col')
      || table.querySelector('thead tr.col-row th')
      || table.tHead;
    const headBottom = headCell
      ? headCell.getBoundingClientRect().bottom
      : scrR.top;
    // Vertical divider: at the right edge of the frozen lvl/unit columns,
    // starting BELOW the sticky column header and spanning the rest of height.
    if (frame) {
      const bottom = Math.min(scrR.bottom, tableR.bottom);
      frame.style.left   = (nameR.right - pageR.left) + 'px';
      frame.style.top    = (headBottom - pageR.top) + 'px';
      frame.style.height = Math.max(0, bottom - headBottom) + 'px';
      frame.style.width  = '0px';
    }
  }

  if (scroller) {
    const syncFrameVisibility = () => {
      const hasOverflowX = scroller.scrollWidth - scroller.clientWidth > 1;
      const sx = hasOverflowX && scroller.scrollLeft > 0;
      scroller.classList.toggle('scrolled', sx);
      if (frame) frame.classList.toggle('visible', sx);
    };
    // The frozen-pane divider's geometry depends on layout, not on the scroll
    // position inside the box: sticky columns and sticky headers keep the same
    // screen-space edges while the tbody scrolls underneath. Re-reading layout
    // on every scroll frame was wasted work on the widest tables.
    let ticking = false;
    const positionFramesRaf = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        try {
          positionFrames();
          syncFrameVisibility();
        } finally { ticking = false; }
      });
    };
    // The page body is locked — vertical + horizontal scrolling both happen
    // INSIDE .creeps-scroll, not on the window. The sticky header pins to the
    // box top while the tbody scrolls under it, and the table's bounding rect
    // (used to clamp the divider's bottom) moves as the content scrolls — so the
    // divider's top/height must be RE-COMPUTED on every box-scroll frame, not
    // just its visibility. raf-throttled, so it's cheap even on the wide matrix.
    scroller.addEventListener('scroll', positionFramesRaf, { passive: true });
    window.addEventListener('resize', positionFramesRaf, { passive: true });
    // Layout-changing toggles (hide-old / filters) broadcast this so the divider
    // re-anchors to the new column widths + table height.
    window.addEventListener('mr:filter-changed', positionFramesRaf);

    // Super-category header colspans must equal the number of CURRENTLY
    // visible leaf columns in each category — otherwise the static (Expanded)
    // colspans misalign with the collapsed columns in Standard view.
    function recomputeCatColspans() {
      document.querySelectorAll('.cat-head[data-cat]').forEach(head => {
        let span = 0;
        document.querySelectorAll('.col-row th[data-cat="' + head.dataset.cat + '"]')
          .forEach(th => { if (th.offsetParent !== null) span += th.colSpan || 1; });
        head.colSpan = span || 1;
      });
    }

    // View toggle (Standard / Expanded) via the calendar-style select.
    const viewSel = document.getElementById('view-mode');
    if (viewSel) {
      const applyView = () => {
        const expanded = viewSel.value === 'expanded';
        table.classList.toggle('mode-standard', !expanded);
        table.classList.toggle('mode-expanded', expanded);
        recomputeCatColspans();
        applyLeftOffsets();   // column widths changed → recompute pinned offsets
        positionFramesRaf();
      };
      viewSel.addEventListener('change', applyView);
      applyView();            // initial pass (Standard)
    } else {
      recomputeCatColspans();
    }

    // Attack-type filters on Neutral Stats. Uses the same toolbar button
    // markup/style as Hero Stats, but operates on the creeps-table rows.
    const attackBtns = [...document.querySelectorAll('.hs-attack-filter')];
    if (attackBtns.length && table.querySelector('tbody tr[data-attack-type]')) {
      let attackFilter = '';
      const applyAttackFilter = () => {
        table.querySelectorAll('tbody tr[data-attack-type]').forEach(tr => {
          tr.classList.toggle(
            'mr-attack-out',
            !!attackFilter && tr.dataset.attackType !== attackFilter
          );
        });
        attackBtns.forEach(btn => {
          const active = btn.dataset.attackFilter === attackFilter;
          btn.classList.toggle('active', active);
          btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
        // Re-collapse level labels over the now-visible row subset (else
        // hidden "first of group" rows blank the next visible row's lvl).
        if (table._groupRows) {
          table._groupRows([...table.querySelectorAll('tbody tr')]);
        }
        applyLeftOffsets();
      };
      attackBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const next = btn.dataset.attackFilter || '';
          attackFilter = attackFilter === next ? '' : next;
          applyAttackFilter();
        });
      });
      applyAttackFilter();
    }
    positionFramesRaf();
  }
})();


// ---- Body-level tooltip for `.qhint` badges ----
// CSS `::after` tooltips are clipped by .creeps-scroll's overflow:auto and by
// the sticky header. Render a single shared <div> at <body> level, positioned
// via fixed coordinates relative to the hovered badge.
(function() {
  const tip = document.createElement('div');
  tip.className = 'qhint-tip';
  tip.setAttribute('role', 'tooltip');
  document.body.appendChild(tip);

  function show(target) {
    const text = target.getAttribute('data-tooltip') || '';
    if (!text) return;
    // Tooltip content is author-written (UA_HEAD_HINTS / ABIL_MANUAL) — using
    // innerHTML lets header tooltips include coloured legend spans.
    // Wrap %placeholder% variables (Valve description macros — values aren't
    // resolved here) in a styled span so they read as "this is a variable
    // name" rather than mystery raw text.
    tip.innerHTML = text.replace(
      /%([A-Za-z0-9_]+)%/g,
      '<span class="abil-var">$1</span>');
    tip.classList.add('is-visible');
    // Position above the badge; flip below if it would overflow the viewport top.
    const r = target.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();
    let left = r.left + r.width / 2 - tipRect.width / 2;
    left = Math.max(6, Math.min(left, window.innerWidth - tipRect.width - 6));
    let top = r.top - tipRect.height - 8;
    if (top < 6) top = r.bottom + 8;            // not enough room above → drop below
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }
  function hide() { tip.classList.remove('is-visible'); }

  // Selector matches the original `?` badge plus any element that just opts
  // into the body-level tooltip via `.abil-ico-hint` (currently used on
  // ability icons in the Unit Abilities table).
  const TIP_SEL = '.qhint, .abil-ico-hint, .hd-patch[data-tooltip]';
  document.addEventListener('mouseover', (e) => {
    const t = e.target.closest(TIP_SEL);
    if (t) show(t);
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest(TIP_SEL)) hide();
  });
  document.addEventListener('focusin', (e) => {
    const t = e.target.closest(TIP_SEL);
    if (t) show(t);
  });
  document.addEventListener('focusout', (e) => {
    if (e.target.closest(TIP_SEL)) hide();
  });
  // Hide on any scroll (the badge's absolute coords change).
  window.addEventListener('scroll', hide, true);
})();

// ---- Body-level tooltip for `.info-tip` "?" badges (patch pages) ----
// CSS-driven `.info-pop` (position:absolute) overflows the viewport when the
// badge is near a screen edge. A single body-level div is positioned via JS
// so it stays clamped inside the viewport on both axes.
(function() {
  const tip = document.createElement('div');
  tip.className = 'info-pop-body';
  document.body.appendChild(tip);

  function show(target) {
    const pop = target.querySelector('.info-pop');
    if (!pop) return;
    tip.innerHTML = pop.innerHTML;
    tip.classList.add('is-visible');
    const r = target.getBoundingClientRect();
    const tipRect = tip.getBoundingClientRect();
    let left = r.left + r.width / 2 - tipRect.width / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tipRect.width - 8));
    let top = r.top - tipRect.height - 8;
    if (top < 8) top = r.bottom + 8;
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }
  function hide() { tip.classList.remove('is-visible'); }

  document.addEventListener('mouseover', e => {
    const t = e.target.closest('.info-tip');
    if (t) show(t);
  });
  document.addEventListener('mouseout', e => {
    if (e.target.closest('.info-tip')) hide();
  });
  document.addEventListener('focusin', e => {
    const t = e.target.closest('.info-tip');
    if (t) show(t);
  });
  document.addEventListener('focusout', e => {
    if (e.target.closest('.info-tip')) hide();
  });
  window.addEventListener('scroll', hide, true);
})();

// ---- Centre the row jumped to via #anchor (cross-page or same-page) ----
// The Tables pages have an inner `.creeps-scroll` overflow box AND the page
// itself scrolls — `el.scrollIntoView({block:'center'})` only centres within
// the immediate scroll parent (usually the inner box), leaving the row near
// the top of the viewport. Manually centre on BOTH axes: scroll the inner
// container so the row is mid-box, then scroll the window so the box's
// mid-point aligns with the viewport centre.
(function() {
  function centerHash() {
    const h = location.hash.slice(1);
    if (!h) return;
    const el = document.getElementById(decodeURIComponent(h));
    if (!el) return;
    // Give the jumped-to row the SAME selected style as a manual row click
    // (gold frame), replacing the old yellow :target flash. Single-select:
    // clear any previously marked row in the same table first.
    if (el.tagName === 'TR') {
      const tb = el.closest('tbody');
      if (tb) tb.querySelectorAll('tr.row-marked').forEach(r =>
        r.classList.remove('row-marked', 'row-flash'));
      el.classList.add('row-marked');
    }
    // Double rAF: lets table layout, sticky header, and any view-toggle
    // reorderings settle before measuring rects.
    requestAnimationFrame(() => requestAnimationFrame(() => {
      const inner = el.closest('.creeps-scroll');
      if (inner) {
        const ir = inner.getBoundingClientRect();
        const er = el.getBoundingClientRect();
        // Account for the sticky <thead> overlapping the inner box's top —
        // subtract its height so the row centres in the VISIBLE area below
        // the frozen header, not in the raw box.
        const thead = inner.querySelector('thead');
        const headH = thead ? thead.getBoundingClientRect().height : 0;
        const visibleTop = ir.top + headH;
        const visibleCenter = visibleTop + (ir.bottom - visibleTop) / 2;
        const elCenter = er.top + er.height / 2;
        inner.scrollTop += (elCenter - visibleCenter);
      }
      // Now align the row with the window viewport centre (page-level scroll).
      const er2 = el.getBoundingClientRect();
      const targetY = er2.top + er2.height / 2;
      window.scrollBy({
        top: targetY - window.innerHeight / 2,
        behavior: 'smooth',
      });
    }));
  }
  window.addEventListener('hashchange', centerHash);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', centerHash);
  } else {
    centerHash();
  }

  // ---- CROSS-HIGHLIGHT FOR ALL <table> ELEMENTS ----
  // On hover of any <td>, light up the entire row + the entire column the
  // cell sits in (visual "+" through the table, like Liquipedia crosstable).
  // Attaches to every <table> on the page after DOM ready.
  function wireCrossHover(table) {
    if (table.dataset.crossWired === '1') return;
    // Dynamics matrices can be 350 rows x 116 patch columns. Column cross-hover
    // mutates one cell per row on every mouse move, which is cheap for normal
    // tables but makes items_dyn heavy when "Hide old" is off. Row click,
    // dyn-cell hover tooltips, sorting and filters stay intact without it.
    if (table.classList.contains('heroes-dyn-table')) return;
    table.dataset.crossWired = '1';
    let activeRow = null;
    const colCells = [];
    const clear = () => {
      if (activeRow) {
        activeRow.classList.remove('cross-row');
        activeRow = null;
      }
      colCells.forEach(c => c.classList.remove('cross-col'));
      colCells.length = 0;
    };
    table.addEventListener('mouseover', e => {
      // Only TD cells trigger / receive the cross-highlight. Hovering a TH
      // (header) shouldn't sweep the row beneath it and shouldn't paint
      // the column band — the heatmap on data cells is the only visual
      // intent there.
      const cell = e.target.closest('td');
      if (!cell || !table.contains(cell)) return;
      const row = cell.parentElement;
      if (row.tagName !== 'TR') return;
      const idx = cell.cellIndex;
      if (row === activeRow &&
          colCells.length && colCells[0].cellIndex === idx) return;
      clear();
      activeRow = row;
      row.classList.add('cross-row');
      // Walk only TBODY rows — TH cells in thead never get cross-col.
      table.querySelectorAll('tbody tr').forEach(tr => {
        const c = tr.cells && tr.cells[idx];
        if (c) {
          c.classList.add('cross-col');
          colCells.push(c);
        }
      });
    });
    table.addEventListener('mouseleave', clear);
  }
  function wireAllTables() {
    document.querySelectorAll('table').forEach(wireCrossHover);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wireAllTables);
  } else {
    wireAllTables();
  }
})();

// ---- SITE NAV HEIGHT → CSS variable (used by every sticky layer below) ----
// The toolbar / view / blurb on table pages all scroll away with the page;
// only the site nav + table category headers stay pinned. The thead pins
// directly under the nav, so all we need to publish is its live height.
(function() {
  const nav = document.querySelector('nav.top-nav');
  if (!nav) return;
  function recalc() {
    const navH = nav.getBoundingClientRect().height;
    const root = document.documentElement.style;
    root.setProperty('--site-nav-h', navH + 'px');
    root.setProperty('--mr-thead-top', navH + 'px');
  }
  recalc();
  window.addEventListener('resize', recalc, { passive: true });
  window.addEventListener('load', recalc);
})();

// ---- MANA REGEN TABLE: simple sortable ----
// Plain sort by data-sort attribute on each <td>. No row grouping / level
// collapse / ability merging — the table is flat, so the existing creeps
// sort would over-engineer it.
(function() {
  const tables = document.querySelectorAll('.mr-table');
  tables.forEach(table => {
    const tbody = table.querySelector('tbody');
    const headers = [...table.querySelectorAll('thead th.sortable')];
    if (!tbody || !headers.length) return;

    function cellVal(tr, colIdx) {
      const td = tr.children[colIdx];
      if (!td) return null;
      if (td.dataset.sort !== undefined && td.dataset.sort !== '') {
        const n = parseFloat(td.dataset.sort);
        return isNaN(n) ? td.dataset.sort.toLowerCase() : n;
      }
      const t = td.textContent.trim();
      if (!t) return null;
      const m = t.replace(',', '.').match(/-?\d+(?:\.\d+)?/);
      return m ? parseFloat(m[0]) : t.toLowerCase();
    }

    // Snapshot the server-rendered order so the neutral state can restore it.
    const originalOrder = [...tbody.querySelectorAll('tr')];
    // The default-sorted column is marked .sort-desc in the markup, so the
    // 3-state cycle starts already on that column at "descending".
    let sortCol = headers.findIndex(th =>
      th.classList.contains('sort-asc') || th.classList.contains('sort-desc'));
    if (sortCol === -1) sortCol = null;
    // sortState: 0 = neutral, 1 = descending, 2 = ascending.
    let sortState = sortCol !== null
      ? (headers[sortCol].classList.contains('sort-asc') ? 2 : 1)
      : 0;

    function sortBy(colIdx, dir) {
      const rows = [...tbody.querySelectorAll('tr')];
      rows.sort((a, b) => {
        const va = cellVal(a, colIdx);
        const vb = cellVal(b, colIdx);
        if (va == null && vb == null) return 0;
        if (va == null) return 1;          // empties sink
        if (vb == null) return -1;
        if (typeof va === 'number' && typeof vb === 'number') {
          return dir === 'asc' ? va - vb : vb - va;
        }
        const sa = String(va), sb = String(vb);
        return dir === 'asc' ? sa.localeCompare(sb) : sb.localeCompare(sa);
      });
      rows.forEach(r => tbody.appendChild(r));
    }

    headers.forEach((th, i) => {
      th.addEventListener('click', () => {
        // 3-state cycle per header: neutral → descending → ascending → neutral.
        if (sortCol === i) sortState = (sortState + 1) % 3;
        else { sortCol = i; sortState = 1; }   // first click = descending
        headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
        if (sortState === 0) {
          // Neutral — restore the original server-rendered order.
          sortCol = null;
          originalOrder.forEach(r => tbody.appendChild(r));
        } else {
          const dir = sortState === 1 ? 'desc' : 'asc';
          th.classList.add(dir === 'asc' ? 'sort-asc' : 'sort-desc');
          sortBy(i, dir);
        }
        // Heatmap follows the new row order / visible set.
        window.dispatchEvent(new CustomEvent('mr:filter-changed'));
      });
    });
  });
})();

// ---- MANA ITEMS: "Hide active" toggle ----
// Hides every <tr.mr-active-row> when checked. Heatmap recomputes via the
// shared `mr:filter-changed` channel so column gradients reflect the
// currently-visible row set.
(function() {
  const toggle = document.getElementById('mr-hide-active');
  if (!toggle) return;
  const apply = () => {
    document.querySelectorAll('.mr-active-row').forEach(tr => {
      tr.classList.toggle('mr-hide-active', toggle.checked);
    });
    window.dispatchEvent(new CustomEvent('mr:filter-changed'));
  };
  toggle.addEventListener('change', apply);
})();

// ---- MANA ITEMS: per-column conditional formatting ----
// For every column whose <th data-direction> is set, scan all visible cells
// and paint a faint pastel gradient — green at the "good" end, red at the
// "bad" end. Pure visual aid; doesn't alter values or sort order.
(function() {
  const table = document.querySelector('.mr-table');
  if (!table) return;
  const headRow = table.querySelector('thead tr.col-row') || table.querySelector('thead tr');
  const headers = headRow ? [...headRow.querySelectorAll('th')] : [];

  function applyHeatmap() {
    // Respect the on-page Heatmap switch — when off, all cells stay flat.
    // (The toggle IIFE separately strips any inline backgrounds we set.)
    const toggle = document.getElementById('mr-heatmap-toggle');
    if (toggle && !toggle.checked) return;
    const rows = [...table.querySelectorAll('tbody tr')];
    headers.forEach((th, colIdx) => {
      const direction = th.dataset.direction;
      if (!direction) return;
      // Gather numeric data-sort values for visible non-dash cells. Rows
      // hidden by the price filter (.mr-filtered-out) are also excluded so
      // colours always reflect the current visible set.
      const cells = [];
      rows.forEach(tr => {
        if (tr.hasAttribute('hidden')) return;
        if (tr.classList.contains('mr-filtered-out')) return;
        if (tr.classList.contains('mr-search-out')) return;
        if (tr.classList.contains('mr-attack-out')) return;
        if (tr.classList.contains('mr-hide-active')) return;
        const td = tr.children[colIdx];
        if (!td) return;
        td.style.backgroundColor = '';        // reset previous paint
        if (td.querySelector('.ua-dash')) return;
        const v = parseFloat(td.dataset.sort);
        if (isNaN(v) || v === 0) return;
        cells.push({ td, v });
      });
      if (cells.length < 2) return;
      // Rank-percentile mapping: each cell's colour is decided by its rank
      // within the column, not its raw value. Eliminates the previous problem
      // where a single outlier (Dagon 5's 25.5k cost-per-regen) compressed
      // every other value into the same green band — now mid-tier rows get
      // mid-tier colours regardless of how far the worst outlier sits.
      // Rank over UNIQUE values so ties share one colour — otherwise a
      // column of identical numbers (hero Vision: 1800 everywhere) painted
      // a meaningless green→red gradient purely by row order.
      const uniq = [...new Set(cells.map(c => c.v))].sort((a, b) => a - b);
      if (uniq.length < 2) {
        cells.forEach(c => { c.td.style.backgroundColor = ''; });
        return;
      }
      const rankMap = new Map(uniq.map((v, i) => [v, i]));
      const last = uniq.length - 1;
      cells.forEach(c => {
        let t = rankMap.get(c.v) / last;   // [0, 1] by unique-value rank
        if (direction === 'lower') t = 1 - t;
        // 0 → red, 60 → amber, 120 → green. Keep saturation + alpha
        // moderate so cross-hover darkening still reads on top.
        const hue = Math.round(t * 120);
        c.td.style.backgroundColor =
          `hsla(${hue}, 60%, 50%, 0.22)`;
      });
    });
  }
  applyHeatmap();
  // Filter / sort events from sibling IIFEs trigger a recompute.
  window.addEventListener('mr:filter-changed', applyHeatmap);
})();

// ---- MANA ITEMS: click row to highlight (yellow). Click again to deselect. ----
(function() {
  const table = document.querySelector('.mr-table');
  if (!table) return;
  table.addEventListener('click', e => {
    const tr = e.target.closest('tbody tr');
    if (!tr || !table.contains(tr)) return;
    const was = tr.classList.contains('mr-row-selected');
    table.querySelectorAll('tr.mr-row-selected').forEach(r =>
      r.classList.remove('mr-row-selected'));
    if (!was) tr.classList.add('mr-row-selected');
  });
})();

// ---- MANA ITEMS: Price min/max filter ----
(function() {
  const table = document.querySelector('.mr-table');
  if (!table) return;
  const minIn = document.getElementById('mr-price-min');
  const maxIn = document.getElementById('mr-price-max');
  const clear = document.getElementById('mr-price-clear');
  if (!minIn || !maxIn) return;
  // Find the Price column index from the header (data-col="cost").
  const headers = [...table.querySelectorAll('thead th')];
  const priceIdx = headers.findIndex(th => th.dataset.col === 'cost');
  if (priceIdx < 0) return;

  function applyFilter() {
    const lo = parseFloat(minIn.value);
    const hi = parseFloat(maxIn.value);
    const hasLo = !isNaN(lo);
    const hasHi = !isNaN(hi);
    // Show the X only when at least one bound is set — otherwise the
    // combo widget reads as a simple "Price from–to" placeholder pair.
    clear.hidden = !(hasLo || hasHi);
    table.querySelectorAll('tbody tr').forEach(tr => {
      const td = tr.children[priceIdx];
      const v = td ? parseFloat(td.dataset.sort) : NaN;
      let keep = true;
      if (!isNaN(v)) {
        if (hasLo && v < lo) keep = false;
        if (hasHi && v > hi) keep = false;
      }
      tr.classList.toggle('mr-filtered-out', !keep);
    });
    // Heatmap re-applies over the new visible set.
    window.dispatchEvent(new CustomEvent('mr:filter-changed'));
  }
  minIn.addEventListener('input', applyFilter);
  maxIn.addEventListener('input', applyFilter);
  clear.addEventListener('click', () => {
    minIn.value = '';
    maxIn.value = '';
    applyFilter();
  });
})();

// ---- MANA ITEMS: name search ----
// Independent of the price/hide-active filters (each uses its own display:none
// class, so any one hiding a row wins). Comma-separated, partial, like the
// dynamics search. Re-fires mr:filter-changed so the heatmap recomputes.
(function() {
  const table = document.querySelector('.mr-table');
  const search = document.getElementById('mr-search');
  if (!table || !search) return;
  const rows = [...table.querySelectorAll('tbody tr')];
  const apply = () => {
    const terms = search.value.toLowerCase().split(',').map(s => s.trim()).filter(Boolean);
    rows.forEach(tr => {
      const name = (tr.querySelector('.mr-name-text')?.textContent || '').toLowerCase();
      const hit = !terms.length || terms.some(t => name.includes(t));
      tr.classList.toggle('mr-search-out', !hit);
    });
    window.dispatchEvent(new CustomEvent('mr:filter-changed'));
  };
  search.addEventListener('input', apply);
})();

// ---- HERO STATS (heroes_stats.html): Base / Starting / Expanded view ----
// Reuses the mr-table front-end (sort / heatmap / search / stat-hist tooltips).
// Three modes via the View dropdown (mirrors Neutral Creeps):
//   base     — bare values from the game files
//   starting — DEFAULT, level-1 values with attribute bonuses
//   expanded — Starting + extra columns (.hs-extra)
// Some columns (HP, MP, regens, armor, magic resist, damage, attack speed)
// have DIFFERENT values per mode. The build emits the Starting value as the
// default cell content; cells that differ from Base carry data-base-sort /
// data-base-html / data-base-hist. We stash the Starting values on first
// load, then swap on every mode change. data-hist drives the hover tooltip
// (existing stat-hist code reads it live), data-sort drives sorting.
(function() {
  const viewSel = document.getElementById('hs-view-mode');
  if (!viewSel) return;
  const table = document.querySelector('.mr-table');
  if (!table) return;
  const levelInput = document.getElementById('hs-level-input');
  const plus2Toggle = document.getElementById('hs-plus2-toggle');
  const innatesToggle = document.getElementById('hs-innates-toggle');
  const attackBtns = [...document.querySelectorAll('.hs-attack-filter')];
  const attrBtns = [...document.querySelectorAll('.hs-attr-filter')];
  const cells = [...table.querySelectorAll('tbody td[data-col]')];
  let attackFilter = '';
  let attrFilter = '';
  const PLUS2_LEVELS = [15, 16, 17, 19, 20, 21, 22];

  const clampLevel = () => {
    if (!levelInput) return 1;
    const raw = parseInt(levelInput.value, 10);
    const next = Math.max(1, Math.min(30, Number.isFinite(raw) ? raw : 1));
    if (String(next) !== levelInput.value) levelInput.value = String(next);
    return next;
  };

  const num = v => {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  };
  const g = v => {
    const s = Number(v).toFixed(2).replace(/\.?0+$/, '');
    return s || '0';
  };
  const g1 = v => {
    const s = Number(v).toFixed(1).replace(/\.?0+$/, '');
    return s || '0';
  };
  const g0 = v => String(Math.round(Number(v) || 0));
  const pct = v => g(v) + '%';
  const pct1 = v => g1(v) + '%';
  const regen = v => Math.abs(Number(v) || 0) < 1e-9 ? '0' : Number(v).toFixed(2);
  const armorFactor = a => (0.06 * a) / (1 + 0.06 * Math.abs(a));
  const armorPct = a => Math.round(armorFactor(a) * 100);
  const ehpPhys = (hp, armor) => Math.round(hp / Math.max(0.01, 1 - armorFactor(armor)));
  const ehpMag = (hp, mr) => Math.round(hp / Math.max(0.01, 1 - mr / 100));
  const plus2CountAt = level => PLUS2_LEVELS.filter(l => l <= level).length;
  const techiesPoolPctAt = level => {
    const lvl = Math.max(1, Number(level) || 1);
    return 0.001 + lvl * 0.0001;
  };
  const attrsAt = (s, level, includePlus2) => {
    const bonus = includePlus2 ? plus2CountAt(level) * 2 : 0;
    // Ogre Magi has 0 base Intelligence and cannot gain Int from levels OR from
    // the +2-all-stats level-ups (his innate replaces Int scaling with Strength-
    // based mana) — so the +2 bonus only feeds his Str and Agi, never Int.
    const intBonus = s.slug === 'ogre_magi' ? 0 : bonus;
    return {
      str: num(s.str) + (level - 1) * num(s.strGain) + bonus,
      agi: num(s.agi) + (level - 1) * num(s.agiGain) + bonus,
      int: num(s.int) + (level - 1) * num(s.intGain) + intBonus,
    };
  };
  const wholeAttrs = a => ({
    str: Math.floor(a.str),
    agi: Math.floor(a.agi),
    int: Math.floor(a.int),
  });
  const rowStats = tr => {
    if (!tr._hsStats) {
      try { tr._hsStats = JSON.parse(tr.dataset.hsStats || '{}'); }
      catch { tr._hsStats = {}; }
    }
    return tr._hsStats;
  };
  const innate = (key, s, a, level) => {
    if (!innatesToggle?.checked) return 0;
    if (s.slug === 'morphling') {
      if (key === 'range') return a.agi * 0.25;
      if (key === 'ms') return a.agi * 0.15;
    }
    if (s.slug === 'void_spirit') {
      if (key === 'hpr') return 0.1 * a.str * 0.30;
      if (key === 'mpr') return 0.05 * a.int * 0.30;
      if (key === 'aspd') return a.agi * 0.30;
    }
    if (s.slug === 'centaur' && key === 'ms') return a.str * 0.40;
    // Dragon Knight — Dragon Blood (innate): bonus HP regen AND armor, both
    // 2 + 0.5 per hero level.
    if (s.slug === 'dragon_knight' && (key === 'hpr' || key === 'armor')) {
      return 2 + 0.5 * (level || 1);
    }
    // Lifestealer — innate bonus Attack Speed, 4 per hero level.
    if (s.slug === 'life_stealer' && key === 'aspd') return 4 * (level || 1);
    // Luna — Lunar Blessing (innate): bonus Night Vision, 225 + 25 per level.
    if (s.slug === 'luna' && key === 'nvision') return 225 + 25 * (level || 1);
    // Razor — Unstable Current (innate, 7.41a+): +1 Move Speed per hero level.
    if (s.slug === 'razor' && key === 'ms') {
      return patchGe(hsTablePatch, '7.41a') ? (level || 1) : 0;
    }
    // Dark Seer — Quick Wit (innate): +Attack Speed per point of Intelligence.
    // KV int_to_atkspd: 0.5 @ 7.36..7.37e → 1.0 @ 7.38+.
    if (s.slug === 'dark_seer' && key === 'aspd') {
      const f = patchGe(hsTablePatch, '7.38') ? 1.0 : 0.5;
      return a.int * f;
    }
    // Keeper of the Light — Bright Speed (innate, 7.41a+): +1 MS per N Int.
    // KV intelligence_per_speed: 2.5 @ 7.41a..7.41b → 3.0 @ 7.41c+.
    if (s.slug === 'keeper_of_the_light' && key === 'ms') {
      if (!patchGe(hsTablePatch, '7.41a')) return 0;
      const N = patchGe(hsTablePatch, '7.41c') ? 3.0 : 2.5;
      return a.int / N;
    }
    // Beastmaster — Inner Beast (innate, 7.41a+): +(7 + 3·level) Attack Speed
    // per unit controlled including the hero himself — we count just the hero.
    if (s.slug === 'beastmaster' && key === 'aspd') {
      return patchGe(hsTablePatch, '7.41a') ? (7 + 3 * (level || 1)) : 0;
    }
    return 0;
  };
  // Death Prophet — Witchcraft (innate): multiplicative +(base+per_level·L)% to
  // Move Speed. KV value/hero_levelup: 0.75+0.75·L (7.40..7.40c) → 0.5+0.75·L
  // (7.41a+). Returns the FACTOR to multiply move speed by (1 + pct/100), or 1
  // when the toggle is off / hero doesn't match / patch is too old.
  const dpWitchcraftMsMult = (s, level) => {
    if (!innatesToggle?.checked || s.slug !== 'death_prophet') return 1;
    if (!patchGe(hsTablePatch, '7.40')) return 1;
    const base = patchGe(hsTablePatch, '7.41a') ? 0.5 : 0.75;
    return 1 + (base + 0.75 * (level || 1)) / 100;
  };
  const axeStrBonus = (s, a) => {
    if (!innatesToggle?.checked || s.slug !== 'axe') return 0;
    const armor = num(s.armor) + a.agi / 6;
    return armor * 0.5;
  };
  // Drow — innate bonus Agility = 10% + 1% per level of her CURRENT Agility.
  // Self-referential (off her already-scaled agi), folded into the agi attr so
  // every agi-derived stat (damage, armor, attack speed) picks it up.
  const drowAgiBonus = (s, rawA, level) => {
    if (!innatesToggle?.checked || s.slug !== 'drow_ranger') return 0;
    return rawA.agi * (0.10 + 0.01 * level);
  };
  // Extra flat/attribute bonus DAMAGE from innates (added on top of the primary-
  // attribute damage). Sven: 0.08 + 0.02 per level, per point of Strength.
  // Luna: 2 flat damage per level.
  const innateDmg = (s, a, level, startHp) => {
    if (!innatesToggle?.checked) return 0;
    if (s.slug === 'sven') return a.str * (0.08 + 0.02 * level);
    if (s.slug === 'luna') return 2 * level;
    // Ursa — Earthshock Maul (innate): bonus damage = % of CURRENT HP. KV:
    // 1.5 @ 7.36..7.37a → leveled 1.2/1.3/1.4/1.5 @ 7.37b..7.39c → 1.25 @ 7.39d+.
    // We use the flat current-patch value (taking max-rank for the leveled
    // window) — heroes_stats doesn't model skill point distribution.
    if (s.slug === 'ursa') {
      const pct = patchGe(hsTablePatch, '7.39d') ? 1.25
                : patchGe(hsTablePatch, '7.37b') ? 1.5
                : patchGe(hsTablePatch, '7.36') ? 1.5
                : 0;
      return (startHp || 0) * pct / 100;
    }
    return 0;
  };
  // Medusa — Mana Shield. The ability absorbs 98% of incoming damage BEFORE
  // armor / magic resistance, at `damage_per_mana` damage per mana point. Since
  // it soaks raw pre-mitigation damage, every mana point adds a FLAT, armor/
  // resist-independent 0.98·dpm to BOTH physical and magical EHP.
  //
  // dpm has changed across patches (values taken from KV files, see
  // data/stats/<patch>/heroes/npc_dota_hero_medusa.txt):
  //   ≤ 7.36c — leveled ability: 2/2.4/2.8/3.2/3.6 (assumes max rank at L30+)
  //   7.37    — 2.4   (became innate with 7.36 hero-rework cycle)
  //   7.38..7.39d — 2.2
  //   7.39e..7.40c — 2.0
  //   7.41a+  — 2 + 0.1·level   (current; Liquipedia EHP: 2.058/mp L1 → 4.9/mp L30)
  // We compare patch strings via the helpers below (same as `_ge` in the
  // Python side). absorption_pct = 98 across every version checked.
  const hsTablePatch = (table.dataset.patch || '7.41d');
  const patchKey = v => {
    const m = String(v || '').match(/^7\.(\d+)([a-z]?)/);
    if (!m) return [0, 0];
    return [parseInt(m[1], 10), m[2] ? m[2].charCodeAt(0) - 96 : 0];
  };
  const patchGe = (a, b) => {
    const [x1, y1] = patchKey(a), [x2, y2] = patchKey(b);
    return x1 !== x2 ? x1 > x2 : y1 >= y2;
  };
  const medusaDpm = (level) => {
    const v = hsTablePatch;
    if (patchGe(v, '7.41a')) return 2 + 0.1 * level;
    if (patchGe(v, '7.39e')) return 2.0;
    if (patchGe(v, '7.38'))  return 2.2;
    if (patchGe(v, '7.37'))  return 2.4;
    // ≤7.36c: skill with ranks 1-4 → assume max-ranked at hero level ≥ 7.
    const ranks = [2, 2, 2.4, 2.8, 3.2, 3.6];
    return ranks[Math.min(5, Math.max(0, Math.floor((level + 1) / 2)))];
  };
  const manaShieldEhp = (s, mana, level) => {
    if (!innatesToggle?.checked || s.slug !== 'medusa') return 0;
    return mana * 0.98 * medusaDpm(level);
  };
  const primaryDmg = (s, a) => {
    if (s.attr === 'str') return Math.floor(a.str);
    if (s.attr === 'agi') return Math.floor(a.agi);
    if (s.attr === 'int') return Math.floor(a.int);
    const mult = s.slug === 'void_spirit' ? 0.45 * 1.15 : 0.45;
    return Math.floor((a.str + a.agi + a.int) * mult);
  };
  const valueFor = (s, col, mode, level) => {
    const effectiveLevel = mode === 'base' ? 1 : level;
    const usePlus2 = mode !== 'base' && !!plus2Toggle?.checked;
    const rawAttrs = attrsAt(s, effectiveLevel, usePlus2);
    const a = mode === 'base' ? rawAttrs : {
      str: rawAttrs.str + axeStrBonus(s, rawAttrs),
      agi: rawAttrs.agi + drowAgiBonus(s, rawAttrs, effectiveLevel),
      int: rawAttrs.int,
    };
    const wa = wholeAttrs(a);
    const baseAs = num(s.bas);
    const startAs = baseAs + a.agi + innate('aspd', s, a, effectiveLevel);
    const startArmor = num(s.armor) + a.agi / 6 + innate('armor', s, a, effectiveLevel);
    const startMr = num(s.mr) + a.int * 0.1;
    const rawHp = num(s.hp);
    const startHp = Math.round(rawHp + wa.str * 22);
    // bonusDmg references startHp (Ursa Maul = % of current HP), so compute it
    // AFTER startHp. primaryDmg = the universal attribute-to-damage; innateDmg
    // adds Sven/Luna/Ursa on top.
    const bonusDmg = primaryDmg(s, wa) + innateDmg(s, wa, effectiveLevel, startHp);
    const rawMana = s.slug === 'huskar' ? 0 : num(s.mp);
    const rawManaRegen = s.slug === 'huskar' ? 0 : num(s.mpr);
    const startMana = (() => {
      if (s.slug === 'huskar') return 0;
      if (s.slug === 'ogre_magi') return Math.round(num(s.mp) + wa.str * 6 + wa.int * 12);
      return Math.round(num(s.mp) + wa.int * 12);
    })();
    const startManaRegen = (() => {
      if (s.slug === 'huskar') return 0;
      const techiesPoolPct = techiesPoolPctAt(effectiveLevel); // 0.10% + 0.01% per level
      const techiesPoolRegen = (innatesToggle?.checked && s.slug === 'techies')
        ? startMana * techiesPoolPct
        : 0;
      if (s.slug === 'ogre_magi') return num(s.mpr) + a.str * 0.02 + a.int * 0.05;
      return num(s.mpr) + wa.int * 0.05 + innate('mpr', s, a, effectiveLevel) + techiesPoolRegen;
    })();
    const start = mode !== 'base';
    switch (col) {
      case 'hp': return [start ? startHp : rawHp, g0];
      case 'ehp_phys': {
        const shield = start ? manaShieldEhp(s, startMana, effectiveLevel) : 0;
        return [ehpPhys(start ? startHp : rawHp, start ? startArmor : num(s.armor)) + shield, g0];
      }
      case 'ehp_mag': {
        const shield = start ? manaShieldEhp(s, startMana, effectiveLevel) : 0;
        return [ehpMag(start ? startHp : rawHp, start ? startMr : num(s.mr)) + shield, g0];
      }
      case 'hpr': return [start ? num(s.hpr) + wa.str * 0.1 + innate('hpr', s, a, effectiveLevel) : num(s.hpr), regen];
      case 'mp': return [start ? startMana : rawMana, g0];
      case 'mpr': return [start ? startManaRegen : rawManaRegen, regen];
      case 'str': return [a.str, g];
      case 'str_gain': return [num(s.strGain), g];
      case 'agi': return [a.agi, g];
      case 'agi_gain': return [num(s.agiGain), g];
      case 'int': return [a.int, g];
      case 'int_gain': return [num(s.intGain), g];
      case 'gper': return [num(s.strGain) + num(s.agiGain) + num(s.intGain), g1];
      case 'armor': return [start ? startArmor : num(s.armor), g1];
      case 'armor_pct': return [armorPct(start ? startArmor : num(s.armor)), pct];
      case 'mr': return [start ? startMr : num(s.mr), pct1];
      case 'dmg': {
        // Main Damage column = single AVERAGE value (min/max live in Expanded).
        const min = num(s.dmin) + (start ? bonusDmg : 0);
        const max = num(s.dmax) + (start ? bonusDmg : 0);
        return [(min + max) / 2, g0];
      }
      case 'dmin': return [num(s.dmin) + (start ? bonusDmg : 0), g0];
      case 'dmax': return [num(s.dmax) + (start ? bonusDmg : 0), g0];
      case 'aspd': return [start ? startAs : baseAs, g0];
      case 't_per_attack': {
        const ats = start ? startAs : baseAs || 100;
        return [ats ? num(s.bat) * 100 / ats : num(s.bat), g];
      }
      case 'bat': return [num(s.bat), g];
      case 'range': return [start ? num(s.range) + innate('range', s, a, effectiveLevel) : num(s.range), g0];
      case 'proj': return [num(s.proj), g0];
      case 'dvision': return [num(s.dvision), g0];
      case 'nvision': return [start ? num(s.nvision) + innate('nvision', s, a, effectiveLevel) : num(s.nvision), g0];
      case 'ms': {
        if (!start) return [num(s.ms), g0];
        // Death Prophet Witchcraft applies a multiplicative % bonus to MS;
        // Razor / KotL add flat bonuses via innate(). Apply mult LAST so the
        // mult scales the full base+flat-innate stack.
        const flat = num(s.ms) + innate('ms', s, a, effectiveLevel);
        return [flat * dpWitchcraftMsMult(s, effectiveLevel), g0];
      }
      case 'turn': return [num(s.turn), g];
      case 'collision': return [num(s.collision), g0];
      case 'bound': return [num(s.bound), g0];
      default: return [parseFloat(s[col]) || 0, g];
    }
  };

  // Stash Starting values once — those are the cell's INITIAL data.
  cells.forEach(td => {
    if (!td.dataset.startSort) td.dataset.startSort = td.dataset.sort;
    if (!td.dataset.startHist) td.dataset.startHist = td.dataset.hist || '';
    if (!td.dataset.startHtml) td.dataset.startHtml = td.innerHTML;
  });
  function recomputeCats() {
    table.querySelectorAll('thead tr.cat-row th.cat-head[data-cat]').forEach(head => {
      let span = 0;
      table.querySelectorAll('thead tr.col-row th[data-cat="' + head.dataset.cat + '"]')
        .forEach(th => { if (th.offsetParent !== null) span += th.colSpan || 1; });
      head.colSpan = span || 1;
      head.style.display = span ? '' : 'none';
    });
  }
  const apply = () => {
    const mode = viewSel.value;
    const level = clampLevel();
    if (levelInput) {
      const baseMode = mode === 'base';
      levelInput.disabled = baseMode;
      levelInput.title = baseMode
        ? 'Base view uses raw level-1 game-file values'
        : 'Hero level';
    }
    table.classList.remove('hs-mode-base', 'hs-mode-starting', 'hs-mode-expanded');
    table.classList.add('hs-mode-' + mode);
    cells.forEach(td => {
      const tr = td.closest('tr[data-hs-stats]');
      const col = td.dataset.col;
      const stats = tr ? rowStats(tr) : {};
      const [sortVal, formatter] = valueFor(stats, col, mode, level);
      const attackType = tr?.dataset.attackType || '';
      const html = col === 'range' && attackType
        ? `<span class="atk-num">${formatter(sortVal)}</span>` +
          `<span class="atk-badge atk-${attackType}" title="${attackType === 'ranged' ? 'Ranged' : 'Melee'}">` +
          `<img src="icons/ui/atk_${attackType}.png" alt="${attackType === 'ranged' ? 'Ranged' : 'Melee'}" ` +
          `title="${attackType === 'ranged' ? 'Ranged' : 'Melee'}" loading="lazy"></span>`
        : formatter(sortVal);
      if (mode === 'base') {
        td.dataset.sort = sortVal;
        td.dataset.hist = td.dataset.baseHist;
        td.innerHTML = html;
      } else {
        td.dataset.sort = sortVal;
        td.dataset.hist = td.dataset.startHist;
        td.innerHTML = html;
      }
      if (col === 'hpr' || col === 'mpr') {
        td.classList.toggle('regen-zero', Math.abs(Number(sortVal) || 0) < 1e-9);
      }
      td.classList.toggle('has-history', !!td.dataset.hist);
    });
    table.querySelectorAll('tbody tr[data-hs-stats]').forEach(tr => {
      const stats = rowStats(tr);
      const icon = tr.querySelector('.hs-innate-mini');
      if (!icon) return;
      const show = !!innatesToggle?.checked && !!stats.hasStatInnate && mode !== 'base';
      icon.classList.toggle('is-hidden', !show);
    });
    recomputeCats();
    window.dispatchEvent(new CustomEvent('mr:filter-changed'));  // heatmap re-scan
  };

  const applyHeroFilters = () => {
    table.querySelectorAll('tbody tr[data-hs-stats]').forEach(tr => {
      const hideAttack = !!attackFilter && tr.dataset.attackType !== attackFilter;
      const hideAttr = !!attrFilter && tr.dataset.attrType !== attrFilter;
      tr.classList.toggle('mr-attack-out', hideAttack || hideAttr);
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
    window.dispatchEvent(new CustomEvent('mr:filter-changed'));
  };

  viewSel.addEventListener('change', apply);
  if (levelInput) {
    levelInput.addEventListener('input', apply);
    levelInput.addEventListener('change', apply);
  }
  if (plus2Toggle) plus2Toggle.addEventListener('change', apply);
  if (innatesToggle) innatesToggle.addEventListener('change', apply);
  attackBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const next = btn.dataset.attackFilter || '';
      attackFilter = attackFilter === next ? '' : next;
      applyHeroFilters();
    });
  });
  attrBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const next = btn.dataset.attrFilter || '';
      attrFilter = attrFilter === next ? '' : next;
      applyHeroFilters();
    });
  });
  window.addEventListener('resize', recomputeCats, { passive: true });
  apply();
  applyHeroFilters();
})();

// ---- HERO LAB: two-side hero + item calculator ----
(function() {
  const root = document.querySelector('.hero-lab');
  const dataEl = document.getElementById('hero-lab-data');
  if (!root || !dataEl) return;
  let data;
  try { data = JSON.parse(dataEl.textContent || '{}'); }
  catch { return; }
  const heroes = data.heroes || [];
  const items = data.items || [];
  if (!heroes.length) return;

  const PLUS2_LEVELS = [15, 16, 17, 19, 20, 21, 22];
  const ATTR_META = {
    str: { label: 'Strength', short: 'STR', icon: 'icons/strength.webp', color: '#cf6d5e' },
    agi: { label: 'Agility', short: 'AGI', icon: 'icons/agility.webp', color: '#63c774' },
    int: { label: 'Intelligence', short: 'INT', icon: 'icons/intelligence.webp', color: '#63b8e6' },
    uni: { label: 'Universal', short: 'UNI', icon: 'icons/universal.webp', color: '#e1b85b' },
  };
  const BASIC_SECTIONS = ['Consumables', 'Attributes', 'Equipment', 'Miscellaneous', 'Secret Shop'];
  const UPGRADE_SECTIONS = ['Accessories', 'Support', 'Magical', 'Armor', 'Weapons', 'Armaments'];
  const C = {
    hpStr: 22, hprStr: 0.1, mpInt: 12, mprInt: 0.05,
    armorAgi: 1 / 6, mrInt: 0.1, asAgi: 1, uniDmg: 0.45,
  };
  const METRICS = [
    ['hp', 'HP'], ['mp', 'MP'], ['hpr', 'HP/sec'], ['mpr', 'MP/sec'],
    ['str', 'STR'], ['agi', 'AGI'], ['int', 'INT'],
    ['armor', 'Armor'], ['armorPct', 'Armor %'], ['mr', 'Mag. resist'],
    ['evasion', 'Evasion'], ['dmg', 'Damage'], ['dmin', 'Dmg min'],
    ['dmax', 'Dmg max'], ['aspd', 'Attack speed'], ['tHit', 'Time to hit'],
    ['ms', 'Movespeed'], ['range', 'Attack range'],
    ['ehpPhys', 'EHP phys'], ['ehpMag', 'EHP mag'],
  ];
  const CUSTOM = [
    ['hp', 'HP'], ['mp', 'MP'], ['hpr', 'HP/sec'], ['mpr', 'MP/sec'],
    ['armor', 'Armor'], ['mr', 'Magic resist'], ['evasion', 'Evasion'],
  ];
  const byHero = new Map(heroes.map(h => [h.id, h]));
  const byItem = new Map(items.map(i => [i.id, i]));
  const heroGroups = {
    str: heroes.filter(h => h.stats?.attr === 'str'),
    agi: heroes.filter(h => h.stats?.attr === 'agi'),
    int: heroes.filter(h => h.stats?.attr === 'int'),
    uni: heroes.filter(h => h.stats?.attr === 'uni'),
  };
  const itemGroups = {
    basics: BASIC_SECTIONS.map(name => [name, items.filter(i => i.class === 'regular' && i.category === name)]),
    upgrades: UPGRADE_SECTIONS.map(name => [name, items.filter(i => i.class === 'regular' && i.category === name)]),
    neutrals: {
      tiers: [0, 1, 2, 3, 4].map(tier => [tier, items.filter(i => i.class === 'neutral' && i.tier === tier)]),
      enchants: items.filter(i => i.class === 'enchant'),
    },
  };
  const overlay = document.createElement('div');
  overlay.className = 'hl-overlay';
  overlay.hidden = true;
  document.body.appendChild(overlay);
  let activePicker = null;

  const fmt = (v, d = 0) => {
    const n = Number(v) || 0;
    return d ? n.toFixed(d).replace(/\.?0+$/, '') : String(Math.round(n));
  };
  const fmtMetric = (key, v) => {
    if (key === 'hpr' || key === 'mpr' || key === 'tHit') return Number(v || 0).toFixed(2);
    if (key === 'armor') return fmt(v, 1);
    if (key === 'mr' || key === 'evasion' || key === 'armorPct') return fmt(v, 1) + '%';
    return fmt(v);
  };
  const armorFactor = a => (0.06 * a) / (1 + 0.06 * Math.abs(a));
  const plus2At = lvl => PLUS2_LEVELS.filter(x => x <= lvl).length * 2;
  const combinePct = vals => (1 - vals.reduce((acc, v) => acc * (1 - Math.max(0, v) / 100), 1)) * 100;
  const iconHtml = (src, name, cls) => `<img class="${cls}" src="${src}" alt="${name}" loading="lazy">`;
  const quickFmt = v => Number(v || 0).toFixed(2).replace(/\.00$/, '');
  const tierLabel = tier => `Tier ${Number(tier) + 1}`;

  function renderPanel(panel, side, heroId) {
    const hero = byHero.get(heroId) || heroes[0];
    panel.innerHTML = `
      <div class="hl-hud">
        <div class="hl-identity">
          <div class="hl-portrait-wrap">
            <button type="button" class="hl-hero-trigger" data-open-hero-picker aria-label="Choose hero">
              ${iconHtml(hero.icon, hero.name, 'hl-hero-icon')}
            </button>
            <span class="hl-level-corner">
              <input class="hl-level-input" type="number" min="1" max="30" value="1" data-field="level" aria-label="Hero level">
            </span>
          </div>
          <div class="hl-identity-main"></div>
        </div>
        <div class="hl-inventory">
          <div class="hl-inv-grid">
            ${Array.from({ length: 6 }, (_, i) => `
              <button type="button" class="hl-inv-slot is-empty" data-open-item-picker data-slot="${i}" aria-label="Choose item slot ${i + 1}">
                <span class="hl-slot-bevel"></span>
                <span class="hl-slot-glow"></span>
              </button>`).join('')}
          </div>
          <div class="hl-neutral-stack">
            <button type="button" class="hl-inv-slot hl-neutral-slot is-empty" data-open-item-picker data-slot="neutral" aria-label="Choose neutral item">
              <span class="hl-neutral-mark">N</span>
              <span class="hl-slot-bevel"></span>
              <span class="hl-slot-glow"></span>
            </button>
            <button type="button" class="hl-inv-slot hl-enchant-slot is-empty" data-open-item-picker data-slot="enchant" aria-label="Choose enchantment">
              <span class="hl-enchant-mark">E</span>
              <span class="hl-slot-bevel"></span>
              <span class="hl-slot-glow"></span>
            </button>
          </div>
        </div>
      </div>
      <div class="hl-bars">
        <div class="hl-bar hl-bar-hp">
          <div class="hl-bar-fill"></div>
          <span class="hl-bar-value" data-bar-value="hp"></span>
          <span class="hl-bar-regen" data-bar-regen="hpr"></span>
        </div>
        <div class="hl-bar hl-bar-mp">
          <div class="hl-bar-fill"></div>
          <span class="hl-bar-value" data-bar-value="mp"></span>
          <span class="hl-bar-regen" data-bar-regen="mpr"></span>
        </div>
      </div>
      <details class="hl-custom">
        <summary>Custom stats</summary>
        <div class="hl-custom-grid">
          ${CUSTOM.map(([key, label]) => `
            <label>${label}<input type="number" step="0.1" placeholder="auto" data-custom="${key}"></label>`).join('')}
        </div>
      </details>
      <div class="hl-total-list" data-total-list></div>
    `;
    panel.dataset.hero = hero.id;
    panel.dataset.side = side;
    panel.dataset.items = JSON.stringify(['', '', '', '', '', '']);
    panel.dataset.neutralItem = '';
    panel.dataset.enchantItem = '';
  }

  function state(panel) {
    const heroId = panel.dataset.hero || heroes[0].id;
    let level = parseInt(panel.querySelector('[data-field="level"]')?.value || '1', 10);
    level = Math.max(1, Math.min(30, Number.isFinite(level) ? level : 1));
    panel.querySelector('[data-field="level"]').value = String(level);
    const itemIds = JSON.parse(panel.dataset.items || '["","","","","",""]').filter(Boolean);
    const neutralItem = panel.dataset.neutralItem || '';
    if (neutralItem) itemIds.push(neutralItem);
    const enchantItem = panel.dataset.enchantItem || '';
    if (enchantItem) itemIds.push(enchantItem);
    const custom = {};
    panel.querySelectorAll('[data-custom]').forEach(inp => {
      custom[inp.dataset.custom] = inp.value === '' ? null : (Number(inp.value) || 0);
    });
    return { hero: byHero.get(heroId) || heroes[0], level, itemIds, custom };
  }

  function itemTotals(ids, attackType) {
    const isRanged = String(attackType || '').toLowerCase() === 'ranged';
    const out = { str: 0, agi: 0, int: 0, hp: 0, mp: 0, hpr: 0, mpr: 0, armor: 0, mrVals: [], evVals: [], damage: 0, aspd: 0, ms: 0, range: 0, cost: 0 };
    ids.forEach(id => {
      const it = byItem.get(id);
      if (!it) return;
      const b = it.bonus || {};
      out.str += Number(b.str) || 0;
      out.agi += Number(b.agi) || 0;
      out.int += Number(b.int) || 0;
      out.hp += Number(b.hp) || 0;
      out.mp += Number(b.mp) || 0;
      out.hpr += Number(b.hpr) || 0;
      out.mpr += Number(b.mpr) || 0;
      out.armor += Number(b.armor) || 0;
      if (b.mr) out.mrVals.push(Number(b.mr) || 0);
      if (b.evasion) out.evVals.push(Number(b.evasion) || 0);
      out.damage += (Number(b.damage) || 0) + (isRanged ? (Number(b.damageRanged) || 0) : (Number(b.damageMelee) || 0));
      out.aspd += Number(b.aspd) || 0;
      out.ms += (Number(b.ms) || 0) + (isRanged ? (Number(b.msRanged) || 0) : (Number(b.msMelee) || 0));
      if (isRanged) out.range += Number(b.range) || 0;
      out.cost += Number(it.cost) || 0;
    });
    return out;
  }

  function calc(st) {
    const s = st.hero.stats || {};
    const lvl = st.level;
    const plus = plus2At(lvl);
    const itemsTotal = itemTotals(st.itemIds, st.hero.attackType);
    const rawStr = (Number(s.str) || 0) + (lvl - 1) * (Number(s.strGain) || 0) + plus + itemsTotal.str;
    const rawAgi = (Number(s.agi) || 0) + (lvl - 1) * (Number(s.agiGain) || 0) + plus + itemsTotal.agi;
    const rawInt = st.hero.id === 'ogre_magi'
      ? 0
      : (Number(s.int) || 0) + (lvl - 1) * (Number(s.intGain) || 0) + plus + itemsTotal.int;
    const str = Math.floor(rawStr), agi = Math.floor(rawAgi), int = Math.floor(rawInt);
    const isOgre = st.hero.id === 'ogre_magi';
    const isHuskar = st.hero.id === 'huskar';
    const mpFromAttr = isHuskar ? 0 : (isOgre ? str * 6 : int * C.mpInt);
    const mprFromAttr = isHuskar ? 0 : (isOgre ? str * 0.02 : int * C.mprInt);
    const baseMr = (Number(s.mr) || 25) + int * C.mrInt;
    let mr = combinePct([baseMr, ...itemsTotal.mrVals]);
    let evasion = combinePct([...itemsTotal.evVals]);
    let armor = (Number(s.armor) || 0) + agi * C.armorAgi + itemsTotal.armor;
    let hp = Math.round((Number(s.hp) || 120) + str * C.hpStr + itemsTotal.hp);
    let mp = isHuskar ? 0 : Math.round((Number(s.mp) || 75) + mpFromAttr + itemsTotal.mp);
    let hpr = (Number(s.hpr) || 0) + str * C.hprStr + itemsTotal.hpr;
    let mpr = isHuskar ? 0 : (Number(s.mpr) || 0) + mprFromAttr + itemsTotal.mpr;
    if (st.custom.hp !== null) hp = Math.round(st.custom.hp);
    if (st.custom.mp !== null && !isHuskar) mp = Math.round(st.custom.mp);
    if (st.custom.hpr !== null) hpr = st.custom.hpr;
    if (st.custom.mpr !== null && !isHuskar) mpr = st.custom.mpr;
    if (st.custom.armor !== null) armor = st.custom.armor;
    if (st.custom.mr !== null) mr = st.custom.mr;
    if (st.custom.evasion !== null) evasion = st.custom.evasion;
    const primary = s.attr === 'uni' ? Math.floor((str + agi + int) * C.uniDmg)
      : s.attr === 'str' ? str : s.attr === 'agi' ? agi : int;
    const dmin = (Number(s.dmin) || 0) + primary + itemsTotal.damage;
    const dmax = (Number(s.dmax) || 0) + primary + itemsTotal.damage;
    const dmg = (dmin + dmax) / 2;
    const aspd = (Number(s.bas) || 100) + agi * C.asAgi + itemsTotal.aspd;
    const bat = Number(s.bat) || 1.7;
    const tHit = bat * 100 / Math.max(1, aspd);
    const ms = (Number(s.ms) || 0) + itemsTotal.ms;
    const range = (Number(s.range) || 0) + itemsTotal.range;
    const armorPct = armorFactor(armor) * 100;
    const ehpPhys = hp / Math.max(0.01, 1 - armorFactor(armor));
    const ehpMag = hp / Math.max(0.01, 1 - mr / 100);
    return { hp, mp, hpr, mpr, str, agi, int, armor, armorPct, mr, evasion, dmg, dmin, dmax, aspd, tHit, ms, range, ehpPhys, ehpMag, cost: itemsTotal.cost };
  }

  function renderHeroHud(panel, st, vals) {
    const hero = st.hero;
    const portrait = panel.querySelector('.hl-hero-icon');
    const hpValue = panel.querySelector('[data-bar-value="hp"]');
    const hpRegen = panel.querySelector('[data-bar-regen="hpr"]');
    const mpValue = panel.querySelector('[data-bar-value="mp"]');
    const mpRegen = panel.querySelector('[data-bar-regen="mpr"]');
    if (portrait) { portrait.src = hero.icon; portrait.alt = hero.name; }
    if (hpValue) hpValue.textContent = `${fmt(vals.hp)} / ${fmt(vals.hp)}`;
    if (hpRegen) hpRegen.textContent = `${vals.hpr >= 0 ? '+' : ''}${quickFmt(vals.hpr)}`;
    if (mpValue) mpValue.textContent = `${fmt(vals.mp)} / ${fmt(vals.mp)}`;
    if (mpRegen) mpRegen.textContent = `${vals.mpr >= 0 ? '+' : ''}${quickFmt(vals.mpr)}`;

    const slots = JSON.parse(panel.dataset.items || '["","","","","",""]');
    panel.querySelectorAll('.hl-inv-slot').forEach((slotEl, idx) => {
      const isNeutral = slotEl.dataset.slot === 'neutral';
      const isEnchant = slotEl.dataset.slot === 'enchant';
      const itemId = isNeutral
        ? (panel.dataset.neutralItem || '')
        : isEnchant
          ? (panel.dataset.enchantItem || '')
          : (slots[idx] || '');
      const item = byItem.get(itemId);
      slotEl.dataset.itemId = itemId;
      slotEl.classList.toggle('is-empty', !item);
      slotEl.innerHTML = item
        ? `<img src="${item.icon}" alt="${item.name}" loading="lazy"><span class="hl-slot-bevel"></span><span class="hl-slot-glow"></span>`
        : `${isNeutral ? '<span class="hl-neutral-mark">N</span>' : isEnchant ? '<span class="hl-enchant-mark">E</span>' : ''}<span class="hl-slot-bevel"></span><span class="hl-slot-glow"></span>`;
      slotEl.title = item ? item.name : (isNeutral ? 'Empty neutral slot' : isEnchant ? 'Empty enchantment slot' : 'Empty slot');
    });
  }

  function renderTotals(panel, vals) {
    const list = panel.querySelector('[data-total-list]');
    if (!list) return;
    list.innerHTML = METRICS.map(([key, label]) => `
      <div class="hl-stat-row"><span>${label}</span><strong>${fmtMetric(key, vals[key])}</strong></div>
    `).join('') + `<div class="hl-stat-row hl-cost"><span>Items cost</span><strong>${fmt(vals.cost)}g</strong></div>`;
  }

  function heroPickerMarkup(selectedId) {
    return `
      <div class="hl-picker-card hl-hero-picker-card" role="dialog" aria-modal="true" aria-label="Choose hero">
        <div class="hl-picker-head">
          <strong>Choose Hero</strong>
          <button type="button" class="hl-picker-close" data-picker-close aria-label="Close">x</button>
        </div>
        <div class="hl-hero-grid-wrap">
          ${['str', 'agi', 'int', 'uni'].map(key => `
            <section class="hl-hero-group hl-hero-group-${key}">
              <header>
                ${iconHtml(ATTR_META[key].icon, ATTR_META[key].label, 'hl-hero-group-icon')}
                <span>${ATTR_META[key].label}</span>
              </header>
              <div class="hl-hero-grid">
                ${heroGroups[key].map(hero => `
                  <button type="button" class="hl-hero-tile${hero.id === selectedId ? ' is-selected' : ''}" data-hero-id="${hero.id}" aria-label="${hero.name}">
                    <img src="${hero.icon}" alt="${hero.name}" loading="lazy">
                  </button>`).join('')}
              </div>
            </section>`).join('')}
        </div>
      </div>
    `;
  }

  function itemSectionMarkup(title, list, selectedId) {
    if (!list.length) return '';
    return `
      <section class="hl-item-section">
        <header>${title}</header>
        <div class="hl-item-grid">
          ${list.map(item => `
            <button type="button" class="hl-item-tile${item.id === selectedId ? ' is-selected' : ''}" data-item-id="${item.id}" aria-label="${item.name}">
              <img src="${item.icon}" alt="${item.name}" loading="lazy">
            </button>`).join('')}
        </div>
      </section>
    `;
  }

  function itemPickerMarkup(selectedId, tab, mode) {
    const neutralOnly = mode === 'neutral';
    const enchantOnly = mode === 'enchant';
    const currentTab = neutralOnly ? 'neutrals' : enchantOnly ? 'enchants' : (tab || 'basics');
    const neutral = itemGroups.neutrals;
    return `
      <div class="hl-picker-card hl-item-picker-card" role="dialog" aria-modal="true" aria-label="Choose item">
        <div class="hl-picker-head">
          <strong>Choose Item</strong>
          <div class="hl-picker-actions">
            <button type="button" class="hl-picker-clear" data-item-id="">Empty</button>
            <button type="button" class="hl-picker-close" data-picker-close aria-label="Close">x</button>
          </div>
        </div>
        <div class="hl-shop-tabs">
          ${((neutralOnly || enchantOnly) ? [[currentTab, neutralOnly ? 'Neutrals' : 'Enchants']] : [['basics', 'Basics'], ['upgrades', 'Upgrades']]).map(([id, label]) => `
            <button type="button" class="hl-shop-tab${currentTab === id ? ' is-active' : ''}" data-shop-tab="${id}">${label}</button>`).join('')}
        </div>
        <div class="hl-shop-body">
          ${currentTab === 'basics' ? itemGroups.basics.map(([name, list]) => itemSectionMarkup(name, list, selectedId)).join('') : ''}
          ${currentTab === 'upgrades' ? itemGroups.upgrades.map(([name, list]) => itemSectionMarkup(name, list, selectedId)).join('') : ''}
          ${currentTab === 'neutrals' ? `
            <div class="hl-neutrals-layout">
              <div class="hl-neutrals-tiers">
                ${neutral.tiers.map(([tier, list]) => itemSectionMarkup(tierLabel(tier), list, selectedId)).join('')}
              </div>
              <div class="hl-neutrals-enchants">
                ${itemSectionMarkup('Enchantment', neutral.enchants, selectedId)}
              </div>
            </div>
          ` : ''}
          ${currentTab === 'enchants' ? itemSectionMarkup('Enchantment', neutral.enchants, selectedId) : ''}
        </div>
      </div>
    `;
  }

  function closePicker() {
    activePicker = null;
    overlay.hidden = true;
    overlay.classList.remove('is-open');
    overlay.innerHTML = '';
  }

  function openHeroPicker(panel) {
    activePicker = { kind: 'hero', panel };
    overlay.innerHTML = heroPickerMarkup(panel.dataset.hero || heroes[0].id);
    overlay.hidden = false;
    overlay.classList.add('is-open');
  }

  function openItemPicker(panel, slot, tab) {
    const itemsState = JSON.parse(panel.dataset.items || '["","","","","",""]');
    const mode = slot === 'neutral' ? 'neutral' : slot === 'enchant' ? 'enchant' : 'normal';
    activePicker = { kind: 'item', panel, slot, tab: mode === 'normal' ? (tab || 'basics') : mode, mode };
    const selectedId = mode === 'neutral'
      ? (panel.dataset.neutralItem || '')
      : mode === 'enchant'
        ? (panel.dataset.enchantItem || '')
        : (itemsState[slot] || '');
    overlay.innerHTML = itemPickerMarkup(selectedId, activePicker.tab, mode);
    overlay.hidden = false;
    overlay.classList.add('is-open');
  }

  function update() {
    const panels = [...root.querySelectorAll('.hl-panel')];
    const aState = state(panels[0]);
    const bState = state(panels[1]);
    const a = calc(aState);
    const b = calc(bState);
    renderHeroHud(panels[0], aState, a);
    renderHeroHud(panels[1], bState, b);
    renderTotals(panels[0], a);
    renderTotals(panels[1], b);
    const diffTitle = document.getElementById('hl-diff-title');
    if (diffTitle) {
      diffTitle.textContent = `${aState.hero?.name || 'none'} vs ${bState.hero?.name || 'none'}`;
    }
    const diff = document.getElementById('hl-diff-list');
    diff.innerHTML = METRICS.map(([key, label]) => {
      const delta = (a[key] || 0) - (b[key] || 0);
      const cls = delta > 0 ? 'pos' : delta < 0 ? 'neg' : 'zero';
      return `<div class="hl-diff-row"><span>${label}</span><strong class="${cls}">${delta > 0 ? '+' : ''}${fmtMetric(key, delta)}</strong></div>`;
    }).join('');
  }

  const panels = [...root.querySelectorAll('.hl-panel')];
  renderPanel(panels[0], 'a', heroes[0].id);
  renderPanel(panels[1], 'b', heroes[Math.min(1, heroes.length - 1)].id);
  root.addEventListener('input', (e) => {
    if (e.target.matches('[data-field="level"], [data-custom]')) update();
  });
  root.addEventListener('click', (e) => {
    if (e.target.closest('.hl-level-corner')) return;
    const heroBtn = e.target.closest('[data-open-hero-picker]');
    if (heroBtn) {
      openHeroPicker(heroBtn.closest('.hl-panel'));
      return;
    }
    const itemBtn = e.target.closest('[data-open-item-picker]');
    if (itemBtn) {
      if (itemBtn.dataset.slot === 'enchant') {
        openItemPicker(itemBtn.closest('.hl-panel'), 'enchant');
        return;
      }
      openItemPicker(itemBtn.closest('.hl-panel'), itemBtn.dataset.slot === 'neutral' ? 'neutral' : Number(itemBtn.dataset.slot || 0));
      return;
    }
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.closest('[data-picker-close]')) {
      closePicker();
      return;
    }
    const heroTile = e.target.closest('[data-hero-id]');
    if (heroTile && activePicker?.kind === 'hero') {
      activePicker.panel.dataset.hero = heroTile.dataset.heroId;
      closePicker();
      update();
      return;
    }
    const tabBtn = e.target.closest('[data-shop-tab]');
    if (tabBtn && activePicker?.kind === 'item') {
      openItemPicker(activePicker.panel, activePicker.slot, tabBtn.dataset.shopTab);
      return;
    }
    const itemTile = e.target.closest('[data-item-id]');
    if (itemTile && activePicker?.kind === 'item') {
      if (activePicker.slot === 'neutral') {
        activePicker.panel.dataset.neutralItem = itemTile.dataset.itemId || '';
      } else if (activePicker.slot === 'enchant') {
        activePicker.panel.dataset.enchantItem = itemTile.dataset.itemId || '';
      } else {
        const slots = JSON.parse(activePicker.panel.dataset.items || '["","","","","",""]');
        slots[activePicker.slot] = itemTile.dataset.itemId || '';
        activePicker.panel.dataset.items = JSON.stringify(slots);
      }
      closePicker();
      update();
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !overlay.hidden) closePicker();
  });
  update();
})();

// ---- HERO STATS: vertical frozen-pane divider after the pinned Hero column ----
// The hs-table is mr-table-based (not creeps-table), so it doesn't get the
// creeps sticky-frame overlay. This positions a thin vertical line at the
// right edge of the sticky Hero column, drawn in the non-scrolling
// .creeps-page so it keeps repainting during horizontal scroll, shown only
// once the box is scrolled sideways (same convention as Neutral Creeps).
(function() {
  const table = document.querySelector('.hs-table');
  if (!table) return;
  const scroller = table.closest('.creeps-scroll');
  const page = table.closest('.creeps-page');
  const frame = page && page.querySelector('.hs-sticky-frame');
  if (!scroller || !page || !frame) return;

  function position() {
    const nameCell = table.querySelector('thead th.hs-name')
      || table.querySelector('tbody td.hs-name');
    if (!nameCell) return;
    const pageR = page.getBoundingClientRect();
    const scrR = scroller.getBoundingClientRect();
    const tableR = table.getBoundingClientRect();
    const nameR = nameCell.getBoundingClientRect();
    // Anchor the divider top to the pinned header's bottom (thead th is
    // sticky:top, so its rect tracks the visible pinned position).
    const headCell = table.querySelector('thead th.hs-name') || nameCell;
    const headBottom = headCell.getBoundingClientRect().bottom;
    const bottom = Math.min(scrR.bottom, tableR.bottom);
    frame.style.left = (nameR.right - pageR.left) + 'px';
    frame.style.top = (headBottom - pageR.top) + 'px';
    frame.style.height = Math.max(0, bottom - headBottom) + 'px';
    frame.style.width = '0px';
  }

  let posTicking = false;
  const positionRaf = () => {
    if (posTicking) return;
    posTicking = true;
    requestAnimationFrame(() => {
      position();
      frame.classList.toggle('visible', scroller.scrollLeft > 0);
      posTicking = false;
    });
  };
  // Scrolling happens INSIDE .creeps-scroll (the page body is locked), so the
  // divider must be repositioned on the BOX scroll — both vertical (the table's
  // bounding bottom that clamps the divider height moves as content scrolls) and
  // horizontal (visibility). Window scroll never fires here; resize + filter
  // changes also re-anchor (left/height from new column widths + row count).
  scroller.addEventListener('scroll', positionRaf, { passive: true });
  window.addEventListener('resize', positionRaf, { passive: true });
  window.addEventListener('mr:filter-changed', positionRaf);
  position();
})();

// ---- MANA ITEMS: Heatmap on/off toggle + recompute on filter change ----
(function() {
  const table = document.querySelector('.mr-table');
  const toggle = document.getElementById('mr-heatmap-toggle');
  if (!table || !toggle) return;
  function applyOrClear() {
    if (toggle.checked) {
      // Recompute by dispatching a synthetic event the heatmap IIFE
      // listens to. (The heatmap IIFE re-runs its applyHeatmap each
      // time a filter/sort changes — we route through it here too.)
      window.dispatchEvent(new CustomEvent('mr:filter-changed'));
    } else {
      // Strip all backgroundColor inline styles set by the heatmap.
      table.querySelectorAll('tbody td').forEach(td => {
        td.style.backgroundColor = '';
      });
    }
  }
  toggle.addEventListener('change', applyOrClear);
})();


/* ---- STAR SKY + WALL OF SIGNATURES (index) ----
   A few dim, lightly/independently twinkling pixel "stars" form the backdrop.
   The member names start HIDDEN (nothing painted at load → light first paint);
   a gold laser from the Premium star reveals them ONE per shot and they stay
   lit, so the wall fills up over time. Stars and names are laid out so they
   never overlap (they may sit very close). Re-runs on resize. Index-only. */
(function () {
  const layer = document.querySelector('.inv-signatures');
  if (!layer) return;
  // A name is "blank" if it has no visible char (only whitespace / zero-width),
  // so a beam never flies to an empty-looking name (blank names can still have a
  // nonzero render width, which is why offsetWidth alone doesn't catch them).
  function hasVisible(s) {
    const t = s.textContent;
    for (let i = 0; i < t.length; i++) {
      if (t[i].trim() === '') continue;                       // whitespace
      const c = t.charCodeAt(i);
      // zero-width chars + blank "filler" letters used as empty usernames:
      // Hangul fillers (115F/1160/3164/FFA0), Braille blank (2800), Mongolian sep.
      if (c === 0x200B || c === 0x200C || c === 0x200D || c === 0x2060 || c === 0xFEFF ||
          c === 0x115F || c === 0x1160 || c === 0x3164 || c === 0xFFA0 ||
          c === 0x2800 || c === 0x180E || c === 0x3000) continue;
      return true;
    }
    return false;
  }
  const sigs = [...layer.querySelectorAll('.inv-sig')].filter(hasVisible);
  if (!sigs.length) return;

  const overlap = (a, b) => !(a.r <= b.l || a.l >= b.r || a.b <= b.t || a.t >= b.b);

  // Dedicated star-sky layer behind everything.
  let sky = document.querySelector('.star-sky');
  if (!sky) {
    sky = document.createElement('div');
    sky.className = 'star-sky';
    sky.setAttribute('aria-hidden', 'true');
    document.body.appendChild(sky);
  }

  let pos = [];          // computed name positions {x,y,cx,cy,rot} (null if dropped)
  let starRects = [];    // star bounding rects, so names avoid them

  function forbiddenZones(W, H, M) {
    const zones = [];
    const book = document.querySelector('.inv-book');
    if (book) {
      const br = book.getBoundingClientRect();
      zones.push({ l: br.left - M, t: br.top - M, r: br.right + M, b: br.bottom + M });
    }
    const nav = document.querySelector('nav.top-nav');
    if (nav) {
      const nr = nav.getBoundingClientRect();
      zones.push({ l: 0, t: 0, r: W, b: nr.bottom + M });
    }
    return zones;
  }

  // A handful of dim pixel stars, avoiding the book/nav and each other.
  function placeStars(W, H) {
    sky.textContent = '';
    starRects = [];
    const forbidden = forbiddenZones(W, H, 4);
    const COUNT = Math.round(Math.min(92, Math.max(46, (W * H) / 13000)));  // +15% more (incl. smaller ones)
    const SM = 3;                                  // min gap between stars
    const twinkleCenters = [];                     // keep twinkling stars spread apart
    for (let i = 0; i < COUNT; i++) {
      for (let tryN = 0; tryN < 40; tryN++) {
        const sr = Math.random();
        const sz = sr < 0.12 ? 1 : sr < 0.30 ? 2 : sr < 0.78 ? 3 : 4;   // ~30% small (1–2px), rest 3–4px
        const x = 5 + Math.random() * (W - 10);
        const y = 5 + Math.random() * (H - 10);
        const r = { l: x - SM, t: y - SM, r: x + sz + SM, b: y + sz + SM };
        if (forbidden.some(f => overlap(r, f))) continue;
        if (starRects.some(s => overlap(r, s))) continue;
        const star = document.createElement('i');
        star.className = 'star';
        star.style.left = x.toFixed(1) + 'px';
        star.style.top = y.toFixed(1) + 'px';
        star.style.width = star.style.height = sz + 'px';
        // Three brightness tiers: most dim, ~22% bright, ~10% extra-bright (brighter still).
        const roll = Math.random();
        let lo, hi, staticOp;
        // Wide low→high swing so the twinkle is clearly visible (dims to nearly
        // nothing, then brightens to a clear peak).
        if (roll < 0.10) {
          lo = 0.35; hi = 1.0; staticOp = 0.78;
          star.style.boxShadow = '0 0 4px rgba(236,228,205,0.78)';
        } else if (roll < 0.32) {
          lo = 0.2; hi = 0.9; staticOp = 0.52;
          star.style.boxShadow = '0 0 3px rgba(232,224,200,0.5)';
        } else {
          lo = 0.08; hi = 0.5; staticOp = 0.3;
        }
        // Only ~22% twinkle (extra-bright lean toward it), and never too close to
        // another twinkling star — so few flicker at once and they stay spread out.
        const cx = x + sz / 2, cy = y + sz / 2;
        const spaced = !twinkleCenters.some(c => Math.hypot(c.x - cx, c.y - cy) < 55);
        const wantTwinkle = roll < 0.10 ? Math.random() < 0.6 : Math.random() < 0.22;
        if (wantTwinkle && spaced) {
          star.style.setProperty('--lo', lo);
          star.style.setProperty('--hi', hi);
          star.style.opacity = lo;
          const durN = 3 + Math.random() * 3.5;               // faster cadence → more noticeable
          // NEGATIVE delay = start already partway through the cycle, at a random
          // phase, so stars never twinkle in sync (positive delays would just
          // stagger the start but keep them aligned early on).
          const del = (-Math.random() * durN).toFixed(2);
          star.style.animation = 'starTwinkle ' + durN.toFixed(1) + 's ease-in-out ' + del + 's infinite';
          twinkleCenters.push({ x: cx, y: cy });
        } else {
          star.style.opacity = staticOp;
        }
        sky.appendChild(star);
        starRects.push(r);
        break;
      }
    }
  }

  // Place every name (avoiding book/nav, stars, and each other) but keep them
  // HIDDEN — they reveal only when a beam reaches them. Strict read/write phases
  // so the browser lays out ~twice (no per-name reflow). is-lit is preserved
  // across re-layout so already-revealed names stay visible.
  function placeNames(W, H) {
    const M = Math.max(2, Math.round(11 - sigs.length * 0.05));
    const FONT_MIN = 11, FONT_MAX = 22;
    const crowd = Math.max(0, Math.min(1, (sigs.length - 120) / 240));
    const fontTop = Math.round(FONT_MAX - (FONT_MAX - FONT_MIN) * crowd);
    const fontBot = Math.max(FONT_MIN, fontTop - 6);
    const EDGE = 6;
    const forbidden = forbiddenZones(W, H, M).concat(starRects);   // also dodge stars
    const n = sigs.length;
    // (1) write font sizes
    for (let i = 0; i < n; i++) {
      sigs[i].style.display = '';
      sigs[i].style.fontSize = (fontBot + Math.floor(Math.random() * (fontTop - fontBot + 1))) + 'px';
    }
    // (2) measure once
    const ws = new Array(n), hs = new Array(n);
    for (let i = 0; i < n; i++) { ws[i] = sigs[i].offsetWidth; hs[i] = sigs[i].offsetHeight; }
    // (3) pure-JS placement
    const placed = [];
    pos = new Array(n);
    for (let i = 0; i < n; i++) {
      const w0 = ws[i], h0 = hs[i];
      if (!w0 || !h0) { pos[i] = null; continue; }
      const rot = Math.random() * 14 - 7;
      const rad = Math.abs(rot) * Math.PI / 180;
      const bw = w0 * Math.cos(rad) + h0 * Math.sin(rad);
      const bh = w0 * Math.sin(rad) + h0 * Math.cos(rad);
      const cxMin = EDGE + bw / 2, cxMax = W - EDGE - bw / 2;
      const cyMin = EDGE + bh / 2, cyMax = H - EDGE - bh / 2;
      if (cxMax <= cxMin || cyMax <= cyMin) { pos[i] = null; continue; }
      let done = false;
      for (let k = 0; k < 60 && !done; k++) {
        const cx = cxMin + Math.random() * (cxMax - cxMin);
        const cy = cyMin + Math.random() * (cyMax - cyMin);
        const r = { l: cx - bw / 2 - M, t: cy - bh / 2 - M, r: cx + bw / 2 + M, b: cy + bh / 2 + M };
        let bad = false;
        for (let f = 0; f < forbidden.length; f++) { if (overlap(r, forbidden[f])) { bad = true; break; } }
        if (bad) continue;
        for (let p = 0; p < placed.length; p++) { if (overlap(r, placed[p])) { bad = true; break; } }
        if (bad) continue;
        pos[i] = { x: cx - w0 / 2, y: cy - h0 / 2, cx: cx, cy: cy, rot: rot };
        placed.push(r);
        done = true;
      }
      if (!done) pos[i] = null;
    }
    // (4) write transforms; do NOT reveal — names stay hidden until a beam hits.
    for (let i = 0; i < n; i++) {
      const s = sigs[i], p = pos[i];
      if (!p) { s.style.display = 'none'; continue; }
      s.style.transform = 'translate(' + p.x.toFixed(1) + 'px,' + p.y.toFixed(1) + 'px) rotate(' + p.rot.toFixed(1) + 'deg)';
    }
    layer.style.opacity = '1';     // layer is up; individual names hidden via CSS
  }

  function layout() {
    const W = document.documentElement.clientWidth;
    const H = document.documentElement.clientHeight;
    placeStars(W, H);
    placeNames(W, H);
  }

  function run() {
    // Wait for the wall font (Handjet) so widths measure right, capped at 300ms.
    const fontReady = (document.fonts && document.fonts.load)
      ? document.fonts.load('20px "Handjet"').catch(() => {})
      : Promise.resolve();
    Promise.race([
      Promise.resolve(fontReady),
      new Promise(r => setTimeout(r, 300)),
    ]).then(() => requestAnimationFrame(layout));   // defer off the first paint
  }
  if (document.readyState !== 'loading') run();
  else document.addEventListener('DOMContentLoaded', run);
  let t;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(layout, 200); }, { passive: true });

  // Premium-star laser: reveals one not-yet-lit name per shot; it then stays lit.
  const star = document.querySelector('.inv-cell-star .inv-icon')
            || document.querySelector('.inv-cell-star');
  let fx = null;                       // shared overlay for beams + dust
  function fxLayer() {
    if (!fx) {
      fx = document.createElement('div');
      fx.className = 'sig-beam-layer';
      fx.setAttribute('aria-hidden', 'true');
      document.body.appendChild(fx);
    }
    return fx;
  }
  function shootBeam(ox, oy, tx, ty) {
    if (!star) return;
    const beamLayer = fxLayer();
    const dx = tx - ox, dy = ty - oy;
    const dist = Math.hypot(dx, dy);
    const ang = Math.atan2(dy, dx) * 180 / Math.PI;
    const beam = document.createElement('div');
    beam.className = 'sig-beam';
    beam.style.left = ox + 'px';
    beam.style.top = oy + 'px';
    beam.style.width = dist + 'px';
    const tr = 'rotate(' + ang + 'deg)';
    const anim = beam.animate([
      { transform: tr + ' scaleX(0)', opacity: 0 },
      { transform: tr + ' scaleX(1)', opacity: 0.6, offset: 0.4 },
      { transform: tr + ' scaleX(1)', opacity: 0 },
    ], { duration: 600, easing: 'ease-out', fill: 'forwards' });
    beamLayer.appendChild(beam);
    anim.onfinish = () => beam.remove();
  }
  // VIP-name forge sparks: a small azure burst when a beam lights a VIP name,
  // as if it were just struck on an anvil. Specks shoot up + out, then gravity
  // arcs them down past the start and they fade. Same azure as .inv-sig-vip.
  function forgeSparks(sig) {
    const r = sig.getBoundingClientRect();
    const fxl = fxLayer();
    const N = 10 + Math.floor(Math.random() * 5);     // 10–14 sparks
    for (let k = 0; k < N; k++) {
      const p = document.createElement('i');
      p.className = 'sig-spark';
      const sz = Math.random() < 0.6 ? 2 : 3;
      p.style.width = p.style.height = sz + 'px';
      p.style.left = (r.left + Math.random() * r.width).toFixed(1) + 'px';
      p.style.top = (r.top + r.height * (0.3 + Math.random() * 0.5)).toFixed(1) + 'px';
      const ang = -Math.PI / 2 + (Math.random() - 0.5) * 1.9;   // fan around "up"
      const rad = 14 + Math.random() * 26;
      const dx = Math.cos(ang) * rad;
      const up = Math.sin(ang) * rad;                  // negative = upward
      const fall = 10 + Math.random() * 18;
      const a = p.animate([
        { transform: 'translate(0,0)', opacity: 1, offset: 0 },
        { transform: 'translate(' + (dx * 0.6).toFixed(1) + 'px,' + up.toFixed(1) + 'px)', opacity: 1, offset: 0.45 },
        { transform: 'translate(' + dx.toFixed(1) + 'px,' + (up + fall).toFixed(1) + 'px)', opacity: 0, offset: 1 },
      ], { duration: 600 + Math.random() * 500, easing: 'cubic-bezier(0.25,0.6,0.4,1)', fill: 'forwards' });
      fxl.appendChild(p);
      a.onfinish = () => p.remove();
    }
  }
  function lightUp(s) {
    s.classList.add('is-lit');
    if (s.classList.contains('inv-sig-vip')) forgeSparks(s);
  }
  function fireBeam(i) {
    const s = sigs[i];
    if (star) {
      const sr = star.getBoundingClientRect();
      shootBeam(sr.left + sr.width / 2, sr.top + sr.height / 2, pos[i].cx, pos[i].cy);
      setTimeout(() => lightUp(s), 220);   // light as the beam lands
    } else {
      lightUp(s);
    }
  }
  function spotlightOnce() {
    if (document.hidden || !pos.length) return;
    const pool = [];
    for (let i = 0; i < sigs.length; i++) {
      if (pos[i] && !sigs[i].classList.contains('is-lit')) pool.push(i);
    }
    if (!pool.length) { clearInterval(beamInterval); return; }
    // Usually one beam, but sometimes a volley: 20% chance of 2 beams at once,
    // 10% chance of 3 (each lights a different name).
    const roll = Math.random();
    let count = roll < 0.10 ? 3 : roll < 0.30 ? 2 : 1;
    count = Math.min(count, pool.length);
    for (let k = 0; k < count; k++) {
      const j = Math.floor(Math.random() * pool.length);
      fireBeam(pool.splice(j, 1)[0]);          // distinct name each beam
    }
  }
  setTimeout(spotlightOnce, 5000);              // first beam ~5s after load
  const beamInterval = setInterval(spotlightOnce, 2500);

  document.addEventListener('visibilitychange', () => {
    sky.classList.toggle('paused', document.hidden);
  });

  // Click a lit name → it "disintegrates" into pixel gold dust and returns to the
  // unlit pool, so a later beam can re-light it.
  function disintegrate(sig) {
    const r = sig.getBoundingClientRect();
    const fxl = fxLayer();
    const N = 16 + Math.floor(Math.random() * 10);   // 16–25 specks
    // Per-click randomisation so no two bursts disperse the same way.
    const spreadF = 0.8 + Math.random() * 0.7;       // this cloud's overall size
    const durBase = 3300 + Math.random() * 1800;     // this cloud's tempo (slow)
    const drift = Math.random() * Math.PI * 2;       // slight directional lean
    const driftAmt = Math.random() * 12;
    const vip = sig.classList.contains('inv-sig-vip');
    for (let k = 0; k < N; k++) {
      const p = document.createElement('i');
      p.className = vip ? 'sig-dust sig-dust-vip' : 'sig-dust';
      const sz = Math.random() < 0.5 ? 2 : 3;        // clear little squares (2–3px)
      p.style.width = p.style.height = sz + 'px';
      p.style.left = (r.left + Math.random() * r.width).toFixed(1) + 'px';
      p.style.top = (r.top + Math.random() * r.height).toFixed(1) + 'px';
      // Puff outward in all directions, spread wide so specks end up further apart,
      // + a gentle downward settle and this burst's directional lean.
      const ang = Math.random() * Math.PI * 2;
      const rad = (26 + Math.random() * 50) * spreadF;
      const dx = Math.cos(ang) * rad + Math.cos(drift) * driftAmt;
      const dy = Math.sin(ang) * rad * 0.6 + Math.sin(drift) * driftAmt + (5 + Math.random() * 16);
      const a = p.animate([
        { transform: 'translate(0,0)', opacity: 1, offset: 0 },
        { opacity: 1, offset: 0.5 },                 // linger visible longer before fading
        { transform: 'translate(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px)', opacity: 0, offset: 1 },
      ], { duration: durBase + Math.random() * 1400,  // ~10% slower dispersal, longer-lived
           easing: 'cubic-bezier(0.14,0.7,0.28,1)', fill: 'forwards' });
      fxl.appendChild(p);
      a.onfinish = () => p.remove();
    }
    sig.classList.remove('is-lit');                // fades out; rejoins the unlit pool
  }
  layer.addEventListener('click', (e) => {
    const sig = e.target.closest && e.target.closest('.inv-sig');
    if (sig && sig.classList.contains('is-lit')) disintegrate(sig);
  });
})();

// ---- INVENTORY SUB-PANELS: a tile with [data-panel-open="<name>"] opens its
// sub-panel ([data-panel="<name>"]) IN PLACE of the inventory grid instead of
// redirecting (Support → Telegram/Donation; Dynamics → Heroes/Items). The back
// arrow (or Escape) returns to the grid. Generic over any number of panels. ----
(function () {
  const book = document.querySelector('.inv-book');
  if (!book) return;
  const openers = [...book.querySelectorAll('[data-panel-open]')];
  const panels = [...book.querySelectorAll('[data-panel]')];
  if (!openers.length || !panels.length) return;
  const names = panels.map(p => p.dataset.panel);
  let lastOpener = null;
  const setOpen = (name) => {
    names.forEach(n => book.classList.toggle(n + '-open', n === name));
    panels.forEach(p => p.setAttribute('aria-hidden', p.dataset.panel === name ? 'false' : 'true'));
    openers.forEach(o => o.setAttribute('aria-expanded', o.dataset.panelOpen === name ? 'true' : 'false'));
    if (name) {
      const back = book.querySelector('.support-back');
      if (back) back.focus();
    } else if (lastOpener) {
      lastOpener.focus();
    }
  };
  openers.forEach(o => o.addEventListener('click', (e) => {
    e.preventDefault();
    lastOpener = o;
    setOpen(o.dataset.panelOpen);
  }));
  book.querySelectorAll('[data-panel-close]').forEach(
    (b) => b.addEventListener('click', () => setOpen(null)));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && names.some(n => book.classList.contains(n + '-open'))) {
      setOpen(null);
    }
  });
})();

// ---- CALENDAR tile: hover burns the date page (gold pixel fire) and loops 1→31.
// JS src-swap (not CSS content:url) with a one-time cache-bust, because the
// calendar GIF filename predates the other tile GIFs and browsers/CDN cached the
// old number-cycle version — the `?v=` forces the new burning GIF to load.
(function () {
  const tile = document.querySelector('.inv-cell-calendar');
  if (!tile) return;
  const img = tile.querySelector('.inv-icon');
  if (!img) return;
  const PNG = img.getAttribute('src');
  const GIF = 'icons/ui/gothic/icon_calendar.gif?v=' + Date.now();
  tile.addEventListener('mouseenter', () => { img.src = GIF; });
  tile.addEventListener('mouseleave', () => { img.src = PNG; });
})();

// ---- ITEMS tile: hover plays a one-shot chest-OPEN intro (key flies in → lid
// opens → gold beam + treasure), then LOOPS the open chest with the beam + gold
// glints twinkling for as long as it's hovered. Two APNGs swapped via JS (a
// single animation can't play an intro once then loop only its tail — same
// pattern as the mana fill+wave). The ?v= cache-bust forces each to restart
// from frame 0. Reverts to the closed PNG on mouse-out. Skipped under
// prefers-reduced-motion (stays closed). INTRO_MS must match the generator's
// printed intro duration (scripts/gen_chest_icon.py).
(function () {
  const tile = document.querySelector('.inv-cell-items');
  if (!tile) return;
  const img = tile.querySelector('.inv-icon');
  if (!img) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const PNG = img.getAttribute('src');
  const OPEN = 'icons/ui/gothic/icon_chest_open.png';   // intro, plays once
  const LOOP = 'icons/ui/gothic/icon_chest_loop.png';   // open + glints, loops
  const INTRO_MS = 1044;
  // Preload + decode both APNGs so swapping src mid-hover is instant — without
  // this the browser fetches the loop on first swap and the beam visibly stalls.
  [OPEN, LOOP].forEach(s => { const p = new Image(); p.src = s; });
  let timer = null;
  tile.addEventListener('mouseenter', () => {
    clearTimeout(timer);
    img.src = ''; img.src = OPEN;
    timer = setTimeout(() => { img.src = ''; img.src = LOOP; }, INTRO_MS);
  });
  tile.addEventListener('mouseleave', () => {
    clearTimeout(timer);
    img.src = PNG;
  });
})();

// ---- MANA ITEMS tile: hover plays a one-shot FILL (empty→half), then loops the
// wave at that level. Two GIFs swapped via JS — a single GIF can't play an intro
// once and then loop only its tail. Reverts to the static bottle on mouse-out.
(function () {
  // The mana icon now lives on the "Mana" button inside the Items sub-panel
  // (it used to be a top-level tile). querySelectorAll keeps this robust no
  // matter where `.inv-cell-mana` sits.
  const FILL = 'icons/ui/gothic/icon_mana_fill.gif';
  const WAVE = 'icons/ui/gothic/icon_mana.gif';
  const FILL_MS = 11 * 150;            // fill GIF: 11 frames × 150ms
  document.querySelectorAll('.inv-cell-mana').forEach((tile) => {
    const img = tile.querySelector('.inv-icon');
    if (!img) return;
    const PNG = img.getAttribute('src');
    let timer = null;
    tile.addEventListener('mouseenter', () => {
      clearTimeout(timer);
      img.src = FILL + '?' + Date.now();  // cache-bust forces the fill to replay
      timer = setTimeout(() => { img.src = WAVE; }, FILL_MS);
    });
    tile.addEventListener('mouseleave', () => {
      clearTimeout(timer);
      img.src = PNG;
    });
  });
})();

// ---- Ko-Fi gold stack: hover plays the sparkle APNG, reverts on mouse-out.
//      Skipped under prefers-reduced-motion.
(function () {
  const btn = document.querySelector('.support-kofi');
  if (!btn) return;
  const img = btn.querySelector('.inv-icon');
  if (!img) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const PNG      = img.getAttribute('src');
  const SPARKLE  = 'icons/ui/gothic/gold_stack_sparkle.png';
  btn.addEventListener('mouseenter', () => { img.src = SPARKLE + '?' + Date.now(); });
  btn.addEventListener('mouseleave', () => { img.src = PNG; });
})();


/* ---- Formula calculator (formula_change) ----
   Each `.formula-change[data-fx-old]` has a number input; on change we re-evaluate
   both formulas for every example row (the `fixed` variable = the input value,
   the `vary` variable = the row's data-h) and refresh the gold cell + Δ% badge.
   Patch pages only; mirrors b()/gradient_class colouring. */
(function () {
  const blocks = document.querySelectorAll('.formula-change[data-fx-old]');
  if (!blocks.length) return;
  const fmt = (x) => (Math.round(x * 10) / 10).toString();
  function gradClass(mag, isBuff) {
    const p = isBuff ? 'buff' : 'nerf';
    if (mag <= 5) return p + '1';
    if (mag <= 10) return p + '2';
    if (mag <= 15) return p + '3';
    if (mag <= 20) return p + '4';
    if (mag <= 25) return p + '5';
    if (mag <= 33) return p + '6';
    if (mag <= 45) return p + '7';
    if (mag <= 60) return p + '8';
    if (mag <= 80) return p + '9';
    return p + '10';
  }
  function pctBadge(o, n, lower) {
    let inner;
    if (o === 0 || n === o) {
      inner = '<span class="badge neutral">0%</span>';
    } else {
      const raw = (n - o) / o * 100;
      const isBuff = lower ? (n < o) : (n > o);
      const disp = (n > o ? '+' : '-') + fmt(Math.abs(raw)) + '%';
      inner = '<span class="badge ' + gradClass(Math.abs(raw), isBuff) + '">' + disp + '</span>';
    }
    return '<span class="badge-group">' + inner + '</span>';   // plain text, no pill box
  }
  blocks.forEach((block) => {
    const input = block.querySelector('.formula-input');
    if (!input) return;
    const invar = block.dataset.fxInvar;
    const varyvar = block.dataset.fxVaryvar;
    const def = parseFloat(block.dataset.fxDefault);
    const lower = block.dataset.fxLower === '1';
    let fOld, fNew;
    // `^` = exponentiation (Valve writes x^2), not JS bitwise xor.
    const toJs = (e) => e.replace(/\^/g, '**');
    try {
      // Formulas are author-authored (data attributes we emit), so Function() is safe here.
      fOld = new Function(invar, varyvar, 'return (' + toJs(block.dataset.fxOld) + ');');
      fNew = new Function(invar, varyvar, 'return (' + toJs(block.dataset.fxNew) + ');');
    } catch (e) { return; }
    const rows = [...block.querySelectorAll('tr[data-h]')];
    function recalc() {
      let nv = parseFloat(input.value);
      if (!isFinite(nv)) nv = def;
      rows.forEach((tr) => {
        const h = parseFloat(tr.dataset.h);
        let o, n;
        try { o = fOld(nv, h); n = fNew(nv, h); } catch (e) { return; }
        const isOld = tr.closest('.formula-pane-old');
        const gold = tr.querySelector('.fx-gold');
        if (gold) gold.textContent = fmt(isOld ? o : n);
        const pc = tr.querySelector('.fx-pct');
        if (pc && !isOld) pc.innerHTML = pctBadge(o, n, lower);   // Δ% only in NEW pane
      });
    }
    input.addEventListener('input', recalc);
  });
})();

(function() {
  // ---- TERRAIN COMPARE (terrain.html) — swipe slider + Loupe magnifier ----
  //  - Divider moves ONLY by dragging the handle (or arrow keys).
  //  - Trees / Camps top-bar checkboxes toggle the SVG overlay layers.
  //  - "Loupe" is a MODE (top-bar button). When on, hovering the MAP (not the
  //    handle or top-bar) shows a gold magnifier following the cursor; click
  //    pins it, then sweeping the handle compares that spot old↔new inside the
  //    circle (the toggled tree/camp markers are cloned into the lens too).
  function initTerrainCompare() {
    // One slider per map pair (e.g. 7.41 and 7.40 panes both exist; hidden ones
    // are still wired so switching the picker shows a working slider).
    document.querySelectorAll('.terrain-compare').forEach(initOneTerrainCompare);
  }
  function initOneTerrainCompare(root) {
    if (!root) return;
    const stage = root.querySelector('.tc-stage');
    const handle = root.querySelector('.tc-handle');
    if (!stage || !handle) return;

    const ZOOM = parseFloat(root.dataset.zoom) || 1.9;
    const lens = root.querySelector('.tc-lens');
    const lensOld = root.querySelector('.tc-lens-old');
    const lensNew = root.querySelector('.tc-lens-new');
    const lensRim = root.querySelector('.tc-lens-rim');
    const markerSvgs = stage.querySelectorAll('.tc-markers');
    const lensOk = !!(lens && lensOld && lensNew);
    const LENS_PX = parseFloat(root.dataset.lens) || 184;
    if (root.dataset.lens) stage.style.setProperty('--lens', root.dataset.lens + 'px');

    let pos = parseFloat(root.dataset.pos);
    if (!isFinite(pos)) pos = 50;
    function apply(p) {
      pos = Math.max(0, Math.min(100, p));
      stage.style.setProperty('--pos', pos + '%');
      handle.setAttribute('aria-valuenow', Math.round(pos));
    }
    apply(pos);

    // ---- divider drag: HANDLE ONLY (pointer capture isolates it) ----
    let dragging = false;
    let dragRect = null;      // stage rect cached at pointerdown — avoids
    let dragHalfW = 22;       // getBoundingClientRect() on every pointermove
    let sliderRaf = null;
    let pendingX = 0;

    function posFromX(clientX) {
      const r = dragRect || stage.getBoundingClientRect();
      if (r.width <= 0) return pos;
      return ((clientX - r.left) / r.width) * 100;
    }
    // During drag, position the handle via transform (compositor) so the
    // browser never triggers layout for the handle's left property.
    function applyHandleTransform(p) {
      if (!dragRect) return;
      handle.style.transform = 'translateX(' + (dragRect.width * p / 100 - dragHalfW) + 'px)';
    }
    handle.addEventListener('pointerdown', function(e) {
      dragging = true;
      dragRect = stage.getBoundingClientRect();
      dragHalfW = handle.offsetWidth / 2;
      stage.classList.add('is-dragging');
      // Switch from CSS left:var(--pos) to transform-based positioning.
      // Read current position first so the handle doesn't jump on click.
      var curPos = parseFloat(stage.style.getPropertyValue('--pos')) || 50;
      handle.style.left = '0';
      handle.style.transform = 'translateX(' + (dragRect.width * curPos / 100 - dragHalfW) + 'px)';
      if (e.pointerId != null && handle.setPointerCapture) {
        try { handle.setPointerCapture(e.pointerId); } catch (_) {}
      }
      e.preventDefault();
      e.stopPropagation();
    });
    handle.addEventListener('pointermove', function(e) {
      if (!dragging) return;
      pendingX = e.clientX;
      if (sliderRaf !== null) return;
      sliderRaf = requestAnimationFrame(function() {
        sliderRaf = null;
        const p = posFromX(pendingX);
        apply(p);
        applyHandleTransform(pos);
      });
    });
    function endDrag() {
      if (!dragging) return;
      dragging = false;
      dragRect = null;
      stage.classList.remove('is-dragging');
      // Revert handle to CSS-driven left: var(--pos) for arrow keys / resize.
      handle.style.left = '';
      handle.style.transform = '';
    }
    handle.addEventListener('pointerup', endDrag);
    handle.addEventListener('pointercancel', endDrag);
    handle.addEventListener('keydown', function(e) {
      let step = 0;
      switch (e.key) {
        case 'ArrowLeft': case 'ArrowDown': step = -2; break;
        case 'ArrowRight': case 'ArrowUp': step = 2; break;
        case 'PageDown': step = -10; break;
        case 'PageUp': step = 10; break;
        case 'Home': apply(0); e.preventDefault(); return;
        case 'End': apply(100); e.preventDefault(); return;
        default: return;
      }
      apply(pos + step);
      e.preventDefault();
    });

    // ---- magnifier lens (Zoom mode) ----
    let loupeMode = false;
    let pinned = false;
    let lensMarkers = [];          // cloned marker SVGs (trees-old/new, camps)
    let lensR = LENS_PX / 2;       // lens radius — derived from data-lens attr,
                                   // never read from DOM to avoid layout reflow
    let rafId = null;              // RAF handle for move throttling
    let pendingCx = 0, pendingCy = 0;
    function buildLensMarkers() {
      if (!lensOk || lensMarkers.length || !markerSvgs.length) return;
      markerSvgs.forEach(function(svg) {
        const clone = svg.cloneNode(true);   // keeps its clip + toggle classes
        clone.classList.add('tc-lens-markers');
        clone.removeAttribute('aria-hidden');
        lens.insertBefore(clone, lensRim || null);
        lensMarkers.push(clone);
      });
    }
    function sizeLens() {
      if (!lensOk) return;
      const w = stage.getBoundingClientRect().width * ZOOM;
      [lensOld, lensNew].concat(lensMarkers).forEach(function(el) {
        if (el) { el.style.width = w + 'px'; el.style.height = w + 'px'; }
      });
      // lensR is fixed (derived from data-lens); no DOM read needed here.
    }
    function placeLens(cx, cy) {
      if (!lensOk) return;
      lens.style.transform = 'translate(' + (cx - lensR) + 'px,' + (cy - lensR) + 'px)';
      const tf = 'translate(' + (lensR - cx * ZOOM) + 'px,' + (lensR - cy * ZOOM) + 'px)';
      lensOld.style.transform = tf;
      lensNew.style.transform = tf;
      lensMarkers.forEach(function(el) { el.style.transform = tf; });
    }
    // RAF-throttled wrapper: coalesces rapid pointermove events to one
    // placeLens call per animation frame, preventing layout thrashing.
    function schedulePlaceLens(cx, cy) {
      pendingCx = cx; pendingCy = cy;
      if (rafId !== null) return;
      rafId = requestAnimationFrame(function() {
        rafId = null;
        placeLens(pendingCx, pendingCy);
      });
    }
    function localXY(e) {
      const r = stage.getBoundingClientRect();
      return [e.clientX - r.left, e.clientY - r.top];
    }
    // Over the handle → no lens (so you can grab it with a normal cursor). The
    // layer toggles now live ABOVE the stage, so they never overlap the map.
    function overControls(e) {
      return !!(e.target.closest && e.target.closest('.tc-handle'));
    }
    function hideLens() { if (lensOk) lens.classList.remove('visible'); }

    if (lensOk) {
      stage.addEventListener('pointermove', function(e) {
        if (!loupeMode || pinned || dragging || e.pointerType === 'touch') return;
        if (overControls(e)) { hideLens(); return; }
        const xy = localXY(e);
        lens.classList.add('visible');
        schedulePlaceLens(xy[0], xy[1]);
      });
      stage.addEventListener('pointerleave', function() { if (!pinned) hideLens(); });
      stage.addEventListener('click', function(e) {
        if (!loupeMode || dragging || overControls(e)) return;
        const xy = localXY(e);
        pinned = !pinned;
        stage.classList.toggle('lens-pinned', pinned);
        lens.classList.add('visible');
        placeLens(xy[0], xy[1]);
      });
      window.addEventListener('resize', sizeLens);
    }

    // ---- top-bar toggle buttons (aria-pressed) ----
    function pressed(btn) { return btn.getAttribute('aria-pressed') === 'true'; }
    function setPressed(btn, on) { btn.setAttribute('aria-pressed', on ? 'true' : 'false'); }

    // Zoom (magnifier mode)
    const zoomBtn = root.querySelector('.tc-btn-zoom');
    if (zoomBtn && lensOk) {
      zoomBtn.addEventListener('click', function() {
        loupeMode = !loupeMode;
        root.classList.toggle('loupe-on', loupeMode);
        setPressed(zoomBtn, loupeMode);
        if (loupeMode) {
          buildLensMarkers();
          sizeLens();
        } else {
          pinned = false;
          stage.classList.remove('lens-pinned');
          hideLens();
        }
      });
    }

    // ---- POWER RUNE cycling: a power-rune spot can roll any of the 7 runes, so
    // while the Power layer is ON its map markers cycle through tc_rune_0..6
    // every 3s. The toolbar button shows a random rune on load. ----
    const RUNE_BASE = 'icons/ui/gothic/tc_rune_';
    const RUNE_COUNT = 7;
    let powerTimer = null, powerIdx = 0;
    function setRune(i) {
      const src = RUNE_BASE + i + '.png';
      root.querySelectorAll('.tm-layer-power image').forEach(function(im) {
        im.setAttribute('href', src);
        im.setAttribute('xlink:href', src);   // older SVG href
      });
    }
    function togglePowerCycle(on) {
      if (powerTimer) { clearInterval(powerTimer); powerTimer = null; }
      if (!on) return;
      setRune(powerIdx);
      powerTimer = setInterval(function() {
        powerIdx = (powerIdx + 1) % RUNE_COUNT;
        setRune(powerIdx);
      }, 3000);
    }
    const powerBtnImg = root.querySelector('.tc-layer-btn[data-layer="power"] img');
    if (powerBtnImg) powerBtnImg.src = RUNE_BASE + Math.floor(Math.random() * RUNE_COUNT) + '.png';

    // Layer toggles (Trees / Camps + the point-entity layers). Each carries
    // data-layer="<key>"; clicking flips root .show-<key>, which the CSS uses to
    // reveal that layer's SVG markers (split old/new by the slider).
    root.querySelectorAll('.tc-layer-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const on = !pressed(btn);
        setPressed(btn, on);
        root.classList.toggle('show-' + btn.dataset.layer, on);
        if (btn.dataset.layer === 'power') togglePowerCycle(on);
      });
    });
  }

  // ---- PATCH PICKER (terrain.html) — gold dropdown; switching it swaps the
  // visible map pane (slider or fallback) + the matching change-list pane. Same
  // structure as the calendar year-picker. ----
  function initTerrainPicker() {
    const picker = document.querySelector('.tc-picker');
    if (!picker) return;
    const btn = picker.querySelector('.cal-year-current');
    const menu = picker.querySelector('.cal-year-menu');
    const valEl = picker.querySelector('.cal-year-current-val');
    const opts = [...menu.querySelectorAll('.cal-year-opt')];
    const open = () => { menu.hidden = false; picker.classList.add('is-open'); btn.setAttribute('aria-expanded', 'true'); };
    const close = () => { menu.hidden = true; picker.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false'); };
    const select = (ver) => {
      valEl.textContent = ver;
      opts.forEach(o => {
        const on = o.dataset.patch === ver;
        o.classList.toggle('is-selected', on);
        o.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      document.querySelectorAll('.terrain-map-pane, .terrain-list-pane')
        .forEach(p => { p.hidden = (p.dataset.patch !== ver); });
    };
    btn.addEventListener('click', e => { e.stopPropagation(); menu.hidden ? open() : close(); });
    opts.forEach(o => o.addEventListener('click', () => { select(o.dataset.patch); close(); }));
    document.addEventListener('click', e => { if (!picker.contains(e.target)) close(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });

    // Deep-link: ?patch=<ver> (from a patch page's "View on map" button)
    // preselects that patch if it has a terrain pane.
    const wanted = new URLSearchParams(location.search).get('patch');
    if (wanted && opts.some(o => o.dataset.patch === wanted)) select(wanted);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initTerrainCompare();
      initTerrainPicker();
    });
  } else {
    initTerrainCompare();
    initTerrainPicker();
  }
})();

// ---------------------------------------------------------------------
// Info-tip (i) popup positioning — keep the bubble inside the viewport.
// CSS centers it above the (i); this nudges it horizontally so it never
// runs off-screen, and flips it below when there isn't room above.
// Event-delegated so it covers every (i) without per-element listeners.
// ---------------------------------------------------------------------
(function () {
  var MARGIN = 8;
  function place(tip) {
    var pop = tip.querySelector('.info-pop');
    if (!pop) return;
    // Reset so we measure the natural size, then position explicitly.
    pop.style.left = '0';
    pop.style.right = 'auto';
    pop.style.transform = 'none';
    var tr = tip.getBoundingClientRect();
    var pw = pop.offsetWidth;
    var ph = pop.offsetHeight;
    var vw = document.documentElement.clientWidth;
    // Horizontal: center over the (i), then clamp into the viewport.
    var vpLeft = tr.left + tr.width / 2 - pw / 2;
    vpLeft = Math.max(MARGIN, Math.min(vpLeft, vw - pw - MARGIN));
    pop.style.left = (vpLeft - tr.left) + 'px';
    // Vertical: prefer above; flip below if it would clip the top.
    if (tr.top - ph - 10 < MARGIN) {
      pop.style.top = 'calc(100% + 8px)';
      pop.style.bottom = 'auto';
    } else {
      pop.style.bottom = 'calc(100% + 8px)';
      pop.style.top = 'auto';
    }
  }
  function handler(e) {
    var t = e.target;
    if (!t || !t.closest) return;
    var tip = t.closest('.info-tip');
    if (tip) place(tip);
  }
  document.addEventListener('mouseover', handler, true);
  document.addEventListener('focusin', handler, true);
})();

// ---- WHAT'S NEW badge (index.html) ----
(function() {
  const btn = document.querySelector('.version-beta-wrap');
  const popup = document.querySelector('.whatsnew-popup');
  if (!btn || !popup) return;
  const LS_KEY = 'wn_seen_v1';
  if (localStorage.getItem(LS_KEY)) btn.classList.add('wn-seen');

  function place() {
    // measure with display:block to get real dimensions
    const wasHidden = !popup.classList.contains('wn-open');
    if (wasHidden) { popup.style.visibility = 'hidden'; popup.style.display = 'block'; }
    const pr = popup.getBoundingClientRect();
    const br = btn.getBoundingClientRect();
    if (wasHidden) { popup.style.display = ''; popup.style.visibility = ''; }
    const gap = 10, vw = window.innerWidth, vh = window.innerHeight;
    let top = br.top - pr.height - gap;
    if (top < gap) top = br.bottom + gap;
    top = Math.max(gap, Math.min(top, vh - pr.height - gap));
    let left = br.right - pr.width;
    left = Math.max(gap, Math.min(left, vw - pr.width - gap));
    popup.style.top = top + 'px';
    popup.style.left = left + 'px';
  }

  btn.addEventListener('click', function(e) {
    e.stopPropagation();
    if (popup.classList.contains('wn-open')) {
      popup.classList.remove('wn-open');
    } else {
      place();
      popup.classList.add('wn-open');
      if (!btn.classList.contains('wn-seen')) {
        btn.classList.add('wn-seen');
        try { localStorage.setItem(LS_KEY, '1'); } catch(_) {}
      }
    }
  });
  document.addEventListener('click', function(e) {
    if (!popup.contains(e.target) && e.target !== btn)
      popup.classList.remove('wn-open');
  });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') popup.classList.remove('wn-open');
  });
  window.addEventListener('resize', function() {
    if (popup.classList.contains('wn-open')) place();
  });
})();
