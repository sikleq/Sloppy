"""Weekly recap post for telegra.ph — built from the site's changelog screenshots.

    python tools/telegraph_post/build_post.py     # needs dist/ served on :8799 for the cover
    -> icons/telegraph/<week>/*.jpg|gif   (images; hosted by the site after deploy)
    -> tools/telegraph_post/out/post.json (Telegraph content nodes + title)
    -> tools/telegraph_post/out/preview.html (local look at the post)
Then publish with tools/telegraph_post/publish.py (run it yourself — it creates a Telegraph account).

Telegraph shows images by URL, so they must be LIVE on the site first: commit + push icons/telegraph/.
Only tags Telegraph allows are used: h3, h4, p, a, b, i, ul, li, figure, img, figcaption, blockquote, hr.
"""
import html
import json
import pathlib

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
WEEK = "2026-09-20_25"
SITE = "https://sikleq.github.io/Sloppy/"
IMG_DIR = ROOT / "icons" / "telegraph" / WEEK
IMG_URL = f"{SITE}icons/telegraph/{WEEK}/"
OUT = pathlib.Path(__file__).resolve().parent / "out"
SHOTS = ROOT / "icons" / "changelog"
TITLE = "Sloppy: что нового за неделю (20–25 сентября)"

# ---- the post: (kind, payload). "img" = (changelog shot file, caption)
POST = [
    ("cover", "Неделя обновлений · 20–25 сентября"),
    ("p", 'Sloppy — сайт о патчах Dota 2: каждое изменение размечено тегами, а в таблицах '
          'Materials собраны герои, предметы и крипы с историей по патчам. За неделю сайт '
          'сменил облик, получил новые страницы, полностью размеченный патч 7.38 и пачку исправлений.'),
    ("links", [("Открыть сайт", SITE), ("Changelog сайта", SITE + "changelog.html")]),
    ("toc", None),
    ("h3", "Новый облик"),
    ("h4", "Шапка «Угольки»"),
    ("p", "Кнопки в шапке теперь просто текст. Текущая страница горит золотом, "
          "а из тонкой полоски под ней поднимаются искры — как у автокаста в игре."),
    ("img", ("2026-09-24_header.webp", "Шапка и панель фильтров страницы патча")),
    ("h4", "Пиксельные кнопки и меню"),
    ("p", "Меню, панели фильтров, переключатели и поля ввода перешли на один стиль: пиксельный "
          "шрифт, ступенчатые углы, «игровые» кнопки. Нажатая кнопка заливается золотом. "
          "Иконки ближнего и дальнего боя, талантов и жука исправлений нарисованы заново."),
    ("img", ("2026-09-25_controls.webp", "Панель фильтров Hero Stats")),
    ("img", ("2026-09-25_menu.webp", "Выпадающее меню с пиксельными галочками")),
    ("h4", "Тёплые цвета"),
    ("p", "Холодные стальные серые и синие ушли. Теперь фон, линии и шапки таблиц в спокойных "
          "тёплых тонах. Синий остался только там, где он что-то значит: QOL, магический урон, "
          "интеллект, Aghanim, мана."),
    ("img", ("2026-09-25_warm.webp", "Neutral Stats в новых цветах")),
    ("h4", "Главная и автокаст"),
    ("p", "У каждой плитки главной страницы своя пиксельная иконка. А способности с автокастом "
          "в таблицах нейтралов показывают эффект из самой игры — огонь бежит по краю иконки."),
    ("img", ("2026-09-24_index.webp", "Главная страница")),
    ("img", ("2026-09-24_autocast.webp", "Автокаст, как в игре")),
    ("h3", "Патч 7.38 целиком"),
    ("p", "Все 1585 изменений патча 7.38 размечены и сверены построчно с данными Valve. "
          "Переработанные механики читаются одним описанием того, как они работают теперь. "
          "У изменённых способностей — карточки «было / стало» с настоящими старыми подсказками "
          "из игры, а значения, растущие со временем, раскрываются таблицей по минутам."),
    ("img", ("2026-09-20_patch738.webp", "Страница патча 7.38")),
    ("img", ("2026-09-24_tormentor_card.webp", "Мучитель: карточка «было / стало» с таблицей")),
    ("h3", "Новые страницы"),
    ("p", "<b>Unit Changes и Structures</b> — история изменений каждого нейтрала, призыва и "
          "линейного крипа, а ещё башен, казарм и Мучителя."),
    ("img", ("2026-09-22_unit_changes.webp", "Unit Changes")),
    ("p", "<b>Рошан и Мучитель</b> получили свои страницы с полной историей — как у героев."),
    ("img", ("2026-09-23_roshan.webp", "Страница Рошана")),
    ("p", "<b>Changelog</b> — всё новое на сайте по датам, со скриншотами. Исправления "
          "отмечены пиксельным жуком."),
    ("img", ("2026-09-24_changelog.webp", "Changelog сайта")),
    ("h3", "Таблицы Materials"),
    ("ul", ["<b>Mana Items:</b> сколько даёт одно очко интеллекта (+12 маны, +0.05 регена) — "
            "прямо в панели фильтров, с историей по патчам.",
            "<b>Hero Lab:</b> список Difference открывается таблицей 4×7 — без прокрутки.",
            "<b>Terrain:</b> стрелки у номера патча переходят на соседнюю карту (7.41 ↔ 7.40).",
            "Описания над таблицами убраны: страницы открываются сразу с фильтров."]),
    ("img", ("2026-09-25_per_int.webp", "Per Int на Mana Items")),
    ("img", ("2026-09-25_hl_diff.webp", "Difference в Hero Lab")),
    ("h3", "Исправления"),
    ("ul", ["Базовая скорость атаки в 7.41f застряла на значениях 7.41e — теперь верно: "
            "Earth Spirit 95, Keeper of the Light 90, Warlock 95. Данные героев для новых патчей "
            "берутся прямо из файлов игры.",
            "AoE Increase снова показывает все радиусы.",
            "Hero и Item Dynamics больше не тормозят при прокрутке и наведении.",
            "История Mana Items учитывает, сколько маны давал интеллект в каждом патче "
            "(11 в 7.36–7.38, а не сегодняшние 12).",
            "Врождённые способности 7.41f читаются правильно."]),
    ("hr", None),
    ("p", 'Полный список — в <a href="%schangelog.html">Changelog</a>.' % SITE),
]


