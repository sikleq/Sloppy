"""Generate dyn-cell gem icons from icons/ref/gems.png.

Takes the reference pixel gem (emerald cut, purple/pink facets), squashes it
to the square dyn-cell proportions (24x24 CSS px, rendered at 2x = 48px) and
recolors it into every dynamics tag color (DYN_TAG_RGB in scripts.js),
preserving the pixel facet shading: per-pixel VALUE (brightness) survives,
hue/saturation are replaced by the tag color. The dark outline stays dark.

Output: icons/dyn_gems/gem_<tag>.png (48x48) + gem_preview.png contact sheet.
"""
import colorsys
import os

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "icons", "ref", "gems.png")
OUT_DIR = os.path.join(HERE, "icons", "dyn_gems")

# Must mirror DYN_TAG_RGB in scripts.js
TAG_RGB = {
    "buff":   (93, 177, 78),
    "new":    (220, 175, 95),
    "rework": (164, 114, 207),
    "misc":   (139, 144, 153),
    "qol":    (108, 171, 240),
    "del":    (177, 78, 107),
    "nerf":   (209, 75, 75),
}
SIZE = 48          # output canvas (2x of the 24px dyn-cell)
INSET = 1          # transparent margin so the outline isn't clipped


def content_bbox(img):
    """Bounding box of non-white, non-transparent pixels."""
    px = img.load()
    w, h = img.size
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 10 and not (r > 245 and g > 245 and b > 245):
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def native_grid(img):
    """The art uses big uniform pixels — find the cell size by scanning for
    the most common run length of identical pixels along rows."""
    px = img.load()
    w, h = img.size
    runs = {}
    for y in range(0, h, max(1, h // 24)):
        run = 1
        for x in range(1, w):
            if px[x, y] == px[x - 1, y]:
                run += 1
            else:
                if run < w:
                    runs[run] = runs.get(run, 0) + 1
                run = 1
    if not runs:
        return 1
    # smallest run that appears often = native pixel size
    common = sorted(runs.items(), key=lambda kv: (-kv[1], kv[0]))
    sizes = [r for r, n in common if n >= max(runs.values()) * 0.25]
    return max(1, min(sizes))


def recolor(img, rgb):
    """Replace hue/sat with the tag color, keep per-pixel V (facet shading).
    Very dark pixels (outline) stay as-is; near-white sparkles stay white."""
    th, ts, tv = colorsys.rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    src = img.load()
    dst = out.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a == 0:
                continue
            _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if v < 0.22:                       # dark outline — keep
                dst[x, y] = (r, g, b, a)
                continue
            if s < 0.12 and v > 0.85:          # white sparkle — keep
                dst[x, y] = (r, g, b, a)
                continue
            # Facet: tag hue, saturation pulled toward the tag's own,
            # brightness from the source pixel (this keeps the cut pattern).
            ns = min(1.0, ts * (0.55 + 0.65 * s))
            nv = v
            nr, ng, nb = colorsys.hsv_to_rgb(th, ns, nv)
            dst[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
    return out


def make_mask_and_facets(base):
    """Two layers for the live dyn-cell:
    * gem_mask.png   — opaque where the gem is (shape mask for the fluid
                       gradient, outline included).
    * gem_facets.png — translucent facet shading designed to sit OVER any
                       color: outline/sparkles opaque, facets encoded as
                       white/black with alpha proportional to how much
                       lighter/darker they are than the gem's median tone.
    """
    px = base.load()
    w, h = base.size
    # median facet brightness (excluding outline/transparent)
    vals = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if v >= 0.22:
                vals.append(v)
    vals.sort()
    v_mid = vals[len(vals) // 2] if vals else 0.7

    # IMPORTANT: CSS mask-image clips by the image's ALPHA channel
    # (mask-mode: match-source → alpha for raster images). A plain "L"
    # grayscale PNG has implicit alpha=255 everywhere and clips NOTHING —
    # the shape must live in the alpha channel.
    mask = Image.new("L", base.size, 0)
    facets = Image.new("RGBA", base.size, (0, 0, 0, 0))
    mpx, fpx = mask.load(), facets.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            mpx[x, y] = 255
            _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if v < 0.22:                      # dark outline — opaque
                fpx[x, y] = (r, g, b, 235)
            elif s < 0.12 and v > 0.85:       # white sparkle
                fpx[x, y] = (255, 255, 255, 215)
            else:
                d = v - v_mid
                if d >= 0:
                    fpx[x, y] = (255, 255, 255, min(160, int(d * 420)))
                else:
                    fpx[x, y] = (0, 0, 0, min(170, int(-d * 460)))
    return mask, facets


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    src = Image.open(SRC).convert("RGBA")
    x0, y0, x1, y1 = content_bbox(src)
    gem = src.crop((x0, y0, x1, y1))
    # White background inside the crop → transparent
    px = gem.load()
    for y in range(gem.height):
        for x in range(gem.width):
            r, g, b, a = px[x, y]
            if r > 245 and g > 245 and b > 245:
                px[x, y] = (0, 0, 0, 0)
    cell = native_grid(gem)
    # Downscale to the native pixel grid (true pixel-art resolution)…
    gw, gh = max(1, round(gem.width / cell)), max(1, round(gem.height / cell))
    small = gem.resize((gw, gh), Image.NEAREST)
    # …squash to the SQUARE dyn-cell shape at half the canvas (24 logical px
    # is too small for this cut; 22px logical inside 24 keeps the outline)…
    target = SIZE // 2 - INSET * 2
    squared = small.resize((target, target), Image.NEAREST)
    # …then 2x for crisp rendering at 24 CSS px.
    canvas = Image.new("RGBA", (SIZE // 2, SIZE // 2), (0, 0, 0, 0))
    canvas.paste(squared, (INSET, INSET), squared)
    base = canvas.resize((SIZE, SIZE), Image.NEAREST)

    mask, facets = make_mask_and_facets(base)
    mask_rgba = Image.new("RGBA", mask.size, (255, 255, 255, 0))
    mask_rgba.putalpha(mask)
    mask_rgba.save(os.path.join(OUT_DIR, "gem_mask.png"))
    facets.save(os.path.join(OUT_DIR, "gem_facets.png"))
    print("  gem_mask.png + gem_facets.png (live-cell layers)")

    sheet = Image.new("RGBA", ((SIZE + 6) * len(TAG_RGB) + 6, SIZE + 12),
                      (13, 17, 23, 255))
    for i, (tag, rgb) in enumerate(TAG_RGB.items()):
        gem_t = recolor(base, rgb)
        gem_t.save(os.path.join(OUT_DIR, f"gem_{tag}.png"))
        sheet.paste(gem_t, (6 + i * (SIZE + 6), 6), gem_t)
        print(f"  gem_{tag}.png")
    sheet.save(os.path.join(OUT_DIR, "gem_preview.png"))
    print("  gem_preview.png (contact sheet)")


if __name__ == "__main__":
    main()
