"""The map's gridnav (maps/dota.gnv): one byte per 64-unit cell — where a hero can walk and where a ward can't stand.

Why (the owner 2026-10-02: "a layer of every place where wards can't be placed"): the byte's flags, checked against
the map —
    bit0 (1)   the cell is walkable;
    bit4 (16)  no wards here: set on the walkable ground of both fountains, both Roshan pits and the secret shop (the
               map's five trigger_no_wards volumes, baked into the grid) and on every cliff edge;
    bit2 (4)   with bit4 (= 20): out of bounds, the void around the map (7.40: "Added additional blocks preventing
               flying movement around the edges of the map").
A ward stands only on a walkable cell without the no-ward flag (trees aside: they are entities, not in the grid).
7.39d's "Fixed a ward spot in Radiant safe lane hard camp" is 4 cells there turned no-ward; 7.41c opened 149 cells
by the Twin Gates and Tormentors that no note mentions.

File: 32-byte header (magic 0xfadebead, float cell size 64 @4, uint32 width @16, height @20, int32 origin cell x
@24, y @28 → the grid starts at (-10240, -10752)), then width x height bytes, row 0 = the south edge.

    python scripts/gen/gridnav.py extract VPK OUT.gnv.gz      # maps/dota.gnv of a map VPK (env S2V_CLI)
    python scripts/gen/gridnav.py overlay IN.gnv.gz OUT.png   # the Terrain page's no-ward layer picture
"""
import gzip
import os
import struct
import subprocess
import sys
import tempfile

MAGIC = 0xFADEBEAD
WALKABLE, NO_WARD, OUT = 1, 16, 4
# overlay colours (RGBA): a no-ward zone on walkable ground stands out, a cliff/obstacle less, the void least
# magenta: no other layer uses it (Roshan is crimson, Tormentors red, lotus pink, wisdom purple)
ZONE, BLOCKED, VOID = (235, 80, 255, 175), (235, 80, 255, 95), (235, 80, 255, 38)


def parse(raw):
    """(header dict, cells bytes) of a dota.gnv."""
    magic, cell = struct.unpack_from("<If", raw, 0)
    w, h, ox, oy = struct.unpack_from("<IIii", raw, 16)
    if magic != MAGIC or cell <= 0 or len(raw) < 32 + w * h:
        raise ValueError("not a dota.gnv")
    return {"cell": cell, "w": w, "h": h, "x0": ox * cell, "y0": oy * cell}, raw[32:32 + w * h]


def load(path):
    with (gzip.open if path.endswith(".gz") else open)(path, "rb") as f:
        return parse(f.read())


def wardable(v):
    return bool(v & WALKABLE) and not v & NO_WARD


def kind(v):
    """'ward' (a ward can stand here), 'zone' (walkable, no wards), 'void' (out of bounds) or 'blocked'."""
    if wardable(v):
        return "ward"
    if v & WALKABLE:
        return "zone"
    return "void" if v & NO_WARD and v & OUT else "blocked"


def ward_changes(old_cells, new_cells):
    """(lost, gained): cells where a ward could stand before and can't now, and the other way round."""
    lost = sum(1 for a, b in zip(old_cells, new_cells) if wardable(a) and not wardable(b))
    gained = sum(1 for a, b in zip(old_cells, new_cells) if not wardable(a) and wardable(b))
    return lost, gained


def changed_cells(head, old_cells, new_cells):
    """([[x, y]] that turned no-ward, [[x, y]] that turned wardable): world centres of the cells whose wardability
    changed (the Terrain chips outline them on the map — green where no-ward ground was added, red where removed)."""
    w, cell = head["w"], head["cell"]
    to_no_ward, to_wardable = [], []
    for i, (a, b) in enumerate(zip(old_cells, new_cells)):
        if wardable(a) != wardable(b):
            centre = [int(head["x0"] + (i % w + 0.5) * cell), int(head["y0"] + (i // w + 0.5) * cell)]
            (to_no_ward if wardable(a) else to_wardable).append(centre)
    return to_no_ward, to_wardable


def no_ward_cells(cells):
    """Cells of the map (out of bounds aside) where a ward can't stand."""
    return sum(1 for v in cells if kind(v) in ("zone", "blocked"))


def extract(vpk, out):
    """maps/dota.gnv of a map VPK -> out (.gnv.gz). Needs Source2Viewer-CLI (env S2V_CLI)."""
    cli = os.environ.get("S2V_CLI")
    if not cli:
        sys.exit("Set S2V_CLI to Source2Viewer-CLI.exe (https://github.com/ValveResourceFormat/ValveResourceFormat)")
    with tempfile.TemporaryDirectory() as tmp:
        dst = os.path.join(tmp, "dota.gnv")
        subprocess.run([cli, "-i", vpk, "-o", dst, "--vpk_filepath", "maps/dota.gnv"], check=True, capture_output=True)
        with open(dst, "rb") as f:
            raw = f.read()
    parse(raw)
    with gzip.open(out, "wb") as f:
        f.write(raw)


def overlay(src, out):
    """The no-ward layer picture: one pixel per cell, north up, transparent where a ward can stand."""
    from PIL import Image
    head, cells = load(src)
    w, h = head["w"], head["h"]
    colour = {"zone": ZONE, "blocked": BLOCKED, "void": VOID}
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for i, v in enumerate(cells):
        c = colour.get(kind(v))
        if c:
            px[i % w, h - 1 - i // w] = c
    im.save(out, optimize=True)


if __name__ == "__main__":
    cmd, a, b = sys.argv[1:4]
    {"extract": extract, "overlay": overlay}[cmd](a, b)
