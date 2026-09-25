"""Row scoring for the dynamics widget "Weights" mode — two scales per (entity, patch).

  w  (net balance)  = Σ weight(type) × direction × magnitude     signed
  v  (volume)       = Σ weight(type) × magnitude                 unsigned, reworks included

  type       — characteristic class of the row (ordered regex table, first match wins).
               Matched against the PARAMETRIC part of the row (text before the first verb
               increased/decreased/rescaled/…), then against the whole row as a fallback —
               so "Cooldown decreased … dispels …" is cooldown, not bkb_pierce.
  J          — signal J (exchange rate from Valve's own buff<->nerf compensations, 3 865 pairs):
               value of +1% of a type. For rows with % badges the value is
               u[type] × mean|%| / 20 — this REPLACES weight × magnitude there (24 types).
  weight     — data/rules/valve_weights.json "final" (consensus shrunk towards `other`
               when fewer than 3 signals back the type: w = other + (raw − other) × n/3).
  direction  — +1 buff, −1 nerf, ±0.5 new/del (only when it is the row's sole tag),
               0 rework/misc/qol.
  magnitude  — HYBRID. Hero base-stat rows (GENERAL block): |delta| / typical Valve step
               for that stat (signal F: MS 5, base damage 3, stats 2, armor 1, …), so
               "Base Armor -1" is 1.0 for every hero. Other rows: mean |%| over the row's
               badges (0% included; "Recipe … Total cost …" -> total only) divided by the
               type's typical |%| (signal C medians), so a typical change is 1.0. Cap 3.
               Rows without a % badge count as 1.0.
  items      — priced stat rows ("+0.8 -> +0.6 mana regen", "Total cost 4900g -> 5100g") are
               scored in GOLD: Δ × gold-per-unit (signal A, data/rules/item_stat_prices.json)
               / item cost; net = 0.6 × sign × min(5 × fraction, 3). Other item rows (actives,
               cooldowns) fall back to the hero formula.
  context    — multiplier by where the row lives (data/rules/valve_weights.json "context"):
               ultimate 1.3, basic ability/innate/scepter/base stat/item 1.0, shard 0.9,
               facet 0.8, talent 10/15/20/25 = 0.6/0.8/1.0/1.2.
  priority   — basic abilities are further scaled 0.7–1.3 by how pros skill them (share of the
               first 10 skill points, OpenDota pro matches; data/rules/ability_priority.json).
  talents    — "Level N Talent: A replaced with B" (REWORK) gets a DIRECTION from signal K when
               known (data/rules/talent_tiers.json): measured shift of the pro pick share of the
               slot against the unchanged sibling (20 points = 1.0), else LEVEL MOVES — the new
               talent came from another level: earlier = buff, later = nerf (0.5 x weight per
               step); the tier total is split between its rows. Unknown -> net 0.
  volume     — buff/nerf/new/del rows: weight × magnitude; rework rows: weight × 1.0
               (a rework is a big, sign-less decision); misc/qol: 0.

Decisions 2026-09-16 (Денис): two scales (net + volume), hybrid magnitude.
"""
import json as _json
import os as _os
import re as _re

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_WJ = _json.load(open(_os.path.join(_HERE, "data", "rules", "valve_weights.json"), encoding="utf-8"))
_W = _WJ["final"]

