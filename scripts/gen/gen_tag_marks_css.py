"""The tag marks' icons as CSS masks (owner 2026-11-06: tags as small squares on the panel's left line, "Buff это
стрелочка вверх, Nerf это стрелочка вниз, New это плюсик, Del это крестик, Swap это 2 стрелочки меняющиеся и т.д, цвета
сохранить"). Prints the block for src/css/patch-tag-marks.css between its markers.

    python scripts/gen/gen_tag_marks_css.py --write
"""
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
    # a gear (owner 2026-11-06: "Rework тег иконки сделай шестерёнку"): Phosphor gear-six-fill (MIT), filled, its own
    # 256 grid (a width of None)
    ("rework", "M237.94,107.21a8,8,0,0,0-3.89-5.4l-29.83-17-.12-33.62a8,8,0,0,0-2.83-6.08,111.91,111.91,0,0,0-36.72-20.67,"
               "8,8,0,0,0-6.46.59L128,41.85,97.88,25a8,8,0,0,0-6.47-.6A111.92,111.92,0,0,0,54.73,45.15a8,8,0,0,0-2.83,6.07"
               "l-.15,33.65-29.83,17a8,8,0,0,0-3.89,5.4,106.47,106.47,0,0,0,0,41.56,8,8,0,0,0,3.89,5.4l29.83,17,.12,33.63"
               "a8,8,0,0,0,2.83,6.08,111.91,111.91,0,0,0,36.72,20.67,8,8,0,0,0,6.46-.59L128,214.15,158.12,231a7.91,7.91,0,0,0,"
               "3.9,1,8.09,8.09,0,0,0,2.57-.42,112.1,112.1,0,0,0,36.68-20.73,8,8,0,0,0,2.83-6.07l.15-33.65,29.83-17a8,8,0,0,0,"
               "3.89-5.4A106.47,106.47,0,0,0,237.94,107.21ZM128,168a40,40,0,1,1,40-40A40,40,0,0,1,128,168Z", None),
    # two arrows on a round orbit (owner 2026-11-06: "иконку свапа поменяй на стрелочки с более круговой орбитой"; the
    # straight ones before)
    ("swap", "M2.7 5.6A4.6 4.6 0 0 1 10.9 4M11.5 1.7v2.9H8.6M11.3 8.4A4.6 4.6 0 0 1 3.1 10M2.5 12.3V9.4h2.9", 1.9),
    ("del", "M3.3 3.3l7.4 7.4M10.7 3.3l-7.4 7.4", 2),
]


def data_uri(path, width):
    if width is None:                    # a filled icon on its own 256 grid (Phosphor's)
        svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256' fill='black'><path d='{path}'/></svg>"
        return "data:image/svg+xml," + svg.replace("<", "%3C").replace(">", "%3E")
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 14 14' fill='none' stroke='black' "
           f"stroke-width='{width}' stroke-linecap='round' stroke-linejoin='round'><path d='{path}'/></svg>")
    return "data:image/svg+xml," + svg.replace("<", "%3C").replace(">", "%3E")


def block():
    rows = [f'.tag-marks .badge[data-tag~="{tag}"] {{ --tm: url("{data_uri(path, w)}"); }}' for tag, path, w in ICONS]
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
