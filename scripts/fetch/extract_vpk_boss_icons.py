"""extract_vpk_boss_icons.py — Roshan, Tormentor and Courier art straight from the game VPK.

Roshan's and the Tormentor's ability icons (roshan_revengeroar, roshan_grab_and_throw,
miniboss_*) are not on Valve's web CDN, and neither is Roshan's portrait. The client has
them: panorama/images/spellicons/<slug>_png.vtex_c and
panorama/images/heroes/npc_dota_hero_roshan_png.vtex_c. Decoding reuses extract_vpk_icons.

    python scripts/fetch/extract_vpk_boss_icons.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_vpk_icons import DEFAULT_VPK, decode, read_file, read_tree  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ABILITIES = ["roshan_bash", "roshan_slam", "roshan_spell_block", "roshan_revengeroar", "roshan_grab_and_throw",
             "miniboss_unyielding_shield", "miniboss_reflect", "miniboss_radiance", "miniboss_alleviation",
             "miniboss_fortification",
             # Strength of the Immortal (roshan_devotion) is hidden and has no picture of its own yet
             "roshan_devotion",
             # lane creeps' abilities, for their cards in General Updates (2026-10-16, 7.40 Flagbearer Inspiration Aura)
             "flagbearer_creep_aura_effect"]
# An ability with no picture in the game shows the game's own placeholder, the grey Dota logo (owner 2026-11-07:
# "лучше не с ликвипедии брать и похожую иконку, а на плейсхолдер. В игре уже есть иконка для способностей без своей
# иконки"); a later build that gives it a picture replaces the placeholder on the next run.
PLACEHOLDER = "empty"
UNIT_SIZE = (128, 72)
UNITS = {"npc_dota_roshan": "panorama/images/heroes/npc_dota_hero_roshan_png.vtex_c",
         "npc_dota_miniboss": "panorama/images/heroes/npc_dota_tormentor_radiant_png.vtex_c",
         "npc_dota_courier": "panorama/images/items/courier_radiant_png.vtex_c"}


def spellicon(slug):
    return f"panorama/images/spellicons/{slug}_png.vtex_c"


def unit_portrait(img, dst):
    """A portrait cut to the size the site already has for it (the Tormentor's is square), else every portrait one
    size (the courier's icon is 88x64)."""
    size = Image.open(dst).size if dst.exists() else UNIT_SIZE
    return img if img.size == size else ImageOps.fit(img, size, Image.LANCZOS, centering=(0.5, 0.4))


def same_picture(img, dst):
    """The file already holds this picture: rewriting it would only change its bytes (2026-11-07: a run rewrote the
    Courier's and the Tormentor's portraits though the game's pictures were the same)."""
    if not dst.exists():
        return False
    old = Image.open(dst).convert("RGBA")
    return old.size == img.size and old.tobytes() == img.convert("RGBA").tobytes()


def main() -> int:
    entries, base = read_tree(DEFAULT_VPK)
    jobs = [((spellicon(s), spellicon(PLACEHOLDER)), ROOT / "icons" / "abilities" / f"{s}.png") for s in ABILITIES]
    jobs += [((src,), ROOT / "icons" / "units" / f"{name}.png") for name, src in UNITS.items()]
    missing = 0
    for sources, dst in jobs:
        img = None
        for internal in sources:
            try:
                img = decode(read_file(DEFAULT_VPK, internal, entries, base))
                break
            except KeyError:
                print(f"  missing in VPK: {internal}")
        if img is None:
            missing += 1
            continue
        if dst.parent.name == "units":
            if dst.exists():        # the site's portrait is cut by hand (the Tormentor's square): never rewritten
                continue
            img = unit_portrait(img, dst)
        if same_picture(img, dst):
            continue
        img.save(dst)
        print(f"  {dst.relative_to(ROOT)}  {img.size[0]}x{img.size[1]}  from {internal}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
