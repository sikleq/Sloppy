"""What changed where on the map, per Terrain step, next to that patch's notes — to check the notes against the map
file and the pictures (the owner 2026-10-02: "check the changed terrain for other errors too, both what the patch
notes say and what actually changed").

Every change is placed by its nearest landmark ("Radiant bot T1, 450 S"): trees added/removed in clusters, camps
moved or resized boxes, tier changes, towers and the other point objects. With --pictures (sfm/final, the full
renders map_<sha8>_sfm_full.png) also the spots where the ground itself changed beyond render noise
(map_picture_diff.py).

    python scripts/gen/terrain_audit.py [PATCH ...] [--pictures DIR] > audit.txt
"""
import argparse
import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)
from builders import map_versions as mv  # noqa: E402
import builders.terrain as terrain  # noqa: E402

CLUSTER = 450             # units: trees closer than this are one cluster
POINTS = {"npc_dota_watch_tower": "outpost", "npc_dota_lantern": "watcher", "npc_dota_unit_twin_gate": "twin gate",
          "npc_dota_xp_fountain": "wisdom shrine", "npc_dota_lotus_pool": "lotus pool",
          "npc_dota_mango_tree": "lotus pool (old)", "dota_item_rune_spawner_bounty": "bounty rune",
          "dota_item_rune_spawner_powerup": "power rune", "dota_item_rune_spawner_xp": "wisdom rune",
          "npc_dota_roshan_spawner": "Roshan pit", "npc_dota_miniboss_spawner": "Tormentor",
          "npc_dota_barracks": "barracks", "npc_dota_fort": "ancient", "ent_dota_shop": "shop"}


def load(ver):
    with open(os.path.join(_ROOT, "data", "map", f"mapdata_{mv.code(ver)}.json"), encoding="utf-8") as f:
        return json.load(f)["data"]


def tower_name(t):
    x, y = t["x"], t["y"]
    team = "Radiant" if x + y < 0 else "Dire"
    d = x - y
    lane = "mid" if abs(d) < 2500 else ("top" if d < 0 else "bot")
    tier = t.get("subType", "tower?").replace("tower", "T")
    return f"{team} T4" if tier == "T4" else f"{team} {lane} {tier}"


def camp_name(c):
    tier = {"0": "small", "1": "medium", "2": "large", "3": "ancient"}.get(str(c.get("neutralType")), "?")
    side = "Dire" if "evil" in c["triggerName"] else "Radiant"
    return f"{side} {tier} camp {c['triggerName'].split('_')[-1]}"


def landmarks(d):
    out = [(t["x"], t["y"], tower_name(t)) for t in d["npc_dota_tower"]]
    out += [(c["x"], c["y"], camp_name(c)) for c in d["npc_dota_neutral_spawner"]]
    for key, label in POINTS.items():
        out += [(e["x"], e["y"], label) for e in d.get(key, [])]
    return out


