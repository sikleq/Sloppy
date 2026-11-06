"""Health / mana regeneration icons for a hero's GENERAL block (owner 2026-11-06: "нужно будет либо достать из игры,
либо придумать … в патчах есть значки регенераций, но там плюсики в квадрате, что мне не нравится"; of five variants
the owner took C: "heart + arrow", then the plus instead of the arrow, variant 5). The game's HUD has none, so the
glyphs come from Phosphor Icons (MIT, no credit needed): heart-fill and drop-fill in the colours of the game's health
and mana bars, with plus-bold on a dark disc in the lower right corner. Writes icons/health_regen.svg and
icons/mana_regen.svg.

    python scripts/gen/gen_regen_icons.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Phosphor Icons 2.x, fill weight, viewBox 0 0 256 256 — https://phosphoricons.com (MIT)
HEART = ("M240,102c0,70-103.79,126.66-108.21,129a8,8,0,0,1-7.58,0C119.79,228.66,16,172,16,102A62.07,62.07,0,0,1,78,40"
         "c20.65,0,38.73,8.88,50,23.89C139.27,48.88,157.35,40,178,40A62.07,62.07,0,0,1,240,102Z")
DROP = ("M174,47.75a254.19,254.19,0,0,0-41.45-38.3,8,8,0,0,0-9.18,0A254.19,254.19,0,0,0,82,47.75C54.51,79.32,40,"
        "112.6,40,144a88,88,0,0,0,176,0C216,112.6,201.49,79.32,174,47.75Zm9.85,105.59a57.6,57.6,0,0,1-46.56,46.55A8.75,"
        "8.75,0,0,1,136,200a8,8,0,0,1-1.32-15.89c16.57-2.79,30.63-16.85,33.44-33.45a8,8,0,0,1,15.78,2.68Z")
# plus-bold: a plus, not the up arrow, which misled on a decrease (owner 2026-11-06: "Base Health Regen decreased by
# 0.25. Там стрелочка вверх, а изменение отрицательное" -> of five variants "вариант значков 5", the plus in the corner)
PLUS = ("M228,128a12,12,0,0,1-12,12H140v76a12,12,0,0,1-24,0V140H40a12,12,0,0,1,0-24h76V40a12,12,0,0,1,24,0v76h76"
        "A12,12,0,0,1,228,128Z")

ICONS = {
    "health_regen": (HEART, "#5fb44a"),     # the health bar's green
    "mana_regen": (DROP, "#4a86e0"),        # the mana bar's blue
}
DISC, PLUS_COLOUR = "#1d1a17", "#e9e3d6"     # the site's tile colour, the plus light


def svg(path, colour):
    # the badge: a disc of r=62 at (194, 194); the plus's own box (28..228, centre 128) scaled 0.375, its centre on the
    # disc's. The drop without its highlight, as in the chosen mock
    path = path.split("Zm")[0] + "Z"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="32" height="32">'
            f'<path fill="{colour}" d="{path}"/>'
            f'<circle cx="194" cy="194" r="62" fill="{DISC}"/>'
            f'<g transform="translate(146 146) scale(0.375)"><path fill="{PLUS_COLOUR}" d="{PLUS}"/></g></svg>\n')


def main():
    for name, (path, colour) in ICONS.items():
        out = ROOT / "icons" / f"{name}.svg"
        out.write_text(svg(path, colour), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
