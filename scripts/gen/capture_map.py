"""Our top-down map picture shot IN THE GAME (the game's own look — as leamare's SFM method, without SFM's clicks):
a running Dota 2 in Workshop Tools mode with the custom game scripts/gen/topdown_addon (no fog of war, no units,
the camera straight down), driven through its remote console (scripts/gen/game_console.py): for every tile the
camera looks straight down at the tile's centre, the game writes a screenshot, and only the middle of it is kept —
the game camera is a wide-angle one, so tall things lean outwards away from a frame's centre; small tiles keep
that lean small. The tiles are stitched on the world grid of our map images (data/terrain_map_meta.json).

    1. install the addon + start the game (the game window must be allowed to render: r_always_render_all_windows):
       python scripts/gen/capture_map.py --install
       dota2.exe -tools -novid -vconsole -condebug -windowed -w 1920 -h 1080 -addon sloppy_topdown
                 +dota_launch_custom_game sloppy_topdown dota
    2. python scripts/gen/capture_map.py 7.41 --work D:\\maprender
       (one game session per tiles folder: two sessions' tiles differed in scale by ~4%)
The site picture goes through the colour table of scripts/gen/tone_match.py (leamare's look), the full one doesn't.
"""
import argparse
import glob
import json
import os
import shutil
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tone_match  # noqa: E402
from game_console import GameConsole  # noqa: E402
from render_map import SITE_PX, world_rect  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
GAME = os.environ.get("DOTA_GAME", r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game")
SHOTS = os.path.join(GAME, "dota", "screenshots")
LOG = os.path.join(GAME, "dota", "console.log")                         # the game's console output (-condebug)
ADDON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topdown_addon")
# render while not focused (Tools' "Render All Windows"), no fog / UI / health bars, units hidden, and the camera
# jumps instead of gliding (with the glide a shot 1 s after a move was taken mid-flight: tiles off by ~20%)
# no butterflies / critters, no tree shake or cloth wind, no wind in the foliage, no drifting cloud shadows, particles
# frozen, outposts removed (the owner 2026-10-01: "ambient like butterflies, moving water" — two shots of one spot
# 3 s apart differ in 0.03% of the pixels, a pond's ripples). The game is NOT paused: PauseGame stops neither the
# foliage nor the water, and while paused the server runs console commands 10-20 s late — the camera stayed put
SETUP = ("r_always_render_all_windows 1", "engine_no_focus_sleep 0", "fog_enable 0", "r_drawpanorama 0",
         "dota_hud_healthbars 0", "topdown_hide", "dota_camera_lerp_duration 0", "dota_camera_smooth_count 1",
         "dota_ambient_creatures 0", "cl_dota_ambient_tree_shake 0", "dota_ambient_cloth 0",
         "r_dota_allow_wind_on_trees 0", "r_dota_clouds 0", "r_freezeparticles 1")


def install():
    root = os.path.dirname(GAME)
    for part, dest in (("game", os.path.join(GAME, "dota_addons", "sloppy_topdown")),
                       ("content", os.path.join(root, "content", "dota_addons", "sloppy_topdown"))):
        shutil.copytree(os.path.join(ADDON, part), dest, dirs_exist_ok=True)
    print("installed")


class Camera:
    def __init__(self, dist, shot_w, shot_h, settle):
        self.c = GameConsole(timeout=60)
        self.c.pump(1)
        for cmd in SETUP + (f"screenshot_width {shot_w}", f"screenshot_height {shot_h}"):
            self.c.run(cmd, 0.4)
        self.dist, self.settle = dist, settle
        time.sleep(3)                       # the first shot right after the settings came out shifted and different

    def lookat(self, timeout=3.0):
        """Where the camera looks now (x, y), from the game's own report in console.log (needs -condebug)."""
        size = os.path.getsize(LOG)
        self.c.run("dota_camera_get_lookatpos", 0.1)
        deadline = time.time() + timeout
        while time.time() < deadline:
            with open(LOG, "rb") as f:
                f.seek(size)
                lines = [l for l in f.read().decode("utf-8", "replace").splitlines() if "Camera look-at position:" in l]
            if lines:
                return tuple(float(v) for v in lines[-1].split(":")[-1].split()[:2])
            time.sleep(0.1)
        return None

    def goto(self, x, y, tries=6):
        """Point the camera and make sure it got there: a move sent right after another one is now and then lost."""
        for _ in range(tries):
            self.c.run(f"topdown_cam {x:.1f} {y:.1f} {self.dist}", 0.2)
            for _ in range(10):
                at = self.lookat()
                if at and abs(at[0] - x) < 2 and abs(at[1] - y) < 2:
                    return
                time.sleep(0.2)
        raise RuntimeError(f"the camera does not go to {x} {y}")

    def shot(self, x, y):
        """The game's screenshot of the ground straight below (x, y), as a greyscale-able PIL image."""
        before = set(glob.glob(os.path.join(SHOTS, "*.tga")))
        self.goto(x, y)
        time.sleep(self.settle)
        self.c.run("screenshot", 0.2)
        deadline = time.time() + 60
        while time.time() < deadline:
            new = set(glob.glob(os.path.join(SHOTS, "*.tga"))) - before
            if new:
                path = new.pop()
                for _ in range(40):                      # wait until the file is complete
                    try:
                        im = Image.open(path)
                        im.load()
                        break
                    except OSError:
                        time.sleep(0.25)
                im = im.convert("RGB")
                os.remove(path)
                return im
            self.c.pump(0.2)
        raise RuntimeError("no screenshot")


def calibrate(cam, x, y, step=400):
    """Game units per screenshot pixel at the ground: two shots `step` apart, phase correlation of their middles."""
    a, b = cam.shot(x, y), cam.shot(x + step, y)
    w, h = a.size
    box = (w // 2 - 1024, h // 2 - 1024, w // 2 + 1024, h // 2 + 1024)
    A = np.asarray(a.convert("L").crop(box), dtype=np.float32)
    B = np.asarray(b.convert("L").crop(box), dtype=np.float32)
    F = np.fft.fft2(A) * np.conj(np.fft.fft2(B))
    r = np.fft.ifft2(F / (np.abs(F) + 1e-9)).real
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    ix = ix - A.shape[1] if ix > A.shape[1] // 2 else ix
    return step / abs(ix)


def look_at_bounds(cam, far=20000):
    """How far the game lets the camera look: it clamps its look-at point to the playable area (7.41: x ±8448,
    y -9472..8448), so a tile beyond that is shot from the nearest allowed point and cut off-centre."""
    got = []
    for x, y in ((-far, -far), (far, far)):
        for _ in range(6):                                  # until the camera leaves the middle, the move may be lost
            cam.c.run(f"topdown_cam {x} {y} {cam.dist}", 0.3)
            time.sleep(0.8)
            at = cam.lookat()
            if at and abs(at[0]) > 4000 and abs(at[1]) > 4000:
                break
        got.append(at)
    (ax, ay), (bx, by) = got
    return ax, bx, ay, by


def capture(cam, upp, x0, x1, y0, y1, tile, out_dir, bounds):
    """Every tile's middle (tile x tile game units) into out_dir/r_c.png; returns the grid size."""
    os.makedirs(out_dir, exist_ok=True)
    cols, rows = int(np.ceil((x1 - x0) / tile)), int(np.ceil((y1 - y0) / tile))
    half = tile / upp / 2
    bx0, bx1, by0, by1 = bounds
    for r in range(rows):
        for c in range(cols):
            path = os.path.join(out_dir, f"{r}_{c}.png")
            if os.path.exists(path):
                continue
            cx, cy = x0 + tile * (c + 0.5), y1 - tile * (r + 0.5)
            sx, sy = min(max(cx, bx0), bx1), min(max(cy, by0), by1)        # where the camera may look
            im = cam.shot(sx, sy)
            w, h = im.size
            mx, my = w / 2 + (cx - sx) / upp, h / 2 - (cy - sy) / upp        # the tile's centre in the shot
            # a pixel of margin all round, trimmed when stitching (no black hairline at the seams)
            im.crop((round(mx - half) - 1, round(my - half) - 1, round(mx + half) + 1, round(my + half) + 1)).save(path)
            print(f"tile {r} {c} / {rows} {cols}", flush=True)
    return rows, cols


def stitch(out_dir, rows, cols, upp, tile):
    px = round(tile / upp)
    full = Image.new("RGB", (px * cols, px * rows))
    for r in range(rows):
        for c in range(cols):
            im = Image.open(os.path.join(out_dir, f"{r}_{c}.png"))
            im = im.crop((1, 1, im.width - 1, im.height - 1)).resize((px, px), Image.LANCZOS)
            full.paste(im, (c * px, r * px))
    return full


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version", nargs="?")
    ap.add_argument("--work", help="a folder outside the repo")
    ap.add_argument("--install", action="store_true", help="copy the custom game into the game folders")
    ap.add_argument("--dist", type=float, default=5000, help="camera height above the ground")
    ap.add_argument("--tile", type=float, default=900, help="game units kept from the middle of each shot")
    ap.add_argument("--shot", default="7680x4320")
    ap.add_argument("--settle", type=float, default=1.2, help="seconds for textures to stream after a move")
    ap.add_argument("--region", type=float, nargs=4, metavar=("X0", "X1", "Y0", "Y1"),
                    help="a part of the map (default: the whole picture rectangle)")
    ap.add_argument("--no-grade", action="store_true", help="keep the game's own colours in the site picture")
    args = ap.parse_args()
    if args.install:
        install()
        return
    w, h = map(int, args.shot.split("x"))
    cam = Camera(args.dist, w, h, args.settle)
    x0, x1, y0, y1 = args.region or world_rect()
    upp_path = os.path.join(args.work, f"upp_{int(args.dist)}.json")
    if os.path.exists(upp_path):
        upp = json.load(open(upp_path))["upp"]
    else:
        upp = calibrate(cam, (x0 + x1) / 2, (y0 + y1) / 2)
        json.dump({"upp": upp, "dist": args.dist, "shot": args.shot}, open(upp_path, "w"))
    print("units per pixel", round(upp, 4))
    bounds = look_at_bounds(cam)
    print("camera look-at bounds", bounds)
    tiles = os.path.join(args.work, f"tiles_{args.version}_{int(args.dist)}_{int(args.tile)}")
    rows, cols = capture(cam, upp, x0, x1, y0, y1, args.tile, tiles, bounds)
    full = stitch(tiles, rows, cols, upp, args.tile)
    # the tiles run past the rectangle's right / bottom edge: cut it back to the rectangle exactly
    per = round(args.tile / upp) / args.tile                 # pixels per game unit of the stitched picture
    full = full.crop((0, 0, round((x1 - x0) * per), round((y1 - y0) * per)))
    full.save(os.path.join(args.work, f"map_{args.version}_game_full.png"))      # as the game shows it
    if not args.region:
        site = full.resize((SITE_PX, SITE_PX), Image.LANCZOS)
        if os.path.exists(tone_match.LUT) and not args.no_grade:      # leamare's colour look (tone_match.py)
            site = tone_match.apply(site)
        site.save(os.path.join(args.work, f"map_{args.version}_game.webp"), "WEBP", quality=88, method=6)
    print("done", full.size)


if __name__ == "__main__":
    main()
