# -*- coding: utf-8 -*-
"""Signal A v2 — Valve's gold price of EVERY item stat, per patch version.

Writes data/rules/item_stat_prices.json (read by patch/weights.py for item rows).

Data: items.txt of every version — data/stats/<v>/items.txt when present, else the d2vpkr history
kept with the weights model (~/outputs/valve-revealed-weights-20260915/items_history/<v>/items.txt).
Which KV fields are STAT LINES comes from Valve's own tooltips (data/abilities_english.txt):
`DOTA_Tooltip_ability_<item>_<field>` = "+$armor" / "%+Slow Resistance" is a row of the item's stat
list; the label names the stat. Items missing from today's tooltips (removed items) use the
field-name map learned from the same tooltips (bonus_strength -> strength, ...).

Method (per version):
  1. PURE items: purchasable (ItemCost > 0, not a recipe, not obsolete), no active (AbilityBehavior
     only PASSIVE), no ability heading in the tooltip ("Passive: Ability Upgrade" of Aghanim's
     Scepter; "Passive: Lifesteal" / "Damage Block" are stats) and every non-zero KV value is a
     stat line — Sange, Kaya, Yasha, Aether Lens,
     Octarine Core, Vanguard (its passive IS a stat: damage block, see 3.), all basic items.
     Items with an active or another passive carry value we cannot see, so they are not used.
  2. cost_i = sum_s price_s * x_is  over the pure items, non-negative least squares, residuals
     weighted 1/sqrt(cost) (a 10 % miss on a 5000 g item counts more than on a 150 g one, but not
     33x more). Upgrades (Sange = Ogre Axe + Belt + 650 recipe) price the stats that only exist on
     upgrades: the recipe pays for slow resistance + health restoration.
  3. Damage block is a stat of Vanguard / Crimson Guard / Stout Shield / Poor Man's Shield /
     Heaven's Halberd 7.38: value = chance x (melee block + ranged block) / 2 (expected damage
     blocked per attack, averaged over melee and ranged holders); priced like any other stat.
  4. Weak prior: every stat that a single-stat BASIC item sells (Ogre Axe = strength, Cloak =
     magic resistance, Talisman = evasion, Morbid Mask = lifesteal ...) gets a quarter-weight
     virtual item priced at that basic item's rate; %-stats without such an item get the median
     %-stat rate. It only decides what the data cannot: Sange-family stats (slow resistance,
     health restoration, status resistance, spell amp, mana regen amp) always come together, so
     their split is the prior's (confidence "prior"). Identified stats barely move.
  5. Confidence per stat: "anchor" (a single-stat basic item sells it), "fit" (identified by >= 2
     pure items), "single" (identified by one pure item: Aether Lens = cast range, Octarine Core =
     cooldown reduction, Dragon Lance = attack range, Vanguard = damage block), "prior" (collinear —
     only the family total is identified). Stats the data cannot identify and that have no prior,
     or whose fitted price is 0, are left unpriced -> weights.py falls back to the per-type weight.

Also written: the damage block value of every item that has one (so "Damage Block (passive)" without
numbers can be valued from the KV), and `ref_cost` — the median cost of purchasable items with an
active, used for mana-cost rows of items without a price (neutral items).

Usage:  python tools/fit_item_prices.py          # needs numpy + scipy (offline tool, not the build)
"""
import collections
import json
import math
import os
import re
import sys

import numpy as np
from scipy.optimize import lsq_linear

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from builders.silent import parse_kv  # noqa: E402
from patch.meta import RELEASE_HISTORY  # noqa: E402

MODEL = os.path.join(os.path.expanduser("~"), "outputs", "valve-revealed-weights-20260915")
HIST = os.path.join(MODEL, "items_history")
OUT = os.path.join(HERE, "data", "rules", "item_stat_prices.json")
LOC = os.path.join(HERE, "data", "abilities_english.txt")

PRIOR_WEIGHT = 0.25          # a stat's virtual prior item counts as a quarter of a real item
ZERO = 1e-9

