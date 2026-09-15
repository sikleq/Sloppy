# -*- coding: utf-8 -*-
"""One-image patch summary (PNG) — icons, arrows, streaks and untouched lists.

Usage:  python tools/patch_infographic.py 7.41f            -> outputs/infographic/7.41f.png
        python tools/patch_infographic.py 7.41f --out x.png

Inputs (all already produced by the site build):
  dist/patches/<v>.html              the built page: tags + delta badges after manual review
  _dynamics.json                     per-entity tag counts per patch (streaks / untouched)
  icons/heroes, icons/items          local Valve art
Fonts: Reaver / Radiance from the Dota 2 client (fallback: Arial).
"""
import sys, os, re, json, argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota\panorama\fonts"

# ---- palette (light background) ------------------------------------------------------------
BG = (246, 242, 234)
BG2 = (255, 253, 248)
INK = (36, 32, 28)
MUTED = (120, 112, 100)
LINE = (214, 206, 192)
TAG = {"buff": (46, 158, 79), "nerf": (201, 70, 61), "rework": (214, 138, 30),
       "new": (52, 120, 200), "del": (110, 110, 110), "misc": (150, 145, 135), "qol": (95, 150, 170)}
TAG_LABEL = {"buff": "BUFF", "nerf": "NERF", "rework": "REWORK", "new": "NEW", "del": "REMOVED",
             "misc": "MISC", "qol": "QoL"}

W = 1600
PAD = 56


def font(name, size):
    for cand in (os.path.join(FONT_DIR, name), r"C:\Windows\Fonts\arialbd.ttf" if "bold" in name or "black" in name
                 else r"C:\Windows\Fonts\arial.ttf"):
        try:
            return ImageFont.truetype(cand, size)
        except OSError:
            continue
    return ImageFont.load_default()


F_TITLE = font("reaver-bold.otf", 84)
F_H = font("reaver-semibold.otf", 34)
F_SUB = font("radiance-semibold.otf", 24)
F_BODY = font("radiance-regular.otf", 20)
F_SMALL = font("radiance-semibold.otf", 16)
F_TINY = font("radiance-regular.otf", 14)
F_NUM = font("reaver-bold.otf", 22)


# ---- data ---------------------------------------------------------------------------------
def load(version):
    dyn = json.load(open(os.path.join(HERE, "_dynamics.json"), encoding="utf-8"))
    meta = next(p for p in dyn["patches"] if p["version"] == version)
    html = open(os.path.join(HERE, "dist", "patches", f"{version}.html"), encoding="utf-8").read()
    return parse_page(html), dyn, meta


_ENTITY_RE = re.compile(r'<div class="entity (hero|item)-entity" id="dyn-(hero|item)-([a-z0-9-]+)">.*?'
                        r'src="\.\./icons/(?:heroes|items)/([a-z0-9_]+)\.png" alt="([^"]*)"', re.S)
_ROW_RE = re.compile(r'<li data-tag="([a-z]+)"(.*?)</li>', re.S)
_PCT_RE = re.compile(r'<span class="badge (?:buff|nerf)\d+">([+\-−]?\d+(?:\.\d+)?)%</span>')


def parse_page(html):
    """Entities from the BUILT page (reflects manual review, unlike the generator's normalized JSON).
    Per entity: tag counts + the page's own delta badges (first badge per row = the headline delta)."""
    blocks = html.split('<div class="entity-block">')[1:]
    out = []
    for b in blocks:
        m = _ENTITY_RE.search(b)
        if not m:
            continue
        kind, slug, name = m.group(1), m.group(4), m.group(5)
        tags, deltas = {}, []
        for tag, body in _ROW_RE.findall(b):
            tags[tag] = tags.get(tag, 0) + 1
            pm = _PCT_RE.search(body)
            if pm:
                d = abs(float(pm.group(1).replace("−", "-")))
                if d < 100:   # 0->-1 armor steps and recipe doublings read as ±100% — not a real "swing"
                    deltas.append(d)
        net = tags.get("buff", 0) - tags.get("nerf", 0)
        out.append({"id": slug, "name": name, "type": kind, "tags": tags, "n": sum(tags.values()),
                    "net": net, "mag": (sum(deltas) / len(deltas)) if deltas else 0.0})
    return out


