"""Spots for the pictures of a patch's terrain rows, found from the map file (owner 2026-11-19, 7.42: "Moved small
flooded camps …", "Added some trees to the sides of Mid lane …" и др. — "показать визуальные изменения"; 3 of 13 rows
had pictures, the rest waited for spots written by hand).

For each Terrain row of the patch without an entry in data/terrain_spots.json: the changes of the row's object
(patch/terrain_notes.show_keys: camps, trees, towers, spawn boxes) that the map file of the patch has, kept to the
side and lane the row names (Radiant / Dire, mid / safelane / offlane, top / bottom), grouped by place; each group a
spot (its centre), the square wide enough for the group. A row whose words find no change gets none (a cliff, ground).

    python scripts/gen/terrain_spots_auto.py 7.42            # print the entries
    python scripts/gen/terrain_spots_auto.py 7.42 --write    # add them to data/terrain_spots.json
then scripts/gen/terrain_shots.py <patch> makes the pictures.
"""
import json
import math
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path[:0] = [_ROOT, _HERE]

SPOTS = os.path.join(_ROOT, "data", "terrain_spots.json")
GROUP = 1800            # changes this close are one picture
R_MIN, R_MAX = 900, 2600


def _side(x, y):
    return "dire" if x + y > 0 else "radiant"


def _lane(x, y):
    """mid only in the middle of the map (the bases sit on the same diagonal), else top / bot by the diagonal."""
    if abs(x - y) < 2500 and abs(x) < 5000 and abs(y) < 5000:
        return "mid"
    return "top" if x - y < 0 else "bot"


def _safelane(side, lane):
    return (side == "radiant" and lane == "bot") or (side == "dire" and lane == "top")


def wanted(text):
    """What the row names: sides, lanes, camp tiers, tower tiers, and whether trees were added / removed."""
    t = text.lower()
    want = {"sides": {s for s in ("radiant", "dire") if s in t}, "lanes": set(), "camp": set(), "tier": set(),
            "trees": None}
    if re.search(r"\bmid(?:lane| lane)?\b|\bmidlane\b", t):
        want["lanes"].add("mid")
    if "safelane" in t or "safe lane" in t:
        want["lanes"].add("safe")
    if "offlane" in t:
        want["lanes"].add("off")
    if re.search(r"\btop\b", t):
        want["lanes"].add("top")
    if re.search(r"\bbottom\b|\bbot\b", t):
        want["lanes"].add("bot")
    want["camp"] = {k for k in ("small", "medium", "large", "ancient") if re.search(rf"\b{k}\b", t)}
    want["tier"] = {f"T{n}" for n in re.findall(r"\btier (\d)\b", t)}
    if re.search(r"\b(?:added|more trees)\b", t):
        want["trees"] = "added"
    elif re.search(r"\b(?:removed|cleaned up)\b", t):
        want["trees"] = "removed"
    return want


def _fits(x, y, want):
    side, lane = _side(x, y), _lane(x, y)
    if want["sides"] and side not in want["sides"]:
        return False
    lanes = want["lanes"]
    if not lanes:
        return True
    if lane in lanes or ({"top", "bot"} <= lanes and lane in ("top", "bot")):
        return True
    return ("safe" in lanes and _safelane(side, lane)) or ("off" in lanes and lane != "mid" and not _safelane(side, lane))