# Tooltip label -> stat. Checked in order on the label text (after the leading "%+"/"+").
LABELS = [
    ("all_stats", r"\$all\b"), ("strength", r"\$str\b"), ("agility", r"\$agi\b"),
    ("intelligence", r"\$int\b"), ("primary_attribute", r"\$primary_attribute|\$selected_attrib"),
    ("damage", r"\$damage|^Damage \((?:MELEE|RANGED)\)"),
    ("armor", r"\$armor"), ("attack_speed_pct", r"\$attack_pct"), ("attack_speed", r"\$attack\b"),
    ("health", r"\$health"), ("mana", r"\$mana\b"),
    ("health_regen", r"\$hp_regen"), ("mana_regen", r"\$mana_regen"),
    ("magic_res", r"\$spell_resist"), ("evasion", r"\$evasion"),
    ("spell_lifesteal", r"\$spell_lifesteal"), ("lifesteal", r"\$lifesteal"),
    ("cast_range", r"\$cast_range"), ("attack_range", r"\$attack_range"),
    ("cooldown_reduction", r"\$cooldown_reduction"),
    ("slow_res", r"\$slow_resistance|^Slow Resistance"),
    ("status_res", r"\$status_resist|^Status Resistance"),
    ("restoration_amp", r"\$restoration_amp|^Health Regen and Lifesteal Amp|^Health Restoration"),
    ("spell_amp", r"^Spell Amplification"), ("mana_regen_amp", r"^Mana Regen Amplification"),
    ("spell_lifesteal_amp", r"^Spell Lifesteal Amplification"),
    ("manacost_reduction", r"\$manacost_reduction|^Mana Cost/Mana Loss Reduction"),
    ("aoe_bonus", r"\$aoe_bonus"), ("debuff_amp", r"\$debuff_amp"), ("heal_amp", r"\$healing_amp"),
    ("max_mana_pct", r"\$max_mana_percentage"), ("projectile_speed", r"\$projectile_speed|^Attack Projectile Speed"),
    ("night_vision", r"Night Vision|BONUS VISION|^Bonus Vision"), ("cast_speed", r"^Cast Speed"),
    ("max_health_regen_pct", r"^Max Health Regen"),
    ("move_speed", r"\$move_speed|^Movement Speed|^Move Speed \((?:Melee|Ranged) Heroes\)"),
]
_LABELS = [(s, re.compile(p)) for s, p in LABELS]
# stats measured in % (priced per 1 %); move speed is flat unless its label starts with "%"
PCT_STATS = {"magic_res", "evasion", "spell_lifesteal", "lifesteal", "cooldown_reduction", "slow_res",
             "status_res", "restoration_amp", "spell_amp", "mana_regen_amp", "spell_lifesteal_amp",
             "manacost_reduction", "debuff_amp", "heal_amp", "max_mana_pct", "cast_speed",
             "max_health_regen_pct", "attack_speed_pct", "move_speed_pct"}
# boots: movement speed from boots does not stack, Valve sells it far cheaper (Boots of Speed
# 45 MS = 500 g vs Wind Lace 15 MS = 225 g) -> its own stat
BOOTS = {"item_boots", "item_phase_boots", "item_power_treads", "item_arcane_boots",
         "item_tranquil_boots", "item_travel_boots", "item_travel_boots_2", "item_guardian_greaves",
         "item_boots_of_bearing"}
_ACTIVE_RE = re.compile(r"NO_TARGET|UNIT_TARGET|POINT|TOGGLE|CHANNELLED|AOE|DIRECTIONAL|AUTOCAST")
_BLOCK_FIELDS = {"block_damage_melee", "block_damage_ranged", "damage_block_melee",
                 "damage_block_ranged", "block_chance"}
_HEAD_RE = re.compile(r"<h1>\s*(?:Active|Passive|Toggle|Use|Upgrade|Aura)\s*:\s*([^<]*)</h1>", re.I)
_STAT_HEADS = {"lifesteal", "spell lifesteal", "damage block"}
# harmless non-stat fields (tooltip helpers, model size)
_INERT_RE = re.compile(r"^(?:tooltip_.*|model_scale|.*_tooltip)$")


def vkey(v):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", v)]


def load_loc():
    rx = re.compile(r'^\s*"([^"]+)"\s+"((?:[^"\\]|\\.)*)"', re.M)
    out = {}
    for m in rx.finditer(open(LOC, encoding="utf-8").read()):
        out.setdefault(m.group(1).lower(), m.group(2))
    return out


