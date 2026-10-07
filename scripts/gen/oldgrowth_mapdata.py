"""Oldgrowth's object lists, every layer (the owner 2026-10-06: "Добавь слои в Oldgrowth"): for each map file of the
history (an Oldgrowth versions/<patch>/ folder without "same_as"),

  versions/<patch>/mapdata.json     the objects Sloppy reads (extract_map_entities.extract): trees, camps, towers …
                                    and the 2026-10-06 layers — lane creep paths, river currents with their radius and
                                    strength, shop / no-ward / Roshan pit zones, spawn points
  versions/<patch>/entities.json.gz EVERY entity of the map file as decompiled, vision included (the owner: "Полный
                                    список объектов всех карт, включая обзор — можно выложить и на GitHub"; Sloppy
                                    only never DRAWS vision)

  versions/<patch>/{gridnav,elev,fow}.bin.gz + info.json "grid"   the cell grids (scripts/gen/map_grids.py) — every
                                    map file gets them, a NEW one too (2026-10-07: another tool reads them from here)

from the map store (D:\\DotaMaps: maps/<sha1>.vpk, ents/<sha8>.json.gz). The "changes" line of info.json is left as it
is. Runs on the owner's PC (Source2Viewer-CLI, the store, numpy); then `python build_index.py` in Oldgrowth:

    python scripts/gen/oldgrowth_mapdata.py [--store D:/DotaMaps] [--og ~/Documents/Oldgrowth] [patch ...]
"""
import argparse
import json
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import extract_map_entities as ext  # noqa: E402


def _folders(og, only):
    vdir = os.path.join(og, "versions")
    for ver in sorted(os.listdir(vdir)):
        with open(os.path.join(vdir, ver, "info.json"), encoding="utf-8") as f:
            info = json.load(f)
        if not info.get("same_as") and (not only or ver in only):
            yield ver, info


def publish(store, og, ver, info, grids=True):
    sha = info["map_sha1"]
    vdir = os.path.join(og, "versions", ver)
    md = ext.extract(os.path.join(store, "maps", f"{sha}.vpk"))
    with open(os.path.join(vdir, "mapdata.json"), "w", encoding="utf-8") as f:
        json.dump({"source": f"maps/dota.vpk of patch {ver}: sha1 {sha}, Steam depot 373301 manifest "
                             f"{info['manifest']}", "data": md["data"], "counts": md["counts"]},
                  f, ensure_ascii=False, separators=(",", ":"))
    raw = ext.write_ents(store, sha, os.path.join(store, "maps", f"{sha}.vpk"))     # only when missing, atomically
    shutil.copyfile(raw, os.path.join(vdir, "entities.json.gz"))
    c = md["counts"]
    line = (f"{ver}: {c['ent_dota_tree']} trees, {c['path_corner']} lane corners, "
            f"{c['dota_movespeed_modifier_path']} currents, {c['trigger_shop']} shop zones")
    if grids:
        # the three cell grids too (2026-10-07: every new map file gets them — another tool reads them from here)
        import map_grids
        line += " | " + map_grids.publish(store, og, ver, info).split(": ", 1)[1]
    return line


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("patches", nargs="*", help="only these Oldgrowth folders (default: every map file)")
    ap.add_argument("--store", default="D:/DotaMaps")
    ap.add_argument("--og", default=os.environ.get("OLDGROWTH_DIR",
                                                   os.path.join(os.path.expanduser("~"), "Documents", "Oldgrowth")))
    ap.add_argument("--no-grids", action="store_true", help="skip the cell grids (scripts/gen/map_grids.py)")
    args = ap.parse_args()
    for ver, info in _folders(args.og, set(args.patches)):
        print(publish(args.store, args.og, ver, info, grids=not args.no_grids), flush=True)


if __name__ == "__main__":
    main()
