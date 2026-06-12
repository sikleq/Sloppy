"""gen_chest_icon.py — turn icons/ref/chest.mp4 into the gold-palette gothic
"Items" tile icons:

    icons/ui/gothic/icon_chest.png   — closed chest (rest state)
    icons/ui/gothic/icon_chest.gif   — key flies in → inserts → turns → lid
                                       opens, chest squashes wider, gold light
                                       beam + treasure inside (hover state)

The source clip is colourful pixel art on a green background. We:
  1. key out the green (background + grass drop-shadow) to alpha;
  2. recolour everything to the site's gold luminance ramp (anchor #e3c46a),
     matching the rule that every icons/ui/gothic/ glyph is gold, not coloured;
  3. fade the top of the frame so the upward light beam dissolves toward the
     icon's top edge instead of hard-clipping;
  4. downscale to a crisp 64px pixel icon and assemble a non-looping GIF
     (plays once, holds open while hovered; reverts to the PNG on mouse-out).

Run once after dropping a new chest.mp4:
    python scripts/gen_chest_icon.py
Needs ffmpeg on PATH (frame extraction) + Pillow.
"""
import os
import subprocess
import glob
import tempfile
from PIL import Image

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_HERE, "icons", "ref", "chest.mp4")
_OUT_DIR = os.path.join(_HERE, "icons", "ui", "gothic")

# Fixed crop window into the 576x500 source — square so the icon isn't squashed.
# Sized so the CLOSED chest (the rest state, x190-360 keyed) fills ~82% of the
# cell width — as big as the sibling glyphs, instead of looking small. The chest
# is wide+short, so it anchors low and the light beam fills the space above it up
# to the top edge. The open lid flips out to x~415; sizing for the closed chest
# clips ~20px of that flip on a few transient frames — an accepted trade for a
# properly-sized rest icon (per request: match size even if the beam shrinks).
# (x0, y0, x1, y1)
CROP = (185, 147, 393, 355)           # 208 x 208
CELL = 64                             # final icon resolution (pixelated)

# Green-screen keys (background + the darker grass drop-shadow under the chest).
_BG = (105, 124, 63)
_SHADOW = (63, 86, 40)

# Gold luminance ramp, dark → light. Anchor = #e3c46a (the site's "sikle" gold).
_RAMP = [
    (26, 19, 9),       # near-black outline
    (74, 52, 24),      # dark bronze (wood shadow)
    (120, 86, 38),     # bronze (wood)
    (170, 134, 58),    # gold (trim)
    (227, 196, 106),   # anchor bright gold  #e3c46a
    (245, 224, 150),   # highlight (coins)
    (252, 243, 208),   # pale shine (beam / glints)
]

# Beam handling. The source light beam is one distinct saturated yellow,
# (214,195,58), different from the chest's wood/trim/coins — so we key it BY
# COLOUR (not luminance, which overlaps the gold trim) and only above the chest
# mouth (so coins of a similar hue inside stay solid). Keyed beam pixels become
# a faint glow fading from ~0 at the top edge up to _BEAM_ALPHA at the mouth.
_BEAM_RGB = (214, 195, 58)
_BEAM_TOL = 36             # colour distance to count as beam
_BEAM_MOUTH = 0.50         # fraction of cell height = chest mouth / coin line
_BEAM_ALPHA = 0.34         # opacity of the beam glow (vs 1.0) — visible, not solid
_BEAM_TOP_FADE = 0.14      # only the top this-fraction of the cell tapers to 0


def _is_beam(r, g, b):
    return (abs(r - _BEAM_RGB[0]) < _BEAM_TOL
            and abs(g - _BEAM_RGB[1]) < _BEAM_TOL
            and abs(b - _BEAM_RGB[2]) < _BEAM_TOL)


def _is_green(r, g, b):
    """True if the pixel is background green or grass shadow (→ transparent)."""
    if abs(r - _BG[0]) < 30 and abs(g - _BG[1]) < 30 and abs(b - _BG[2]) < 30:
        return True
    if abs(r - _SHADOW[0]) < 22 and abs(g - _SHADOW[1]) < 22 and abs(b - _SHADOW[2]) < 24:
        return True
    # generic green-dominant anti-aliased edge
    return g > r + 8 and g > b + 22 and g > 70


def _ramp_for(lum):
    """Map 0..255 luminance to a gold-ramp RGB."""
    idx = int(lum * (len(_RAMP) - 1) / 255 + 0.5)
    return _RAMP[max(0, min(len(_RAMP) - 1, idx))]


