"""gen_camp_icons.py — the pictures of a camp's icon in camp_table (owner 2026-11-19, style "A" + counter "P1"):

    icons/camps/creepcamp_<type>_22.png   the game's camp-type glyph (icons/camps/creepcamp_<type>.png, 32 px) as a
                                          crisp 22 px file: the same drawing, empty margins cut, every pixel snapped
                                          to the original's own colours, hard edge (the 32 px file shown at 22 blurs)
    icons/camps/faces/<creep>.png         each neutral creep's whole face, 34x22 in a gold chamfered frame: the
                                          full height and most of the width of its game portrait (icons/units)
    icons/camps/count_<n>.png             the count of a repeated creep: a big 5x7 pixel digit on a dark plate (9x11)
    ...@2x.png                            each of them doubled pixel for pixel, for sharp screens

Run after a new neutral creep's portrait lands in icons/units:
    python scripts/gen/gen_camp_icons.py
Pillow only; the output is the same on every run.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
UNITS = ROOT / "icons" / "units"
CAMPS = ROOT / "icons" / "camps"
FACES = CAMPS / "faces"

S = 22
FACE_W = 34
INK = (13, 13, 12)
GOLD = (227, 196, 106)
GOLD_LT = (247, 228, 160)
GOLD_DK = (138, 108, 46)
TYPES = ("small", "mid", "big", "ancient")
PORTRAIT = (512, 288)          # portraits come as 128x72 or 512x288; both are brought to 512x288 first
# every creep a camp_table shows (a new camp's creeps go here, tests/test_camp_icons.py checks): the centre x of its
# face in the 512x288 portrait (picked by eye 2026-11-19)
FACE_CX = {"tadpole": 220, "froglet": 230, "froglet_mage": 270, "grown_frog": 260, "grown_frog_mage": 210,
           "ancient_frog": 250, "ancient_frog_mage": 310, "prowler_acolyte": 250, "prowler_shaman": 220,
           "radigull": 170, "odobenus_frostmage": 280, "odobenus_footman": 370, "eimermole_foreman": 220,
           "eimermole": 190, "ogre_seal": 300, "ogre_seal_pup": 250,
           # 7.42 "home jungle" camps (their make-up: server.dll 6984, the camp table at RVA 0x4C2E270)
           "kobold": 200, "kobold_tunneler": 220, "kobold_taskmaster": 256, "forest_troll_berserker": 256,
           "forest_troll_high_priest": 256, "gnoll_assassin": 256, "fel_beast": 256, "ghost": 256, "harpy_scout": 240,
           "harpy_storm": 256, "ogre_mauler": 220, "ogre_magi": 256, "giant_wolf": 220, "alpha_wolf": 200,
           "satyr_trickster": 280, "satyr_soulstealer": 256, "mud_golem": 256, "centaur_outrunner": 256,
           "centaur_khan": 240, "wildkin": 170, "enraged_wildkin": 300, "polar_furbolg_champion": 256,
           "polar_furbolg_ursa_warrior": 280, "satyr_hellcaller": 256, "dark_troll": 256, "dark_troll_warlord": 256}
DIGITS = {"2": ["11110", "00001", "00001", "01110", "10000", "10000", "11111"],
          "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
          "4": ["10001", "10001", "10001", "11111", "00001", "00001", "00001"],
          "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
          "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
          "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
          "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
          "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"]}


def save(img, path):
    """the 1x file and its pixel-doubled @2x twin"""
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(path.with_name(path.stem + "@2x.png"), optimize=True)


def _palette(im, n=10):
    opaque = Image.new("RGB", im.size)
    opaque.paste(im.convert("RGB"), (0, 0), im.getchannel("A").point(lambda v: 255 if v > 200 else 0))
    pal = opaque.quantize(n, method=Image.Quantize.MEDIANCUT).getpalette()[: n * 3]
    return [tuple(pal[i:i + 3]) for i in range(0, len(pal), 3)]


def type_icon(src):
    """the game glyph at 22 px: margins cut, shrunk, each pixel snapped to the source's colours, no soft edge"""
    pal = _palette(src)
    part = src.crop(src.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox())
    side = max(part.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(part, ((side - part.width) // 2, (side - part.height) // 2))
    small = sq.resize((S, S), Image.LANCZOS)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for y in range(S):
        for x in range(S):
            r, g, b, a = small.getpixel((x, y))
            if a >= 110:
                best = min(pal, key=lambda p: (p[0] - r) ** 2 + (p[1] - g) ** 2 + (p[2] - b) ** 2)
                out.putpixel((x, y), best + (255,))
    return out


def _chamfer_mask(w, h):
    m = Image.new("L", (w, h), 0)
    r, b, c = w - 1, h - 1, max(2, h // 6)
    ImageDraw.Draw(m).polygon([(c, 0), (r - c, 0), (r, c), (r, b - c), (r - c, b), (c, b), (0, b - c), (0, c)], fill=255)
    return m


def _edge(mask):
    w, h = mask.size

    def on(x, y):
        return 0 <= x < w and 0 <= y < h and mask.getpixel((x, y)) > 0
    for y in range(h):
        for x in range(w):
            if on(x, y):
                up, left, down, right = not on(x, y - 1), not on(x - 1, y), not on(x, y + 1), not on(x + 1, y)
                if up or left or down or right:
                    yield x, y, (up or left) and not (down or right)


def face(slug):
    """the creep's whole face in the gold chamfered frame, FACE_W x 22: the portrait's full height and most of its width
    (a square cut the faces, owner 2026-11-19 "у многих обрезаны лица … чуть вытянутее по ширине"); ink ring outside,
    gold ring inside, lit on the top and left"""
    im = Image.open(UNITS / f"npc_dota_neutral_{slug}.png").convert("RGB").resize(PORTRAIT, Image.LANCZOS)
    h = PORTRAIT[1]
    w = round(h * FACE_W / S)
    x0 = max(0, min(PORTRAIT[0] - w, FACE_CX[slug] - w // 2))
    im = im.crop((x0, 0, x0 + w, h)).resize((FACE_W, S), Image.LANCZOS)
    im = ImageEnhance.Sharpness(ImageEnhance.Contrast(im).enhance(1.12)).enhance(1.3)
    mask = _chamfer_mask(FACE_W, S)
    out = Image.new("RGBA", (FACE_W, S), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    ring = list(_edge(mask))
    inner = mask.copy()
    for x, y, _ in ring:
        out.putpixel((x, y), INK + (255,))
        inner.putpixel((x, y), 0)
    for x, y, lit in _edge(inner):
        out.putpixel((x, y), (GOLD_LT if lit else GOLD) + (255,))
    return out


def count_mark(n):
    """P1: the big pixel digit (light top, gold body) on a dark plate with the top-left corner cut"""
    w, h = 9, 11
    p = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    d.rectangle((1, 0, w - 1, h - 1), fill=INK)
    d.rectangle((0, 1, w - 1, h - 1), fill=INK)
    for y, row in enumerate(DIGITS[str(n)]):
        for x, c in enumerate(row):
            if c == "1":
                p.putpixel((2 + x, 2 + y), (GOLD_LT if y < 3 else GOLD) + (255,))
    return p


def main():
    for t in TYPES:
        save(type_icon(Image.open(CAMPS / f"creepcamp_{t}.png").convert("RGBA")), CAMPS / f"creepcamp_{t}_22.png")
    missing = [s for s in FACE_CX if not (UNITS / f"npc_dota_neutral_{s}.png").exists()]
    if missing:
        raise SystemExit(f"no portrait in {UNITS} for: {', '.join(missing)}")
    for slug in FACE_CX:
        save(face(slug), FACES / f"{slug}.png")
    for n in DIGITS:
        save(count_mark(int(n)), CAMPS / f"count_{n}.png")
    print(f"camp icons: 4 types, {len(FACE_CX)} faces, {len(DIGITS)} counts")


if __name__ == "__main__":
    main()
