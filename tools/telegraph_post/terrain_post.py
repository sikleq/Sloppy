"""telegra.ph post about the map history (the owner 2026-10-04: "all maps, letter patches too, and we know every
terrain change"; slider animations of the layers, the pictures in the patch notes, the objects we keep, the
"On the map" cells, the All layers button). Built with build_post.py's machinery:

    python tools/telegraph_post/terrain_post.py      # needs dist/ served on :8799
    -> icons/telegraph/2026-10-04_terrain/*.jpg|gif  (hosted by the site: commit + push before posting)
    -> tools/telegraph_post/out_terrain/{post.json, post_telegraph.html, preview.html}
Then open out_terrain/post_telegraph.html in a browser, select all, copy, paste into the telegra.ph editor.
"""
import html
import json
import pathlib
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_post as bp  # noqa: E402

ROOT = bp.ROOT
SHOTS = ROOT / "icons" / "changelog"
OLDGROWTH = pathlib.Path(r"C:\Users\sikle\Documents\Oldgrowth")
bp.WEEK = "2026-10-04_terrain"
bp.IMG_DIR = ROOT / "icons" / "telegraph" / bp.WEEK
bp.IMG_URL = f"{bp.SITE}icons/telegraph/{bp.WEEK}/"
bp.OUT = HERE / "out_terrain"
bp.TITLE = "Sloppy: вся история карты Dota 2"
bp.COVER_HTML = (bp.COVER_HTML
                 .replace("Новый облик · патч 7.38 · новые страницы · sikleq.github.io/Sloppy",
                          "65 карт · буквенные патчи тоже · sikleq.github.io/Sloppy")
                 # smaller and lower than the weekly cover's: the bottom line stays readable
                 .replace(".shot{position:absolute;right:-40px;bottom:-30px;width:640px;",
                          ".shot{position:absolute;right:-30px;bottom:-95px;width:560px;")
                 # the cover's picture is made here, after the last build: read it from the source folder
                 .replace("http://localhost:8799/icons/changelog/2026-09-25_warm.webp",
                          (ROOT / "icons" / "changelog" / "2026-10-04_terrain_cover.webp").as_uri()))
SITE = bp.SITE
OG_URL = "https://github.com/sikleq/Oldgrowth"
GIF_W = 480                 # animations shrink for the post: Instant View fetches big GIFs badly

