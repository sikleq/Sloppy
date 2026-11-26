
// ---- NEUTRAL STATS: a neutral creep's stats at upgrade N (owner 2026-11-23) ----
// neutral_upgrade (server.dll 6989, read by the IDA researcher): every 450 s of game time from the horn, max 30 steps,
// each step FLAT: +3 damage (min and max), +5 attack speed, +0.5 armor, +30 HP, +4 XP; gold min += floor(L/2),
// max += floor((L+1)/2). The cells keep their base value in data-base; the derived ones (attack interval, armor %,
// EHP) are worked out again from the new numbers.
(function() {
  const table = document.querySelector('.creeps-table');
  const input = document.getElementById('upgrade-step');
  if (!table || !input) return;
  const time = document.getElementById('upgrade-time');
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
    time.textContent = Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
    table.querySelectorAll('tbody tr').forEach(tr => {
      if (!cell(tr, 'hp')) return;
      const r = rule(tr, L);
      const hp = base(tr, 'hp') + r.hp;
      const armor = base(tr, 'armor') + r.armor;
      const as = base(tr, 'as') + r.as;
      const bat = base(tr, 'bat');
      const mr = base(tr, 'magres') / 100;
      const pct = 0.06 * armor / (1 + 0.06 * Math.abs(armor));
      put(tr, 'hp', hp, 0, L);
      put(tr, 'armor', armor, 1, L);
      put(tr, 'armor_pct', Math.round(pct * 100), 0, L);
      if (L) { const td = cell(tr, 'armor_pct'); if (td) td.textContent += '%'; }
      put(tr, 'as', as, 0, L);
      put(tr, 't_per_attack', bat / (as / 100), 2, L);
      put(tr, 'ehp_phys', hp / (1 - pct), 0, L);
      if (isFinite(mr)) put(tr, 'ehp_mag', hp / (1 - mr), 0, L);
      put(tr, 'dmg_min', base(tr, 'dmg_min') + r.dmg, 0, L);
      put(tr, 'dmg_max', base(tr, 'dmg_max') + r.dmg, 0, L);
      put(tr, 'dmg_avg', base(tr, 'dmg_avg') + r.dmg, 1, L);
      const gmin = base(tr, 'gold_min') + r.gmin, gmax = base(tr, 'gold_max') + r.gmax;
      put(tr, 'gold_min', gmin, 0, L);
      put(tr, 'gold_max', gmax, 0, L);
      put(tr, 'gold', (gmin + gmax) / 2, 1, L);
      put(tr, 'xp', base(tr, 'xp') + r.xp, 0, L);
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
    const c = Math.min(L, u.cap === undefined ? L : u.cap);
    const g = (u.gold || 0) * L;
    return {hp: (u.hp || 0) * c, armor: 0, as: 0, dmg: (u.dmg || 0) * c, xp: (u.xp || 0) * L, gmin: g, gmax: g};
  }
  input.addEventListener('input', apply);
  input.addEventListener('change', apply);
  apply();
})();