# Parametric categories — first match wins. Ordered: specific before generic.
CAT = [
    ("cooldown", r"cooldown|\bcd\b|charge restore|recharge|restore time"),
    ("mana_cost", r"mana cost|manacost|costs? \d+ mana|mana per"),
    ("cast_range", r"cast range"),
    ("cast_point", r"cast point|cast time|cast speed|backswing|attack point|animation|\bdelay\b"),
    ("stun", r"stun|bash|knockback|taunt"),
    ("silence", r"silence|\bhex\b|\broot|disarm|mute|leash"),
    ("slow_res", r"slow resist"), ("slow", r"slow"), ("status_res", r"status resist"),
    ("spell_amp", r"spell amp|spell damage amp"),
    ("attack_speed", r"attack speed|base attack time|\bbat\b|attack rate|attack interval"),
    ("turn_rate", r"\bturn rate|\bturn speed"),   # before move_speed: "Turn Speed" ties with "speed"
    ("projectile", r"\b(projectile|missile|bolt|arrow|orb|spear|shard|dagger|blade|glaive|axe|hook|ball|wave|dart|rocket|shot|throw|toss|flight|travel) speed|projectile|missile"),
    ("move_speed", r"movement speed|move speed|movespeed|movement|\bms\b|\bspeed\b"),
    ("evasion", r"evasion|dodge|backtrack|miss chance"),
    ("magic_res", r"magic resist|magical resist|spell block"),
    ("armor", r"armor|corruption|damage block|\bblock\b"), ("crit", r"crit"),
    ("lifesteal", r"lifesteal|life steal"),
    ("health", r"health|\bhp\b|regen|\bheal|healing"), ("mana", r"\bmana\b|\bmp\b"),
    ("stats", r"strength|agility|intelligence|all stats|attribute"),
    ("base_damage", r"base damage|attack damage|damage at level"),
    ("charges", r"charge|stack|max attacks|attacks to"),
    ("gold_xp", r"gold|bounty|experience|\bxp\b"), ("respawn", r"respawn|reincarnat"),
    ("vision", r"vision|sight|reveal"),
    ("cost", r"recipe cost|total cost|(?<!health )\bcost\b|price"),   # a spell's health cost = health
    ("damage", r"damage|dmg|dps|burn|cleave"),
    ("duration", r"duration|\btime\b|lasts|linger|channel"),
    ("range", r"radius|range|distance|\baoe\b|\barea\b|width|length"),
    ("bkb_pierce", r"pierce|debuff immun|spell immun|magic immun|dispel"),
    ("chance", r"chance|probability"),
]
_CAT = [(c, _re.compile(p, _re.I)) for c, p in CAT]
_TAGS_RE = _re.compile(r"<[^>]+>")
_QUAL_RE = _re.compile(r"\s+(?:on|when|while|against|per|for|to|in|with|during|after|vs\.?)\s+", _re.I)
_VERB_RE = _re.compile(r"\b(increased|decreased|reduced|improved|rescaled|changed|lowered|raised|"
                       r"replaced|now|no longer|removed|added)\b", _re.I)
_PCT_CLS_RE = _re.compile(r'class="badge (buff|nerf|neutral)\d*">([+\-−]?\d+(?:\.\d+)?)%<')
_OVERALL_RE = _re.compile(r'data-overall="(buff|nerf)"')


def _row_pcts(text, badge_html):
    """|%| values that define the row's size (review F.6): for per-level rows take the badge
    at the level b() used for the DIRECTION — the last non-zero level (max rank) when its
    direction agrees with the row's overall tag; when b() flipped the tag by the average
    (front-/back-loaded, early-game cut, flatten) use all levels. Recipe+total -> total."""
    found = [(c, abs(float(v.replace("−", "-")))) for c, v in _PCT_CLS_RE.findall(badge_html or "")]
    if not found:
        return []
    if len(found) >= 2 and _re.search(r"total cost", _plain(text), _re.I):
        return [found[-1][1]]
    if len(found) >= 2:
        overall = _OVERALL_RE.search(badge_html or "")
        last = next(((c, v) for c, v in reversed(found) if c != "neutral"), None)
        if last and overall and last[0] == overall.group(1):
            return [last[1]]
    return [v for _, v in found]
_DIR = {"buff": 1.0, "nerf": -1.0}


def _plain(text):
    return _TAGS_RE.sub(" ", text or "")


def classify(text):
    t = _plain(text)
    m = _re.search(r"replaced with (.*)$", t, _re.I)
    if m:                                    # talent/ability swap: the NEW effect is what exists now
        t = m.group(1)
    head = t
    m = _VERB_RE.search(t)
    if m and m.start() > 0:
        head = t[:m.start()]
    # The parameter name is "<qualifiers> <measured thing>": drop trailing "on/when/against/
    # per/for …" clauses and take the LAST matching category in what is left, so
    # "Movement speed bonus duration" is duration and "Keen Eye disable duration on taking
    # damage" is duration, not damage.
    head = _QUAL_RE.split(head, 1)[0]
    best = None                                  # (category, match end); ties -> earlier in CAT
    for c, rx in _CAT:
        mm = None
        for mm in rx.finditer(head):
            pass
        if mm and (best is None or mm.end() > best[1]):
            best = (c, mm.end())
    if best:
        return best[0]
    return next((c for c, rx in _CAT if rx.search(t)), "other")


