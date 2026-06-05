
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
      const y = el.getBoundingClientRect().top + window.scrollY - navH - 8;
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
    // Offset for the sticky nav so the heading lands just BELOW it. Plain
    // scrollIntoView({block:'start'}) parks the heading at viewport top, hidden
    // behind the nav — so you see the rows under it and it reads as "jumped
    // past / below the result". Mirror the re-anchor offset used on load.
    const navH = parseFloat(getComputedStyle(document.documentElement)
      .getPropertyValue('--site-nav-h')) || 70;
    const y = target.element.getBoundingClientRect().top + window.scrollY - navH - 8;
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

  function dynBuildPill(patch, counts, entityId, isCurrent, fromVersion, filePrefix, bnOnly, removed) {
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
    const gradCounts = bnOnly
      ? { buff: (eff.buff || 0) + (eff.new || 0),
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

  // Cache the per-page patches window so we compute it once, not 250+ times.
  // Pure function of manifest → ordered patches array.
  function dynWindow(manifest) {
    // Always show the 12 newest patches in RELEASE_HISTORY, regardless of
    // which patch page the user is currently on. The .current class on the
    // pill that matches the page version visually marks where they are.
    // manifest.patches is newest-first → take first 12, reverse so oldest
    // is on the left in the rendered row.
    return manifest.patches.slice(0, 12).reverse();
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
      row.appendChild(dynBuildPill(p, counts, id, p.version === currentVersion, currentVersion));
    }
    entityDiv.appendChild(row);
  }

  // Fill / refill the heroes_dyn matrix's data cells with one pill each. Only
  // cells the builder marked with data-ver/data-hkey (the hero actually changed
  // that patch) are filled — untouched cells stay as the CSS empty diamond, so
  // runtime work scales with real data, not the full N×M grid. Re-runnable: it
  // clears any existing pill first, so the "Buff/nerf only" toggle can rebuild.
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
      td.appendChild(dynBuildPill(patch, counts, td.dataset.eid, false, fromTok, 'patches/', bnOnly, removed));
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

  // Wire the heroes_dyn toolbar: Hide old (fit-to-width), Buff/nerf only,
  // the "Remove" tag chips, and the hero search box.
  function dynSetupMatrix(table, manifest) {
    const elOld = document.getElementById('hd-hide-old');
    const elBn = document.getElementById('hd-bn-only');
    const removed = new Set();                 // tags the user toggled off
    const chips = [...table.closest('.creeps-page').querySelectorAll('.hd-tag[data-tag]')];
    const syncChips = () => chips.forEach(c => c.classList.toggle('removed', removed.has(c.dataset.tag)));
    const layout = () => dynLayoutMatrix(table, !elOld || elOld.checked);
    const refill = () => dynFillMatrix(table, manifest, !!(elBn && elBn.checked), removed);
    refill();
    layout();
    if (elOld) elOld.addEventListener('change', layout);

    // "Buff/nerf only": besides the two-band colouring, it auto-removes every
    // tag except buff/nerf from the chips (more logical — the cell then shows
    // ONLY buff vs nerf, matching the toggle's name). We snapshot the user's
    // own Remove selection on the way in and restore it when they switch off.
    let bnSnapshot = null;
    if (elBn) elBn.addEventListener('change', () => {
      if (elBn.checked) {
        bnSnapshot = new Set(removed);
        DYN_TAG_ORDER.forEach(t => { if (t !== 'buff' && t !== 'nerf') removed.add(t); });
      } else {
        removed.clear();
        if (bnSnapshot) bnSnapshot.forEach(t => removed.add(t));
        bnSnapshot = null;
      }
      syncChips();
      refill();
    });

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
    const classChips = page ? [...page.querySelectorAll('.hd-class-chip[data-class]')] : [];
    const delToggle = document.getElementById('hd-show-deleted');
    const priceMin = document.getElementById('hd-price-min');
    const priceMax = document.getElementById('hd-price-max');
    const priceClear = document.getElementById('hd-price-clear');
    const rows = [...table.querySelectorAll('tbody tr')];
    const applyRowFilters = () => {
      const terms = search
        ? search.value.toLowerCase().split(',').map(s => s.trim()).filter(Boolean)
        : [];
      const enabled = classChips.length
        ? new Set(classChips.filter(c => c.getAttribute('aria-pressed') !== 'false')
                            .map(c => c.dataset.class))
        : null;
      const showDeleted = !!(delToggle && delToggle.checked);
      const lo = priceMin ? parseFloat(priceMin.value) : NaN;
      const hi = priceMax ? parseFloat(priceMax.value) : NaN;
      const hasLo = !isNaN(lo), hasHi = !isNaN(hi);
      // Clear-X visible only when a bound is set.
      if (priceClear) priceClear.hidden = !(hasLo || hasHi);
      rows.forEach(tr => {
        const name = (tr.querySelector('td.hd-hero')?.dataset.sort || '').toLowerCase();
        const okSearch = !terms.length || terms.some(t => name.includes(t));
        const okClass = !enabled || enabled.has(tr.dataset.class);
        // data-current="0" = removed from the game → shown only when "Show deleted".
        const okDel = showDeleted || tr.dataset.current !== '0';
        // Price: items without data-price (neutrals/enchants = free) are EXEMPT.
        let okPrice = true;
        const p = tr.dataset.price;
        if ((hasLo || hasHi) && p !== undefined) {
          const v = parseFloat(p);
          if (hasLo && v < lo) okPrice = false;
          if (hasHi && v > hi) okPrice = false;
        }
        tr.style.display = (okSearch && okClass && okDel && okPrice) ? '' : 'none';
      });
    };
    if (search) search.addEventListener('input', applyRowFilters);
    classChips.forEach(chip => chip.addEventListener('click', () => {
      chip.setAttribute('aria-pressed',
        chip.getAttribute('aria-pressed') === 'false' ? 'true' : 'false');
      applyRowFilters();
    }));
    if (delToggle) delToggle.addEventListener('change', applyRowFilters);
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
          const windowed = dynWindow(manifest);
          entities.forEach(e => dynRenderRow(e, manifest, windowed, currentVersion));
          // Rendering a pill row into EVERY entity adds ~28px of height to each
          // one — so any entity targeted by the #hash drifts far down after the
          // browser's initial anchor. Re-anchor now that all rows exist (the
          // getBoundingClientRect read forces layout first). Offset for the nav.
          if (window.location.hash) {
            const el = document.getElementById(
              decodeURIComponent(window.location.hash.slice(1)));
            if (el) {
              const navH = parseFloat(getComputedStyle(document.documentElement)
                .getPropertyValue('--site-nav-h')) || 70;
              const y = el.getBoundingClientRect().top + window.scrollY - navH - 8;
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
  // row order, so the grouped look survives sorting by level.
  function collapseLevels(rows) {
    let prev = null;
    rows.forEach(tr => {
      const cell = tr.querySelector('.lvl-cell');
      if (!cell) return;
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
    rows.forEach(tr => tbody.appendChild(tr));
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
        originalOrder.forEach(tr => tbody.appendChild(tr));
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

  // Body identity cells are the first three: lvl(0), icon(1), name(2).
  // The header has only two cells over them: lvl th(0) + Юнит th(1,
  // colspan=2). Compute cumulative left offsets from the body widths and
  // apply them to both the body sticky cells and the header sticky cells.
  function applyLeftOffsets() {
    const tds = [...firstRow.children];
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
    // Right edge of the frozen identity block = right edge of the LAST sticky
    // column in the row. Creeps/UA pin 2-3 columns; the heroes_dyn matrix pins
    // just one (the hero name) — measuring the last sticky cell keeps the
    // divider correct for any number of frozen columns (hardcoding firstTds[2]
    // put the divider 2 columns too far right on the single-column matrix).
    const stickyCells = firstRow.querySelectorAll('.sticky-col');
    const lastSticky = stickyCells[stickyCells.length - 1] || firstTds[2];
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
      frame.style.left   = (nameR.right - pageR.left) + 'px';
      frame.style.top    = (headBottom - pageR.top) + 'px';
      frame.style.height = (scrR.bottom - headBottom) + 'px';
      frame.style.width  = '0px';
    }
  }

  if (scroller) {
    const onScroll = () => {
      const sx = scroller.scrollLeft > 0;
      scroller.classList.toggle('scrolled', sx);
      positionFrames();
      if (frame) frame.classList.toggle('visible', sx);
    };
    // rAF-throttle: positionFrames() reads layout (getBoundingClientRect),
    // so running it on every raw scroll event caused jank.
    let ticking = false;
    const onScrollRaf = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        try { onScroll(); } finally { ticking = false; }
      });
    };
    scroller.addEventListener('scroll', onScrollRaf, { passive: true });
    window.addEventListener('resize', onScrollRaf, { passive: true });

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
        onScroll();
      };
      viewSel.addEventListener('change', applyView);
      applyView();            // initial pass (Standard)
    } else {
      recomputeCatColspans();
    }
    onScroll();
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
  const headers = [...table.querySelectorAll('thead th')];

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
      const sorted = cells.slice().sort((a, b) => a.v - b.v);
      const rankMap = new Map();
      sorted.forEach((c, i) => rankMap.set(c, i));
      const last = sorted.length - 1;
      cells.forEach(c => {
        let t = rankMap.get(c) / last;     // [0, 1] by rank
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
    if (!pool.length) return;                  // all revealed (keep ticking cheaply)
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
  setInterval(spotlightOnce, 2500);

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

// ---- MANA ITEMS tile: hover plays a one-shot FILL (empty→half), then loops the
// wave at that level. Two GIFs swapped via JS — a single GIF can't play an intro
// once and then loop only its tail. Reverts to the static bottle on mouse-out.
(function () {
  const tile = document.querySelector('.inv-cell-mana');
  if (!tile) return;
  const img = tile.querySelector('.inv-icon');
  if (!img) return;
  const PNG = img.getAttribute('src');
  const FILL = 'icons/ui/gothic/icon_mana_fill.gif';
  const WAVE = 'icons/ui/gothic/icon_mana.gif';
  const FILL_MS = 11 * 150;            // fill GIF: 11 frames × 150ms
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
    function posFromX(clientX) {
      const r = stage.getBoundingClientRect();
      if (r.width <= 0) return pos;
      return ((clientX - r.left) / r.width) * 100;
    }
    handle.addEventListener('pointerdown', function(e) {
      dragging = true;
      if (e.pointerId != null && handle.setPointerCapture) {
        try { handle.setPointerCapture(e.pointerId); } catch (_) {}
      }
      e.preventDefault();
      e.stopPropagation();
    });
    handle.addEventListener('pointermove', function(e) {
      if (dragging) apply(posFromX(e.clientX));
    });
    handle.addEventListener('pointerup', function() { dragging = false; });
    handle.addEventListener('pointercancel', function() { dragging = false; });
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
    }
    function placeLens(cx, cy) {
      if (!lensOk) return;
      const R = lens.offsetWidth / 2;
      lens.style.transform = 'translate(' + (cx - R) + 'px,' + (cy - R) + 'px)';
      const tf = 'translate(' + (R - cx * ZOOM) + 'px,' + (R - cy * ZOOM) + 'px)';
      lensOld.style.transform = tf;
      lensNew.style.transform = tf;
      lensMarkers.forEach(function(el) { el.style.transform = tf; });
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
        placeLens(xy[0], xy[1]);
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