def changes(old, new, keys, want):
    """[(x, y)] of the changes of the row's kind of object between two map files (scripts/gen/terrain_audit.load)."""
    import terrain_audit as ta
    pts = []
    if "spawnboxes" in keys:
        ob = {t["name"]: t["points"] for t in old.get("trigger_multiple", [])}
        for t in new.get("trigger_multiple", []):
            o = ob.get(t["name"])
            if o is None or {(p["x"], p["y"]) for p in o} == {(p["x"], p["y"]) for p in t["points"]}:
                continue
            camp = next((c for c in new["npc_dota_neutral_spawner"] if c["triggerName"] == t["name"]), None)
            if camp and want["camp"] and ta.camp_name(camp).split()[1] not in want["camp"]:
                continue
            if camp and abs(math.dist(*[(sum(p["x"] for p in ps) / len(ps), sum(p["y"] for p in ps) / len(ps))
                                       for ps in (o, t["points"])])) > 400:
                continue                              # a box that moved with its camp: the camp row's, not this one
            pts.append((sum(p["x"] for p in t["points"]) / len(t["points"]),
                        sum(p["y"] for p in t["points"]) / len(t["points"])))
        return pts
    if "camps" in keys:
        oc = {c["triggerName"]: c for c in old["npc_dota_neutral_spawner"]}
        for c in new["npc_dota_neutral_spawner"]:
            o = oc.get(c["triggerName"])
            if not o or math.dist((o["x"], o["y"]), (c["x"], c["y"])) < 120:
                continue
            if want["camp"] and ta.camp_name(o).split()[1] not in want["camp"]:
                continue
            pts += [(c["x"], c["y"]), (o["x"], o["y"])]
    if "trees" in keys:
        a = {(t["x"], t["y"]) for t in old["ent_dota_tree"]}
        b = {(t["x"], t["y"]) for t in new["ent_dota_tree"]}
        pts += sorted(b - a if want["trees"] == "added" else a - b if want["trees"] == "removed" else a ^ b)
    if "towers" in keys:
        for t in new["npc_dota_tower"]:
            same = [o for o in old["npc_dota_tower"] if o.get("subType") == t.get("subType")]
            o = min(same, key=lambda o: (o["x"] - t["x"]) ** 2 + (o["y"] - t["y"]) ** 2)
            if math.dist((o["x"], o["y"]), (t["x"], t["y"])) < 1:
                continue
            if want["tier"] and ta.tower_name(t).split()[-1] not in want["tier"]:
                continue
            pts.append((t["x"], t["y"]))
    return pts


def groups(pts, near=GROUP):
    out = []
    for p in pts:
        g = next((g for g in out if any(math.dist(p, q) <= near for q in g)), None)
        (g.append(p) if g else out.append([p]))
    return out


def spot_entries(rows, old, new, have):
    """New terrain_spots entries for the rows (texts) that have none yet."""
    from patch.terrain_notes import note_phrase, show_keys
    out = []
    for text in rows:
        if any(text.startswith(h) for h in have):
            continue
        keys = {"spawnboxes"} if re.search(r"\bspawn ?box", text, re.I) else show_keys(text)
        want = wanted(text)
        pts = [p for p in changes(old, new, keys, want) if _fits(*p, want)]
        if not pts:
            continue
        spots, r = [], R_MIN
        # a camp's old and new places are one picture (they lie up to ~2500 apart); a second picture only for the
        # other side of the map, when the row names no side (7.42 "… top/bottom rims")
        found = sorted(groups(pts, 3000 if "camps" in keys else GROUP), key=len, reverse=True)
        pick = found[:1]
        if found and not want["sides"]:
            pick += [g for g in found[1:] if _side(*g[0]) != _side(*found[0][0])][:1]
        for g in pick:
            cx, cy = sum(x for x, _ in g) / len(g), sum(y for _, y in g) / len(g)
            spread = max(math.dist((cx, cy), p) for p in g)
            r = min(R_MAX, max(r, int(spread * 1.25) + 300))
            spots.append([round(cx), round(cy)])
        entry = {"match": " ".join(text.split()[:9]), "spots": spots, "r": r}
        if keys == {"spawnboxes"}:
            entry["show"] = ["camps"]
        phrase = note_phrase(text)
        if phrase:
            entry["phrase"] = phrase
        out.append(entry)
    return out


def patch_rows(patch):
    from patch import terrain_index
    return [text for text, _tag, _sg, _note in terrain_index._terrain_notes_by_patch().get(patch, [])]


def main(args):
    import terrain_audit as ta
    from patch import map_versions as mv
    patch = args[0]
    step = next(st for st in mv.steps() if st.patch == patch)
    old, new = ta.load(step.old_pic), ta.load(step.new_pic)
    with open(SPOTS, encoding="utf-8") as f:
        spots = json.load(f)
    have = [e["match"] for e in spots.get(patch, [])]
    found = spot_entries(patch_rows(patch), old, new, have)
    for e in found:
        print(json.dumps(e, ensure_ascii=False))
    if "--write" in args and found:
        spots.setdefault(patch, []).extend(found)
        tmp = SPOTS + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(spots, ensure_ascii=False, indent=2) + "\n")
        os.replace(tmp, SPOTS)


if __name__ == "__main__":
    main(sys.argv[1:])
