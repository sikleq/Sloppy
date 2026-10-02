"""Do two full map renders differ beyond render noise? (The owner 2026-10-02: "if nothing changed in a patch,
there's nothing to compare".)

Two SFM renders of the very same ground are never pixel-equal: the trees sway, the water moves, particles differ.
At 8 units per pixel such noise makes blobs of up to ~600 px; a real change makes bigger ones (7.39 -> 7.39b, trees
planted and cut, a tower moved: blobs of 1000-3800 px). The Terrain pages skip a patch whose objects didn't move
and whose notes list nothing (builders/terrain.py `_quiet`) — this script is how that was checked against the
pictures: 7.39c/d/e, 7.40c, 7.41c/d/e/f all stay under 620 px.

    python scripts/gen/map_picture_diff.py OLD_full.png NEW_full.png
"""
import argparse

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
SCALE = 4                 # the full render is 2 units/px -> 8 units/px
THRESHOLD = 30            # a channel differs by more than this
NOISE_BLOB = 700          # px at 8 units/px: render noise stays below


def blobs(old, new, scale=SCALE, threshold=THRESHOLD):
    """Sizes (px, biggest first) of the regions where the two HxWx3 arrays differ, after shrinking by `scale`."""
    def small(a):
        im = Image.fromarray(a)
        return np.asarray(im.resize((im.width // scale, im.height // scale), Image.BOX), np.int16)
    d = np.abs(small(old) - small(new)).max(axis=2) > threshold
    d = ndimage.binary_opening(d, iterations=1)
    lab, n = ndimage.label(ndimage.binary_closing(d, iterations=2))
    return sorted(np.bincount(lab.ravel())[1:].tolist(), reverse=True) if n else []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    args = ap.parse_args()
    a = np.asarray(Image.open(args.old).convert("RGB"))
    b = np.asarray(Image.open(args.new).convert("RGB"))
    sizes = blobs(a, b)
    real = [s for s in sizes if s >= NOISE_BLOB]
    print(f"biggest differences (px at {2 * SCALE} units/px): {sizes[:8]}")
    print(f"{len(real)} bigger than render noise" if real else "nothing but render noise")


if __name__ == "__main__":
    main()
