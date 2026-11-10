# -*- coding: utf-8 -*-
"""Fit signal R (patch/weights.py ADOPT_FIT): how much of the Tier 1-2 pro adoption shift a cell's net explains.

On every NON-rework cell (no REWORK / SWAP row, not a NEW + DEL replacement) with enough games, a robust line
(Theil-Sen, as the first fit 2026-09-26) through dlog = log(share after / share before) against the cell's net:
    dlog = slope x net + drift,    noise = median |dlog|  (the meta's own movement)
Run after the weights or the adoption data change (python build_site.py first: reads .cache/_dynamics.json),
then copy the printed numbers into ADOPT_FIT.  Needs numpy + scipy.

Usage:  python tools/fit_signal_r.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = (("hero", "hero_adoption.json", "heroes", 20), ("item", "item_adoption.json", "items", 30))


def cell_points(dynamics, adoption, kind, key, min_n):
    """(net, dlog) of the non-rework cells of one entity kind that have enough games."""
    out = []
    for ek, rec in dynamics.items():
        if not ek.startswith(kind + "|"):
            continue
        slug = rec.get("icon") or ek.split("|", 1)[1].replace("-", "_")
        for ver, b in rec.get("patches", {}).items():
            if b.get("rework") or b.get("swap") or (b.get("new") and b.get("del")) or "w" not in b:
                continue
            win = adoption.get(ver)
            n = win and win[key].get(slug)
            if not n or n[0] + n[1] < min_n or not all(win["games"]):
                continue
            g0, g1 = win["games"]
            out.append((b["w"], math.log(((n[1] + 1) / g1) / ((n[0] + 1) / g0))))
    return out


def fit(points):
    """{"slope", "drift", "noise", "n", "rho"} of a Theil-Sen line through (net, dlog) points."""
    import numpy as np
    from scipy.stats import spearmanr, theilslopes
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    slope, drift, _lo, _hi = theilslopes(y, x)
    return {"slope": round(float(slope), 3), "drift": round(float(drift), 3),
            "noise": round(float(np.median(np.abs(y))), 2), "n": len(points),
            "rho": round(float(spearmanr(x, y).correlation), 3)}


def main():
    dyn = json.load(open(os.path.join(HERE, ".cache", "_dynamics.json"), encoding="utf-8"))["entities"]
    for kind, fname, key, min_n in KINDS:
        adoption = json.load(open(os.path.join(HERE, "data", "rules", fname), encoding="utf-8"))["versions"]
        print(kind, fit(cell_points(dyn, adoption, kind, key, min_n)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
