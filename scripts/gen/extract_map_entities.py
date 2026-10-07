"""Map entities (trees, camps, towers, runes, Roshan, Tormentors …) straight from the game's own map files ->
data/map/mapdata_<code>.json — our own source for the Terrain pages, independent of third-party repos.

The shape is the one of leamare/dota-interactive-map's mapdata.json ("data": {classname: [{x, y, …}]}), so
scripts/gen/build_terrain_diff.py reads either. Checked against it: 7.41 = 2475 trees, 28 camps (tests).

How it works (no game running, no downloads): Source2Viewer-CLI decompiles the map VPK's entity lumps
(maps/dota/entities/*.vents_c; default_ents + the *_base world layers, never *_destruction — those are the trees
that grow back / the destroyed state) and every camp volume's hull model (its m_Bounds + the entity's origin give
the camp box). The game install carries the current map (dota.vpk) and legacy snapshots of older maps
(dota_683.vpk … dota_737.vpk, kept for old replays).

    set S2V_CLI=C:\\path\\to\\Source2Viewer-CLI.exe
    python scripts/gen/extract_map_entities.py                 # every map below
    python scripts/gen/extract_map_entities.py 741 737         # some
    python scripts/gen/extract_map_entities.py --vpk X.vpk 740 # a map VPK taken from an old build
"""
import argparse
import json
import math
import os
import re
import struct
import subprocess
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(_ROOT, "data", "map")
MAPS_DIR = os.environ.get("DOTA_MAPS",
                          r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota\maps")
# code (patch without the dot) -> the VPK in the game's maps folder. The legacy files are named after the last
# patch that map was used in; the current dota.vpk is the live map (7.41 terrain, unchanged in 7.41a-f).
MAPS = {"683": "dota_683.vpk", "685": "dota_685.vpk", "688": "dota_688.vpk", "706": "dota_706.vpk",
        "719": "dota_719.vpk", "722": "dota_722.vpk", "728": "dota_728.vpk", "732": "dota_732.vpk",
        "737": "dota_737.vpk", "741": "dota.vpk"}

# classname -> the same key in the output (leamare's), plus what else a record carries
_POINTS = ("ent_dota_tree", "ent_dota_fountain", "ent_dota_shop", "npc_dota_fort", "npc_dota_watch_tower",
           "npc_dota_lantern", "npc_dota_unit_twin_gate", "npc_dota_xp_fountain", "npc_dota_lotus_pool",
           "npc_dota_mango_tree", "npc_dota_healer", "dota_item_rune_spawner_bounty",
           "dota_item_rune_spawner_powerup", "dota_item_rune_spawner_xp")


def _cli():
    path = os.environ.get("S2V_CLI", "")
    if not path or not os.path.exists(path):
        sys.exit("Set S2V_CLI to Source2Viewer-CLI.exe (https://github.com/ValveResourceFormat/ValveResourceFormat)")
    return path


def _run(*args):
    out = subprocess.run([_cli(), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode:
        raise RuntimeError(f"Source2Viewer-CLI {' '.join(args)}: {out.stderr or out.stdout}")
    return out.stdout


def _value(raw):
    raw = raw.strip()
    if raw.startswith("["):
        return [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?", raw)]
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw.startswith("resource_name:"):
        return raw.split(":", 1)[1].strip('"')
    return raw


def parse_vents(text):
    """[{key: value}] of one decompiled entity lump ("====N====" blocks of "key value" lines). A value opened by
    three quotes runs over several lines up to the closing three quotes (the river currents' "pathnodes": a list
    of spline nodes) and becomes the list of every number in it."""
    ents, cur, multi = [], None, None
    for line in text.splitlines():
        if multi is not None:
            key, buf = multi
            if line.strip() == '"""':
                cur[key] = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?", "\n".join(buf))]
                multi = None
            else:
                buf.append(line)
            continue
        if re.match(r"^====\d+====$", line):
            cur = {}
            ents.append(cur)
        elif cur is not None and line.strip():
            m = re.match(r"^(\S+)\s+(.*)$", line)
            if m:
                if m.group(2).strip() == '"""':
                    multi = (m.group(1), [])
                else:
                    cur[m.group(1)] = _value(m.group(2))
    return ents


def _vec(v):
    """[x, y, z]: newer lumps write "[ 1.0, 2.0, 3.0 ]", the legacy maps a string "1 2 3"."""
    if isinstance(v, str):
        v = [float(x) for x in v.split()]
    return list(v or []) + [0.0] * (3 - len(v or []))


def _xy(e):
    o = _vec(e.get("origin"))           # whole units: a 0.12 difference must not read as "camp moved" in a diff
    return {"x": int(round(o[0])), "y": int(round(o[1]))}


def _name(e):
    return re.sub(r"^\[PR#\]", "", str(e.get("targetname") or e.get("volumename") or ""))


def _box(e, bounds):
    """The camp volume's four corners on the ground: its hull bounds around the entity, turned by its yaw."""
    (x0, y0), (x1, y1) = bounds
    o, yaw = _vec(e.get("origin")), math.radians(_vec(e.get("angles"))[1])
    c, s = math.cos(yaw), math.sin(yaw)
    pts = []
    for x, y in ((x0, y0), (x0, y1), (x1, y1), (x1, y0)):
        pts.append({"x": int(round(o[0] + x * c - y * s)), "y": int(round(o[1] + x * s + y * c))})
    return pts


_NUM = r"(-?\d+(?:\.\d+)?(?:e[-+]?\d+)?)"


def hull_vertices(dump):
    """[[(x, y), …] per hull] of a hull model's `Source2Viewer-CLI -a` text. Since 7.35c the points are float32 x/y/z
    in m_VertexPositions (hex bytes; m_Vertices then holds indices); in older .vphys_c they are hex in m_Vertices, and
    in the oldest maps (before 7.32e) m_Vertices is a text list of [ x, y, z ]."""
    out = []
    blocks = re.findall(r"m_VertexPositions = \s*#\[(.*?)\]", dump, re.S) or \
        re.findall(r"m_Vertices = \s*#\[(.*?)\]", dump, re.S)
    for block in blocks:
        raw = bytes.fromhex("".join(block.split()))
        if len(raw) >= 36 and not len(raw) % 12:
            out.append([struct.unpack_from("<3f", raw, i)[:2] for i in range(0, len(raw), 12)])
    if not out:
        for block in re.findall(r"m_Vertices = \s*\[\s*(\[.*?\],)\s*\]", dump, re.S):
            pts = [(float(x), float(y)) for x, y, _z in re.findall(rf"\[ {_NUM}, {_NUM}, {_NUM} \]", block)]
            if len(pts) >= 3:
                out.append(pts)
    return out


def convex(points):
    """The convex hull of (x, y) points (monotone chain), counter-clockwise."""
    pts = sorted({(round(x, 2), round(y, 2)) for x, y in points})
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _hull_bounds(vpk, models, tmp, polys=None):
    """{model path: ((minx, miny), (maxx, maxy))} of the volumes' hull models; with `polys` (a dict) it also gets
    {model path: [[(x, y), …] per hull]} — the hulls' real footprints (convex, in the model's frame)."""
    out = {}
    if not models:
        return out
    folder = os.path.join(tmp, "hulls")
    _run("-i", vpk, "-f", "maps/", "-e", "vmdl_c,vphys_c", "-o", folder)
    for model in models:
        # the hull sits in the model itself, or (legacy maps) in the .vphys_c next to it
        for path in (os.path.join(folder, *(model + "_c").split("/")),
                     os.path.join(folder, *(model[:-5] + ".vphys_c").split("/"))):
            if not os.path.exists(path):
                continue
            dump = _run("-i", path, "-a")
            # a volume can be several hulls (7.06 neutralcamp_good_5): the box around all of them
            mns = re.findall(r"m_vMinBounds = \[ (\S+), (\S+),", dump)
            mxs = re.findall(r"m_vMaxBounds = \[ (\S+), (\S+),", dump)
            if mns and mxs:
                out[model] = ((min(float(x) for x, _ in mns), min(float(y) for _, y in mns)),
                              (max(float(x) for x, _ in mxs), max(float(y) for _, y in mxs)))
                if polys is not None:
                    polys[model] = [convex(h) for h in hull_vertices(dump)]
                break
    return out


def _zone_shapes(e, bounds, polys):
    """A zone volume's outlines on the ground: each hull's real footprint turned by the entity's yaw (2026-10-07: the
    7.41 secret shop is an octagon of radius 640 — the box around it reached 905 units out, and a hero standing in
    its drawn corner could not buy; the Roshan pits' no-ward zones are 7-gons). The box when no vertices are read."""
    model = _model(e)
    hulls = [h for h in (polys or {}).get(model, []) if len(h) >= 3]
    if not hulls:
        return [_box(e, bounds[model])]
    o, yaw = _vec(e.get("origin")), math.radians(_vec(e.get("angles"))[1])
    c, s = math.cos(yaw), math.sin(yaw)
    return [[{"x": int(round(o[0] + x * c - y * s)), "y": int(round(o[1] + x * s + y * c))} for x, y in h]
            for h in hulls]


def _model(e):
    """The volume's model path, "/" separated and without the compiled "_c" (legacy maps write "maps\\\\dota\\\\…")."""
    return re.sub(r"[\\/]+", "/", str(e.get("model", ""))).replace(".vmdl_c", ".vmdl")


def _sub(unit, pattern):
    m = re.search(pattern, unit or "")
    return m.group(1) if m else ""


# Map layers of 2026-10-06 (owner: "все слои"): lane creep paths, river currents, zones, spawn points.
# Zones are brush volumes like the camp boxes (hull bounds around the entity, turned by its yaw).
_ZONES = ("trigger_no_wards", "trigger_shop", "trigger_boss_attackable")
_SPAWNER_RE = re.compile(r"npc_dota_spawner_(good|bad)_(top|mid|bot)")


def _current(e):
    """A river current: its spline nodes in world units (node = position, in- and out-tangent, 3 numbers each,
    relative to the entity), and each node's width scale."""
    o, raw = _vec(e.get("origin")), e.get("pathnodes") or []
    # the nodes are in the entity's own frame: turned by its yaw (the two Dire currents of 7.41 are at 180°, drawn
    # mirrored off the water until 2026-10-06 — the owner: "Слой течений воды неправильный")
    yaw = math.radians(_vec(e.get("angles"))[1])
    c, s = math.cos(yaw), math.sin(yaw)

    def turn(x, y):
        return x * c - y * s, x * s + y * c
    nodes = []
    for i in range(0, len(raw) - 8, 9):
        x, y = turn(raw[i], raw[i + 1])
        ix, iy = turn(raw[i + 3], raw[i + 4])
        ox, oy = turn(raw[i + 6], raw[i + 7])
        nodes.append({"x": int(round(x + o[0])), "y": int(round(y + o[1])),
                      "in": [int(round(ix)), int(round(iy))], "out": [int(round(ox)), int(round(oy))]})
    # each node's radius in world units (where the current acts: the buff zone matches the water's banks on the
    # renders) and its strength (1 moderate, 2 strong — 7.38: "up to 100 / up to 150 bonus movement speed")
    scales = e.get("pathnoderadiusscales") or []
    types = e.get("pathnodemovespeedtypes") or []
    return {"nodes": nodes, "radius": [round(s, 2) for s in scales] if isinstance(scales, list) else [],
            "types": [int(t) for t in types] if isinstance(types, list) else []}


def _layers(by, zones, bounds, polys=None):
    """The records of the 2026-10-06 layers. Vision entities (fog blockers, revealers) are left out on purpose:
    they are not published on this site."""
    out = {"path_corner": [{**_xy(e), "name": _name(e), "next": re.sub(r"^\[PR#\]", "", str(e.get("target") or ""))}
                           for e in by.get("path_corner", [])]}
    spawners = []
    for cls, es in by.items():
        m = _SPAWNER_RE.fullmatch(cls)
        for e in es if m else ():
            spawners.append({**_xy(e), "team": m.group(1), "lane": m.group(2),
                             "first": re.sub(r"^\[PR#\]", "", str(e.get("npcfirstwaypoint") or ""))})
    out["npc_dota_spawner"] = sorted(spawners, key=lambda s: (s["team"], s["lane"]))
    out["dota_movespeed_modifier_path"] = [_current(e) for e in by.get("dota_movespeed_modifier_path", [])]
    # one record per hull; "volume" = which entity (a fountain's shop is 3 hulls), so a count is of shops, not parts
    for cls, es in zones.items():
        out[cls] = [{"points": shape, "volume": i,
                     **({"shopType": str(e.get("shoptype", ""))} if cls == "trigger_shop" else {})}
                    for i, e in enumerate(es) if _model(e) in bounds for shape in _zone_shapes(e, bounds, polys)]
    out["info_player_start"] = [{**_xy(e), "team": "good" if cls.endswith("goodguys") else "bad"}
                                for cls in ("info_player_start_goodguys", "info_player_start_badguys")
                                for e in by.get(cls, [])]
    out["info_courier_spawn"] = [{**_xy(e), "team": "good" if "radiant" in cls else "bad"}
                                 for cls, es in sorted(by.items()) if cls.startswith("info_courier_spawn_")
                                 for e in es]
    out["ent_dota_neutral_item_stash"] = [_xy(e) for e in by.get("ent_dota_neutral_item_stash", [])]
    return out


def raw_entities(vpk):
    """Every entity of the map (all classes, the vision ones too) — for the private store next to the map files,
    never for data/map (that folder is published)."""
    with tempfile.TemporaryDirectory() as tmp:
        _run("-i", vpk, "-e", "vents_c", "-d", "-o", tmp)
        ents = []
        for dirpath, _, files in os.walk(tmp):
            for f in sorted(files):
                if f.endswith(".vents"):
                    with open(os.path.join(dirpath, f), encoding="utf-8", errors="replace") as fh:
                        ents += [{"_lump": f[:-6], **e} for e in parse_vents(fh.read())]
    return ents


def extract(vpk):
    """The mapdata dict {"data": {...}, "counts": {...}} of one map VPK."""
    with tempfile.TemporaryDirectory() as tmp:
        _run("-i", vpk, "-e", "vents_c", "-d", "-o", tmp)
        ents = []
        for dirpath, _, files in os.walk(tmp):
            for f in sorted(files):
                if f.endswith(".vents") and "_destruction" not in f:
                    with open(os.path.join(dirpath, f), encoding="utf-8", errors="replace") as fh:
                        ents += parse_vents(fh.read())
        by = {}
        for e in ents:
            by.setdefault(str(e.get("classname", "")), []).append(e)
        camps = [e for e in by.get("trigger_multiple", []) if _name(e).startswith("neutralcamp")]
        zones = {k: by.get(k, []) for k in _ZONES}
        polys = {}
        bounds = _hull_bounds(vpk, [_model(e) for e in camps] + [_model(e) for z in zones.values() for e in z], tmp,
                              polys)
    data = {k: [_xy(e) for e in by.get(k, [])] for k in _POINTS}
    data["npc_dota_tower"] = [{**_xy(e), "subType": _sub(e.get("mapunitname"), r"_(tower\d)")}
                              for e in by.get("npc_dota_tower", [])]
    data["npc_dota_barracks"] = [{**_xy(e), "subType": _sub(e.get("mapunitname"), r"_(melee|range)_rax")}
                                 for e in by.get("npc_dota_barracks", [])]
    data["npc_dota_filler"] = [_xy(e) for e in by.get("npc_dota_building", []) if "filler" in str(e.get("mapunitname"))]
    # shrines (7.00-7.22ish): buildings named "npc_dota_goodguys_healers", whatever their class
    data["npc_dota_healer"] = [_xy(e) for e in ents if "_healers" in str(e.get("mapunitname", ""))]
    data["npc_dota_neutral_spawner"] = [
        {**_xy(e), "triggerName": _name(e), "pullType": str(e.get("pulltype", "")),
         "neutralType": str(e.get("neutraltype", ""))} for e in by.get("npc_dota_neutral_spawner", [])]
    starts = {_name(e): e for e in by.get("info_player_start_dota", [])}
    # Roshan: the spawner entity plus the other pit (7.38+: "roshan_location_2"); Tormentors: both locations
    rosh = [_xy(e) for e in by.get("npc_dota_roshan_spawner", [])]
    rosh += [_xy(e) for n, e in sorted(starts.items()) if re.fullmatch(r"roshan_location_[2-9]", n)]
    data["npc_dota_roshan_spawner"] = rosh
    mini = [_xy(e) for n, e in sorted(starts.items(), reverse=True) if n.startswith("miniboss_location")]
    data["npc_dota_miniboss_spawner"] = mini or [_xy(e) for e in by.get("npc_dota_miniboss_spawner", [])]
    data["trigger_multiple"] = [{"points": _box(e, bounds[_model(e)]), "name": _name(e)} for e in camps
                                if _model(e) in bounds]
    data.update(_layers(by, zones, bounds, polys))
    counts = {k: len(v) for k, v in data.items()}
    counts["camps_by_type"] = {t: sum(1 for c in data["npc_dota_neutral_spawner"] if c["neutralType"] == t)
                               for t in sorted({c["neutralType"] for c in data["npc_dota_neutral_spawner"]})}
    return {"source": f"game files: maps/{os.path.basename(vpk)}", "data": data, "counts": counts}


def write_ents(store, sha, vpk, refresh=False):
    """The map's every entity -> <store>/ents/<sha8>.json.gz: only when missing (or `refresh`), and atomically (a .part
    file renamed over it) — other tools read these files while this runs."""
    import gzip
    path = os.path.join(store, "ents", f"{sha[:8]}.json.gz")
    if os.path.exists(path) and not refresh:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path + ".part", "wt", encoding="utf-8") as f:
        json.dump(raw_entities(vpk), f, ensure_ascii=False, separators=(",", ":"))
    os.replace(path + ".part", path)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codes", nargs="*", help="map codes (patch without the dot); default: all known")
    ap.add_argument("--vpk", help="a map VPK to read instead of the game's (one code)")
    ap.add_argument("--out", default=OUT_DIR, help="where mapdata_<code>.json goes (default: data/map)")
    ap.add_argument("--store", help="the private map store (D:\\DotaMaps): a per-patch code (738c) reads "
                                    "maps/<sha1>.vpk named in data/map/patch_maps.json, and every entity of the "
                                    "map goes to ents/<sha8>.json.gz there (never into data/map)")
    ap.add_argument("--refresh-ents", action="store_true",
                    help="rewrite the store's ents/<sha8>.json.gz even where it exists (by default only missing ones)")
    args = ap.parse_args()
    codes = args.codes or list(MAPS)
    os.makedirs(args.out, exist_ok=True)
    shas = {}
    if args.store:
        with open(os.path.join(_ROOT, "data", "map", "patch_maps.json"), encoding="utf-8") as f:
            shas = {v.replace(".", ""): m["sha1"] for v, m in json.load(f)["patches"].items()}
    for code in codes:
        # a legacy code (MAPS: 683 … 737) is the game's legacy file, the LAST map of that patch family; a per-patch
        # code (737e, 738c …) is the store's map of that patch. Never the other way: patch_maps' "7.22" is the 7.22
        # release map, not dota_722.vpk (2026-10-06: one 7.22 filler moved when the store's file was read instead)
        # ("741" -> dota.vpk is the LIVE map, i.e. the newest patch's: the store's 7.41 file is the right one)
        in_store = args.store and code in shas and (code not in MAPS or MAPS[code] == "dota.vpk")
        if args.vpk:
            vpk = args.vpk
        elif in_store:
            vpk = os.path.join(args.store, "maps", f"{shas[code]}.vpk")
        else:
            vpk = os.path.join(MAPS_DIR, MAPS[code])
        md = extract(vpk)
        if in_store:
            write_ents(args.store, shas[code], vpk, refresh=args.refresh_ents)
        with open(os.path.join(args.out, f"mapdata_{code}.json"), "w", encoding="utf-8") as f:
            json.dump(md, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        c = md["counts"]
        print(f"{code}: {c['ent_dota_tree']} trees, {c['npc_dota_neutral_spawner']} camps {c['camps_by_type']}, "
              f"{c['npc_dota_tower']} towers, {c['trigger_multiple']} camp boxes")


if __name__ == "__main__":
    main()