def streaks_and_untouched(dyn, version, kind):
    """kind: 'hero' | 'item'. Returns (streak list, untouched list) using dynamics' patch order
    (newest first). streak = consecutive patches with any change ending at <version>."""
    order = [p["version"] for p in dyn["patches"]]  # newest first
    i0 = order.index(version)
    order = order[i0:]
    res_streak, res_untouched = [], []
    for key, ent in dyn["entities"].items():
        if ent.get("kind") != kind:
            continue
        if kind == "item":
            it = next((x for x in dyn["items"] if x["key"] == key), None)
            if it and not it.get("current", True):
                continue
        touched = [v in ent.get("patches", {}) for v in order]
        s = 0
        for t in touched:
            if not t: break
            s += 1
        if s >= 2:
            res_streak.append((s, ent["name"], ent["icon"], None))
        if not touched[0]:
            gap = 0
            for t in touched:
                if t: break
                gap += 1
            last = order[gap] if gap < len(order) else None
            res_untouched.append((gap, ent["name"], ent["icon"], last))
    res_streak.sort(key=lambda x: (-x[0], x[1]))
    res_untouched.sort(key=lambda x: (-x[0], x[1]))
    return res_streak, res_untouched


# ---- drawing helpers ----------------------------------------------------------------------
def icon(kind, slug, size):
    p = os.path.join(HERE, "icons", "heroes" if kind == "hero" else "items", f"{slug}.png")
    if not os.path.exists(p):
        im = Image.new("RGBA", size, (200, 195, 185, 255))
    else:
        im = Image.open(p).convert("RGBA")
        im = im.resize(size, Image.LANCZOS)
    return im


def rounded(im, r):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], r, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def shadow_card(canvas, box, r=14, fill=BG2):
    x0, y0, x1, y1 = box
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 2, y0 + 5, x1 + 2, y1 + 5], r, fill=(60, 50, 30, 42))
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    canvas.alpha_composite(sh)
    ImageDraw.Draw(canvas).rounded_rectangle(box, r, fill=fill, outline=LINE)