def label_stat(label):
    """Tooltip text of a stat line -> (stat, sign) or None when it is not a stat line."""
    m = re.match(r"^\s*(%?)([+\-])\s*(.*)$", label or "")
    if not m:
        return None
    pct, sign, body = m.groups()
    body = re.sub(r"<[^>]+>", "", body).strip()
    stat = next((s for s, rx in _LABELS if rx.search(body)), None)
    if stat is None:
        return None
    if stat == "move_speed" and pct:
        stat = "move_speed_pct"
    return stat, (1 if sign == "+" else -1)


def item_values(blk):
    """Non-zero first-level numeric KV values of an item block (AbilityValues or AbilitySpecial)."""
    out = {}
    av = blk.get("AbilityValues")
    if isinstance(av, dict):
        for k, v in av.items():
            out[k] = v.get("value", "") if isinstance(v, dict) else v
    asp = blk.get("AbilitySpecial")
    if isinstance(asp, dict):
        for d in asp.values():
            if isinstance(d, dict):
                for k, v in d.items():
                    if k not in ("var_type", "LinkedSpecialBonus", "CalculateSpellDamageTragedy"):
                        out.setdefault(k, v)
    num = {}
    for k, v in out.items():
        m = re.match(r"^\s*(-?\d+(?:\.\d+)?)", str(v))
        if m and float(m.group(1)) != 0:
            num[k] = float(m.group(1))
    return num


def learn_field_map(loc, item_names):
    """field -> stat, from every item tooltip whose field is shown as a stat line (for items the
    current tooltips no longer describe)."""
    seen = collections.defaultdict(collections.Counter)
    names = sorted(item_names, key=len, reverse=True)
    for key, text in loc.items():
        if not key.startswith("dota_tooltip_ability_item_"):
            continue
        rest = key[len("dota_tooltip_ability_"):]
        it = next((n for n in names if rest.startswith(n + "_")), None)
        if not it:
            continue
        ls = label_stat(text)
        if ls and ls[1] > 0:
            seen[rest[len(it) + 1:]][ls[0]] += 1
    fmap = {f: c.most_common(1)[0][0] for f, c in seen.items() if len(c) == 1}
    # historic field names the current tooltips do not use any more
    fmap.update({"bonus_spell_amp": "spell_amp", "bonus_status_resistance": "status_res",
                 "bonus_slow_resistance": "slow_res", "bonus_magic_resistance": "magic_res"})
    return fmap


def kv_path(v):
    p = os.path.join(HERE, "data", "stats", v, "items.txt")
    if os.path.exists(p):
        return p
    p = os.path.join(HIST, v, "items.txt")
    return p if os.path.exists(p) else None


def damage_block(vals):
    ch = vals.get("block_chance")
    mel = vals.get("block_damage_melee", vals.get("damage_block_melee"))
    rng = vals.get("block_damage_ranged", vals.get("damage_block_ranged", mel))
    if not (ch and mel):
        return None
    return round(ch / 100.0 * (mel + (rng or 0)) / 2.0, 3)


