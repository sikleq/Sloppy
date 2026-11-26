# -*- coding: utf-8 -*-
"""When each neutral tier opens, per patch -> data/rules/neutral_tier_times.json ({version: {tier: minute}}).

From neutral_items.txt of each patch since 7.38 ("neutral_tiers" -> tier -> "start_time", "M:SS"). Used by
patch/enchant_gold.py to compare an enchantment's values by game minute, not by tier number: 7.42 moved tier 3
from 25:00 to 30:00 and tier 4 from 35:00 to 50:00 (Fable 5.2 review 2026-11-26).

Usage:  python tools/build_neutral_tier_times.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from patch import game_files  # noqa: E402
from patch.kv import parse_kv  # noqa: E402
from patch.meta import RELEASE_HISTORY  # noqa: E402

OUT = os.path.join(HERE, "data", "rules", "neutral_tier_times.json")
FIRST = "7.38"      # the tier system with enchantments


def _minutes(s):
    m, _, sec = str(s).partition(":")
    return int(m) + int(sec or 0) / 60.0


def tier_times(version):
    text = game_files.npc(version, "neutral_items.txt")
    if not text:
        return None
    root = parse_kv(text)
    tiers = root.get("neutral_items", root).get("neutral_tiers") or {}
    out = {t: round(_minutes(b["start_time"]), 2) for t, b in tiers.items()
           if t.isdigit() and isinstance(b, dict) and b.get("start_time")}
    return out or None


def main():
    if not game_files.available():
        sys.exit("game files are not available (DOTA_FILES_DIR)")
    order = [r["version"] for r in RELEASE_HISTORY][::-1]          # oldest first
    versions = order[order.index(FIRST):]
    data = {}
    for v in versions:
        t = tier_times(v)
        if t is None:
            raise ValueError(f"{v}: no neutral tier start times in neutral_items.txt")
        data[v] = t
    doc = ("Minute each neutral tier opens, per patch (neutral_items.txt start_time; tools/build_neutral_tier_times.py). "
           "Used by patch/enchant_gold.py to line enchantment values up by game minute.")
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"_doc": doc, "versions": data}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, OUT)
    print(f"{len(data)} patches -> {OUT}")


if __name__ == "__main__":
    main()
