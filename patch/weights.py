"""Row scoring for the dynamics widget "Weights" mode — two scales per (entity, patch).

  w  (net balance)  = Σ weight(type) × direction × magnitude     signed
  v  (volume)       = Σ weight(type) × magnitude                 unsigned, reworks included

  type       — characteristic class of the row (ordered regex table, first match wins).
               Matched against the PARAMETRIC part of the row (text before the first verb
               increased/decreased/rescaled/…), then against the whole row as a fallback —
               so "Cooldown decreased … dispels …" is cooldown, not bkb_pierce.
  weight     — data/rules/valve_weights.json "final" (consensus shrunk towards `other`
               when fewer than 3 signals back the type: w = other + (raw − other) × n/3).
  direction  — +1 buff, −1 nerf, ±0.5 new/del (only when it is the row's sole tag),
               0 rework/misc/qol.
  magnitude  — mean |%| over the row's per-level badges INCLUDING 0% ones, clamped to
               MAG_CAP and divided by 25 (25% = 1.0). "Recipe … Total cost …" rows use
               the total-cost badge only. Rows without a % badge count as 1.0.
  volume     — buff/nerf/new/del rows: weight × magnitude; rework rows: weight × 1.0
               (a rework is a big, sign-less decision); misc/qol: 0.

Decisions 2026-09-16 (Денис): two scales (net + volume), hybrid magnitude (typical Valve
step for base stats — TODO next step, % for the rest).
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
    ("cast_point", r"cast point|cast time|backswing|attack point|animation|\bdelay\b"),
    ("stun", r"stun|bash|knockback|taunt"),
    ("silence", r"silence|\bhex\b|\broot|disarm|mute|leash"),
    ("slow_res", r"slow resist"), ("slow", r"slow"), ("status_res", r"status resist"),
    ("spell_amp", r"spell amp|spell damage amp"),
    ("attack_speed", r"attack speed|base attack time|\bbat\b"),
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
    ("turn_rate", r"turn rate"), ("vision", r"vision|sight|reveal"),
    ("cost", r"recipe cost|total cost|\bcost\b|price"),
    ("damage", r"damage|dmg|dps|burn|cleave"),
    ("duration", r"duration|\btime\b|lasts|linger|channel"),
    ("range", r"radius|range|distance|\baoe\b|\barea\b|width|length"),
    ("projectile", r"projectile|missile"),
    ("bkb_pierce", r"pierce|debuff immun|spell immun|magic immun|dispel"),
    ("chance", r"chance|probability"),
]
_CAT = [(c, _re.compile(p, _re.I)) for c, p in CAT]
_TAGS_RE = _re.compile(r"<[^>]+>")
_VERB_RE = _re.compile(r"\b(increased|decreased|reduced|improved|rescaled|changed|lowered|raised|"
                       r"replaced|now|no longer|removed|added)\b", _re.I)
_PCT_RE = _re.compile(r'class="badge (?:(?:buff|nerf)\d+|neutral)">([+\-−]?\d+(?:\.\d+)?)%<')
_DIR = {"buff": 1.0, "nerf": -1.0}
MAG_CAP = 50.0


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
    for c, rx in _CAT:
        if rx.search(head):
            return c
    return next((c for c, rx in _CAT if rx.search(t)), "other")


def weight_of(kind):
    return _W.get(kind, _W["other"])


def _magnitude(text, badge_html):
    pcts = [abs(float(x.replace("−", "-"))) for x in _PCT_RE.findall(badge_html or "")]
    if not pcts:
        return 1.0
    if len(pcts) >= 2 and _re.search(r"total cost", _plain(text), _re.I):
        pcts = [pcts[-1]]                       # recipe + total: the total is the real change
    return min(sum(pcts) / len(pcts), MAG_CAP) / 25.0


def row_scores(text, tags, badge_html=""):
    """(net, volume) of one row; both 0.0 when the row is not scorable."""
    kind = classify(text)
    w = weight_of(kind)
    if "buff" in tags or "nerf" in tags:
        d = _DIR["buff"] if "buff" in tags else _DIR["nerf"]
        mag = _magnitude(text, badge_html)
        return round(w * d * mag, 3), round(w * mag, 3)
    if "rework" in tags:
        return 0.0, round(w, 3)
    if tags == {"new"}:
        return round(w * 0.5, 3), round(w, 3)
    if tags == {"del"}:
        return round(-w * 0.5, 3), round(w, 3)
    return 0.0, 0.0


def row_score(text, tags, badge_html=""):
    """Back-compat: the net scale only."""
    return row_scores(text, tags, badge_html)[0]
