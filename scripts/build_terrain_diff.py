"""Compute the 7.40 -> 7.41 terrain diff -> data/terrain_diff.json.

Primary terrain-data sources:
  - Interactive map: https://tools.spectral.gg/interactive-map
  - Coords (GitHub):  leamare/dota-interactive-map
    (assets/data/<ver>/mapdata.json + root worlddata.json bounds)

Reads two `mapdata.json` exports from leamare/dota-interactive-map (cached
locally under .cache/leamare/mapdata_{740,741}.json — NOT committed; this is a
regeneration helper, like scripts/fetch_*.py) and emits a small, committed diff
the site build (build_terrain.py) projects onto the terrain map:

  - addedTrees / removedTrees : exact tree world coords that appeared / vanished
  - camps   : neutral camps moved / relocated / demoted (hard->medium)
  - towers  : towers repositioned
  - tormentors / twinGates / lotus : these objects' moves

World coords are kept as-is; build_terrain.py projects them with the leamare
worlddata bounds (worldMinX -10464 .. worldMaxX 10400, same Y), which line up
pixel-accurately with our cropped 1280x1280 map renders (verified by overlaying
all trees on the map image).

Refresh the cached inputs with::

    mkdir -p .cache/leamare
    for v in 740 741; do
      curl -s "https://raw.githubusercontent.com/leamare/dota-interactive-map/master/assets/data/$v/mapdata.json" \
        -o ".cache/leamare/mapdata_$v.json"
    done
    python scripts/build_terrain_diff.py
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_CACHE = os.path.join(_ROOT, ".cache", "leamare")
OUT = os.path.join(_ROOT, "data", "terrain_diff.json")

OLD_VER, NEW_VER = "740", "741"


def _load(ver):
    path = os.path.join(_CACHE, f"mapdata_{ver}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)["data"]


def _nearest(target, candidates):
    return min(candidates, key=lambda c: (c["x"] - target["x"]) ** 2
               + (c["y"] - target["y"]) ** 2)


def main():
    A = _load(OLD_VER)
    B = _load(NEW_VER)

    # ---- trees: exact coordinate set difference ----
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
        # A camp that vanished + a new camp nearby == a relocation.
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
            camps.append({"kind": "demoted", "label": "Hard camp → Medium camp",
                          "x": b["x"], "y": b["y"]})

    # ---- towers: match by subType, report moved ones ----
    towers = []
    old_t = {e["subType"]: e for e in A["npc_dota_tower"]}
    for e in B["npc_dota_tower"]:
        o = old_t.get(e["subType"])
        # subType isn't unique (4x tower1 etc.) — pair each NEW tower with the
        # nearest OLD tower of the same subType to detect the small shifts.
        same = [t for t in A["npc_dota_tower"] if t["subType"] == e["subType"]]
        if not same:
            continue
        o = _nearest(e, same)
        if (o["x"], o["y"]) != (e["x"], e["y"]):
            towers.append({"kind": "moved", "label": "Tower repositioned",
                           "x": e["x"], "y": e["y"], "ox": o["x"], "oy": o["y"]})

    def moves(cat, label):
        out = []
        for b in B[cat]:
            o = _nearest(b, A[cat])
            if (o["x"], o["y"]) != (b["x"], b["y"]):
                out.append({"kind": "moved", "label": label,
                            "x": b["x"], "y": b["y"], "ox": o["x"], "oy": o["y"]})
        return out

    # ---- FULL tree sets for both patches — the "Trees" overlay shows the 7.40
    # layout on the old side and the 7.41 layout on the new side, so sweeping
    # the slider reveals how the forest was rearranged. ----
    trees_old = sorted((t["x"], t["y"]) for t in A["ent_dota_tree"])
    trees_new = sorted((t["x"], t["y"]) for t in B["ent_dota_tree"])

    # ---- camps with tier (neutralType: 0=small 1=medium 2=large 3=ancient, per
    # leamare styleDefinitions.neutralCamp) for BOTH patches, so the "Camps"
    # overlay can split old/new by the slider (see what a camp became + where). ----
    def camp_list(src):
        return [{"x": e["x"], "y": e["y"], "tier": int(e.get("neutralType", 0))}
                for e in src]
    camps40 = camp_list(A["npc_dota_neutral_spawner"])
    camps41 = camp_list(B["npc_dota_neutral_spawner"])

    diff = {
        "oldVer": "7.40", "newVer": "7.41",
        "world": {"minX": -10464, "maxX": 10400, "minY": -10464, "maxY": 10400},
        "treesOld": [[x, y] for x, y in trees_old],
        "treesNew": [[x, y] for x, y in trees_new],
        "camps40": camps40,
        "camps41": camps41,
        # move data kept for reference (not drawn): camps/towers/objectives
        "camps": camps,
        "towers": towers,
        "tormentors": moves("npc_dota_miniboss_spawner", "Tormentor relocated"),
        "twinGates": moves("npc_dota_unit_twin_gate", "Twin Gate moved"),
        "lotus": moves("npc_dota_lotus_pool", "Lotus Pool moved"),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(diff, f, separators=(",", ":"))
    from collections import Counter
    tiers = Counter(c["tier"] for c in camps41)
    print(f"  -> {os.path.relpath(OUT, _ROOT)}: "
          f"trees {len(trees_old)}->{len(trees_new)} "
          f"({len(trees_new) - len(trees_old):+d}), "
          f"camps {len(camps40)}/{len(camps41)} tiers={dict(tiers)}, "
          f"{len(towers)} towers")


if __name__ == "__main__":
    main()
