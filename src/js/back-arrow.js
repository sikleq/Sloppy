
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
  } else if (back && fromParam === 'unit_changes') {
    // Arrived from the Unit Changes index (a summon card links to its parent
    // hero's page). Point the back arrow there instead of Hero Changes.
    back.href = '../unit_changes.html';
    back.title = 'Back to Unit Changes';
    back.setAttribute('aria-label', 'Back to Unit Changes');
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
  } else if (back && fromParam && /^terrain_[0-9a-z]+$/.test(fromParam)) {
    // Arrived from a Terrain page's patch label: back to that map.
    back.href = '../' + fromParam + '.html';
    back.title = 'Back to Terrain';
    back.setAttribute('aria-label', 'Back to the Terrain map');
    back.classList.add('visible');
  } else if (back && fromParam && /^(hero|item):[a-z0-9-]+$/.test(fromParam)) {
    // Arrived from a Hero / Item Changes page: go back to it (same patch section).
    const [kind, slug] = fromParam.split(':');
    const pv = (window.location.pathname.match(/(\d+\.\d+[a-z]?)\.html$/) || [])[1];
    back.href = '../' + (kind === 'hero' ? 'heroes' : 'items') + '/' + slug + '.html' + (pv ? '#p-' + pv : '');
    back.title = 'Back to all changes';
    back.setAttribute('aria-label', 'Back to all changes of this ' + kind);
    back.classList.add('visible');
  } else if (back && fromParam && /^\d+\.\d+[a-z]?$/.test(fromParam) && document.body.classList.contains('entity-page')) {
    // On a Changes page, arrived from a patch page: return to that entity in that patch.
    back.href = '../patches/' + fromParam + '.html#' + (document.body.dataset.ecEid || '');
    back.title = 'Back to ' + fromParam;
    back.setAttribute('aria-label', 'Back to patch ' + fromParam);
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
