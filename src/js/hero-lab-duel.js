// ---- HERO LAB DUEL: two heroes trade right-clicks until one dies (no DOM; hero-lab.js draws it) ----
// The rules are docs/tables.md "Hero Lab battle rules": both heroes start their first attack at 0.00s, the attack
// interval between the next ones; a melee hero's hidden block is 16 damage at a 50% long-run chance, as PRD with a
// 30.21% step, its counter reset by a proc; block before armor, only the largest block that procs; ranged heroes and
// Vengeful Spirit get no hidden block. On top of them:
// - the attack point shrinks with attack speed like the attack interval; a ranged hit lands after its projectile
//   flies the attacker's range; killed or stunned before the attack point = no attack, a projectile in the air lands
// - the passives of the items (`onHit`, read from items.txt by builders/hero_lab.py `_item_on_hit`): crit, bash (a
//   stun cancels the swing it catches), pierce procs, chain lightning, armor corruption, attack poisons, mana break,
//   attack slow, health restoration cut, item damage block, Echo Strike. Every chance is PRD (its C from the
//   chance), each source with its own counter; passive cooldowns count
// - evasion is a plain roll; regen, mana regen and poisons run between hits; lifesteal heals by the physical damage
// No abilities, no cleave, no actives. A seeded random: the same builds give the same answer on every redraw.
var heroLabPrdC = (function () {
  var cache = {};
  // the C whose PRD gives the long-run chance p: 1 / (expected attacks to a proc) = p
  var rate = function (c) {
    var expected = 0, notYet = 1;
    for (var n = 1; notYet > 0; n++) {
      var p = Math.min(1, c * n);
      expected += n * notYet * p;
      notYet *= 1 - p;
    }
    return 1 / expected;
  };
  return function (p) {
    if (p <= 0) return 0;
    if (p >= 1) return 1;
    var key = p.toFixed(4);
    if (cache[key] != null) return cache[key];
    var lo = 0, hi = p;
    for (var i = 0; i < 40; i++) { var mid = (lo + hi) / 2; if (rate(mid) < p) lo = mid; else hi = mid; }
    return (cache[key] = (lo + hi) / 2);
  };
})();

