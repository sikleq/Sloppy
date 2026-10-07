"""Three cell grids of every map file in the history -> Oldgrowth versions/<patch>/ (the owner 2026-10-07: publish
the walkable, height and vision-blocker grids of all 65 map files as raw data):

  gridnav.bin.gz  maps/dota.gnv's cells as they are (bit 0 walkable, bit 4 no wards, 20 = the void beyond the map)
  elev.bin.gz     the height level of each cell: the highest z of the map's physics surface (the "physics_group" mesh
                  of maps/dota/world_physics.vmdl_c, legacy maps world_physics.vphys_c) above the cell's centre, in
                  steps of 128 from the river: z_river = the lowest 128-step layer holding >= 1 % of the covered cells,
                  level = clip(round((z - z_river) / 128), 0, 254); 255 = no ground
  fow.bin.gz      1 in the cell of every ent_fow_blocker_node of the default_ents lump, else 0 (raw data only: the
                  Terrain pages never draw vision)

uint8, row-major, row 0 = the grid's min_y, w x h. Each map file has its own grid (the gnv header; 64-unit cells:
before 7.33 260 x 260 from (-8320, -8320), since 7.33 320 x 328 from (-10240, -10752)), written into info.json:
"grid": {"w", "h", "min_x", "min_y", "edge": 64, "z_river"}. Sources: the map store (maps/<sha1>.vpk,
ents/<sha8>.json.gz). gzip without a name or time, so a re-run that finds the same cells writes the same bytes.

    python scripts/gen/map_grids.py [--store D:/DotaMaps] [--og ~/Documents/Oldgrowth] [patch ...]
"""
import argparse
import gzip
import io
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

EDGE = 64.0
STEP, NODATA = 128.0, 255
_PHYSICS = ("maps/dota/world_physics.vmdl_c", "maps/dota/world_physics.vphys_c")


def _cli():
    path = os.environ.get("S2V_CLI", "")
    if not path or not os.path.exists(path):
        sys.exit("Set S2V_CLI to Source2Viewer-CLI.exe (https://github.com/ValveResourceFormat/ValveResourceFormat)")
    return path


def gridnav(vpk, tmp):
    """(cell bytes, grid) of a map's maps/dota.gnv — size and origin from its header."""
    subprocess.run([_cli(), "-i", vpk, "-o", tmp, "--vpk_filepath", "maps/dota.gnv"], check=True, capture_output=True)
    with open(os.path.join(tmp, "maps", "dota.gnv"), "rb") as f:
        raw = f.read()
    cell = float(np.frombuffer(raw[4:8], "<f4")[0])
    w, h = int.from_bytes(raw[16:20], "little"), int.from_bytes(raw[20:24], "little")
    ox, oy = (int.from_bytes(raw[i:i + 4], "little", signed=True) for i in (24, 28))
    if cell != EDGE or len(raw) < 32 + w * h:
        raise ValueError(f"unexpected gridnav: cell {cell}, {w}x{h}, {len(raw)} bytes")
    return raw[32:32 + w * h], {"w": w, "h": h, "min_x": ox * EDGE, "min_y": oy * EDGE, "edge": EDGE}


def _mesh(path):
    """(vertices, triangles) of the glTF's "physics_group" mesh."""
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    with open(os.path.join(os.path.dirname(path), doc["buffers"][0]["uri"]), "rb") as f:
        buf = f.read()
    prim = next(m for m in doc["meshes"] if m.get("name") == "physics_group")["primitives"][0]

    def acc(i):
        a = doc["accessors"][i]
        view = doc["bufferViews"][a["bufferView"]]
        off, n = view.get("byteOffset", 0) + a.get("byteOffset", 0), a["count"]
        if a["componentType"] == 5126:
            comp = {"VEC3": 3, "VEC2": 2, "SCALAR": 1}[a["type"]]
            return np.frombuffer(buf, np.float32, n * comp, off).reshape(n, comp)
        dtype = {5125: np.uint32, 5123: np.uint16}.get(a["componentType"])
        if dtype is None:
            raise ValueError(f"componentType {a['componentType']}")
        return np.frombuffer(buf, dtype, n, off)
    return (acc(prim["attributes"]["POSITION"]).astype(np.float64),
            acc(prim["indices"]).astype(np.int64).reshape(-1, 3))


def physics_mesh(vpk, tmp):
    """The map's physics surface: its world_physics model exported to glTF (several files come out of a .vmdl_c —
    the one holding the physics_group mesh)."""
    for name in _PHYSICS:
        out = os.path.join(tmp, "phys")
        subprocess.run([_cli(), "--input", vpk, "--vpk_filepath", name, "-o", out, "-d",
                        "--gltf_export_format", "gltf"], capture_output=True)
        # a single model is written NEXT to the -o path (phys.gltf), several go into it (phys/…): search all of tmp
        for dirpath, _dirs, files in sorted(os.walk(tmp)):
            for fn in sorted(files):
                if not fn.endswith(".gltf"):
                    continue
                path = os.path.join(dirpath, fn)
                with open(path, encoding="utf-8") as f:
                    doc = json.load(f)
                if doc.get("buffers") and any(m.get("name") == "physics_group" for m in doc.get("meshes", [])):
                    return _mesh(path)
    raise RuntimeError(f"no map physics in {os.path.basename(vpk)}")