def weight_of(kind):
    return _W.get(kind, _W["other"])


_STEP = _WJ.get("typical_step", {})
_TPCT = _WJ.get("typical_pct", {})
_CTX = _WJ.get("context", {})
MAG_CAP_NORM = float(_WJ.get("magnitude_cap", 3.0))
# hero GENERAL rows -> which typical step applies (order matters)
BASE_STAT_RE = [
    ("stats_gain", r"(strength|agility|intelligence)\s+gain"),
    ("stats", r"strength|agility|intelligence"),
    ("health_regen", r"health regen"), ("mana_regen", r"mana regen"),
    ("bat", r"base attack time|\bbat\b"), ("attack_speed", r"attack speed"),
    ("attack_range", r"attack range"), ("projectile", r"projectile"),
    ("magic_res", r"magic resist"), ("turn_rate", r"turn rate"), ("vision", r"vision"),
    ("move_speed", r"movement speed|move speed"), ("base_damage", r"damage"),
    ("armor", r"armor"), ("health", r"health"), ("mana", r"mana"),
]
_BASE_STAT = [(k, _re.compile(rx, _re.I)) for k, rx in BASE_STAT_RE]
_FROMTO_RE = _re.compile(r"from\s+(-?\d+(?:\.\d+)?)\S*\s+to\s+(-?\d+(?:\.\d+)?)", _re.I)
_BYN_RE = _re.compile(r"\bby\s+(-?\d+(?:\.\d+)?)", _re.I)
_ULT_CACHE = {}
try:
    _PRIO = _json.load(open(_os.path.join(_HERE, "data", "rules", "ability_priority.json"),
                            encoding="utf-8"))["abilities"]
except OSError:
    _PRIO = {}


def ultimates():
    """Engine slugs of every ultimate in the latest KV snapshot (data/stats/<latest>/heroes)."""
    if _ULT_CACHE:
        return _ULT_CACHE["set"]
    import glob as _glob
    from .meta import latest_stats_version
    out = set()
    for f in _glob.glob(_os.path.join(_HERE, "data", "stats", latest_stats_version(), "heroes", "*.txt")):
        t = open(f, encoding="utf-8", errors="replace").read()
        for m in _re.finditer(r'"([a-z_0-9]+)"\s*\{(?:[^{}]|\{[^{}]*\})*?"AbilityType"\s*"(?:DOTA_)?ABILITY_TYPE_ULTIMATE"', t):
            out.add(m.group(1))
    _ULT_CACHE["set"] = out
    return out


def context_multiplier(ctx):
    if not ctx:
        return 1.0
    if ctx.get("kind") == "item":
        return _CTX.get("item", 1.0)
    if ctx.get("talent"):
        return _CTX.get(f"talent{ctx['talent']}", 1.0)
    if ctx.get("base_stat"):
        return _CTX.get("base_stat", 1.0)
    if ctx.get("facet"):
        return _CTX.get("facet", 1.0)
    if ctx.get("shard"):
        return _CTX.get("shard", 1.0)
    if ctx.get("scepter"):
        return _CTX.get("scepter", 1.0)
    if ctx.get("innate"):
        return _CTX.get("innate", 1.0)
    if ctx.get("ability") and ctx["ability"] in ultimates():
        return _CTX.get("ultimate", 1.0)
    # basic ability: how central it is in the hero's kit, from how pros skill it
    # (data/rules/ability_priority.json, tools/fetch_skill_priority.py): maxed-first ~1.2,
    # value point ~0.7, unknown 1.0.
    prio = _PRIO.get(ctx.get("ability") or "", {}).get("mult", 1.0)
    return _CTX.get("ability", 1.0) * prio


