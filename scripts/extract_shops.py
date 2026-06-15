"""extract_shops.py — Pull the Dota 2 shop layout (item categories) from the VPK.

The shop CATEGORIES shown on Liquipedia's Portal:Items (Consumables, Attributes,
Equipment, Support, Magical, Armor, Weapons, Artifacts, Secret Shop, …) are NOT in
items.txt or the web datafeed — they live in scripts/shops.txt inside pak01_dir.vpk.
Valve reshuffles them between patches (e.g. 7.41 "Shop Reshuffle"), so we extract the
file per patch; patch/rosters.py then derives the items_dyn Category filter from it.

Run after a patch (needs the game installed + `pip install vpk`), then rebuild:

    python scripts/extract_shops.py
    python builders/patch.py
    # optional: non-default install path
    python scripts/extract_shops.py "D:\\Steam\\steamapps\\common\\dota 2 beta\\game\\dota"
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "shops.txt"
DEFAULT_DOTA = r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota"


def decode_valve_text(data: bytes) -> str:
    if data.startswith(b"\xff\xfe"):
        return data[2:].decode("utf-16-le", errors="replace")
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8", errors="replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-16-le", errors="replace")


def main() -> int:
    dota_path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DOTA_PATH", DEFAULT_DOTA)
    vpk_file = Path(dota_path) / "pak01_dir.vpk"
    if not vpk_file.exists():
        print(f"X pak01_dir.vpk not found at {vpk_file}\n"
              f"  Pass your dota path: python scripts/extract_shops.py <path-to>/game/dota")
        return 1
    try:
        import vpk
    except ImportError:
        print("X missing the 'vpk' library — run:  pip install vpk")
        return 1

    print(f"Opening {vpk_file} ...")
    pak = vpk.open(str(vpk_file))
    try:
        all_paths = list(pak)
    except TypeError:
        all_paths = list(getattr(pak, "tree", {}).keys())

    # The shop layout = a file named shops.txt, NOT under a workshop/ directory.
    hits = [p for p in all_paths
            if p.lower().replace("\\", "/").endswith("/shops.txt") or p.lower() == "shops.txt"]
    hits = [p for p in hits if "workshop" not in p.lower()]
    if not hits:
        print("X no shops.txt found in the VPK — Valve may have moved it. "
              "Run scripts/extract_shops_recon.py-style discovery or tell me.")
        return 1
    src = hits[0]
    f = pak.get_file(src)
    text = decode_valve_text(f.read())
    f.close()
    OUT.write_text(text, encoding="utf-8")

    # Quick sanity: count sections + item lines.
    sections = re.findall(r'^\s*"([a-z0-9_]+)"\s*(?://.*)?$', text, re.M)
    items = re.findall(r'^\s*"item"\s*"item_[a-z0-9_]+"', text, re.M)
    print(f"-> {src}  ->  {OUT.relative_to(ROOT)}")
    print(f"   {len(sections)} sections, {len(items)} item entries. "
          f"Now run:  python builders/patch.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