def rasterize_max_z(verts, tris, grid):
    """The highest z of the surface over the centre of every cell (-inf where none)."""
    W, H, X0, Y0 = grid["w"], grid["h"], grid["min_x"], grid["min_y"]
    zmax = np.full((H, W), -np.inf)
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    xs, ys = np.stack([a[:, 0], b[:, 0], c[:, 0]]), np.stack([a[:, 1], b[:, 1], c[:, 1]])
    gx0 = np.clip(np.floor((xs.min(0) - X0 - EDGE / 2) / EDGE + 1e-9), 0, W - 1).astype(int)
    gx1 = np.clip(np.floor((xs.max(0) - X0 - EDGE / 2) / EDGE), 0, W - 1).astype(int)
    gy0 = np.clip(np.floor((ys.min(0) - Y0 - EDGE / 2) / EDGE + 1e-9), 0, H - 1).astype(int)
    gy1 = np.clip(np.floor((ys.max(0) - Y0 - EDGE / 2) / EDGE), 0, H - 1).astype(int)
    for t in range(len(tris)):
        if gx1[t] < gx0[t] or gy1[t] < gy0[t]:
            continue
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = a[t], b[t], c[t]
        det = (by - ay) * (cx - ax) - (bx - ax) * (cy - ay)
        if abs(det) < 1e-12:
            continue
        px, py = np.meshgrid(X0 + (np.arange(gx0[t], gx1[t] + 1) + 0.5) * EDGE,
                             Y0 + (np.arange(gy0[t], gy1[t] + 1) + 0.5) * EDGE)
        w0 = ((by - ay) * (px - ax) - (bx - ax) * (py - ay)) / det
        w1 = -((cy - ay) * (px - ax) - (cx - ax) * (py - ay)) / det
        inside = (w0 >= -1e-9) & (w1 >= -1e-9) & (w0 + w1 <= 1 + 1e-9)
        if inside.any():
            sub = zmax[gy0[t]:gy1[t] + 1, gx0[t]:gx1[t] + 1]
            np.maximum(sub, np.where(inside, az + w1 * (bz - az) + w0 * (cz - az), -np.inf), out=sub)
    return zmax


def levels(zmax):
    """(uint8 levels, z_river): 0 = the river (the lowest 128-step layer holding >= 1 % of the covered cells), then
    one per 128 up; 255 = no ground."""
    covered = np.isfinite(zmax)
    q = np.round(zmax[covered] / STEP).astype(int)
    uq, cnt = np.unique(q, return_counts=True)
    z_river = uq[cnt >= 0.01 * covered.sum()].min() * STEP
    lv = np.clip(np.round((zmax - z_river) / STEP), 0, 254)
    return np.where(covered, lv, NODATA).astype(np.uint8), float(z_river)


def _xy(e):
    o = e.get("origin")
    if isinstance(o, str):
        o = [float(v) for v in o.split()]
    return float(o[0]), float(o[1])


def fow_grid(ents, grid):
    """1 in the cell of every vision blocker node of the default_ents lump."""
    out = np.zeros((grid["h"], grid["w"]), np.uint8)
    for e in ents:
        if e.get("classname") != "ent_fow_blocker_node" or e.get("_lump") != "default_ents":
            continue
        x, y = _xy(e)
        gx, gy = int(np.floor((x - grid["min_x"]) / EDGE)), int(np.floor((y - grid["min_y"]) / EDGE))
        if 0 <= gx < grid["w"] and 0 <= gy < grid["h"]:
            out[gy, gx] = 1
    return out


def _write_gz(path, data):
    """gzip with no file name and time 0 inside (same cells -> same bytes), written atomically."""
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as f:
        f.write(data)
    with open(path + ".part", "wb") as f:
        f.write(buf.getvalue())
    os.replace(path + ".part", path)


def publish(store, og, ver, info):
    sha = info["map_sha1"]
    vpk = os.path.join(store, "maps", f"{sha}.vpk")
    vdir = os.path.join(og, "versions", ver)
    with tempfile.TemporaryDirectory() as tmp:
        cells, grid = gridnav(vpk, tmp)
        elev, z_river = levels(rasterize_max_z(*physics_mesh(vpk, tmp), grid))
    with gzip.open(os.path.join(store, "ents", f"{sha[:8]}.json.gz"), "rt", encoding="utf-8") as f:
        fow = fow_grid(json.load(f), grid)
    _write_gz(os.path.join(vdir, "gridnav.bin.gz"), cells)
    _write_gz(os.path.join(vdir, "elev.bin.gz"), elev.tobytes())
    _write_gz(os.path.join(vdir, "fow.bin.gz"), fow.tobytes())
    info = {**info, "grid": {"w": grid["w"], "h": grid["h"], "min_x": grid["min_x"], "min_y": grid["min_y"],
                             "edge": int(EDGE), "z_river": z_river}}
    with open(os.path.join(vdir, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return f"{ver}: {grid['w']}x{grid['h']}, z_river {z_river:g}, {int(fow.sum())} blocker cells, " \
           f"{int((elev != NODATA).sum())} ground cells"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("patches", nargs="*", help="only these Oldgrowth folders (default: every map file)")
    ap.add_argument("--store", default="D:/DotaMaps")
    ap.add_argument("--og", default=os.environ.get("OLDGROWTH_DIR",
                                                   os.path.join(os.path.expanduser("~"), "Documents", "Oldgrowth")))
    args = ap.parse_args()
    vdir = os.path.join(args.og, "versions")
    for ver in sorted(os.listdir(vdir)):
        with open(os.path.join(vdir, ver, "info.json"), encoding="utf-8") as f:
            info = json.load(f)
        if info.get("same_as") or (args.patches and ver not in args.patches):
            continue
        print(publish(args.store, args.og, ver, info), flush=True)


if __name__ == "__main__":
    main()
