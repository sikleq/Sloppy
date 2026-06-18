"""Compute per-patch terrain diffs -> data/terrain_diff_<newVer>.json.

Primary terrain-data sources:
  - Interactive map: https://tools.spectral.gg/interactive-map
  - Coords (GitHub):  leamare/dota-interactive-map
    (assets/data/<ver>/mapdata.json + root worlddata.json bounds)

For each old->new patch pair we read the two `mapdata.json` exports from
leamare/dota-interactive-map (cached under .cache/leamare/mapdata_<code>.json —
NOT committed; this is a regeneration helper, like scripts/fetch_*.py) and emit a
small, committed diff per NEW patch that the site build (builders/terrain.py)
projects onto that patch's terrain map:

  - treesOld / treesNew     : full tree coord sets (forest layout each side)
  - campsOld / campsNew      : neutral camps with tier (split old/new by slider)
  - entities                 : full old+new sets per point-entity layer
                               (towers / lotus / gates / tormentors / runes /
                               wisdom / outposts / watchers / roshan)
  - camps / towers / …       : move/relocate/demote records (kept for reference)

World coords are kept as-is; builders/terrain.py projects them with the shared crop
meta (data/terrain_map_meta.json), which lines up pixel-accurately with our
cropped map renders (verified by overlaying all trees on the map image). The crop
box is shared across every version, so the same projector places any patch's
markers correctly.

Refresh the cached inputs + rebuild ALL pairs with::

    mkdir -p .cache/leamare
    for v in 739 740 741; do
      curl -s "https://raw.githubusercontent.com/leamare/dota-interactive-map/master/assets/data/$v/mapdata.json" \
        -o ".cache/leamare/mapdata_$v.json"
    done
    python scripts/gen/build_terrain_diff.py            # default pairs below
    python scripts/gen/build_terrain_diff.py 739:740    # or a single pair
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_CACHE = os.path.join(_ROOT, ".cache", "leamare")

# old_code -> new_code pairs. Each NEW patch gets its own diff file. Codes are the
# leamare/tile-server form (no dot); the diff is keyed by the dotted NEW version.
DEFAULT_PAIRS = [("739", "740"), ("740", "741")]

# Point-entity layers (full old+new sets → toggleable slider-split map layers).
# leamare keys (layerDefinitions.js): Outpost == npc_dota_watch_tower (2),
# Watcher == npc_dota_lantern (10) — SEPARATE layers.
_ENTITY_KEYS = {
    "towers": "npc_dota_tower",
    "lotus": "npc_dota_lotus_pool",
    "twinGates": "npc_dota_unit_twin_gate",
    "tormentors": "npc_dota_miniboss_spawner",
    "bounty": "dota_item_rune_spawner_bounty",
    "power": "dota_item_rune_spawner_powerup",
    "wisdom": "npc_dota_xp_fountain",       # Shrine of Wisdom
    "outposts": "npc_dota_watch_tower",
    "watchers": "npc_dota_lantern",
    "roshan": "npc_dota_roshan_spawner",
}


def _dotted(code):
    """'740' -> '7.40' (insert the dot after the major '7')."""
    return code if "." in code else f"{code[0]}.{code[1:]}"


def _load(code):
    path = os.path.join(_CACHE, f"mapdata_{code}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)["data"]


def _nearest(target, candidates):
    return min(candidates, key=lambda c: (c["x"] - target["x"]) ** 2
               + (c["y"] - target["y"]) ** 2)


def _diff_pair(old_code, new_code):
    A = _load(old_code)
    B = _load(new_code)

    # ---- trees: exact coordinate set difference (move records, not drawn) ----
    ta = {(t["x"], t["y"]) for t in A["ent_dota_tree"]}
    tb = {(t["x"], t["y"]) for t in B["ent_dota_tree"]}
    added_trees = sorted(tb - ta)
    removed_trees = sorted(ta - tb)

    # ---- neutral camps: match by triggerName ----
    ca = {e["triggerName"]: e for e in A["npc_dota_neutral_spawner"]}
    cb = {e["triggerName"]: e for e in B["npc_dota_neutral_spawner"]}
    camps = []
    rem = [ca[n] for n in ca if n not in cb]
    add = [cb[n] for n in cb if n not in ca]
    used_add = set()
    for a in rem:
        pool = [c for i, c in enumerate(add) if i not in used_add]
        if pool:
            b = _nearest(a, pool)
            used_add.add(add.index(b))
            camps.append({"kind": "relocated", "label": "Neutral camp relocated",
                          "x": b["x"], "y": b["y"], "ox": a["x"], "oy": a["y"]})
    for n in ca:
        if n not in cb:
            continue
        a, b = ca[n], cb[n]
        if (a["x"], a["y"]) != (b["x"], b["y"]):
            camps.append({"kind": "moved", "label": "Neutral camp moved",
                          "x": b["x"], "y": b["y"], "ox": a["x"], "oy": a["y"]})
        if a.get("neutralType") != b.get("neutralType"):
            camps.append({"kind": "demoted", "label": "Camp tier changed",
                          "x": b["x"], "y": b["y"]})

    # ---- towers: pair each NEW tower with the nearest OLD of same subType ----
    towers = []
    for e in B["npc_dota_tower"]:
        same = [t for t in A["npc_dota_tower"] if t["subType"] == e["subType"]]
        if not same:
            continue
        o = _nearest(e, same)
        if (o["x"], o["y"]) != (e["x"], e["y"]):
            towers.append({"kind": "moved", "label": "Tower repositioned",
                           "x": e["x"], "y": e["y"], "ox": o["x"], "oy": o["y"]})

    def moves(cat, label):
        out = []
        for b in B.get(cat, []):
            if not A.get(cat):
                continue
            o = _nearest(b, A[cat])
            if (o["x"], o["y"]) != (b["x"], b["y"]):
                out.append({"kind": "moved", "label": label,
                            "x": b["x"], "y": b["y"], "ox": o["x"], "oy": o["y"]})
        return out

    # ---- FULL tree sets each side (the "Trees" overlay shows the old layout on
    # the old side, new on the new side; sweep reveals the rearrangement). ----
    trees_old = sorted((t["x"], t["y"]) for t in A["ent_dota_tree"])
    trees_new = sorted((t["x"], t["y"]) for t in B["ent_dota_tree"])

    # ---- camps with tier (0=small 1=medium 2=large 3=ancient) both sides ----
    def camp_list(src):
        return [{"x": e["x"], "y": e["y"], "tier": int(e.get("neutralType", 0))}
                for e in src]
    camps_old = camp_list(A["npc_dota_neutral_spawner"])
    camps_new = camp_list(B["npc_dota_neutral_spawner"])

    def coords(src, key):
        return [[e["x"], e["y"]] for e in src.get(key, [])]
    entities = {name: {"old": coords(A, key), "new": coords(B, key)}
                for name, key in _ENTITY_KEYS.items()}

    return {
        "oldVer": _dotted(old_code), "newVer": _dotted(new_code),
        "world": {"minX": -10464, "maxX": 10400, "minY": -10464, "maxY": 10400},
        "treesOld": [[x, y] for x, y in trees_old],
        "treesNew": [[x, y] for x, y in trees_new],
        "campsOld": camps_old,
        "campsNew": camps_new,
        # toggleable point-entity layers (full old+new sets, split by slider)
        "entities": entities,
        # move data kept for reference (not drawn)
        "camps": camps,
        "towers": towers,
        "tormentors": moves("npc_dota_miniboss_spawner", "Tormentor relocated"),
        "twinGates": moves("npc_dota_unit_twin_gate", "Twin Gate moved"),
        "lotus": moves("npc_dota_lotus_pool", "Lotus Pool moved"),
    }


def main(pairs):
    from collections import Counter
    for old_code, new_code in pairs:
        diff = _diff_pair(old_code, new_code)
        out = os.path.join(_ROOT, "data", f"terrain_diff_{diff['newVer']}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(diff, f, separators=(",", ":"))
        tiers = Counter(c["tier"] for c in diff["campsNew"])
        ent_summary = ", ".join(f"{k} {len(v['new'])}"
                                for k, v in diff["entities"].items())
        print(f"  -> {os.path.relpath(out, _ROOT)}: "
              f"{diff['oldVer']}->{diff['newVer']}  "
              f"trees {len(diff['treesOld'])}->{len(diff['treesNew'])} "
              f"({len(diff['treesNew']) - len(diff['treesOld']):+d}), "
              f"camps {len(diff['campsOld'])}/{len(diff['campsNew'])} "
              f"tiers={dict(tiers)}, {len(diff['towers'])} towers\n"
              f"     entities: {ent_summary}")


def _parse_args(argv):
    pairs = []
    for a in argv:
        if ":" in a:
            o, n = a.split(":", 1)
            pairs.append((o.replace(".", ""), n.replace(".", "")))
    return pairs or DEFAULT_PAIRS


if __name__ == "__main__":
    main(_parse_args(sys.argv[1:]))
