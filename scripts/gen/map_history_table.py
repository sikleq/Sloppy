"""data/map/map_history.json — the map history 7.08 → now for the Terrain Stats page (builders/terrain_stats.py),
from Oldgrowth's versions.json (the owner 2026-10-04: "add the table somewhere, carefully, not breaking the Terrain
page — a sub-tab of Terrain, Terrain Stats, with more info"). The site build can't reach the Oldgrowth folder, so
the numbers are copied here, compact; rerun after Oldgrowth gains a patch:

    python scripts/gen/map_history_table.py [path/to/Oldgrowth/versions.json]
"""
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\sikle\Documents\Oldgrowth\versions.json"
OUT = os.path.join(_ROOT, "data", "map", "map_history.json")


def counts(c):
    """The objects a reader cares about, under plain names. Lotus pools were 'mango trees' and wisdom shrines rune
    spawners before 7.38 (the map file's own classes)."""
    tiers = c.get("camps_by_type") or {}
    return {
        "trees": c.get("ent_dota_tree", 0),
        "camps": c.get("npc_dota_neutral_spawner", 0),
        "camp_tiers": [tiers.get(str(t), 0) for t in range(4)],          # small, medium, large, ancient
        "towers": c.get("npc_dota_tower", 0),
        "outposts": c.get("npc_dota_watch_tower", 0),
        "watchers": c.get("npc_dota_lantern", 0),
        "lotus": c.get("npc_dota_lotus_pool", 0) or c.get("npc_dota_mango_tree", 0),
        "wisdom": c.get("npc_dota_xp_fountain", 0) or c.get("dota_item_rune_spawner_xp", 0),
        "gates": c.get("npc_dota_unit_twin_gate", 0),
        "bounty": c.get("dota_item_rune_spawner_bounty", 0),
        "power": c.get("dota_item_rune_spawner_powerup", 0),
        "shrines": c.get("npc_dota_healer", 0),
        "roshan": c.get("npc_dota_roshan_spawner", 0),
        "tormentors": c.get("npc_dota_miniboss_spawner", 0),
    }


# the names builders/terrain._moved_summary writes -> the keys above ("camp tiers" / "camp spawn boxes" have no count)
_NAMES = {"trees": "trees", "camps": "camps", "camp tiers": "camp_tiers", "camp spawn boxes": "boxes",
          "towers": "towers", "lotus pools": "lotus", "twin gates": "gates", "Tormentors": "tormentors",
          "bounty runes": "bounty", "power runes": "power", "wisdom shrines": "wisdom", "wisdom runes": "wisdom",
          "outposts": "outposts", "watchers": "watchers", "Roshan pits": "roshan", "shrines": "shrines"}
_DELTA_RE = re.compile(r"^(.+?) \+(\d+) [−-](\d+)$")
_COUNT_RE = re.compile(r"^(.+?) (moved|changed|re-tiered|resized): (\d+)$")


def moves(changes):
    """'trees +324 −304; camps moved: 7; camp tiers changed: 2' -> {"trees": {"add": 324, "rem": 304},
    "camps": {"moved": 7}, "camp_tiers": {"changed": 2}} (the owner 2026-10-04: "what moved shows like the removed
    / added, in yellow" — instead of a sentence per row)."""
    out = {}
    for seg in (changes or "").split("; "):
        m = _DELTA_RE.match(seg)
        if m and m.group(1) in _NAMES:
            e = out.setdefault(_NAMES[m.group(1)], {})
            e["add"], e["rem"] = e.get("add", 0) + int(m.group(2)), e.get("rem", 0) + int(m.group(3))
            continue
        m = _COUNT_RE.match(seg)
        if m and m.group(1) in _NAMES:
            kind = "moved" if m.group(2) == "moved" else "changed"
            e = out.setdefault(_NAMES[m.group(1)], {})
            e[kind] = e.get(kind, 0) + int(m.group(3))
    return out


def main():
    with open(SRC, encoding="utf-8") as f:
        rows = json.load(f)
    out = []
    for r in rows:
        e = {"patch": r["patch"], "date": r.get("date", ""), "sha8": r["map_sha1"][:8]}
        if r.get("same_as"):
            e["same_as"] = r["same_as"]
        else:
            e["changes"] = r.get("changes", "")
            e["n"] = counts(r.get("counts") or {})
            e["moves"] = moves(e["changes"])
        out.append(e)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"_about": "Map history for Terrain Stats, from Oldgrowth versions.json "
                             "(scripts/gen/map_history_table.py). A patch with 'same_as' shipped that patch's map "
                             "file unchanged.", "patches": out}, f, ensure_ascii=False, indent=0)
        f.write("\n")
    print(len(out), "patches,", sum(1 for e in out if "n" in e), "map files ->", os.path.relpath(OUT, _ROOT))


if __name__ == "__main__":
    main()
