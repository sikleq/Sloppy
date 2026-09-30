"""Our own top-down map picture of one patch, from the game's map files — no screenshots, no third-party tiles.

1. Source2Viewer-CLI exports the map VPK (maps/dota.vmap_c) to glTF with its materials (env S2V_CLI; version
   20.0+ — 19.x can't read Dota's current shaders and leaves the ground white).
2. Blender renders it from straight above with an orthographic camera (scripts/gen/render_map_blender.py), in
   tiles, lit as the map lights itself (env_global_light), over the SAME world rectangle our map images use
   (data/terrain_map_meta.json) — so the site's markers land where they did.
3. The tiles are stitched and scaled to the site's 4096 x 4096 picture.

    set S2V_CLI=C:\\path\\to\\Source2Viewer-CLI.exe
    set BLENDER=C:\\path\\to\\blender.exe
    python scripts/gen/render_map.py 7.41 --work D:\\maprender              # -> <work>/map_7.41.webp
    python scripts/gen/render_map.py 7.41 --work D:\\maprender --px 2048    # a quick look
    python scripts/gen/render_map.py 7.40 --vpk old/dota.vpk --work ...      # a map VPK from an old build
"""
import argparse
import json
import os
import re
import subprocess
import sys

from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAPS_DIR = os.environ.get("DOTA_MAPS", r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota\maps")
SITE_PX = 4096
TILES = 4                                    # must match render_map_blender.TILES
Image.MAX_IMAGE_PIXELS = None


def world_rect():
    """(x0, x1, y_bottom, y_top) in game units of our map images: the crop box of data/terrain_map_meta.json."""
    with open(os.path.join(_ROOT, "data", "terrain_map_meta.json"), encoding="utf-8") as f:
        m = json.load(f)
    (xa, xb), (ya, yb) = m["xBounds"], m["yBounds"]
    sc, cr = m["canvasScale"], m["crop"]
    fx = lambda px: xa + px * sc / m["mapW"] * (xb - xa)
    fy = lambda py: ya + py * sc / m["mapH"] * (yb - ya)
    return fx(cr["x"]), fx(cr["x"] + cr["w"]), fy(cr["y"] + cr["h"]), fy(cr["y"])


def export(vpk, work):
    glb = os.path.join(work, "maps", "dota.glb")
    if os.path.exists(glb):
        return glb
    cli = os.environ.get("S2V_CLI", "")
    if not os.path.exists(cli):
        sys.exit("Set S2V_CLI to Source2Viewer-CLI.exe 20.0+")
    subprocess.run([cli, "-i", vpk, "-f", "maps/dota.vmap_c", "-d", "--gltf_export_format", "glb",
                    "--gltf_export_materials", "--gltf_textures_adapt", "-o", work], check=True,
                   stdout=subprocess.DEVNULL)
    return glb


def _glb_materials(glb):
    """The material names inside a .glb (its JSON chunk)."""
    import struct
    with open(glb, "rb") as f:
        f.read(12)
        length, _ = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(length))
    return sorted({re.sub(r"\.\d{3}$", "", m.get("name", "")) for m in doc.get("materials", [])})


def _vmat(text):
    """{key: value} of a decompiled .vmat's top level (strings, and [r g b a] vectors as lists)."""
    out = {}
    for k, v in re.findall(r'^\s*"([^"]+)"\s+"([^"]*)"', text, re.M):
        vec = re.fullmatch(r"\[([-\d.e ]+)\]", v.strip())
        out.setdefault(k, [float(x) for x in vec.group(1).split()] if vec else v)
    return out


