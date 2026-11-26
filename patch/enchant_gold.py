"""Neutral enchantment rows in gold (owner 2026-11-26: "можем учитывать это всё для весов?" -> "да").

An enchantment has no shop price, but its stats do (data/rules/item_stat_prices.json). A row like "Health bonus
changed from +110/150/190/230 to +110/170/230" is scored like an item row: the gold the stat moves, over what the
whole enchantment is worth.
- Values per tier: data/rules/enchant_tables.json (scripts/gen/enchant_table.py).
- Compared TIER AGAINST TIER on the patch's own tier schedule (data/rules/neutral_tier_times.json): players swap
  the enchantment every time a tier opens, so what matters is what it gives at each tier it is offered at. Each
  tier slot lasts from its start to the next tier's start; the enchantment counts only while its tier is the
  current one. A change of the schedule itself (7.42: tier 3 at 30:00 instead of 25:00) hits every enchantment
  alike and is not put on each one's rows. (A Fable 5.2 review the same day proposed real game minutes with the old
  schedule on the old side; the owner chose tier against tier: "с тиром".)
- Minutes are weighted by the share of pro games still running (SURVIVAL), over the minutes the enchantment is held
  on both sides. Gold moved = price x that weighted mean of (new - old).
- Worth of the enchantment = the same weighted mean of its priced stats' gold, the mean of before and after.
  Penalties ("Damage penalty", red labels) are neither priced nor counted in the worth: what they cost depends on
  the hero's role.
- None (the caller keeps its usual formula): penalties, an enchantment with a stat that has no shop price (its
  worth would be too low: Timeless 7.42 scored -3.2), no table or tier times for the patch, no change.
"""

import html as _html
import json as _json
import os as _os
import re as _re

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_TABLES = None
_TIMES = None
_NUM_RE = _re.compile(r"[-−]?\d+(?:\.\d+)?")
_HEAD_RE = _re.compile(r"^\s*(?:now (?:also )?provides|no longer provides)\s+[^A-Za-z]*", _re.I)
_TAG_RE = _re.compile(r"<[^>]+>")
_RED = "#e03e2e"                       # the notes' penalty colour

# Share of pro games still running at minute m (hero-games reaching each tier, all pro matches 7.38-7.42,
# 82 790 hero-games at 25/35/60 min); linear between the knots.
SURVIVAL = ((0, 1.0), (15, 0.995), (25, 0.936), (35, 0.64), (60, 0.064), (75, 0.0))
HORIZON = 75


def _load(name):
    try:
        with open(_os.path.join(_HERE, "data", "rules", name), encoding="utf-8") as f:
            return _json.load(f)
    except OSError:
        return {}


def _tables():
    global _TABLES
    if _TABLES is None:
        _TABLES = _load("enchant_tables.json")
    return _TABLES


def _times(version):
    global _TIMES
    if _TIMES is None:
        _TIMES = _load("neutral_tier_times.json").get("versions", {})
    return _TIMES.get(version or "")


def survival(m):
    for (m0, s0), (m1, s1) in zip(SURVIVAL, SURVIVAL[1:]):
        if m0 <= m <= m1:
            return s0 + (s1 - s0) * (m - m0) / (m1 - m0)
    return 0.0


def _num(v):
    m = _NUM_RE.search(str(v or ""))
    return float(m.group(0).replace("−", "-")) if m else 0.0


def clean_label(st):
    """Label without the notes' markup: "<font color='#e03e2e'>Damage penalty</font>" -> "Damage penalty"."""
    return " ".join(_html.unescape(_TAG_RE.sub("", st.get("label") or "")).split())


def is_penalty(st):
    raw = (st.get("label") or "").lower()
    return bool(st.get("penalty")) or _RED in raw or "penalty" in clean_label(st).lower()


def stat_is_pct(stat):
    return any("%" in str(x) for x in list(stat.get("new", {}).values()) + list(stat.get("old", {}).values()))


def _block(name, version):
    tab = _tables().get(version) or {}
    if name in tab:
        return tab[name]
    low = (name or "").lower()                 # "Keen-Eyed" (7.41 table) vs "Keen-eyed" (page)
    return next((b for k, b in tab.items() if k.lower() == low), None)