def _base_stat_magnitude(text):
    """Hero GENERAL row: |delta| / typical Valve step (signal F). None if unparsable."""
    t = _plain(text)
    key = next((k for k, rx in _BASE_STAT if rx.search(t)), None)
    step = _STEP.get(key) if key else None
    if not step:
        return None
    m = _FROMTO_RE.search(t)
    if m:
        delta = abs(float(m.group(2)) - float(m.group(1)))
    else:
        m = _BYN_RE.search(t)
        if not m:
            return None
        delta = abs(float(m.group(1)))
    return delta / step


# ---- items: gold scale (review E.6) ---------------------------------------------------
_PRICES = _json.load(open(_os.path.join(_HERE, "data", "rules", "item_stat_prices.json"),
                          encoding="utf-8"))["versions"]
# A priced row names ONLY the stat the item grants ("Agility bonus", "Bonus Damage", "Mana Regen").
# Rows about an active / aura / debuff ("Glimmer Bonus Movement Speed", "Dominated Creep movement
# speed", "Arctic Blast damage", "Corrosion armor reduction") are not the item's stat line and fall
# back to the hero formula — pricing them in gold scored a creep's move speed as the item's.
_ITEM_STAT_RE = [  # full stat phrase -> priced stat; %-stats listed in _PCT_STATS
    ("all_stats", r"all stats|all attributes"), ("strength", r"strength"), ("agility", r"agility"),
    ("intelligence", r"intelligence|int"), ("health_regen", r"health regen(?:eration)?|hp regen"),
    ("mana_regen", r"mana regen(?:eration)?"), ("lifesteal", r"(?:spell )?lifesteal"),
    ("spell_amp", r"spell amp(?:lification)?"), ("magic_res", r"magic resist(?:ance)?"),
    ("evasion", r"evasion"), ("attack_speed", r"attack speed"), ("armor", r"armor"),
    ("move_speed", r"movement speed|move speed"), ("health", r"(?:max )?health"),
    ("mana", r"(?:max )?mana"), ("damage", r"(?:attack )?damage"),
]
_ITEM_STAT = [(k, _re.compile(r"^\s*(?:bonus\s+)?(?:" + rx + r")(?:\s+bonus)?\s*$", _re.I))
              for k, rx in _ITEM_STAT_RE]
_PCT_STATS = {"lifesteal", "spell_amp", "magic_res", "evasion"}
_STAT_FROMTO_RE = _re.compile(r"from\s+\+?(-?\d+(?:\.\d+)?)(%?)\S*\s+to\s+\+?(-?\d+(?:\.\d+)?)(%?)", _re.I)
_TOTAL_COST_RE = _re.compile(r"total cost[^.]*?from\s+(\d+)[\d/]*g?\s+to\s+(\d+)", _re.I)
_TOTAL_SAME_RE = _re.compile(r"total cost (?:is )?unchanged", _re.I)
_COST_HEAD_RE = _re.compile(r"^\s*(?:recipe\s+)?cost\s*$", _re.I)
_COST_FROMTO_RE = _re.compile(r"from\s+(\d+)g?\s+to\s+(\d+)", _re.I)
ITEM_GOLD_K = 5.0        # 20% of the item's value = 1.0
ITEM_GOLD_W = 0.6        # neutral weight so item rows sit on the hero scale (median type weight)
_COST_CACHE = {}


def _item_cost(slug, version):
    """ItemCost from data/stats/<version>/items.json (or the nearest earlier snapshot)."""
    from .meta import RELEASE_HISTORY
    if version not in _COST_CACHE:
        order = [r["version"] for r in RELEASE_HISTORY]        # newest first
        start = order.index(version) if version in order else 0
        table = {}
        for v in order[start:]:
            f = _os.path.join(_HERE, "data", "stats", v, "items.json")
            if _os.path.exists(f):
                table = _json.load(open(f, encoding="utf-8"))
                break
        _COST_CACHE[version] = table
    rec = _COST_CACHE[version].get("item_" + (slug or ""), {})
    return rec.get("ItemCost") or 0


