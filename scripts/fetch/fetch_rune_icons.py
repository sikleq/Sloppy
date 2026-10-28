"""The runes' icons for the patch rows (owner 2026-10-28: 7.40 "Bounty Rune: …", "Haste Rune: …" rows show the rune's
icon, its name on hover — like a facet row's ability icon).

    python scripts/fetch/fetch_rune_icons.py        -> icons/runes/<key>.png

The game has 10 runes (data/abilities_english.txt DOTA_Tooltip_rune_*): Bounty, Haste, Amplify Damage (Double
Damage), Illusion, Invisibility, Regeneration, Arcane, Shield, Water, Wisdom (removed in 7.38). One style for all —
the game's minimap icons, as the Terrain page already shows them (owner 2026-10-28: "в terrain всё есть кроме
wisdom/water, придерживаемся этого, остальные докачиваем"):
- the 7 power runes and Bounty: copied from the Terrain page's icons (icons/ui/gothic/tc_rune_0..6, tc_bounty —
  scripts/gen/gen_terrain_layer_icons.py, from the Liquipedia map icons in icons/ref/);
- water.png, wisdom.png: "<Name> Rune mapicon dota2 gameasset.png" from Liquipedia's Runes page, downloaded once
  through tools/liquipedia_cache.py's throttle and kept here (this script does not touch them);
- no icon for the power runes as a whole: the client's HUD power-rune timer icon is the Water rune (owner
  2026-10-28), and the Terrain page has none either (its button cycles the 7 runes) — a "Power Rune: …" row keeps
  its words.
"""
import os
import shutil

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# rune -> the Terrain page's icon of it (gen_terrain_layer_icons.RUNE_ORDER: amplify, arcane, haste, illusion,
# invisibility, regeneration, shield)
TERRAIN = {"doubledamage": "tc_rune_0", "arcane": "tc_rune_1", "haste": "tc_rune_2", "illusion": "tc_rune_3",
           "invisibility": "tc_rune_4", "regeneration": "tc_rune_5", "shield": "tc_rune_6", "bounty": "tc_bounty"}
OUT = os.path.join(_ROOT, "icons", "runes")


def main():
    os.makedirs(OUT, exist_ok=True)
    for key, name in TERRAIN.items():
        shutil.copyfile(os.path.join(_ROOT, "icons", "ui", "gothic", f"{name}.png"), os.path.join(OUT, f"{key}.png"))
        print(key, "<-", name)
    for key in ("water", "wisdom"):
        print(key, "kept" if os.path.exists(os.path.join(OUT, f"{key}.png")) else "MISSING (Liquipedia map icon)")


if __name__ == "__main__":
    main()