def _stat_row(block, text):
    """The table stat the row is about: the longest label the row starts with (after "Now provides +0/0/16%")."""
    head = _HEAD_RE.sub("", _TAG_RE.sub("", _html.unescape(text))).strip().lower()
    stats = [(st, clean_label(st).lower()) for st in block.get("stats", [])]
    full = [(st, lab) for st, lab in stats if lab and head.startswith(lab)]
    if full:
        return max(full, key=lambda x: len(x[1]))[0]
    # the row shortens the label: "No longer provides +25% Slow Resist" / table "Slow Resistance"
    stem = _re.split(r"\s+(?:bonus|changed|increased|decreased|reduced|now)\b", head)[0].strip()
    short = [(st, lab) for st, lab in stats if stem and lab.startswith(stem)]
    return short[0][0] if len(short) == 1 else None


def _step(tiers, times):
    """(offered tiers, [(start minute, tier)] of ALL the patch's tiers). A tier the schedule does not have (the old
    side's tier 5 on the 7.42 schedule) has no slot and is dropped; None when nothing is left."""
    offered = {str(t) for t in tiers if str(t) in times}
    if not offered:
        return None
    return offered, sorted((start, t) for t, start in times.items())


def _value_at(step, vals, m):
    """Value at minute m, or None when the enchantment is not held then. Players swap the enchantment every time a
    tier opens (owner 2026-11-26: "чары точно всегда меняют"), so it counts only while the CURRENT tier (the latest
    one opened) is a tier it is offered at: before its first tier and after a later tier without it, it is gone."""
    offered, starts = step
    cur = None
    for start, t in starts:
        if start <= m:
            cur = t
    return _num(vals.get(cur)) if cur in offered else None


def _minutes():
    return [(m + 0.5, survival(m + 0.5)) for m in range(HORIZON)]


def _sides(block, version):
    """Both sides on the patch's OWN tier schedule: tier against tier, each tier slot weighted by how long it lasts.
    A change of the schedule itself (7.42: tier 3 at 30:00 instead of 25:00) hits every enchantment alike and is
    not put on each one's rows (owner 2026-11-26, "с тиром": Keen-eyed's Mana Regen 1.5 -> 2 at tier 3 is a buff,
    not cancelled by tier 3 opening later)."""
    new_t = _times(version)
    if not new_t:
        return None
    new = _step(block.get("tiers_new") or [], new_t)
    old = _step(block.get("tiers_old") or [], new_t)
    if not new or not old:
        return None
    return old, new


def _worth(block, step, side, price_of):
    """Survival-weighted mean gold of the side's non-penalty stats over the minutes it can be had; None when one of
    them has no price (night vision, debuff amp, Item Potency)."""
    priced = []
    for st in block.get("stats", []):
        if is_penalty(st):
            continue
        vals = st.get(side) or {}
        if not any(_num(v) for v in vals.values()):
            continue
        p = price_of(st)
        if p is None:
            return None
        priced.append((p, vals))
    num = den = 0.0
    for m, w in _minutes():
        if _value_at(step, {}, m) is None:
            continue
        num += w * sum(p * (_value_at(step, vals, m) or 0.0) for p, vals in priced)
        den += w
    return num / den if den else 0.0


def enchant_row_gold(text, name, version, price_of):
    """(signed gold, enchantment worth) of one enchantment row, or None when the row is not a priced stat.
    `price_of(stat_entry)` -> gold per +1 of that table stat in `version`, or None."""
    block = _block(name, version)
    if not block:
        return None
    st = _stat_row(block, text)
    if st is None or is_penalty(st):
        return None
    p = price_of(st)
    if p is None:
        return None
    sides = _sides(block, version)
    if sides is None:
        return None
    old_step, new_step = sides
    old, new = st.get("old") or {}, st.get("new") or {}
    num = den = 0.0
    for m, w in _minutes():
        a, b = _value_at(old_step, old, m), _value_at(new_step, new, m)
        if a is None or b is None:
            continue
        num += w * (b - a)
        den += w
    if not den or not num:
        return None
    delta = num / den
    w_new = _worth(block, new_step, "new", price_of)
    w_old = _worth(block, old_step, "old", price_of)
    if w_new is None or w_old is None:
        return None
    worth = (w_new + w_old) / 2.0 if (w_new and w_old) else (w_new or w_old)
    if not worth or worth <= 0:
        return None
    return p * delta, worth
