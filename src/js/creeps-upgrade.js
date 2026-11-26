
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
      // Nuke's "−Armor" box comes off the armor the table shows too, and so off its physical resistance and EHP
      // (owner 2026-11-26: "в столбцах с броней тоже надо отнимать значение и пересчитывать Phys. resist")
      const cut = nukeVal(nukeArmor);
      const armorOn = on || cut ? 1 : 0;
      const pct = 0.06 * (armor - cut) / (1 + 0.06 * Math.abs(armor - cut));
      const pctEff = 0.06 * (armorEff - cut) / (1 + 0.06 * Math.abs(armorEff - cut));
      put(tr, 'hp', hp, 0, on);
      put(tr, 'armor', armor - cut, 1, armorOn);
      put(tr, 'armor_pct', Math.round(pct * 100), 0, armorOn);
      if (armorOn) { const td = cell(tr, 'armor_pct'); if (td && td.dataset.base) td.textContent += '%'; }
      put(tr, 'as', as, 0, on);
      put(tr, 't_per_attack', bat / (as / 100), 2, on);
      // EHP with the unit's own aura even at step 0 (the build wrote them from its numbers without it)
      const ownAura = own(tr, 'hp', hp) || own(tr, 'armor', armor) || own(tr, 'magres', base(tr, 'magres'));
      put(tr, 'ehp_phys', hpEff / (1 - pctEff), 0, on || ownAura || cut ? 1 : 0);
      if (isFinite(mrEff)) put(tr, 'ehp_mag', hpEff / (1 - mrEff), 0, on || aura || ownAura ? 1 : 0);
      nukeCell(cell(tr, 'hp'), hpEff, armorEff, mrEff);
      // Timeline view: the same test on every step's HP cell (its armor and the flagbearer's aura at that step)
      for (let i = 0; i <= 8; i++) {
        const th = cell(tr, 'tl_hp_' + i), ta = cell(tr, 'tl_armor_' + i);
        if (!th) continue;
        const am = aura ? AURA.step * Math.min(i, AURA.max) / 100 : 0;
        // the step's armor less "−Armor" on show; Nuke takes the box off by itself, so it reads the build's number
        if (ta) {
          if (ta.dataset.base === undefined) ta.dataset.base = ta.textContent.trim();
          const b = num(ta.dataset.base);
          ta.textContent = cut && isFinite(b) ? fmt(b - cut, 1) : ta.dataset.base;
          ta.classList.toggle('upg-on', !!cut && isFinite(b));
        }
        const hi = num(th.textContent), ai = ta ? num(ta.dataset.base) : 0;
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
    waves();
  }
  // What step L adds to a row. Neutrals: neutral_upgrade above. Lane creeps (data-upg, builders/creeps.py
  // LANE_UPGRADE; owner 2026-11-26 "правила другие, не как у нейтралов"): flat per step, HP and damage stop at
  // "cap" steps, gold (min and max alike) and XP do not; no armor or attack speed. A lane creep without data-upg
  // does not grow.
  function rule(tr, L) {
    // neutral_upgrade unless the row carries its own rule (lane creeps; hero summons carry "{}": no growth)
    if (tr.dataset.group !== 'lane' && tr.dataset.upg === undefined) {
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
  const nukeMag = document.getElementById('nuke-mag'), nukePhys = document.getElementById('nuke-phys');
  const nukePure = document.getElementById('nuke-pure');      // pure: nothing blocks it
  // armor reduction (owner 2026-11-26): taken off the armor before the physical part; armor may go below zero
  const nukeArmor = document.getElementById('nuke-armor');
  const nukeVal = el => { const v = Math.round(Number(el && el.value)); return isFinite(v) && v > 0 ? v : 0; };
  // what the boxes do to a unit: null when they are empty, else the damage after armor / resistance
  function nukeHit(armor, mr) {
    const mag = nukeVal(nukeMag), phys = nukeVal(nukePhys), pure = nukeVal(nukePure);
    if (!(mag || phys || pure)) return null;
    const a = (isFinite(armor) ? armor : 0) - nukeVal(nukeArmor), m = isFinite(mr) ? mr : 0;
    const physTaken = phys * (1 - 0.06 * a / (1 + 0.06 * Math.abs(a)));
    const magTaken = mag * (1 - m);
    return {mag, phys, pure, a, physTaken, magTaken, dealt: physTaken + magTaken + pure};
  }
  // the hint's last words: how much HP is left, or by how much the damage overshoots (owner 2026-11-26:
  // "надо в всплывающей подсказке показывать, сколько ХП остается")
  const hpLeft = (dealt, hp) => dealt >= hp ? `dies (${Math.round(dealt - hp)} over)` : `${Math.round(hp - dealt)} HP left`;
  function nukeCell(td, hp, armor, mr) {
    if (!td) return;
    const h = isFinite(hp) ? nukeHit(armor, mr) : null;
    td.classList.toggle('nuke-live', false);
    td.classList.toggle('nuke-dead', false);
    if (!h) { if (td.dataset.nukeTitle !== undefined) { td.removeAttribute('title'); delete td.dataset.nukeTitle; } return; }
    td.classList.toggle(h.dealt >= hp ? 'nuke-dead' : 'nuke-live', true);
    td.dataset.nukeTitle = '';
    const blocked = Math.round(h.phys - h.physTaken);     // armor below zero adds damage instead
    td.title = `Physical ${h.phys} → ${Math.round(h.physTaken)} (armor ${fmt(h.a, 1)} ` +
               `${blocked >= 0 ? 'blocks ' + blocked : 'adds ' + -blocked}), ` +
               `magic ${h.mag} → ${Math.round(h.magTaken)} (resistance blocks ${Math.round(h.mag - h.magTaken)}), ` +
               `pure ${h.pure}: ${Math.round(h.dealt)} of ${Math.round(hp)} HP, ${hpLeft(h.dealt, hp)}`;
  }
  // always open (owner 2026-11-26): it counts once a box holds a number
  [nukeMag, nukePhys, nukePure, nukeArmor].forEach(el => el && el.addEventListener('input', () => {
    const v = el.value.replace(/[^0-9]/g, '');
    if (v !== el.value) el.value = v;
    apply();
  }));
  // ---- View: Waves (owner 2026-11-26; builders/creeps_waves.py) ----
  // One row per wave make-up, the wave sums at every 7:30 step like Timeline. The numbers are the lane rows' of the
  // Creeps choice (Normal / Super / Mega) at that step, by the same rule() as the table. A make-up with a flagbearer
  // has its Inspiration Aura on every unit (in the game it reaches its own wave); the aura button puts it on all.
  // A click on any unit's icon greys it and leaves it out of THAT row's sums (owner 2026-11-26: "выключать дать
  // возможность любой тип крипа … и не во всех строках сразу, а там где выключил"). Nuke: each HP cell red when the whole wave dies, yellow when part of it,
  // green when none; its hint says how many ("4/6").
  const wavesTable = document.querySelector('.waves-table');
  const tierSel = document.getElementById('lane-tier');
  const WAVE_KINDS = {melee: 'lane_melee', flag: 'lane_flagbearer', ranged: 'lane_ranged', siege: 'lane_siege'};
  function unitAt(tr, L, auraMr) {
    const r = rule(tr, L);
    const hp = base(tr, 'hp') + r.hp, armor = base(tr, 'armor') + r.armor;
    const mrOwn = (base(tr, 'magres') + own(tr, 'magres', base(tr, 'magres'))) / 100;
    return {hp: hp + own(tr, 'hp', hp), armor: armor + own(tr, 'armor', armor),
            mr: 1 - (1 - (isFinite(mrOwn) ? mrOwn : 0)) * (1 - auraMr),
            dmg: base(tr, 'dmg_avg') + r.dmg, as: base(tr, 'as') + r.as,
            gold: (base(tr, 'gold_min') + r.gmin + base(tr, 'gold_max') + r.gmax) / 2,
            xp: base(tr, 'xp') + r.xp};
  }
  function waves() {
    if (!wavesTable) return;
    const tier = tierSel ? tierSel.value : 'normal';
    const rowOf = {};
    Object.entries(WAVE_KINDS).forEach(([k, id]) => {
      rowOf[k] = document.getElementById('unit-' + id + (tier === 'normal' ? '' : '_' + tier));
    });
    wavesTable.querySelectorAll('tbody tr').forEach(tr => {
      const off = new Set((tr.dataset.off || '').split(' ').filter(Boolean));
      // the flagbearer's aura only while it is in the wave (a flagbearer switched off takes its aura with it)
      const hasFlag = Number(tr.dataset.flag) > 0 && !off.has('flag');
      tr.querySelectorAll('.wv-unit').forEach(ch => ch.classList.toggle('wv-off', off.has(ch.dataset.kind)));
      for (let L = 0; L <= 8; L++) {
        const auraMr = (hasFlag || auraOn()) && AURA ? AURA.step * Math.min(L, AURA.max) / 100 : 0;
        // HP / damage / gold / XP: the wave's sums; armor and attack speed: the mean over its units
        const sum = {hp: 0, armor: 0, dmg: 0, as: 0, gold: 0, xp: 0};
        let units = 0, killed = 0, nukeOn = false;
        const lines = [];      // the hint: each kind's HP left after the nuke
        Object.keys(WAVE_KINDS).forEach(k => {
          const n = Number(tr.dataset[k]) || 0;
          if (!n || !rowOf[k] || off.has(k)) return;
          const u = unitAt(rowOf[k], L, auraMr);
          Object.keys(sum).forEach(s => { sum[s] += n * (isFinite(u[s]) ? u[s] : 0); });
          units += n;
          const h = nukeHit(u.armor, u.mr);
          if (!h) return;
          nukeOn = true;
          if (h.dealt >= u.hp) killed += n;
          const label = rowOf[k].querySelector('td.col-name');
          lines.push(`${(label ? label.textContent.trim() : k)}${n > 1 ? ' ×' + n : ''}: ` +
                     `${Math.round(h.dealt)} of ${Math.round(u.hp)} HP, ${hpLeft(h.dealt, u.hp)}`);
        });
        Object.keys(sum).forEach(s => {
          const td = tr.querySelector(`td.wv-${s}-${L}`);
          if (!td) return;
          if (s === 'armor') {      // the wave's mean armor less Nuke's "−Armor"
            const cut = nukeVal(nukeArmor);
            td.textContent = units ? fmt(sum.armor / units - cut, 1) : '';
            td.classList.toggle('upg-on', !!cut);
          }
          else if (s === 'as') td.textContent = units ? Math.round(sum.as / units) : '';
          else td.textContent = Math.round(sum[s]);
        });
        const hc = tr.querySelector(`td.wv-hp-${L}`);
        if (!hc) continue;
        hc.classList.remove('nuke-dead', 'nuke-live', 'nuke-part');
        if (nukeOn) {
          hc.classList.add(killed === units ? 'nuke-dead' : killed ? 'nuke-part' : 'nuke-live');
          hc.title = `${killed}/${units} die\n` + lines.join('\n');
        } else hc.removeAttribute('title');
      }
    });
  }
  if (wavesTable) {
    wavesTable.addEventListener('click', e => {
      const chip = e.target.closest('.wv-unit');
      if (!chip) return;
      const tr = chip.closest('tr');
      const off = new Set((tr.dataset.off || '').split(' ').filter(Boolean));
      if (off.has(chip.dataset.kind)) off.delete(chip.dataset.kind); else off.add(chip.dataset.kind);
      tr.dataset.off = [...off].join(' ');
      waves();
    });
  }
  if (tierSel) tierSel.addEventListener('change', waves);
  input.addEventListener('input', apply);
  input.addEventListener('change', apply);
  apply();
})();
