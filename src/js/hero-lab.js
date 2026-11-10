
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
  const innateRules = data.innateRules || {};
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
  var SHOP_ORDER = {
    Consumables: ['clarity','tango','flask','bottle','enchanted_mango','faerie_fire','smoke_of_deceit','ward_sentry','dust','infused_raindrop','blood_grenade'],
    Attributes: ['branches','gauntlets','slippers','mantle','circlet','crown','boots_of_elves','belt_of_strength','ogre_axe','blade_of_alacrity','staff_of_wizardry','robe','ghost','diadem'],
    Equipment: ['blades_of_attack','broadsword','claymore','javelin','mithril_hammer','orb_of_venom','blight_stone','orb_of_frost','quelling_blade','ring_of_protection','splintmill','chainmail','helm_of_iron_will','blitz_knuckles','gloves','splintmail'],
    Miscellaneous: ['magic_stick','wind_lace','ring_of_regen','sobi_mask','boots','cloak','fluffy_hat','gem','blink','shadow_amulet','lifesteal','shawl','voodoo_mask','wizard_hat','chasm_stone'],
    'Secret Shop': ['ring_of_health','void_stone','energy_booster','vitality_booster','point_booster','platemail','talisman_of_evasion','hyperstone','ultimate_orb','demon_edge','mystic_staff','reaver','eagle','relic','tiara_of_selemene','ring_of_tarrasque'],
    Accessories: ['magic_wand','null_talisman','wraith_band','bracer','soul_ring','orb_of_corrosion','falcon_blade','power_treads','phase_boots','oblivion_staff','pers','mask_of_madness','hand_of_midas','travel_boots','moon_shard','soul_booster'],
    Support: ['ring_of_basilius','headdress','buckler','urn_of_shadows','tranquil_boots','arcane_boots','pavise','mekansm','spirit_vessel','ancient_janggo','glimmer_cape','holy_locket','solar_crest','pipe','guardian_greaves','boots_of_bearing','essence_distiller'],
    Magical: ['veil_of_discord','aether_lens','force_staff','rod_of_atos','cyclone','meteor_hammer','ultimate_scepter','orchid','dagon','phylactery','ethereal_blade','octarine_core','refresher','sheepstick','gungir','wind_waker','bloodstone','bloodthorn','angels_demise','crellas_crozier'],
    Armor: ['buckler','blade_mail','vanguard','helm_of_the_dominator','vladmir','armlet','crimson_guard','black_king_bar','consecrated_wraps','lotus_orb','aeon_disk','shivas_guard','assault','heart','helm_of_the_overlord','sphere'],
    Weapons: ['lesser_crit','maelstrom','invis_sword','desolator','basher','mage_slayer','bfury','monkey_king_bar','manta','heavens_halberd','radiance','greater_crit','butterfly','silver_edge','satanic','abyssal_blade','mjollnir','rapier','revenants_brooch','nullifier'],
    Armaments: ['sange','yasha','kaya','witch_blade','diffusal_blade','dragon_lance','echo_sabre','devastator','sange_and_yasha','kaya_and_sange','yasha_and_kaya','harpoon','hurricane_pike','disperser','specialists_array','hydras_breath','skadi','arcane_blink','swift_blink','overwhelming_blink'],
  };
  // Attribute constants from the page (builders/hero_lab.py embeds
  // patch/game_constants.for_js()) — one source for Python and JS.
  const C = data.constants || {};
  const METRICS = [
    ['hp', 'HP'], ['mp', 'MP'], ['hpr', 'HP/sec'], ['mpr', 'MP/sec'],
    ['str', 'Strength'], ['agi', 'Agility'], ['int', 'Intelligence'],
    ['armor', 'Armor'], ['armorPct', 'Armor %'], ['mr', 'Mag. resist'],
    ['statusRes', 'Status resist'], ['slowRes', 'Slow resist'], ['spellAmp', 'Spell amp'],
    ['evasion', 'Evasion'], ['dmg', 'Damage'], ['aspd', 'Attack speed'], ['tHit', 'Attack Interval'],
    ['lifesteal', 'Lifesteal'], ['spellLifesteal', 'Spell Lifesteal'],
    ['ms', 'Movespeed'], ['range', 'Attack range'],
    ['dvision', 'Day Vision'], ['nvision', 'Night Vision'], ['castRange', 'Cast Range'],
    ['dps', 'Dummy DPS'],
    ['ehpPhys', 'EHP phys'], ['ehpMag', 'EHP mag'],
    ['itemCdr', 'Item CDR'],
  ];
  const byHero = new Map(heroes.map(h => [h.id, h]));
  const byItem = new Map(items.map(i => [i.id, i]));
  // Enchanter's Bauble multiplier for tier-5 enchantments. Values come from the
  // item's own KV (builders/hero_lab.py → enchantScale): first craft adds
  // `base`, every recraft after it adds `growth`. Never hardcode them — 7.41e
  // moved the recraft bonus from 40% to 35%.
  function baubleScaleFor(level) {
    if (!level || level < 1) return 1;
    const sc = (byItem.get('item_enchanters_bauble') || {}).enchantScale || {};
    const base = typeof sc.base === 'number' ? sc.base : 0.10;
    const growth = typeof sc.growth === 'number' ? sc.growth : 0.35;
    return 1 + base + (level - 1) * growth;
  }
  const heroGroups = {
    str: heroes.filter(h => h.stats?.attr === 'str'),
    agi: heroes.filter(h => h.stats?.attr === 'agi'),
    int: heroes.filter(h => h.stats?.attr === 'int'),
    uni: heroes.filter(h => h.stats?.attr === 'uni'),
  };
  function shopSort(list, cat) {
    var order = SHOP_ORDER[cat];
    if (!order) return list;
    return list.slice().sort(function(a, b) {
      var ai = order.indexOf(a.slug), bi = order.indexOf(b.slug);
      if (ai === -1) ai = 9999;
      if (bi === -1) bi = 9999;
      return ai - bi;
    });
  }
  const itemGroups = {
    basics: BASIC_SECTIONS.map(name => [name, shopSort(items.filter(i => i.class === 'regular' && i.category === name && i.id !== 'item_tpscroll' && i.slug !== 'aghanims_shard'), name)]),
    upgrades: UPGRADE_SECTIONS.map(name => [name, shopSort(items.filter(i => i.class === 'regular' && i.category === name && i.id !== 'item_tpscroll'), name)]),
    neutrals: {
      tiers: [0, 1, 2, 3, 4].map(tier => [tier, items.filter(i => i.class === 'neutral' && i.tier === tier)]),
      enchants: items.filter(i => i.class === 'enchant'),
    },
  };
  const allEnchants = itemGroups.neutrals.enchants.slice().sort((a, b) => (a.tierSort || 99) - (b.tierSort || 99));
  function filteredEnchants(heroAttr) {
    if (!heroAttr) return allEnchants;
    return allEnchants.filter(function(item) {
      var ea = item.enchantAttr;
      if (!ea) return true;
      return ea.indexOf('all') >= 0 || ea.indexOf(heroAttr) >= 0;
    });
  }
  const overlay = document.createElement('div');
  overlay.className = 'hl-overlay';
  overlay.hidden = true;
  document.body.appendChild(overlay);
  let activePicker = null;
  let dragState = null;
  let suppressSlotClickUntil = 0;

  const fmt = (v, d = 0) => {
    const n = Number(v) || 0;
    return d ? n.toFixed(d).replace(/\.?0+$/, '') : String(Math.round(n));
  };
  const fmtMetric = (key, v) => {
    if (key === 'hpr' || key === 'mpr' || key === 'tHit') return Number(v || 0).toFixed(2);
    if (key === 'dps') return Number(v || 0).toFixed(1);
    if (key === 'armor') return fmt(v, 1);
    if (key === 'mr' || key === 'evasion' || key === 'armorPct' || key === 'statusRes' || key === 'slowRes' || key === 'spellAmp' || key === 'lifesteal' || key === 'spellLifesteal' || key === 'itemCdr') return fmt(v, 1) + '%';
    return fmt(v);
  };
  const fmtDiffMetric = (key, v) => {
    const n = Number(v) || 0;
    const abs = Math.abs(n);
    const sign = n > 0 ? '+' : n < 0 ? '-' : '';
    if (key === 'hpr' || key === 'mpr') return sign + abs.toFixed(2);
    if (key === 'tHit') return sign + abs.toFixed(2) + 's';
    if (key === 'dps') return sign + abs.toFixed(1);
    if (key === 'armor') return sign + fmt(abs, 1);
    if (key === 'mr' || key === 'evasion' || key === 'armorPct' || key === 'statusRes' || key === 'slowRes' || key === 'spellAmp' || key === 'lifesteal' || key === 'spellLifesteal' || key === 'itemCdr') return sign + fmt(abs, 1) + '%';
    return sign + fmt(abs);
  };
  const armorFactor = a => (0.06 * a) / (1 + 0.06 * Math.abs(a));
  const plus2At = lvl => PLUS2_LEVELS.filter(x => x <= lvl).length * 2;
  const combinePct = vals => (1 - vals.reduce((acc, v) => acc * (1 - Math.max(0, v) / 100), 1)) * 100;
  const iconHtml = (src, name, cls) => `<img class="${cls}" src="${src}" alt="${name}" loading="lazy">`;
  const quickFmt = v => Number(v || 0).toFixed(2).replace(/\.00$/, '');
  const patchKey = v => {
    const m = String(v || '').match(/^7\.(\d+)([a-z]?)/);
    if (!m) return [0, 0];
    return [parseInt(m[1], 10), m[2] ? m[2].charCodeAt(0) - 96 : 0];
  };
  const patchGe = (a, b) => {
    const [x1, y1] = patchKey(a), [x2, y2] = patchKey(b);
    return x1 !== x2 ? x1 > x2 : y1 >= y2;
  };
  const currentPatch = data.patch || root.dataset.patch || '';
  const _SEC = {
    'hpr:str': C.hprStr, 'mpr:int': C.mprInt, 'aspd:agi': C.asAgi, 'armor:agi': C.armorAgi, 'mr:int': C.mrInt,
  };

  function heroLabInnatesOn() {
    const innateToggle = document.querySelector('[data-innates-toggle]');
    return innateToggle ? innateToggle.checked : true;
  }

  function heroLabMergePositiveOn() {
    const toggle = document.querySelector('[data-hl-merge-positive-toggle]');
    return toggle ? toggle.checked : false;
  }

  function heroLabDiffPercentOn() {
    const toggle = document.querySelector('[data-hl-diff-percent-toggle]');
    return toggle ? toggle.checked : false;
  }

  function activeEntry(eff, patch) {
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
  }

  // Active entry of one hero's innate effect (entry fields over the effect's own),
  // null if none — Medusa / Void Spirit / Ogre Magi numbers come from the rules.
  function innateEntry(slug, target, formula) {
    const eff = (innateRules[slug]?.effects || []).find(e => e.target === target && e.formula === formula);
    const entry = eff ? activeEntry(eff, currentPatch) : null;
    return entry ? { ...eff, ...entry } : null;
  }

  function heroLabInnate(key, s, a, level, startHp, includeInnates) {
    if (!includeInnates) return 0;
    const rules = innateRules[s.slug];
    if (!rules) return 0;
    let total = 0;
    for (const eff of (rules.effects || [])) {
      if (eff.target !== key) continue;
      const entry = activeEntry(eff, currentPatch);
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
      } else if (f === 'hp_threshold') {
        // Primal Beast Colossal: base + per_threshold per `threshold` max HP.
        total += entry.base + entry.per_threshold * Math.floor((startHp || 0) / entry.threshold);
      } else if (f === 'attr_pct_per_level') {
        total += a[eff.source] * (entry.base_pct + entry.per_level_pct * (level || 1));
      } else if (f === 'hp_pct') {
        total += (startHp || 0) * entry.factor / 100;
      } else if (f === 'secondary_attr_factor') {
        total += a[eff.source] * (_SEC[`${key}:${eff.source}`] || 0) * entry.factor;
      } else if (f === 'mana_pool_pct_per_level') {
        const manaPool = a && a._manaPool ? a._manaPool : 0;
        total += manaPool * (entry.base_pct + entry.per_level_pct * (level || 1));
      } else if (f === 'attr_floor_capped') {
        total += Math.min(Math.floor(a[eff.source] / (eff.divisor || 1)), eff.cap || 100);
      }
    }
    return total;
  }

  // Percentage innate bonuses that add to the matching item % bonus:
  // ms_multiplier on ms (Death Prophet Witchcraft, Razor Unstable Current)
  // and regen_amp_pct on hpr/mpr (Dark Willow Pixie Dust).
  function heroLabInnatePct(key, s, level, includeInnates) {
    if (!includeInnates) return 0;
    const rules = innateRules[s.slug];
    if (!rules) return 0;
    let pct = 0;
    for (const eff of (rules.effects || [])) {
      if (eff.target !== key) continue;
      const entry = activeEntry(eff, currentPatch);
      if (!entry) continue;
      if (eff.formula === 'ms_multiplier') pct += (entry.base_pct || 0) + entry.per_level_pct * (level || 1);
      else if (eff.formula === 'regen_amp_pct') pct += entry.factor;
    }
    return pct;
  }

  // Centaur Horsepower (7.41+) does not stack with boots move speed.
  function innateMsStacksWithBoots(s, includeInnates) {
    if (!includeInnates) return true;
    const rules = innateRules[s.slug];
    for (const eff of (rules?.effects || [])) {
      if (eff.target !== 'ms') continue;
      const entry = activeEntry(eff, currentPatch);
      if (entry && entry.stacks_with_boots === false) return false;
    }
    return true;
  }

  // Elder Titan — Momentum (innate, 7.41a+): armor = factor% of BONUS movement
  // speed (MS above base). Depends on the computed MS, so it is applied in calc()
  // after ms is known, not via the generic innate() dispatch.
  function elderTitanMomentumArmor(s, ms, level, includeInnates) {
    if (!includeInnates || s.slug !== 'elder_titan') return 0;
    const rules = innateRules.elder_titan;
    const eff = rules?.effects?.find(e => e.target === 'armor' && e.formula === 'bonus_ms_factor');
    if (!eff) return 0;
    const entry = activeEntry(eff, currentPatch);
    if (!entry) return 0;
    const baseMs = Number(s.ms) || 0;
    const bonusMs = Math.max(0, ms - baseMs);
    // factor scales with level; increment provided at level 1 (7.41 innate rule).
    const factor = (Number(entry.base) || 0) + (Number(entry.per_level) || 0) * (level || 1);
    return bonusMs * factor / 100;
  }

  function axeStrBonus(s, a, includeInnates) {
    if (!includeInnates || s.slug !== 'axe') return 0;
    const rules = innateRules.axe;
    const eff = rules?.effects?.find(e => e.target === 'str' && e.formula === 'armor_factor');
    if (!eff) return 0;
    const entry = activeEntry(eff, currentPatch);
    if (!entry) return 0;
    return ((Number(s.armor) || 0) + a.agi * C.armorAgi) * entry.factor;
  }

  function drowAgiBonus(s, rawA, level, includeInnates) {
    if (!includeInnates || s.slug !== 'drow_ranger') return 0;
    const rules = innateRules.drow_ranger;
    const eff = rules?.effects?.find(e => e.target === 'agi' && e.formula === 'self_attr_pct_per_level');
    if (!eff) return 0;
    const entry = activeEntry(eff, currentPatch);
    if (!entry) return 0;
    return rawA.agi * (entry.base_pct + entry.per_level_pct * (level || 1));
  }

  function manaShieldEhp(s, mana, level, includeInnates) {
    if (!includeInnates || s.slug !== 'medusa') return 0;
    const e = innateEntry('medusa', 'ehp', 'mana_shield_ehp');   // absorb_pct + damage per mana
    return e ? mana * e.absorb_pct * innateDpm(e, level) : 0;
  }

  // Void Spirit Intrinsic Edge: (1 + factor) on the Universal damage per attribute.
  function universalDmgMult(s, includeInnates) {
    const edge = includeInnates ? innateEntry(s.slug, 'dmg', 'dmg_universal_bonus_pct') : null;
    return edge ? C.uniDmg * (1 + edge.factor) : C.uniDmg;
  }

  function primaryDmg(s, a, includeInnates) {
    if (s.attr === 'str') return Math.floor(a.str);
    if (s.attr === 'agi') return Math.floor(a.agi);
    if (s.attr === 'int') return Math.floor(a.int);
    return Math.floor((a.str + a.agi + a.int) * universalDmgMult(s, includeInnates));
  }

  function renderPanel(panel, side, heroId) {
    const hero = byHero.get(heroId) || heroes[0];
    panel.innerHTML = `
      <div class="hl-hud">
        <div class="hl-identity">
          <div class="hl-portrait-row">
            <div class="hl-portrait-wrap">
              <button type="button" class="hl-hero-trigger" data-open-hero-picker aria-label="Choose hero">
                ${iconHtml(hero.icon, hero.name, 'hl-hero-icon')}
              </button>
              <button type="button" class="hl-innate-chip is-hidden" data-innate-chip aria-label="Innate tooltip" tabindex="-1">
                <img class="hl-innate-chip-icon" data-innate-icon alt="" loading="lazy">
              </button>
              <span class="hl-level-corner">
                <svg class="hl-level-ring" viewBox="0 0 44 44" aria-hidden="true">
                  <circle class="hl-level-ring-bg" cx="22" cy="22" r="18"/>
                  <circle class="hl-level-ring-fg" cx="22" cy="22" r="18" data-ring/>
                </svg>
                <input class="hl-level-input" type="text" inputmode="numeric" maxlength="2" value="1" data-field="level" aria-label="Hero level" autocomplete="off">
              </span>
            </div>
            <div class="hl-quickstats">
              <div class="hl-qs-cell">
                <span class="hl-qs-label">DUMMY DPS</span>
                <span class="hl-qs-value" data-dps-value></span>
              </div>
              <div class="hl-qs-cell">
                <span class="hl-qs-label">DMG GOLD</span>
                <span class="hl-qs-value" data-dmggold-value></span>
              </div>
              <div class="hl-qs-cell">
                <span class="hl-qs-label">pEHP</span>
                <span class="hl-qs-value" data-pehp-value></span>
              </div>
              <div class="hl-qs-cell">
                <span class="hl-qs-label">mEHP</span>
                <span class="hl-qs-value" data-mehp-value></span>
              </div>
            </div>
          </div>
          <div class="hl-identity-main"></div>
          <span class="hl-cost-badge" data-cost-badge>
            <img class="hl-cost-icon" src="icons/misc/gold.png" alt="" loading="lazy">
            <span class="hl-cost-value" data-cost-value></span>
          </span>
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
            <button type="button" class="hl-inv-slot hl-enchant-slot is-empty" data-open-item-picker data-slot="enchant" aria-label="Choose enchantment">
              <span class="hl-enchant-mark">E</span>
              <span class="hl-slot-bevel"></span>
              <span class="hl-slot-glow"></span>
            </button>
            <div class="hl-bauble-connector"></div>
            <div class="hl-bauble-wrap">
              <button type="button" class="hl-bauble-slot" data-slot="bauble" aria-label="Enchanter's Bauble">
                <img src="icons/items/enchanters_bauble.png" alt="Enchanter's Bauble" loading="lazy">
                <span class="hl-slot-bevel"></span>
                <span class="hl-slot-glow"></span>
              </button>
              <input type="number" class="hl-bauble-level" data-field="bauble-level" min="0" max="100" value="0" placeholder="0">
            </div>
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
      <div class="hl-total-list" data-total-list></div>
    `;
    panel.dataset.hero = hero.id;
    panel.dataset.side = side;
    panel.dataset.items = JSON.stringify(['', '', '', '', '', '']);
    panel.dataset.itemModes = JSON.stringify({});

    panel.dataset.enchantItem = '';
  }

  function safeJsonParse(str, fallback) {
    try { return JSON.parse(str); } catch { return fallback; }
  }

  function state(panel) {
    const heroId = panel.dataset.hero || heroes[0].id;
    let level = parseInt(panel.querySelector('[data-field="level"]')?.value || '1', 10);
    level = Math.max(1, Math.min(30, Number.isFinite(level) ? level : 1));
    panel.querySelector('[data-field="level"]').value = String(level);
    const itemModes = safeJsonParse(panel.dataset.itemModes, {});
    const itemEntries = safeJsonParse(panel.dataset.items, ["","","","","",""])
      .map((id, idx) => id ? { id, mode: itemModes[String(idx)] || null, slot: idx } : null)
      .filter(Boolean);
    const enchantItem = panel.dataset.enchantItem || '';
    if (enchantItem) itemEntries.push({ id: enchantItem, mode: itemModes.enchant || null, slot: 'enchant' });
    const baubleLevel = Math.max(0, Math.min(100, parseInt(panel.querySelector('[data-field="bauble-level"]')?.value || '0', 10) || 0));
    const custom = { hp: null, mp: null, hpr: null, mpr: null, armor: null, mr: null, evasion: null };
    panel.querySelectorAll('[data-custom]').forEach(inp => {
      custom[inp.dataset.custom] = inp.value === '' ? null : (Number(inp.value) || 0);
    });
    return { hero: byHero.get(heroId) || heroes[0], level, itemEntries, baubleLevel, custom };
  }

  function slotAcceptsItem(slot, item) {
    if (!item) return true;
    if (slot === 'enchant') return item.class === 'enchant';
    return item.class === 'regular';
  }

  function getSlotState(panel, slot) {
    const items = safeJsonParse(panel.dataset.items, ["","","","","",""]);
    const itemModes = safeJsonParse(panel.dataset.itemModes, {});
    if (slot === 'enchant') {
      return { id: panel.dataset.enchantItem || '', mode: itemModes.enchant || null };
    }
    const idx = Number(slot);
    return { id: items[idx] || '', mode: itemModes[String(slot)] || null };
  }

  function setSlotState(panel, slot, next) {
    const items = safeJsonParse(panel.dataset.items, ["","","","","",""]);
    const itemModes = safeJsonParse(panel.dataset.itemModes, {});
    const id = next && next.id ? next.id : '';
    const mode = next && next.mode ? next.mode : null;
    if (slot === 'enchant') {
      panel.dataset.enchantItem = id;
      if (mode) itemModes.enchant = mode;
      else delete itemModes.enchant;
    } else {
      const idx = Number(slot);
      items[idx] = id;
      panel.dataset.items = JSON.stringify(items);
      if (mode) itemModes[String(slot)] = mode;
      else delete itemModes[String(slot)];
    }
    if (slot === 'enchant') {
      panel.dataset.itemModes = JSON.stringify(itemModes);
      return;
    }
    panel.dataset.itemModes = JSON.stringify(itemModes);
  }

  function swapSlots(srcPanel, srcSlot, dstPanel, dstSlot) {
    const src = getSlotState(srcPanel, srcSlot);
    const dst = getSlotState(dstPanel, dstSlot);
    const srcItem = src.id ? byItem.get(src.id) : null;
    const dstItem = dst.id ? byItem.get(dst.id) : null;
    if (!srcItem) return false;
    if (!slotAcceptsItem(dstSlot, srcItem)) return false;
    if (dstItem && !slotAcceptsItem(srcSlot, dstItem)) return false;
    setSlotState(srcPanel, srcSlot, dst);
    setSlotState(dstPanel, dstSlot, src);
    return true;
  }

  function syncEnchantMode(panel) {
    const enchId = panel.dataset.enchantItem || '';
    if (!enchId) return;
    const enchItem = byItem.get(enchId);
    if (!enchItem || !enchItem.tiersAvailable) return;
    const tiers = enchItem.tiersAvailable;
    const best = tiers[tiers.length - 1];
    const itemModes = safeJsonParse(panel.dataset.itemModes, {});
    itemModes.enchant = 't' + best;
    panel.dataset.itemModes = JSON.stringify(itemModes);
  }

  function activeItemMode(item, modeKey) {
    if (!item || !item.modes) return null;
    const key = modeKey || item.modes.default || null;
    return key ? (item.modes[key] || null) : null;
  }

  function itemModeBadge(item, modeKey) {
    if (!item || !item.modes) return '';
    if (item.id === 'item_rapier') return modeKey === 'spell' ? 'AMP' : 'DMG';
    if (item.id === 'item_dagon') {
      const mode = activeItemMode(item, modeKey);
      return 'L' + String((mode && mode.level) || 1);
    }
    if (item.id === 'item_power_treads') return (modeKey || 'str').toUpperCase();
    if (item.id === 'item_desolator') return (modeKey && modeKey !== 'none') ? '+' + modeKey : '0';
    if (item.id === 'item_tranquil_boots') return modeKey === 'broken' ? 'OFF' : 'ON';
    if (item.tiersAvailable && modeKey && modeKey.startsWith('t')) return '';
    return 'ALT';
  }

  function itemModeAccent(item, modeKey) {
    if (!item || !item.modes) return '';
    if (item.id === 'item_rapier') return modeKey === 'spell' ? 'arcane' : 'damage';
    if (item.id === 'item_dagon') return 'damage';
    if (item.id === 'item_power_treads') return modeKey || 'str';
    return '';
  }

  function itemVisual(item, modeKey) {
    const mode = activeItemMode(item, modeKey);
    return {
      icon: (mode && mode.icon) || item.icon,
      cost: mode && mode.costOverride != null ? mode.costOverride : item.cost,
      mode,
    };
  }

  function itemTotals(entries, attackType, baubleLevel) {
    const isRanged = String(attackType || '').toLowerCase() === 'ranged';
    const baubleScale = baubleScaleFor(baubleLevel);
    const out = { str: 0, agi: 0, int: 0, hp: 0, mp: 0, hpr: 0, mpr: 0, mprAmp: 0, _mprAmpVals: [], armor: 0, _rangeUniqueAllVals: [], _rangeUniqueRangedVals: [], _msBootVals: [], _cdrUniqVals: [], _cdrStackVals: [], _spellAmpUniqueVals: [], projSpeed: 0, mrVals: [], evVals: [], statusResVals: [], slowResVals: [], spellAmp: 0, damage: 0, damagePct: 0, aspd: 0, ms: 0, range: 0, dvision: 0, nvision: 0, cost: 0, hprPct: 0, missingHprPct: 0, mpPct: 0, lifesteal: 0, spellLifesteal: 0, castRange: 0, primaryStat: 0, primaryStatUni: 0, batReduce: 0, healthRestoration: 0, cooldownReduction: 0, debuffAmp: 0, hpPct: 0, msPct: 0, _msPctVals: [], knockbackResist: 0, maxHpRegen: 0, incomingDamage: 0, magicDamage: 0, castSpeed: 0, visionReduce: 0, manacostIncrease: 0, intelligencePct: 0, hpRegenReduce: 0, manacostReduction: 0, gpm: 0, xpm: 0, aspdPct: 0, manaReductionPct: 0 };
    const visionSeen = new Set();
    entries.forEach(entry => {
      const id = typeof entry === 'string' ? entry : entry.id;
      const mode = typeof entry === 'string' ? null : entry.mode;
      const it = byItem.get(id);
      if (!it) return;
      // Enchanter's Bauble only amplifies Tier 5 enchants. The item picker dims
      // non-T5 enchants when a bauble is active, so in normal use this branch is
      // never reached. If it is (e.g. bauble added after enchant selection),
      // we skip the enchant rather than showing unscaled T<5 stats.
      if (it.class === 'enchant' && baubleLevel > 0 && mode !== 't5') return;
      const _entryScale = (it.class === 'enchant' && baubleScale !== 1 && mode === 't5') ? baubleScale : 1;
      // CDR is excluded from linear scaling — it gets two separate multiplicative stacks below.
      const _bs = _entryScale !== 1 ? Object.fromEntries(Object.entries(it.bonus || {}).map(([k,v]) => [k, typeof v === 'number' && k !== 'cooldownReduction' && k !== 'cdrUnique' ? v * _entryScale : v])) : (it.bonus || {});
      const b = _bs;
      // "All Attributes" feeds every stat; per-attribute bonuses stack on top.
      const allAttr = Number(b.all) || 0;
      out.str += (Number(b.str) || 0) + allAttr;
      out.agi += (Number(b.agi) || 0) + allAttr;
      out.int += (Number(b.int) || 0) + allAttr;
      out.hp += Number(b.hp) || 0;
      out.mp += Number(b.mp) || 0;
      out.hpr += Number(b.hpr) || 0;
      out.mpr += Number(b.mpr) || 0;
      if (b.mprAmp) out._mprAmpVals.push(Number(b.mprAmp) || 0);
      if (b.msPct) out._msPctVals.push(Number(b.msPct) || 0);
      out.hprPct += Number(b.hprPct) || 0;
      out.missingHprPct += Number(b.missingHprPct) || 0;
      out.mpPct += Number(b.mpPct) || 0;
      out.armor += Number(b.armor) || 0;
      if (b.mr) out.mrVals.push(Number(b.mr) || 0);
      if (b.evasion) out.evVals.push(Number(b.evasion) || 0);
      if (b.statusRes) out.statusResVals.push(Number(b.statusRes) || 0);
      if (b.slowRes) out.slowResVals.push(Number(b.slowRes) || 0);
      out.spellAmp += Number(b.spellAmp) || 0;
      if (b.spellAmpUnique) out._spellAmpUniqueVals.push(Number(b.spellAmpUnique));
      out.damage += (Number(b.damage) || 0) + (isRanged ? (Number(b.damageRanged) || 0) : (Number(b.damageMelee) || 0));
      out.damagePct += Number(b.damagePct) || 0;
      out.lifesteal += Number(b.lifesteal) || 0;
      out.spellLifesteal += Number(b.spellLifesteal) || 0;
      out.castRange += Number(b.castRange) || 0;
      out.primaryStat += Number(b.primaryStat) || 0;
      out.primaryStatUni += Number(b.primaryStatUni) || 0;
      out.batReduce += Number(b.batReduce) || 0;
      out.healthRestoration += Number(b.healthRestoration) || 0;
      if (b.cdrUnique) out._cdrUniqVals.push(Number(b.cdrUnique));
      else if (b.cooldownReduction) {
        out._cdrStackVals.push(Number(b.cooldownReduction));
        if (_entryScale !== 1) { const _cb = Number(b.cooldownReduction) * (_entryScale - 1); if (_cb > 0.001) out._cdrStackVals.push(_cb); }
      }
      out.debuffAmp += Number(b.debuffAmp) || 0;
      out.hpPct += Number(b.hpPct) || 0;

      out.knockbackResist += Number(b.knockbackResist) || 0;
      out.maxHpRegen += Number(b.maxHpRegen) || 0;
      out.incomingDamage += Number(b.incomingDamage) || 0;
      out.magicDamage += Number(b.magicDamage) || 0;
      out.castSpeed += Number(b.castSpeed) || 0;
      out.visionReduce += Number(b.visionReduce) || 0;
      out.manacostIncrease += Number(b.manacostIncrease) || 0;
      out.intelligencePct += Number(b.intelligencePct) || 0;
      out.hpRegenReduce += Number(b.hpRegenReduce) || 0;
      out.manacostReduction += Number(b.manacostReduction) || 0;
      out.gpm += Number(b.gpm) || 0;
      out.xpm += Number(b.xpm) || 0;
      out.aspdPct += Number(b.aspdPct) || 0;
      out.manaReductionPct += Number(b.manaReductionPct) || 0;
      out.aspd += Number(b.aspd) || 0;
      { const _bms = (Number(b.ms) || 0) + (isRanged ? (Number(b.msRanged) || 0) : (Number(b.msMelee) || 0));
        if (it.isBoot) { if (_bms) out._msBootVals.push(_bms); } else out.ms += _bms; }
      out.range += Number(b.range) || 0;
      if (b.rangeUniqueAll) out._rangeUniqueAllVals.push(Number(b.rangeUniqueAll));
      // Melee-only unique range (MKB 7.41: "+50 Attack Range to melee heroes only").
      if (b.rangeUniqueMelee && !isRanged) out._rangeUniqueAllVals.push(Number(b.rangeUniqueMelee));
      // Butterfly: +% of base + Agility attack speed only (not item/buff AS).
      out.baseAspdPct = (out.baseAspdPct || 0) + (Number(b.baseAspdPct) || 0);
      if (b.rangeUniqueRanged) out._rangeUniqueRangedVals.push(Number(b.rangeUniqueRanged));
      if (isRanged) out.projSpeed += Number(b.projSpeed) || 0;
      if (!visionSeen.has(id)) { out.dvision += Number(b.dvision) || 0; out.nvision += Number(b.nvision) || 0; }
      if (it.modes) {
        const activeMode = mode || it.modes.default || 'damage';
        const _rawMb = it.modes[activeMode] || {};
        const mb = _entryScale !== 1 ? Object.fromEntries(Object.entries(_rawMb).map(([k,v]) => [k, typeof v === 'number' && k !== 'cooldownReduction' && k !== 'cdrUnique' ? v * _entryScale : v])) : _rawMb;
        const allAttrMode = Number(mb.all) || 0;
        out.str += (Number(mb.str) || 0) + allAttrMode;
        out.agi += (Number(mb.agi) || 0) + allAttrMode;
        out.int += (Number(mb.int) || 0) + allAttrMode;
        out.hp += Number(mb.hp) || 0;
        out.mp += Number(mb.mp) || 0;
        out.hpr += Number(mb.hpr) || 0;
        out.mpr += Number(mb.mpr) || 0;
        out.armor += Number(mb.armor) || 0;
        if (mb.mr) out.mrVals.push(Number(mb.mr) || 0);
        if (mb.evasion) out.evVals.push(Number(mb.evasion) || 0);
        if (mb.statusRes) out.statusResVals.push(Number(mb.statusRes) || 0);
        if (mb.slowRes) out.slowResVals.push(Number(mb.slowRes) || 0);
        out.spellAmp += Number(mb.spellAmp) || 0;
        if (mb.spellAmpUnique) out._spellAmpUniqueVals.push(Number(mb.spellAmpUnique));
        out.damagePct += Number(mb.damagePct) || 0;
        if (mb.mprAmp) out._mprAmpVals.push(Number(mb.mprAmp) || 0);
        if (mb.msPct) out._msPctVals.push(Number(mb.msPct) || 0);
        out.hprPct += Number(mb.hprPct) || 0;
        out.missingHprPct += Number(mb.missingHprPct) || 0;
        out.damage += (Number(mb.damage) || 0) + (isRanged ? (Number(mb.damageRanged) || 0) : (Number(mb.damageMelee) || 0));
        out.aspd += Number(mb.aspd) || 0;
        { const _mms = (Number(mb.ms) || 0) + (isRanged ? (Number(mb.msRanged) || 0) : (Number(mb.msMelee) || 0));
          if (it.isBoot) { if (_mms) out._msBootVals.push(_mms); } else out.ms += _mms; }
        out.range += Number(mb.range) || 0;
        if (mb.rangeUniqueAll) out._rangeUniqueAllVals.push(Number(mb.rangeUniqueAll));
        if (mb.rangeUniqueRanged) out._rangeUniqueRangedVals.push(Number(mb.rangeUniqueRanged));
        if (isRanged) out.projSpeed += Number(mb.projSpeed) || 0;
        if (!visionSeen.has(id)) { out.dvision += Number(mb.dvision) || 0; out.nvision += Number(mb.nvision) || 0; }
        out.lifesteal += Number(mb.lifesteal) || 0;
        out.spellLifesteal += Number(mb.spellLifesteal) || 0;
        out.castRange += Number(mb.castRange) || 0;
        out.mpPct += Number(mb.mpPct) || 0;
        out.primaryStat += Number(mb.primaryStat) || 0;
        out.primaryStatUni += Number(mb.primaryStatUni) || 0;
        out.batReduce += Number(mb.batReduce) || 0;
        out.healthRestoration += Number(mb.healthRestoration) || 0;
        if (mb.cdrUnique) out._cdrUniqVals.push(Number(mb.cdrUnique));
        else if (mb.cooldownReduction) {
          out._cdrStackVals.push(Number(mb.cooldownReduction));
          if (_entryScale !== 1) { const _cb = Number(mb.cooldownReduction) * (_entryScale - 1); if (_cb > 0.001) out._cdrStackVals.push(_cb); }
        }
        out.debuffAmp += Number(mb.debuffAmp) || 0;
        out.hpPct += Number(mb.hpPct) || 0;
        out.knockbackResist += Number(mb.knockbackResist) || 0;
        out.maxHpRegen += Number(mb.maxHpRegen) || 0;
        out.incomingDamage += Number(mb.incomingDamage) || 0;
        out.magicDamage += Number(mb.magicDamage) || 0;
        out.castSpeed += Number(mb.castSpeed) || 0;
        out.visionReduce += Number(mb.visionReduce) || 0;
        out.manacostIncrease += Number(mb.manacostIncrease) || 0;
        out.intelligencePct += Number(mb.intelligencePct) || 0;
        out.hpRegenReduce += Number(mb.hpRegenReduce) || 0;
        out.manacostReduction += Number(mb.manacostReduction) || 0;
        out.gpm += Number(mb.gpm) || 0;
        out.xpm += Number(mb.xpm) || 0;
        out.aspdPct += Number(mb.aspdPct) || 0;
        out.manaReductionPct += Number(mb.manaReductionPct) || 0;
        out.cost += Number(mb.costOverride != null ? mb.costOverride : it.cost) || 0;
      } else {
        out.cost += Number(it.cost) || 0;
      }
      visionSeen.add(id);
    });
    out.spellAmp += out._spellAmpUniqueVals.length ? Math.max(...out._spellAmpUniqueVals) : 0;
    out.mprAmp = out._mprAmpVals.length ? Math.max(...out._mprAmpVals) : 0;
    out.msPct = out._msPctVals.length ? Math.max(...out._msPctVals) : 0;
    out.msBoots = out._msBootVals.length ? Math.max(...out._msBootVals) : 0;
    out.ms += out.msBoots;
    { const _uniq = Math.min(out._cdrUniqVals.length ? Math.max(...out._cdrUniqVals) : 0, 99.9);
      let _mult = 1; for (const v of out._cdrStackVals) _mult *= (1 - v / 100);
      out.cooldownReduction = Math.min(Math.round((1 - (1 - _uniq / 100) * _mult) * 1000) / 10, 99.9); }
    const _allMax = out._rangeUniqueAllVals.length ? Math.max(...out._rangeUniqueAllVals) : 0;
    const _rangedMax = out._rangeUniqueRangedVals.length ? Math.max(...out._rangeUniqueRangedVals) : 0;
    out.range += isRanged ? Math.max(_allMax, _rangedMax) : _allMax;
    return out;
  }

  function calc(st, opts) {
    opts = opts || {};
    const s = st.hero.stats || {};
    const lvl = st.level;
    const plus = plus2At(lvl);
    const includeInnates = opts.includeInnates == null ? heroLabInnatesOn() : !!opts.includeInnates;
    const itemsTotal = itemTotals(st.itemEntries, st.hero.attackType, st.baubleLevel);
    const attr = s.attr;
    if (attr === 'uni') {
      const psu = itemsTotal.primaryStatUni;
      itemsTotal.str += psu; itemsTotal.agi += psu; itemsTotal.int += psu;
    } else {
      const ps = itemsTotal.primaryStat;
      if (attr === 'str') itemsTotal.str += ps;
      else if (attr === 'agi') itemsTotal.agi += ps;
      else if (attr === 'int') itemsTotal.int += ps;
    }
    const rawStr = (Number(s.str) || 0) + (lvl - 1) * (Number(s.strGain) || 0) + plus + itemsTotal.str;
    const rawAgi = (Number(s.agi) || 0) + (lvl - 1) * (Number(s.agiGain) || 0) + plus + itemsTotal.agi;
    const rawInt = st.hero.id === 'ogre_magi'
      ? 0
      : ((Number(s.int) || 0) + (lvl - 1) * (Number(s.intGain) || 0) + plus + itemsTotal.int) * (1 + itemsTotal.intelligencePct / 100);
    const rawAttrs = { str: rawStr, agi: rawAgi, int: rawInt };
    const liveAttrs = includeInnates ? {
      str: rawAttrs.str + axeStrBonus(s, rawAttrs, includeInnates),
      agi: rawAttrs.agi + drowAgiBonus(s, rawAttrs, lvl, includeInnates),
      int: rawAttrs.int,
    } : rawAttrs;
    const str = Math.floor(liveAttrs.str), agi = Math.floor(liveAttrs.agi), int = Math.floor(liveAttrs.int);
    const a = { str: liveAttrs.str, agi: liveAttrs.agi, int: liveAttrs.int };
    const isOgre = st.hero.id === 'ogre_magi';
    const isHuskar = st.hero.id === 'huskar';
    // Ogre Magi Dumb Luck: mana / mana regen per Strength from the innate rules
    const ogreMp = isOgre ? innateEntry('ogre_magi', 'mp', 'attr_substitution') : null;
    const ogreMpr = isOgre ? innateEntry('ogre_magi', 'mpr', 'attr_substitution') : null;
    const mpFromAttr = isHuskar ? 0 : (ogreMp ? str * ogreMp.factor : int * C.mpInt);
    const mprFromAttr = isHuskar ? 0 : (ogreMpr ? str * ogreMpr.factor : int * C.mprInt);
    const baseMr = (Number(s.mr) || 25) + int * C.mrInt + heroLabInnate('mr', s, a, lvl, 0, includeInnates);
    let mr = Math.min(combinePct([baseMr, ...itemsTotal.mrVals]), 99.9);
    let evasion = Math.min(combinePct([heroLabInnate('evasion', s, a, lvl, 0, includeInnates), ...itemsTotal.evVals]), 99.9);
    const spellAmp = itemsTotal.spellAmp;
    let armor = (Number(s.armor) || 0) + agi * C.armorAgi + heroLabInnate('armor', s, a, lvl, 0, includeInnates) + itemsTotal.armor;
    let hp = Math.round(((Number(s.hp) || 120) + str * C.hpStr + heroLabInnate('hp', s, a, lvl, 0, includeInnates) + itemsTotal.hp) * (1 + itemsTotal.hpPct / 100));
    let mp = isHuskar ? 0 : Math.round(((Number(s.mp) || 75) + mpFromAttr + itemsTotal.mp) * (1 + itemsTotal.mpPct / 100) * (1 - itemsTotal.manaReductionPct / 100));
    a._manaPool = mp;
    const statusRes = Math.min(combinePct([...itemsTotal.statusResVals, heroLabInnate('statusRes', s, a, lvl, hp, includeInnates)]), 99.9);
    const slowRes = Math.min(combinePct([...itemsTotal.slowResVals, heroLabInnate('slowRes', s, a, lvl, hp, includeInnates)]), 99.9);
    // missingHprPct (e.g. Heart of Tarrasque) requires knowing current HP at
    // runtime and is intentionally excluded from the static calc display.
    // It is shown as a separate stat row ("Missing HP Regen") instead.
    let hpr = ((Number(s.hpr) || 0) + str * C.hprStr + heroLabInnate('hpr', s, a, lvl, hp, includeInnates) + itemsTotal.hpr - itemsTotal.hpRegenReduce) * (1 + (itemsTotal.healthRestoration + heroLabInnatePct('hpr', s, lvl, includeInnates)) / 100)
      + hp * (itemsTotal.hprPct + itemsTotal.maxHpRegen) / 100;
    let mpr = isHuskar ? 0 : ((Number(s.mpr) || 0) + mprFromAttr + heroLabInnate('mpr', s, a, lvl, hp, includeInnates) + itemsTotal.mpr) * (1 + (itemsTotal.mprAmp + heroLabInnatePct('mpr', s, lvl, includeInnates)) / 100);
    if (st.custom.hp !== null) hp = Math.round(st.custom.hp);
    if (st.custom.mp !== null && !isHuskar) mp = Math.round(st.custom.mp);
    if (st.custom.hpr !== null) hpr = st.custom.hpr;
    if (st.custom.mpr !== null && !isHuskar) mpr = st.custom.mpr;
    if (st.custom.armor !== null) armor = st.custom.armor;
    if (st.custom.mr !== null) mr = st.custom.mr;
    if (st.custom.evasion !== null) evasion = st.custom.evasion;
    const primary = primaryDmg(s, { str, agi, int }, includeInnates);
    const dmgInnate = heroLabInnate('dmg', s, { str, agi, int }, lvl, hp, includeInnates);
    const whiteDmin = (Number(s.dmin) || 0) + primary + dmgInnate;
    const whiteDmax = (Number(s.dmax) || 0) + primary + dmgInnate;
    const dmin = whiteDmin + Math.floor(whiteDmin * itemsTotal.damagePct / 100) + itemsTotal.damage;
    const dmax = whiteDmax + Math.floor(whiteDmax * itemsTotal.damagePct / 100) + itemsTotal.damage;
    const dmg = (dmin + dmax) / 2;
    const aspdRaw = ((Number(s.bas) || 100) + agi * C.asAgi) * (1 + (itemsTotal.baseAspdPct || 0) / 100) + heroLabInnate('aspd', s, a, lvl, hp, includeInnates) + itemsTotal.aspd;
    const aspd = Math.min(Math.max(aspdRaw * (1 + itemsTotal.aspdPct / 100), 20), 700);
    const batBase = Number(s.bat) || 1.7;
    const bat = batBase * (1 - itemsTotal.batReduce / 100);
    const tHit = bat * 100 / Math.max(1, aspd);
    // Flat innate MS (Centaur/KotL/Morphling). Horsepower does not stack with
    // boots: only the larger of the two applies. % innates (Witchcraft,
    // Unstable Current) add to item % MS and scale every flat source, boots too.
    let msInnateFlat = heroLabInnate('ms', s, a, lvl, hp, includeInnates);
    let msItemsFlat = itemsTotal.ms;
    if (!innateMsStacksWithBoots(s, includeInnates)) {
      msItemsFlat -= itemsTotal.msBoots;
      msInnateFlat = Math.max(msInnateFlat, itemsTotal.msBoots);
    }
    const msFlat = (Number(s.ms) || 0) + msInnateFlat + msItemsFlat;
    const msMax = s.slug === 'windrunner' ? 600 : 550;
    const ms = Math.min(Math.round(msFlat * (1 + (itemsTotal.msPct + heroLabInnatePct('ms', s, lvl, includeInnates)) / 100)), msMax);
    const range = (Number(s.range) || 0) + heroLabInnate('range', s, a, lvl, hp, includeInnates) + itemsTotal.range;
    const proj = (Number(s.proj) || 0) + itemsTotal.projSpeed;
    const dvision = Math.round(((Number(s.dvision) || 0) + itemsTotal.dvision) * (1 - itemsTotal.visionReduce / 100));
    const nvision = Math.round(((Number(s.nvision) || 0) + itemsTotal.nvision + heroLabInnate('nvision', s, a, lvl, hp, includeInnates)) * (1 - itemsTotal.visionReduce / 100));
    // Elder Titan Momentum: armor from bonus MS — added after ms is known.
    // Skip when armor was explicitly overridden (custom value is authoritative).
    if (st.custom.armor === null) armor += elderTitanMomentumArmor(s, ms, lvl, includeInnates);
    const armorPct = armorFactor(armor) * 100;
    const manaShield = manaShieldEhp(s, mp, lvl, includeInnates);
    const ehpPhys = hp / Math.max(0.01, 1 - armorFactor(armor)) + manaShield;
    const ehpMag = hp / Math.max(0.01, 1 - mr / 100) + manaShield;
    const lifesteal = itemsTotal.lifesteal + heroLabInnate('lifesteal', s, a, lvl, hp, includeInnates);
    const spellLifesteal = itemsTotal.spellLifesteal;
    const castRange = itemsTotal.castRange + heroLabInnate('castRange', s, a, lvl, hp, includeInnates);
    const itemsCdr = itemsTotal.cooldownReduction || 0;
    // Spell CDR innates (Death Prophet Witchcraft) stack multiplicatively with item CDR.
    const innateCdr = heroLabInnate('cdr', s, a, lvl, hp, includeInnates);
    const cooldownReduction = innateCdr > 0
      ? Math.min(Math.round((1 - (1 - innateCdr / 100) * (1 - itemsCdr / 100)) * 1000) / 10, 99.9)
      : itemsCdr;
    const innateItemCdr = heroLabInnate('itemCdr', s, { str, agi, int }, lvl, hp, includeInnates);
    const itemCdr = innateItemCdr > 0
      ? Math.min(Math.round((1 - (1 - innateItemCdr / 100) * (1 - itemsCdr / 100)) * 1000) / 10, 99.9)
      : 0;
    const dps = tHit > 0 ? dmg / tHit : 0;
    const healthRestoration = itemsTotal.healthRestoration;
    return { hp, mp, hpr, mpr, str, agi, int, armor, armorPct, mr, evasion, statusRes, slowRes, spellAmp, dmg, dmin, dmax, whiteDmin, whiteDmax, aspd, tHit, ms, range, proj, dvision, nvision, ehpPhys, ehpMag, lifesteal, spellLifesteal, castRange, cooldownReduction, itemCdr, healthRestoration, dps, cost: itemsTotal.cost };
  }

  function renderHeroHud(panel, st, vals) {
    const hero = st.hero;
    const portrait = panel.querySelector('.hl-hero-icon');
    const innateChip = panel.querySelector('[data-innate-chip]');
    const innateIcon = panel.querySelector('[data-innate-icon]');
    const hpValue = panel.querySelector('[data-bar-value="hp"]');
    const hpRegen = panel.querySelector('[data-bar-regen="hpr"]');
    const mpValue = panel.querySelector('[data-bar-value="mp"]');
    const mpRegen = panel.querySelector('[data-bar-regen="mpr"]');
    const dpsEl = panel.querySelector('[data-dps-value]');
    const pehpEl = panel.querySelector('[data-pehp-value]');
    const mehpEl = panel.querySelector('[data-mehp-value]');
    const dmgGoldEl = panel.querySelector('[data-dmggold-value]');
    if (portrait) { portrait.src = hero.icon; portrait.alt = hero.name; }
    const innateToggle = document.querySelector('[data-innates-toggle]');
    const innatesOn = innateToggle ? innateToggle.checked : true;
    const statInnate = hero.statInnate || null;
    const showInnate = !!(innatesOn && statInnate && statInnate.icon && statInnate.name);
    if (innateChip && innateIcon) {
      innateChip.classList.toggle('is-hidden', !showInnate);
      innateChip.tabIndex = showInnate ? 0 : -1;
      if (showInnate) {
        innateIcon.src = 'icons/misc/innate_icon.png';
        innateIcon.alt = statInnate.name;
      } else {
      }
    }
    const stBase = { hero: hero || { stats: {}, id: '' }, level: st ? st.level : 1, itemEntries: [], custom: { hp: null, mp: null, hpr: null, mpr: null, armor: null, mr: null, evasion: null } };
    const base = calc(stBase, { includeInnates: false });
    const hpBonus = vals.hp - base.hp;
    const mpBonus = vals.mp - base.mp;
    if (hpValue) hpValue.textContent = hpBonus > 0 ? `${fmt(vals.hp)} (+${fmt(hpBonus)})` : `${fmt(vals.hp)}`;
    if (hpRegen) hpRegen.textContent = `${vals.hpr >= 0 ? '+' : ''}${quickFmt(vals.hpr)}`;
    if (mpValue) mpValue.textContent = mpBonus > 0 ? `${fmt(vals.mp)} (+${fmt(mpBonus)})` : `${fmt(vals.mp)}`;
    if (mpRegen) mpRegen.textContent = `${vals.mpr >= 0 ? '+' : ''}${quickFmt(vals.mpr)}`;
    if (dpsEl) dpsEl.textContent = vals.dps.toFixed(1);
    if (pehpEl) pehpEl.textContent = fmt(Math.round(vals.ehpPhys));
    if (mehpEl) mehpEl.textContent = fmt(Math.round(vals.ehpMag));
    const bonusDps = vals.dps - base.dps;
    if (dmgGoldEl) dmgGoldEl.textContent = bonusDps > 0.01 ? fmt(Math.round(vals.cost / bonusDps)) : '—';
    var costBadge = panel.querySelector('[data-cost-badge]');
    var costValue = panel.querySelector('[data-cost-value]');
    if (costBadge && costValue) {
      var hasCost = !!vals.cost;
      costBadge.classList.toggle('is-empty', !hasCost);
      costValue.textContent = hasCost ? fmt(vals.cost) : '0';
    }

    const slots = safeJsonParse(panel.dataset.items, ["","","","","",""]);
    const itemModes = safeJsonParse(panel.dataset.itemModes, {});
    panel.querySelectorAll('.hl-inv-slot').forEach((slotEl, idx) => {
      const isEnchant = slotEl.dataset.slot === 'enchant';
      const itemId = isEnchant
        ? (panel.dataset.enchantItem || '')
        : (slots[idx] || '');
      const item = byItem.get(itemId);
      const modeKey = item && item.modes ? (itemModes[String(slotEl.dataset.slot)] || item.modes.default || 'damage') : '';
      const visual = item ? itemVisual(item, modeKey) : null;
      slotEl.dataset.itemId = itemId;
      slotEl.classList.toggle('is-empty', !item);
      slotEl.draggable = !!item;
      if (item && item.modes) {
        slotEl.dataset.itemMode = modeKey;
        const accent = itemModeAccent(item, modeKey);
        if (accent) slotEl.dataset.modeAccent = accent;
        else delete slotEl.dataset.modeAccent;
      } else {
        delete slotEl.dataset.itemMode;
        delete slotEl.dataset.modeAccent;
      }
      slotEl.innerHTML = item
        ? `<img src="${visual.icon}" alt="${item.name}" loading="lazy"><span class="hl-slot-bevel"></span><span class="hl-slot-glow"></span>${item && item.modes && !item.tiersAvailable ? `<button type="button" class="hl-slot-mode" data-cycle-item-mode aria-label="Cycle item mode">${itemModeBadge(item, slotEl.dataset.itemMode)}</button>` : ''}<button type="button" class="hl-slot-clear" data-clear-slot aria-label="Remove item">x</button>`
        : `${isEnchant ? '<span class="hl-enchant-mark">E</span>' : ''}<span class="hl-slot-bevel"></span><span class="hl-slot-glow"></span>`;
      slotEl.removeAttribute('title');
      slotEl.classList.remove('hl-slot-drop-target');
    });
  }

  function renderTotals(panel, vals, st) {
    const list = panel.querySelector('[data-total-list]');
    if (!list) return;
    const hero = st ? st.hero : null;
    const s = (hero && hero.stats) ? hero.stats : {};
    // Compute base (no items, no custom overrides) for bonus display
    const stBase = { hero: hero || { stats: {}, id: '' }, level: st ? st.level : 1, itemEntries: [], custom: { hp: null, mp: null, hpr: null, mpr: null, armor: null, mr: null, evasion: null } };
    const base = calc(stBase, { includeInnates: false });
    const attr = s.attr || 'str';
    const strGain = Number(s.strGain) || 0;
    const agiGain = Number(s.agiGain) || 0;
    const intGain = Number(s.intGain) || 0;
    const ATTR_ICONS = {
      str: 'icons/attributes/strength.png',
      agi: 'icons/attributes/agility.png',
      int: 'icons/attributes/intelligence.png',
      uni: 'icons/attributes/universal.png',
    };
    const ATTR_COLORS = {
      str: '#ec3d06',
      agi: '#3ed038',
      int: '#00d9ec',
      uni: '#d9ec00',
    };
    const ATTR_BG = {
      str: 'linear-gradient(to right, #380f01, #000)',
      agi: 'linear-gradient(to right, #09360b, #000)',
      int: 'linear-gradient(to right, #003237, #000)',
      uni: 'linear-gradient(to right, #323700, #000)',
    };
    const fmtStat = v => {
      const n = Number(v) || 0;
      if (Number.isInteger(n)) return String(n);
      return n.toFixed(1).replace(/\.0$/, '');
    };
    const fmtGain = v => {
      const n = Number(v) || 0;
      if (Number.isInteger(n)) return String(n);
      return n.toFixed(2).replace(/\.?0+$/, '');
    };
    const fmtPct = v => (Number(v) || 0).toFixed(1) + '%';
    const mergePositive = heroLabMergePositiveOn();

    // Build bonus HTML: green +N or red −N; returns '' for zero bonus
    const bonusHtml = (delta, fmtFn) => {
      const n = Number(delta) || 0;
      if (Math.abs(n) < 0.0001) return '';
      const sign = n > 0 ? '+' : '−'; // + or −
      const cls = n > 0 ? 'hl-ds-bon-pos' : 'hl-ds-bon-neg';
      return `<span class="${cls}">${sign}${fmtFn(Math.abs(n))}</span>`;
    };
    const bonusInt = delta => bonusHtml(delta, v => String(Math.round(v)));
    const bonusDec1 = delta => bonusHtml(delta, v => v.toFixed(1));
    const bonusDec2 = delta => bonusHtml(delta, v => v.toFixed(2));
    const bonusPct1 = delta => bonusHtml(delta, v => v.toFixed(1) + '%');
    const mergeDisplay = (baseVal, finalVal, delta, fmtBase, isBenefitPositive = true) => {
      const beneficial = isBenefitPositive ? delta > 0.0001 : delta < -0.0001;
      return mergePositive && beneficial ? fmtBase(finalVal) : fmtBase(baseVal);
    };

    const statRow = (label, baseStr, bonStr) => {
      const bon = bonStr || '';
      return `<div class="hl-ds-row"><span class="hl-ds-name">${label}</span><span class="hl-ds-val">${baseStr}${bon ? ' ' + bon : ''}</span></div>`;
    };

    // ATTACK panel rows (base + bonus)
    const aspdBonus = bonusInt(vals.aspd - base.aspd);
    const tHitDiff = vals.tHit - base.tHit;
    const tHitBon = Math.abs(tHitDiff) >= 0.005
      ? `<span class="${tHitDiff < 0 ? 'hl-ds-bon-pos' : 'hl-ds-bon-neg'}">${tHitDiff < 0 ? '-' : '+'}${Math.abs(tHitDiff).toFixed(2)}s</span>`
      : '';
    const dmgBonusAmt = attr === 'uni'
      ? vals.dmin - vals.whiteDmin
      : vals.dmin - base.dmin;
    const dmgBonus = bonusInt(dmgBonusAmt);
    const rangeBonus = bonusInt(vals.range - base.range);
    const msBonus = bonusInt(vals.ms - base.ms);
    const mprBonus = bonusDec2(vals.mpr - base.mpr);
    const spellAmpBonus = bonusPct1(vals.spellAmp - base.spellAmp);

    const lifestealBonus = bonusPct1(vals.lifesteal - base.lifesteal);
    const spellLifestealBonus = bonusPct1(vals.spellLifesteal - base.spellLifesteal);
    const attackRows = [
      statRow('Damage', `${mergeDisplay(attr === 'uni' ? vals.whiteDmin : base.dmin, vals.dmin, dmgBonusAmt, fmt)} - ${mergeDisplay(attr === 'uni' ? vals.whiteDmax : base.dmax, vals.dmax, dmgBonusAmt, fmt)}`, mergePositive && dmgBonusAmt > 0 ? '' : dmgBonus),
      statRow('Attack Speed', mergeDisplay(base.aspd, vals.aspd, vals.aspd - base.aspd, fmt), mergePositive && (vals.aspd - base.aspd) > 0 ? '' : aspdBonus),
      statRow('Attack Interval', `${mergeDisplay(base.tHit, vals.tHit, tHitDiff, v => Number(v || 0).toFixed(2) + 's', false)}`, mergePositive && tHitDiff < 0 ? '' : tHitBon),
      statRow('Attack Range', mergeDisplay(base.range, vals.range, vals.range - base.range, fmt), mergePositive && (vals.range - base.range) > 0 ? '' : rangeBonus),
      statRow('Projectile', mergeDisplay(base.proj || 0, vals.proj || 0, (vals.proj || 0) - (base.proj || 0), fmt), mergePositive && ((vals.proj || 0) - (base.proj || 0)) > 0 ? '' : bonusInt((vals.proj || 0) - (base.proj || 0))),
      statRow('Cast Range', mergeDisplay(base.castRange || 0, vals.castRange || 0, (vals.castRange || 0) - (base.castRange || 0), fmt), mergePositive && ((vals.castRange || 0) - (base.castRange || 0)) > 0 ? '' : bonusInt(vals.castRange - base.castRange)),
      statRow('Move Speed', mergeDisplay(base.ms, vals.ms, vals.ms - base.ms, fmt), mergePositive && (vals.ms - base.ms) > 0 ? '' : msBonus),
      statRow('Spell Amp', mergeDisplay(base.spellAmp, vals.spellAmp, vals.spellAmp - base.spellAmp, fmtPct), mergePositive && (vals.spellAmp - base.spellAmp) > 0 ? '' : spellAmpBonus),
      statRow('Lifesteal', mergeDisplay(base.lifesteal, vals.lifesteal, vals.lifesteal - base.lifesteal, fmtPct), mergePositive && (vals.lifesteal - base.lifesteal) > 0 ? '' : lifestealBonus),
      statRow('Spell Lifesteal', mergeDisplay(base.spellLifesteal, vals.spellLifesteal, vals.spellLifesteal - base.spellLifesteal, fmtPct), mergePositive && (vals.spellLifesteal - base.spellLifesteal) > 0 ? '' : spellLifestealBonus),
      statRow('Mana Regen', mergeDisplay(base.mpr, vals.mpr, vals.mpr - base.mpr, v => Number(v || 0).toFixed(2)), mergePositive && (vals.mpr - base.mpr) > 0 ? '' : mprBonus),
    ].join('');

    // DEFENSE panel rows (base + bonus)
    const armorBonus = bonusDec1(vals.armor - base.armor);
    const armorPctBonus = bonusPct1(vals.armorPct - base.armorPct);
    const mrBonus = bonusPct1(vals.mr - base.mr);
    const evasionBonus = bonusPct1(vals.evasion - base.evasion);
    const hprBonus = bonusDec2(vals.hpr - base.hpr);
    const statusResBonus = bonusPct1(vals.statusRes - base.statusRes);
    const slowResBonus = bonusPct1(vals.slowRes - base.slowRes);

    const defenseRows = [
      statRow('Armor', mergeDisplay(base.armor, vals.armor, vals.armor - base.armor, fmtStat), mergePositive && (vals.armor - base.armor) > 0 ? '' : armorBonus),
      statRow('Physical Resist', mergeDisplay(base.armorPct, vals.armorPct, vals.armorPct - base.armorPct, fmtPct), mergePositive && (vals.armorPct - base.armorPct) > 0 ? '' : armorPctBonus),
      statRow('Magic Resist', mergeDisplay(base.mr, vals.mr, vals.mr - base.mr, fmtPct), mergePositive && (vals.mr - base.mr) > 0 ? '' : mrBonus),
      statRow('Status Resist', mergeDisplay(base.statusRes, vals.statusRes, vals.statusRes - base.statusRes, fmtPct), mergePositive && (vals.statusRes - base.statusRes) > 0 ? '' : statusResBonus),
      statRow('Slow Resist', mergeDisplay(base.slowRes, vals.slowRes, vals.slowRes - base.slowRes, fmtPct), mergePositive && (vals.slowRes - base.slowRes) > 0 ? '' : slowResBonus),
      statRow('Evasion', mergeDisplay(base.evasion, vals.evasion, vals.evasion - base.evasion, fmtPct), mergePositive && (vals.evasion - base.evasion) > 0 ? '' : evasionBonus),
      statRow('Health Regen', mergeDisplay(base.hpr, vals.hpr, vals.hpr - base.hpr, v => Number(v || 0).toFixed(2)), mergePositive && (vals.hpr - base.hpr) > 0 ? '' : hprBonus),
      statRow('Health Restoration', mergeDisplay(base.healthRestoration || 0, vals.healthRestoration || 0, (vals.healthRestoration || 0) - (base.healthRestoration || 0), fmtPct), mergePositive && ((vals.healthRestoration || 0) - (base.healthRestoration || 0)) > 0 ? '' : bonusPct1((vals.healthRestoration || 0) - (base.healthRestoration || 0))),
      statRow('Day Vision', mergeDisplay(base.dvision || 0, vals.dvision || 0, (vals.dvision || 0) - (base.dvision || 0), fmt), mergePositive && ((vals.dvision || 0) - (base.dvision || 0)) > 0 ? '' : bonusInt(vals.dvision - base.dvision)),
      statRow('Night Vision', mergeDisplay(base.nvision || 0, vals.nvision || 0, (vals.nvision || 0) - (base.nvision || 0), fmt), mergePositive && ((vals.nvision || 0) - (base.nvision || 0)) > 0 ? '' : bonusInt(vals.nvision - base.nvision)),
      statRow('Cooldown Reduction', mergeDisplay(base.cooldownReduction || 0, vals.cooldownReduction || 0, (vals.cooldownReduction || 0) - (base.cooldownReduction || 0), fmtPct), mergePositive && ((vals.cooldownReduction || 0) - (base.cooldownReduction || 0)) > 0 ? '' : bonusPct1((vals.cooldownReduction || 0) - (base.cooldownReduction || 0))),
      (vals.itemCdr || base.itemCdr) ? statRow('Item CDR', mergeDisplay(base.itemCdr || 0, vals.itemCdr || 0, (vals.itemCdr || 0) - (base.itemCdr || 0), fmtPct), mergePositive && ((vals.itemCdr || 0) - (base.itemCdr || 0)) > 0 ? '' : bonusPct1((vals.itemCdr || 0) - (base.itemCdr || 0))) : '',
    ].join('');

    // Attribute rows builder — shows base attr + item bonus on the number
    const attrRow = (key, baseAttr, totalAttr, gainVal, bonusLine, detailLine, isPrimary) => {
      const icon = ATTR_ICONS[key] || ATTR_ICONS.str;
      const color = ATTR_COLORS[key];
      const bg = isPrimary ? `style="background:${ATTR_BG[key]};margin-left:0"` : '';
      const attrDelta = totalAttr - baseAttr;
      const attrBon = mergePositive && attrDelta > 0 ? '' : bonusInt(attrDelta);
      const shownBase = mergePositive && attrDelta > 0 ? totalAttr : baseAttr;
      const primaryBonus = isPrimary
        ? `<div class="hl-da-primary" style="color:${color}">${bonusLine}</div>`
        : '';
      return `
        <div class="hl-da-row${isPrimary ? ' hl-da-primary-row' : ''}" ${bg}>
          <img class="hl-da-icon" src="${icon}" alt="${key}" loading="lazy">
          <div class="hl-da-details">
            <div class="hl-da-top">
              <span class="hl-da-base">${fmt(shownBase)}${attrBon ? ' ' + attrBon : ''}</span>
              <span class="hl-da-gain">(Gains ${fmtGain(gainVal)} per lvl)</span>
            </div>
            ${primaryBonus}
            <div class="hl-da-breakdown">${detailLine}</div>
          </div>
        </div>`;
    };

    // Compute primary damage bonus text (using final vals for display)
    let primaryDmgStr, primaryDmgAgi, primaryDmgInt, primaryDmgUni;
    if (attr === 'str') {
      primaryDmgStr = `= ${fmt(vals.str)} Damage (Primary Role Bonus)`;
    } else if (attr === 'agi') {
      primaryDmgAgi = `= ${fmt(vals.agi)} Damage (Primary Role Bonus)`;
    } else if (attr === 'int') {
      primaryDmgInt = `= ${fmt(vals.int)} Damage (Primary Role Bonus)`;
    } else if (attr === 'uni') {
      const uniTotal = vals.str + vals.agi + vals.int;
      primaryDmgUni = `= ${fmt(Math.floor(uniTotal * C.uniDmg))} Damage (Primary Role Bonus)`;
    }

    const strDetail = `= ${fmt(vals.str * C.hpStr)} HP and ${Number(vals.str * C.hprStr).toFixed(2)} HP Regen`;
    const agiDetail = `= ${Number(vals.agi * C.armorAgi).toFixed(2)} Armor and ${fmt(vals.agi * C.asAgi)} Attack Speed`;
    const mrFromInt = Number(vals.int * C.mrInt).toFixed(1);
    const intDetail = `= ${fmt(vals.int * C.mpInt)} Mana, ${Number(vals.int * C.mprInt).toFixed(2)} Mana Regen and ${mrFromInt}% Base Magic Resistance`;

    const plus2 = plus2At(st.level);
    const strRow = attrRow('str', base.str - plus2, vals.str, strGain, primaryDmgStr, strDetail, attr === 'str');
    const agiRow = attrRow('agi', base.agi - plus2, vals.agi, agiGain, primaryDmgAgi, agiDetail, attr === 'agi');
    const intRow = attrRow('int', base.int - plus2, vals.int, intGain, primaryDmgInt, intDetail, attr === 'int');
    let uniRow = '';
    if (attr === 'uni') {
      const uniBase = base.str + base.agi + base.int;
      const uniTotal = vals.str + vals.agi + vals.int;
      const uniDelta = uniTotal - uniBase;
      const uniBon = mergePositive && uniDelta > 0 ? '' : bonusInt(uniDelta);
      const uniShown = mergePositive && uniDelta > 0 ? uniTotal : uniBase;
      const innateToggle = document.querySelector('[data-innates-toggle]');
      const hlInnatesOn = innateToggle ? innateToggle.checked : true;
      const uniDmgGain = (strGain + agiGain + intGain) * universalDmgMult(s, hlInnatesOn);
      const uniGainStr = uniDmgGain.toFixed(1).replace(/\.0$/, '');
      uniRow = `
        <div class="hl-da-row hl-da-primary-row" style="background:${ATTR_BG.uni};margin-left:0">
          <img class="hl-da-icon" src="${ATTR_ICONS.uni}" alt="uni" loading="lazy">
          <div class="hl-da-details">
            <div class="hl-da-top">
              <span class="hl-da-base">${fmt(uniShown)}${uniBon ? ' ' + uniBon : ''}</span>
              <span class="hl-da-gain">(Gains ${uniGainStr} damage per lvl)</span>
            </div>
            <div class="hl-da-primary" style="color:${ATTR_COLORS.uni}">${primaryDmgUni}</div>
          </div>
        </div>`;
    }

    list.innerHTML = `
      <div class="hl-dota-stats">
        <div class="hl-dota-combat">
          <section class="hl-dota-stat-panel hl-dota-attack">
            <h3 class="hl-ds-head">ATTACK</h3>
            ${attackRows}
          </section>
          <section class="hl-dota-stat-panel hl-dota-defense">
            <h3 class="hl-ds-head">DEFENSE</h3>
            ${defenseRows}
          </section>
        </div>
        <div class="hl-dota-attributes">
          ${strRow}
          ${agiRow}
          ${intRow}
          ${uniRow}
        </div>
      </div>
    `;
  }

  function heroPickerMarkup(selectedId) {
    return `
      <div class="hl-picker-card hl-hero-picker-card" role="dialog" aria-modal="true" aria-label="Choose hero">
        <div class="hl-picker-head">
          <strong>Choose Hero</strong>
          <button type="button" class="hl-picker-close" data-picker-close aria-label="Close">x</button>
        </div>
        <div class="hl-picker-searchbar">
          <input type="text" class="hl-picker-search" data-hero-search placeholder="Search hero..." aria-label="Search hero" autocomplete="off">
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

  // Item Changes index look (ecShopMarkup): Basics | Upgrades panels for the shop,
  // one "Neutral Enchantments" panel for the enchantment slot.
  const HL_SHOP_PANELS = [
    ['Basics', 'basics', ['Consumables', 'Attributes', 'Equipment', 'Miscellaneous', 'Secret Shop', 'Other']],
    ['Upgrades', 'upgrades', ['Accessories', 'Support', 'Magical', 'Armor', 'Weapons', 'Armaments']],
  ];
  function hlTile(item, selectedId, extraCls, attrs) {
    return `<button type="button" class="ec-card ec-card-item hl-item-tile${item.id === selectedId ? ' is-selected' : ''}${extraCls || ''}" data-item-id="${item.id}" aria-label="${item.name}"${attrs || ''}>
                  <img src="${item.icon}" alt="${item.name}" loading="lazy">
                </button>`;
  }

  function itemPickerMarkup(selectedId, tab, mode, heroAttr, baubleActive) {
    // no title words: the search box (shop) and the close button share the top row
    const head = search => `
        <div class="ec-picker-top${search ? '' : ' is-bare'}">${search ? `
          <input type="text" class="hl-picker-search" data-item-search placeholder="Search item..." aria-label="Search item" autocomplete="off">` : ''}
          <button type="button" class="hl-picker-close" data-picker-close aria-label="Close"></button>
        </div>`;
    if (mode === 'enchant') {
      const tiles = filteredEnchants(heroAttr).map(item => {
        const isT5 = item.tiersAvailable && item.tiersAvailable.indexOf(5) >= 0;
        const dimmed = baubleActive && !isT5;
        return hlTile(item, selectedId, dimmed ? ' hl-enchant-bauble-dim' : '',
                      dimmed ? ' title="Enchanter&#39;s Bauble only works with Tier 5 enchants"' : '');
      }).join('');
      return `
      <div class="hl-picker-card hl-item-picker-card hl-enchant-picker ec-shop-card" role="dialog" aria-modal="true" aria-label="Choose enchantment">
        ${head(false)}
        <div class="hl-shop-body">${ecShopMarkup([{ title: 'Enchantments', one: true, neutral: true, groups: [{ tiles }] }])}</div>
      </div>`;
    }
    const panels = HL_SHOP_PANELS.map(([title, key, cats]) => ({ title, groups: cats.map(n => {
      const g = (itemGroups[key] || []).find(x => x[0] === n);
      return { title: n, tiles: g ? g[1].map(item => hlTile(item, selectedId)).join('') : '' };
    }) }));
    return `
      <div class="hl-picker-card hl-item-picker-card ec-shop-card is-wide" role="dialog" aria-modal="true" aria-label="Choose item">
        ${head(true)}
        <div class="hl-shop-body">${ecShopMarkup(panels)}</div>
      </div>`;
  }

  function closePicker() {
    activePicker = null;
    overlay.hidden = true;
    overlay.classList.remove('is-open');
    hideTooltip();
  }

  function openHeroPicker(panel) {
    activePicker = { kind: 'hero', panel };
    _itemPickerCacheKey = null;
    overlay.innerHTML = heroPickerMarkup(panel.dataset.hero || heroes[0].id);
    overlay.hidden = false;
    overlay.classList.add('is-open');
    const input = overlay.querySelector('[data-hero-search]');
    if (input) input.focus();
  }

  function showEnchantTierPicker(panel, item) {
    hideTooltip();
    const tiers = item.tiersAvailable;
    const bonusLines = tiers.map(t => {
      const mode = item.modes ? item.modes['t' + t] : null;
      if (!mode) return '';
      return Object.entries(mode).filter(([k,v]) => k !== 'level' && Math.abs(v) > 0.001)
        .map(([k,v]) => `${BONUS_LABELS[k] || k}: ${BONUS_PCT.has(k) ? fmtNum(v) + '%' : fmtNum(v)}`).join(', ');
    });
    _itemPickerCacheKey = null;
    overlay.innerHTML = `
      <div class="hl-picker-card hl-tier-picker" role="dialog" aria-modal="true">
        <div class="hl-picker-head">
          <button type="button" class="hl-picker-back" data-picker-back aria-label="Back"><svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="9,2 4,7 9,12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
          <img src="${item.icon}" style="width:28px;height:28px;border-radius:3px;margin-right:6px">
          <strong>${item.name}</strong>
          <div class="hl-picker-actions">
            <button type="button" class="hl-picker-close" data-picker-close aria-label="Close"><svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg"><line x1="1" y1="1" x2="11" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="11" y1="1" x2="1" y2="11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
          </div>
        </div>
        <div class="hl-tier-list">
          ${tiers.map((t, i) => `<button type="button" class="hl-tier-option" data-item-id="${item.id}" data-enchant-tier="${t}">
            <span class="hl-tier-label">Tier ${t}</span>
            <span class="hl-tier-stats">${bonusLines[i] || '—'}</span>
          </button>`).join('')}
        </div>
      </div>`;
  }

  var _itemPickerCacheKey = null;

  function openItemPicker(panel, slot) {
    const itemsState = safeJsonParse(panel.dataset.items, ["","","","","",""]);
    const mode = slot === 'enchant' ? 'enchant' : 'normal';
    const heroId = panel.dataset.hero || '';
    const heroObj = byHero.get(heroId);
    const heroAttr = heroObj ? (heroObj.stats || {}).attr : null;
    const bl = Math.max(0, Math.min(100, parseInt((panel.querySelector('[data-field="bauble-level"]') || {}).value || '0', 10) || 0));
    const baubleActive = bl > 0;
    activePicker = { kind: 'item', panel, slot, mode, tab: 'basics', heroAttr, baubleActive };
    const selectedId = mode === 'enchant'
      ? (panel.dataset.enchantItem || '')
      : (itemsState[slot] || '');
    const cacheKey = mode + '|' + heroAttr + '|' + baubleActive;
    if (_itemPickerCacheKey !== cacheKey) {
      overlay.innerHTML = itemPickerMarkup(selectedId, null, mode, heroAttr, baubleActive);
      _itemPickerCacheKey = cacheKey;
    } else {
      overlay.querySelectorAll('.hl-item-tile.is-selected').forEach(el => el.classList.remove('is-selected'));
      if (selectedId) {
        const sel = overlay.querySelector(`.hl-item-tile[data-item-id="${selectedId}"]`);
        if (sel) sel.classList.add('is-selected');
      }
    }
    overlay.hidden = false;
    overlay.classList.add('is-open');
    // reset the search and highlight the current item, then focus for keyboard use
    const isearch = overlay.querySelector('[data-item-search]');
    if (isearch) {
      isearch.value = '';
      overlay.querySelectorAll('.hl-item-tile').forEach(t => {
        t.classList.remove('is-hidden');
        t.classList.toggle('is-selected', !!selectedId && t.dataset.itemId === selectedId);
      });
      overlay.querySelectorAll('.hl-item-section').forEach(s => s.classList.remove('is-hidden'));
      isearch.focus();
    }
  }



  function update() {
    const panels = [...root.querySelectorAll('.hl-panel')];
    panels.forEach(p => updateLevelRing(p));
    const aState = state(panels[0]);
    const bState = state(panels[1]);
    const a = calc(aState);
    const b = calc(bState);
    panels[0].dataset.cdr = String(a.cooldownReduction || 0);
    panels[1].dataset.cdr = String(b.cooldownReduction || 0);
    panels.forEach(panel => {
      var _modes = {};
      _modes = safeJsonParse(panel.dataset.itemModes, {});
      var _enchantMode = _modes.enchant || null;
      var _enchantId = panel.dataset.enchantItem || '';
      var _bl = Math.max(0, Math.min(100, parseInt((panel.querySelector('[data-field="bauble-level"]') || {}).value || '0', 10) || 0));
      var _baubleActive = _bl > 0;
      var _enchantIsT5 = _enchantMode === 't5';
      var _enchantSlot = panel.querySelector('[data-slot="enchant"]');
      // Enchant slot: dimmed when bauble>0 and enchant equipped but not t5
      if (_enchantSlot) _enchantSlot.classList.toggle('hl-enchant-bauble-mismatch', _baubleActive && !!_enchantId && !_enchantIsT5);
      // Bauble slot: never disabled by itself — remove old class if present
      var _bSlot = panel.querySelector('.hl-bauble-slot');
      if (_bSlot) _bSlot.classList.remove('hl-bauble-disabled');
    });
    renderHeroHud(panels[0], aState, a);
    renderHeroHud(panels[1], bState, b);
    renderTotals(panels[0], a, aState);
    renderTotals(panels[1], b, bState);
    const diff = document.getElementById('hl-diff-list');
    const diffPctOn = heroLabDiffPercentOn();
    diff.innerHTML = METRICS.map(([key, label]) => {
      const leftVal = Number(a[key] || 0);
      const rightVal = Number(b[key] || 0);
      const rawDelta = leftVal - rightVal;
      const delta = key === 'tHit' ? -rawDelta : rawDelta;
      const avgMag = (Math.abs(leftVal) + Math.abs(rightVal)) / 2;
      const pctAbs = avgMag < 0.0001 ? (Math.abs(leftVal - rightVal) < 0.0001 ? 0 : 200) : (Math.abs(leftVal - rightVal) / avgMag) * 100;
      const diffValue = diffPctOn ? (delta === 0 ? 0 : (delta > 0 ? pctAbs : -pctAbs)) : delta;
      const cls = delta > 0 ? 'pos' : delta < 0 ? 'neg' : 'zero';
      const side = delta > 0 ? 'left' : delta < 0 ? 'right' : 'none';
      return `<div class="hl-diff-row ${cls}" data-adv="${side}" data-diff-key="${key}"
        <strong class="hl-diff-side hl-diff-left">${fmtMetric(key, leftVal)}</strong>
        <span class="hl-diff-center">
          <span class="hl-diff-label">${label}</span>
          <strong class="hl-diff-mid ${cls}">${diffPctOn ? fmt(diffValue, 1) + '%' : fmtDiffMetric(key, diffValue)}</strong>
        </span>
        <strong class="hl-diff-side hl-diff-right">${fmtMetric(key, rightVal)}</strong>
      </div>`;
    }).join('');
    applyDiffCatFilter();
  }
  function applyDiffCatFilter() {
    const menu = document.querySelector('.hd-dd-menu[data-dd="diffstat"]');
    if (!menu) return;
    const checked = new Set([...menu.querySelectorAll('input[data-diffstat]:checked')].map(i => i.dataset.diffstat));
    document.querySelectorAll('#hl-diff-list .hl-diff-row').forEach(row => {
      row.classList.toggle('diff-cat-hidden', !checked.has(row.dataset.diffKey));
    });
  }

  const panels = [...root.querySelectorAll('.hl-panel')];
  // left defaults to the first hero of the picker grid (Alchemist), right keeps Abaddon
  const leftDefaultHero = byHero.has('alchemist') ? 'alchemist' : heroes[Math.min(1, heroes.length - 1)].id;
  renderPanel(panels[0], 'a', leftDefaultHero);
  renderPanel(panels[1], 'b', heroes[0].id);
  panels.forEach(p => updateLevelRing(p));
  (function() {
    const dd = document.querySelector('.hero-lab-toolbar .hd-dd[data-dd="diffstat"]');
    if (!dd) return;
    const btn = dd.querySelector('.hd-dd-btn');
    const menu = dd.querySelector('.hd-dd-menu');
    const badge = dd.querySelector('.hd-dd-badge');
    menu.innerHTML =
      '<label class="hd-dd-opt hd-dd-all"><input type="checkbox" data-dd-all><span>All</span></label>' +
      '<div class="hd-dd-sep" aria-hidden="true"></div>' +
      METRICS.map(([key, label]) =>
        `<label class="hd-dd-opt"><input type="checkbox" data-diffstat="${key}" checked><span>${label}</span></label>`
      ).join('');
    const allBox = menu.querySelector('input[data-dd-all]');
    const boxes = [...menu.querySelectorAll('input[data-diffstat]')];
    document.body.appendChild(menu);
    menu.style.position = 'fixed';
    // kept on the screen: on a phone the 4-column stat menu ran 220px past the right edge (audit 2026-11-08)
    const place = () => {
      const r = btn.getBoundingClientRect();
      menu.style.top = (r.bottom + 6) + 'px';
      menu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - menu.offsetWidth - 8)) + 'px';
    };
    const sync = () => {
      const n = boxes.filter(b => b.checked).length;
      if (badge) badge.textContent = n === boxes.length ? 'all' : String(n);
      if (allBox) { allBox.checked = n === boxes.length; allBox.indeterminate = n > 0 && n < boxes.length; }
    };
    sync();
    btn.addEventListener('click', (e) => { e.stopPropagation(); const open = menu.hidden; menu.hidden = !open; btn.setAttribute('aria-expanded', String(open)); if (open) place(); });
    menu.addEventListener('click', (e) => e.stopPropagation());
    if (allBox) allBox.addEventListener('change', () => { boxes.forEach(b => { b.checked = allBox.checked; }); sync(); applyDiffCatFilter(); });
    boxes.forEach(b => b.addEventListener('change', () => { sync(); applyDiffCatFilter(); }));
    document.addEventListener('click', () => { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); });
    window.addEventListener('scroll', (e) => { if (!menu.contains(e.target)) { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); } }, true);
  })();
  function updateLevelRing(panel) {
    const lvl = Math.max(1, Math.min(30, parseInt(panel.querySelector('[data-field="level"]')?.value || '1', 10) || 1));
    const ring = panel.querySelector('[data-ring]');
    if (!ring) return;
    const circ = 2 * Math.PI * 18;
    const fill = (lvl / 30) * circ;
    ring.style.strokeDasharray = fill + ' ' + circ;
    ring.style.stroke = lvl >= 30 ? '#ffcc44' : '#E7D291';
  }

  root.addEventListener('input', (e) => {
    if (e.target.matches('[data-field="level"]')) {
      const clean = String(e.target.value || '').replace(/[^\d]/g, '').slice(0, 2);
      e.target.value = clean || '';
      const panel = e.target.closest('.hl-panel');
      if (panel) updateLevelRing(panel);
      update();
      return;
    }
    if (e.target.matches('[data-field="bauble-level"]')) {
      const raw = parseInt(e.target.value || '0', 10) || 0;
      const clamped = Math.max(0, Math.min(100, raw));
      if (raw !== clamped) e.target.value = clamped || '';
      update();
      const panel = e.target.closest('.hl-panel');
      if (panel) {
        const slot = panel.querySelector('.hl-bauble-slot');
        if (slot) slot.classList.toggle('is-active', clamped > 0);
      }
      return;
    }
    if (e.target.matches('[data-custom]')) update();
  });
  document.addEventListener('change', (e) => {
    if (e.target.matches('[data-innates-toggle], [data-hl-merge-positive-toggle], [data-hl-diff-percent-toggle]')) {
      update();
    }
  });
  root.addEventListener('focusin', (e) => {
    if (e.target.matches('[data-field="level"]')) {
      requestAnimationFrame(() => e.target.select());
    }
  });
  root.addEventListener('mouseup', (e) => {
    if (e.target.matches('[data-field="level"]')) {
      e.target.select();
    }
  });
  root.addEventListener('dragstart', (e) => {
    const slotEl = e.target.closest('.hl-inv-slot');
    if (!slotEl || slotEl.classList.contains('is-empty') || !slotEl.dataset.itemId) {
      e.preventDefault();
      return;
    }
    const panel = slotEl.closest('.hl-panel');
    if (!panel) {
      e.preventDefault();
      return;
    }
    dragState = { panel, slot: slotEl.dataset.slot };
    suppressSlotClickUntil = Date.now() + 250;
    slotEl.classList.add('hl-slot-dragging');
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', `${panel.dataset.side}:${slotEl.dataset.slot}`);
    }
  });
  root.addEventListener('dragover', (e) => {
    const slotEl = e.target.closest('.hl-inv-slot');
    if (!slotEl || !dragState) return;
    const panel = slotEl.closest('.hl-panel');
    if (!panel) return;
    const srcPanel = dragState.panel;
    const srcSlot = dragState.slot;
    const dstSlot = slotEl.dataset.slot;
    const src = getSlotState(srcPanel, srcSlot);
    const dst = getSlotState(panel, dstSlot);
    const srcItem = src.id ? byItem.get(src.id) : null;
    const dstItem = dst.id ? byItem.get(dst.id) : null;
    const valid = !!srcItem && slotAcceptsItem(dstSlot, srcItem) && (!dstItem || slotAcceptsItem(srcSlot, dstItem));
    if (!valid) return;
    e.preventDefault();
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
    root.querySelectorAll('.hl-slot-drop-target').forEach(el => el.classList.remove('hl-slot-drop-target'));
    slotEl.classList.add('hl-slot-drop-target');
  });
  root.addEventListener('drop', (e) => {
    const slotEl = e.target.closest('.hl-inv-slot');
    if (!slotEl || !dragState) return;
    const panel = slotEl.closest('.hl-panel');
    if (!panel) return;
    e.preventDefault();
    const ok = swapSlots(dragState.panel, dragState.slot, panel, slotEl.dataset.slot);
    root.querySelectorAll('.hl-slot-drop-target').forEach(el => el.classList.remove('hl-slot-drop-target'));
    root.querySelectorAll('.hl-slot-dragging').forEach(el => el.classList.remove('hl-slot-dragging'));
    dragState = null;
    if (ok) update();
  });
  root.addEventListener('dragend', () => {
    root.querySelectorAll('.hl-slot-drop-target').forEach(el => el.classList.remove('hl-slot-drop-target'));
    root.querySelectorAll('.hl-slot-dragging').forEach(el => el.classList.remove('hl-slot-dragging'));
    dragState = null;
  });
  root.addEventListener('click', (e) => {
    if (e.target.closest('.hl-level-corner')) return;
    const heroBtn = e.target.closest('[data-open-hero-picker]');
    if (heroBtn) {
      openHeroPicker(heroBtn.closest('.hl-panel'));
      return;
    }
    const modeBtn = e.target.closest('[data-cycle-item-mode]');
    if (modeBtn) {
      e.stopPropagation();
      const slotEl = modeBtn.closest('.hl-inv-slot');
      const panel = modeBtn.closest('.hl-panel');
      if (slotEl && panel) {
        const item = byItem.get(slotEl.dataset.itemId || '');
        if (item && item.modes) {
          const modes = Object.keys(item.modes).filter(k => k !== 'default' && k !== 'base');
          const modeKey = String(slotEl.dataset.slot);
          const itemModes = safeJsonParse(panel.dataset.itemModes, {});
          const current = itemModes[modeKey] || item.modes.default || modes[0] || 'damage';
          const idx = Math.max(0, modes.indexOf(current));
          itemModes[modeKey] = modes[(idx + 1) % modes.length] || current;
          panel.dataset.itemModes = JSON.stringify(itemModes);
          update();
        }
      }
      return;
    }
    const clearBtn = e.target.closest('[data-clear-slot]');
    if (clearBtn) {
      e.stopPropagation();
      var slotEl = clearBtn.closest('.hl-inv-slot');
      var panel = clearBtn.closest('.hl-panel');
      if (slotEl && panel) {
        var sl = slotEl.dataset.slot;
        var itemModes = safeJsonParse(panel.dataset.itemModes, {});
        if (sl === 'enchant') { panel.dataset.enchantItem = ''; }
        else { var its = safeJsonParse(panel.dataset.items, ["","","","","",""]); its[Number(sl)] = ''; panel.dataset.items = JSON.stringify(its); }
        delete itemModes[String(sl)];
        panel.dataset.itemModes = JSON.stringify(itemModes);
        update();
      }
      return;
    }
    const itemBtn = e.target.closest('[data-open-item-picker]');
    if (itemBtn) {
      if (Date.now() < suppressSlotClickUntil) return;
      if (itemBtn.dataset.slot === 'enchant') {
        openItemPicker(itemBtn.closest('.hl-panel'), 'enchant');
        return;
      }
      openItemPicker(itemBtn.closest('.hl-panel'), Number(itemBtn.dataset.slot || 0));
      return;
    }
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.closest('[data-picker-close]')) {
      closePicker();
      return;
    }
    if (e.target.closest('[data-picker-back]')) {
      if (activePicker && activePicker.panel) openItemPicker(activePicker.panel, 'enchant');
      return;
    }
    const heroTile = e.target.closest('[data-hero-id]');
    if (heroTile && activePicker?.kind === 'hero') {
      activePicker.panel.dataset.hero = heroTile.dataset.heroId;
      closePicker();
      update();
      return;
    }
    const tierBtn = e.target.closest('[data-enchant-tier]');
    if (tierBtn && activePicker?.kind === 'item' && activePicker.slot === 'enchant') {
      const itemModes = JSON.parse(activePicker.panel.dataset.itemModes || '{}');
      activePicker.panel.dataset.enchantItem = tierBtn.dataset.itemId || '';
      itemModes.enchant = 't' + tierBtn.dataset.enchantTier;
      Object.keys(itemModes).forEach(key => itemModes[key] === undefined && delete itemModes[key]);
      activePicker.panel.dataset.itemModes = JSON.stringify(itemModes);
      closePicker();
      update();
      return;
    }
    const itemTile = e.target.closest('[data-item-id]');
    if (itemTile && activePicker?.kind === 'item') {
      const item = byItem.get(itemTile.dataset.itemId || '');
      const itemModes = JSON.parse(activePicker.panel.dataset.itemModes || '{}');
      if (activePicker.slot === 'enchant') {
        if (item && item.tiersAvailable && item.tiersAvailable.length > 1) {
          showEnchantTierPicker(activePicker.panel, item);
          return;
        }
        activePicker.panel.dataset.enchantItem = itemTile.dataset.itemId || '';
        itemModes.enchant = item?.tiersAvailable?.length ? 't' + item.tiersAvailable[0] : (item?.modes ? (Object.keys(item.modes)[0] || 'damage') : 'damage');
      } else {

        const slots = JSON.parse(activePicker.panel.dataset.items || '["","","","","",""]');
        slots[activePicker.slot] = itemTile.dataset.itemId || '';
        activePicker.panel.dataset.items = JSON.stringify(slots);
        let initialMode = item && item.modes ? (item.modes.default || 'damage') : undefined;
        if (item && item.id === 'item_power_treads') {
          const panelHero = byHero.get(activePicker.panel.dataset.hero || '') || heroes[0];
          const pAttr = panelHero && panelHero.stats && panelHero.stats.attr;
          initialMode = (pAttr === 'agi' || pAttr === 'int') ? pAttr : 'str';
        }
        itemModes[String(activePicker.slot)] = initialMode;
      }
      Object.keys(itemModes).forEach(key => itemModes[key] === undefined && delete itemModes[key]);
      activePicker.panel.dataset.itemModes = JSON.stringify(itemModes);
      if (activePicker.slot === 'enchant') {
        syncEnchantMode(activePicker.panel);
      }
      closePicker();
      update();
    }
  });
  // search filter + keyboard navigation, shared by the hero picker and the item shop
  const HL_SEARCH_SEL = '[data-hero-search], [data-item-search]';
  const hlTiles = (input) => input.matches('[data-hero-search]')
    ? { tile: '.hl-hero-tile', group: '.hl-hero-group' }
    : { tile: '.hl-item-tile', group: '.hl-item-section' };
  overlay.addEventListener('input', (e) => {
    const input = e.target.closest(HL_SEARCH_SEL);
    if (!input) return;
    const sel = hlTiles(input);
    const q = String(input.value || '').trim().toLowerCase();
    overlay.querySelectorAll(sel.tile).forEach(tile => {
      const name = String(tile.getAttribute('aria-label') || '').toLowerCase();
      tile.classList.toggle('is-hidden', !!q && !name.includes(q));
    });
    overlay.querySelectorAll(sel.group).forEach(group => {
      const anyVisible = [...group.querySelectorAll(sel.tile)].some(tile => !tile.classList.contains('is-hidden'));
      group.classList.toggle('is-hidden', !anyVisible);
    });
    // while searching, keep the first match highlighted so Enter / arrows have a starting point
    const visible = [...overlay.querySelectorAll(sel.tile + ':not(.is-hidden)')];
    if (q && visible.length && !overlay.querySelector(sel.tile + '.is-selected:not(.is-hidden)')) {
      overlay.querySelectorAll(sel.tile).forEach(tile => tile.classList.toggle('is-selected', tile === visible[0]));
    }
  });
  // keyboard navigation (hero picker contributed by r41ngee, PR #12; extended to the item shop)
  overlay.addEventListener('keydown', (e) => {
    const input = e.target.closest(HL_SEARCH_SEL);
    if (!input) return;
    const tileSel = hlTiles(input).tile;
    if (e.key === 'Escape') {
      e.preventDefault();
      if (input.value) {                       // has text → clear the search
        input.value = '';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.focus();
      } else {                                 // already empty → close the picker
        closePicker();
      }
      return;
    }
    const visible = [...overlay.querySelectorAll(tileSel + ':not(.is-hidden)')];
    if (!visible.length) return;
    if (e.key === 'Enter') {
      e.preventDefault();
      const chosen = overlay.querySelector(tileSel + '.is-selected:not(.is-hidden)') || visible[0];
      if (chosen) chosen.click();              // reuse the tile's own click handler (hero or item)
      return;
    }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      const current = overlay.querySelector(tileSel + '.is-selected:not(.is-hidden)') || visible[0];
      const cur = current.getBoundingClientRect();
      const cx0 = cur.left + cur.width / 2, cy0 = cur.top + cur.height / 2;
      // spatial move: pick the nearest visible tile in the pressed direction (works across columns)
      let best = null, bestScore = Infinity;
      for (const tile of visible) {
        if (tile === current) continue;
        const r = tile.getBoundingClientRect();
        const dx = (r.left + r.width / 2) - cx0, dy = (r.top + r.height / 2) - cy0;
        let along, across;
        if (e.key === 'ArrowRight') { if (dx <= 1) continue; along = dx; across = Math.abs(dy); }
        else if (e.key === 'ArrowLeft') { if (dx >= -1) continue; along = -dx; across = Math.abs(dy); }
        else if (e.key === 'ArrowDown') { if (dy <= 1) continue; along = dy; across = Math.abs(dx); }
        else { if (dy >= -1) continue; along = -dy; across = Math.abs(dx); }
        const score = along + across * 2;     // prefer tiles aligned with the movement axis
        if (score < bestScore) { bestScore = score; best = tile; }
      }
      if (best) {
        overlay.querySelectorAll(tileSel).forEach(tile => tile.classList.toggle('is-selected', tile === best));
        best.scrollIntoView({ block: 'nearest', inline: 'nearest' });
      }
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !overlay.hidden) {
      const input = overlay.querySelector(HL_SEARCH_SEL);
      if (input && document.activeElement === input) return;   // handled by the picker's own Escape
      closePicker();
    }
  });

  // ---- Item tooltip ----
  const BONUS_LABELS = {
    all: 'All Attributes',
    str: 'Strength', agi: 'Agility', int: 'Intelligence',
    hp: 'Health', mp: 'Mana', hpr: 'Health Regeneration', mpr: 'Mana Regeneration',
    armor: 'Armor', mr: 'Magic Resistance', evasion: 'Evasion',
    damage: 'Damage', damageMelee: 'Damage (Melee)', damageRanged: 'Damage (Ranged)',
    aspd: 'Attack Speed', ms: 'Movement Speed', msMelee: 'Movement Speed (Melee)',
    msRanged: 'Movement Speed (Ranged)', range: 'Attack Range',
    dvision: 'Day Vision', nvision: 'Night Vision',
    spellAmp: 'Spell Amplification', statusRes: 'Status Resistance', slowRes: 'Slow Resistance',
    mprAmp: 'Mana Regen Amplification',
    hprPct: 'HP Regen %', missingHprPct: 'Missing HP Regen', mpPct: 'Max Mana %',
    lifesteal: 'Lifesteal', spellLifesteal: 'Spell Lifesteal', castRange: 'Cast Range',
    primaryStat: 'Primary Attribute', primaryStatUni: 'Primary Attribute (Universal)',
    damagePct: 'Damage %',
    batReduce: 'BAT Reduction', healthRestoration: 'Health Restoration',
    cooldownReduction: 'Cooldown Reduction', debuffAmp: 'Debuff Amplification',
    hpPct: 'Max Health %', msPct: 'Movement Speed %', knockbackResist: 'Knockback Resistance',
    incomingDamage: 'Incoming Damage', magicDamage: 'Magic Damage',
    castSpeed: 'Cast Speed', visionReduce: 'Vision',
    manacostIncrease: 'Manacost / Mana Loss Increase', intelligencePct: 'Intelligence %',
    maxHpRegen: 'Max Health Regen', hpRegenReduce: 'Health Regeneration',
    manacostReduction: 'Manacost Reduction',
    gpm: 'Gold Per Minute', xpm: 'XP Per Minute',
    aspdPct: 'Attack Speed',
    manaReductionPct: 'Max Mana',
  };
  const BONUS_PCT = new Set(['mr', 'evasion', 'spellAmp', 'statusRes', 'slowRes', 'mprAmp', 'hprPct', 'mpPct', 'lifesteal', 'spellLifesteal', 'damagePct', 'batReduce', 'cooldownReduction', 'debuffAmp', 'hpPct', 'msPct', 'knockbackResist', 'incomingDamage', 'castSpeed', 'visionReduce', 'manacostIncrease', 'intelligencePct', 'manacostReduction', 'maxHpRegen', 'aspdPct', 'manaReductionPct', 'healthRestoration', 'itemCdr']);
  function fmtNum(v) { var n = Math.abs(v); return n === Math.floor(n) ? String(n) : n % 1 === 0 ? String(n) : n.toFixed(2).replace(/0+$/, '').replace(/\.$/, ''); }
  function fmtBonusVal(k, v, flip) { var dv = flip ? -v : v; var av = fmtNum(dv); var sign = dv >= 0 ? '+' : '-'; return BONUS_PCT.has(k) ? sign + av + '%' : sign + av; }
  const BONUS_FLIP_NEG = new Set(['hpRegenReduce', 'manaReductionPct', 'visionReduce']);
  const BONUS_RED_POS = new Set(['incomingDamage', 'manacostIncrease']);

  var tipEl = document.createElement('div');
  tipEl.className = 'hl-tooltip';
  tipEl.hidden = true;
  document.body.appendChild(tipEl);
  var tipCurrentTile = null;
  var innateTipEl = document.createElement('div');
  innateTipEl.className = 'hl-tooltip hl-innate-tooltip';
  innateTipEl.hidden = true;
  document.body.appendChild(innateTipEl);
  var innateTipCurrent = null;

  function cleanDesc(html) {
    return html
      .replace(/\\n/g, '<br>')
      .replace(/\n/g, '<br>')
      .replace(/<br\s*\/?>\s*<br\s*\/?>/g, '<br>');
  }

  function buildTooltip(item, modeKey, showSeries, showEnchantSeries, baubleScale, heroCdr) {
    baubleScale = baubleScale || 1;
    heroCdr = heroCdr || 0;
    var tip = item.tip || {};
    var b = item.bonus || {};
    var visual = itemVisual(item, modeKey);
    var mode = visual.mode || null;
    var lines = [];
    // Header
    lines.push('<div class="hlt-head">');
    lines.push('<img class="hlt-icon" src="' + visual.icon + '" alt="">');
    lines.push('<div class="hlt-title">');
    lines.push('<span class="hlt-name">' + item.name + '</span>');
    if (visual.cost > 0) {
      var costText = item.id === 'item_dagon' && showSeries && tip.levels
        ? tip.levels.map(function(l) { return String(l.cost); }).join(' / ')
        : String(visual.cost);
      lines.push('<span class="hlt-cost"><img class="hlt-gold-icon" src="icons/misc/gold.png" alt=""> ' + costText + '</span>');
    }
    lines.push('</div></div>');
    // Ability info line
    var infoLine = [];
    if (tip.target) infoLine.push('ABILITY: ' + tip.target);
    if (tip.affects) infoLine.push('AFFECTS: ' + tip.affects);
    if (tip.disp) { const _d = tip.disp; infoLine.push('DISPELLABLE: ' + (/strong/i.test(_d) ? `<span style="color:#e05050">${_d}</span>` : _d)); }
    if (infoLine.length) lines.push('<div class="hlt-info">' + infoLine.join('<br>') + '</div>');
    var stats = [];
    // Neutral artifacts do not grant direct hero stats. Their AbilityValues
    // describe the item's active/passive mechanic and belong in its ability
    // description, not in the green attribute list. Enchantments still render
    // their actual stat rows below.
    if (item.id === 'item_dagon' && tip.levels && tip.levels.length) {
      if (showSeries) {
        stats.push('<span class="hlt-stat"><b>' + tip.levels.map(function(l){ return String(l.all).replace(/\.0$/, ''); }).join(' / ') + '</b> All Attributes</span>');
        stats.push('<span class="hlt-stat"><b>' + tip.levels.map(function(l){ return String(l.hp).replace(/\.0$/, ''); }).join(' / ') + '</b> Health</span>');
        stats.push('<span class="hlt-stat"><b>' + tip.levels.map(function(l){ return String(l.mp).replace(/\.0$/, ''); }).join(' / ') + '</b> Mana</span>');
        stats.push('<span class="hlt-stat"><b>' + tip.levels.map(function(l){ return String(l.cr).replace(/\.0$/, ''); }).join(' / ') + '</b> Cast Range</span>');
      } else if (mode) {
        stats.push('<span class="hlt-stat"><b>+' + String(mode.all).replace(/\.0$/, '') + '</b> All Attributes</span>');
        stats.push('<span class="hlt-stat"><b>+' + String(mode.hp).replace(/\.0$/, '') + '</b> Health</span>');
        stats.push('<span class="hlt-stat"><b>+' + String(mode.mp).replace(/\.0$/, '') + '</b> Mana</span>');
        stats.push('<span class="hlt-stat"><b>+' + String(mode.cr).replace(/\.0$/, '') + '</b> Cast Range</span>');
      }
    } else if (showEnchantSeries && item.modes && item.tiersAvailable) {
      var tierKeys = item.tiersAvailable.map(function(t) { return 't' + t; });
      var allKeys = {};
      tierKeys.forEach(function(tk) {
        var m = item.modes[tk];
        if (m) Object.keys(m).forEach(function(k) { if (k !== 'level' && Math.abs(m[k]) > 0.001) allKeys[k] = true; });
      });
      var bonusRows = [], penaltyRows = [];
      Object.keys(allKeys).forEach(function(k) {
        var label = BONUS_LABELS[k] || k;
        var flip = BONUS_FLIP_NEG.has(k);
        var vals = tierKeys.map(function(tk) {
          var m = item.modes[tk];
          var v = m ? (m[k] || 0) : 0;
          return fmtBonusVal(k, v, flip);
        });
        var isPenalty = flip
          ? tierKeys.some(function(tk) { var m = item.modes[tk]; return m && (m[k] || 0) > 0; })
          : BONUS_RED_POS.has(k)
            ? tierKeys.some(function(tk) { var m = item.modes[tk]; return m && (m[k] || 0) > 0; })
            : tierKeys.some(function(tk) { var m = item.modes[tk]; return m && (m[k] || 0) < 0; });
        var row = '<span class="hlt-stat' + (isPenalty ? ' hlt-penalty' : '') + '"><b>' + vals.join(' / ') + '</b> ' + label + '</span>';
        if (isPenalty) penaltyRows.push(row); else bonusRows.push(row);
      });
      stats.push.apply(stats, bonusRows.concat(penaltyRows));
    } else if (item.tiersAvailable && mode && !showEnchantSeries) {
      var bonusRows = [], penaltyRows = [];
      for (var k in BONUS_LABELS) {
        var v = mode[k];
        if (v && Math.abs(v) > 0.001) {
          var sv = (item['class'] === 'enchant' && baubleScale !== 1)
            ? ((k === 'cooldownReduction' || k === 'cdrUnique')
                ? 100 * (1 - (1 - v/100) * (1 - v*(baubleScale-1)/100))
                : v * baubleScale)
            : v;
          var flip = BONUS_FLIP_NEG.has(k);
          var formatted = fmtBonusVal(k, sv, flip);
          var pen = flip ? sv > 0 : (BONUS_RED_POS.has(k) ? sv > 0 : sv < 0);
          var row = '<span class="hlt-stat' + (pen ? ' hlt-penalty' : '') + '"><b>' + formatted + '</b> ' + BONUS_LABELS[k] + '</span>';
          if (pen) penaltyRows.push(row); else bonusRows.push(row);
        }
      }
      stats.push.apply(stats, bonusRows.concat(penaltyRows));
    } else if (item['class'] === 'enchant' && b) {
      var bonusRows = [], penaltyRows = [];
      for (var k in BONUS_LABELS) {
        var v = b[k];
        if (v && Math.abs(v) > 0.001) {
          var sv = baubleScale !== 1
            ? ((k === 'cooldownReduction' || k === 'cdrUnique')
                ? (function(){ var _s1 = Math.min(v, 99.9), _s2 = Math.min(v*(baubleScale-1), 99.9); return Math.min(Math.round((1-(1-_s1/100)*(1-_s2/100))*1000)/10, 99.9); })()
                : v * baubleScale)
            : v;
          var flip = BONUS_FLIP_NEG.has(k);
          var formatted = fmtBonusVal(k, sv, flip);
          var pen = flip ? sv > 0 : (BONUS_RED_POS.has(k) ? sv > 0 : sv < 0);
          var row = '<span class="hlt-stat' + (pen ? ' hlt-penalty' : '') + '"><b>' + formatted + '</b> ' + BONUS_LABELS[k] + '</span>';
          if (pen) penaltyRows.push(row); else bonusRows.push(row);
        }
      }
      stats.push.apply(stats, bonusRows.concat(penaltyRows));
    } else if (item['class'] !== 'neutral' && tip.attribs && tip.attribs.length) {
      tip.attribs.forEach(function(a) {
        var m = a.match(/^([+\-]?\s*[\d.]+%?)\s+(.*)/);
        if (m) stats.push('<span class="hlt-stat"><b>' + m[1] + '</b> ' + m[2] + '</span>');
        else stats.push('<span class="hlt-stat">' + a + '</span>');
      });
    } else if (item['class'] !== 'neutral') {
      for (var k in BONUS_LABELS) {
        var v = b[k];
        if (v && Math.abs(v) > 0.001) {
          var formatted = BONUS_PCT.has(k) ? (v > 0 ? '+ ' : '') + v + '%' : (v > 0 ? '+ ' : '') + (v === Math.floor(v) ? v : v.toFixed(1));
          stats.push('<span class="hlt-stat"><b>' + formatted + '</b> ' + BONUS_LABELS[k] + '</span>');
        }
      }
    }
    if (stats.length) lines.push('<div class="hlt-stats">' + stats.join('') + '</div>');
    // Active/Passive bar + cost icons
    var costBar = [];
    var castRangeVal = mode && mode.cr != null ? mode.cr : tip.cr;
    var manaCostVal = mode && mode.mc != null ? mode.mc : tip.mc;
    var cooldownVal = mode && mode.cd != null ? mode.cd : tip.cd;
    if (castRangeVal) costBar.push('<span class="hlt-cost-icon hlt-cast-range" title="Cast Range">' + castRangeVal + '</span>');
    if (manaCostVal) costBar.push('<span class="hlt-cost-icon hlt-mana-cost" title="Mana Cost">' + manaCostVal + '</span>');
    if (cooldownVal) {
      var cdNum = parseFloat(cooldownVal);
      if (heroCdr > 0 && !isNaN(cdNum)) {
        var cdReduced = +(cdNum * (1 - heroCdr / 100)).toFixed(1);
        costBar.push('<span class="hlt-cost-icon hlt-cooldown" title="Cooldown (with ' + heroCdr + '% CDR)">' + cdReduced + ' <s style="opacity:.45;font-size:.85em">' + cooldownVal + '</s></span>');
      } else {
        costBar.push('<span class="hlt-cost-icon hlt-cooldown" title="Cooldown">' + cooldownVal + '</span>');
      }
    }
    // Description
    if (tip.desc) {
      var desc = cleanDesc(tip.desc);
      if (item.id === 'item_dagon' && mode) {
        var dmgVal = String(mode.dagonDamage != null ? mode.dagonDamage : 400).replace(/\.0$/, '');
        var manaVal = String(mode.mc != null ? mode.mc : (tip.mc || '')).replace(/\.0$/, '');
        desc = desc
          .replace(/(Damage:\s*<span class="GameplayVariable">)([^<]+)(<\/span>)/i, '$1' + dmgVal + '$3')
          .replace(/(Mana Cost:\s*<span class="GameplayVariable">)([^<]+)(<\/span>)/i, '$1' + manaVal + '$3');
      }
      // Extract <h1> headers — there can be multiple (Active + Passive sections)
      var sections = [];
      var remaining = desc;
      var hRe = /<h1>(.*?)<\/h1>/g;
      var lastIdx = 0;
      var match;
      while ((match = hRe.exec(desc)) !== null) {
        var before = desc.substring(lastIdx, match.index).trim();
        if (before && sections.length > 0) {
          sections[sections.length - 1].body = before;
        }
        sections.push({ header: match[1], body: '' });
        lastIdx = match.index + match[0].length;
      }
      var tail = desc.substring(lastIdx).trim();
      if (sections.length > 0) {
        sections[sections.length - 1].body = tail;
      }
      if (sections.length > 0) {
        var first = true;
        sections.forEach(function(sec) {
          var h = sec.header.toLowerCase();
          var isActive = h.startsWith('active') || h.startsWith('use');
          // Consumables (Tango/Salve) use the green "Use" header in-game.
          var barType = (item.consumable && isActive) ? 'is-use' : (isActive ? 'is-active' : 'is-passive');
          lines.push('<div class="hlt-ability-bar ' + barType + '">' +
            '<span class="hlt-ability-name">' + sec.header + '</span>' +
            (first && costBar.length ? '<span class="hlt-ability-costs">' + costBar.join('') + '</span>' : '') +
            '</div>');
          if (sec.body) lines.push('<div class="hlt-desc ' + barType + '">' + sec.body + '</div>');
          first = false;
        });
      } else {
        if (costBar.length) {
          lines.push('<div class="hlt-ability-bar is-passive"><span class="hlt-ability-costs">' + costBar.join('') + '</span></div>');
        }
        lines.push('<div class="hlt-desc">' + remaining + '</div>');
      }
    } else if (tip.short && !stats.length) {
      if (costBar.length) {
        lines.push('<div class="hlt-ability-bar is-passive"><span class="hlt-ability-costs">' + costBar.join('') + '</span></div>');
      }
      lines.push('<div class="hlt-desc">' + tip.short + '</div>');
    }
    if (tip.notes && tip.notes.length) {
      lines.push('<div class="hlt-notes">' + tip.notes.map(function(note) {
        return '<div class="hlt-note">' + cleanDesc(note) + '</div>';
      }).join('') + '</div>');
    }
    return lines.join('');
  }

  function showTooltip(tileEl) {
    var itemId = tileEl.dataset.itemId;
    var item = byItem.get(itemId);
    if (!item) return;
    var modeKey = tileEl.dataset.itemMode || '';
    var inPicker = !tileEl.closest('.hl-panel');
    var showSeries = item.id === 'item_dagon' && inPicker;
    var showEnchantSeries = item.tiersAvailable && item.tiersAvailable.length > 1 && inPicker;
    var baubleScale = 1;
    var heroCdr = 0;
    var _panel = tileEl.closest('.hl-panel');
    if (_panel) {
      if (item['class'] === 'enchant') {
        var _bl = parseInt((_panel.querySelector('[data-field="bauble-level"]') || {}).value || '0', 10) || 0;
        if (_bl > 0) {
          var _modes = {};
          try { _modes = JSON.parse(_panel.dataset.itemModes || '{}'); } catch(e) {}
          if ((_modes.enchant || null) === 't5') baubleScale = baubleScaleFor(_bl);
        }
      }
      heroCdr = parseFloat(_panel.dataset.cdr || '0') || 0;
    }
    var cls = 'hl-tooltip';
    if (item['class'] === 'neutral' && item.tier != null) {
      cls += ' neutral-tier-' + (item.tier + 1);
    }
    tipEl.className = cls;
    tipEl.innerHTML = buildTooltip(item, modeKey, showSeries, showEnchantSeries, baubleScale, heroCdr);
    tipEl.hidden = false;
    positionTooltip(tileEl);
  }

  function positionTooltip(anchor) {
    var r = anchor.getBoundingClientRect();
    var tw = tipEl.offsetWidth;
    var th = tipEl.offsetHeight;
    var left = r.right + 10;
    var top = r.top;
    if (left + tw > window.innerWidth - 8) left = r.left - tw - 10;
    if (top + th > window.innerHeight - 8) top = window.innerHeight - 8 - th;
    if (top < 8) top = 8;
    tipEl.style.left = left + 'px';
    tipEl.style.top = top + 'px';
  }

  function hideTooltip() { tipEl.hidden = true; tipCurrentTile = null; }
  function hideInnateTooltip() { innateTipEl.hidden = true; innateTipCurrent = null; }

  function buildInnateTooltip(hero) {
    var statInnate = hero && hero.statInnate ? hero.statInnate : null;
    if (!statInnate) return '';
    var lines = [];
    lines.push('<div class="hlt-head">');
    lines.push('<img class="hlt-icon" src="icons/misc/innate_icon.png" alt="">');
    lines.push('<div class="hlt-title">');
    lines.push('<span class="hlt-name">' + statInnate.name + '</span>');
    lines.push('</div></div>');
    if (statInnate.desc) {
      lines.push('<div class="hlt-desc">' + cleanDesc(statInnate.desc) + '</div>');
    }
    return lines.join('');
  }

  function showInnateTooltip(chipEl) {
    var panel = chipEl.closest('.hl-panel');
    if (!panel) return;
    var hero = byHero.get(panel.dataset.hero || heroes[0].id) || heroes[0];
    if (!hero.statInnate) return;
    innateTipEl.className = 'hl-tooltip hl-innate-tooltip';
    innateTipEl.innerHTML = buildInnateTooltip(hero);
    innateTipEl.hidden = false;
    var r = chipEl.getBoundingClientRect();
    var tw = innateTipEl.offsetWidth;
    var th = innateTipEl.offsetHeight;
    var left = r.right + 10;
    var top = r.top - 4;
    if (left + tw > window.innerWidth - 8) left = r.left - tw - 10;
    if (top + th > window.innerHeight - 8) top = window.innerHeight - 8 - th;
    if (top < 8) top = 8;
    innateTipEl.style.left = left + 'px';
    innateTipEl.style.top = top + 'px';
    innateTipCurrent = chipEl;
  }

  overlay.addEventListener('pointerover', function(e) {
    var tile = e.target.closest('.hl-item-tile');
    if (!tile) return;
    if (tile !== tipCurrentTile) {
      tipCurrentTile = tile;
      showTooltip(tile);
    }
  }, true);
  overlay.addEventListener('pointerout', function(e) {
    var tile = e.target.closest('.hl-item-tile');
    if (!tile) return;
    var related = e.relatedTarget;
    if (related && tile.contains(related)) return;
    hideTooltip();
  }, true);

  root.addEventListener('pointerover', function(e) {
    var slot = e.target.closest('.hl-inv-slot');
    if (!slot || slot.classList.contains('is-empty') || !slot.dataset.itemId) return;
    if (slot !== tipCurrentTile) {
      tipCurrentTile = slot;
      showTooltip(slot);
    }
  }, true);
  root.addEventListener('pointerout', function(e) {
    var slot = e.target.closest('.hl-inv-slot');
    if (!slot) return;
    var related = e.relatedTarget;
    if (related && (slot.contains(related) || tipEl.contains(related))) return;
    hideTooltip();
  }, true);

  root.addEventListener('pointerover', function(e) {
    var bslot = e.target.closest('.hl-bauble-slot');
    if (bslot && bslot !== tipCurrentTile) {
      tipCurrentTile = bslot;
      var panel = bslot.closest('.hl-panel');
      var bl = panel ? (parseInt((panel.querySelector('[data-field="bauble-level"]') || {}).value || '0', 10) || 0) : 0;
      // Base/growth come from the item's KV (enchantScale), never hardcoded —
      // 7.41e moved the recraft bonus from 40% to 35%.
      var _bsc = (byItem.get('item_enchanters_bauble') || {}).enchantScale || { base: 0.10, growth: 0.35 };
      var basePct = Math.round(_bsc.base * 100);
      var growthPct = Math.round(_bsc.growth * 100);
      var bonusPct = bl > 0 ? '+' + (basePct + (bl - 1) * growthPct) + '%' : '—';
      tipEl.className = 'hl-tooltip';
      tipEl.innerHTML = '<div class="hlt-head"><img class="hlt-icon" src="icons/items/enchanters_bauble.png" alt=""><div class="hlt-title"><span class="hlt-name">Enchanter\'s Bauble</span></div></div>'
        + (bl > 0 ? '<div class="hlt-stats"><span class="hlt-stat"><b>' + bonusPct + '</b> Enchantment Bonus</span></div>' : '')
        + '<div class="hlt-info">ABILITY: Passive</div>'
        + '<div class="hlt-desc">Increases the bonuses of the item\'s Neutral Enchantment by <span style="color:#9cf">' + basePct + '%</span>. Every time this item is crafted again the bonus is increased by <span style="color:#9cf">' + growthPct + '%</span>.</div>';
      tipEl.hidden = false;
      positionTooltip(bslot);
    }
  }, true);
  root.addEventListener('pointerout', function(e) {
    var bslot = e.target.closest('.hl-bauble-slot');
    if (!bslot) return;
    var related = e.relatedTarget;
    if (related && bslot.contains(related)) return;
    hideTooltip();
  }, true);
  root.addEventListener('pointerover', function(e) {
    var chip = e.target.closest('[data-innate-chip]');
    if (!chip || chip.classList.contains('is-hidden')) return;
    if (chip !== innateTipCurrent) showInnateTooltip(chip);
  }, true);
  root.addEventListener('pointerout', function(e) {
    var chip = e.target.closest('[data-innate-chip]');
    if (!chip) return;
    var related = e.relatedTarget;
    if (related && (chip.contains(related) || innateTipEl.contains(related))) return;
    hideInnateTooltip();
  }, true);
  innateTipEl.addEventListener('pointerleave', function() {
    hideInnateTooltip();
  });

  update();
})();
