# -*- coding: utf-8 -*-
"""One-image patch summary (PNG): who was touched and how, streaks, untouched, biggest swings.

Usage:  python tools/patch_infographic.py 7.41f            -> outputs/infographic/7.41f.png
        python tools/patch_infographic.py 7.41f --out x.png

Inputs (all produced by the site build):
  dist/patches/<v>.html   the built page — tags + delta badges AFTER manual review
  _dynamics.json          per-entity tag counts per annotated patch (streaks / untouched)
  icons/heroes, icons/items
Fonts: Reaver / Radiance from the Dota 2 client (fallback: Arial).

Streaks/untouched are computed over the ANNOTATED patches only (content/p*.py), because
_dynamics.json has no rows for patches without a page. The footer states the sample.
"""
import sys, os, re, json, argparse
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota\panorama\fonts"

# ---- palette ------------------------------------------------------------------------------
BG = (230, 224, 211)
CARD = (243, 239, 230)
INK = (34, 30, 26)
MUTED = (112, 104, 92)
LINE = (200, 191, 174)
TAG = {"buff": (40, 148, 74), "nerf": (196, 62, 54), "rework": (208, 130, 24),
       "new": (52, 120, 200), "del": (105, 105, 105), "misc": (150, 145, 135), "qol": (95, 150, 170)}
TAG_LABEL = {"buff": "BUFF", "nerf": "NERF", "rework": "REWORK", "new": "NEW", "del": "REMOVED",
             "misc": "MISC", "qol": "QoL"}

W = 1600
PAD = 48
HERO_AR = 256 / 144   # Valve hero art
ITEM_AR = 88 / 64     # Valve item art


def font(name, size):
    cands = [os.path.join(FONT_DIR, name),
             r"C:\Windows\Fonts\arialbd.ttf" if ("bold" in name or "black" in name or "semibold" in name)
             else r"C:\Windows\Fonts\arial.ttf"]
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            continue
    return ImageFont.load_default()


F_TITLE = font("reaver-bold.otf", 64)
F_H = font("reaver-semibold.otf", 30)
F_SUB = font("radiance-semibold.otf", 20)
F_BODY = font("radiance-regular.otf", 18)
F_SMALL = font("radiance-semibold.otf", 15)
F_TINY = font("radiance-regular.otf", 13)
F_NUM = font("reaver-bold.otf", 18)


# ---- data ---------------------------------------------------------------------------------
_ENTITY_RE = re.compile(r'<div class="entity (hero|item)-entity" id="dyn-(hero|item)-([a-z0-9-]+)">.*?'
                        r'src="\.\./icons/(?:heroes|items)/([a-z0-9_]+)\.png" alt="([^"]*)"', re.S)
_ROW_RE = re.compile(r'<li data-tag="([a-z]+)"(.*?)</li>', re.S)
_PCT_RE = re.compile(r'<span class="badge (?:buff|nerf)\d+">([+\-\u2212]?\d+(?:\.\d+)?)%</span>')


def parse_page(html):
    """Entities from the BUILT page. Per entity: tag counts + the page's own delta badges
    (first badge per row = the headline delta). ±100% steps (armor 0->-1, recipe doubling) skipped."""
    out = []
    for b in html.split('<div class="entity-block">')[1:]:
        m = _ENTITY_RE.search(b)
        if not m:
            continue
        tags, deltas = {}, []
        for tag, body in _ROW_RE.findall(b):
            tags[tag] = tags.get(tag, 0) + 1
            pm = _PCT_RE.search(body)
            if pm:
                d = abs(float(pm.group(1).replace("\u2212", "-")))
                if d < 100:
                    deltas.append(d)
        out.append({"id": m.group(4), "name": m.group(5), "type": m.group(1), "tags": tags,
                    "net": tags.get("buff", 0) - tags.get("nerf", 0),
                    "mag": (sum(deltas) / len(deltas)) if deltas else 0.0})
    return out


