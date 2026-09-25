# -*- coding: utf-8 -*-
"""Signal J — Valve's exchange rate between characteristics, refitted for how the site uses it.

Data: events.json of the research folder (outputs/valve-revealed-weights-20260915, t_events.py).
Pairs: inside one (hero, patch) every numeric buff is paired with every numeric nerf of another
type (the same rule as cde_dynamics.py, signal C): Valve paid n% of Y for b% of X, so
    log u_X - log u_Y = log n - log b          (least squares, anchor mean log u = 0).
u = value of +1 % of the type; types with < 30 pair sides are dropped.

Why a refit (2026-09-25): the first fit pooled hero BASE-STAT events with ability/talent events.
Base stats move in tiny % steps (+5 of 300 movement speed = 1.7 %, +3 of 55 damage = 5 %), so they
dragged u up for exactly the types that also name ability parameters: base_damage 2.80, move_speed
2.11, stats 1.21. The site never applies J to base-stat rows (those use Valve's typical step), so a
spell's "Base Damage 270 -> 240" was valued as if it were hero base damage (x2.6 over "Damage").
Here base-stat events get their own types ("base:<type>", kept in the file for reference only) and
the u used by patch/weights.py comes from ability/talent events: base_damage 1.23, move_speed 1.12.
Blind-judge agreement (docs/weights.md): sample 1 rho 0.346 -> 0.377, sample 2 0.426 -> 0.452.

Usage:  python tools/fit_signal_j.py            # writes data/rules/valve_weights.json -> "J"
"""
import collections
import json
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(os.path.expanduser("~"), "outputs", "valve-revealed-weights-20260915")
MIN_SIDES = 30
BOOT = 200


def type_of(e):
    return ("base:" + e["type"]) if e["scope"] == "hero_base" else e["type"]


def compensation_pairs(events):
    by = collections.defaultdict(lambda: {"+": [], "-": []})
    for e in events:
        if e["sign"]:
            by[(e["hero"], e["patch"])]["+" if e["sign"] > 0 else "-"].append(e)
    out = []
    for d in by.values():
        for b in d["+"]:
            for n in d["-"]:
                tb, tn = type_of(b), type_of(n)
                if tb != tn and "other" not in (b["type"], n["type"]):
                    out.append((tb, tn, abs(b["pct"]), abs(n["pct"])))
    return out


def fit(pairs):
    sides = collections.Counter()
    for tb, tn, _, _ in pairs:
        sides[tb] += 1
        sides[tn] += 1
    types = sorted(t for t, k in sides.items() if k >= MIN_SIDES)
    ti = {t: i for i, t in enumerate(types)}
    use = [p for p in pairs if p[0] in ti and p[1] in ti and p[2] > 0 and p[3] > 0]
    a = np.zeros((len(use) + 1, len(types)))
    y = np.zeros(len(use) + 1)
    for k, (tb, tn, bp, np_) in enumerate(use):
        a[k, ti[tb]], a[k, ti[tn]] = 1, -1
        y[k] = math.log(np_) - math.log(bp)
    a[-1, :] = 1
    sol = np.linalg.lstsq(a, y, rcond=None)[0]
    return {t: math.exp(sol[ti[t]]) for t in types}, {t: sides[t] for t in types}, len(use)


def main():
    path = os.path.join(MODEL, "events.json")
    if not os.path.exists(path):
        print("research folder not found:", path)
        return 1
    events = [e for e in json.load(open(path, encoding="utf-8"))
              if e["kind"] == "numeric" and e["pct"] is not None
              and e["scope"] in ("ability", "hero_base", "talent")]
    pairs = compensation_pairs(events)
    u, n, used = fit(pairs)
    rng = random.Random(20260925)
    boot = collections.defaultdict(list)
    for _ in range(BOOT):
        bu, _, _ = fit([pairs[rng.randrange(len(pairs))] for _ in pairs])
        for t, v in bu.items():
            boot[t].append(v)
    ci = {t: [round(sorted(v)[int(0.025 * len(v))], 2), round(sorted(v)[int(0.975 * len(v)) - 1], 2)]
          for t, v in boot.items() if t in u}
    wpath = os.path.join(HERE, "data", "rules", "valve_weights.json")
    wj = json.load(open(wpath, encoding="utf-8"))
    wj["J"] = {
        "_doc": ("Signal J - exchange rate: log u_X - log u_Y = log(nerf%) - log(buff%) over Valve's "
                 "buff<->nerf compensation pairs inside one (hero, patch) (events.json of the research "
                 "folder, types with >= 30 sides), least squares, anchor mean log u = 0; ci = 95% "
                 "bootstrap. Hero BASE-STAT events are typed separately (base_u, reference only: the site "
                 "sizes base-stat rows by Valve's typical step), so u is the value of +1% of an "
                 "ability/talent/item parameter. Used for % rows: value = u * mean|%| / 20. "
                 "Refit: python tools/fit_signal_j.py"),
        "pairs": used,
        "u": {t: round(v, 3) for t, v in u.items() if not t.startswith("base:")},
        "ci": {t: v for t, v in ci.items() if not t.startswith("base:")},
        "n": {t: v for t, v in n.items() if not t.startswith("base:")},
        "base_u": {t[5:]: round(v, 3) for t, v in u.items() if t.startswith("base:")},
    }
    with open(wpath, "w", encoding="utf-8") as f:
        json.dump(wj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    for t in sorted(u):
        print(f"{t:18} u={u[t]:.3f} ci={ci.get(t)} sides={n[t]}")
    print("pairs used:", used)
    return 0


if __name__ == "__main__":
    sys.exit(main())
