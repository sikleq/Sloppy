"""server.dll's neutral camp table -> data/rules/camp_table.json[<version>] — no IDA, no address to look up by hand
(owner 2026-11-22: "нельзя автоматически научить?").

The table (read once with the IDA researcher, server.dll 6975 / 6989): 4 tiers (spawner neutralType 0 small, 1 medium,
2 large, 3 ancient), 0x148 bytes each = an int32 make-up count, then 8 make-ups x 5 char* npc names (0x28 each); an
empty string is no unit. Make-up i is the map's spawn type i+1. A flooded camp grows by reading its make-up one tier up.

Found by its shape, not its address: every qword pointing at the string "npc_dota_neutral_kobold" is tried as a slot of
tier 0; the base whose four tiers all read as neutral creep names (counts 1-8, kobolds in tier 0, an ancient in tier 3)
is the table. Exactly one must fit, else it stops.

    python scripts/gen/camp_table.py 7.42                       # the installed game's server.dll
    python scripts/gen/camp_table.py 7.41f --dll path/to/server.dll
"""
import argparse
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(_ROOT, "data", "rules", "camp_table.json")
DLL = os.path.join(os.environ.get("DOTA_DIR", r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta"),
                   "game", "dota", "bin", "win64", "server.dll")
TIER, MAKEUP, SLOTS, MAKEUPS, TIERS = 0x148, 0x28, 5, 8, 4
PREFIX = b"npc_dota_neutral_"


class Image:
    """A PE file's sections, enough to follow pointers (no pefile needed in CI)."""

    def __init__(self, path):
        with open(path, "rb") as f:
            self.raw = f.read()
        r = self.raw
        pe = int.from_bytes(r[0x3C:0x40], "little")
        nsec = int.from_bytes(r[pe + 6:pe + 8], "little")
        opt = pe + 24
        self.base = int.from_bytes(r[opt + 24:opt + 32], "little")
        sec = opt + int.from_bytes(r[pe + 20:pe + 22], "little")
        self.secs = []
        for i in range(nsec):
            s = sec + 40 * i
            vsize, va, rsize, ptr = (int.from_bytes(r[s + o:s + o + 4], "little") for o in (8, 12, 16, 20))
            self.secs.append((va, max(vsize, rsize), ptr, rsize))

    def off(self, rva):
        for va, size, ptr, rsize in self.secs:
            if va <= rva < va + size:
                return ptr + rva - va if rva - va < rsize else None
        return None

    def rva_of(self, off):
        for va, _size, ptr, rsize in self.secs:
            if ptr <= off < ptr + rsize:
                return va + off - ptr
        return None

    def qword(self, rva):
        o = self.off(rva)
        return None if o is None else int.from_bytes(self.raw[o:o + 8], "little")

    def cstr(self, va):
        o = self.off(va - self.base)
        if o is None:
            return None
        end = self.raw.find(b"\0", o, o + 96)
        return None if end < 0 else self.raw[o:end]


def read_table(img, base):
    """{tier: [[npc, …] × 8]} at `base`, or None when it is not the table."""
    tiers = {}
    for t in range(TIERS):
        tb = base + t * TIER
        o = img.off(tb)
        if o is None:
            return None
        count = int.from_bytes(img.raw[o:o + 4], "little", signed=True)
        if not 1 <= count <= MAKEUPS:
            return None
        rows = []
        for m in range(MAKEUPS):
            row = []
            for s in range(SLOTS):
                p = img.qword(tb + 8 + m * MAKEUP + s * 8)
                name = img.cstr(p) if p else None
                if name is None:
                    return None
                if name and not name.startswith(PREFIX):
                    return None
                if name:
                    row.append(name.decode())
            rows.append(row)
        tiers[str(t)] = rows
    flat0 = sum(tiers["0"], [])
    ancient = sum(tiers["3"], [])
    if "npc_dota_neutral_kobold" not in flat0 or not any(n in ancient for n in (
            "npc_dota_neutral_black_dragon", "npc_dota_neutral_granite_golem")):
        return None
    return tiers


def find_table(img):
    """(rva, tiers) of the one place the table fits; raises when none or several do."""
    target = img.raw.find(b"\0npc_dota_neutral_kobold\0")
    if target < 0:
        raise SystemExit("server.dll has no npc_dota_neutral_kobold string")
    va = img.base + img.rva_of(target + 1)
    needle = va.to_bytes(8, "little")
    found = {}
    pos = img.raw.find(needle)
    while pos >= 0:
        ref = img.rva_of(pos)
        if ref is not None:
            for m in range(MAKEUPS):
                for s in range(SLOTS):
                    base = ref - 8 - m * MAKEUP - s * 8
                    if base not in found:
                        t = read_table(img, base)
                        if t:
                            found[base] = t
        pos = img.raw.find(needle, pos + 1)
    if len(found) != 1:
        raise SystemExit(f"camp table: {len(found)} places fit ({[hex(b) for b in found]}) — read it with the IDA "
                         "researcher and fix the layout in this script")
    return next(iter(found.items()))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version")
    ap.add_argument("--dll", default=DLL)
    ap.add_argument("--build", type=int, help="the build number to record (default: from steam.inf)")
    args = ap.parse_args(argv)
    img = Image(args.dll)
    rva, tiers = find_table(img)
    build = args.build
    if build is None:
        inf = os.path.join(os.path.dirname(args.dll), "..", "..", "steam.inf")
        try:
            with open(inf, encoding="utf-8") as f:
                build = next(int(l.split("=")[1]) for l in f if l.startswith("ClientVersion"))
        except (OSError, StopIteration, ValueError):
            build = None
    with open(OUT, encoding="utf-8") as f:
        data = json.load(f)
    data[args.version] = {"build": build, "table_rva": hex(rva), "tiers": tiers}
    tmp = OUT + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    os.replace(tmp, OUT)
    print(f"{args.version}: camp table at {hex(rva)} (build {build}), make-ups per tier "
          f"{ {t: sum(1 for r in rows if r) for t, rows in tiers.items()} }")
    return 0


if __name__ == "__main__":
    sys.exit(main())