def _prepare_images():
    """Changelog WebP -> JPG (GIF for the animated autocast) under icons/telegraph/<week>/."""
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    names = {}
    for kind, payload in POST:
        if kind != "img":
            continue
        src = SHOTS / payload[0]
        im = Image.open(src)
        if getattr(im, "n_frames", 1) > 1:
            name = src.stem + ".gif"
            frames = []
            for i in range(im.n_frames):
                im.seek(i)
                frames.append(im.convert("RGB").convert("P", palette=Image.ADAPTIVE))
            frames[0].save(IMG_DIR / name, save_all=True, append_images=frames[1:],
                           duration=im.info.get("duration", 40), loop=0)
        else:
            name = src.stem + ".jpg"
            im.convert("RGB").save(IMG_DIR / name, "JPEG", quality=88, optimize=True)
        names[payload[0]] = name
    return names


COVER_HTML = """<!doctype html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&family=Handjet:wght@500&display=block" rel="stylesheet">
<style>
body{margin:0;width:1280px;height:640px;overflow:hidden;font-family:'Jersey 10',monospace;
 background:radial-gradient(ellipse 70% 90% at 25% 30%,#2a2118 0%,#12100d 60%,#0b0a09 100%);color:#e8dcc0}
.helm{position:absolute;left:84px;top:150px;width:192px;height:192px;image-rendering:pixelated}
.t{position:absolute;left:320px;top:132px;font-family:'Jersey 25';font-size:112px;color:#e3c46a;letter-spacing:2px;
 text-shadow:0 0 18px rgba(255,150,40,.35)}
.s{position:absolute;left:326px;top:258px;font-family:'Handjet';font-size:54px;color:#d6cbb5;letter-spacing:1px;white-space:nowrap}
.bar{position:absolute;left:326px;top:346px;width:420px;height:4px;background:#e3c46a;box-shadow:0 0 10px #ff9a2a}
.e{position:absolute;width:5px;height:5px;background:#ffcf6a;box-shadow:0 0 6px #ff8a1a}
.shot{position:absolute;right:-40px;bottom:-30px;width:640px;border:2px solid rgba(227,196,106,.45);
 box-shadow:0 10px 40px rgba(0,0,0,.7);transform:rotate(-4deg)}
.u{position:absolute;left:326px;top:384px;font-family:'Handjet';font-size:36px;color:#9b917f}
</style></head><body>
<img class="helm" src="http://localhost:8799/icons/ui/gothic/icon_helm.png">
<div class="t">SLOPPY</div><div class="s">__SUB__</div><div class="bar"></div>
<i class="e" style="left:400px;top:336px"></i><i class="e" style="left:520px;top:330px;opacity:.7"></i>
<i class="e" style="left:630px;top:338px;opacity:.85"></i><i class="e" style="left:470px;top:326px;opacity:.5"></i>
<div class="u">Новый облик · патч 7.38 · новые страницы · sikleq.github.io/Sloppy</div>
<img class="shot" src="http://localhost:8799/icons/changelog/2026-09-25_warm.webp">
</body></html>"""


