"""The Source Filmmaker session that renders the whole map top-down (docs/terrain.md, "rendered in Source
Filmmaker"): `sfm_map_session.dmx` next to this script (KeyValues2 text) with its export folder filled in, converted
to SFM's binary by the game's dmxconvert. The camera: 1-degree lens from z 240000, keyed once a second over 6 x 11
frames of 3840 x 2160 in a serpentine — stitch_sfm.py reads that path back to place the frames.

The template is kept in the repo (the owner 2026-10-02: "if you made your own, they'd be handy in the repo too");
the export folder is the placeholder FRAMES_DIR.

    python scripts/gen/sfm_session.py FRAMES_DIR OUT.dmx            # binary, ready for SFM's sessions folder
    python scripts/gen/sfm_session.py FRAMES_DIR OUT.dmx --text     # KeyValues2 text only
"""
import argparse
import os
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(_HERE, "sfm_map_session.dmx")
PLACEHOLDER = '"FRAMES_DIR"'
GAME = os.environ.get("DOTA_GAME", r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game")


def session_text(frames_dir):
    """The template with the export folder set: a KeyValues2 string, backslashes doubled, ending in one."""
    with open(TEMPLATE, encoding="utf-8") as f:
        s = f.read()
    path = os.path.normpath(frames_dir).rstrip("\\/") + "\\"
    return s.replace(PLACEHOLDER, '"' + path.replace("\\", "\\\\") + '"')


def write_session(frames_dir, out, text_only=False, game=GAME):
    """Write the session to `out` (binary unless text_only); returns out."""
    text = out if text_only else os.path.splitext(out)[0] + "_text.dmx"
    with open(text, "w", encoding="utf-8") as f:
        f.write(session_text(frames_dir))
    if not text_only:
        subprocess.run([os.path.join(game, "bin", "win64", "dmxconvert.exe"), "-i", text, "-o", out,
                        "-oe", "binary"], check=True, capture_output=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frames_dir")
    ap.add_argument("out")
    ap.add_argument("--text", action="store_true", help="write the KeyValues2 text, no conversion")
    args = ap.parse_args()
    print(write_session(args.frames_dir, args.out, args.text))


if __name__ == "__main__":
    main()
