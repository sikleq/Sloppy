# -*- coding: utf-8 -*-
r"""Re-extract data/stats/<version>/{items,heroes,units}.json from the per-patch KV history, where they differ.

Why (2026-09-27): fetch_stats takes the first d2vpkr commit dated on the patch day, which can predate the
patch, so several slim JSONs were copies of the previous patch: items.json 7.41 = 7.40c byte for byte (the
whole 7.41 item overhaul sat in 7.41a), 7.37e kept Khanda's 7.37d recipe (600, not 500); heroes.json 7.41
= 7.40c (78 heroes), 7.41b missed Alchemist's 22 -> 19 Agility, 7.39c Batrider's 1.75 -> 1.25 regen. The
per-patch KV history (the weights model's) is the authority; the extraction is fetch_stats' own (same shape
as tools/slim_from_kv.py). A version whose raw KV sits in data/stats/<v>/ (slim_from_kv's input, taken
from the live VPK) is left alone.

Usage:  python tools/resync_snapshots.py            # dry run: what would change
        python tools/resync_snapshots.py --write    # rewrite the stale files
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY = os.path.join(os.path.expanduser("~"), "outputs", "valve-revealed-weights-20260915")
FETCH_STATS = os.environ.get("SLOPPY_FETCH_STATS", r"D:\Sloppy Patches\fetch_stats.py")  # outside the repo
KINDS = (  # slim file, history folder, raw file, extractor name
    ("items.json", "items_history", "items.txt", "extract_items"),
    ("heroes.json", "heroes_history", "npc_heroes.txt", "extract_heroes"),
    # units_history: npc_units.txt of dotabuff/d2vpkr at the items history plan's commits (2026-09-27)
    ("units.json", "units_history", "npc_units.txt", "extract_units"),
)   # abilities.json is read by no page: not resynced

# d2vpkr has no commit between 7.41 and 7.41a (the history plan maps both to 62894e2, the 7.41a state), so the 7.41
# heroes come out with 7.41a's base stats: the 7.41 page said Lifestealer's damage is "now 23" (26) and the 7.41a
# page priced its -3 from 23 (audit 2026-10-03). Valve's 7.41a notes undo them: {version: {slim: {npc: {field}}}}.
LATER_STATE_UNDONE = {"7.41": {"heroes.json": {
    "npc_dota_hero_antimage": {"MovementSpeed": 310, "StatusHealthRegen": 1.0},
    "npc_dota_hero_morphling": {"AttributeAgilityGain": 3.9},
    "npc_dota_hero_windrunner": {"AttributeBaseAgility": 17},
    "npc_dota_hero_skeleton_king": {"AttackRate": 1.7, "AttributeIntelligenceGain": 1.6},
    "npc_dota_hero_leshrac": {"AttributeStrengthGain": 2.8},
    "npc_dota_hero_life_stealer": {"AttackDamageMin": 26, "AttackDamageMax": 32},
    "npc_dota_hero_doom_bringer": {"ArmorPhysical": 2},
    "npc_dota_hero_alchemist": {"MovementSpeed": 295},
    "npc_dota_hero_invoker": {"AttributeBaseIntelligence": 20},
    "npc_dota_hero_chaos_knight": {"AttackDamageMin": 29, "AttackDamageMax": 49},
    "npc_dota_hero_void_spirit": {"StatusManaRegen": 0.6},
}}}


def _undo_later_state(v, slim_name, truth):
    """truth with a later patch's values put back where the history file is that later patch's state."""
    fix = LATER_STATE_UNDONE.get(v, {}).get(slim_name, {})
    return {k: ({**row, **fix[k]} if k in fix else row) for k, row in truth.items()}


def stale_snapshots(fs):
    """[(version, slim file, items differing, extracted truth)] for every slim JSON that differs."""
    stats = os.path.join(HERE, "data", "stats")
    out = []
    for slim_name, hist, raw_name, fn in KINDS:
        for v in sorted(os.listdir(stats)):
            slim, raw = os.path.join(stats, v, slim_name), os.path.join(HISTORY, hist, v, raw_name)
            if not (os.path.exists(slim) and os.path.exists(raw)) or os.path.exists(os.path.join(stats, v, raw_name)):
                continue
            text = open(raw, encoding="utf-8", errors="replace").read()
            if "#base" in text:
                continue                                   # an include list (7.41f+): slim_from_kv's job
            truth = _undo_later_state(v, slim_name, getattr(fs, fn)(fs.parse_kv(text)))
            have = json.load(open(slim, encoding="utf-8"))
            if truth != have:
                out.append((v, slim_name, sum(1 for k in set(truth) | set(have) if truth.get(k) != have.get(k)), truth))
    return out


def load_fetch_stats():
    spec = importlib.util.spec_from_file_location("fetch_stats", FETCH_STATS)
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)
    return fs


def main(write):
    stale = stale_snapshots(load_fetch_stats())
    for v, slim_name, n, truth in stale:
        if write:
            with open(os.path.join(HERE, "data", "stats", v, slim_name), "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(truth, ensure_ascii=False, indent=2))
        print(f"  {v} {slim_name}: {n} entries {'rewritten' if write else 'differ'}")
    print(f"{len(stale)} snapshots {'rewritten' if write else 'to rewrite'}")


if __name__ == "__main__":
    main("--write" in sys.argv)
