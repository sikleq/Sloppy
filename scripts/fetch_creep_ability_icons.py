"""fetch_creep_ability_icons.py — добивает иконки способностей нейтралов в
icons/abilities/<slug>.png. Источники, по порядку:

  1. Valve dota_react CDN (dota_react/abilities/<slug>.png) — отдаёт ~39/57.
  2. Локально извлечённые spellicons (panorama/images/spellicons/<slug>_png.png)
     — для иконок, которых нет на CDN (~15). Папку задаёт переменная окружения
     CREEP_SPELLICONS_DIR (или дефолтный путь ниже). Извлекается из pak01_dir.vpk
     через GCFScape / Source2Viewer.
  3. ALIAS — несколько нейтральных способностей переиспользуют геройскую
     иконку (своей нет даже в VPK); берём её по слагу из тех же двух источников.

Запуск:
    python scripts/fetch_creep_ability_icons.py
    CREEP_SPELLICONS_DIR="D:/dump/panorama/images/spellicons" python scripts/fetch_creep_ability_icons.py
"""
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
STATS_DIR = ROOT / "data" / "stats"
ICONS_DIR = ROOT / "icons" / "abilities"
CDN = "https://cdn.steamstatic.com/apps/dota2/images/dota_react/abilities/"
ABILITY_SKIP = {"neutral_upgrade", "creep_piercing"}

# Default local spellicons dump (override with CREEP_SPELLICONS_DIR).
SPELLICONS_DIR = Path(os.environ.get(
    "CREEP_SPELLICONS_DIR",
    str(Path.home() / "OneDrive" / "Desktop" / "panorama" / "images" / "spellicons"),
))

# Neutral abilities with no dedicated icon anywhere — reuse the hero icon the
# game itself falls back to (matched by AbilitySound / shared name).
ALIAS = {
    "ogre_bruiser_ogre_smash": "ogre_magi_smash",
    "ice_shaman_incendiary_bomb": "ogre_magi_ignite",
    "giant_wolf_intimidate": "legion_commander_intimidate",
    "fel_beast_haunt": "spectre_haunt",
}


def neutral_ability_slugs():
    slugs = set()
    for d in STATS_DIR.iterdir():
        p = d / "npc_units.json"
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for e in data.values():
            if isinstance(e, dict):
                for i in range(1, 6):
                    s = e.get(f"Ability{i}")
                    if s and s not in ABILITY_SKIP:
                        slugs.add(s)
    return slugs


def from_cdn(slug, dest):
    try:
        req = urllib.request.Request(CDN + slug + ".png",
                                     headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=20).read()
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            dest.write_bytes(data)
            return True
    except Exception:
        pass
    return False


def from_local(slug, dest):
    src = SPELLICONS_DIR / f"{slug}_png.png"
    if src.exists():
        shutil.copyfile(src, dest)
        return True
    return False


def acquire(slug, dest):
    # 1) CDN by slug, 2) local spellicons by slug,
    # 3) alias on CDN, 4) alias locally.
    if from_cdn(slug, dest):
        return "cdn"
    if from_local(slug, dest):
        return "local"
    alias = ALIAS.get(slug)
    if alias:
        if from_cdn(alias, dest):
            return f"cdn:{alias}"
        if from_local(alias, dest):
            return f"local:{alias}"
    return None


def main():
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    slugs = sorted(neutral_ability_slugs())
    print(f"Слугов: {len(slugs)} | spellicons dir: {SPELLICONS_DIR} "
          f"({'есть' if SPELLICONS_DIR.is_dir() else 'НЕТ'})")
    got = {}
    missing = []
    for s in slugs:
        dest = ICONS_DIR / f"{s}.png"
        if dest.exists():
            continue
        src = acquire(s, dest)
        if src:
            got.setdefault(src.split(":")[0], 0)
            got[src.split(":")[0]] += 1
            print(f"  + {s}  ←  {src}")
        else:
            missing.append(s)
    print(f"Готово: добавлено {sum(got.values())} {dict(got)} | "
          f"осталось без иконки {len(missing)}")
    if missing:
        print("  нет нигде:", missing)
    return 0


if __name__ == "__main__":
    sys.exit(main())