def compass(dx, dy):
    if math.hypot(dx, dy) < 120:
        return "at"
    a = math.degrees(math.atan2(dy, dx)) % 360
    return ["E", "NE", "N", "NW", "W", "SW", "S", "SE"][int((a + 22.5) // 45) % 8]


def where(x, y, marks):
    lx, ly, name = min(marks, key=lambda m: (m[0] - x) ** 2 + (m[1] - y) ** 2)
    dist = math.hypot(x - lx, y - ly)
    return f"{name}, {dist:.0f} {compass(x - lx, y - ly)}" if dist >= 120 else f"at {name}"


def near(x, y, marks):
    w = where(x, y, marks)
    return w if w.startswith("at ") else f"near {w}"


def moved(dist, dx, dy):
    """'79 S' — a short move keeps its direction (compass() calls under 120 units 'at')."""
    a = math.degrees(math.atan2(dy, dx)) % 360
    return f"{dist:.0f} {['E', 'NE', 'N', 'NW', 'W', 'SW', 'S', 'SE'][int((a + 22.5) // 45) % 8]}"


def clusters(pts):
    pts, out = list(pts), []
    while pts:
        group = [pts.pop()]
        i = 0
        while i < len(group):
            gx, gy = group[i]
            near = [p for p in pts if (p[0] - gx) ** 2 + (p[1] - gy) ** 2 <= CLUSTER ** 2]
            for p in near:
                pts.remove(p)
            group += near
            i += 1
        out.append(group)
    return sorted(out, key=len, reverse=True)


def step_report(step, notes, pictures=None):
    a, b = load(step.old_pic), load(step.new_pic)
    marks = landmarks(b)
    lines = [f"===== {step.patch}  ({step.before} -> {step.patch})"]
    rows = notes.get(step.patch) or []
    lines.append("NOTES:" if rows else "NOTES: none")
    lines += [f"  [{tag}] {(sg + ': ') if sg else ''}{text}" + (f"  (note: {note})" if note else "")
              for text, tag, sg, note in rows]
    lines.append("MAP FILE:")
    ta = {(t["x"], t["y"]) for t in a["ent_dota_tree"]}
    tb = {(t["x"], t["y"]) for t in b["ent_dota_tree"]}
    for label, pts in (("trees added", tb - ta), ("trees removed", ta - tb)):
        for g in clusters(pts):
            cx, cy = sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g)
            lines.append(f"  {label}: {len(g)} {near(cx, cy, marks)}")
    ca = {c["triggerName"]: c for c in a["npc_dota_neutral_spawner"]}
    for c in b["npc_dota_neutral_spawner"]:
        o = ca.get(c["triggerName"])
        if not o:
            lines.append(f"  camp new: {camp_name(c)} {near(c['x'], c['y'], marks)}")
            continue
        dist = math.hypot(c["x"] - o["x"], c["y"] - o["y"])
        if dist:
            lines.append(f"  camp moved: {camp_name(c)} {moved(dist, c['x'] - o['x'], c['y'] - o['y'])}")
        if c.get("neutralType") != o.get("neutralType"):
            lines.append(f"  camp tier: {camp_name(o)} -> {camp_name(c)}")
    gone = set(ca) - {c["triggerName"] for c in b["npc_dota_neutral_spawner"]}
    lines += [f"  camp gone: {camp_name(ca[n])}" for n in sorted(gone)]
    ba = {t["name"]: t["points"] for t in a.get("trigger_multiple", [])}
    for t in b.get("trigger_multiple", []):
        o = ba.get(t["name"])
        if o is None or {(p["x"], p["y"]) for p in o} == {(p["x"], p["y"]) for p in t["points"]}:
            continue

        def size(ps):
            xs, ys = [p["x"] for p in ps], [p["y"] for p in ps]
            return max(xs) - min(xs), max(ys) - min(ys), (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        w0, h0, x0, y0 = size(o)
        w1, h1, x1, y1 = size(t["points"])
        cname = next((camp_name(c) for c in b["npc_dota_neutral_spawner"] if c["triggerName"] == t["name"]), t["name"])
        lines.append(f"  spawn box: {cname} {w0}x{h0} -> {w1}x{h1}, centre moved {math.hypot(x1 - x0, y1 - y0):.0f}")
    for t in b["npc_dota_tower"]:
        same = [o for o in a["npc_dota_tower"] if o.get("subType") == t.get("subType")]
        o = min(same, key=lambda o: (o["x"] - t["x"]) ** 2 + (o["y"] - t["y"]) ** 2)
        dist = math.hypot(t["x"] - o["x"], t["y"] - o["y"])
        if dist:
            lines.append(f"  tower moved: {tower_name(t)} {moved(dist, t['x'] - o['x'], t['y'] - o['y'])}")
    for key, label in POINTS.items():
        pa = {(e["x"], e["y"]) for e in a.get(key, [])}
        pb = {(e["x"], e["y"]) for e in b.get(key, [])}
        for x, y in sorted(pb - pa):
            if pa:
                ox, oy = min(pa, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
                if len(pa) == len(pb):
                    lines.append(f"  {label} moved: {moved(math.hypot(x - ox, y - oy), x - ox, y - oy)}, "
                                 f"now {near(x, y, marks)}")
                    continue
            lines.append(f"  {label} new: {where(x, y, marks)}")
        if len(pa) != len(pb):
            lines += [f"  {label} gone: was {where(x, y, landmarks(a))}" for x, y in sorted(pa - pb)]
    if pictures:
        lines += picture_lines(step, pictures, marks)
    return lines


def picture_lines(step, pictures, marks):
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    import map_picture_diff as mpd
    from render_map import world_rect
    pm = mv.load_patch_maps()

    def full(ver):
        path = os.path.join(pictures, f"map_{pm[ver][:8]}_sfm_full.png")
        return np.asarray(Image.open(path).convert("RGB")) if os.path.exists(path) else None
    a, b = full(step.old_pic), full(step.new_pic)
    if a is None or b is None:
        return ["PICTURES: not found"]
    x0, _x1, _yb, yt = world_rect()
    s = mpd.SCALE

    def small(arr):
        im = Image.fromarray(arr)
        return np.asarray(im.resize((im.width // s, im.height // s), Image.BOX), np.int16)
    d = np.abs(small(a) - small(b)).max(axis=2) > mpd.THRESHOLD
    d = ndimage.binary_opening(d, iterations=1)
    lab, n = ndimage.label(ndimage.binary_closing(d, iterations=2))
    out = ["PICTURES (ground changes bigger than render noise):"]
    for i, size in sorted(enumerate(np.bincount(lab.ravel())[1:], 1), key=lambda t: -t[1]):
        if size < mpd.NOISE_BLOB:
            break
        ys, xs = np.nonzero(lab == i)
        wx, wy = x0 + (xs.mean() + 0.5) * 2 * s, yt - (ys.mean() + 0.5) * 2 * s
        out.append(f"  {size} px {near(wx, wy, marks)} "
                   f"({(xs.max() - xs.min() + 1) * 2 * s} x {(ys.max() - ys.min() + 1) * 2 * s} units)")
    return out if len(out) > 1 else ["PICTURES: nothing but render noise"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("patches", nargs="*")
    ap.add_argument("--pictures", help="folder of the full renders map_<sha8>_sfm_full.png")
    args = ap.parse_args()
    notes = terrain._terrain_notes_by_patch()
    for step in mv.steps():
        if args.patches and step.patch not in args.patches:
            continue
        print("\n".join(step_report(step, notes, args.pictures)), flush=True)
        print()


if __name__ == "__main__":
    main()
