
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
    const dl = selfAura(td, v);
    td.textContent = !L ? td.dataset.base : (dl ? `${fmt(v, d)} (${fmt(v + dl, d)})` : fmt(v, d));
    // gold only where the number really changed (a Mega row at step 0 keeps its armor, speed, gold…)
    td.classList.toggle('upg-on', !!L && td.textContent !== td.dataset.base);
  };
  // A cell "own (with its own aura)" — a neutral whose aura buffs itself (builders/creeps.py AURA_SELF): how much its
  // own aura adds, read from the build's two numbers (owner 2026-11-26: Nuke has to count Centaur Courser's 20%)
  // v = the unit's own number now (after the upgrade); a % aura (data-self-mul, builders/creeps.py) scales it, a flat
  // one adds what it added at base (Fable 5.2 review 2026-11-26: Granite Golem's +16% HP was added flat)
  function selfAura(td, v) {
    if (!td) return 0;
    if (td.dataset.base === undefined) td.dataset.base = td.textContent.trim();
    const parts = td.dataset.base.split('(');
    if (parts.length < 2) return 0;
    const mul = num(td.dataset.selfMul);
    if (isFinite(mul) && isFinite(v)) return v * (mul - 1);
    const dl = num(parts[1]) - num(parts[0]);
    return isFinite(dl) ? dl : 0;
  }
  const own = (tr, k, v) => selfAura(cell(tr, k), v);
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
      // what the unit really has: its own aura included ("0% (20%)" -> 20%) — for EHP and Nuke
      const mrOwn = (base(tr, 'magres') + own(tr, 'magres', base(tr, 'magres'))) / 100;
      const mrEff = 1 - (1 - mrOwn) * (1 - auraMr);
      const hpEff = hp + own(tr, 'hp', hp), armorEff = armor + own(tr, 'armor', armor);
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
      const pctEff = 0.06 * armorEff / (1 + 0.06 * Math.abs(armorEff));
      put(tr, 'hp', hp, 0, on);
      put(tr, 'armor', armor, 1, on);
      put(tr, 'armor_pct', Math.round(pct * 100), 0, on);
      if (on) { const td = cell(tr, 'armor_pct'); if (td) td.textContent += '%'; }
      put(tr, 'as', as, 0, on);
      put(tr, 't_per_attack', bat / (as / 100), 2, on);
      // EHP with the unit's own aura even at step 0 (the build wrote them from its numbers without it)
      const ownAura = own(tr, 'hp', hp) || own(tr, 'armor', armor) || own(tr, 'magres', base(tr, 'magres'));
      put(tr, 'ehp_phys', hpEff / (1 - pctEff), 0, on || ownAura ? 1 : 0);
      if (isFinite(mrEff)) put(tr, 'ehp_mag', hpEff / (1 - mrEff), 0, on || aura || ownAura ? 1 : 0);
      nukeCell(cell(tr, 'hp'), hpEff, armorEff, mrEff);
      // Timeline view: the same test on every step's HP cell (its armor and the flagbearer's aura at that step)
      for (let i = 0; i <= 8; i++) {
        const th = cell(tr, 'tl_hp_' + i), ta = cell(tr, 'tl_armor_' + i);
        if (!th) continue;
        const am = aura ? AURA.step * Math.min(i, AURA.max) / 100 : 0;
        const hi = num(th.textContent), ai = ta ? num(ta.textContent) : 0;
        nukeCell(th, hi + own(tr, 'hp', hi), ai + own(tr, 'armor', ai),
                 1 - (1 - mrOwn) * (1 - am));
      }
      put(tr, 'dmg_min', base(tr, 'dmg_min') + r.dmg, 0, on);
      put(tr, 'dmg_max', base(tr, 'dmg_max') + r.dmg, 0, on);
      put(tr, 'dmg_avg', base(tr, 'dmg_avg') + r.dmg, 1, on);
      const gmin = base(tr, 'gold_min') + r.gmin, gmax = base(tr, 'gold_max') + r.gmax;
      put(tr, 'gold_min', gmin, 0, on);
      put(tr, 'gold_max', gmax, 0, on);
      put(tr, 'gold', Math.ceil((gmin + gmax) / 2), 0, on);   // rounded up, as the build writes the column
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
  const nukePure = document.getElementById('nuke-pure');      // pure: nothing blocks it
  const nukeVal = el => { const v = Math.round(Number(el && el.value)); return isFinite(v) && v > 0 ? v : 0; };
  function nukeCell(td, hp, armor, mr) {
    if (!td) return;
    const mag = nukeVal(nukeMag), phys = nukeVal(nukePhys), pure = nukeVal(nukePure);
    const on = !!(nukeToggle && nukeToggle.checked) && (mag || phys || pure) && isFinite(hp);
    td.classList.toggle('nuke-live', false);
    td.classList.toggle('nuke-dead', false);
    if (!on) { if (td.dataset.nukeTitle !== undefined) { td.removeAttribute('title'); delete td.dataset.nukeTitle; } return; }
    const a = isFinite(armor) ? armor : 0, m = isFinite(mr) ? mr : 0;
    const physTaken = phys * (1 - 0.06 * a / (1 + 0.06 * Math.abs(a)));
    const magTaken = mag * (1 - m);
    const dealt = physTaken + magTaken + pure;
    td.classList.toggle(dealt >= hp ? 'nuke-dead' : 'nuke-live', true);
    td.dataset.nukeTitle = '';
    td.title = `Physical ${phys} → ${Math.round(physTaken)} (armor blocks ${Math.round(phys - physTaken)}), ` +
               `magic ${mag} → ${Math.round(magTaken)} (resistance blocks ${Math.round(mag - magTaken)}), ` +
               `pure ${pure}: ` +
               `${Math.round(dealt)} of ${Math.round(hp)} HP`;
  }
  if (nukeToggle) {
    nukeToggle.addEventListener('change', () => {
      if (nukeFields) nukeFields.classList.toggle('nuke-off', !nukeToggle.checked);   // invisible, its place kept
      apply();
    });
    [nukeMag, nukePhys, nukePure].forEach(el => el && el.addEventListener('input', () => {
      const v = el.value.replace(/[^0-9]/g, '');
      if (v !== el.value) el.value = v;
      apply();
    }));
  }
  input.addEventListener('input', apply);
  input.addEventListener('change', apply);
  apply();
})();
