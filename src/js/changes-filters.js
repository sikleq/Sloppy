
// ---- HERO / ITEM CHANGES page: "Show: General/Abilities/…" + "Ability: <name>" filters ----
(function() {
  const scopeBtns = [...document.querySelectorAll('.ec-scope-btn[data-ec-scope]')];
  const abBtns = [...document.querySelectorAll('.ec-ab-btn[data-ec-ability]')];
  if (!scopeBtns.length && !abBtns.length) return;
  const scopes = new Set(), abilities = new Set();
  // a renamed block "Old→New" answers to the chip "New"
  const titleOf = blk => { const t = blk.querySelector('.ability-title'); return t ? t.textContent.trim().split('→').pop().trim() : ''; };
  const parentOfSlug = {};
  (window.SLOPPY_ABILITY_TREES || []).forEach(t => t.children.forEach(c => { parentOfSlug[c] = t.parent; }));
  const viaParent = blk => {
    const img = blk.querySelector('img[data-slug]');
    const parent = img && parentOfSlug[img.dataset.slug];
    if (!parent) return false;
    const scope = blk.closest('section.ec-patch') || document;
    const pimg = scope.querySelector('img[data-slug="' + parent + '"]');
    const pblk = pimg && pimg.closest('.ability-block');
    return !!pblk && abilities.has(titleOf(pblk));
  };
  const apply = () => {
    // "innate" is a pseudo-scope: it selects innate ability blocks wherever they sit;
    // "shard" / "scepter" select the rows an Aghanim upgrade changes (abilities, talents, facets)
    const PSEUDO = ['innate', 'shard', 'scepter'];
    const realScopes = new Set([...scopes].filter(x => !PSEUDO.includes(x)));
    const wantInnate = scopes.has('innate');
    const aghs = ['shard', 'scepter'].filter(x => scopes.has(x));
    const aghsSel = aghs.map(a => `li.aghanim-${a}, .ability-change-row.aghanim-${a}`).join(', ');
    document.querySelectorAll('.ec-aghs-hide').forEach(x => x.classList.remove('ec-aghs-hide'));
    document.querySelectorAll('.ec-scope').forEach(sc => {
      let any = false;
      sc.querySelectorAll('.ability-block').forEach(blk => {
        const innate = blk.classList.contains('is-innate');
        const baseOk = !scopes.size || realScopes.has(sc.dataset.scope) || (wantInnate && innate);
        const aghsRows = aghs.length ? [...blk.querySelectorAll(aghsSel)] : [];
        const viaAghs = !baseOk && aghsRows.length > 0;
        if (viaAghs)            // chosen only for its Aghanim rows: the other rows step aside
          blk.querySelectorAll('ul.changes > li').forEach(li => { if (!aghsRows.includes(li)) li.classList.add('ec-aghs-hide'); });
        const scopeOk = baseOk || viaAghs;
        // an active innate (Invoke) has a chip of its own: its block answers to it like any ability;
        // a child of an ability tree (Earth Brewling) answers to its parent's chip (Primal Split)
        let ok = scopeOk && (!abilities.size || abilities.has(titleOf(blk)) || viaParent(blk));
        // talents block: with an ability chip active, keep only the rows that upgrade that ability
        // an innate block whose rows name another ability (Galvanized: "Leveling up Ball Lightning ...")
        // answers to that ability's chip with those rows only, like talents
        const rowFilter = blk.classList.contains('talents-block')
          || (innate && abilities.size > 0 && !abilities.has(titleOf(blk)));
        // rows hidden by an EARLIER chip come back first: Quas hid Invoke's rows, then Invoke showed an
        // empty Invoke block (owner 2026-09-26)
        if (!rowFilter) blk.querySelectorAll('li.ec-scope-hide').forEach(li => li.classList.remove('ec-scope-hide'));
        const rows = rowFilter ? [...blk.querySelectorAll('li')] : [];
        if (rows.length) {
          let anyRow = false;
          rows.forEach(li => {
            const abs = (li.dataset.ecAb || '').split('|').filter(Boolean);
            const rowOk = !abilities.size || abs.some(a => abilities.has(a));
            li.classList.toggle('ec-scope-hide', abilities.size > 0 && !rowOk);
            // a row the Shard / Scepter filter already hid does not keep the block alive
            anyRow = anyRow || (rowOk && !li.classList.contains('ec-aghs-hide'));
          });
          ok = scopeOk && anyRow;
        }
        blk.classList.toggle('ec-scope-hide', !ok);
        any = any || ok;
      });
      sc.classList.toggle('ec-scope-hide', !any);
    });
    // a patch with nothing left to show collapses entirely
    document.querySelectorAll('section.ec-patch').forEach(sec => {
      const parts = sec.querySelectorAll('.ec-scope');
      sec.classList.toggle('ec-scope-hide',
        (scopes.size > 0 || abilities.size > 0) && parts.length > 0 && [...parts].every(x => x.classList.contains('ec-scope-hide')));
    });
  };
  const wire = (btns, set, key) => btns.forEach(b => b.addEventListener('click', () => {
    const k = b.dataset[key];
    if (set.has(k)) set.delete(k); else set.add(k);
    b.classList.toggle('active', set.has(k));
    apply();
  }));
  wire(scopeBtns, scopes, 'ecScope');
  wire(abBtns, abilities, 'ecAbility');
  // Deep-link: ?ability=<name> (e.g. from a summon card on the Unit Changes
  // page) pre-activates that ability filter so only its changes show. If the
  // name matches no chip, nothing is filtered (all changes stay visible).
  const preAbility = new URLSearchParams(window.location.search).get('ability');
  if (preAbility) {
    const target = abBtns.find(b => b.dataset.ecAbility === preAbility);
    if (target) {
      abilities.add(preAbility);
      target.classList.add('active');
      apply();
      target.scrollIntoView({ block: 'center' });
    }
  }
})();
