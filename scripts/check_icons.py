"""check_icons.py — Проверяет что каждый URL иконки в _ability_icons.txt
действительно существует на CDN. Запускать ПОСЛЕ builders/patch.py.

Печатает только проблемные (404, network errors). Для каждой такой иконки
соответствующая <img> в HTML автоматически свапнет на innate_icon.png через
onerror handler.
"""
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests"); sys.exit(1)

URLS_FILE = Path(__file__).resolve().parent.parent / "_ability_icons.txt"
INNATE_ICON = "https://cdn.steamstatic.com/apps/dota2/images/dota_react/icons/innate_icon.png"

if not URLS_FILE.exists():
    print(f"❌ {URLS_FILE} not found. Run python builders/patch.py first.")
    sys.exit(1)

urls = [line.strip() for line in URLS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
print(f"Checking {len(urls)} ability-icon URLs...")

def check(url):
    try:
        r = requests.head(url, timeout=8, allow_redirects=True)
        return url, r.status_code
    except Exception as e:
        return url, str(e)

missing = []
ok_count = 0
with ThreadPoolExecutor(max_workers=16) as ex:
    futures = {ex.submit(check, u): u for u in urls}
    for fut in as_completed(futures):
        url, status = fut.result()
        if isinstance(status, int) and status == 200:
            ok_count += 1
        else:
            missing.append((url, status))

print(f"\nOK:      {ok_count}")
print(f"Missing: {len(missing)}")
if missing:
    print("\nMissing icons (will fall back to innate_icon.png in browser):")
    for url, status in sorted(missing):
        slug = url.rsplit("/", 1)[-1].replace(".png", "")
        print(f"  {status:>3}  {slug}")

# Verify innate fallback itself loads
try:
    r = requests.head(INNATE_ICON, timeout=8, allow_redirects=True)
    if r.status_code != 200:
        print(f"\n⚠ Innate fallback icon also fails: {r.status_code} {INNATE_ICON}")
    else:
        print(f"\nFallback ({INNATE_ICON.rsplit('/',1)[-1]}) — OK")
except Exception as e:
    print(f"\n⚠ Cannot reach innate fallback: {e}")
