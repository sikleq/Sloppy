"""The header's filters button icon (owner 2026-11-07: "иконка фильтра всё ещё не нравится — поменяй в целом модельку,
не вот эту трубу"): three sliders, the mixing-desk sign for "filters", on the colour-blind eye's 24-pixel grid and
palette (icons/ui/gothic/icon_cb_off.png: dark outline, gold body, light highlight). Each slider is a rail with a
cream knob, the knobs at different places. Shipped x2 as icons/ui/gothic/icon_filter.png.

    python tools/pixel_icons/filter_icon.py
"""
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parents[2] / "icons" / "ui" / "gothic" / "icon_filter.png"
PALETTE = {
    ".": (0, 0, 0, 0),
    "k": (20, 17, 14, 255),      # outline, as the eye's
    "a": (246, 230, 170, 255),   # light, as the eye's white
    "b": (188, 160, 92, 255),    # gold, as the eye's lid
    "m": (128, 102, 52, 255),    # the rail's shaded half
}
SIZE = 24
# (the rail's top row, the knob's left column)
SLIDERS = ((4, 13), (11, 4), (18, 10))
RAIL_X = (2, 21)
KNOB_W, KNOB_H = 6, 6


def grid_rows():
    g = [["."] * SIZE for _ in range(SIZE)]
    x0, x1 = RAIL_X
    for y, kx in SLIDERS:
        # the rail: outline, gold top half, shaded bottom half, outline
        for x in range(x0, x1 + 1):
            g[y - 1][x] = g[y + 2][x] = "k"
            g[y][x], g[y + 1][x] = "b", "m"
        g[y][x0] = g[y + 1][x0] = g[y][x1] = g[y + 1][x1] = "k"
        # the knob: outline, cream face, gold right and bottom edge
        top = y - 2
        for dy in range(KNOB_H):
            for dx in range(KNOB_W):
                edge = dy in (0, KNOB_H - 1) or dx in (0, KNOB_W - 1)
                shade = dy == KNOB_H - 2 or dx == KNOB_W - 2
                g[top + dy][kx + dx] = "k" if edge else ("b" if shade else "a")
    return ["".join(r) for r in g]


def main():
    im = Image.new("RGBA", (SIZE, SIZE))
    for y, row in enumerate(grid_rows()):
        for x, c in enumerate(row):
            im.putpixel((x, y), PALETTE[c])
    im.resize((SIZE * 2, SIZE * 2), Image.NEAREST).save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