def parse_version(v, loc, fmap):
    root = parse_kv(open(kv_path(v), encoding="utf-8", errors="replace").read())
    root = root.get("DOTAAbilities", root)
    items = {}
    for name, blk in root.items():
        if not (isinstance(blk, dict) and name.startswith("item_")) or "recipe" in name:
            continue
        try:
            cost = float(blk.get("ItemCost", 0) or 0)
        except ValueError:
            cost = 0.0
        vals = item_values(blk)
        in_loc = f"dota_tooltip_ability_{name}" in loc
        stats, other, amounts = {}, {}, collections.defaultdict(list)

        def field_stat(f):
            lab = loc.get(f"dota_tooltip_ability_{name}_{f}")
            ls = label_stat(lab) if lab else None
            if ls is None and not lab and f in fmap:
                ls = (fmap[f], 1)
            return ls

        for f, x in vals.items():
            ls = field_stat(f)
            base = re.sub(r"_(?:melee|ranged?)$", "", f)
            if ls is None and base != f and base in vals:
                ls = field_stat(base)          # "<stat field>_melee": melee value of the same stat line
            if ls is None:
                if f not in _BLOCK_FIELDS and not _INERT_RE.match(f):
                    other[f] = x
                continue
            stat, sign = ls
            if stat == "move_speed" and name in BOOTS:
                stat = "boots_move_speed"
            amounts[stat].append(sign * abs(x))
        for stat, xs in amounts.items():
            # melee/ranged variants (Phase Boots damage, Power Treads MS) -> their mean;
            # the same value twice (Cloak: tooltip_resist + bonus_magical_armor) -> once
            stats[stat] = sum(set(xs)) / len(set(xs)) if len(xs) > 1 else xs[0]
        blk_val = damage_block(vals)
        if blk_val:
            stats["damage_block"] = blk_val
        # an ability the KV does not spell out in values (Aghanim's Scepter "Ability Upgrade"):
        # today's tooltip headings; a stat-like passive (Lifesteal, Damage Block) is a stat
        heads = [h for h in _HEAD_RE.findall(loc.get(f"dota_tooltip_ability_{name}_description", ""))
                 if h.strip().lower() not in _STAT_HEADS]
        if heads:
            other["<ability>"] = len(heads)
        beh = blk.get("AbilityBehavior", "") or ""
        purchasable =(cost > 0 and blk.get("ItemPurchasable") != "0" and blk.get("IsObsolete") != "1")
        reqs = None
        rec = root.get("item_recipe_" + name[5:])
        if isinstance(rec, dict):
            rq = rec.get("ItemRequirements")
            reqs = (rq.get("01") if isinstance(rq, dict) else None) or ""
        items[name] = {
            "cost": cost, "stats": stats, "other": other, "purchasable": purchasable,
            "active": bool(_ACTIVE_RE.search(beh)), "basic": rec is None, "in_loc": in_loc,
            "components": reqs,
        }
    return items


def pure(it):
    return (it["purchasable"] and not it["active"] and not it["other"] and it["stats"]
            and all(x > 0 for x in it["stats"].values()))


def direct_prices(items):
    """Single-stat basic items: gold per unit, median per stat (the 'anchor' rate)."""
    per = collections.defaultdict(list)
    for it in items.values():
        if pure(it) and it["basic"] and len(it["stats"]) == 1:
            (s, x), = it["stats"].items()
            per[s].append(it["cost"] / x)
    return {s: float(np.median(v)) for s, v in per.items()}


def identified(A, cols):
    """Columns whose coefficient the design A pins down (not in the null space)."""
    if A.shape[0] == 0:
        return set()
    _, sv, vt = np.linalg.svd(A, full_matrices=True)
    rank = int((sv > sv.max() * 1e-8).sum()) if len(sv) else 0
    null = vt[rank:]
    return {c for j, c in enumerate(cols) if null.shape[0] == 0 or np.abs(null[:, j]).max() < 1e-6}


def fit_version(items):
    rows = [it for it in items.values() if pure(it)]
    anchors = direct_prices(items)
    pct_anchor = [p for s, p in anchors.items() if s in PCT_STATS]
    pct_prior = float(np.median(pct_anchor)) if pct_anchor else None
    stats = sorted({s for it in rows for s in it["stats"]})
    idx = {s: j for j, s in enumerate(stats)}
    A, y = [], []
    for it in rows:
        w = 1.0 / math.sqrt(it["cost"])
        a = np.zeros(len(stats))
        for s, x in it["stats"].items():
            a[idx[s]] = x * w
        A.append(a)
        y.append(it["cost"] * w)
    A, y = np.array(A), np.array(y)
    data_ident = identified(A, stats)
    prior = {}
    for s in stats:
        if s in anchors:
            prior[s] = anchors[s]
        elif s in PCT_STATS and pct_prior:
            prior[s] = pct_prior
    # virtual prior items: typical amount of the stat at the prior rate, quarter weight
    P, q = [], []
    for s, p0 in prior.items():
        amt = float(np.median([it["stats"][s] for it in rows if s in it["stats"]]))
        val = p0 * amt
        w = math.sqrt(PRIOR_WEIGHT) / math.sqrt(val)
        a = np.zeros(len(stats))
        a[idx[s]] = amt * w
        P.append(a)
        q.append(val * w)
    AA = np.vstack([A] + ([np.array(P)] if P else []))
    yy = np.concatenate([y] + ([np.array(q)] if q else []))
    sol = lsq_linear(AA, yy, bounds=(0, np.inf), method="bvls")
    ident = identified(AA, stats)
    carriers = collections.Counter(s for it in rows for s in it["stats"])
    prices, conf = {}, {}
    for s in stats:
        p = float(sol.x[idx[s]])
        if s not in ident or p <= ZERO:
            continue                                   # not pinned down, no prior: unpriced
        prices[s] = round(p, 3 if p < 10 else 1)
        if s in anchors:
            conf[s] = "anchor"
        elif s not in data_ident:
            conf[s] = "prior"
        else:
            conf[s] = "fit" if carriers[s] >= 2 else "single"
    return prices, conf, {"n_pure": len(rows), "anchors": {s: round(p, 1) for s, p in anchors.items()}}


