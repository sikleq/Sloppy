"""The runes' icons from the game client (owner 2026-10-28: 7.40 "Bounty Rune: …", "Haste Rune: …" rows show the
rune's icon, its name on hover — like a facet row's ability icon).

    python scripts/fetch/fetch_rune_icons.py        -> icons/runes/<key>.png

The game has 10 runes (data/abilities_english.txt DOTA_Tooltip_rune_*): Bounty, Haste, Amplify Damage (Double
Damage), Illusion, Invisibility, Regeneration, Arcane, Shield, Water, Wisdom (removed in 7.38). The power runes'
icons are their buff icons (panorama/images/spellicons/rune_*); Bounty has the HUD rune timer's icon.
Not from here (kept as they are, this script does not touch them):
- water.png, wisdom.png — the game's minimap icons ("<Name> Rune mapicon dota2 gameasset.png"), downloaded from
  Liquipedia's Runes page through tools/liquipedia_cache.py's throttle (owner 2026-10-28: the client's emoticons and
  the HUD timer's sparkle were not the rune);
- illusion.png — no 2D icon in the client: the Terrain page's power-rune picture icons/ui/gothic/tc_rune_3.png, made
  from the same Liquipedia map icon, copied by this script.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

# rune -> the client's picture of it
SOURCES = {
    "bounty": "panorama/images/hud/timer/bounty_rune_png.vtex_c",
    "haste": "panorama/images/spellicons/rune_haste_png.vtex_c",
    "doubledamage": "panorama/images/spellicons/rune_doubledamage_png.vtex_c",
    "invisibility": "panorama/images/spellicons/rune_invis_png.vtex_c",
    "regeneration": "panorama/images/spellicons/rune_regen_png.vtex_c",
    "arcane": "panorama/images/spellicons/rune_arcane_png.vtex_c",
    "shield": "panorama/images/spellicons/rune_shield_png.vtex_c",
    "power": "panorama/images/hud/timer/power_rune_png.vtex_c",
}
OUT = os.path.join(_ROOT, "icons", "runes")


def main():
    import extract_vpk_icons as vpk
    entries, base = vpk.read_tree(vpk.DEFAULT_VPK)
    os.makedirs(OUT, exist_ok=True)
    for key, path in SOURCES.items():
        if path not in entries:
            print("MISSING", key, path)
            continue
        img = vpk.decode(vpk.read_file(vpk.DEFAULT_VPK, path, entries, base))
        img.save(os.path.join(OUT, f"{key}.png"))
        print(key, img.size)
    import shutil
    shutil.copyfile(os.path.join(_ROOT, "icons", "ui", "gothic", "tc_rune_3.png"), os.path.join(OUT, "illusion.png"))
    print("illusion <- icons/ui/gothic/tc_rune_3.png")


if __name__ == "__main__":
    main()
