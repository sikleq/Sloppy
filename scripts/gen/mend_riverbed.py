"""Take out a pale riverbed patch that shows through the water in a full map render, keeping the water's own detail.

Why (the owner 2026-11-19, the 7.42 mid by the Radiant stairs: "a strange extra corner", not seen in the game): the
7.42 map's Dire riverbed (dark 64-unit tiles at z 0) leaves out a corner at (-256, -256), and the lighter Radiant
riverbed under it shows through the water in SFM's straight-down light as a pale area with dead-straight edges. It
is map geometry — no console variable or particle hides it — so the stitched picture is mended.

The patch is the water plus an extra brightness that rises towards the sharp sides (where the Dire tiles stop) and
fades towards the soft ones. For each sharp side in turn, along every line across the box, the patch's smoothed
brightness (blurred along the side only, never across the box's edge) is brought onto a straight line from its
value at the soft side to the water's value just past the sharp side; the excess is subtracted, fading out near the
other axis's soft sides. Ripples and stones stay (only the smoothed part moves), and the straight edge is gone.
First tries that failed: replacing the blurred brightness by a smooth fill (the step's own sharp part stayed in the
detail), and carrying the step measured at the edge inwards (the patch brightens towards the edge, a pale strip
stayed). Boxes are per map file, in world units (FIXES), with their sharp sides ("l", "r", "t", "b"); placed on the
7.42 render with the riverbed meshes as a guide (Sloppy docs/terrain.md, "Riverbed corner at mid").

    python scripts/gen/mend_riverbed.py IN_full.png OUT_DIR SHA8
    -> OUT_DIR/map_SHA8_sfm_full.png + map_SHA8_sfm.webp (4096, as stitch_sfm.py writes them)
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
UPP = 2.0                 # game units per pixel of the full picture
BLUR = 5                  # px: what counts as "large-scale" brightness
FADE = 10                 # px: how far the correction fades out from a soft side
MARGIN = 24               # px of water around a box
STEP = 4                  # px past a sharp side where the water's brightness is read
# map file (sha1[:8]) -> boxes (x0, x1, y0, y1, sharp sides) in world units. The render puts the tile edge at -253,
# not the mesh's -256 (measured: the step lies between the picture columns of x -254 and -252, rows of y -254 and
# -252). The small bluish slab with a bright rim at (-440, -186) is a stone under the water (the Radiant riverbed's
# slanted tiles), not touched.
_MID_742 = [(-326, -252, -446, -252, "rt")]        # the pale corner left of x -253, below y -253
FIXES = {"118cfcea": _MID_742,                     # 7.42
         "0d7217cc": _MID_742,                     # 7.42-v2: the same riverbed
         "51dc118a": _MID_742}                     # 7.42-v3 (build 6980): the same riverbed


def _ramp(n, sharp_lo, sharp_hi, fade):
    """1-D weight over a box side to side: 1 inside, falling to 0 over `fade` px towards a soft side."""
    i = np.arange(n, dtype=np.float32)
    w = np.ones(n, np.float32)
    if not sharp_lo:
        w = np.minimum(w, (i + 0.5) / fade)
    if not sharp_hi:
        w = np.minimum(w, (n - i - 0.5) / fade)
    return np.clip(w, 0, 1)


def _flatten(win, inside, axis, sharp_hi):
    """Along each line across the box (axis 1: rows, the sharp side left or right; axis 0: columns, top or bottom),
    the patch's smoothed brightness is brought onto a straight line from its value at the soft side to the water's
    value just across the sharp side. Returns the brightness to subtract (>= 0), 0 outside the box."""
    m = MARGIN
    along = (3 * BLUR, 1, 0) if axis == 1 else (1, 3 * BLUR, 0)
    w = ndimage.gaussian_filter(inside.astype(np.float32), along[:2])
    patch = ndimage.gaussian_filter(win * inside[..., None], along) / np.maximum(w, 1e-3)[..., None]
    wo = ndimage.gaussian_filter((~inside).astype(np.float32), along[:2])
    water = ndimage.gaussian_filter(win * (~inside)[..., None], along) / np.maximum(wo, 1e-3)[..., None]
    if axis == 0:                                   # work on rows: transpose columns into rows
        patch, water = patch.transpose(1, 0, 2), water.transpose(1, 0, 2)
    n = patch.shape[1] - 2 * m                      # box width along the line
    t = (np.arange(n, dtype=np.float32) + 0.5) / n  # 0 at the low side, 1 at the high side
    if sharp_hi:
        start, end = patch[:, m], water[:, m + n + STEP]
    else:
        start, end = water[:, m - STEP], patch[:, m + n - 1]
        t = 1 - t
        start, end = end, start
    line = start[:, None] + (end - start)[:, None] * t[None, :, None]
    extra = np.zeros_like(patch)
    extra[:, m:m + n] = np.clip(patch[:, m:m + n] - line, 0, None)
    extra *= inside.transpose(1, 0)[..., None] if axis == 0 else inside[..., None]
    return extra.transpose(1, 0, 2) if axis == 0 else extra


def mend_box(img, box_px, sharp):
    """img: float32 HxWx3 (changed in place); box_px: (c0, c1, r0, r1); sharp: sides with a hard edge
    (at most one of l/r and one of t/b). Each sharp side is flattened in turn; the correction fades out over FADE
    px towards the soft sides along the other axis, so nothing new appears there."""
    c0, c1, r0, r1 = box_px
    win = img[r0 - MARGIN:r1 + MARGIN, c0 - MARGIN:c1 + MARGIN]
    inside = np.zeros(win.shape[:2], bool)
    inside[MARGIN:-MARGIN, MARGIN:-MARGIN] = True
    h, w = r1 - r0, c1 - c0
    for side in sharp:
        axis = 1 if side in "lr" else 0
        extra = _flatten(win, inside, axis, side in "rb")
        fade = np.zeros(win.shape[:2], np.float32)
        if axis == 1:                               # fade along the column direction (rows) at soft top/bottom
            fade[MARGIN:-MARGIN, MARGIN:-MARGIN] = _ramp(h, "t" in sharp, "b" in sharp, FADE)[:, None]
        else:
            fade[MARGIN:-MARGIN, MARGIN:-MARGIN] = _ramp(w, "l" in sharp, "r" in sharp, FADE)[None, :]
        win -= extra * fade[..., None]


def mend(arr, sha8, rect=None, upp=UPP):
    """arr: HxWx3 uint8 full picture; returns the mended copy (unchanged when the map file has no fix)."""
    boxes = FIXES.get(sha8)
    if not boxes:
        return arr
    x0, _x1, _yb, yt = rect or world_rect()
    img = arr.astype(np.float32)
    for bx0, bx1, by0, by1, sharp in boxes:
        box = (int(round((bx0 - x0) / upp)), int(round((bx1 - x0) / upp)),
               int(round((yt - by1) / upp)), int(round((yt - by0) / upp)))
        mend_box(img, box, sharp)
    return np.clip(img + 0.5, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("full")
    ap.add_argument("out_dir")
    ap.add_argument("sha8")
    args = ap.parse_args()
    if args.sha8 not in FIXES:
        raise SystemExit(f"no riverbed fix for {args.sha8} (FIXES: {', '.join(FIXES)})")
    arr = np.asarray(Image.open(args.full).convert("RGB"))
    full = Image.fromarray(mend(arr, args.sha8))
    full.save(os.path.join(args.out_dir, f"map_{args.sha8}_sfm_full.png"))
    full.resize((SITE_PX, SITE_PX), Image.LANCZOS).save(
        os.path.join(args.out_dir, f"map_{args.sha8}_sfm.webp"), "WEBP", quality=88, method=6)
    print("mended", args.sha8, len(FIXES[args.sha8]), "boxes ->", args.out_dir)


if __name__ == "__main__":
    main()