def _price(stat, version):
    from .meta import RELEASE_HISTORY
    order = [r["version"] for r in RELEASE_HISTORY]
    start = order.index(version) if version in order else 0
    for v in order[start:]:
        if v in _PRICES and stat in _PRICES[v]:
            return _PRICES[v][stat]
    return None


def _item_gold_fraction(text, ctx):
    """Δ of an item row in gold / item cost, or None when the row is not a priced stat / cost.
    Cost rows: "Total cost unchanged" -> 0 (only the build path moved); "Total cost A -> B" -> B-A;
    a basic item's "Cost A -> B" and a lone "Recipe cost A -> B" -> B-A (the total moves with the
    recipe unless the note says otherwise). The KV snapshots are NOT used for the delta: some
    (7.39c, 7.41 items.json) are pre-patch copies."""
    t = _plain(text)
    cost = _item_cost(ctx.get("item"), ctx.get("version"))
    if not cost:
        return None
    if _TOTAL_SAME_RE.search(t):
        return 0.0
    m = _TOTAL_COST_RE.search(t)
    if m:
        return abs(float(m.group(2)) - float(m.group(1))) / cost
    head = t
    vm = _VERB_RE.search(t)
    if vm and vm.start() > 0:
        head = t[:vm.start()]
    if _COST_HEAD_RE.match(head):
        m = _COST_FROMTO_RE.search(t)
        if not m:
            return None
        return abs(float(m.group(2)) - float(m.group(1))) / cost
    stat = next((k for k, rx in _ITEM_STAT if rx.match(head)), None)
    if not stat:
        return None
    m = _STAT_FROMTO_RE.search(t)
    if not m:
        return None
    is_pct = bool(m.group(2) or m.group(4))
    if is_pct != (stat in _PCT_STATS):
        return None                         # e.g. "bonus movement speed 22% -> 20%": not a flat stat
    price_key = "agility" if stat == "intelligence" else stat
    price = _price(price_key, ctx.get("version"))
    if price is None:
        return None
    return abs(float(m.group(3)) - float(m.group(1))) * price / cost


_J = _WJ.get("J", {}).get("u", {})       # signal J: value of +1% of the type (exchange rate)
J_PCT_UNIT = 20.0                        # a 20% change of a u=1 type = 1.0


_ABS_FROMTO_RE = _re.compile(r"from\s+([+\-\d./%s x]+?)\s+to\s+([+\-\d./%s x]+?)(?=[\s.,;)]|$)", _re.I)
_NUM_RE = _re.compile(r"-?\d+(?:\.\d+)?")


def _small_change_damp(text):
    """Absolute floor (agreement test 2026-09-17): a big % of a tiny number is still tiny.
    Seconds: |Δ| < 0.25 s -> x0.35, < 0.5 s -> x0.5. Percentage points: |Δ| < 2 pp -> x0.5.
    Δ is taken at the LAST level whose value changed — the same level _row_pcts sizes the row by.
    (Taking the last level blindly damped "30/25/20/15s -> 24/21/18/15s" x0.35: max rank equal.)
    1.0 when not applicable."""
    m = _ABS_FROMTO_RE.search(_plain(text))
    if not m:
        return 1.0
    a, b = m.group(1), m.group(2)
    na = [float(x) for x in _NUM_RE.findall(a)]
    nb = [float(x) for x in _NUM_RE.findall(b)]
    if not na or not nb:
        return 1.0
    n = max(len(na), len(nb))
    na, nb = (na + na[-1:] * n)[:n], (nb + nb[-1:] * n)[:n]
    delta = next((abs(y - x) for x, y in zip(reversed(na), reversed(nb)) if x != y), 0.0)
    if a.rstrip().endswith("s") or b.rstrip().endswith("s"):
        return 0.35 if delta < 0.25 else (0.5 if delta < 0.5 else 1.0)
    if "%" in a or "%" in b:
        return 0.5 if delta < 2 else 1.0
    return 1.0


COMPRESS = True


