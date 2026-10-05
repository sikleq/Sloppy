"""The map's height grid (maps/dota.vhcg) — every map file since 7.08 carries one.

Why (the owner 2026-10-05: "decode dota.vhcg and make a height layer — the interactive ward map will need it"):
heights decide what a ward on high ground sees. Decoded 2026-10-05 from the file itself (no outside source):

    header (128 bytes): "vhcg", u32 version 1, u32 cell 128, u32 W 165, u32 H 938, u32 S 5,
                        f32 cell 128.0, f32 x0 -10752.0, f32 y0 -109440.0, zero padding to byte 128
    W x H records, row-major (row = y, south -> north; col = x, west -> east), 9 bytes each:
        f32 a — the cell's ground height (-16384 = no single height: see the flag)
        f32 b — a second surface where there is one (the river's water, 16 above its bed), else -16384
        u8  flag — 1 = the cell is not flat (cliffs, ramps): its heights are the next S x S block below
    then one S x S block of f32 per flagged cell, in the same row-major order, sample [r][q] at
        (x0 + col * cell + q * cell / (S - 1), y0 + row * cell + r * cell / (S - 1)) — edge samples equal the
        neighbouring cells' heights (checked on 7.41f: 5206 of 5206 edges next to a flat cell agree).
    Cell (col, row) spans x0 + col*128 .. +128, y0 + row*128 .. +128. The main map is rows ~779-927, cols ~8-156;
    the grid's far rows (y down to -109440) are empty here. Heights seen on 7.41f: river 0, low ground 128,
    high ground 256, 384, bases 512, 640, walls 768+.

Frame used by the site (the same as the gridnav no-ward picture): x -10240 .. 10240, y -10752 .. 10240, one value per
32 units -> 640 x 656.

    python scripts/gen/heightmap.py extract VPK OUT.vhcg          # maps/dota.vhcg of a map VPK (env S2V_CLI)
    python scripts/gen/heightmap.py grid IN.vhcg OUT.png          # 16-bit grid (height + 1024; 0 = no ground)
    python scripts/gen/heightmap.py overlay IN.vhcg OUT.png       # every height on one picture (a look)
    (the page uses one picture per height, icons/maps/heights_<ver>_<band>.png, written by `all`)
    python scripts/gen/heightmap.py all                           # both for every map file with a gridnav
"""
import gzip
import json
import os
import struct
import subprocess
import sys
import tempfile

MAGIC = b"vhcg"
NONE = -16384.0
FRAME_X0, FRAME_Y0, FRAME_W, FRAME_H, STEP = -10240, -10752, 640, 656, 32
# the bands of the Heights layer: (upper bound, RGB, label). Levels are the game's: river 0, low 128, high 256, …
# labels are the numbers only (the owner 2026-10-05: "instead of River 0, Base 512 keep only the values")
BANDS = [(64, (52, 132, 218), "0"), (192, (88, 170, 72), "128"), (320, (206, 194, 72), "256"),
         (448, (228, 144, 56), "384"), (576, (214, 84, 62), "512"), (704, (176, 86, 176), "640"),
         (1e9, (150, 150, 160), "768+")]
FILL_A, EDGE_A = 95, 225          # band fill and contour alpha
LOW_FILL_A = 40                   # low ground, the commonest level, stays light so the map shows through


def parse(raw):
    """(header dict, records [(a, b, flag)], blocks [S x S lists]) of a dota.vhcg."""
    if raw[:4] != MAGIC:
        raise ValueError("not a dota.vhcg")
    ver, cell_i, w, h, s = struct.unpack_from("<5I", raw, 4)
    cell, x0, y0 = struct.unpack_from("<3f", raw, 24)
    if ver != 1 or cell_i != int(cell):
        raise ValueError(f"unknown vhcg layout (version {ver}, cell {cell_i}/{cell})")
    start = 128
    recs = list(struct.iter_unpack("<ffB", raw[start:start + 9 * w * h]))
    flagged = sum(1 for r in recs if r[2] == 1)
    det = raw[start + 9 * w * h:]
    if len(det) != flagged * s * s * 4:
        raise ValueError(f"{len(det)} detail bytes for {flagged} flagged cells of {s}x{s}")
    vals = struct.unpack(f"<{flagged * s * s}f", det)
    blocks = [[list(vals[(k * s + r) * s:(k * s + r + 1) * s]) for r in range(s)] for k in range(flagged)]
    head = {"cell": cell, "w": w, "h": h, "s": s, "x0": x0, "y0": y0}
    return head, recs, blocks


def load(path):
    with (gzip.open if path.endswith(".gz") else open)(path, "rb") as f:
        return parse(f.read())


