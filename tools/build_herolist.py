"""data/herolist.json from the game files of the newest snapshot (the shape of Valve's datafeed herolist).

Until 2026-10-21 the file had no writer (a one-off copy of dota2.com/datafeed/herolist), so a new hero reached
it only by hand. This rebuilds it offline from

  data/stats/<latest>/heroes/npc_dota_hero_*.txt   HeroID, AttributePrimary, Complexity (7.41f+ per-hero files)
  data/stats/<latest>/npc_heroes.txt               the same fields for snapshots before 7.41f
  data/abilities_english.txt                       "npc_dota_hero_<x>:n" = the hero's English name

{"result": {"data": {"heroes": [{id, name, name_loc, name_english_loc, primary_attr, complexity}, ...]}}},
in the game's hero order (npc_heroes.txt), only heroes with `"Enabled" "1"` (no npc_dota_hero_base, no
target_dummy) — exactly what the datafeed lists (checked 2026-10-21: the 7.41f rebuild equals the old copy).

    python tools/build_herolist.py            # write data/herolist.json
    python tools/build_herolist.py --check    # exit 1 when it is stale (what would change is printed)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "data", "herolist.json")
PRIMARY = {"DOTA_ATTRIBUTE_STRENGTH": 0, "DOTA_ATTRIBUTE_AGILITY": 1, "DOTA_ATTRIBUTE_INTELLECT": 2,
           "DOTA_ATTRIBUTE_ALL": 3}


def hero_blocks(stats_dir):
    """{npc_dota_hero_x: KV block} of a snapshot, #base includes followed (slim_from_kv.load_kv)."""
    from tools.slim_from_kv import load_kv
    kv = load_kv(os.path.join(stats_dir, "npc_heroes.txt"))
    root = next(iter(kv.values()), {}) if kv else {}
    return {k: v for k, v in root.items() if k.startswith("npc_dota_hero_") and isinstance(v, dict)}


def build(stats_dir, loc):
    """The herolist table of a snapshot. `loc` is build_abilities_slim.load_loc() (lower-case keys)."""
    heroes = []
    for name, block in hero_blocks(stats_dir).items():
        hero_id = str(block.get("HeroID", "")).strip()
        title = loc.get(f"{name}:n")
        if str(block.get("Enabled", "")).strip() != "1" or not hero_id.isdigit() or title is None:
            continue
        heroes.append({"id": int(hero_id), "name": name, "name_loc": title, "name_english_loc": title,
                       "primary_attr": PRIMARY.get(str(block.get("AttributePrimary", "")).strip(), 0),
                       "complexity": int(str(block.get("Complexity", "1")).strip() or 1)})
    return {"result": {"data": {"heroes": heroes}}}


def changes(current, new):
    """[(hero name, old row or None, new row or None)]."""
    old = {h["name"]: h for h in current["result"]["data"]["heroes"]}
    fresh = {h["name"]: h for h in new["result"]["data"]["heroes"]}
    return [(n, old.get(n), fresh.get(n)) for n in sorted(set(old) | set(fresh)) if old.get(n) != fresh.get(n)]


def dumps(table):
    """The file's own layout: indent 0 (one key per line), as the datafeed copy was saved."""
    return json.dumps(table, ensure_ascii=False, indent=0)


def main(argv):
    from patch.meta import latest_stats_version
    from tools.build_abilities_slim import load_loc
    check = "--check" in argv
    ver = latest_stats_version()
    with open(OUT, encoding="utf-8") as f:
        current = json.load(f)
    new = build(os.path.join(ROOT, "data", "stats", ver), load_loc())
    diff = changes(current, new)
    for name, old, fresh in diff:
        print(f"  {name}: {old} -> {fresh}")
    print(f"herolist.json vs data/stats/{ver}: {len(diff)} hero(es) {'would change' if check else 'changed'}")
    if check:
        return 1 if diff else 0
    if diff:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(dumps(new))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
