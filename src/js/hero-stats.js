
// Medusa Mana Shield damage per mana at a hero level, from an innate-rules entry
// (Hero Stats + Hero Lab): dpm_base + dpm_per_level·level, or the old leveled
// ability's dpm_ranks (rank = floor((level + 1) / 2), assumes max rank).
function innateDpm(entry, level) {
  if (Array.isArray(entry.dpm_ranks)) {
    const r = entry.dpm_ranks;
    return r[Math.min(r.length - 1, Math.max(0, Math.floor((level + 1) / 2)))];
  }
  return (Number(entry.dpm_base) || 0) + (Number(entry.dpm_per_level) || 0) * level;
}

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
  const _innateRulesEl = document.getElementById('hs-innate-rules');
  const _innateRules = _innateRulesEl ? JSON.parse(_innateRulesEl.textContent) : {};
  // Attribute constants (HP per Str, armor per Agi, …) come from the page —
  // builders/heroes_stats.py embeds patch/game_constants.for_js(); no numbers here.
  const _constEl = document.getElementById('hs-game-constants');
  const C = _constEl ? JSON.parse(_constEl.textContent) : {};
  const attackBtns = [...document.querySelectorAll('.hs-attack-filter')];
  const attrBtns = [...document.querySelectorAll('.hs-attr-filter[data-attr-filter]')];
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
  // Techies M.A.D.: share of the mana pool as mana regen, from the embedded
  // innate rules (KV bonus_mana_as_mana_regen; followed per patch by the builder).
  const techiesPoolPctAt = level => {
    const e = innateEntry('techies', 'mpr', 'mana_pool_pct_per_level');
    if (!e) return 0;
    const lvl = Math.max(1, Number(level) || 1);
    return e.base_pct + lvl * e.per_level_pct;
  };
  const attrsAt = (s, level, includePlus2) => {
    const bonus = includePlus2 ? plus2CountAt(level) * 2 : 0;
    // Ogre Magi has 0 base Intelligence and cannot gain Int from levels OR from
    // the +2-all-stats level-ups (his innate replaces Int scaling with Strength-
    // based mana) — so the +2 bonus only feeds his Str and Agi, never Int. Before 7.33 (no Dumb Luck) he was normal.
    const intBonus = s.slug === 'ogre_magi' && innateEntry('ogre_magi', 'mp', 'attr_substitution') ? 0 : bonus;
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
  // Returns the active history entry for an effect at the given patch string.
  // Mirrors Python _active_entry() in builders/heroes_stats.py.
  const _activeEntry = (eff, patch) => {
    if (!eff.history) {
      const s = eff.since, u = eff.until;
      if (s && !patchGe(patch, s)) return null;
      if (u && !patchGe(u, patch)) return null;
      return eff;
    }
    for (let i = eff.history.length - 1; i >= 0; i--) {
      const e = eff.history[i];
      if (patchGe(patch, e.since || '7.00')) {
        if (e.until == null || patchGe(e.until, patch)) return e;
      }
    }
    return null;
  };
  // Active entry of one hero's innate effect at the table's patch (null if none) —
  // Techies / Medusa / Void Spirit / Ogre Magi numbers come from here, not from code.
  const innateEntry = (slug, target, formula) => {
    const eff = (_innateRules[slug]?.effects || []).find(e => e.target === target && e.formula === formula);
    const entry = eff ? _activeEntry(eff, hsTablePatch) : null;
    return entry ? { ...eff, ...entry } : null;      // entry fields over the effect's own
  };
  // secondary_attr_factor constants: derived-stat-per-attr unit rates.
  const _SEC = {
    'hpr:str': C.hprStr, 'mpr:int': C.mprInt, 'aspd:agi': C.asAgi, 'armor:agi': C.armorAgi, 'mr:int': C.mrInt,
  };
  // Generic innate stat bonus dispatcher. Reads from embedded hero_stat_innates.json.
  // startHp is only needed for hp_pct formula (Ursa dmg).
  const innate = (key, s, a, level, startHp) => {
    if (!innatesToggle?.checked) return 0;
    const rules = _innateRules[s.slug];
    if (!rules) return 0;
    let total = 0;
    for (const eff of (rules.effects || [])) {
      if (eff.target !== key) continue;
      const entry = _activeEntry(eff, hsTablePatch);
      if (!entry) continue;
      const f = eff.formula;
      if (f === 'attr_factor') {
        total += a[eff.source] * entry.factor;
      } else if (f === 'base_plus_level') {
        total += entry.base + entry.per_level * (level || 1);
      } else if (f === 'flat_per_level') {
        total += entry.per_level * (level || 1);
      } else if (f === 'flat_per_level_interval') {
        // Tidehunter Leviathan's Catch: a fixed bonus every N levels.
        total += entry.value * Math.max(0, Math.floor(((level || 1) - (entry.offset || 0)) / entry.interval));
      } else if (f === 'attr_pct_per_level') {
        total += a[eff.source] * (entry.base_pct + entry.per_level_pct * (level || 1));
      } else if (f === 'hp_pct') {
        total += (startHp || 0) * entry.factor / 100;
      } else if (f === 'secondary_attr_factor') {
        total += a[eff.source] * (_SEC[`${key}:${eff.source}`] || 0) * entry.factor;
      }
      // ms_multiplier/regen_amp_pct → innateMult; dmg_universal_bonus_pct/attr_substitution → dedicated callers
    }
    return total;
  };
  // Multiplicative innate bonus (1 + pct/100): ms_multiplier on ms (Death
  // Prophet Witchcraft, Razor Unstable Current — % move speed) and
  // regen_amp_pct on hpr/mpr (Dark Willow Pixie Dust).
  const innateMult = (key, s, level) => {
    if (!innatesToggle?.checked) return 1;
    const rules = _innateRules[s.slug];
    if (!rules) return 1;
    let pct = 0;
    for (const eff of (rules.effects || [])) {
      if (eff.target !== key) continue;
      const entry = _activeEntry(eff, hsTablePatch);
      if (!entry) continue;
      if (eff.formula === 'ms_multiplier') pct += (entry.base_pct || 0) + entry.per_level_pct * (level || 1);
      else if (eff.formula === 'regen_amp_pct') pct += entry.factor;
    }
    return 1 + pct / 100;
  };
  // Axe — One Man Army: bonus STR = (base_armor + agi/6) * 0.5.
  // Self-referential via armor formula; computed before wa to feed HP/armor derivations.
  const axeStrBonus = (s, a) => {
    if (!innatesToggle?.checked || s.slug !== 'axe') return 0;
    const rules = _innateRules['axe'];
    const eff = rules?.effects?.find(e => e.target === 'str' && e.formula === 'armor_factor');
    if (!eff) return 0;
    const entry = _activeEntry(eff, hsTablePatch);
    if (!entry) return 0;
    return (num(s.armor) + a.agi * C.armorAgi) * entry.factor;
  };
  // Drow — Trueshot: self-referential AGI bonus, folded into agi before all derived stats.
  const drowAgiBonus = (s, rawA, level) => {
    if (!innatesToggle?.checked || s.slug !== 'drow_ranger') return 0;
    const rules = _innateRules['drow_ranger'];
    const eff = rules?.effects?.find(e => e.target === 'agi' && e.formula === 'self_attr_pct_per_level');
    if (!eff) return 0;
    const entry = _activeEntry(eff, hsTablePatch);
    if (!entry) return 0;
    return rawA.agi * (entry.base_pct + entry.per_level_pct * (level || 1));
  };
  // Medusa — Mana Shield. The ability absorbs 98% of incoming damage BEFORE
  // armor / magic resistance, at `damage_per_mana` damage per mana point. Since
  // it soaks raw pre-mitigation damage, every mana point adds a FLAT, armor/
  // resist-independent 0.98·dpm to BOTH physical and magical EHP.
  //
  // dpm and the absorbed share come from the embedded innate rules (medusa →
  // mana_shield_ehp: dpm_base + dpm_per_level·level, or dpm_ranks for the old
  // leveled ability; absorb_pct) — the builder follows KV damage_per_mana /
  // absorption_pct for every new patch (7.41a+: 2 + 0.1·level, 98%).
  // We compare patch strings via the helpers below (same as `_ge` in the
  // Python side).
  const hsTablePatch = table.dataset.patch || '';   // the builder stamps the latest stats patch
  const patchKey = v => {
    const m = String(v || '').match(/^7\.(\d+)([a-z]?)/);
    if (!m) return [0, 0];
    return [parseInt(m[1], 10), m[2] ? m[2].charCodeAt(0) - 96 : 0];
  };
  const patchGe = (a, b) => {
    const [x1, y1] = patchKey(a), [x2, y2] = patchKey(b);
    return x1 !== x2 ? x1 > x2 : y1 >= y2;
  };
  const manaShieldEhp = (s, mana, level) => {
    if (!innatesToggle?.checked || s.slug !== 'medusa') return 0;
    const e = innateEntry('medusa', 'ehp', 'mana_shield_ehp');
    return e ? mana * e.absorb_pct * innateDpm(e, level) : 0;
  };
  const primaryDmg = (s, a) => {
    if (s.attr === 'str') return Math.floor(a.str);
    if (s.attr === 'agi') return Math.floor(a.agi);
    if (s.attr === 'int') return Math.floor(a.int);
    const edge = innateEntry(s.slug, 'dmg', 'dmg_universal_bonus_pct');   // Void Spirit Intrinsic Edge
    const mult = edge ? C.uniDmg * (1 + edge.factor) : C.uniDmg;
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
    const startAs = baseAs + a.agi * C.asAgi + innate('aspd', s, a, effectiveLevel);
    // divide by Agility-per-armor (6), not multiply by 1/6: an exact half (12.95) keeps rounding up
    const startArmor = num(s.armor) + a.agi / (1 / C.armorAgi) + innate('armor', s, a, effectiveLevel);
    const startMr = num(s.mr) + a.int * C.mrInt;
    const rawHp = num(s.hp);
    const startHp = Math.round(rawHp + wa.str * C.hpStr + innate('hp', s, a, effectiveLevel));
    // bonusDmg references startHp (Ursa Maul = % of current HP), so compute it
    // AFTER startHp. primaryDmg = the universal attribute-to-damage; innateDmg
    // adds Sven/Luna/Ursa on top.
    const bonusDmg = primaryDmg(s, wa) + innate('dmg', s, wa, effectiveLevel, startHp);
    const rawMana = s.slug === 'huskar' ? 0 : num(s.mp);
    const rawManaRegen = s.slug === 'huskar' ? 0 : num(s.mpr);
    const startMana = (() => {
      if (s.slug === 'huskar') return 0;
      // Ogre Magi Dumb Luck: mana / mana regen per Strength from the innate rules
      const ogreMp = s.slug === 'ogre_magi' && innateEntry('ogre_magi', 'mp', 'attr_substitution');
      if (ogreMp) return Math.round(num(s.mp) + wa.str * ogreMp.factor + wa.int * C.mpInt);
      return Math.round(num(s.mp) + wa.int * C.mpInt);
    })();
    const startManaRegen = (() => {
      if (s.slug === 'huskar') return 0;
      const techiesPoolPct = techiesPoolPctAt(effectiveLevel); // KV share of the pool per level
      const techiesPoolRegen = (innatesToggle?.checked && s.slug === 'techies')
        ? startMana * techiesPoolPct
        : 0;
      const ogreMpr = s.slug === 'ogre_magi' && innateEntry('ogre_magi', 'mpr', 'attr_substitution');
      if (ogreMpr) return num(s.mpr) + a.str * ogreMpr.factor + a.int * C.mprInt;
      return (num(s.mpr) + wa.int * C.mprInt + innate('mpr', s, a, effectiveLevel) + techiesPoolRegen) * innateMult('mpr', s, effectiveLevel);
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
      case 'hpr': return [start ? (num(s.hpr) + wa.str * C.hprStr + innate('hpr', s, a, effectiveLevel)) * innateMult('hpr', s, effectiveLevel) : num(s.hpr), regen];
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
        // Death Prophet Witchcraft / Razor Unstable Current are % bonuses;
        // Centaur / KotL / Morphling add flat MS via innate(). Apply the %
        // LAST so it scales the full base+flat-innate stack.
        const flat = num(s.ms) + innate('ms', s, a, effectiveLevel);
        return [flat * innateMult('ms', s, effectiveLevel), g0];
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
