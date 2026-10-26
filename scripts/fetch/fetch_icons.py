"""fetch_icons.py — Скачивает все недостающие иконки абилок из Valve CDN.

После `python build_site.py patch` файл `.cache/_ability_icons.txt` содержит относительные
пути ко всем иконкам, на которые ссылаются собранные патч-страницы. Этот
скрипт идёт по списку, проверяет какие файлы локально отсутствуют, и
качает их с `https://cdn.steamstatic.com/apps/dota2/images/dota_react/abilities/`.

Запускать ПОСЛЕ builders/build_patches.py — добавление нового slug в content/ (список пишет patch/rosters.py)
автоматически попадёт в _ability_icons.txt, и следующий запуск этого
скрипта добьёт недостающие PNG-ки.

Нет на CDN — ищем в файлах игры (правило владельца 2026-10-26: «если не находишь —
ищешь в файлах игры»): сначала значок, который игра рисует для способности
(KV `AbilityTextureName`, 7.41 Squee's Scope = techies_stasis_trap) — на CDN и в VPK,
потом `panorama/images/spellicons/<slug>_png.vtex_c` в pak01_dir.vpk клиента.
Только то, чего нет и там (innate без своего арта), остаётся с пометкой —
в браузере для них onerror-fallback на innate_icon.png; такие slug'и вносить
в patch/known_exceptions.py KNOWN_INNATE_NO_CDN_ICON с пометкой «not in the client VPK nor the CDN».
"""
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests"); sys.exit(1)

import re

ROOT = Path(__file__).resolve().parent.parent.parent
URLS_FILE = ROOT / ".cache" / "_ability_icons.txt"
ICONS_DIR = ROOT / "icons" / "abilities"
CDN_BASE = "https://cdn.steamstatic.com/apps/dota2/images/dota_react/abilities/"

ICONS_DIR.mkdir(parents=True, exist_ok=True)

# Parse local paths from _ability_icons.txt (patch builder output)
slugs = []
if URLS_FILE.exists():
    for line in URLS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        name = line.rsplit("/", 1)[-1]
        if name.endswith(".png"):
            slugs.append(name[:-4])

# Also scan all built HTML pages for ability icon references so that tables
# like aoe_increase (which don't use _ability_icons.txt) are covered.
DIST = ROOT / "dist"
if DIST.is_dir():
    for html_file in DIST.glob("*.html"):
        for m in re.finditer(r'icons/abilities/([^"\']+)\.png', html_file.read_text(encoding="utf-8", errors="ignore")):
            slugs.append(m.group(1))

slugs = sorted(set(slugs))
missing_local = [s for s in slugs if not (ICONS_DIR / f"{s}.png").exists()]

print(f"Total icons referenced: {len(slugs)}")
print(f"Already present locally: {len(slugs) - len(missing_local)}")
print(f"Missing locally:         {len(missing_local)}")

if not missing_local:
    print("\nAll icons present. Nothing to fetch.")
    sys.exit(0)


_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _from_cdn(name, out):
    """(status, bytes written) of the CDN's <name>.png saved as `out`."""
    try:
        r = requests.get(f"{CDN_BASE}{name}.png", timeout=15, allow_redirects=True)
    except Exception as e:
        return str(e), 0
    if r.status_code != 200 or not r.content:
        return str(r.status_code), 0
    if not r.content.startswith(_PNG_MAGIC):
        return "not-png", 0
    out.write_bytes(r.content)
    return "OK", len(r.content)


def texture_name(slug):
    """The icon the game draws for the ability: KV AbilityTextureName of the newest patch that has it, or None."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from patch.aghs_text import _blocks
    from patch.meta import RELEASE_HISTORY, _parse_date
    for p in sorted(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]), reverse=True):
        block = _blocks(p["version"]).get(slug)
        if isinstance(block, dict):
            return block.get("AbilityTextureName") or None
    return None


_VPK = {}


def from_vpk(name, out):
    """(status, bytes) of panorama/images/spellicons/<name>_png.vtex_c from the client's pak01_dir.vpk saved as `out`."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import extract_vpk_icons as vpk
    if not vpk.DEFAULT_VPK.exists():
        return "no-vpk", 0
    if not _VPK:
        _VPK["entries"], _VPK["base"] = vpk.read_tree(vpk.DEFAULT_VPK)
    internal = f"panorama/images/spellicons/{name}_png.vtex_c"
    if internal not in _VPK["entries"]:
        return "not-in-vpk", 0
    try:
        vpk.decode(vpk.read_file(vpk.DEFAULT_VPK, internal, _VPK["entries"], _VPK["base"])).save(out)
    except ValueError as e:                 # a texture format the decoder doesn't know yet: say so, don't stop
        return f"vpk-decode: {e}", 0
    return "OK", out.stat().st_size


def fetch(slug):
    out = ICONS_DIR / f"{slug}.png"
    status, size = _from_cdn(slug, out)
    if status == "OK":
        return slug, status, size
    return slug, f"{status} (CDN)", 0


def from_game_files(slug):
    """CDN 404 -> the game's own icon for it: its AbilityTextureName (CDN, then VPK), then its own name in the VPK."""
    out = ICONS_DIR / f"{slug}.png"
    tex = texture_name(slug)
    tried = []
    for name, src in ([(tex, "cdn"), (tex, "vpk")] if tex and tex != slug else []) + [(slug, "vpk")]:
        status, size = (_from_cdn if src == "cdn" else from_vpk)(name, out)
        tried.append(f"{src}:{name}={status}")
        if status == "OK":
            return slug, f"OK via {src}:{name}", size
    return slug, "; ".join(tried), 0


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

if fail:
    print(f"\nNot on CDN: {len(fail)} — looking in the game files (AbilityTextureName, client VPK)...")
    still = []
    for slug, _ in sorted(fail):
        slug, status, size = from_game_files(slug)
        if status.startswith("OK"):
            ok += 1
            print(f"  + {slug}  ({size:,} bytes, {status[3:]})")
        else:
            still.append((slug, status))
    fail = still

print(f"\nDownloaded: {ok}")
print(f"Skipped:    {len(fail)}")
if fail:
    print("\nNot on the CDN nor in the game files (browser uses onerror fallback to innate_icon.png;")
    print("add them to patch/known_exceptions.py KNOWN_INNATE_NO_CDN_ICON):")
    for slug, status in sorted(fail):
        print(f"  {slug}: {status}")