function heroLabDuel(a, b, opts) {
  opts = opts || {};
  var RUNS = opts.runs || 1000;
  var MAX_T = opts.maxTime || 60;
  var armorMult = function (armor) { return 1 - (0.06 * armor) / (1 + 0.06 * Math.abs(armor)); };

  var seed = opts.seed == null ? 0x5107 : opts.seed;
  var rnd = function () {                       // mulberry32
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  var proc = function (src, counters, key) {   // PRD: the chance grows by C per attack without a proc
    if (!src || src.p <= 0) return false;
    var n = (counters[key] || 0) + 1;
    if (rnd() < Math.min(1, src.c * n)) { counters[key] = 0; return true; }
    counters[key] = n;
    return false;
  };
  var withC = function (p) { return { p: p, c: heroLabPrdC(p) }; };
  var best = function (list, by) { return list.reduce(function (x, y) { return !x || by(y) > by(x) ? y : x; }, null); };

  var side = function (s) {
    var ranged = !!s.ranged;
    var aspd = Math.max(1, Number(s.aspd) || 100);
    var hits = (s.onHit || []).filter(Boolean);
    var all = function (k) { return hits.map(function (h) { return h[k]; }).filter(Boolean); };
    var x = {
      hpMax: Math.max(1, Number(s.hp) || 1), hpr: Number(s.hpr) || 0,
      mpMax: Math.max(0, Number(s.mp) || 0), mpr: Number(s.mpr) || 0,
      aspd: aspd, bat: (Number(s.tHit) || ((Number(s.bat) || 1.7) * 100 / aspd)) * aspd / 100,
      point: Number(s.attackPoint) || 0,
      travel: ranged && Number(s.proj) > 0 ? (Number(s.range) || 0) / Number(s.proj) : 0,
      dmin: Math.max(0, Math.round(Number(s.dmin) || 0)), armor: Number(s.armor) || 0,
      mr: Math.min(Math.max(Number(s.mr) || 0, 0), 100) / 100,
      evasion: Math.min(Math.max(Number(s.evasion) || 0, 0), 100) / 100, lifesteal: (Number(s.lifesteal) || 0) / 100,
      ranged: ranged, int: Number(s.int) || 0,
    };
    x.dmax = Math.max(x.dmin, Math.round(Number(s.dmax) || 0));
    x.crits = all('crit').map(function (c) { var o = withC(c.chance / 100); o.mult = c.mult / 100; return o; });
    var bash = best(all('bash'), function (k) { return ranged ? k.ranged : k.melee; });
    if (bash) { x.bash = withC((ranged ? bash.ranged : bash.melee) / 100); x.bash.dmg = bash.dmg; x.bash.stun = bash.stun; x.bash.cd = bash.cd || 0; }
    var pierce = best(all('pierce'), function (k) { return k.chance; });
    if (pierce) { x.pierce = withC(pierce.chance / 100); x.pierce.dmg = pierce.dmg; }
    var chain = best(all('chain'), function (k) { return k.dmg; });
    if (chain) { x.chain = withC(chain.chance / 100); x.chain.dmg = chain.dmg; x.chain.cd = chain.cd || 0; }
    x.corrupt = best(all('corrupt'), function (k) { return k.armor; });
    x.dots = all('dot').map(function (d) {
      return { dps: d.intMult ? d.intMult * x.int : d.dps, dur: d.dur, magic: !!d.magic, cd: d.cd || 0, trueStrike: !!d.trueStrike };
    });
    x.manaBreak = best(all('manaBreak'), function (k) { return k.mana; });
    x.attackSlow = best(all('attackSlow'), function (k) { return Math.max(k.melee, k.ranged); });
    x.healCut = best(all('healCut'), function (k) { return k.pct; });
    var echo = !ranged && best(all('echo'), function (k) { return -k.cd; });
    x.echo = echo || null;
    // block taken: the hidden melee block and the items'; a ranged holder gets the items' ranged value
    x.blocks = [];
    if (!ranged && !s.noBlock) { var hidden = withC(0.5); hidden.amount = 16; x.blocks.push(hidden); }
    all('block').forEach(function (k) {
      var o = withC((k.chanceHero || k.chance) / 100);
      o.amount = ranged ? k.ranged : k.melee;
      x.blocks.push(o);
    });
    return x;
  };
  var S = [side(a), side(b)];

  var fight = function (trace) {
    var u = [0, 1].map(function (i) {
      return { s: S[i], hp: S[i].hpMax, mp: S[i].mpMax, next: 0, hits: 0, dealt: 0, dead: Infinity, prd: {},
               ready: {}, stun: 0, corrupt: null, slow: null, healCut: null, dots: [] };
    });
    var flying = [];                            // projectiles in the air: { t, from }
    var now = 0;
    var log = trace ? [[0, u[0].hp, u[1].hp]] : null;
    var alive = function (x) { return x.dead === Infinity; };
    var active = function (d, t) { return d && d.until > t; };
    var aspdNow = function (x, t) { return x.s.aspd * (active(x.slow, t) ? 1 - x.slow.pct / 100 : 1); };
    var armorNow = function (x, t) { return x.s.armor - (active(x.corrupt, t) ? x.corrupt.armor : 0); };
    // HP change per second of x between events: regen (cut while the debuff lasts) minus the poisons on it
    var poisonRate = function (x, t) {
      var r = 0;
      x.dots.forEach(function (d) {
        if (d.until > t) r += d.dps * (d.magic ? 1 - x.s.mr : armorMult(armorNow(x, t)));
      });
      return r;
    };
    var rate = function (x, t) {
      return x.s.hpr * (active(x.healCut, t) ? 1 - x.healCut.pct / 100 : 1) - poisonRate(x, t);
    };
    var advance = function (t) {                // to time t, which no debuff edge lies inside
      var dt = t - now;
      if (dt <= 0) return;
      for (var i = 0; i < 2; i++) {
        var x = u[i];
        if (!alive(x)) continue;
        var r = rate(x, now);
        var poison = poisonRate(x, now);           // credited to the other side's damage dealt
        if (r < 0 && x.hp + r * dt <= 0) {        // a poison finishes it between hits
          var left = x.hp / -r;
          u[1 - i].dealt += poison * left;
          x.dead = now + left;
          x.hp = 0;
          continue;
        }
        u[1 - i].dealt += poison * dt;
        x.hp = Math.min(x.s.hpMax, x.hp + r * dt);
        x.mp = Math.min(x.s.mpMax, x.mp + x.s.mpr * dt);
      }
      now = t;
    };
    var edges = function () {                   // the next time a debuff starts or stops changing HP
      var t = Infinity;
      u.forEach(function (x) {
        [x.corrupt, x.healCut, x.slow].concat(x.dots).forEach(function (d) { if (d && d.until > now && d.until < t) t = d.until; });
      });
      return t;
    };

    var hit = function (i, t) {
      var me = u[i], foe = u[1 - i], s = me.s, f = foe.s;
      if (!alive(foe)) return;
      var pierce = proc(s.pierce, me.prd, 'pierce');
      var dotsReady = s.dots.map(function (d, k) { return !d.cd || !(me.ready['dot' + k] > t); });
      var trueStrike = pierce || s.dots.some(function (d, k) { return d.trueStrike && dotsReady[k]; });
      if (!trueStrike && rnd() < f.evasion) return;
      // corruption lands with the attack: this hit already meets the lower armor
      if (s.corrupt) foe.corrupt = { armor: s.corrupt.armor, until: t + s.corrupt.dur };
      var phys = s.dmin + Math.floor(rnd() * (s.dmax - s.dmin + 1));
      var mult = 1;
      s.crits.forEach(function (c, k) { if (proc(c, me.prd, 'crit' + k)) mult = Math.max(mult, c.mult); });
      phys *= mult;
      var magic = 0;
      if (s.bash && !(me.ready.bash > t) && proc(s.bash, me.prd, 'bash')) {
        phys += s.bash.dmg;
        me.ready.bash = t + s.bash.cd;
        foe.stun = Math.max(foe.stun, t + s.bash.stun);
      }
      if (s.manaBreak && foe.mp > 0) {
        var burned = Math.min(s.manaBreak.mana, foe.mp);
        foe.mp -= burned;
        phys += burned * s.manaBreak.dmgPer;
      }
      var blocked = 0;
      f.blocks.forEach(function (bl, k) { if (proc(bl, foe.prd, 'block' + k)) blocked = Math.max(blocked, bl.amount); });
      phys = Math.max(0, phys - blocked) * armorMult(armorNow(foe, t));
      if (pierce) magic += s.pierce.dmg;
      if (s.chain && !(me.ready.chain > t) && proc(s.chain, me.prd, 'chain')) { magic += s.chain.dmg; me.ready.chain = t + s.chain.cd; }
      magic *= 1 - f.mr;
      if (log) log.push([t, u[0].hp, u[1].hp]);
      me.dealt += Math.min(phys + magic, Math.max(0, foe.hp));     // no overkill
      foe.hp -= phys + magic;
      me.hits += 1;
      if (alive(me)) me.hp = Math.min(s.hpMax, me.hp + phys * s.lifesteal * (active(me.healCut, t) ? 1 - me.healCut.pct / 100 : 1));
      if (s.attackSlow) foe.slow = { pct: f.ranged ? s.attackSlow.ranged : s.attackSlow.melee, until: t + s.attackSlow.dur };
      if (s.healCut) foe.healCut = { pct: s.healCut.pct, until: t + s.healCut.dur };
      s.dots.forEach(function (d, k) {
        if (!dotsReady[k]) return;
        foe.dots = foe.dots.filter(function (o) { return o.src !== i + ':' + k; });
        foe.dots.push({ src: i + ':' + k, dps: d.dps, magic: d.magic, until: t + d.dur });
        if (d.cd) me.ready['dot' + k] = t + d.cd;
      });
      if (log) log.push([t, Math.max(0, u[0].hp), Math.max(0, u[1].hp)]);
      if (foe.hp <= 0) { foe.hp = 0; foe.dead = t; }
    };

    for (var guard = 0; guard < 100000; guard++) {
      var ev = null;
      flying.forEach(function (fl, k) { if (!ev || fl.t < ev.t) ev = { t: fl.t, from: fl.from, fly: k }; });
      [0, 1].forEach(function (i) {
        var x = u[i];
        if (!alive(x)) return;
        var start = Math.max(x.next, x.stun);
        var t = start + x.s.point * 100 / aspdNow(x, start);
        if (!ev || t < ev.t || (t === ev.t && rnd() < 0.5)) ev = { t: t, from: i, fly: -1 };
      });
      var edge = edges();
      if (!ev || Math.min(ev.t, edge) > MAX_T) { advance(MAX_T); break; }
      if (edge < ev.t) { advance(edge); if (!alive(u[0]) || !alive(u[1])) break; continue; }
      advance(ev.t);
      if (!alive(u[0]) || !alive(u[1])) break;
      var me = u[ev.from];
      // a swing a bash caught never reaches this point: its time is counted from the end of the stun above
      if (ev.fly >= 0) { flying.splice(ev.fly, 1); hit(ev.from, ev.t); }
      else {
        me.next = Math.max(me.next, me.stun) + me.s.bat * 100 / aspdNow(me, ev.t);
        if (me.s.echo && !(me.ready.echo > ev.t)) { me.next = ev.t; me.ready.echo = ev.t + me.s.echo.cd; }
        if (me.s.travel > 0) flying.push({ t: ev.t + me.s.travel, from: ev.from });
        else hit(ev.from, ev.t);
      }
      if (!alive(u[0]) || !alive(u[1])) break;
    }
    var winner = !alive(u[1]) && alive(u[0]) ? 0 : !alive(u[0]) && alive(u[1]) ? 1 : -1;
    var end = winner < 0 ? now : u[1 - winner].dead;
    if (log && log[log.length - 1][0] < end) log.push([end, Math.max(0, u[0].hp), Math.max(0, u[1].hp)]);
    return { winner: winner, t: end, hits: [u[0].hits, u[1].hits], dealt: [u[0].dealt, u[1].dealt],
             hpLeft: [Math.max(0, u[0].hp), Math.max(0, u[1].hp)], log: log };
  };

  var median = function (xs) {
    if (!xs.length) return null;
    var s = xs.slice().sort(function (x, y) { return x - y; });
    return s[Math.floor((s.length - 1) / 2)];
  };
  var wins = [0, 0], draws = 0, times = [[], []], hits = [[], []], left = [[], []], dealt = [0, 0], spent = 0;
  for (var r = 0; r < RUNS; r++) {
    var f = fight(false);
    dealt[0] += f.dealt[0]; dealt[1] += f.dealt[1]; spent += f.t;
    if (f.winner < 0) { draws++; continue; }
    wins[f.winner]++;
    times[f.winner].push(f.t);
    hits[f.winner].push(f.hits[f.winner]);
    left[f.winner].push(f.hpLeft[f.winner]);
  }
  // a typical fight for the chart: the likelier winner, as close to its median time as the seed gives
  var fav = !wins[0] && !wins[1] ? -1 : wins[0] >= wins[1] ? 0 : 1;
  var sample = null;
  if (fav >= 0) {
    var want = median(times[fav]), gapBest = Infinity;
    for (var k = 0; k < 60; k++) {
      var g = fight(true);
      if (g.winner !== fav) continue;
      var gap = Math.abs(g.t - want);
      if (gap < gapBest) { gapBest = gap; sample = g; }
      if (gap < 0.01) break;
    }
  }
  var per = function (i) {
    return { win: wins[i] / RUNS, time: median(times[i]), hits: median(hits[i]), hpLeft: median(left[i]),
             dps: spent > 0 ? dealt[i] / spent : 0 };
  };
  return { runs: RUNS, maxTime: MAX_T, draw: draws / RUNS, sides: [per(0), per(1)], hpMax: [S[0].hpMax, S[1].hpMax],
           sample: sample ? { winner: sample.winner, t: sample.t, log: sample.log } : null };
}
if (typeof module !== 'undefined' && module.exports) module.exports = { heroLabDuel: heroLabDuel, heroLabPrdC: heroLabPrdC };