def ref_cost(items):
    costs = [it["cost"] for it in items.values() if it["purchasable"] and it["active"] and it["cost"] >= 500]
    return float(np.median(costs)) if costs else None


def write_json(data):
    """One line per version (diff-friendly, ~5x smaller than indent=1)."""
    parts = []
    for k, val in data.items():
        if isinstance(val, dict) and val and all(isinstance(x, dict) for x in val.values()):
            inner = ",\n".join(f"  {json.dumps(v)}: {json.dumps(x, ensure_ascii=False, sort_keys=True)}"
                               for v, x in val.items())
            parts.append(f" {json.dumps(k)}: {{\n{inner}\n }}")
        else:
            parts.append(f" {json.dumps(k)}: {json.dumps(val, ensure_ascii=False)}")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("{\n" + ",\n".join(parts) + "\n}\n")


def main():
    loc = load_loc()
    versions = sorted({r["version"] for r in RELEASE_HISTORY if kv_path(r["version"])}, key=vkey)
    names = set()
    for v in versions:
        names |= set(re.findall(r'^\t"(item_[a-z0-9_]+)"', open(kv_path(v), encoding="utf-8",
                                                                  errors="replace").read(), re.M))
    fmap = learn_field_map(loc, names)
    out_v, out_c, out_meta, out_block, out_ref, out_nfs = {}, {}, {}, {}, {}, {}
    last_nfs = None
    for v in versions:
        items = parse_version(v, loc, fmap)
        nfs = sorted(n[5:] for n, it in items.items() if it["cost"] > 0 and not it["purchasable"])
        if nfs != last_nfs:                  # stored at change points only
            out_nfs[v] = last_nfs = nfs
        prices, conf, meta = fit_version(items)
        out_v[v], out_c[v], out_meta[v] = prices, conf, meta
        out_ref[v] = ref_cost(items)
        out_block[v] = {n[5:]: it["stats"]["damage_block"] for n, it in sorted(items.items())
                        if "damage_block" in it["stats"]}
    doc = ("Gold per +1 unit of every item stat, per patch version (signal A v2, tools/fit_item_prices.py; "
           "method in docs/weights.md 'Item prices'). %-stats are priced per 1 %. damage_block unit = "
           "expected damage blocked per attack (chance x mean of melee and ranged block). confidence: "
           "anchor = a single-stat basic item sells it, fit = identified by >= 2 pure items, single = by "
           "one pure item, prior = only the item family's total is identified, the split is the weak "
           "prior's. ref_cost = median cost of "
           "purchasable items with an active (mana-cost rows of items without a price). not_for_sale = items "
           "with an ItemCost that the shop does not sell (Roshan drops, neutral items), listed at the "
           "versions where the list changes (valid until the next entry).")
    data = {"_doc": doc, "versions": out_v, "confidence": out_c, "ref_cost": out_ref,
            "damage_block": out_block, "not_for_sale": out_nfs,
            "n_pure": {v: m["n_pure"] for v, m in out_meta.items()}}
    write_json(data)
    last = versions[-1]
    print(f"{len(versions)} versions, {last}: {out_meta[last]['n_pure']} pure items")
    print(f"{'stat':22s} {'price':>8s} {'conf':7s} {'anchor':>8s}")
    for s in sorted(out_v[last]):
        print(f"{s:22s} {out_v[last][s]:8.2f} {out_c[last][s]:7s} {out_meta[last]['anchors'].get(s, ''):>8}")


if __name__ == "__main__":
    main()