def load(version):
    dyn = json.load(open(os.path.join(HERE, "_dynamics.json"), encoding="utf-8"))
    meta = next(p for p in dyn["patches"] if p["version"] == version)
    html = open(os.path.join(HERE, "dist", "patches", f"{version}.html"), encoding="utf-8").read()
    return parse_page(html), dyn, meta


def annotated_order(dyn, version):
    """Annotated patches, newest first, starting at <version> (only those with a content page)."""
    have = {v for e in dyn["entities"].values() for v in e.get("patches", {})} | {version}
    order = [p["version"] for p in dyn["patches"] if p["version"] in have]
    return order[order.index(version):]


def streaks_and_untouched(dyn, order, kind):
    streak, untouched = [], []
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
            if not t:
                break
            s += 1
        if s >= 2:
            streak.append((s, ent["name"], ent["icon"], None))
        if not touched[0]:
            gap = touched.index(True) if True in touched else len(touched)
            untouched.append((gap, ent["name"], ent["icon"], order[gap] if gap < len(order) else None))
    streak.sort(key=lambda x: (-x[0], x[1]))
    untouched.sort(key=lambda x: (-x[0], x[1]))
    return streak, untouched


# ---- drawing helpers ----------------------------------------------------------------------
def icon(kind, slug, w):
    """Icon at width w with Valve's native aspect ratio (no stretching)."""
    ar = HERO_AR if kind == "hero" else ITEM_AR
    size = (int(w), int(round(w / ar)))
    p = os.path.join(HERE, "icons", "heroes" if kind == "hero" else "items", f"{slug}.png")
    im = Image.open(p).convert("RGBA") if os.path.exists(p) else Image.new("RGBA", size, (190, 184, 172, 255))
    return im.resize(size, Image.LANCZOS)


