"""Generate Items Dynamics icon to match Heroes Dynamics closely,
but with two extra bars.

Outputs:
  icons/ui/gothic/icon_dynamics_items.png
  icons/ui/gothic/icon_dynamics_items.gif
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "icons" / "ui" / "gothic"
S = 32

BG = (0, 0, 0, 0)
OUT = (34, 24, 12, 255)
AXIS = (118, 86, 44, 255)
AXIS_D = (92, 68, 34, 255)
B1 = (170, 134, 58, 255)
B2 = (208, 174, 92, 255)
B3 = (227, 196, 106, 255)
B4 = (238, 214, 138, 255)
B5 = (252, 243, 208, 255)
PALETTE = [B1, B2, B3, B4, B5]

LEFT = 4
BASE = 27
TOP = 6
BAR_W = 2
XS = [10, 13, 16, 19, 22]


def newimg():
    return Image.new("RGBA", (S, S), BG)


def put(img, x, y, c):
    if 0 <= x < S and 0 <= y < S:
        img.putpixel((x, y), c)


def line(img, x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        put(img, x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def rect(img, x, y, w, h, fill):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            put(img, xx, yy, fill)


def bar(img, x, height, fill):
    y = BASE - height + 1
    rect(img, x, y, BAR_W, height, fill)
    for yy in range(y, BASE + 1):
        put(img, x, yy, OUT)
    for xx in range(x + 1, x + BAR_W):
        put(img, xx, y, B5 if fill != B5 else fill)


def frame(heights):
    img = newimg()
    # Match the heroes icon family: same axis style, same baseline/top.
    line(img, LEFT, TOP, LEFT, BASE, AXIS)
    line(img, LEFT, BASE, 29, BASE, AXIS)
    line(img, LEFT + 1, TOP, LEFT + 1, BASE, AXIS_D)
    line(img, LEFT, BASE - 1, 29, BASE - 1, AXIS_D)
    put(img, LEFT, TOP, OUT)
    put(img, 29, BASE, OUT)

    for x, h, col in zip(XS, heights, PALETTE):
        bar(img, x, h, col)
    return img


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # 23-frame loop, mirroring the timing cadence of Heroes Dynamics:
    # one slightly longer first frame, a longer mid-loop rest on frame 11,
    # otherwise even steps. Motion is the same bar-chart "breathing", just
    # with 5 narrower columns instead of 3 wider ones.
    seq = [
        [3, 6, 8, 10, 7],
        [3, 7, 7, 10, 8],
        [4, 7, 6, 10, 9],
        [4, 6, 7, 9, 10],
        [5, 5, 8, 8, 10],
        [6, 4, 9, 7, 9],
        [7, 4, 10, 6, 8],
        [8, 5, 9, 6, 7],
        [9, 6, 8, 7, 6],
        [8, 7, 7, 8, 5],
        [7, 8, 6, 9, 4],
        [6, 9, 5, 10, 4],
        [5, 10, 4, 9, 5],
        [4, 9, 5, 8, 6],
        [4, 8, 6, 7, 7],
        [5, 7, 7, 6, 8],
        [6, 6, 8, 5, 9],
        [7, 5, 9, 4, 10],
        [8, 4, 10, 4, 9],
        [9, 4, 9, 5, 8],
        [8, 5, 8, 6, 7],
        [6, 5, 8, 8, 7],
        [3, 6, 8, 10, 7],
    ]
    static = frame(seq[0])
    static.save(OUT_DIR / "icon_dynamics_items.png")
    frames = [frame(h) for h in seq[:-1]]
    durations = [220] + [110] * 10 + [550] + [110] * 10
    frames[0].save(
        OUT_DIR / "icon_dynamics_items.gif",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
        transparency=0,
    )
    print("  -> icon_dynamics_items.png + icon_dynamics_items.gif")


if __name__ == "__main__":
    main()
