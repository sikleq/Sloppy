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


def _push_pull(rgb, known, levels=10):
    """Smooth colours for the unknown pixels, spread in from the known ones (an image pyramid down and up)."""
    if levels == 0 or min(rgb.shape[:2]) < 4:
        mean = rgb[known].mean(axis=0) if known.any() else np.zeros(3, np.float32)
        out = rgb.copy()
        out[~known] = mean
        return out
    h, w = known.shape
    hh, ww = (h + 1) // 2, (w + 1) // 2
    k = np.zeros((hh * 2, ww * 2), np.float32)
    k[:h, :w] = known
    c = np.zeros((hh * 2, ww * 2, 3), np.float32)
    c[:h, :w] = rgb * known[..., None]
    ks = k.reshape(hh, 2, ww, 2).sum(axis=(1, 3))
    cs = c.reshape(hh, 2, ww, 2, 3).sum(axis=(1, 3))
    small_known = ks > 0
    small = np.where(small_known[..., None], cs / np.maximum(ks, 1)[..., None], 0)
    filled = _push_pull(small, small_known, levels - 1)
    up = np.repeat(np.repeat(filled, 2, axis=0), 2, axis=1)[:h, :w]
    out = rgb.copy()
    out[~known] = up[~known]
    return out


def fill_void(img, dark=0.3, reach=700, min_area=40000):
    """The corners beyond the map's edge (nothing renders there: black) painted in: the edge's own colours carried
    outwards, more and more blurred and darkened over `reach` pixels — land fading into darkness, with no copied
    objects that could be mistaken for map. The owner 2026-10-01: "fill the black corners, in our own way"
    (leamare's pictures have Microsoft ICE's auto-complete). Mirroring the edge outwards was tried first: it
    duplicated cliffs and left hard lines where the mirror ran out."""
    from scipy import ndimage

    a = np.asarray(img.convert("RGB"))
    c = a.astype(np.int16)
    void = c.max(axis=2) < 8
    # the picture's outermost ~12 px past the map's edge are SFM's flat grey background, not black
    grey = (abs(c[..., 0] - c[..., 1]) < 3) & (abs(c[..., 1] - c[..., 2]) < 3) & (c.max(axis=2) >= 45) & (c.max(axis=2) <= 66)
    rim = np.zeros(void.shape, bool)
    rim[:20], rim[-20:], rim[:, :20], rim[:, -20:] = True, True, True, True
    void |= grey & rim
    labels, n = ndimage.label(void)
    border = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}
    sizes = ndimage.sum(void, labels, range(n + 1))
    keep = [i for i in border if sizes[i] >= min_area]
    if not keep:
        return img
    mask = ndimage.binary_dilation(np.isin(labels, keep), iterations=2)
    out = a.copy()
    q = 4                                                       # the fill is smooth: worked out at 1/4 size
    for sl in ndimage.find_objects(ndimage.label(mask)[0]):
        y0, y1 = max(sl[0].start - reach, 0), min(sl[0].stop + reach, a.shape[0])
        x0, x1 = max(sl[1].start - reach, 0), min(sl[1].stop + reach, a.shape[1])
        m = mask[y0:y1, x0:x1]
        h, w = m.shape
        small = np.asarray(Image.fromarray(a[y0:y1, x0:x1]).resize((w // q, h // q), Image.BOX), np.float32)
        known = np.asarray(Image.fromarray((~m).astype(np.uint8) * 255).resize((w // q, h // q), Image.BOX)) > 250
        k = known.astype(np.float32)

        def spread(sigma):
            """Normalized convolution: the known colours' Gaussian average, wherever there is any weight."""
            wsum = ndimage.gaussian_filter(k, sigma)
            col = ndimage.gaussian_filter(small * k[..., None], (sigma, sigma, 0))
            return col / np.maximum(wsum, 1e-6)[..., None], wsum

        fill, _ = spread(reach / q)                             # coarse first, then finer where weight allows
        for sigma in (reach / q / 3, reach / q / 10):
            col, wsum = spread(sigma)
            wgt = np.clip(wsum / 0.25, 0, 1)[..., None]
            fill = col * wgt + fill * (1 - wgt)
        dist = ndimage.distance_transform_edt(~known) * q
        t = np.clip(dist / reach, 0, 1)
        t = (t * t * (3 - 2 * t))[..., None]
        fill = fill * (1 - t * (1 - dark))
        big = np.asarray(Image.fromarray(np.clip(fill + 0.5, 0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC))
        region = out[y0:y1, x0:x1]
        region[m] = big[m]
    return Image.fromarray(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session")
    ap.add_argument("frames", help="the folder SFM exported the image sequence into")
    ap.add_argument("version")
    ap.add_argument("--work", required=True, help="a folder outside the repo")
    ap.add_argument("--upp", type=float, default=2.0, help="game units per pixel of the full picture")
    args = ap.parse_args()
    frames, quat, fov, width, height = camera_path(session_text(args.session))
    files = sorted(glob.glob(os.path.join(args.frames, "*.png")))
    if len(files) != len(frames):
        raise SystemExit(f"{len(files)} frames on disk, the session exports {len(frames)}")
    prints = footprints(frames, quat, fov, width)
    upp = measured_upp(files, frames)
    print("units per pixel in a frame: lens", round(prints[0][3], 4), "measured", upp and round(upp, 4))
    if upp:
        prints = [(c, r, u, upp) for c, r, u, _ in prints]
    full = fill_void(stitch(files, prints, args.upp, world_rect()))
    full.save(os.path.join(args.work, f"map_{args.version}_sfm_full.png"))
    full.resize((SITE_PX, SITE_PX), Image.LANCZOS).save(
        os.path.join(args.work, f"map_{args.version}_sfm.webp"), "WEBP", quality=88, method=6)
    print("done", full.size)


if __name__ == "__main__":
    main()