def _compress(x):
    """Soft ceiling for one row: up to 1.0 (a typical change) the value is linear, above it grows
    logarithmically — 1.5 -> 1.41, 2 -> 1.69, 3 -> 2.10, 6 -> 2.79. A halved niche parameter
    ("invisibility linger 2s -> 1s") no longer outweighs a real nerf of a core ability."""
    import math
    if not COMPRESS:
        return min(x, MAG_CAP_NORM)
    return x if x <= 1.0 else 1.0 + math.log(min(x, 6.0))


def _row_value(text, badge_html, kind, ctx):
    """Unsigned value of a buff/nerf row on the common scale (before context)."""
    if ctx and ctx.get("base_stat"):
        m = _base_stat_magnitude(text)
        if m is not None:
            return weight_of(kind) * min(m, MAG_CAP_NORM)
    pcts = _row_pcts(text, badge_html)
    damp = _small_change_damp(text)
    if pcts and kind in _J:
        return _compress(_J[kind] * (sum(pcts) / len(pcts)) / J_PCT_UNIT) * damp
    if pcts:
        return weight_of(kind) * _compress((sum(pcts) / len(pcts)) / _TPCT.get(kind, 20.0)) * damp
    return weight_of(kind)


try:
    _TTIERS = _json.load(open(_os.path.join(_HERE, "data", "rules", "talent_tiers.json"),
                              encoding="utf-8"))["tiers"]
except OSError:
    _TTIERS = {}
TALENT_SHIFT_UNIT = 0.2      # a 20-point move of the pro pick share against the sibling = 1.0
TALENT_MOVE_STEP = 0.5       # one level step (5 hero levels) earlier/later, in units of the type weight


def _talent_tier_net(ctx, cm):
    """Signal K for a "Level N Talent: A replaced with B" row -> signed net or None.
    1. measured: shift of the pro pick share of the slot against the UNCHANGED sibling
       (single-side replacements, >= 30 picks before and after);
    2. else inferred from LEVEL MOVES: a new talent that came from another level with the same
       meaning — earlier = buff of that effect, later = nerf (0.5 x type weight per level step).
    The tier total is split between the tier's rows (1 or 2 replaced sides)."""
    if not ctx or not ctx.get("talent") or not ctx.get("hero"):
        return None
    rec = _TTIERS.get(f"{ctx.get('version')}|{ctx['hero']}|{ctx['talent']}")
    if not rec:
        return None
    k = max(1, rec.get("changed", 1))
    if "share_delta" in rec:
        d = rec["share_delta"]
        return (1 if d > 0 else -1) * min(abs(d) / TALENT_SHIFT_UNIT, MAG_CAP_NORM) * weight_of("other") * cm / k
    if rec.get("moves"):
        tot = sum(m["steps"] * TALENT_MOVE_STEP * weight_of(m["type"]) for m in rec["moves"])
        return max(-1.5, min(1.5, tot)) * cm / k
    return None


def row_scores(text, tags, badge_html="", ctx=None):
    """(net, volume) of one row; both 0.0 when the row is not scorable."""
    kind = classify(text)
    cm = context_multiplier(ctx)
    w = weight_of(kind) * cm
    if "buff" in tags or "nerf" in tags:
        d = _DIR["buff"] if "buff" in tags else _DIR["nerf"]
        if ctx and ctx.get("kind") == "item":
            frac = _item_gold_fraction(text, ctx)
            if frac is not None:
                mag = min(ITEM_GOLD_K * frac, MAG_CAP_NORM)
                return round(ITEM_GOLD_W * d * mag, 3), round(ITEM_GOLD_W * mag, 3)
        val = _row_value(text, badge_html, kind, ctx) * cm
        return round(d * val, 3), round(val, 3)
    if "rework" in tags:
        net = _talent_tier_net(ctx, cm)             # signal K: talent replacement / level move
        if net is not None:
            return round(net, 3), round(max(w, abs(net)), 3)
        return 0.0, round(w, 3)
    if tags == {"new"}:
        return round(w * 0.5, 3), round(w, 3)
    if tags == {"del"}:
        return round(-w * 0.5, 3), round(w, 3)
    return 0.0, 0.0


def row_score(text, tags, badge_html=""):
    """Back-compat: the net scale only."""
    return row_scores(text, tags, badge_html)[0]