def height_at(head, recs, blocks, index, x, y):
    """Ground height at world (x, y), None where there is none. `index` = flagged cell -> block number."""
    col = int((x - head["x0"]) // head["cell"])
    row = int((y - head["y0"]) // head["cell"])
    if not (0 <= col < head["w"] and 0 <= row < head["h"]):
        return None
    a, _b, flag = recs[row * head["w"] + col]
    if flag == 1:
        step = head["cell"] / (head["s"] - 1)
        q = int((x - head["x0"] - col * head["cell"]) // step)
        r = int((y - head["y0"] - row * head["cell"]) // step)
        a = blocks[index[row * head["w"] + col]][min(r, head["s"] - 1)][min(q, head["s"] - 1)]
    return None if a <= NONE + 1 else a


def block_index(recs):
    out, k = {}, 0
    for i, r in enumerate(recs):
        if r[2] == 1:
            out[i] = k
            k += 1
    return out


def frame(head, recs, blocks):
    """The site's frame as rows (north first) of heights at 32-unit samples; None = no ground."""
    index = block_index(recs)
    rows = []
    for j in range(FRAME_H):
        y = FRAME_Y0 + (FRAME_H - 1 - j) * STEP + STEP / 2
        rows.append([height_at(head, recs, blocks, index, FRAME_X0 + i * STEP + STEP / 2, y) for i in range(FRAME_W)])
    return rows


def band(hgt):
    for k, (top, _rgb, _label) in enumerate(BANDS):
        if hgt < top:
            return k
    return len(BANDS) - 1


def band_overlays(rows):
    """{band: picture} — each height on its own transparent picture, so the page can switch the heights one by one
    (the owner 2026-10-05: "click 0, 128 … to turn those layers on and off"). Bands filled faintly, the step drawn
    strong on its upper side. Bands with no ground at all are left out."""
    from PIL import Image
    h, w = len(rows), len(rows[0])
    bands = [[None if v is None else band(v) for v in row] for row in rows]
    out = {}
    for j in range(h):
        for i in range(w):
            k = bands[j][i]
            if k is None:
                continue
            if k not in out:
                out[k] = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            rgb = BANDS[k][1]
            edge = any(0 <= jj < h and 0 <= ii < w and bands[jj][ii] is not None and bands[jj][ii] < k
                       for jj, ii in ((j, i + 1), (j, i - 1), (j + 1, i), (j - 1, i)))
            if edge:   # the upper side of a step carries the line, darker
                out[k].putpixel((i, j), tuple(int(c * 0.55) for c in rgb) + (EDGE_A,))
            else:
                out[k].putpixel((i, j), rgb + (LOW_FILL_A if k == 1 else FILL_A,))
    return out


def overlay_image(rows):
    """Every band on one picture (the bands never overlap)."""
    from PIL import Image
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for _k, layer in sorted(band_overlays(rows).items()):
        im.alpha_composite(layer)
    return im


def grid_image(rows):
    """16-bit grayscale: height + 1024 (0 = no ground) — the data a ward tool can read back."""
    from PIL import Image
    h, w = len(rows), len(rows[0])
    im = Image.new("I;16", (w, h), 0)
    px = im.load()
    for j in range(h):
        for i in range(w):
            v = rows[j][i]
            px[i, j] = 0 if v is None else max(1, min(65535, int(round(v)) + 1024))
    return im


def extract(vpk, out):
    """maps/dota.vhcg of a map VPK -> out. Needs Source2Viewer-CLI (env S2V_CLI)."""
    cli = os.environ.get("S2V_CLI")
    if not cli:
        sys.exit("Set S2V_CLI to Source2Viewer-CLI.exe (https://github.com/ValveResourceFormat/ValveResourceFormat)")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([cli, "-i", vpk, "-o", tmp, "--vpk_filepath", "maps/dota.vhcg"], check=True, capture_output=True)
        # the CLI keeps the file's path inside the output folder (tmp/maps/dota.vhcg)
        with open(os.path.join(tmp, "maps", "dota.vhcg"), "rb") as f:
            raw = f.read()
    parse(raw)                                        # refuse to save something we can't read
    with open(out, "wb") as f:
        f.write(raw)


def _all():
    """Heights for every map file that has a gridnav in data/map (the Terrain pages' map files)."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    maps = json.load(open(os.path.join(root, "data", "map", "patch_maps.json"), encoding="utf-8"))["patches"]
    vpks = os.environ.get("OLDBUILDS_MAPS",
                          os.path.join(os.path.expanduser("~"), "tools", "maprender", "oldbuilds", "maps"))
    for name in sorted(os.listdir(os.path.join(root, "data", "map"))):
        if not (name.startswith("gridnav_") and name.endswith(".gnv.gz")):
            continue
        code = name[len("gridnav_"):-len(".gnv.gz")]
        ver = f"{code[0]}.{code[1:]}"
        vpk = os.path.join(vpks, maps[ver]["sha1"] + ".vpk")
        with tempfile.TemporaryDirectory() as tmp:
            raw_path = os.path.join(tmp, "dota.vhcg")
            extract(vpk, raw_path)
            rows = frame(*load(raw_path))
        grid_image(rows).save(os.path.join(root, "data", "map", f"heights_{code}.png"), optimize=True)
        for k, layer in band_overlays(rows).items():     # one picture per height: the page switches them one by one
            layer.save(os.path.join(root, "icons", "maps", f"heights_{ver}_{k}.png"), optimize=True)
        print("heights", ver)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "all":
        _all()
    elif cmd == "extract":
        extract(sys.argv[2], sys.argv[3])
    else:
        src, out = sys.argv[2], sys.argv[3]
        rows = frame(*load(src))
        (grid_image if cmd == "grid" else overlay_image)(rows).save(out, optimize=True)