def rounded(im, r):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], r, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def text_w(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def fit(draw, s, f, w):
    while text_w(draw, s, f) > w and len(s) > 3:
        s = s[:-2].rstrip() + "…"
    return s


def glyph(draw, x, cy, shape, col, r=4):
    if shape == "up":
        draw.polygon([(x, cy + r), (x + 2 * r, cy + r), (x + r, cy - r)], fill=col)
    elif shape == "down":
        draw.polygon([(x, cy - r), (x + 2 * r, cy - r), (x + r, cy + r)], fill=col)
    else:
        draw.polygon([(x + r, cy - r), (x + 2 * r, cy), (x + r, cy + r), (x, cy)], fill=col)


def net_color(s):
    if s["net"] > 0:
        return TAG["buff"]
    if s["net"] < 0:
        return TAG["nerf"]
    return TAG["rework"] if (s["tags"].get("rework") or s["tags"].get("new")) else TAG["misc"]


def section(draw, y, title, sub=None):
    draw.text((PAD, y), title.upper(), font=F_H, fill=INK)
    if sub:
        draw.text((PAD + text_w(draw, title.upper(), F_H) + 16, y + 9), sub, font=F_BODY, fill=MUTED)
    draw.line([PAD, y + 40, W - PAD, y + 40], fill=LINE, width=2)
    return y + 52


def tile(canvas, draw, x, y, s, kind, cell_w):
    iw = cell_w - 10
    im = rounded(icon(kind, s["id"], iw), 7)
    ih = im.size[1]
    draw.rounded_rectangle([x - 2, y - 2, x + iw + 2, y + ih + 2], 9, fill=net_color(s))
    canvas.alpha_composite(im, (x, y))
    ty = y + ih + 6
    draw.text((x, ty), fit(draw, s["name"], F_SMALL, iw), font=F_SMALL, fill=INK)
    ty += 19
    px = x
    for shape, key in (("up", "buff"), ("down", "nerf"), ("diamond", "rework"), ("diamond", "new"), ("diamond", "del")):
        n = s["tags"].get(key)
        if not n:
            continue
        glyph(draw, px, ty + 8, shape, TAG[key])
        draw.text((px + 11, ty), str(n), font=F_SMALL, fill=TAG[key])
        px += 11 + text_w(draw, str(n), F_SMALL) + 7
    if s["mag"]:
        m = f"{'+' if s['net'] > 0 else '\u2212' if s['net'] < 0 else '\u00b1'}{s['mag']:.0f}%"
        draw.text((x + iw - text_w(draw, m, F_SMALL), ty), m, font=F_SMALL, fill=MUTED)
    return ih + 6 + 19 + 22


def grid(canvas, draw, y, entries, kind, cols):
    cell_w = (W - 2 * PAD) // cols
    ih = int(round((cell_w - 10) / (HERO_AR if kind == "hero" else ITEM_AR)))
    cell_h = ih + 6 + 19 + 22 + 8
    for i, s in enumerate(entries):
        r, c = divmod(i, cols)
        tile(canvas, draw, PAD + 2 + c * cell_w, y + r * cell_h, s, kind, cell_w)
    return y + ((len(entries) + cols - 1) // cols) * cell_h


def strip(canvas, draw, y, label, col, entries, kind, badge_fn, max_n=12, label_w=190):
    """One compact row: label at the left, then small icons with a badge (no names — the
    icon is the name; name goes under only when narrow enough to read)."""
    l1, l2 = label.split("\n") if "\n" in label else (label, "")
    draw.text((PAD, y + 4), l1, font=F_SUB, fill=col)
    if l2:
        draw.text((PAD, y + 30), l2, font=F_BODY, fill=MUTED)
    entries = entries[:max_n]
    if not entries:
        draw.text((PAD + label_w, y + 8), "\u2014", font=F_BODY, fill=MUTED)
        return y + 44
    x0 = PAD + label_w
    cell_w = (W - PAD - x0) // max_n
    iw = cell_w - 10
    ih = 0
    for i, (n, name, slug, last) in enumerate(entries):
        x = x0 + i * cell_w
        im = rounded(icon(kind, slug, iw), 6)
        ih = im.size[1]
        canvas.alpha_composite(im, (x, y))
        badge = badge_fn(n, last)
        bf = F_NUM if len(badge) <= 3 else F_TINY
        bw = text_w(draw, badge, bf) + 10
        draw.rounded_rectangle([x + iw - bw, y - 6, x + iw + 3, y + 14], 6, fill=INK)
        draw.text((x + iw - bw + 5, y - 6 + (0 if bf is F_NUM else 2)), badge, font=bf, fill=CARD)
        draw.text((x, y + ih + 3), fit(draw, name, F_TINY, iw), font=F_TINY, fill=MUTED)
    return y + ih + 26


def swing_list(canvas, draw, x, y, title, col, lst, colw):
    draw.text((x, y), title, font=F_SUB, fill=col)
    yy = y + 32
    for s in lst:
        im = rounded(icon(s["type"], s["id"], 40), 4)
        canvas.alpha_composite(im, (x, yy + (26 - im.size[1]) // 2))
        draw.text((x + 50, yy + 3), s["name"], font=F_BODY, fill=INK)
        m = f"{'+' if s['net'] > 0 else '\u2212'}{s['mag']:.0f}%"
        draw.text((x + colw - 30 - text_w(draw, m, F_NUM), yy + 3), m, font=F_NUM, fill=col)
        yy += 30
    return yy


# ---- main ---------------------------------------------------------------------------------
def render(version, out):
    ents, dyn, meta = load(version)
    heroes = sorted([s for s in ents if s["type"] == "hero"], key=lambda s: (-s["net"], -s["mag"]))
    items = sorted([s for s in ents if s["type"] == "item"], key=lambda s: (-s["net"], -s["mag"]))
    tag_counts = {}
    for s in ents:
        for t, n in s["tags"].items():
            tag_counts[t] = tag_counts.get(t, 0) + n
    n_changes = sum(tag_counts.values())
    order = annotated_order(dyn, version)
    h_streak, h_untouched = streaks_and_untouched(dyn, order, "hero")
    i_streak, i_untouched = streaks_and_untouched(dyn, order, "item")
    swings = sorted([s for s in ents if s["mag"] and s["net"] != 0], key=lambda s: -s["mag"])
    top_nerf = [s for s in swings if s["net"] < 0][:5]
    top_buff = [s for s in swings if s["net"] > 0][:5]

    canvas = Image.new("RGBA", (W, 4000), BG + (255,))
    draw = ImageDraw.Draw(canvas)

    # header
    draw.text((PAD, 34), f"PATCH {version}", font=F_TITLE, fill=INK)
    right = f"{meta['date']}   \u00b7   {n_changes} changes   \u00b7   {len(heroes)} heroes   \u00b7   {len(items)} items"
    draw.text((W - PAD - text_w(draw, right, F_SUB), 66), right, font=F_SUB, fill=MUTED)
    by0 = 118
    total = max(1, sum(tag_counts.values()))
    x = PAD
    for t in ("buff", "nerf", "rework", "new", "del", "misc", "qol"):
        n = tag_counts.get(t, 0)
        if not n:
            continue
        w = int((W - 2 * PAD) * n / total)
        draw.rounded_rectangle([x, by0, x + w - 3, by0 + 24], 5, fill=TAG[t])
        lab = f"{TAG_LABEL[t]} {n}"
        if text_w(draw, lab, F_SMALL) + 12 < w:
            draw.text((x + 8, by0 + 4), lab, font=F_SMALL, fill=(255, 255, 255))
        x += w
    small = [f"{TAG_LABEL[t]} {n}" for t, n in tag_counts.items()
             if text_w(draw, f"{TAG_LABEL[t]} {n}", F_SMALL) + 12 >= int((W - 2 * PAD) * n / total)]
    if small:
        draw.text((PAD, by0 + 30), "also: " + ", ".join(small), font=F_TINY, fill=MUTED)
    y = by0 + 62

    y = section(draw, y, "Heroes", "frame = net direction  ·  % = mean size of the numeric changes")
    lx = W - PAD - 250
    for shape, key, lab in (("up", "buff", "buffs"), ("down", "nerf", "nerfs"), ("diamond", "rework", "rework/new/removed")):
        glyph(draw, lx, y - 35, shape, TAG[key])
        draw.text((lx + 12, y - 44), lab, font=F_SMALL, fill=MUTED)
        lx += 12 + text_w(draw, lab, F_SMALL) + 14
    y = grid(canvas, draw, y, heroes, "hero", 10) + 12
    y = section(draw, y, "Items")
    y = grid(canvas, draw, y, items, "item", 12) + 12

    n_ann = len(order)
    y = section(draw, y, "Trend", f"over the {n_ann} annotated patches, {order[-1]} to {version}")
    y = strip(canvas, draw, y, "On a streak\nheroes", TAG["nerf"], h_streak, "hero", lambda n, l: f"{n}x")
    y = strip(canvas, draw, y, "Untouched\nheroes", TAG["buff"], h_untouched, "hero",
              lambda n, l: (f"since {l}" if l else "never"))
    y = strip(canvas, draw, y, "On a streak\nitems", TAG["nerf"], i_streak, "item", lambda n, l: f"{n}x")
    y = strip(canvas, draw, y, "Untouched\nitems", TAG["buff"], i_untouched, "item",
              lambda n, l: (f"since {l}" if l else "never"))
    y += 8

    y = section(draw, y, "Biggest swings", "mean |\u0394%| over the entity's numeric rows")
    colw = (W - 2 * PAD) // 2
    y1 = swing_list(canvas, draw, PAD, y, "Hit hardest", TAG["nerf"], top_nerf, colw)
    y2 = swing_list(canvas, draw, PAD + colw, y, "Biggest gifts", TAG["buff"], top_buff, colw)
    y = max(y1, y2) + 16
    draw.line([PAD, y, W - PAD, y], fill=LINE, width=1)
    draw.text((PAD, y + 10), "sikleq.github.io/Sloppy  \u00b7  built from the annotated patch page", font=F_TINY, fill=MUTED)

    canvas = canvas.crop((0, 0, W, y + 40))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.convert("RGB").save(out, optimize=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("--out")
    a = ap.parse_args()
    print(render(a.version, a.out or os.path.join(HERE, "outputs", "infographic", f"{a.version}.png")))
