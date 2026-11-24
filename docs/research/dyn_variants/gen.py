"""Research mock-ups: 4 ways to draw Hero/Item Dynamics rows. Reads dist/_dynamics.json, writes index.html here."""
import json, math, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).with_name("index.html")
D = json.loads((ROOT / "dist/_dynamics.json").read_text(encoding="utf8"))
pats = [p["version"] for p in reversed(D["patches"])]
pats = pats[pats.index("7.34d"):]
KEYS = ["hero|abaddon", "hero|alchemist", "hero|anti-mage", "hero|batrider", "hero|brewmaster",
        "hero|beastmaster", "item|black-king-bar", "item|blink-dagger", "item|battle-fury", "item|bloodstone"]
CW, RH = 26, 30          # cell width, row height
W = CW * len(pats)
CAP = 4.0                # |w| at which a mark is full height / full colour


def series(key):
    p = D["entities"][key]["patches"]
    return [p.get(v, {}) for v in pats]


def mag(w):              # sqrt compresses rare huge reworks
    return math.copysign(min(1, math.sqrt(abs(w) / CAP)), w)


def colour(t):           # t in -1..1 -> red..grey..green
    a = abs(t)
    base = (90, 84, 74)
    tgt = (76, 200, 110) if t > 0 else (220, 80, 100)
    return "rgb(%d,%d,%d)" % tuple(round(b + (g - b) * a) for b, g in zip(base, tgt))


def smooth(pts):         # Catmull-Rom -> cubic Bezier path
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def svg(body):
    return f'<svg width="{W}" height="{RH}" viewBox="0 0 {W} {RH}">{body}</svg>'


def grid():
    return "".join(f'<line x1="{i*CW}" x2="{i*CW}" y1="0" y2="{RH}" class="g"/>' for i in range(1, len(pats)))


def v_cumulative(s):
    """A: running sum of w, smooth, coloured fill above/below zero; scale per row."""
    acc, ys = 0, []
    for c in s:
        acc += c.get("w", 0)
        ys.append(acc)
    m = max(1e-6, max(abs(y) for y in ys))
    mid = RH / 2
    pts = [(i * CW + CW / 2, mid - y / m * (mid - 3)) for i, y in enumerate(ys)]
    path = smooth(pts)
    area = f"{path} L{pts[-1][0]},{mid} L{pts[0][0]},{mid} Z"
    cid = "c" + str(abs(hash(path)) % 10**8)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.8" fill="{colour(mag(c["w"]))}"/>'
                   for (x, y), c in zip(pts, s) if c.get("w"))
    return svg(grid() +
               f'<clipPath id="{cid}u"><rect width="{W}" height="{mid}"/></clipPath>'
               f'<clipPath id="{cid}d"><rect y="{mid}" width="{W}" height="{mid}"/></clipPath>'
               f'<path d="{area}" fill="rgba(76,200,110,.28)" clip-path="url(#{cid}u)"/>'
               f'<path d="{area}" fill="rgba(220,80,100,.28)" clip-path="url(#{cid}d)"/>'
               f'<line x1="0" x2="{W}" y1="{mid}" y2="{mid}" class="z"/>'
               f'<path d="{path}" fill="none" stroke="#e8c070" stroke-width="1.4"/>' + dots)


def v_wave(s):
    """B: continuous zero line; each patch a smooth hump up (buff) / down (nerf), height = strength."""
    mid = RH / 2
    pts = [(0, mid)]
    for i, c in enumerate(s):
        pts.append((i * CW + CW / 2, mid - mag(c.get("w", 0)) * (mid - 2)))
    pts.append((W, mid))
    path = smooth(pts)
    area = f"{path} L{W},{mid} L0,{mid} Z"
    cid = "w" + str(abs(hash(path)) % 10**8)
    return svg(grid() +
               f'<clipPath id="{cid}u"><rect width="{W}" height="{mid}"/></clipPath>'
               f'<clipPath id="{cid}d"><rect y="{mid}" width="{W}" height="{mid}"/></clipPath>'
               f'<path d="{area}" fill="rgba(76,200,110,.45)" clip-path="url(#{cid}u)"/>'
               f'<path d="{area}" fill="rgba(220,80,100,.45)" clip-path="url(#{cid}d)"/>'
               f'<path d="{path}" fill="none" stroke="#c9b48a" stroke-width="1"/>')