def _process(frame_path):
    """Crop → key green → gold-recolour → top beam-fade → downscale to CELL."""
    im = Image.open(frame_path).convert("RGBA").crop(CROP)
    px = im.load()
    W, H = im.size
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    op = out.load()
    mouth_px = _BEAM_MOUTH * H
    top_fade_px = _BEAM_TOP_FADE * H
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a < 24 or _is_green(r, g, b):
                continue
            lum = int(0.299 * r + 0.587 * g + 0.114 * b)
            nr, ng, nb = _ramp_for(lum)
            na = a
            # Above the chest mouth, beam-coloured pixels become a translucent
            # glow at a constant low opacity that stays VISIBLE all the way up to
            # the top edge (so the shaft reads as full-height), tapering to 0 only
            # in the top _BEAM_TOP_FADE band so it dissolves into the border
            # instead of hard-clipping. Coins below the mouth keep full opacity.
            if y < mouth_px and _is_beam(r, g, b):
                taper = 1.0 if y >= top_fade_px else max(0.0, y / top_fade_px)
                na = int(a * _BEAM_ALPHA * taper)
            if na <= 0:
                continue
            op[x, y] = (nr, ng, nb, na)
    # Downscale: shrink with BOX for clean averaging, then snap colours back to
    # the ramp so the result is crisp (not muddy) at icon size.
    small = out.resize((CELL, CELL), Image.BOX)
    sp = small.load()
    for y in range(CELL):
        for x in range(CELL):
            r, g, b, a = sp[x, y]
            if a < 24:
                sp[x, y] = (0, 0, 0, 0)
                continue
            lum = int(0.299 * r + 0.587 * g + 0.114 * b)
            nr, ng, nb = _ramp_for(lum)
            # Solid body snaps to full opacity for crisp edges; the translucent
            # beam glow (low alpha from the upper region) keeps its alpha.
            na = 255 if a > 170 else a
            sp[x, y] = (nr, ng, nb, na)
    return small


def main():
    if not os.path.exists(_SRC):
        raise SystemExit(f"missing {_SRC}")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffmpeg", "-y", "-i", _SRC, "-vf", "fps=20", os.path.join(tmp, "f%03d.png")],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        frames = sorted(glob.glob(os.path.join(tmp, "f*.png")))
        if not frames:
            raise SystemExit("ffmpeg produced no frames")

        # Closed chest (rest PNG): frame 0 — chest shut, no key yet.
        closed = _process(frames[0])
        closed.save(os.path.join(_OUT_DIR, "icon_chest.png"))

        # Animation frame selection + per-frame timing (ms):
        n = len(frames)

        def at(i):
            return frames[min(i, n - 1)]

        cache = {}

        def build(seq):
            imgs, durs = [], []
            for idx, dur in seq:
                if idx not in cache:
                    cache[idx] = _process(at(idx))
                imgs.append(cache[idx])
                durs.append(dur)
            return imgs, durs

        def save_apng(name, seq, loop):
            imgs, durs = build(seq)
            imgs[0].save(
                os.path.join(_OUT_DIR, name),
                save_all=True, append_images=imgs[1:], duration=durs,
                loop=loop, disposal=1, blend=0, format="PNG")
            return imgs, durs

        # One animation can't play an intro once then loop only its tail, so we
        # emit TWO APNGs (same trick as the mana icon's fill+wave GIFs):
        #   • icon_chest_open.png — INTRO: key flies in, inserts, turns, lid
        #     opens & the chest settles fully open. Plays once (loop=1), ending
        #     on the open chest. Output APNG (not GIF): GIF's 1-bit transparency
        #     would turn the translucent beam into a solid block; APNG keeps real
        #     per-pixel alpha so the beam glows over the parchment slot.
        #   • icon_chest_loop.png — LOOP: the open chest with the light beam and
        #     the gold glints twinkling (src frames ~50-88, before the lid starts
        #     to close), looping forever (loop=0). Its first frame == the intro's
        #     last frame so the JS swap is seamless.
        # Two things must be settled before the loop, or its seam jerks:
        #   • the BEAM ramps up over src frames 46-52, then constant 52..88;
        #   • the chest BODY keeps its open-squash extra width (x190-420) at
        #     frames 50-52, then settles to its steady width (x195-415) by 53+.
        # So the loop must start AND end inside the fully-settled window (54..88):
        # frame 54 (settled body, full beam, steady width) == the loop's first
        # AND the intro's last frame, and 88 (same width + beam) is the last loop
        # frame → 88→54 is a clean seam, only the small gold glints twinkle.
        intro = []
        for i in range(0, 45, 3):          # key flies in + inserts + turns (fast)
            intro.append((i, 34))
        for i in range(45, 55):            # lid opens, squashes, beam ignites,
            intro.append((i, 55))          # body settles — ends at frame 54
        intro_imgs, intro_durs = save_apng("icon_chest_open.png", intro, loop=1)
        intro_ms = sum(intro_durs)

        loop = []
        for i in range(54, 89, 2):         # settled open chest: beam + glint twinkle
            loop.append((i, 70))           # 54 == intro's last frame (seamless)
        save_apng("icon_chest_loop.png", loop, loop=0)

        print(f"  -> icon_chest.png (closed) + icon_chest_open.png intro "
              f"({len(intro_imgs)} frames, {intro_ms}ms) + icon_chest_loop.png "
              f"({len(loop)} frames, looping)")
        print(f"     scripts.js INTRO_MS should be {intro_ms}")


if __name__ == "__main__":
    main()
