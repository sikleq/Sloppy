"""Our top-down map picture rendered in Source Filmmaker, as leamare's maps are (the owner 2026-10-01: "can we do it
through SFM?" — the in-game capture looked brighter and blurrier than leamare's).

The SFM session (kept outside the repo; see docs/terrain.md for its settings) flies a camera with a 1-degree lens
from 240000 units up over the map in a serpentine, one frame per second: 6 x 11 frames of 3840x2160, each ~4190 x
2360 units, ~15% overlap. With such a narrow lens the frames are near-orthographic, so each one is placed by the
camera's own position and orientation read from the session — no feature matching needed. SFM renders with
modelLod 0 and without the game's post-processing (SkipMainPipelinePostProcessing) — leamare's look, and none of the
in-game capture's orange camp glows, lime grass or blocky FSR upscaling.

    1. dota2.exe -tools -addon dotamapsfm → Tools → Source Filmmaker → open the session → File → Export → Movie
       (image sequence, PNG) into FRAMES
    2. python scripts/gen/stitch_sfm.py SESSION.dmx FRAMES 7.41 --work D:\\maprender
"""
import argparse
import json
import glob
import math
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_map import SITE_PX, world_rect  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
GAME = os.environ.get("DOTA_GAME", r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game")
GROUND_Z = 128.0          # typical ground height: the plane the frames are laid on


def session_text(path):
    """The session as KeyValues2 text (SFM saves binary; the game's dmxconvert converts)."""
    with open(path, "rb") as f:
        head = f.read(64)
    if b"keyvalues2" in head:
        return open(path, encoding="utf-8").read()
    out = os.path.join(tempfile.mkdtemp(), "session_text.dmx")
    subprocess.run([os.path.join(GAME, "bin", "win64", "dmxconvert.exe"), "-i", path, "-o", out,
                    "-oe", "keyvalues2"], check=True, capture_output=True)
    return open(out, encoding="utf-8").read()


def _array(name, block):
    m = re.search(r'"%s" "\w+_array"\s*\[(.*?)\]' % name, block, re.S)
    return [x.strip().strip('"') for x in m.group(1).split(",") if x.strip()]


def _float(name, text):
    return float(re.search(r'"%s" "float" "([-\d.e]+)"' % name, text).group(1))


def camera_path(text):
    """Per exported frame: (camera position, orientation quaternion x y z w), plus fov (deg) and the frame size."""
    pos_block = text[text.find('"name" "string" "transform_pos"'):]
    times = np.array([float(t) for t in _array("times", pos_block)])
    values = np.array([[float(v) for v in s.split()] for s in _array("values", pos_block)])
    rot_block = text[text.find('"name" "string" "transform_rot"'):]
    quat = [float(v) for v in _array("values", rot_block)[0].split()]
    chan = text[text.find('"name" "string" "animSetEditorChannels"'):]
    start = float(re.search(r'"start" "time" "([-\d.]+)"', chan).group(1))      # channel time = shot time - start
    movie = text[text.find('"movieSettings"'):]
    width = int(re.search(r'"width" "int" "(\d+)"', movie).group(1))
    height = int(re.search(r'"height" "int" "(\d+)"', movie).group(1))
    t0, t1 = _float("TimeRangeStartTime", text), _float("TimeRangeEndTime", text)
    fps = _float("frameRate", text)
    frames = []
    for k in range(int(round((t1 - t0) * fps))):
        t = t0 + k / fps - start
        frames.append(np.array([np.interp(t, times, values[:, a]) for a in range(3)]))
    return frames, quat, _float("fieldOfView", text), width, height


def _rotate(q, v):
    x, y, z, w = q
    u = np.array([x, y, z])
    v = np.asarray(v, float)
    return v + 2 * np.cross(u, np.cross(u, v) + w * v)


def footprints(frames, quat, fov, width):
    """Per frame: the ground point under the image centre, the world directions of image right / up, and the
    units per pixel on the ground plane."""
    fwd, left, up = _rotate(quat, [1, 0, 0]), _rotate(quat, [0, 1, 0]), _rotate(quat, [0, 0, 1])
    out = []
    for p in frames:
        dist = (p[2] - GROUND_Z) / -fwd[2]
        centre = p + fwd * dist
        upp = 2 * dist * math.tan(math.radians(fov) / 2) / width
        out.append((centre[:2], -left[:2], up[:2], upp))
    return out


def _shift(a, b):
    """How far frame b's picture is moved against frame a's (phase correlation of the whole frames)."""
    A = np.asarray(a.convert("L").reduce(2), np.float32)
    B = np.asarray(b.convert("L").reduce(2), np.float32)
    F = np.fft.fft2(A) * np.conj(np.fft.fft2(B))
    r = np.fft.ifft2(F / (np.abs(F) + 1e-9)).real
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    h, w = A.shape
    return 2 * (ix - w if ix > w // 2 else ix), 2 * (iy - h if iy > h // 2 else iy)


def measured_upp(frame_files, frames, pairs=8):
    """Units per pixel from neighbouring frames (the lens maths is off by ~0.1%: the ground isn't at one height)."""
    got = []
    for k in range(len(frames) - 1):
        d = frames[k + 1] - frames[k]
        if abs(d[1]) > 1 or abs(d[0]) < 1:                     # same row, next column only
            continue
        dx, dy = _shift(Image.open(frame_files[k]), Image.open(frame_files[k + 1]))
        w = Image.open(frame_files[k]).width
        px = dx - w if dx > 0 else dx                            # the shift wraps around the frame
        if abs(dy) <= 2 and px:
            got.append(abs(d[0]) / abs(px))
        if len(got) >= pairs:
            break
    return float(np.median(got)) if got else None


def _ramp(pos, lo, hi, blend, has_lo, has_hi):
    """Weight of a cell [lo, hi] at positions `pos`: 1 inside, falling linearly to 0 over `blend` units either side
    of a border shared with a neighbour (the two weights there add up to 1)."""
    w = np.ones_like(pos)
    if has_lo:
        w = np.minimum(w, np.clip((pos - (lo - blend)) / (2 * blend), 0, 1))
    if has_hi:
        w = np.minimum(w, np.clip(((hi + blend) - pos) / (2 * blend), 0, 1))
    return w


def _region(im, c, upp, xa, xb, ya, yb, size):
    """World box [xa, xb] x [ya, yb] of one frame resampled to `size` pixels, as floats."""
    w, h = im.size
    box = (w / 2 + (xa - c[0]) / upp, h / 2 - (yb - c[1]) / upp, w / 2 + (xb - c[0]) / upp, h / 2 - (ya - c[1]) / upp)
    return np.asarray(im.transform(size, Image.EXTENT, box, Image.BICUBIC), np.float32)


def stitch(frame_files, prints, upp_out, rect, blend_px=64):
    """Cells of the serpentine grid (each output pixel from the frame whose centre is nearest), cross-faded over
    2 x blend_px at every border: the water's glints depend on where it is in a frame, a hard cut showed as a line.
    Built one row of frames at a time, so only two rows are ever held as floats."""
    x0, x1, y0, y1 = rect
    W, H = int(round((x1 - x0) / upp_out)), int(round((y1 - y0) / upp_out))
    blend = blend_px * upp_out
    canvas = Image.new("RGB", (W, H))
    centres = np.array([c for c, *_ in prints])
    xs, ys = np.unique(np.round(centres[:, 0])), np.unique(np.round(centres[:, 1]))[::-1]      # rows top first
    bx = np.concatenate([[x0], (xs[1:] + xs[:-1]) / 2, [x1]])
    by = np.concatenate([[y1], (ys[1:] + ys[:-1]) / 2, [y0]])                                   # descending
    col_x = x0 + (np.arange(W) + 0.5) * upp_out
    prev, prev_top = None, 0                       # the previous row's strip (floats) and its first canvas row
    for j, yc in enumerate(ys):
        top, bottom = by[j], by[j + 1]
        st = min(top + (blend if j else 0), y1)
        sb = max(bottom - (blend if j < len(ys) - 1 else 0), y0)
        r0, r1 = int(round((y1 - st) / upp_out)), int(round((y1 - sb) / upp_out))
        strip = np.zeros((r1 - r0, W, 3), np.float32)
        for path, (c, _right, _up, upp) in zip(frame_files, prints):
            if abs(round(c[1]) - yc) > 0.5:
                continue
            i = int(np.argmin(abs(xs - round(c[0]))))
            xa, xb = max(bx[i] - (blend if i else 0), x0), min(bx[i + 1] + (blend if i < len(xs) - 1 else 0), x1)
            c0, c1 = int(round((xa - x0) / upp_out)), int(round((xb - x0) / upp_out))
            part = _region(Image.open(path).convert("RGB"), c, upp, x0 + c0 * upp_out, x0 + c1 * upp_out,
                           y1 - r1 * upp_out, y1 - r0 * upp_out, (c1 - c0, r1 - r0))
            wx = _ramp(col_x[c0:c1], bx[i], bx[i + 1], blend, i > 0, i < len(xs) - 1)
            strip[:, c0:c1] += part * wx[None, :, None]
        row_y = y1 - (np.arange(r0, r1) + 0.5) * upp_out
        wy = _ramp(row_y, bottom, top, blend, j < len(ys) - 1, j > 0)                         # lo = bottom edge
        strip *= wy[:, None, None]
        if prev is not None:                                                                    # overlap with the row above
            ov0 = r0 - prev_top
            strip[: prev.shape[0] - ov0] += prev[ov0:]
            done = prev[:ov0]
            canvas.paste(Image.fromarray(np.clip(done + 0.5, 0, 255).astype(np.uint8)), (0, prev_top))
        prev, prev_top = strip, r0
    canvas.paste(Image.fromarray(np.clip(prev + 0.5, 0, 255).astype(np.uint8)), (0, prev_top))
    return canvas


def _void_mask(a, min_area=40000):
    """The empty corners beyond the map's edge: big near-black regions touching the picture's border (their
    outermost ~12 px are SFM's flat grey background, not black)."""
    from scipy import ndimage

    c = a.astype(np.int16)
    void = c.max(axis=2) < 8
    # SFM's flat grey background (64 64 64): a rim past 7.41's edge, wide margins around the older, smaller maps —
    # neutral, and with no texture at all (the Dire ground is grey-blue and textured)
    grey = (abs(c[..., 0] - c[..., 1]) < 3) & (abs(c[..., 1] - c[..., 2]) < 3) & (c.max(axis=2) >= 45) & (c.max(axis=2) <= 80)
    g = c.mean(axis=2).astype(np.float32)
    flat = np.abs(g - ndimage.uniform_filter(g, 7)) < 1.5
    void |= ndimage.binary_opening(grey & flat, iterations=3)
    labels, n = ndimage.label(ndimage.binary_dilation(void, iterations=4))      # joined across thin seams
    border = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}
    sizes = ndimage.sum(void, labels, range(n + 1))
    keep = [i for i in border if sizes[i] >= min_area]
    if not keep:
        return np.zeros(void.shape, bool)
    return ndimage.binary_dilation(void & np.isin(labels, keep), iterations=2)


def _ground_sources(a, known, near, patch=128, count=400, q=4):
    """A pool of `count` clean patches of the void's own ground, from anywhere on the map: the colour to match is
    the most common plain ground near the void (the plainest quarter of its pixels) — grass by Radiant, grey ground
    by Dire, never the land right along the void (cliffs, lava). A patch qualifies with no bush, tree or shadow in
    it (nothing darker than that ground), colour close to it, little colour spread (paving: stones between grass),
    little detail. The owner 2026-10-01: "trees in the corners? remove them if they aren't really there" — six big
    source windows were tried first: on Radiant's lawns every big window has bushes or paving in it.
    Returns (patches, their top-left corners, the ground colour)."""
    from scipy import ndimage

    h, w = known.shape
    small = np.asarray(Image.fromarray(a).resize((w // q, h // q), Image.BOX), np.float32)
    kn = np.asarray(Image.fromarray(known.astype(np.uint8) * 255).resize((w // q, h // q), Image.BOX)) > 250
    nr = np.asarray(Image.fromarray(near.astype(np.uint8) * 255).resize((w // q, h // q), Image.BOX)) > 127
    grey = small.mean(axis=2)
    detail = np.abs(ndimage.sobel(grey, 0)) + np.abs(ndimage.sobel(grey, 1))
    local = ndimage.uniform_filter(detail, 9)
    area = kn & nr
    plain = area & (local <= np.percentile(local[area], 25))
    target = np.median(small[plain], axis=0)
    ground = float(np.median(grey[plain]))
    s = patch // q
    col = np.stack([ndimage.uniform_filter(small[..., k], s) for k in range(3)], axis=-1)
    spread = np.sqrt(np.maximum(np.stack([ndimage.uniform_filter(small[..., k] ** 2, s) for k in range(3)], -1)
                                - col ** 2, 0)).sum(axis=-1)
    dark = ndimage.maximum_filter((ndimage.uniform_filter(grey, 3) < ground - 18).astype(np.uint8), s) > 0
    ok = (ndimage.minimum_filter(kn.astype(np.uint8), s) > 0) & ~dark
    score = ndimage.uniform_filter(detail, s) + 1.5 * spread + 0.5 * np.abs(col - target).sum(axis=-1)
    score[~ok] = np.inf
    score[np.abs(col - target).max(axis=-1) > 12] = np.inf
    ys, xs = np.mgrid[s // 2:small.shape[0] - s // 2:max(s // 2, 1), s // 2:small.shape[1] - s // 2:max(s // 2, 1)]
    flat = score[ys, xs].ravel()
    order = np.argsort(flat)
    picked = []
    for i in order[:count]:
        if not np.isfinite(flat[i]):
            break
        picked.append(((ys.ravel()[i] - s // 2) * q, (xs.ravel()[i] - s // 2) * q))
    patches = [a[y:y + patch, x:x + patch].astype(np.float32) for y, x in picked]
    return patches, picked, target


def _min_cut(err):
    """The cheapest top-to-bottom path through an overlap's error (rows x overlap width): mask, 1 right of it."""
    h, w = err.shape
    cost = err.copy()
    for i in range(1, h):
        left = np.r_[np.inf, cost[i - 1, :-1]]
        right = np.r_[cost[i - 1, 1:], np.inf]
        cost[i] += np.minimum(np.minimum(left, cost[i - 1]), right)
    mask = np.zeros((h, w), np.float32)
    j = int(np.argmin(cost[-1]))
    for i in range(h - 1, -1, -1):
        mask[i, j:] = 1
        if i:
            lo, hi = max(j - 1, 0), min(j + 2, w)
            j = lo + int(np.argmin(cost[i - 1, lo:hi]))
    return mask


def _quilt(sources, h, w, patch=128, overlap=32, tries=80, seed=741, masks=None, target=None, tol=14):
    """A ground texture of h x w from patches of `sources` (Efros & Freeman's image quilting): each patch chosen
    among random ones for the best match with what is already laid down, joined along the cheapest seam."""
    rng = np.random.default_rng(seed)
    step = patch - overlap
    out = np.zeros((h + patch, w + patch, 3), np.float32)
    for y in range(0, h, step):
        for x in range(0, w, step):
            best = None
            drawn = 0
            for _ in range(tries * 20):
                if drawn == tries:
                    break
                k = rng.integers(len(sources))
                src = sources[k]
                sy, sx = rng.integers(src.shape[0] - patch + 1), rng.integers(src.shape[1] - patch + 1)
                if masks is not None and masks[k][sy:sy + patch, sx:sx + patch].any():
                    continue                                   # touches a bush or a tree
                if target is not None and np.abs(src[sy:sy + patch, sx:sx + patch].mean(axis=(0, 1)) - target).max() > tol:
                    continue                                   # a patch of dirt or of a path, not of the ground
                drawn += 1
                cand = src[sy:sy + patch, sx:sx + patch]
                e = 0.0
                if x:
                    e += ((cand[:, :overlap] - out[y:y + patch, x:x + overlap]) ** 2).sum()
                if y:
                    e += ((cand[:overlap] - out[y:y + overlap, x:x + patch]) ** 2).sum()
                if best is None or e < best[0]:
                    best = (e, cand)
            if best is None:                                   # nothing passed the checks: any patch will do
                src = sources[rng.integers(len(sources))]
                sy, sx = rng.integers(src.shape[0] - patch + 1), rng.integers(src.shape[1] - patch + 1)
                best = (0.0, src[sy:sy + patch, sx:sx + patch])
            cand = best[1]
            mask = np.ones((patch, patch), np.float32)
            if x:
                err = ((cand[:, :overlap] - out[y:y + patch, x:x + overlap]) ** 2).sum(axis=2)
                mask[:, :overlap] = np.minimum(mask[:, :overlap], _min_cut(err))
            if y:
                err = ((cand[:overlap] - out[y:y + overlap, x:x + patch]) ** 2).sum(axis=2)
                mask[:overlap] = np.minimum(mask[:overlap], _min_cut(err.T).T)
            region = out[y:y + patch, x:x + patch]
            region[:] = cand * mask[..., None] + region * (1 - mask[..., None])
    return out[:h, :w]


def _land_colour(a, known, box, q=8, reach=640):
    """A smooth colour field over box = (y0, y1, x0, x1): the plain ground nearest each point, spread outwards
    (normalized convolution of the low-detail land at 1/q size) — grass beside Radiant, grey ground beside Dire,
    blended between. Around the older, smaller maps the void is one ring round the whole map: one colour for all
    of it was a muddy green."""
    from scipy import ndimage

    h, w = known.shape
    small = np.asarray(Image.fromarray(a).resize((w // q, h // q), Image.BOX), np.float32)
    kn = np.asarray(Image.fromarray(known.astype(np.uint8) * 255).resize((w // q, h // q), Image.BOX)) > 250
    grey = small.mean(axis=2)
    detail = ndimage.uniform_filter(np.abs(ndimage.sobel(grey, 0)) + np.abs(ndimage.sobel(grey, 1)), 3)
    plain = kn & (detail <= np.percentile(detail[kn], 30))
    wgt = plain.astype(np.float32)
    sig = reach / q
    field = ndimage.gaussian_filter(small * wgt[..., None], (sig, sig, 0)) / np.maximum(
        ndimage.gaussian_filter(wgt, sig), 1e-6)[..., None]
    y0, y1, x0, x1 = box
    crop = field[y0 // q:(y1 + q - 1) // q, x0 // q:(x1 + q - 1) // q]
    big = np.stack([np.asarray(Image.fromarray(crop[..., k]).resize(
        ((x1 + q - 1) // q * q - x0 // q * q, (y1 + q - 1) // q * q - y0 // q * q), Image.BILINEAR)) for k in range(3)], -1)
    oy, ox = y0 - y0 // q * q, x0 - x0 // q * q
    return big[oy:oy + (y1 - y0), ox:ox + (x1 - x0)]


def check_fits(prints, width, height, rect, objects=(), margin=300):
    """What is wrong with this render's coverage, as a list of messages (empty: fine). The owner 2026-10-01:
    "what if a patch's map was a different size?" — sizes did change: trees and buildings reach ±7680 units until
    7.32, ±8768 from 7.33, a little more from 7.40; the ancients never moved. Every picture shares one world
    rectangle and scale, so a smaller map is simply drawn smaller; a bigger one must not be cut off. Checked: the
    frames together cover the rectangle, and every object (x, y) lies inside it with `margin` units to spare."""
    x0, x1, y0, y1 = rect
    upp = prints[0][3]
    cx = [c[0] for c, *_ in prints]
    cy = [c[1] for c, *_ in prints]
    fx0, fx1 = min(cx) - width * upp / 2, max(cx) + width * upp / 2
    fy0, fy1 = min(cy) - height * upp / 2, max(cy) + height * upp / 2
    out = []
    if fx0 > x0 or fx1 < x1 or fy0 > y0 or fy1 < y1:
        out.append(f"the frames cover x {fx0:.0f}..{fx1:.0f}, y {fy0:.0f}..{fy1:.0f}, "
                   f"not the whole picture x {x0:.0f}..{x1:.0f}, y {y0:.0f}..{y1:.0f}")
    if objects:
        ox = [x for x, _ in objects]
        oy = [y for _, y in objects]
        if min(ox) - margin < x0 or max(ox) + margin > x1 or min(oy) - margin < y0 or max(oy) + margin > y1:
            out.append(f"the map's objects reach x {min(ox)}..{max(ox)}, y {min(oy)}..{max(oy)}: closer than "
                       f"{margin} units to the picture's edge — widen it (data/terrain_map_meta.json)")
    return out


def black_void(img):
    """The corners beyond the map's edge left as the game draws them — it lights nothing out there, on the current
    and on the 7.40c engine alike, and no setting changes that (tried 2026-10-01: mat_fullbright,
    sc_disable_baked_lighting, r_indirectlighting, r_dota_shadow_ambient_light, r_deferred_height_fog,
    dota_height_fog_scale, r_dota_height_fog_plane_height). Only SFM's flat grey background around them is
    painted black, so the corners read as one dark field. Every painted fill was rejected by the owner (a blurred
    fade: "murky"; quilted ground: "terrible")."""
    a = np.asarray(img.convert("RGB")).copy()
    a[_void_mask(a)] = 0
    return Image.fromarray(a)


def fill_void(img, shade=0.8, shadow=90, near_px=2500):
    """The corners beyond the map's edge (nothing renders there: black) painted in our own way (the owner
    2026-10-01: "fill the black corners, in our own way" — then "the bottom-left is all murky; leamare's looks more
    harmonious"): plain ground continues past the edge — a texture quilted from the plainest ground next to the
    void (grass by Radiant, grey ground by Dire), a little darker than the map, with a soft shadow under the map's
    edge so it reads as outside the playable area. Tried before: mirroring the edge (duplicated cliffs), a
    blurred colour fade (murky)."""
    from scipy import ndimage

    a = np.asarray(img.convert("RGB"))
    mask = _void_mask(a)
    if not mask.any():
        return img
    out = a.astype(np.float32)
    lab, n = ndimage.label(mask)
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        m = lab == k
        known = ~mask
        q = 8                                                          # where to look, worked out at 1/8 size
        ms = np.asarray(Image.fromarray(m.astype(np.uint8) * 255).resize((m.shape[1] // q, m.shape[0] // q))) > 0
        near_small = ndimage.distance_transform_edt(~ms) < near_px / q
        near = np.asarray(Image.fromarray(near_small.astype(np.uint8) * 255).resize((m.shape[1], m.shape[0]))) > 127
        sources, where, target = _ground_sources(a, known, near)
        print("void", k, len(sources), "clean ground patches, colour", np.round(target), flush=True)
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        tex = _quilt(sources, y1 - y0, x1 - x0, seed=741 + k)
        # no large-scale colour bands (the patches' rows showed as stripes): keep the grass's fine grain, even out
        # everything wider than ~60 px to the ground's own colour
        base = _land_colour(a, ~mask, (y0, y1, x0, x1))
        tex = tex - ndimage.gaussian_filter(tex, (60, 60, 0)) + base
        dist = ndimage.distance_transform_edt(m[y0:y1, x0:x1])          # px from the map's edge (within the box)
        light = shade * (1 - 0.35 * np.exp(-dist / shadow))
        mm = m[y0:y1, x0:x1]
        region = out[y0:y1, x0:x1]
        region[mm] = (tex * light[..., None])[mm]
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session")
    ap.add_argument("frames", help="the folder SFM exported the image sequence into")
    ap.add_argument("version")
    ap.add_argument("--work", required=True, help="a folder outside the repo")
    ap.add_argument("--upp", type=float, default=2.0, help="game units per pixel of the full picture")
    ap.add_argument("--mapdata", help="the version's mapdata json (extract_map_entities.py): its objects must fit")
    ap.add_argument("--no-fill", action="store_true", help="leave the empty corners beyond the map's edge as rendered")
    ap.add_argument("--void-black", action="store_true",
                    help="the corners beyond the map's edge as the game draws them (near-black), SFM's grey rim black")
    args = ap.parse_args()
    frames, quat, fov, width, height = camera_path(session_text(args.session))
    files = sorted(glob.glob(os.path.join(args.frames, "*.png")))
    if len(files) != len(frames):
        raise SystemExit(f"{len(files)} frames on disk, the session exports {len(frames)}")
    prints = footprints(frames, quat, fov, width)
    upp = measured_upp(files, frames)
    lens = prints[0][3]
    print("units per pixel in a frame: lens", round(lens, 4), "measured", upp and round(upp, 4))
    # the measurement wins only when it is plausible: over SFM's flat background (old, smaller maps) the frames
    # have nothing to match and 7.22 measured 3.93 against the lens's 1.09
    if upp and abs(upp / lens - 1) < 0.01:
        prints = [(c, r, u, upp) for c, r, u, _ in prints]
    objects = []
    if args.mapdata:
        with open(args.mapdata, encoding="utf-8") as f:
            md = json.load(f)["data"]
        objects = [(e["x"], e["y"]) for k in ("ent_dota_tree", "npc_dota_fort", "npc_dota_tower", "npc_dota_barracks")
                   for e in md.get(k, []) if "x" in e]
    problems = check_fits(prints, width, height, world_rect(), objects)
    if problems:
        raise SystemExit("this render does not fit: " + "; ".join(problems))
    full = stitch(files, prints, args.upp, world_rect())
    if args.void_black:
        full = black_void(full)
    elif not args.no_fill:
        full = fill_void(full)
    full.save(os.path.join(args.work, f"map_{args.version}_sfm_full.png"))
    full.resize((SITE_PX, SITE_PX), Image.LANCZOS).save(
        os.path.join(args.work, f"map_{args.version}_sfm.webp"), "WEBP", quality=88, method=6)
    print("done", full.size)


if __name__ == "__main__":
    main()
