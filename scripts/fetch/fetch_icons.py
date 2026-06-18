"""fetch_icons.py — Скачивает все недостающие иконки абилок из Valve CDN.

После `python builders/patch.py` файл `_ability_icons.txt` содержит относительные
пути ко всем иконкам, на которые ссылаются собранные патч-страницы. Этот
скрипт идёт по списку, проверяет какие файлы локально отсутствуют, и
качает их с `https://cdn.steamstatic.com/apps/dota2/images/dota_react/abilities/`.

Запускать ПОСЛЕ builders/patch.py — добавление нового slug в builders/patch.py
автоматически попадёт в _ability_icons.txt, и следующий запуск этого
скрипта добьёт недостающие PNG-ки.

Иконки, которых нет на CDN (например innate-абилки), просто пропускаются
с пометкой `404`. В браузере для них работает onerror-fallback на
innate_icon.png — пользователь видит дефолтный маркер, а не сломанную
картинку.
"""
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests"); sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent.parent
URLS_FILE = ROOT / "_ability_icons.txt"
ICONS_DIR = ROOT / "icons" / "abilities"
CDN_BASE = "https://cdn.steamstatic.com/apps/dota2/images/dota_react/abilities/"

if not URLS_FILE.exists():
    print(f"X {URLS_FILE} not found. Run python builders/patch.py first.")
    sys.exit(1)

ICONS_DIR.mkdir(parents=True, exist_ok=True)

# Parse local paths from _ability_icons.txt (relative like ../icons/abilities/<slug>.png)
slugs = []
for line in URLS_FILE.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    name = line.rsplit("/", 1)[-1]
    if name.endswith(".png"):
        slugs.append(name[:-4])

slugs = sorted(set(slugs))
missing_local = [s for s in slugs if not (ICONS_DIR / f"{s}.png").exists()]

print(f"Total icons referenced: {len(slugs)}")
print(f"Already present locally: {len(slugs) - len(missing_local)}")
print(f"Missing locally:         {len(missing_local)}")

if not missing_local:
    print("\nAll icons present. Nothing to fetch.")
    sys.exit(0)


def fetch(slug):
    url = f"{CDN_BASE}{slug}.png"
    out = ICONS_DIR / f"{slug}.png"
    try:
        r = requests.get(url, timeout=15, allow_redirects=True)
        if r.status_code == 200 and r.content:
            out.write_bytes(r.content)
            return slug, "OK", len(r.content)
        return slug, str(r.status_code), 0
    except Exception as e:
        return slug, str(e), 0


print(f"\nFetching {len(missing_local)} icons from Valve CDN...")
ok, fail = 0, []
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(fetch, s): s for s in missing_local}
    for fut in as_completed(futures):
        slug, status, size = fut.result()
        if status == "OK":
            ok += 1
            print(f"  + {slug}  ({size:,} bytes)")
        else:
            fail.append((slug, status))

print(f"\nDownloaded: {ok}")
print(f"Skipped:    {len(fail)}")
if fail:
    print("\nNot on CDN (browser uses onerror fallback to innate_icon.png):")
    for slug, status in sorted(fail):
        print(f"  {status:>3}  {slug}")