def blend_manifest(glb, work, pak):
    """The map's ground materials (Source 2 "multiblend": up to four texture layers mixed by per-vertex weights)
    that the glTF exporter flattens to their first layer: their layers' textures (decompiled next to the .vmat),
    tints and texture scales, for render_map_blender.py to rebuild the blend as the game draws it
    (the formula of ValveResourceFormat's own renderer, Renderer/Shaders/multiblend.frag.slang)."""
    path = os.path.join(work, "blend_materials.json")
    if os.path.exists(path):
        return path
    cli = os.environ["S2V_CLI"]
    names = set(_glb_materials(glb))
    listing = subprocess.run([cli, "-i", pak, "-l", "-e", "vmat_c"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace").stdout
    wanted = [p for p in re.findall(r"^(\S+\.vmat_c)", listing, re.M)
              if os.path.basename(p)[:-7] in names]
    folder = os.path.join(work, "mats")
    for i in range(0, len(wanted), 40):                      # a filter per call keeps the command line short
        subprocess.run([cli, "-i", pak, "-f", ",".join(wanted[i:i + 40]), "-d", "-o", folder], check=True,
                       stdout=subprocess.DEVNULL)
    manifest = {}
    for p in wanted:
        vpath = os.path.join(folder, *p[:-2].split("/"))
        if not os.path.exists(vpath):
            continue
        with open(vpath, encoding="utf-8", errors="replace") as f:
            m = _vmat(f.read())
        if "multiblend" not in str(m.get("shader", "")):
            continue
        here = os.path.dirname(vpath)
        # a texture slot can hold a constant "[0 0 0 0]" instead of a file
        png = lambda key: (os.path.join(here, os.path.basename(m[key]))
                           if isinstance(m.get(key), str) and os.path.exists(os.path.join(here, os.path.basename(m[key])))
                           else "")
        layers = []
        for i in range(4):
            if f"TextureColor{i}" not in m:
                break
            layers.append({"color": png(f"TextureColor{i}"), "reveal": png(f"TextureRevealMask{i}"),
                           "tintmask": png(f"TextureTintMask{i}"),
                           "tint": (m.get(f"g_vColorTint{i}") or [1, 1, 1])[:3],
                           "tintB": (m.get(f"g_vColorTintB{i}") or m.get(f"g_vColorTint{i}") or [1, 1, 1])[:3],
                           "scale": float(m.get(f"g_flTexCoordScale{i}", 1) or 1),
                           "rotate": float(m.get(f"g_flTexCoordRotate{i}", 0) or 0),
                           "offset": (m.get(f"g_vTexCoordOffset{i}") or [0, 0])[:2]})
        manifest[os.path.basename(p)[:-7]] = {"layers": layers, "tintmask": m.get("F_TINT_MASK") == "1"}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    return path


def render(glb, work, px, manifest):
    blender = os.environ.get("BLENDER", "")
    if not os.path.exists(blender):
        sys.exit("Set BLENDER to blender.exe")
    x0, x1, y0, y1 = world_rect()
    out = os.path.join(work, f"render_{px}")
    subprocess.run([blender, "-b", "--factory-startup", "-P",
                    os.path.join(_ROOT, "scripts", "gen", "render_map_blender.py"), "--",
                    glb, out, str(x0), str(x1), str(y0), str(y1), str(px), "render", manifest], check=True)
    return out


def stitch(out):
    rows = [[Image.open(f"{out}.tile_{r}_{c}.png").convert("RGB") for c in range(TILES)] for r in range(TILES)]
    tw, th = rows[0][0].size
    full = Image.new("RGB", (tw * TILES, th * TILES))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            full.paste(im, (c * tw, r * th))
    return full


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version")
    ap.add_argument("--work", required=True, help="a folder outside the repo (the export is ~160 MB)")
    ap.add_argument("--vpk", help="the map VPK (default: the game's live maps/dota.vpk)")
    ap.add_argument("--px", type=int, default=8192, help="render width before scaling to the site's 4096")
    args = ap.parse_args()
    os.makedirs(args.work, exist_ok=True)
    glb = export(args.vpk or os.path.join(MAPS_DIR, "dota.vpk"), args.work)
    manifest = blend_manifest(glb, args.work, os.path.join(os.path.dirname(MAPS_DIR), "pak01_dir.vpk"))
    full = stitch(render(glb, args.work, args.px, manifest))
    full.save(os.path.join(args.work, f"map_{args.version}_full.png"))
    site = full.resize((SITE_PX, SITE_PX), Image.LANCZOS)          # the crop is 9176 x 9578: as our images, squeezed
    path = os.path.join(args.work, f"map_{args.version}.webp")
    site.save(path, "WEBP", quality=88, method=6)
    print(path, full.size)


if __name__ == "__main__":
    main()
