# -*- coding: utf-8 -*-
"""Refresh the EXTERNAL data behind the weights (run after every patch, and monthly).

  1. data/rules/ability_priority.json  - how pros skill each hero (DEMOS, OpenDota only for heroes
                                         DEMOS has no builds for)           tools/fetch_skill_priority.py
  2. data/rules/talent_shift.json      - talent replacements: shift of the pro pick share
     data/rules/talent_tiers.json      - + level moves                       (model folder, signal K)
     Needs the research folder outputs/valve-revealed-weights-20260915 (KV history lives there);
     skipped with a note when it is absent. New patch windows are read from DEMOS; history is cached.

Usage:  python tools/refresh_weights_data.py            # everything
        python tools/refresh_weights_data.py --fast     # skip the slow talent feature pass (~15 min)
Then:   python build_site.py && python -m pytest tests -q   and commit data/rules/*.json
"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(os.path.expanduser("~"), "outputs", "valve-revealed-weights-20260915")


def run(args, cwd):
    print(">>", " ".join(args)); sys.stdout.flush()
    return subprocess.run([sys.executable] + args, cwd=cwd).returncode == 0


def main():
    ok = run(["tools/fetch_skill_priority.py"], HERE)
    if not os.path.isdir(MODEL):
        print("model folder not found - talent tables not refreshed:", MODEL)
        return 0 if ok else 1
    steps = ["k_talent_picks_fetch.py", "b_talent_pairs.py"]
    if "--fast" not in sys.argv:
        steps.append("k_talent_features.py")
    steps.append("k_talent_tiers.py")
    for s in steps:
        ok = run([s], MODEL) and ok
    subprocess.run(["git", "status", "--short", "data/rules"], cwd=HERE)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
