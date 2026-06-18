"""Fetch + stitch the Dota terrain map renders -> icons/maps/map_<ver>.webp.

Source: the **spectral.gg courier tile server** (same render as the
interactive map at https://tools.spectral.gg/interactive-map):

    https://courier.spectral.gg/images/dota/maps/tiles/<code>/<skin>/<z>/tile_<col>_<row>.jpg

  - <code> : patch without the dot (7.41 -> "741", 7.40 -> "740").
  - <skin> : "default" (standard map skin).
  - <z>    : zoom 0..4. Tiles are 256x256.

**Tile scheme (reverse-engineered — NOT a plain 2^z pyramid):**
  - The map render has grey placeholder (#383931 ≈ rgb 56,57,49) padding on the
    TOP and a little on the LEFT; the actual map is flush to the bottom/right.
  - Out-of-range tile requests return that flat grey tile (HTTP 200), so you
    can't probe the grid by status — detect content by colour distance instead.
  - At zoom 2 the whole map fits inside a 24x24 grid (content ≈ 19x19 tiles,
    ~4864px). zoom 2 is the sweet spot: downscaled to 1280² it's far sharper
    than the old blurry export, without zoom 3/4's hundreds of tiles.

We stitch zoom 2 on a 24x24 canvas, crop to the (shared) content bounding box,
and resize to 1280² (square; matches the SVG marker viewBox + the old crop, so
the projection carries over). 7.40 and 7.41 use the SAME crop box → the swipe
slider stays pixel-aligned.

Tiles cache under .cache/tiles/<code>z2full/ (gitignored). Run::

    python scripts/gen/build_terrain_maps.py 740 741
"""
import os
import sys
import urllib.request

from PIL import Image
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))

# leamare/spectral map projection (src/js/mapConstants.js + conversion.js):
# the full map is MAP_W px; world coords map onto it via these boundaries
# (world value at pixel 0 and pixel MAP_W). NOT the worlddata.json bounds.
MAP_W = MAP_H = 20480
X_BOUNDS = [-10829.42, 11487.75]      # world x at pixel x=0 .. MAP_W
Y_BOUNDS = [11351.48, -10939.96]      # world y at pixel y=0 .. MAP_H (y flips)
# zoom-3 tiles: each 256px tile covers 512 map-px, so our stitched canvas
# is the map at MAP_W/2 — i.e. 2 map-px per canvas-px.
CANVAS_SCALE = 2
TILE_BASE = "https://courier.spectral.gg/images/dota/maps/tiles"
SKIN = "default"
ZOOM = 3
GRID = 48                 # 48x48 fully contains the zoom-3 map
T = 256                   # tile px
EMPTY = np.array([56, 57, 49])   # grey placeholder colour
OUT_SIZE = 4096           # crisp fullscreen on 1440p/4K
OUT_QUALITY = 88
UA = {"User-Agent": "Mozilla/5.0 (sikle terrain map builder)"}


def _code(ver):
    return ver.replace(".", "")


def _fetch(ver):
    code = _code(ver)
    cache = os.path.join(_ROOT, ".cache", "tiles", f"{code}z{ZOOM}")
    os.makedirs(cache, exist_ok=True)
    for c in range(GRID):
        for r in range(GRID):
            fn = os.path.join(cache, f"{c}_{r}.jpg")
            if os.path.exists(fn) and os.path.getsize(fn) > 0:
                continue
            url = f"{TILE_BASE}/{code}/{SKIN}/{ZOOM}/tile_{c}_{r}.jpg"
            try:
                req = urllib.request.Request(url, headers=UA)
                data = urllib.request.urlopen(req, timeout=30).read()
                with open(fn, "wb") as f:
                    f.write(data)
            except urllib.error.HTTPError as e:
                # 404 == tile outside the real grid (the map is flush bottom/
                # right with grey padding); expected for the margin, ignore.
                if e.code != 404:
                    print(f"  ! {url}: {e}")
            except Exception as e:
                print(f"  ! {url}: {e}")
    return cache


def _stitch(cache):
    cv = Image.new("RGB", (GRID * T, GRID * T), tuple(EMPTY))
    for c in range(GRID):
        for r in range(GRID):
            fn = os.path.join(cache, f"{c}_{r}.jpg")
            if os.path.exists(fn) and os.path.getsize(fn) > 0:
                try:
                    cv.paste(Image.open(fn).convert("RGB"), (c * T, r * T))
                except Exception:
                    pass
    return cv


def _content_bbox(cv):
    """Tight bounding box of the REAL (colourful) map, excluding the flat-grey
    placeholder padding. A pixel is placeholder iff it is both near the EMPTY
    grey AND low-saturation; everything else is content. We then require a
    column/row to be ≥10% content before counting it as part of the map, so
    stray JPEG noise in the grey margin can't inflate the box (that was the old
    `dist > 22`-on-any-pixel bug → fat grey borders left on every edge)."""
    a = np.asarray(cv).astype(int)
    greydist = np.sqrt(((a - EMPTY) ** 2).sum(2))
    sat = a.max(2) - a.min(2)
    content = ~((greydist < 26) & (sat < 16))
    colfrac = content.mean(0)
    rowfrac = content.mean(1)
    xs = np.where(colfrac > 0.10)[0]
    ys = np.where(rowfrac > 0.10)[0]
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def main(versions):
    canvases = {}
    boxes = []
    for ver in versions:
        cache = _fetch(ver)
        cv = _stitch(cache)
        canvases[ver] = cv
        boxes.append(_content_bbox(cv))
        print(f"  {ver}: bbox {boxes[-1]}")
    # Shared crop box (union) so every version is framed identically.
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
    box = (x0, y0, x1, y1)
    print(f"  shared crop box {box} ({x1 - x0}x{y1 - y0})")
    for ver, cv in canvases.items():
        out = os.path.join(_ROOT, "icons", "maps", f"map_{ver}.webp")
        cv.crop(box).resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS).save(
            out, "WEBP", quality=OUT_QUALITY, method=6)
        print(f"  -> {os.path.relpath(out, _ROOT)} "
              f"({os.path.getsize(out) // 1024} KB)")
    # Projection meta so builders/terrain.py can place markers exactly on the crop:
    # world -> canvas px (MAP_W/CANVAS_SCALE) -> minus crop origin -> /crop size.
    import json as _json
    meta = {
        "xBounds": X_BOUNDS, "yBounds": Y_BOUNDS,
        "mapW": MAP_W, "mapH": MAP_H, "canvasScale": CANVAS_SCALE,
        "crop": {"x": int(x0), "y": int(y0),
                 "w": int(x1 - x0), "h": int(y1 - y0)},
    }
    meta_path = os.path.join(_ROOT, "data", "terrain_map_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        _json.dump(meta, f, separators=(",", ":"))
    print(f"  -> {os.path.relpath(meta_path, _ROOT)}: crop {meta['crop']}")


if __name__ == "__main__":
    vers = sys.argv[1:] or ["7.40", "7.41"]
    main(vers)
