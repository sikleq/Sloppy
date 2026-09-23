"""extract_vpk_boss_icons.py — Roshan and Tormentor art straight from the game VPK.

Roshan's and the Tormentor's ability icons (roshan_revengeroar, roshan_grab_and_throw,
miniboss_*) are not on Valve's web CDN, and neither is Roshan's portrait. The client has
them: panorama/images/spellicons/<slug>_png.vtex_c and
panorama/images/heroes/npc_dota_hero_roshan_png.vtex_c. Decoding reuses extract_vpk_icons.

    python scripts/fetch/extract_vpk_boss_icons.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_vpk_icons import DEFAULT_VPK, decode, read_file, read_tree  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ABILITIES = ["roshan_bash", "roshan_slam", "roshan_spell_block", "roshan_revengeroar", "roshan_grab_and_throw",
             "miniboss_unyielding_shield", "miniboss_reflect", "miniboss_radiance", "miniboss_alleviation",
             "miniboss_fortification"]
UNITS = {"npc_dota_roshan": "panorama/images/heroes/npc_dota_hero_roshan_png.vtex_c",
         "npc_dota_miniboss": "panorama/images/heroes/npc_dota_tormentor_radiant_png.vtex_c"}


def main() -> int:
    entries, base = read_tree(DEFAULT_VPK)
    jobs = [(f"panorama/images/spellicons/{s}_png.vtex_c", ROOT / "icons" / "abilities" / f"{s}.png") for s in ABILITIES]
    jobs += [(src, ROOT / "icons" / "units" / f"{name}.png") for name, src in UNITS.items()]
    missing = 0
    for internal, dst in jobs:
        try:
            img = decode(read_file(DEFAULT_VPK, internal, entries, base))
        except KeyError:
            print(f"  missing in VPK: {internal}")
            missing += 1
            continue
        img.save(dst)
        print(f"  {dst.relative_to(ROOT)}  {img.size[0]}x{img.size[1]}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
