"""Row scoring for the dynamics widget "Weights" mode.

score = weight(type) x direction x magnitude
  type       — characteristic class of the row text (ordered regex table, first match wins;
               same table as outputs/valve-revealed-weights-20260915/common.py CAT)
  weight     — data/rules/valve_weights.json (Valve revealed-preference consensus, 0..1)
  direction  — +1 buff, -1 nerf, +0.5 new, -0.5 del, 0 rework/misc/qol
  magnitude  — mean |%| over the row's per-level badges, clamped to 50, divided by 25 (25% = 1.0);
               rows without a % badge count as 1.0
Per (entity, patch) the scores are summed into the dynamics bucket key "w".
"""
import json as _json
import os as _os
import re as _re

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_W = _json.load(open(_os.path.join(_HERE, "data", "rules", "valve_weights.json"),
                     encoding="utf-8"))["weights"]

CAT = [  # ordered: first match wins
    ("bkb_pierce", r"pierce|debuff immun|spell immun|magic immun|dispel"),
    ("cooldown", r"cooldown|\bcd\b|charge restore|recharge"),
    ("mana_cost", r"mana cost|manacost"),
    ("cast_range", r"cast range"),
    ("cast_point", r"cast point|cast time|backswing|attack point|animation|\bdelay\b"),
    ("stun", r"stun|bash|knockback|taunt"),
    ("silence", r"silence|\bhex\b|\broot|disarm|mute|leash"),
    ("slow_res", r"slow resist"), ("slow", r"slow"), ("status_res", r"status resist"),
    ("spell_amp", r"spell amp|spell damage amp"),
    ("attack_speed", r"attack speed|base attack time|\bbat\b"),
    ("move_speed", r"movement speed|move speed|movespeed|movement|\bms\b"),
    ("evasion", r"evasion|dodge|backtrack|miss chance"),
    ("magic_res", r"magic resist|magical resist|spell block"),
    ("armor", r"armor|corruption"), ("crit", r"crit"),
    ("lifesteal", r"lifesteal|\bsteal\b"),
    ("health", r"health|\bhp\b|regen|\bheal|healing"), ("mana", r"\bmana\b|\bmp\b"),
    ("stats", r"strength|agility|intelligence|all stats|attribute"),
    ("base_damage", r"base damage|attack damage|damage at level"),
    ("charges", r"charge|stack|max attacks|attacks to"),
    ("gold_xp", r"gold|bounty|experience|\bxp\b"), ("respawn", r"respawn|reincarnat"),
    ("turn_rate", r"turn rate"), ("vision", r"vision|sight|reveal"),
    ("cost", r"recipe cost|total cost|\bcost\b|price"),
    ("damage", r"damage|dmg|dps|burn|cleave"), ("duration", r"duration|\btime\b|lasts|channel"),
    ("range", r"radius|range|distance|\baoe\b|\barea\b|width|length"),
    ("projectile", r"projectile|missile|speed"), ("chance", r"chance|\bproc|probability"),
]
_CAT = [(c, _re.compile(p, _re.I)) for c, p in CAT]
_TAGS_RE = _re.compile(r"<[^>]+>")
_PCT_RE = _re.compile(r'class="badge (?:buff|nerf)\d+">([+\-\u2212]?\d+(?:\.\d+)?)%<')
_DIR = {"buff": 1.0, "nerf": -1.0, "new": 0.5, "del": -0.5}
MAG_CAP = 50.0


def classify(text):
    t = _TAGS_RE.sub(" ", text or "")
    return next((c for c, rx in _CAT if rx.search(t)), "other")


def weight_of(kind):
    return _W.get(kind, _W["other"])


def row_score(text, tags, badge_html=""):
    """Signed weighted score of one row, 0.0 when the row is not directional."""
    d = next((_DIR[t] for t in ("buff", "nerf", "new", "del") if t in tags), 0.0)
    if not d:
        return 0.0
    pcts = [abs(float(x.replace("−", "-"))) for x in _PCT_RE.findall(badge_html or "")]
    mag = min(sum(pcts) / len(pcts), MAG_CAP) / 25.0 if pcts else 1.0   # mean over per-level badges
    return round(weight_of(classify(text)) * d * mag, 2)
