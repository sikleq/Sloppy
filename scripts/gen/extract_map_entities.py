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
    """[{key: value}] of one decompiled entity lump ("====N====" blocks of "key value" lines)."""
    ents, cur = [], None
    for line in text.splitlines():
        if re.match(r"^====\d+====$", line):
            cur = {}
            ents.append(cur)
        elif cur is not None and line.strip():
            m = re.match(r"^(\S+)\s+(.*)$", line)
            if m:
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


def _hull_bounds(vpk, models, tmp):
    """{model path: ((minx, miny), (maxx, maxy))} of the camp volumes' hull models."""
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
                break
    return out


def _model(e):
    """The volume's model path, "/" separated and without the compiled "_c" (legacy maps write "maps\\\\dota\\\\…")."""
    return re.sub(r"[\\/]+", "/", str(e.get("model", ""))).replace(".vmdl_c", ".vmdl")


def _sub(unit, pattern):
    m = re.search(pattern, unit or "")
    return m.group(1) if m else ""


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
        bounds = _hull_bounds(vpk, [_model(e) for e in camps], tmp)
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
    counts = {k: len(v) for k, v in data.items()}
    counts["camps_by_type"] = {t: sum(1 for c in data["npc_dota_neutral_spawner"] if c["neutralType"] == t)
                               for t in sorted({c["neutralType"] for c in data["npc_dota_neutral_spawner"]})}
    return {"source": f"game files: maps/{os.path.basename(vpk)}", "data": data, "counts": counts}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codes", nargs="*", help="map codes (patch without the dot); default: all known")
    ap.add_argument("--vpk", help="a map VPK to read instead of the game's (one code)")
    ap.add_argument("--out", default=OUT_DIR, help="where mapdata_<code>.json goes (default: data/map)")
    args = ap.parse_args()
    codes = args.codes or list(MAPS)
    os.makedirs(args.out, exist_ok=True)
    for code in codes:
        vpk = args.vpk or os.path.join(MAPS_DIR, MAPS[code])
        md = extract(vpk)
        with open(os.path.join(args.out, f"mapdata_{code}.json"), "w", encoding="utf-8") as f:
            json.dump(md, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        c = md["counts"]
        print(f"{code}: {c['ent_dota_tree']} trees, {c['npc_dota_neutral_spawner']} camps {c['camps_by_type']}, "
              f"{c['npc_dota_tower']} towers, {c['trigger_multiple']} camp boxes")


if __name__ == "__main__":
    main()
