
// ---- NEUTRAL STATS: a neutral creep's stats at upgrade N (owner 2026-11-23) ----
// neutral_upgrade (server.dll 6989, read by the IDA researcher): every 450 s of game time from the horn, max 30 steps,
// each step FLAT: +3 damage (min and max), +5 attack speed, +0.5 armor, +30 HP, +4 XP; gold min += floor(L/2),
// max += floor((L+1)/2). The cells keep their base value in data-base; the derived ones (attack interval, armor %,
// EHP) are worked out again from the new numbers.
(function() {
  const table = document.querySelector('.creeps-table');
  const input = document.getElementById('upgrade-step');
  if (!table || !input) return;
  const MAX = 30, STEP_S = 450;
  const num = s => parseFloat(String(s).replace(/\s/g, '').replace(',', '.'));
  const fmt = (v, d) => {
    let s = v.toFixed(d);
    if (d && s.indexOf('.') >= 0) s = s.replace(/0+$/, '').replace(/\.$/, '');
    return s.replace('.', ',');
  };
  const cell = (tr, k) => tr.querySelector('td.col-' + k);
  const base = (tr, k) => {
    const td = cell(tr, k);
    if (!td) return NaN;
    if (td.dataset.base === undefined) td.dataset.base = td.textContent.trim();
    return num(td.dataset.base);
  };
  const put = (tr, k, v, d, L) => {
    const td = cell(tr, k);
    if (!td) return;
    if (td.dataset.base === undefined) td.dataset.base = td.textContent.trim();
    if (L && !isFinite(v)) return;
    td.textContent = L ? fmt(v, d) : td.dataset.base;
    td.classList.toggle('upg-on', !!L);
  };
  function apply() {
    let L = Math.round(Number(input.value));
    if (!isFinite(L) || L < 0) L = 0;
    if (L > MAX) L = MAX;
    if (String(L) !== input.value) input.value = L;
    const s = L * STEP_S;
    // the step's game time: the box's hover hint (site tooltip, tooltips.js .tb-tip-target)
    input.setAttribute('data-tooltip', Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'));
    table.querySelectorAll('tbody tr').forEach(tr => {
      if (!cell(tr, 'hp')) return;
      const r = rule(tr, L);
      const on = L || r.on ? 1 : 0;      // a mega row differs from its KV numbers even at step 0
      const hp = base(tr, 'hp') + r.hp;
      const armor = base(tr, 'armor') + r.armor;
      const as = base(tr, 'as') + r.as;
      const bat = base(tr, 'bat');
      // Inspiration Aura (the flagbearer's): +HP regen; magic resistance +step% per 7:30 step up to its maximum,
      // stacked with the unit's own as resistances do: 1 - (1 - own)(1 - aura). On EVERY row (owner 2026-11-26:
      // "давай сделаем, чтобы их тоже учитывала" — in the game it only reaches its own team's creeps, not neutrals).
      // A cell showing "own (with its own aura)" gets the flagbearer's aura on both numbers.
      const aura = auraOn();
      const auraMr = aura ? AURA.step * Math.min(L, AURA.max) / 100 : 0;
      const mr = 1 - (1 - base(tr, 'magres') / 100) * (1 - auraMr);
      ['hp_regen', 'magres'].forEach(k => {
        const td = cell(tr, k);
        if (!td) return;
        if (td.dataset.base === undefined) td.dataset.base = td.textContent.trim();
        const parts = td.dataset.base.split('(').map(num);
        if (!aura || !isFinite(parts[0])) {
          td.textContent = td.dataset.base;
          td.classList.remove('upg-on');           // only the aura changes these two cells
        } else {
          const f = k === 'hp_regen' ? v => (v + AURA.regen).toFixed(2).replace('.', ',')    // "0,50" like the table
                                     : v => Math.round((1 - (1 - v / 100) * (1 - auraMr)) * 100) + '%';
          td.textContent = parts.length > 1 && isFinite(parts[1]) ? `${f(parts[0])} (${f(parts[1])})` : f(parts[0]);
          td.classList.add('upg-on');
        }
        if (k === 'hp_regen') td.classList.toggle('regen-zero', td.textContent.trim() === '0');   // grey only at zero
      });
      const pct = 0.06 * armor / (1 + 0.06 * Math.abs(armor));
      put(tr, 'hp', hp, 0, on);
      put(tr, 'armor', armor, 1, on);
      put(tr, 'armor_pct', Math.round(pct * 100), 0, on);
      if (on) { const td = cell(tr, 'armor_pct'); if (td) td.textContent += '%'; }
      put(tr, 'as', as, 0, on);
      put(tr, 't_per_attack', bat / (as / 100), 2, on);
      put(tr, 'ehp_phys', hp / (1 - pct), 0, on);
      if (isFinite(mr)) put(tr, 'ehp_mag', hp / (1 - mr), 0, on || aura ? 1 : 0);
      nukeCell(tr, hp, armor, mr);
      put(tr, 'dmg_min', base(tr, 'dmg_min') + r.dmg, 0, on);
      put(tr, 'dmg_max', base(tr, 'dmg_max') + r.dmg, 0, on);
      put(tr, 'dmg_avg', base(tr, 'dmg_avg') + r.dmg, 1, on);
      const gmin = base(tr, 'gold_min') + r.gmin, gmax = base(tr, 'gold_max') + r.gmax;
      put(tr, 'gold_min', gmin, 0, on);
      put(tr, 'gold_max', gmax, 0, on);
      put(tr, 'gold', (gmin + gmax) / 2, 1, on);
      put(tr, 'xp', base(tr, 'xp') + r.xp, 0, on);
    });
  }
  // What step L adds to a row. Neutrals: neutral_upgrade above. Lane creeps (data-upg, builders/creeps.py
  // LANE_UPGRADE; owner 2026-11-26 "правила другие, не как у нейтралов"): flat per step, HP and damage stop at
  // "cap" steps, gold (min and max alike) and XP do not; no armor or attack speed. A lane creep without data-upg
  // does not grow.
  function rule(tr, L) {
    if (tr.dataset.group !== 'lane') {
      return {hp: 30 * L, armor: 0.5 * L, as: 5 * L, dmg: 3 * L, xp: 4 * L,
              gmin: Math.floor(L / 2), gmax: Math.floor((L + 1) / 2)};
    }
    let u = {};
    try { u = JSON.parse(tr.dataset.upg || '{}'); } catch (e) { u = {}; }
    // "floor": mega creeps count HP and damage at 30 steps from the start (all six barracks down)
    const c = Math.max(Math.min(L, u.cap === undefined ? L : u.cap), u.floor || 0);
    const g = (u.gold || 0) * L;
    return {hp: (u.hp || 0) * c, armor: 0, as: 0, dmg: (u.dmg || 0) * c, xp: (u.xp || 0) * L, gmin: g, gmax: g,
            on: !!u.floor};
  }
  // ---- Inspiration Aura button ----
  const auraBtn = document.getElementById('flag-aura');
  const AURA = auraBtn ? {regen: num(auraBtn.dataset.regen), step: num(auraBtn.dataset.mrStep),
                          max: num(auraBtn.dataset.mrMax)} : null;
  const auraOn = () => !!(auraBtn && auraBtn.getAttribute('aria-pressed') === 'true');
  if (auraBtn) {
    auraBtn.addEventListener('click', () => {
      const pressed = !auraOn();
      auraBtn.setAttribute('aria-pressed', pressed ? 'true' : 'false');
      auraBtn.classList.toggle('active', pressed);
      apply();
    });
  }
  // ---- Nuke: does the unit survive this much magic + physical damage? (owner 2026-11-26) ----
  // physical after armor: dmg x (1 - 0.06a / (1 + 0.06|a|)); magic after resistance: dmg x (1 - mr). The HP cell
  // turns light green when the unit lives, red when it dies; its title says what armor and resistance blocked.
  const nukeToggle = document.getElementById('nuke-toggle');
  const nukeFields = document.getElementById('nuke-fields');
  const nukeMag = document.getElementById('nuke-mag'), nukePhys = document.getElementById('nuke-phys');
  const nukeVal = el => { const v = Math.round(Number(el && el.value)); return isFinite(v) && v > 0 ? v : 0; };
  function nukeCell(tr, hp, armor, mr) {
    const td = cell(tr, 'hp');
    if (!td) return;
    const mag = nukeVal(nukeMag), phys = nukeVal(nukePhys);
    const on = !!(nukeToggle && nukeToggle.checked) && (mag || phys) && isFinite(hp);
    td.classList.toggle('nuke-live', false);
    td.classList.toggle('nuke-dead', false);
    if (!on) { if (td.dataset.nukeTitle !== undefined) { td.removeAttribute('title'); delete td.dataset.nukeTitle; } return; }
    const a = isFinite(armor) ? armor : 0, m = isFinite(mr) ? mr : 0;
    const physTaken = phys * (1 - 0.06 * a / (1 + 0.06 * Math.abs(a)));
    const magTaken = mag * (1 - m);
    const dealt = physTaken + magTaken;
    td.classList.toggle(dealt >= hp ? 'nuke-dead' : 'nuke-live', true);
    td.dataset.nukeTitle = '';
    td.title = `Physical ${phys} → ${Math.round(physTaken)} (armor blocks ${Math.round(phys - physTaken)}), ` +
               `magic ${mag} → ${Math.round(magTaken)} (resistance blocks ${Math.round(mag - magTaken)}): ` +
               `${Math.round(dealt)} of ${Math.round(hp)} HP`;
  }
  if (nukeToggle) {
    nukeToggle.addEventListener('change', () => {
      if (nukeFields) nukeFields.classList.toggle('nuke-off', !nukeToggle.checked);   // invisible, its place kept
      apply();
    });
    [nukeMag, nukePhys].forEach(el => el && el.addEventListener('input', () => {
      const v = el.value.replace(/[^0-9]/g, '');
      if (v !== el.value) el.value = v;
      apply();
    }));
  }
  input.addEventListener('input', apply);
  input.addEventListener('change', apply);
  apply();
})();