def _cover(subtitle):
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "cover.html"
    tmp.write_text(COVER_HTML.replace("__SUB__", html.escape(subtitle)), encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page(viewport={"width": 1280, "height": 640})
        p.goto(tmp.as_uri(), wait_until="networkidle")
        p.wait_for_timeout(800)
        p.screenshot(path=str(IMG_DIR / "cover.jpg"), type="jpeg", quality=90)
        b.close()
    return "cover.jpg"


def _slug(text):
    """Telegraph heading anchor: the heading text with spaces as '-'."""
    return text.replace(" ", "-")


def _inline(markup):
    """Tiny HTML -> Telegraph nodes for the inline tags used above (<b>, <a href>)."""
    import re
    nodes = []
    for part in re.split(r"(<b>.*?</b>|<a href=\"[^\"]+\">.*?</a>)", markup):
        if not part:
            continue
        m = re.match(r"<b>(.*?)</b>", part)
        if m:
            nodes.append({"tag": "b", "children": [m.group(1)]})
            continue
        m = re.match(r"<a href=\"([^\"]+)\">(.*?)</a>", part)
        if m:
            nodes.append({"tag": "a", "attrs": {"href": m.group(1)}, "children": [m.group(2)]})
            continue
        nodes.append(part)
    return nodes


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    names = _prepare_images()
    heads = [payload for kind, payload in POST if kind == "h3"]
    nodes = []
    for kind, payload in POST:
        if kind == "cover":
            cover = _cover(payload)
            nodes.append({"tag": "figure", "children": [{"tag": "img", "attrs": {"src": IMG_URL + cover}}]})
        elif kind == "p":
            nodes.append({"tag": "p", "children": _inline(payload)})
        elif kind == "links":
            kids = []
            for i, (label, href) in enumerate(payload):
                if i:
                    kids.append("  ·  ")
                kids.append({"tag": "a", "attrs": {"href": href}, "children": [label]})
            nodes.append({"tag": "p", "children": kids})
        elif kind == "toc":
            nodes.append({"tag": "h4", "children": ["Содержание"]})
            nodes.append({"tag": "ul", "children": [
                {"tag": "li", "children": [{"tag": "a", "attrs": {"href": "#" + _slug(h)}, "children": [h]}]}
                for h in heads]})
        elif kind in ("h3", "h4"):
            nodes.append({"tag": kind, "children": [payload]})
        elif kind == "ul":
            nodes.append({"tag": "ul", "children": [{"tag": "li", "children": _inline(x)} for x in payload]})
        elif kind == "img":
            src, cap = payload
            nodes.append({"tag": "figure", "children": [
                {"tag": "img", "attrs": {"src": IMG_URL + names[src]}},
                {"tag": "figcaption", "children": [cap]}]})
        elif kind == "hr":
            nodes.append({"tag": "hr"})
    (OUT / "post.json").write_text(json.dumps({"title": TITLE, "content": nodes}, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    _preview(nodes)
    _markup(nodes)
    print(f"  {len(names) + 1} images -> {IMG_DIR.relative_to(ROOT)}; post.json + preview.html -> {OUT.relative_to(ROOT)}")


def _render(n):
    if isinstance(n, str):
        return html.escape(n)
    attrs = "".join(f' {k}="{html.escape(v)}"' for k, v in n.get("attrs", {}).items())
    if n["tag"] in ("h3", "h4"):
        attrs += f' id="{html.escape(_slug(n["children"][0]))}"'
    if n["tag"] in ("img", "hr"):
        return f"<{n['tag']}{attrs}>"
    return f"<{n['tag']}{attrs}>" + "".join(_render(c) for c in n.get("children", [])) + f"</{n['tag']}>"


def _markup(nodes):
    """The post as plain telegra.ph markup (only tags Telegraph accepts, images by their live site
    URL) — open it in a browser, select all, copy and paste into the telegra.ph editor, or hand
    the markup to any Telegraph tool."""
    body = "\n".join(_render(n) for n in nodes)
    (OUT / "post_telegraph.html").write_text(
        f"<!-- {TITLE} -->\n<!-- telegra.ph markup: h3, h4, p, a, b, ul, li, figure, img, figcaption, hr -->\n"
        f"<meta charset=\"utf-8\">\n<h1>{html.escape(TITLE)}</h1>\n{body}\n", encoding="utf-8")


def _preview(nodes):
    """Rough telegra.ph look (serif body, centred 732px column) with LOCAL image paths."""
    body = "".join(_render(n) for n in nodes).replace(IMG_URL, (IMG_DIR.as_uri() + "/"))
    (OUT / "preview.html").write_text(
        "<!doctype html><meta charset=utf-8><title>preview</title><style>"
        "body{max-width:732px;margin:40px auto;font:18px/1.6 Georgia,serif;color:#222;padding:0 16px}"
        "h1{font:700 32px/1.2 Georgia}h3{font:700 24px Georgia;margin-top:40px}h4{font:700 19px Georgia}"
        "figure{margin:24px 0}img{max-width:100%;display:block;margin:auto}"
        "figcaption{text-align:center;color:#79828b;font-size:15px}a{color:#2e79c8}</style>"
        f"<h1>{html.escape(TITLE)}</h1>{body}", encoding="utf-8")


if __name__ == "__main__":
    build()