def text_w(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def section_title(draw, y, title, sub=None):
    draw.text((PAD, y), title.upper(), font=F_H, fill=INK)
    if sub:
        draw.text((PAD + text_w(draw, title.upper(), F_H) + 18, y + 12), sub, font=F_BODY, fill=MUTED)
    draw.line([PAD, y + 48, W - PAD, y + 48], fill=LINE, width=2)
    return y + 66


def glyph(draw, x, cy, shape, col, r=5):
    if shape == "up":
        draw.polygon([(x, cy + r), (x + 2 * r, cy + r), (x + r, cy - r)], fill=col)
    elif shape == "down":
        draw.polygon([(x, cy - r), (x + 2 * r, cy - r), (x + r, cy + r)], fill=col)
    else:
        draw.polygon([(x + r, cy - r), (x + 2 * r, cy), (x + r, cy + r), (x, cy)], fill=col)


def net_color(s):
    if s["net"] > 0: return TAG["buff"]
    if s["net"] < 0: return TAG["nerf"]
    if s["tags"].get("rework") or s["tags"].get("new"): return TAG["rework"]
    return TAG["misc"]


def tile(canvas, draw, x, y, s, kind, cell_w, icon_h):
    """Entity tile: icon with coloured frame, name, ▲/▼ counts and mean |Δ%|."""
    col = net_color(s)
    iw = cell_w - 12
    im = rounded(icon(kind, s["id"], (iw, icon_h)), 8)
    draw.rounded_rectangle([x, y, x + iw + 6, y + icon_h + 6], 10, fill=col)
    canvas.alpha_composite(im, (x + 3, y + 3))
    ty = y + icon_h + 12
    name = s["name"]
    while text_w(draw, name, F_SMALL) > iw and len(name) > 4:
        name = name[:-2] + "…"
    draw.text((x + 3, ty), name, font=F_SMALL, fill=INK)
    parts = []
    if s["tags"].get("buff"): parts.append(("up", str(s["tags"]["buff"]), TAG["buff"]))
    if s["tags"].get("nerf"): parts.append(("down", str(s["tags"]["nerf"]), TAG["nerf"]))
    for t in ("rework", "new", "del"):
        if s["tags"].get(t): parts.append(("diamond", str(s["tags"][t]), TAG[t]))
    px = x + 3
    for shape, txt, c in parts:
        glyph(draw, px, ty + 30, shape, c)
        draw.text((px + 14, ty + 20), txt, font=F_SMALL, fill=c)
        px += 14 + text_w(draw, txt, F_SMALL) + 10
    if s["mag"]:
        m = f"{'+' if s['net'] > 0 else '−' if s['net'] < 0 else '±'}{s['mag']:.0f}%"
        draw.text((x + iw + 3 - text_w(draw, m, F_SMALL), ty + 20), m, font=F_SMALL, fill=MUTED)


def grid(canvas, draw, y, items, kind, cols, icon_h):
    cell_w = (W - 2 * PAD) // cols
    rows = (len(items) + cols - 1) // cols
    cell_h = icon_h + 62
    for i, s in enumerate(items):
        r, c = divmod(i, cols)
        tile(canvas, draw, PAD + c * cell_w, y + r * cell_h, s, kind, cell_w, icon_h)
    return y + rows * cell_h + 10


def strip(canvas, draw, y, entries, kind, label_fmt, icon_h, max_n=12):
    """Row of small icons with a number badge (streaks / untouched)."""
    entries = entries[:max_n]
    if not entries:
        draw.text((PAD, y), "—", font=F_BODY, fill=MUTED); return y + 30
    cell_w = (W - 2 * PAD) // max_n
    iw = cell_w - 14
    for i, (n, name, slug, last) in enumerate(entries):
        x = PAD + i * cell_w
        im = rounded(icon(kind, slug, (iw, icon_h)), 8)
        canvas.alpha_composite(im, (x, y))
        badge = label_fmt(n, last)
        bf = F_NUM if len(badge) <= 4 else F_SMALL
        bw = text_w(draw, badge, bf) + 14
        bh = 30 if bf is F_NUM else 24
        draw.rounded_rectangle([x + iw - bw, y - 8, x + iw + 4, y - 8 + bh], 8, fill=INK)
        draw.text((x + iw - bw + 7, y - 8 + (2 if bf is F_NUM else 3)), badge, font=bf, fill=BG2)
        nm = name
        while text_w(draw, nm, F_TINY) > iw and len(nm) > 4:
            nm = nm[:-2] + "…"
        draw.text((x, y + icon_h + 6), nm, font=F_TINY, fill=INK)
    return y + icon_h + 34


# ---- main ---------------------------------------------------------------------------------
def render(version, out):
    ents, dyn, meta = load(version)
    heroes = sorted([s for s in ents if s["type"] == "hero"], key=lambda s: (-s["net"], -s["mag"]))
    items = sorted([s for s in ents if s["type"] == "item"], key=lambda s: (-s["net"], -s["mag"]))
    other = []
    tag_counts = {}
    for s in ents:
        for t, n in s["tags"].items():
            tag_counts[t] = tag_counts.get(t, 0) + n
    n_changes = sum(tag_counts.values())
    h_streak, h_untouched = streaks_and_untouched(dyn, version, "hero")
    i_streak, i_untouched = streaks_and_untouched(dyn, version, "item")
    swings = sorted([s for s in ents if s["mag"] and s["net"] != 0], key=lambda s: -s["mag"])
    top_nerf = [s for s in swings if s["net"] < 0][:5]
    top_buff = [s for s in swings if s["net"] > 0][:5]

    # layout pass: compute height
    hero_cols, item_cols = 9, 10
    hero_icon_h, item_icon_h = 84, 72
    H = 300
    H += 66 + ((len(heroes) + hero_cols - 1) // hero_cols) * (hero_icon_h + 62) + 30
    H += 66 + ((len(items) + item_cols - 1) // item_cols) * (item_icon_h + 62) + 30
    H += 66 + 2 * (hero_icon_h + 34) + 40   # streak hero + untouched hero
    H += 66 + 2 * (item_icon_h + 34) + 40   # streak item + untouched item
    H += 66 + 200 + 80

    canvas = Image.new("RGBA", (W, H), BG + (255,))
    # soft top wash
    wash = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    for i in range(260):
        a = int(70 * (1 - i / 260))
        wd.line([0, i, W, i], fill=(235, 225, 205, a))
    canvas.alpha_composite(wash)
    draw = ImageDraw.Draw(canvas)

    # header
    draw.text((PAD, 40), f"PATCH {version}", font=F_TITLE, fill=INK)
    draw.text((PAD + 4, 140), f"Dota 2  ·  {meta['date']}  ·  {n_changes} changes  ·  "
                             f"{len(heroes)} heroes  ·  {len(items)} items", font=F_SUB, fill=MUTED)
    # tag bar
    bx0, by0, bx1 = PAD, 190, W - PAD
    total = max(1, sum(tag_counts.values()))
    x = bx0
    order = ["buff", "nerf", "rework", "new", "del", "misc", "qol"]
    for t in order:
        n = tag_counts.get(t, 0)
        if not n: continue
        w = int((bx1 - bx0) * n / total)
        draw.rounded_rectangle([x, by0, x + w - 3, by0 + 26], 6, fill=TAG[t])
        lab = f"{TAG_LABEL[t]} {n}"
        if text_w(draw, lab, F_SMALL) + 10 < w:
            draw.text((x + 8, by0 + 4), lab, font=F_SMALL, fill=(255, 255, 255))
        x += w
    lx = bx0
    for t in order:
        n = tag_counts.get(t, 0)
        if not n: continue
        draw.rounded_rectangle([lx, by0 + 38, lx + 12, by0 + 50], 3, fill=TAG[t])
        lab = f"{TAG_LABEL[t]} {n}"
        draw.text((lx + 18, by0 + 34), lab, font=F_SMALL, fill=INK)
        lx += text_w(draw, lab, F_SMALL) + 40
    y = 270

    y = section_title(draw, y, "Heroes", f"{len(heroes)} touched  ·  ▲ buffs  ▼ nerfs  ◆ rework/new/removed  ·  % = mean size of numeric changes")
    y = grid(canvas, draw, y, heroes, "hero", hero_cols, hero_icon_h)
    y += 20

    y = section_title(draw, y, "Items", f"{len(items)} touched" + (f"  ·  also: {', '.join(o['name'] for o in other)}" if other else ""))
    y = grid(canvas, draw, y, items, "item", item_cols, item_icon_h)
    y += 20

    y = section_title(draw, y, "Streaks & untouched — heroes", "changed in N patches in a row  ·  last touched in patch ...")
    draw.text((PAD, y), "On a streak", font=F_SUB, fill=TAG["nerf"]); y += 34
    y = strip(canvas, draw, y, h_streak, "hero", lambda n, last: f"{n}x", hero_icon_h)
    draw.text((PAD, y), "Untouched the longest", font=F_SUB, fill=TAG["buff"]); y += 34
    y = strip(canvas, draw, y, h_untouched, "hero", lambda n, last: (f"since {last}" if last else "never"), hero_icon_h)
    y += 20

    y = section_title(draw, y, "Streaks & untouched — items")
    draw.text((PAD, y), "On a streak", font=F_SUB, fill=TAG["nerf"]); y += 34
    y = strip(canvas, draw, y, i_streak, "item", lambda n, last: f"{n}x", item_icon_h)
    draw.text((PAD, y), "Untouched the longest", font=F_SUB, fill=TAG["buff"]); y += 34
    y = strip(canvas, draw, y, i_untouched, "item", lambda n, last: (f"since {last}" if last else "never"), item_icon_h)
    y += 20

    y = section_title(draw, y, "Biggest swings", "mean |Δ%| over the entity's numeric rows")
    colw = (W - 2 * PAD) // 2
    for k, (lst, title, col) in enumerate(((top_nerf, "Hit hardest", TAG["nerf"]), (top_buff, "Biggest gifts", TAG["buff"]))):
        x0 = PAD + k * colw
        shadow_card(canvas, (x0, y, x0 + colw - 20, y + 200))
        draw = ImageDraw.Draw(canvas)
        draw.text((x0 + 18, y + 12), title, font=F_SUB, fill=col)
        yy = y + 48
        for s in lst:
            im = rounded(icon("hero" if s["type"] == "hero" else "item", s["id"], (44, 26 if s["type"] == "hero" else 32)), 5)
            canvas.alpha_composite(im, (x0 + 18, yy))
            draw.text((x0 + 72, yy + 2), s["name"], font=F_BODY, fill=INK)
            m = f"{'+' if s['net'] > 0 else '−'}{s['mag']:.0f}%"
            draw.text((x0 + colw - 40 - text_w(draw, m, F_NUM), yy), m, font=F_NUM, fill=col)
            yy += 30
    y += 230
    draw.text((PAD, y), "sikleq.github.io/Sloppy  ·  generated from the annotated patch page", font=F_TINY, fill=MUTED)

    canvas = canvas.crop((0, 0, W, y + 40))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.convert("RGB").save(out, optimize=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("--out")
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "outputs", "infographic", f"{a.version}.png")
    print(render(a.version, out))