def v_heat(s):
    """C: one colour cell per patch, red..grey..green by strength; mixed patch = striped."""
    out = grid()
    for i, c in enumerate(s):
        if "v" not in c and not c:
            continue
        w = c.get("w", 0)
        mixed = c.get("v", 0) > 0.5 and abs(w) < 0.25 * c.get("v", 0)
        fill = "url(#mix)" if mixed else colour(mag(w))
        out += f'<rect x="{i*CW+2}" y="5" width="{CW-4}" height="{RH-10}" rx="1" fill="{fill}"/>'
    return svg(out)


def v_bars(s):
    """D: thin unbroken baseline + bar up/down, height = strength; gray tick = changes that cancel out."""
    mid = RH / 2
    out = grid() + f'<line x1="0" x2="{W}" y1="{mid}" y2="{mid}" class="base"/>'
    for i, c in enumerate(s):
        if not c:
            continue
        t = mag(c.get("w", 0))
        h = abs(t) * (mid - 2)
        x = i * CW + 7
        if h < 1.5:
            out += f'<rect x="{x}" y="{mid-1}" width="{CW-14}" height="2" fill="#8a8072"/>'
        else:
            y = mid - h if t > 0 else mid
            out += f'<rect x="{x}" y="{y:.1f}" width="{CW-14}" height="{h:.1f}" fill="{colour(t)}"/>'
    return svg(out)


VARIANTS = [
    ("A", "Накопительная кривая", v_cumulative,
     "Линия = сумма всех правок с 7.34d. Вверх = герой в сумме сильнее, вниз = слабее. Без изменений линия идёт ровно."),
    ("B", "Волна от нуля", v_wave,
     "Линия всегда на середине; в патче с правкой — плавный горб вверх (бафф) или яма вниз (нерф), высота = сила."),
    ("C", "Цветные клетки", v_heat,
     "Клетка на патч, цвет от ярко-красного (сильный нерф) через серый к ярко-зелёному (сильный бафф). Штрих = много правок, взаимно гасятся."),
    ("D", "Столбики от линии", v_bars,
     "Сплошная тонкая линия через все патчи, столбик вверх/вниз высотой по силе, цвет тоже по силе."),
]


def row_label(key):
    e = D["entities"][key]
    return e["name"]


def table(v):
    head = "".join(f'<th>{p}</th>' for p in pats)
    rows = "".join(f'<tr><td class="nm">{row_label(k)}</td><td class="ch" colspan="{len(pats)}">{v[2](series(k))}</td></tr>'
                   for k in KEYS)
    return (f'<section><h2>{v[0]}. {v[1]}</h2><p>{v[3]}</p><div class="scroll"><table>'
            f'<thead><tr><th class="nm">Name</th>{head}</tr></thead><tbody>{rows}</tbody></table></div></section>')


CSS = f"""
body{{background:#14110d;color:#e8dcc4;font:13px/1.4 Consolas,monospace;margin:20px}}
h1{{color:#e8c070}} h2{{color:#e8c070;margin:28px 0 4px}} p{{margin:0 0 8px;color:#bfb29a;max-width:900px}}
.scroll{{overflow-x:auto;border:1px solid #5a4a30;background:#1b1712}}
table{{border-collapse:collapse}} th{{font-weight:normal;width:{CW}px;min-width:{CW}px;font-size:9px;color:#c9b48a;
writing-mode:vertical-rl;transform:rotate(180deg);height:40px;border-bottom:1px solid #e8c070}}
th.nm,td.nm{{writing-mode:initial;transform:none;width:130px;min-width:130px;text-align:left;padding:0 8px;
position:sticky;left:0;background:#1b1712;z-index:1}}
td{{padding:0;height:{RH}px;border-bottom:1px solid #2c261d}} td.ch svg{{display:block}}
.g{{stroke:#2c261d}} .z{{stroke:#6b5c42;stroke-dasharray:2 2}} .base{{stroke:#6b5c42}}
"""

DEFS = ('<svg width="0" height="0" style="position:absolute"><defs><pattern id="mix" width="4" height="4" '
        'patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="4" height="4" fill="#5a5448"/>'
        '<rect width="2" height="4" fill="#9a8f7a"/></pattern></defs></svg>')

html = (f'<!doctype html><meta charset="utf-8"><title>Dynamics — варианты графиков</title><style>{CSS}</style>{DEFS}'
        '<h1>Hero / Item Dynamics — 4 варианта строки</h1>'
        f'<p>Настоящие данные: число <b>w</b> из dist/_dynamics.json (сумма весов правок за патч, плюс = бафф). '
        f'Высота и яркость = √(|w|/{CAP}), предел — полная высота. Строка {RH} px, клетка {CW} px.</p>'
        + "".join(table(v) for v in VARIANTS))
OUT.write_text(html, encoding="utf8")
print(OUT)
