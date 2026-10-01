"""The colour look of our in-game map pictures (the owner 2026-10-01: "our map is too bright, it should look like
leamare's"). The game shows the map warmer and more saturated (lime grass, orange sand, light tree shadows) than
leamare's SFM renders. The look is carried over once, on 7.41, and kept as a colour lookup table
(data/map/tone_lut.png) that every picture we shoot goes through — older builds have no reference to fit on.

How: the colours of our 7.41 picture are moved onto the colours of leamare's 7.41 picture by iterative
distribution transfer (Pitié et al. 2005: rotate the RGB cube at random, match the three 1-D histograms, repeat),
which matches the whole spread of colours — a least-squares fit of pixel against pixel was tried first and washed
the picture out (it pulls every colour towards the average). The transfer is baked into a 33x33x33 table, applied
with PIL's Color3DLUT.

    python scripts/gen/tone_match.py fit   OURS.png REFERENCE.webp      # → data/map/tone_lut.png
    python scripts/gen/tone_match.py apply IN.png OUT.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

Image.MAX_IMAGE_PIXELS = None
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LUT = os.path.join(_ROOT, "data", "map", "tone_lut.png")
SIZE = 33              # table points per channel
SAMPLE_PX = 512        # both pictures are sampled at this size
DARK = 10              # pixels darker than this (the void past the map) take no part
ROUNDS = 30
QUANTILES = 256


def _colours(path):
    im = Image.open(path).convert("RGB").resize((SAMPLE_PX, SAMPLE_PX), Image.LANCZOS)
    px = np.asarray(im, np.float64).reshape(-1, 3) / 255
    return px[px.max(axis=1) * 255 > DARK]


def _rotations(rounds, seed=741):
    rng = np.random.default_rng(seed)
    for _ in range(rounds):
        q, r = np.linalg.qr(rng.normal(size=(3, 3)))
        yield q * np.sign(np.diag(r))


def fit(ours, ref):
    """The steps of the transfer: [(rotation, source quantiles, target quantiles)] per round."""
    src, dst = _colours(ours), _colours(ref)
    qs = np.linspace(0, 1, QUANTILES)
    steps = []
    for rot in _rotations(ROUNDS):
        a, b = src @ rot, dst @ rot
        qa, qb = np.quantile(a, qs, axis=0), np.quantile(b, qs, axis=0)
        for j in range(3):
            a[:, j] = np.interp(a[:, j], qa[:, j], qb[:, j])
        src = a @ rot.T
        steps.append((rot, qa, qb))
    return steps


def transfer(colours, steps):
    """Colours (N, 3) in 0..1 through the fitted steps."""
    c = colours.copy()
    for rot, qa, qb in steps:
        a = c @ rot
        for j in range(3):
            a[:, j] = np.interp(a[:, j], qa[:, j], qb[:, j])
        c = a @ rot.T
    return np.clip(c, 0, 1)


def table(steps):
    """The SIZE^3 lookup table, red changing fastest (PIL's Color3DLUT order)."""
    v = np.linspace(0, 1, SIZE)
    b, g, r = np.meshgrid(v, v, v, indexing="ij")
    grid = np.stack([r.ravel(), g.ravel(), b.ravel()], axis=1)
    return transfer(grid, steps)


def save(lut):
    """The table as a SIZE^2 x SIZE picture: pixel (r + SIZE*g, b)."""
    img = (lut.reshape(SIZE, SIZE * SIZE, 3) * 255 + 0.5).astype(np.uint8)
    os.makedirs(os.path.dirname(LUT), exist_ok=True)
    Image.fromarray(img).save(LUT)


def load():
    return np.asarray(Image.open(LUT).convert("RGB"), np.float64).reshape(-1, 3) / 255


def apply(im, lut=None):
    lut = load() if lut is None else lut
    return im.convert("RGB").filter(ImageFilter.Color3DLUT(SIZE, [tuple(c) for c in lut]))


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "fit":
        save(table(fit(sys.argv[2], sys.argv[3])))
        print("saved", LUT)
    elif len(sys.argv) == 4 and sys.argv[1] == "apply":
        apply(Image.open(sys.argv[2])).save(sys.argv[3])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
