"""Mend spots of a full map render with the same spots of another render whose ground there is unchanged.

Why (the owner 2026-10-02, "shouldn't this pink object be gone in 7.39?"): the 7.39 release map file holds two
"templar gates" (npc_dota_unit_templar_gate, the Twin Gate model with skin 2) that no patch note mentions and 7.39b
removed. The build we render pre-7.41 maps on (7.40c) has no material for that skin, so SFM draws them pink. 7.39b's
render has the very same ground there (no tree, camp or building of 7.39b moved within 900 units), so the spots are
taken from it: only the pixels that differ near each spot, so the wind in the trees and the moving water around stay
the 7.39 render's own.

    python scripts/gen/mend_map.py BAD_full.png DONOR_full.png OUT_DIR NAME --at=1874.7,-5074.7 --at=-1527.4,4000
    -> OUT_DIR/map_NAME_sfm_full.png + map_NAME_sfm.webp (4096, as stitch_sfm.py writes them)
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_map import SITE_PX, world_rect  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
UPP = 2.0                 # game units per pixel of the full picture (stitch_sfm.py --upp)
RADIUS = 180.0            # units around a spot that may be replaced: a 0.6-scaled Twin Gate is ~110 units across
THRESHOLD = 25            # a pixel differs when a channel differs by more than this


def pink(img):
    """The engine's missing-material colour: magenta-pink, any shade (hue 300-360 degrees, saturated)."""
    f = img.astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    return (r - g > 50) & (b - g > 15) & (r >= b) & (r > 90)


def spot_mask(bad, donor, centre, radius_px, threshold=THRESHOLD):
    """The pixels to take from the donor around one spot (centre = (col, row)): the pink object touching the spot's
    middle, holes filled, plus its rim and shadow (pixels within 6 px of it that differ from the donor). Only that:
    the ground around it keeps the bad render's own look even where the donor's patch changed it (7.39b painted
    grass where the 7.39 portal stood), and so does the render noise nearby (wind, water).
    Returns a float weight 0..1 with a soft edge."""
    h, w = bad.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    near = (xx - centre[0]) ** 2 + (yy - centre[1]) ** 2 <= radius_px ** 2
    pk = pink(bad) & near
    obj = ndimage.binary_closing(pk, iterations=2)
    labels, _n = ndimage.label(obj)
    core = labels[max(0, centre[1] - 15):centre[1] + 16, max(0, centre[0] - 15):centre[0] + 16]
    body = np.isin(labels, np.unique(core[core > 0]))
    # the model's thin spikes break off into specks of their own: every pink pixel within 20 px of the body
    keep = ndimage.binary_fill_holes(body | (ndimage.binary_dilation(body, iterations=20) & pk))
    diff = np.abs(bad.astype(np.int16) - donor.astype(np.int16)).max(axis=2) > threshold
    keep = keep | (ndimage.binary_dilation(keep, iterations=6) & diff)
    keep = ndimage.binary_dilation(ndimage.binary_fill_holes(keep), iterations=1) & near
    return np.clip(ndimage.gaussian_filter(keep.astype(np.float32), 1.0), 0, 1)


def mend(bad, donor, spots, rect, upp=UPP, radius=RADIUS):
    """bad/donor: HxWx3 uint8 arrays of the same full picture; spots: world (x, y). Returns the mended array."""
    x0, _x1, _yb, yt = rect
    out = bad.astype(np.float32)
    r = int(round(radius / upp))
    for x, y in spots:
        c, row = int(round((x - x0) / upp)), int(round((yt - y) / upp))
        top, left = max(0, row - r - 8), max(0, c - r - 8)
        win = (slice(top, row + r + 9), slice(left, c + r + 9))
        wgt = spot_mask(bad[win], donor[win], (c - left, row - top), r)[..., None]
        if not wgt.any():
            print(f"warning: nothing pink within 30 units of ({x}, {y}) — that spot is left as it was",
                  file=sys.stderr)
        out[win] = out[win] * (1 - wgt) + donor[win].astype(np.float32) * wgt
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bad")
    ap.add_argument("donor")
    ap.add_argument("out_dir")
    ap.add_argument("name")
    ap.add_argument("--at", action="append", required=True, help="x,y in game units")
    ap.add_argument("--radius", type=float, default=RADIUS)
    args = ap.parse_args()
    spots = [tuple(float(v) for v in a.split(",")) for a in args.at]
    bad = np.asarray(Image.open(args.bad).convert("RGB"))
    donor = np.asarray(Image.open(args.donor).convert("RGB"))
    if bad.shape != donor.shape:
        raise SystemExit(f"the pictures differ in size: {bad.shape} vs {donor.shape}")
    full = Image.fromarray(mend(bad, donor, spots, world_rect(), radius=args.radius))
    full.save(os.path.join(args.out_dir, f"map_{args.name}_sfm_full.png"))
    full.resize((SITE_PX, SITE_PX), Image.LANCZOS).save(
        os.path.join(args.out_dir, f"map_{args.name}_sfm.webp"), "WEBP", quality=88, method=6)
    print("mended", len(spots), "spots ->", args.out_dir)


if __name__ == "__main__":
    main()
