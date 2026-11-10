"""The tag marks' icons as CSS masks (owner 2026-11-06: tags as small squares on the panel's left line, "Buff это
стрелочка вверх, Nerf это стрелочка вниз, New это плюсик, Del это крестик, Swap это 2 стрелочки меняющиеся и т.д, цвета
сохранить"). Prints the block for src/css/patch-tag-marks.css between its markers.

    python scripts/gen/gen_tag_marks_css.py --write
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSS = ROOT / "src" / "css" / "patch-tag-marks.css"
BEGIN, END = "/* generated icons: begin */", "/* generated icons: end */"

# 14 x 14 strokes, thicker and clearer than the first 12 x 12 set (owner 2026-11-06: "лучше и чётче оформить значки",
# mock variant 2); the order is the cascade: a "del nerf" badge shows the cross
ICONS = [
    ("misc", "M3.5 7h.01M7 7h.01M10.5 7h.01", 2.9),
    ("qol", "M2.6 7.4l3 3L11.4 3.8", 2),
    ("buff", "M7 12V2.6M3 6.6l4-4 4 4", 2),
    ("nerf", "M7 2v9.4M3 7.4l4 4 4-4", 2),
    ("new", "M7 2.3v9.4M2.3 7h9.4", 2),
    # a filled gear drawn like the owner's reference picture, shown 16px (2026-11-07; tried and rejected: Phosphor's
    # gear, a blob at 12 px; pixel gears on 12 and 16 grids, "маленькая и толстая", "опять ужасная"; a wrench with a
    # screwdriver): 8 trapezoid teeth, a thick ring, a round hole
    ("rework", "GEAR", None),
    # two arrows on a round orbit (owner 2026-11-06: "иконку свапа поменяй на стрелочки с более круговой орбитой"; the
    # straight ones before)
    ("swap", "M2.7 5.6A4.6 4.6 0 0 1 10.9 4M11.5 1.7v2.9H8.6M11.3 8.4A4.6 4.6 0 0 1 3.1 10M2.5 12.3V9.4h2.9", 1.9),
    ("del", "M3.3 3.3l7.4 7.4M10.7 3.3l-7.4 7.4", 2),
]


GEAR_BOX = 16      # the gear's own viewBox and its size in px, bigger than the 12px of the line icons


def gear_path(r_body=5.3, r_hole=2.6, r_root=4.8, r_tip=7.7, w_root=3.6, w_tip=2.6, teeth=8):
    """A filled gear as the owner's reference picture (2026-11-07): a ring, 8 trapezoid teeth, a round hole. The ring
    and teeth run clockwise, the hole the other way: the nonzero fill leaves the hole empty."""
    c = GEAR_BOX / 2

    def f(v):
        return f"{v:.2f}".rstrip("0").rstrip(".")

    parts = [f"M{f(c)} {f(c - r_body)}A{f(r_body)} {f(r_body)} 0 1 1 {f(c)} {f(c + r_body)}"
             f"A{f(r_body)} {f(r_body)} 0 1 1 {f(c)} {f(c - r_body)}z"]
    for k in range(teeth):
        a = k * 2 * math.pi / teeth
        ux, uy, vx, vy = math.sin(a), -math.cos(a), math.cos(a), math.sin(a)      # outwards, along the rim
        pts = [(r_root, -w_root / 2), (r_tip, -w_tip / 2), (r_tip, w_tip / 2), (r_root, w_root / 2)]
        parts.append("M" + "L".join(f"{f(c + r * ux + s * vx)} {f(c + r * uy + s * vy)}" for r, s in pts) + "z")
    parts.append(f"M{f(c)} {f(c - r_hole)}A{f(r_hole)} {f(r_hole)} 0 1 0 {f(c)} {f(c + r_hole)}"
                 f"A{f(r_hole)} {f(r_hole)} 0 1 0 {f(c)} {f(c - r_hole)}z")
    return "".join(parts)


def data_uri(path, width):
    if path == "GEAR":
        svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {GEAR_BOX} {GEAR_BOX}' fill='black'>"
               f"<path d='{gear_path()}'/></svg>")
        return "data:image/svg+xml," + svg.replace("<", "%3C").replace(">", "%3E")
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 14 14' fill='none' stroke='black' "
           f"stroke-width='{width}' stroke-linecap='round' stroke-linejoin='round'><path d='{path}'/></svg>")
    return "data:image/svg+xml," + svg.replace("<", "%3C").replace(">", "%3E")


def block():
    # the same icon on the tag's tile in the filter window (owner 2026-11-07: "использовать иконки-закладки")
    rows = [f'.tag-marks .badge[data-tag~="{tag}"], .filter-btn[data-filter="{tag}"] {{ --tm: url("{data_uri(path, w)}"); }}'
            for tag, path, w in ICONS]
    # the gear bigger than the 12px of the line icons (owner 2026-11-07: "какая-то маленькая и толстая была")
    n = GEAR_BOX
    rows.append(f'.tag-marks ul.changes > li > .badge[data-tag~="rework"]::before, .tag-marks .formula-change-title > '
                f'.badge[data-tag~="rework"]::before, .tag-marks .properties-change '
                f'.property-tag .badge[data-tag~="rework"]::before {{ width: {n}px; height: {n}px; }}')
    return "\n".join([BEGIN] + rows + [END])


def main():
    text = block()
    if "--write" in sys.argv:
        css = CSS.read_text(encoding="utf-8")
        start, end = css.index(BEGIN), css.index(END) + len(END)
        CSS.write_text(css[:start] + text + css[end:], encoding="utf-8")
        print(CSS)
    else:
        print(text)


if __name__ == "__main__":
    main()
