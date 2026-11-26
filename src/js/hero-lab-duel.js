// ---- HERO LAB DUEL: two heroes trade right-clicks until one dies (no DOM; hero-lab.js draws it) ----
// The rules are docs/tables.md "Hero Lab battle rules": both heroes start their first attack at 0.00s, the attack
// interval between the next ones; a melee hero's hidden block is 16 damage at a 50% long-run chance, as PRD with a
// 30.21% step, its counter reset by a proc; block before armor; ranged heroes and Vengeful Spirit get no block.
// On top of them: the attack point shrinks with attack speed like the attack interval, a ranged attack lands after
// its projectile flies the attacker's range, an attack cancelled by death before its attack point does no damage but a
// projectile already in the air still lands, evasion is a plain roll, regen ticks between hits, lifesteal heals the
// attacker by the damage dealt. No abilities, no crit / bash / cleave procs. A seeded random: the same builds give the
// same answer on every redraw.
function heroLabDuel(a, b, opts) {
  opts = opts || {};
  var RUNS = opts.runs || 1000;
  var MAX_T = opts.maxTime || 60;
  var BLOCK = 16, BLOCK_C = 0.3021;
  var armorMult = function (armor) { return 1 - (0.06 * armor) / (1 + 0.06 * Math.abs(armor)); };

  var seed = opts.seed == null ? 0x5107 : opts.seed;
  var rnd = function () {                       // mulberry32
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };

  var side = function (s) {
    var aspd = Math.max(1, Number(s.aspd) || 100);
    var tHit = Number(s.tHit) || ((Number(s.bat) || 1.7) * 100 / aspd);
    var point = (Number(s.attackPoint) || 0) * 100 / aspd;
    var travel = s.ranged && Number(s.proj) > 0 ? (Number(s.range) || 0) / Number(s.proj) : 0;
    var dmin = Math.max(0, Math.round(Number(s.dmin) || 0));
    var dmax = Math.max(dmin, Math.round(Number(s.dmax) || 0));
    return {
      hpMax: Math.max(1, Number(s.hp) || 1), hpr: Number(s.hpr) || 0, tHit: Math.max(0.01, tHit), point: point,
      travel: travel, dmin: dmin, dmax: dmax, armor: Number(s.armor) || 0,
      evasion: Math.min(Math.max(Number(s.evasion) || 0, 0), 100) / 100, lifesteal: (Number(s.lifesteal) || 0) / 100,
      block: !!s.melee && !s.noBlock,
    };
  };
  var A = side(a), B = side(b);

  // the damage one attack of `from` does to `to` on average: for the deterministic "effective DPS" line
  var expectedHit = function (from, to) {
    var avg = (from.dmin + from.dmax) / 2;
    if (to.block) avg -= 0.5 * Math.min(BLOCK, avg);
    return avg * armorMult(to.armor) * (1 - to.evasion);
  };

  var fight = function (trace) {
    var u = [
      { s: A, hp: A.hpMax, prd: 0, next: 0, hits: 0, dead: Infinity },
      { s: B, hp: B.hpMax, prd: 0, next: 0, hits: 0, dead: Infinity },
    ];
    var flying = [];                            // landed later: { t, from }
    var now = 0;
    var log = trace ? [[0, u[0].hp, u[1].hp]] : null;
    var regen = function (t) {
      var dt = t - now;
      if (dt > 0) u.forEach(function (x) { if (x.dead === Infinity) x.hp = Math.min(x.s.hpMax, x.hp + x.s.hpr * dt); });
      now = Math.max(now, t);
    };
    for (var guard = 0; guard < 100000; guard++) {
      // the next thing to happen: a projectile landing or an attack reaching its point
      var best = null;
      flying.forEach(function (f, i) { if (!best || f.t < best.t) best = { t: f.t, from: f.from, fly: i }; });
      [0, 1].forEach(function (i) {
        if (u[i].dead !== Infinity) return;
        var t = u[i].next + u[i].s.point;
        if (!best || t < best.t || (t === best.t && rnd() < 0.5)) best = { t: t, from: i, fly: -1 };
      });
      if (!best || best.t > MAX_T) { regen(MAX_T); break; }
      regen(best.t);
      var me = u[best.from], foe = u[1 - best.from];
      if (best.fly >= 0) flying.splice(best.fly, 1);
      else {
        me.next += me.s.tHit;
        if (me.s.travel > 0) { flying.push({ t: best.t + me.s.travel, from: best.from }); continue; }
      }
      if (foe.dead !== Infinity) continue;
      if (rnd() < foe.s.evasion) continue;
      var dmg = me.s.dmin + Math.floor(rnd() * (me.s.dmax - me.s.dmin + 1));
      if (foe.s.block) {
        foe.prd += 1;
        if (rnd() < Math.min(1, BLOCK_C * foe.prd)) { dmg = Math.max(0, dmg - BLOCK); foe.prd = 0; }
      }
      dmg *= armorMult(foe.s.armor);
      if (log) log.push([best.t, Math.max(0, u[0].hp), Math.max(0, u[1].hp)]);   // the regen up to the hit
      foe.hp -= dmg;
      me.hits += 1;
      if (me.dead === Infinity) me.hp = Math.min(me.s.hpMax, me.hp + dmg * me.s.lifesteal);
      if (log) log.push([best.t, Math.max(0, u[0].hp), Math.max(0, u[1].hp)]);
      if (foe.hp <= 0) { foe.dead = best.t; break; }
    }
    var winner = u[0].dead < Infinity ? 1 : u[1].dead < Infinity ? 0 : -1;
    if (log && log[log.length - 1][0] < now) log.push([now, Math.max(0, u[0].hp), Math.max(0, u[1].hp)]);
    return { winner: winner, t: winner < 0 ? MAX_T : u[1 - winner].dead, hits: [u[0].hits, u[1].hits],
             hpLeft: [Math.max(0, u[0].hp), Math.max(0, u[1].hp)], log: log };
  };

  var median = function (xs) {
    if (!xs.length) return null;
    var s = xs.slice().sort(function (x, y) { return x - y; });
    return s[Math.floor((s.length - 1) / 2)];
  };
  var wins = [0, 0], draws = 0, times = [[], []], hits = [[], []], left = [[], []];
  for (var r = 0; r < RUNS; r++) {
    var f = fight(false);
    if (f.winner < 0) { draws++; continue; }
    wins[f.winner]++;
    times[f.winner].push(f.t);
    hits[f.winner].push(f.hits[f.winner]);
    left[f.winner].push(f.hpLeft[f.winner]);
  }
  // a typical fight for the chart: the likelier winner, as close to its median time as the seed gives
  var fav = wins[0] === wins[1] && !wins[0] ? -1 : wins[0] >= wins[1] ? 0 : 1;
  var sample = null;
  if (fav >= 0) {
    var want = median(times[fav]), bestGap = Infinity;
    for (var k = 0; k < 60; k++) {
      var g = fight(true);
      if (g.winner !== fav) continue;
      var gap = Math.abs(g.t - want);
      if (gap < bestGap) { bestGap = gap; sample = g; }
      if (gap < 0.01) break;
    }
  }
  var per = function (i) {
    var me = i ? B : A, foe = i ? A : B;
    return {
      win: wins[i] / RUNS, time: median(times[i]), hits: median(hits[i]), hpLeft: median(left[i]),
      dps: expectedHit(me, foe) / me.tHit, hitsToKill: Math.ceil(foe.hpMax / Math.max(0.01, expectedHit(me, foe))),
    };
  };
  return { runs: RUNS, maxTime: MAX_T, draw: draws / RUNS, sides: [per(0), per(1)], hpMax: [A.hpMax, B.hpMax],
           sample: sample ? { winner: sample.winner, t: sample.t, log: sample.log } : null };
}
if (typeof module !== 'undefined' && module.exports) module.exports = { heroLabDuel: heroLabDuel };