bp.POST = [
    ("cover", "Все карты с 7.08 и все их изменения"),
    ("p", "Sloppy — сайт о патчах Dota 2. Раньше карту можно было сравнить только между большими патчами. Теперь у "
          "нас есть все карты, которые Valve выпускала с 7.08, включая буквенные патчи, и мы знаем каждое изменение "
          "ландшафта: какое дерево убрали, какой лагерь сдвинули, где перестали ставиться варды."),
    ("links", [("Страница Terrain", SITE + "terrain_741.html"), ("Changelog сайта", SITE + "changelog.html"),
               ("Данные карт на GitHub", OG_URL)]),
    ("toc", None),

    ("h3", "Все карты, даже буквенные"),
    ("p", "Мы скачали файл карты каждого патча с 7.08 по 7.41f и сами отрисовали его сверху, прямо из файлов игры. "
          "Получилось 65 разных карт — ровно столько раз Valve меняла файл карты за восемь лет, включая тихие правки "
          "в буквенных патчах. На сайте у каждого патча с изменённой картой, начиная с 7.38, своя страница с "
          "ползунком «было — стало»."),
    ("img", ("2026-10-04_sweep_trees.webp", "7.40: слой деревьев, ползунок идёт от старой карты к новой")),

    ("h3", "Ползунок: было и стало"),
    ("p", "Включите любой слой, и ползунок покажет, что поменялось: деревья, лагеря, башни, наблюдатели, руны, "
          "логово Рошана, Мучители, земля, где нельзя ставить варды."),
    ("img", ("2026-10-04_sweep_objects.webp", "7.41: лагеря, башни, наблюдатели, Twin Gates, Lotus Pools — "
                                              "старые и новые места")),
    ("img", ("2026-10-04_sweep_nowards.webp", "7.38: земля без вардов — на красном стало можно ставить, "
                                              "на зелёном стало нельзя")),

    ("h3", "Все слои одной кнопкой"),
    ("p", "Кнопка <b>All layers</b> включает все слои сразу: деревья, лагеря, зоны появления крипов, башни, руны и "
          "землю без вардов."),
    ("img", ("2026-10-04_sweep_all_layers.webp", "7.41: все слои сразу")),

    ("h3", "Что изменилось — обведено"),
    ("p", "Под списком изменений — чипы по видам объектов. Нажмите чип, и изменённые места обведутся прямо на "
          "карте: убранное красным, добавленное зелёным, сдвинутое жёлтым. Пунктир всегда значит «где было», "
          "сплошная линия — «где стало»."),
    ("img", ("2026-10-03_terrain_trees_modes.webp", "Деревья на четырёх картах: все изменения, только сдвинутые, "
                                                    "убранные и добавленные")),

    ("h3", "Картинки прямо в патчноутах"),
    ("p", "В разделе Terrain Changes на странице патча название изменённого объекта — «tier 1 safe lane towers», "
          "«several trees» — теперь кнопка. Нажмите, и под строкой откроются две картинки этого места: старая и "
          "новая карта рядом, с мини-картой, где это."),
    ("img", ("2026-10-03_terrain_notes.webp", "7.41: картинки под названиями изменённых объектов")),

    ("h3", "Мы храним данные по объектам"),
    ("p", "Для каждой карты сохранено всё, что на ней стоит: каждое дерево, лагерь, башня, руна, аванпост, логово "
          "Рошана и Мучители — с координатами. Поэтому сайт сам находит, что сдвинулось между патчами, даже если "
          "Valve об этом не написали."),
    ("img", ("2026-10-04_terrain_facts.webp", "Ячейки на странице Terrain: что есть на карте и что изменилось "
                                              "в её файле")),
    ("img", ("2026-10-04_oldgrowth.webp", "Oldgrowth: данные по всем 65 картам")),
    ("p", f'Все картинки и данные лежат в открытом репозитории <a href="{OG_URL}">Oldgrowth</a> — '
          "ими может пользоваться кто угодно."),
]


def _facts_shot():
    """The "On the map" cells and the "Changed in the map file" chips of 7.41's Terrain page (an element shot: the
    list pane scrolls, a page clip misses it)."""
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page(viewport={"width": 1400, "height": 1000}, device_scale_factor=1.5)
        p.goto("http://localhost:8799/terrain_741.html", wait_until="load")
        p.wait_for_timeout(1500)
        p.locator(".terrain-facts").first.screenshot(path=str(bp.OUT / "facts.png"))
        b.close()
    Image.open(bp.OUT / "facts.png").convert("RGB").save(SHOTS / "2026-10-04_terrain_facts.webp", "WEBP", quality=85)


OG_HTML = """<!doctype html><meta charset=utf-8><style>
body{margin:0;background:#12100d;font-family:Rubik,Segoe UI,sans-serif;color:#d6cbb5;padding:22px 26px;width:1060px}
h1{font:600 26px Rubik,sans-serif;color:#e3c46a;margin:0 0 4px}p{margin:0 0 14px;color:#9b917f;font-size:15px}
table{border-collapse:collapse;width:100%;font-size:15px}th,td{padding:7px 10px;text-align:center;
border-bottom:1px solid rgba(227,196,106,.14)}th{color:#e3c46a;font-weight:600}td.c{text-align:left;color:#cfc4ad}
td.v{color:#fff3d6;font-weight:600}</style>
<h1>Oldgrowth</h1><p>65 map files of 118 patches, 7.08 – 7.41f: what stands on each map and what moved</p>
<table><tr><th>Patch</th><th>Trees</th><th>Camps</th><th>Towers</th><th>Watchers</th><th>What moved since the patch before</th></tr>
__ROWS__</table>"""


