
// ---- HERO / ITEM CHANGES index: name filter (comma-separated, partial) ----
(function() {
  const input = document.querySelector('[data-ec-search]');
  if (!input) return;
  const cards = [...document.querySelectorAll('.ec-card')];
  const showOld = document.getElementById('ec-show-old');     // items only: removed / cycled-out
  const classBtns = [...document.querySelectorAll('[data-ec-class]')];   // Shop / Neutral / Enchantments
  const classes = new Set();
  const apply = () => {
    const terms = input.value.toLowerCase().split(',').map(s => s.trim()).filter(Boolean);
    cards.forEach(c => {
      const n = c.dataset.name || '';
      const old = c.dataset.current === '0' && !(showOld && showOld.checked);
      const wrongClass = classes.size > 0 && !classes.has(c.dataset.class || '');
      c.hidden = old || wrongClass || (terms.length > 0 && !terms.some(t => n.includes(t)));
    });
    // a shop category / neutral tier / attribute column with nothing left collapses
    document.querySelectorAll('.ec-igroup, .ec-hcol').forEach(g => {
      g.hidden = ![...g.querySelectorAll('.ec-card')].some(c => !c.hidden);
    });
    document.querySelectorAll('.ec-group').forEach(g => {
      g.hidden = ![...g.querySelectorAll('.ec-card')].some(c => !c.hidden);
    });
  };
  input.addEventListener('input', apply);
  if (showOld) showOld.addEventListener('change', apply);
  classBtns.forEach(b => b.addEventListener('click', () => {
    const k = b.dataset.ecClass;
    if (classes.has(k)) classes.delete(k); else classes.add(k);
    b.classList.toggle('active', classes.has(k));
    b.setAttribute('aria-pressed', classes.has(k) ? 'true' : 'false');
    apply();
  }));
  // once at load too: "Removed neutrals" showed its heading over cards hidden from the start (audit 2026-11-08)
  apply();
})();
