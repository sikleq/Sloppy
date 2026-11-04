"""The runes' icons for the patch rows (owner 2026-10-28: 7.40 "Bounty Rune: …", "Haste Rune: …" rows show the rune's
icon, its name on hover — like a facet row's ability icon).

    python scripts/fetch/fetch_rune_icons.py        -> icons/runes/<key>.png

The game has 10 runes (data/abilities_english.txt DOTA_Tooltip_rune_*): Bounty, Haste, Amplify Damage (Double
Damage), Illusion, Invisibility, Regeneration, Arcane, Shield, Water, Wisdom (removed in 7.38). One style for all —
the game's minimap icons, as the Terrain page already shows them (owner 2026-10-28: "в terrain всё есть кроме
wisdom/water, придерживаемся этого, остальные докачиваем"):
- the 7 power runes, Bounty, Water and Wisdom: the game's map icons from Liquipedia, kept in icons/ref/runes (32 px, not in
  git), through tools/liquipedia_cache.py's throttle when they were downloaded;
- smoothed to 96 px with the colours premultiplied by their transparency, shown at 48: at 32 px with a hard black outline
  their edges were jagged (owner 2026-11-04: Invisibility, Wisdom); cut to their real edges and centred, each as large as
  the square allows (owner 2026-11-04: all runes alike);
- power.png, the power runes as a whole: the game has no icon for it (the client's HUD power-rune timer icon is the
  Water rune, owner 2026-10-28; the Terrain page's button cycles the 7 runes), so it is our own, drawn from three of
  the runes' icons by scripts/gen/gen_power_rune_icon.py (run it after this script; this one does not touch it).
"""
import os

import numpy as np
from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# rune -> its map icon in icons/ref/runes
SOURCE = {"doubledamage": "amplify_damage", "arcane": "arcane", "haste": "haste", "illusion": "illusion",
          "invisibility": "invisibility", "regeneration": "regeneration", "shield": "shield", "bounty": "bounty",
          "water": "water", "wisdom": "wisdom"}
REF = os.path.join(_ROOT, "icons", "ref", "runes")
OUT = os.path.join(_ROOT, "icons", "runes")
SIZE = 96
INNER = 88        # every rune's longer side: all fill the square alike, centred (owner 2026-11-04: Wisdom sat off-centre, small)
SOLID = 16        # a pixel this opaque counts for the rune's real edges: faint specks do not move them


def _scale(image, size):
    """The icon scaled with its colours premultiplied by alpha: no fringe from what lies under its transparent pixels."""
    rgba = np.asarray(image.convert("RGBA")).astype("float32") / 255
    rgba[..., :3] *= rgba[..., 3:]
    channels = [np.asarray(Image.fromarray(rgba[..., i]).resize(size, Image.LANCZOS)) for i in range(4)]
    out = np.stack(channels, -1).clip(0, 1)
    alpha = out[..., 3:]
    out[..., :3] = np.where(alpha > 1e-3, out[..., :3] / np.maximum(alpha, 1e-3), 0).clip(0, 1)
    return Image.fromarray((out * 255).round().astype("uint8"), "RGBA")


def fit(image):
    """The rune cut to its real edges, its longer side INNER px, in the middle of a SIZE px square."""
    image = image.convert("RGBA")
    box = image.getchannel("A").point(lambda v: 255 if v >= SOLID else 0).getbbox()
    rune = image.crop(box)
    k = INNER / max(rune.size)
    scaled = _scale(rune, (max(1, round(rune.width * k)), max(1, round(rune.height * k))))
    square = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    square.paste(scaled, ((SIZE - scaled.width) // 2, (SIZE - scaled.height) // 2))
    return square


def main():
    for key, name in SOURCE.items():
        fit(Image.open(os.path.join(REF, f"{name}.png"))).save(os.path.join(OUT, f"{key}.png"), optimize=True)
        print(key, "<-", name)


if __name__ == "__main__":
    main()