def _oldgrowth_shot():
    """A short table from Oldgrowth's versions.json: a few patches that changed the map most."""
    rows = json.load(open(OLDGROWTH / "versions.json", encoding="utf-8"))
    want = ("7.41", "7.40", "7.39", "7.38", "7.33", "7.23", "7.20", "7.15", "7.08")
    out = []
    for r in rows:
        if r["patch"] in want and "counts" in r:
            c = r["counts"]
            changes = r.get("changes", "")
            changes = changes if len(changes) < 70 else changes[:67].rsplit(";", 1)[0] + "; …"
            out.append(f'<tr><td class="v">{r["patch"]}</td><td>{c.get("ent_dota_tree", 0)}</td>'
                       f'<td>{c.get("npc_dota_neutral_spawner", 0)}</td><td>{c.get("npc_dota_tower", 0)}</td>'
                       # watchers are lanterns in the map file (npc_dota_watch_tower = the outposts)
                       f'<td>{c.get("npc_dota_lantern", 0)}</td><td class="c">{html.escape(changes)}</td></tr>')
    out.sort(key=lambda s: [int(x) for x in s.split('class="v">')[1].split("<")[0].split(".")], reverse=True)
    page = bp.OUT / "oldgrowth.html"
    page.write_text(OG_HTML.replace("__ROWS__", "".join(out)), encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page(viewport={"width": 1112, "height": 600}, device_scale_factor=1.5)
        p.goto(page.as_uri())
        p.locator("body").screenshot(path=str(bp.OUT / "oldgrowth.png"))
        b.close()
    Image.open(bp.OUT / "oldgrowth.png").convert("RGB").save(SHOTS / "2026-10-04_oldgrowth.webp", "WEBP", quality=88)


def _cover_shot():
    """The cover's tilted picture: the middle of the all-layers sweep (old | new with the handle between)."""
    im = Image.open(SHOTS / "2026-10-04_sweep_all_layers.webp")
    im.seek(im.n_frames // 4)
    f = im.convert("RGB")
    # a wide band from the middle (the caption strip left out), so it sits low and leaves the title clear
    f.crop((0, 220, f.width, 580)).save(SHOTS / "2026-10-04_terrain_cover.webp", "WEBP", quality=85)


def _gif(src, dest):
    """An animated WebP as a smaller GIF: GIF_W wide, every other quick frame dropped (its time added to the one
    kept), so a slider sweep stays smooth and the file stays a few MB."""
    im = Image.open(src)
    frames, durations = [], []
    for i in range(im.n_frames):
        im.seek(i)
        d = im.info.get("duration", 100)
        if d < 100 and i % 2 and frames:
            durations[-1] += d
            continue
        f = im.convert("RGB")
        f = f.resize((GIF_W, round(f.height * GIF_W / f.width)), Image.LANCZOS)
        frames.append(f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        durations.append(d)
    frames[0].save(dest, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True,
                   disposal=1)


def _prepare_images():
    bp.IMG_DIR.mkdir(parents=True, exist_ok=True)
    names = {}
    for kind, payload in bp.POST:
        if kind != "img":
            continue
        src = SHOTS / payload[0]
        im = Image.open(src)
        if getattr(im, "n_frames", 1) > 1:
            name = src.stem + ".gif"
            _gif(src, bp.IMG_DIR / name)
        else:
            name = src.stem + ".jpg"
            bp._iv_safe(im.convert("RGB")).save(bp.IMG_DIR / name, "JPEG", quality=88, optimize=True)
        names[payload[0]] = name
        print(f"  {name}: {round((bp.IMG_DIR / name).stat().st_size / 1024)} KB")
    return names


if __name__ == "__main__":
    bp.OUT.mkdir(parents=True, exist_ok=True)
    _facts_shot()
    _oldgrowth_shot()
    _cover_shot()
    bp._prepare_images = _prepare_images
    bp.build()
