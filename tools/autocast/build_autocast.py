"""The in-game autocast ring, rebuilt from Dota's own particle system and baked into a looping
animated WebP (icons/ui/autocast.webp) — near-zero CPU on the page, unlike the old SVG snake.

Source (decompiled with Source2Viewer-CLI from pak01_dir.vpk):
  particles/ui/hud/autocasting_square.vpcf  -> children:
  - autocasting_child.vpcf         "glow": 24 particles/s born on the 40-point square snapshot
    (particles/models/particle/square_trace_40_points_fx.vsnap: an 80x80 square, 8-unit steps,
    walked in reverse), lifetime 1s, alpha 0 -> 1 -> 0 (FadeAndKill), radius 8 x 3 -> x 1,
    colour (255,222,138) -> (210,84,0), random rotation, drifts outward (sphere r<=12,
    speed 12-24). Texture materials/particle/lava_pool_glow (a fiery crackle of veins).
  - autocasting_child_embers.vpcf  "embers": 24/s on the same points, lifetime 0.3-0.9s,
    radius 4-9 -> 0, fade in <=0.1s / out 0.3-0.5s, random force +-150, oscillation +-32
    @ <=2Hz, drag 0.05, colour (255,228,120) -> (255,102,13), additive, overbright x3.
    Texture materials/particle/yellowflare.
The camera looks down the z axis, so the embers' +z gravity is toward the viewer (no screen drift).

One lap = 40 points / 24 per s = 1.667 s. Every random draw is keyed to the birth point, so the
system is exactly periodic after warm-up and the loop has no seam.

    python tools/autocast/build_autocast.py      # -> icons/ui/autocast.webp (+ out/preview.png)
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT_WEBP = os.path.join(ROOT, "icons", "ui", "autocast.webp")
TEX = os.path.join(HERE, "tex")          # lava_pool_glow.png, yellowflare.png (decompiled)

SQUARE = 80.0                             # snapshot square side, game units
UNITS_PER_PX = 80.0 / 56.0                # the 80-unit square = 56 px (2x a 28 px icon; hover zoom is 1.8x)
SIZE = 100                                # frame side, px (square + room for glow/embers)
FPS = 24
RATE = 24.0                               # particles / s, both children
LAP = 40 / RATE                           # 1.667 s
FRAMES = 40                               # = one lap at 24 fps
# The game draws this on a ~64 px HUD button with HDR bloom; our icons are 26 px, where the thin
# glow veins break into dust and the embers into single pixels. Perceptual compensation only
# (the motion, timing, colours and counts stay the game's):
GLOW_GAIN = 1.9                           # glow alpha x (veins survive the downscale)
EMBER_SCALE = 1.5                         # ember sprites x (at least ~2 px at 1x)
BLOOM = 0.9                               # soft bloom added back (the game's HDR glow)
VEIN_GAMMA = 0.55                         # glow texture alpha ** gamma: thicker veins

GLOW_C0, GLOW_C1 = np.array([255, 222, 138]) / 255, np.array([210, 84, 0]) / 255
EMB_C0, EMB_C1 = np.array([255, 228, 120]) / 255, np.array([255, 102, 13]) / 255


def snapshot_points():
    """The 40 points of square_trace_40_points_fx, in file order."""
    pts = []
    for i in range(10):
        pts.append((-40 + 8 * i, -40))
    for i in range(10):
        pts.append((40, -40 + 8 * i))
    for i in range(10):
        pts.append((40 - 8 * i, 40))
    for i in range(10):
        pts.append((-40, 40 - 8 * i))
    return pts


class Stamp:
    """Pre-scaled, pre-rotated sprite cache (radius in px, angle quantised to 15 degrees)."""
    def __init__(self, fname, luminance_alpha):
        self.src = Image.open(os.path.join(TEX, fname)).convert("RGBA")
        self.lum = luminance_alpha
        self.cache = {}

    def get(self, r_px, angle):
        d = max(2, int(round(r_px * 2)))
        key = (d, int(angle // 15) % 24)
        if key not in self.cache:
            im = self.src.rotate(key[1] * 15, resample=Image.BICUBIC).resize((d, d), Image.LANCZOS)
            a = np.asarray(im).astype(np.float32) / 255.0
            # glow texture: white RGB + alpha falloff; flare: colour on black, alpha from brightness
            # glow veins: gamma-thickened so the crackle survives a 26 px icon (see GLOW_GAIN)
            self.cache[key] = (a[..., 3] ** VEIN_GAMMA) if not self.lum else a[..., :3].max(axis=2)
        return self.cache[key]


def rnd(seed, k):
    return random.Random(seed * 7919 + k).random()


def simulate(t):
    """All live particles at time t (s): list of (kind, x, y, radius_units, alpha, rgb, angle)."""
    pts = snapshot_points()[::-1]                      # m_bReverse = true
    out = []
    n_back = int(1.0 * RATE) + 2                       # particles younger than 1 s
    k_now = int(math.floor(t * RATE))
    for k in range(k_now - n_back, k_now + 1):
        born = k / RATE
        age = t - born
        if age < 0:
            continue
        idx = k % 40
        px, py = pts[idx]
        # ---- glow child (lifetime 1 s)
        if age < 1.0:
            life = age / 1.0
            u = rnd(idx, 1) * 2 - 1
            th = rnd(idx, 2) * 2 * math.pi
            s2 = math.sqrt(max(0.0, 1 - u * u))
            dirx, diry = s2 * math.cos(th), s2 * math.sin(th)      # projected 3D direction
            r0 = 12 * rnd(idx, 3) ** (1 / 3)
            spd = 12 + 12 * rnd(idx, 4)
            x = px + dirx * (r0 + spd * age)
            y = py + diry * (r0 + spd * age)
            radius = 8 * (3 + (1 - 3) * life)                     # x3 -> x1
            alpha = life / 0.5 if life < 0.5 else (1 - life) / 0.5  # FadeAndKill 0->1->0
            alpha = min(1.0, alpha * GLOW_GAIN)
            rgb = GLOW_C0 + (GLOW_C1 - GLOW_C0) * life
            out.append(("glow", x, y, radius, max(0.0, alpha), rgb, rnd(idx, 5) * 360))
        # ---- ember child
        lifetime = 0.3 + 0.6 * rnd(idx, 11)
        if age < lifetime:
            life = age / lifetime
            fx = (rnd(idx, 12) * 2 - 1) * 150
            fy = (rnd(idx, 13) * 2 - 1) * 150
            drag = 0.95
            x = px + 0.5 * fx * age * age * drag
            y = py + 0.5 * fy * age * age * drag
            fr = 2 * rnd(idx, 14)
            x += (rnd(idx, 15) * 2 - 1) * 32 / (2 * math.pi * max(fr, 0.3)) * math.sin(2 * math.pi * fr * age)
            y += (rnd(idx, 16) * 2 - 1) * 32 / (2 * math.pi * max(fr, 0.3)) * math.sin(2 * math.pi * fr * age)
            radius = (4 + 5 * rnd(idx, 17)) * (1 - life) * EMBER_SCALE
            fin = 0.1 * rnd(idx, 18)
            fout = 0.3 + 0.2 * rnd(idx, 19)
            alpha = min(1.0, age / fin if fin > 0 else 1.0, (lifetime - age) / fout)
            rgb = EMB_C0 + (EMB_C1 - EMB_C0) * life
            out.append(("ember", x, y, radius, max(0.0, alpha), rgb, rnd(idx, 20) * 360))
    return out


def render(t, glow, flare):
    col = np.zeros((SIZE, SIZE, 3), np.float32)      # premultiplied colour
    alp = np.zeros((SIZE, SIZE), np.float32)
    c = SIZE / 2
    parts = simulate(t)
    for kind in ("glow", "ember"):                   # glow first, embers added on top
        for k, x, y, r, a, rgb, ang in parts:
            if k != kind or a <= 0 or r <= 0:
                continue
            r_px = r / UNITS_PER_PX
            m = (glow if k == "glow" else flare).get(r_px, ang)
            d = m.shape[0]
            cx = c + x / UNITS_PER_PX - d / 2
            cy = c + y / UNITS_PER_PX - d / 2
            x0, y0 = int(round(cx)), int(round(cy))
            x1, y1 = max(0, x0), max(0, y0)
            x2, y2 = min(SIZE, x0 + d), min(SIZE, y0 + d)
            if x1 >= x2 or y1 >= y2:
                continue
            mm = m[y1 - y0:y2 - y0, x1 - x0:x2 - x0] * a
            if k == "glow":                          # alpha blend
                col[y1:y2, x1:x2] = rgb * mm[..., None] + col[y1:y2, x1:x2] * (1 - mm[..., None])
                alp[y1:y2, x1:x2] = mm + alp[y1:y2, x1:x2] * (1 - mm)
            else:                                    # additive, overbright x3
                col[y1:y2, x1:x2] += rgb * mm[..., None] * 3.0
                alp[y1:y2, x1:x2] = np.minimum(1.0, alp[y1:y2, x1:x2] + mm * 1.5)
    # bloom: blur the premultiplied light and add it back (colour + coverage)
    pre = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(3))
    bl = np.asarray(pre).astype(np.float32) / 255.0 * BLOOM
    col = col + bl
    alp = np.maximum(alp, np.clip(bl.max(axis=2) * 1.2, 0, 1))
    rgb = np.clip(col / np.maximum(alp[..., None], 1e-4), 0, 1)
    out = np.dstack([rgb, np.clip(alp, 0, 1)])
    return Image.fromarray((out * 255).astype(np.uint8), "RGBA")


def main():
    glow = Stamp("lava_pool_glow.png", luminance_alpha=False)
    flare = Stamp("yellowflare.png", luminance_alpha=True)
    warm = 2 * LAP                                   # start after warm-up: exactly periodic
    frames = [render(warm + i / FPS, glow, flare) for i in range(FRAMES)]
    os.makedirs(os.path.dirname(OUT_WEBP), exist_ok=True)
    frames[0].save(OUT_WEBP, save_all=True, append_images=frames[1:], duration=int(1000 / FPS),
                   loop=0, lossless=False, quality=76, method=6)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    sheet = Image.new("RGBA", (SIZE * 8, SIZE * 2), (22, 26, 32, 255))
    for i in range(16):
        sheet.alpha_composite(frames[i * 2], ((i % 8) * SIZE, (i // 8) * SIZE))
    sheet.save(os.path.join(HERE, "out", "preview.png"))
    print(f"  -> {OUT_WEBP}: {len(frames)} frames, {os.path.getsize(OUT_WEBP) // 1024} KB")
    demo(frames)


def demo(frames, icon="forest_troll_high_priest_heal", out="icons/changelog/2026-09-24_autocast.webp"):
    """Changelog demo: a real ability icon with the effect running round it (screen blend, 3x)."""
    from PIL import ImageChops
    ic_px = 56 * 3 // 2                                   # icon = the 80-unit square
    box = SIZE * 3 // 2
    icon_im = Image.open(os.path.join(ROOT, "icons", "abilities", f"{icon}.png")).convert("RGB").resize((ic_px, ic_px), Image.LANCZOS)
    shots = []
    for fr in frames:
        base = Image.new("RGB", (box, box), (14, 18, 23))
        base.paste(icon_im, ((box - ic_px) // 2, (box - ic_px) // 2))
        f = fr.resize((box, box), Image.LANCZOS)
        light = Image.new("RGB", f.size, (0, 0, 0))
        light.paste(f.convert("RGB"), mask=f.split()[3])
        shots.append(ImageChops.screen(base, light))
    path = os.path.join(ROOT, out)
    shots[0].save(path, save_all=True, append_images=shots[1:], duration=int(1000 / FPS), loop=0, quality=80, method=6)
    print(f"  -> {out}: demo")


if __name__ == "__main__":
    main()
