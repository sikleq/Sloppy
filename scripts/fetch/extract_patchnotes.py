"""
Dota 2 Patch Notes вЂ” Extractor & Auto-Uploader
==============================================
Р”РѕСЃС‚Р°С‘С‚ РёР· Р»РѕРєР°Р»СЊРЅРѕРіРѕ pak01_dir.vpk:
  вЂў patchnotes_english.txt  в†’ data/
  вЂў patchnotes_russian.txt  в†’ data/
  вЂў npc_heroes.txt          в†’ data/stats/{version}/
  вЂў npc_units.txt           в†’ data/stats/{version}/
  вЂў items.txt               в†’ data/stats/{version}/

Рё Р·Р°Р»РёРІР°РµС‚ РІ GitHub-СЂРµРїРѕР·РёС‚РѕСЂРёР№ sikleq/Sloppy.

Р—Р°РїСѓСЃРєР°С‚СЊ РїРѕСЃР»Рµ РєР°Р¶РґРѕРіРѕ РѕР±РЅРѕРІР»РµРЅРёСЏ Dota 2 (РёР»Рё РїРѕ Р¶РµР»Р°РЅРёСЋ).

РџР•Р Р•Р” РџР•Р Р’Р«Рњ Р—РђРџРЈРЎРљРћРњ:
в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
1. РЈСЃС‚Р°РЅРѕРІРёС‚СЊ Python:    https://python.org/downloads/
   (РїСЂРё СѓСЃС‚Р°РЅРѕРІРєРµ РїРѕСЃС‚Р°РІСЊ РіР°Р»РѕС‡РєСѓ "Add Python to PATH" !)

2. РћС‚РєСЂС‹С‚СЊ РєРѕРјР°РЅРґРЅСѓСЋ СЃС‚СЂРѕРєСѓ (Win+R в†’ cmd) Рё РІС‹РїРѕР»РЅРёС‚СЊ:
       pip install vpk requests

3. РЎРѕР·РґР°С‚СЊ Personal Access Token:
   https://github.com/settings/tokens?type=beta
       Token name:               dota-patch-uploader
       Repository access:        Only select repositories
                                 в†’ РІС‹Р±СЂР°С‚СЊ sikleq/Sloppy
       Repository permissions:   Contents = Read and write
       Generate token в†’ РЎРљРћРџРР РћР’РђРўР¬ (РїРѕРєР°Р·С‹РІР°РµС‚СЃСЏ РѕРґРёРЅ СЂР°Р·!)

4. Р’СЃС‚Р°РІРёС‚СЊ С‚РѕРєРµРЅ РІ РїРµСЂРµРјРµРЅРЅСѓСЋ GITHUB_TOKEN РЅРёР¶Рµ.
5. Р’СЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰СѓСЋ РІРµСЂСЃРёСЋ РїР°С‚С‡Р° РІ PATCH_VERSION РЅРёР¶Рµ.

Р’РђР–РќРћ вљ  : С…СЂР°РЅРё СЌС‚РѕС‚ С„Р°Р№Р» Сѓ СЃРµР±СЏ РЅР° РџРљ. РќР• Р·Р°Р»РёРІР°Р№ РµРіРѕ РЅРёРєСѓРґР° вЂ”
С‚Р°Рј С‚РІРѕР№ РїРµСЂСЃРѕРЅР°Р»СЊРЅС‹Р№ С‚РѕРєРµРЅ. Р•СЃР»Рё СЃР»СѓС‡Р°Р№РЅРѕ Р·Р°СЃРІРµС‚РёР» вЂ” РѕС‚РѕР·РІР°С‚СЊ
РјРѕР¶РЅРѕ РЅР° С‚РѕР№ Р¶Рµ СЃС‚СЂР°РЅРёС†Рµ С‚РѕРєРµРЅРѕРІ РЅР° GitHub.

Р—РђРџРЈРЎРљ:
в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
   python extract_patchnotes.py

РёР»Рё РїСЂРѕСЃС‚Рѕ РґРІРѕР№РЅРѕР№ РєР»РёРє РїРѕ СЌС‚РѕРјСѓ С„Р°Р№Р»Сѓ (РµСЃР»Рё Python РїРѕСЃС‚Р°РІРёР»СЃСЏ
РїСЂР°РІРёР»СЊРЅРѕ Рё .py-С„Р°Р№Р»С‹ РѕС‚РєСЂС‹РІР°СЋС‚СЃСЏ РёРј).
"""

import base64
import difflib
import os
import sys
from pathlib import Path

# РљРѕРЅСЃРѕР»СЊ Windows РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ cp1251 вЂ” СЌРјРѕРґР·Рё РІ print() СЂРѕРЅСЏР»Рё СЃРєСЂРёРїС‚.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _pause(msg: str = "\nРќР°Р¶РјРё Enter С‡С‚РѕР±С‹ Р·Р°РєСЂС‹С‚СЊ РѕРєРЅРѕ..."):
    """Р–РґР°С‚СЊ Enter С‚РѕР»СЊРєРѕ РїСЂРё Р·Р°РїСѓСЃРєРµ РёР· РѕРєРЅР°; РёР· С‚РµСЂРјРёРЅР°Р»Р°/Р°РіРµРЅС‚Р° вЂ” РЅРµ Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ."""
    if sys.stdin is not None and sys.stdin.isatty():
        try:
            input(msg)
        except EOFError:
            pass

# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# РќРђРЎРўР РћР™РљР вЂ” РѕС‚СЂРµРґР°РєС‚РёСЂСѓР№ РїРµСЂРµРґ РєР°Р¶РґС‹Рј РїР°С‚С‡РµРј
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

# Personal Access Token РёР· github.com/settings/tokens.
# РќР• С…СЂР°РЅРёС‚СЊ РІ С„Р°Р№Р»Рµ: Р·Р°РґР°Р№ РїРµСЂРµРјРµРЅРЅСѓСЋ РѕРєСЂСѓР¶РµРЅРёСЏ SLOPPY_GITHUB_TOKEN
#   PowerShell:  $env:SLOPPY_GITHUB_TOKEN = "github_pat_..."
#   РїРѕСЃС‚РѕСЏРЅРЅРѕ:   setx SLOPPY_GITHUB_TOKEN "github_pat_..."
GITHUB_TOKEN = os.environ.get("SLOPPY_GITHUB_TOKEN", "")

# Р’РµСЂСЃРёСЏ РїР°С‚С‡Р° вЂ” РјРµРЅСЏР№ РїСЂРё РєР°Р¶РґРѕРј РЅРѕРІРѕРј РїР°С‚С‡Рµ, РЅР°РїСЂРёРјРµСЂ "7.42"
PATCH_VERSION = "7.41f"

# РџСѓС‚СЊ Рє РїР°РїРєРµ dota (С‚Р°Рј, РіРґРµ pak01_dir.vpk).
# Р•СЃР»Рё Steam СЃС‚РѕРёС‚ РЅР° РґСЂСѓРіРѕРј РґРёСЃРєРµ вЂ” РїРѕРїСЂР°РІСЊ.
DOTA_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota"

# РљСѓРґР° Р·Р°Р»РёРІР°С‚СЊ РІ СЂРµРїРѕ
GITHUB_OWNER  = "sikleq"
GITHUB_REPO   = "Sloppy"

# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# Р”Р°Р»СЊС€Рµ РјРµРЅСЏС‚СЊ РЅРµ РЅР°РґРѕ
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

# РџР°С‚С‡РЅРѕСѓС‚С‹ + Р»РѕРєР°Р»РёР·Р°С†РёСЏ (РѕРїРёСЃР°РЅРёСЏ СЃРїРѕСЃРѕР±РЅРѕСЃС‚РµР№/РїСЂРµРґРјРµС‚РѕРІ) вЂ” РІ data/
PATCHNOTES_VPK_PATHS = [
    "resource/localization/patchnotes/patchnotes_english.txt",
    "resource/localization/patchnotes/patchnotes_russian.txt",
    # dota_english.txt РґРµСЂР¶РёС‚ DOTA_Tooltip_ability_<slug>_Description Рё
    # РїСЂРѕС‡РёРµ С‚СѓР»С‚РёРїС‹ вЂ” РµРґРёРЅСЃС‚РІРµРЅРЅС‹Р№ РёСЃС‚РѕС‡РЅРёРє РѕРїРёСЃР°РЅРёР№ СЃРїРѕСЃРѕР±РЅРѕСЃС‚РµР№ РІ РёРіСЂРµ.
    # Р—Р°Р»РёРІР°РµРј С‚РѕР»СЊРєРѕ Р°РЅРіР»РёР№СЃРєСѓСЋ РІРµСЂСЃРёСЋ: РґР»СЏ UI РґРѕСЃС‚Р°С‚РѕС‡РЅРѕ, Р° 80 РїР°С‚С‡РµР№ Г— 4 РњР‘
    # СЂСѓСЃСЃРєРѕР№ РІРµСЂСЃРёРё С…СЂР°РЅРёС‚СЊ РЅРµРіРґРµ.
    "resource/localization/dota_english.txt",
    # abilities_english.txt вЂ” РѕС‚РґРµР»СЊРЅС‹Р№ С„Р°Р№Р» СЃ РѕРїРёСЃР°РЅРёСЏРјРё СЃРїРѕСЃРѕР±РЅРѕСЃС‚РµР№
    # РЅРµРєРѕРЅС‚СЂРѕР»РёСЂСѓРµРјС‹С… СЋРЅРёС‚РѕРІ (creep auras, summons Рё С‚.Рї.), РєРѕС‚РѕСЂС‹С… РЅРµС‚ РІ
    # dota_english.txt. РўРѕР¶Рµ С‚РѕР»СЊРєРѕ Р°РЅРіР»РёР№СЃРєСѓСЋ РІРµСЂСЃРёСЋ.
    "resource/localization/abilities_english.txt",
]

# РЎС‚Р°С‚С‹ РіРµСЂРѕРµРІ/СЋРЅРёС‚РѕРІ/РїСЂРµРґРјРµС‚РѕРІ вЂ” РІ data/stats/{version}/
STATS_VPK_PATHS = [
    "scripts/npc/npc_heroes.txt",
    "scripts/npc/npc_units.txt",
    "scripts/npc/items.txt",
    "scripts/npc/npc_abilities.txt",
    "scripts/npc/npc_ability_ids.txt",
]

# Per-hero ability С„Р°Р№Р»С‹ вЂ” РєР°С‚Р°Р»РѕРі РІ VPK, РїРµСЂРµС‡РёСЃР»СЏРµРј РїСЂРё Р·Р°РїСѓСЃРєРµ.
# Р—Р°Р»РёРІР°СЋС‚СЃСЏ РІ data/stats/{version}/heroes/npc_dota_hero_<name>.txt
HEROES_VPK_DIR = "scripts/npc/heroes/"


def stop(msg: str):
    print(f"\nвќЊ {msg}")
    _pause()
    sys.exit(1)


def decode_valve_text(data: bytes) -> str:
    """Valve localization-С„Р°Р№Р»С‹ РѕР±С‹С‡РЅРѕ РІ UTF-16 LE СЃ BOM, РёРЅРѕРіРґР° UTF-8."""
    if data.startswith(b"\xff\xfe"):
        return data[2:].decode("utf-16-le", errors="replace")
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8", errors="replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-16-le", errors="replace")


def diff_stats(old: bytes, new: bytes):
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ (added_lines, removed_lines) РёР»Рё (None, None) РµСЃР»Рё РЅРµ РІС‹С€Р»Рѕ."""
    try:
        old_lines = decode_valve_text(old).splitlines()
        new_lines = decode_valve_text(new).splitlines()
        diff = list(difflib.unified_diff(old_lines, new_lines, n=0, lineterm=""))
        added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
        return added, removed
    except Exception:
        return None, None


def _check(r, what: str):
    """Р•РґРёРЅР°СЏ РѕР±СЂР°Р±РѕС‚РєР° РѕС‚РІРµС‚РѕРІ GitHub: 401/403 вЂ” РїРѕРЅСЏС‚РЅР°СЏ РїРѕРґСЃРєР°Р·РєР°, РїСЂРѕС‡РµРµ вЂ” С‚РµРєСЃС‚."""
    if r.status_code in (200, 201):
        return r
    if r.status_code == 401:
        stop("GitHub РѕС‚РєР°Р·Р°Р»: 401 Unauthorized.\n"
             "   РќРµРІР°Р»РёРґРЅС‹Р№ С‚РѕРєРµРЅ. РџСЂРѕРІРµСЂСЊ РїРµСЂРµРјРµРЅРЅСѓСЋ РѕРєСЂСѓР¶РµРЅРёСЏ SLOPPY_GITHUB_TOKEN.")
    if r.status_code == 403:
        stop("GitHub РѕС‚РєР°Р·Р°Р»: 403 Forbidden.\n"
             "   РЈ С‚РѕРєРµРЅР° РЅРµС‚ РїСЂР°РІ РЅР° Р·Р°РїРёСЃСЊ. РџРµСЂРµСЃРѕР·РґР°Р№ С‚РѕРєРµРЅ СЃ РїСЂР°РІР°РјРё\n"
             "   Contents = Read and write РґР»СЏ СЂРµРїРѕ sikleq/Sloppy.")
    stop(f"GitHub РІРµСЂРЅСѓР» {r.status_code} РїСЂРё {what}:\n   {r.text[:300]}")


def _normalize_kv(target_path: str, data: bytes) -> bytes:
    """KV-С„Р°Р№Р»С‹ (data/stats/**) СЃСЂР°РІРЅРёРІР°РµРј Рё РїРёС€РµРј СЃ LF.

    VPK РѕС‚РґР°С‘С‚ CRLF, Р° Р»РѕРєР°Р»СЊРЅС‹Рµ РєРѕРјРјРёС‚С‹ (autocrlf=true) РєР»Р°РґСѓС‚ РІ РёРЅРґРµРєСЃ LF.
    Р‘РµР· РЅРѕСЂРјР°Р»РёР·Р°С†РёРё РєР°Р¶РґС‹Р№ Р·Р°РїСѓСЃРє РїРµСЂРµРІРѕСЂР°С‡РёРІР°Р» РїРµСЂРµРІРѕРґС‹ СЃС‚СЂРѕРє РІРѕ РІСЃРµС…
    ~130 С„Р°Р№Р»Р°С… РіРµСЂРѕРµРІ Рё РґР°РІР°Р» 130 В«РёР·РјРµРЅРµРЅРёР№В» Р±РµР· РµРґРёРЅРѕР№ РїСЂР°РІРєРё РїРѕ СЃСѓС‚Рё.
    Р›РѕРє-С„Р°Р№Р»С‹ РІ data/ (patchnotes Рё С‚.Рї.) РќР• С‚СЂРѕРіР°РµРј вЂ” Р±Р°Р№С‚ РІ Р±Р°Р№С‚.
    """
    if not target_path.startswith("data/stats/"):
        return data
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):   # UTF-16 вЂ” РЅРµ С‚РµРєСЃС‚ РґР»СЏ РЅР°СЃ
        return data
    return data.replace(b"\r\n", b"\n")


def plan_file(session, api_base: str, target_path: str, new_bytes: bytes, label: str):
    """РЎСЂР°РІРЅРёРІР°РµС‚ С„Р°Р№Р» СЃ СЂРµРїРѕ. Р’РѕР·РІСЂР°С‰Р°РµС‚ (target_path, bytes_to_write) РїСЂРё
    СЂРµР°Р»СЊРЅРѕРј РёР·РјРµРЅРµРЅРёРё, РёРЅР°С‡Рµ None. РќРёС‡РµРіРѕ РќР• Р·Р°Р»РёРІР°РµС‚."""
    r = session.get(f"{api_base}/{target_path}")
    existing_bytes = None
    if r.status_code == 200:
        d = r.json()
        if d.get("encoding") == "none" or not d.get("content"):
            # Р¤Р°Р№Р»С‹ > 1 РњР‘: Contents API РЅРµ РѕС‚РґР°С‘С‚ content (encoding='none').
            # Р Р°РЅСЊС€Рµ СЌС‚Рѕ С‡РёС‚Р°Р»РѕСЃСЊ РєР°Рє В«РїСѓСЃС‚Рѕ в‰  С„Р°Р№Р»В» в†’ РїРµСЂРµР·Р°Р»РёРІ С‚РµС… Р¶Рµ Р±Р°Р№С‚
            # Рё РїСѓСЃС‚РѕР№ РєРѕРјРјРёС‚ РЅР° РєР°Р¶РґРѕРј Р·Р°РїСѓСЃРєРµ. Р‘РµСЂС‘Рј blob РїРѕ sha (РґРѕ 100 РњР‘).
            blob_url = api_base.rsplit("/contents", 1)[0] + f"/git/blobs/{d['sha']}"
            b = _check(session.get(blob_url), f"С‡С‚РµРЅРёРё blob {target_path}").json()
            existing_bytes = base64.b64decode(b["content"])
        else:
            existing_bytes = base64.b64decode(d["content"])
    elif r.status_code != 404:
        _check(r, f"С‡С‚РµРЅРёРё {target_path}")

    new_norm = _normalize_kv(target_path, new_bytes)
    old_norm = _normalize_kv(target_path, existing_bytes) if existing_bytes is not None else None

    if old_norm == new_norm:
        print(f"  рџ“„ {label}: РёР·РјРµРЅРµРЅРёР№ РЅРµ Р±С‹Р»Рѕ.")
        return None

    if existing_bytes is None:
        print(f"  вњЁ {label}: РЅРѕРІС‹Р№ С„Р°Р№Р».")
    else:
        print(f"  рџ”„ {label}: СЃРѕРґРµСЂР¶РёРјРѕРµ РёР·РјРµРЅРёР»РѕСЃСЊ.")
        added, removed = diff_stats(old_norm, new_norm)
        if added is not None:
            print(f"      +{added} СЃС‚СЂРѕРє   в€’{removed} СЃС‚СЂРѕРє")
        print(f"      СЂР°Р·РјРµСЂ: Р±С‹Р»Рѕ {len(existing_bytes):,} в†’ СЃС‚Р°Р»Рѕ {len(new_norm):,} Р±Р°Р№С‚")
    return (target_path, new_norm)


def commit_batch(session, owner: str, repo: str, changes, message: str) -> str:
    """РћР”РРќ РєРѕРјРјРёС‚ РЅР° РІСЃРµ РёР·РјРµРЅС‘РЅРЅС‹Рµ С„Р°Р№Р»С‹ (Git Data API: blobs в†’ tree в†’ commit в†’ ref).
    Р’РѕР·РІСЂР°С‰Р°РµС‚ html_url РєРѕРјРјРёС‚Р°."""
    api = f"https://api.github.com/repos/{owner}/{repo}"

    head = _check(session.get(f"{api}/git/ref/heads/main"), "С‡С‚РµРЅРёРё ref main").json()["object"]["sha"]
    base_tree = _check(session.get(f"{api}/git/commits/{head}"), "С‡С‚РµРЅРёРё HEAD-РєРѕРјРјРёС‚Р°").json()["tree"]["sha"]

    tree = []
    for path, content in changes:
        blob = _check(session.post(f"{api}/git/blobs", json={
            "content": base64.b64encode(content).decode("ascii"),
            "encoding": "base64",
        }), f"СЃРѕР·РґР°РЅРёРё blob {path}").json()["sha"]
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": blob})

    new_tree = _check(session.post(f"{api}/git/trees", json={
        "base_tree": base_tree, "tree": tree,
    }), "СЃРѕР·РґР°РЅРёРё tree").json()["sha"]
    if new_tree == base_tree:
        # Р’СЃРµ blob'С‹ СЃРѕРІРїР°Р»Рё СЃ С‚РµРј, С‡С‚Рѕ СѓР¶Рµ РІ СЂРµРїРѕ вЂ” РєРѕРјРјРёС‚РёС‚СЊ РЅРµС‡РµРіРѕ.
        print("   РґРµСЂРµРІРѕ РЅРµ РёР·РјРµРЅРёР»РѕСЃСЊ (Р±Р°Р№С‚С‹ СЃРѕРІРїР°Р»Рё) вЂ” РєРѕРјРјРёС‚ РЅРµ СЃРѕР·РґР°СЋ.")
        return ""
    commit = _check(session.post(f"{api}/git/commits", json={
        "message": message, "tree": new_tree, "parents": [head],
    }), "СЃРѕР·РґР°РЅРёРё РєРѕРјРјРёС‚Р°").json()
    _check(session.patch(f"{api}/git/refs/heads/main", json={"sha": commit["sha"]}),
           "РѕР±РЅРѕРІР»РµРЅРёРё ref main")
    return commit.get("html_url", "")


def main():
    print("=" * 62)
    print("  Dota Patch Notes & Stats Sync")
    print(f"  РџР°С‚С‡: {PATCH_VERSION}")
    print("=" * 62)

    # в”Ђв”Ђ РџСЂРѕРІРµСЂРєР° Р±РёР±Р»РёРѕС‚РµРє в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    try:
        import vpk
    except ImportError:
        stop("РЅРµ СѓСЃС‚Р°РЅРѕРІР»РµРЅР° Р±РёР±Р»РёРѕС‚РµРєР° vpk.\n"
             "   Р’ РєРѕРјР°РЅРґРЅРѕР№ СЃС‚СЂРѕРєРµ РІС‹РїРѕР»РЅРё:  pip install vpk")
    try:
        import requests
    except ImportError:
        stop("РЅРµ СѓСЃС‚Р°РЅРѕРІР»РµРЅР° Р±РёР±Р»РёРѕС‚РµРєР° requests.\n"
             "   Р’ РєРѕРјР°РЅРґРЅРѕР№ СЃС‚СЂРѕРєРµ РІС‹РїРѕР»РЅРё:  pip install requests")

    # в”Ђв”Ђ РџСЂРѕРІРµСЂРєР° С‚РѕРєРµРЅР° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    if not GITHUB_TOKEN:
        stop("РЅРµ Р·Р°РґР°РЅ GitHub Token.\n"
             "   РЎРѕР·РґР°Р№ РµРіРѕ РЅР° https://github.com/settings/tokens?type=beta\n"
             "   (Contents = Read and write РґР»СЏ sikleq/Sloppy) Рё РїРѕР»РѕР¶Рё РІ РїРµСЂРµРјРµРЅРЅСѓСЋ\n"
             "   РѕРєСЂСѓР¶РµРЅРёСЏ:  setx SLOPPY_GITHUB_TOKEN \"github_pat_...\"\n"
             "   (РїРѕСЃР»Рµ setx РїРµСЂРµР·Р°РїСѓСЃС‚Рё РѕРєРЅРѕ/С‚РµСЂРјРёРЅР°Р»).")

    if not PATCH_VERSION or PATCH_VERSION == "X.XX":
        stop("РЅРµ СѓРєР°Р·Р°РЅР° РІРµСЂСЃРёСЏ РїР°С‚С‡Р°.\n"
             "   Р’РїРёС€Рё С‚РµРєСѓС‰СѓСЋ РІРµСЂСЃРёСЋ РІ РїРµСЂРµРјРµРЅРЅСѓСЋ PATCH_VERSION,\n"
             "   РЅР°РїСЂРёРјРµСЂ:  PATCH_VERSION = \"7.42\"")

    # в”Ђв”Ђ РџСЂРѕРІРµСЂРєР° РїСѓС‚Рё Рє VPK в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    vpk_file = Path(DOTA_PATH) / "pak01_dir.vpk"
    if not vpk_file.exists():
        stop(f"РЅРµ РЅР°Р№РґРµРЅ pak01_dir.vpk РїРѕ РїСѓС‚Рё:\n   {vpk_file}\n\n"
             "РџСЂРѕРІРµСЂСЊ РїРµСЂРµРјРµРЅРЅСѓСЋ DOTA_PATH РІ РЅР°С‡Р°Р»Рµ СЃРєСЂРёРїС‚Р°.\n"
             "Р•СЃР»Рё Steam СЃС‚РѕРёС‚ РЅР° РґСЂСѓРіРѕРј РґРёСЃРєРµ РёР»Рё РІ РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅРѕР№ РїР°РїРєРµ вЂ”\n"
             "РїРѕРїСЂР°РІСЊ РїСѓС‚СЊ.")

    # в”Ђв”Ђ РћС‚РєСЂС‹РІР°РµРј VPK в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    print(f"\nрџ“¦ Р§РёС‚Р°СЋ {vpk_file.name}...")
    try:
        pak = vpk.open(str(vpk_file))
    except Exception as e:
        stop(f"РЅРµ РїРѕР»СѓС‡РёР»РѕСЃСЊ РѕС‚РєСЂС‹С‚СЊ VPK-Р°СЂС…РёРІ:\n   {e}")

    def read_vpk(internal_path: str) -> bytes:
        try:
            f = pak.get_file(internal_path)
            content = f.read()
            f.close()
            return content
        except KeyError:
            stop(f"РІ VPK РЅРµ РЅР°Р№РґРµРЅ С„Р°Р№Р»: {internal_path}\n"
                 "   Valve РјРѕРі РїРѕРјРµРЅСЏС‚СЊ РїСѓС‚СЊ вЂ” РЅР°РїРёС€Рё, СЂР°Р·Р±РµСЂС‘РјСЃСЏ.")

    # в”Ђв”Ђ РР·РІР»РµРєР°РµРј РїР°С‚С‡РЅРѕСѓС‚С‹ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    print("\nв”Ђв”Ђ РџР°С‚С‡РЅРѕСѓС‚С‹ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ")
    patchnotes = {}
    for internal in PATCHNOTES_VPK_PATHS:
        content = read_vpk(internal)
        local_name = internal.rsplit("/", 1)[-1]
        patchnotes[local_name] = content
        print(f"   вњ“ {local_name}  ({len(content):,} Р±Р°Р№С‚)")

    # в”Ђв”Ђ РР·РІР»РµРєР°РµРј СЃС‚Р°С‚С‹ РіРµСЂРѕРµРІ/СЋРЅРёС‚РѕРІ/РїСЂРµРґРјРµС‚РѕРІ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    print("\nв”Ђв”Ђ РЎС‚Р°С‚С‹ РіРµСЂРѕРµРІ / СЋРЅРёС‚РѕРІ / РїСЂРµРґРјРµС‚РѕРІ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ")
    stats = {}
    for internal in STATS_VPK_PATHS:
        content = read_vpk(internal)
        local_name = internal.rsplit("/", 1)[-1]
        stats[local_name] = content
        print(f"   вњ“ {local_name}  ({len(content):,} Р±Р°Р№С‚)")

    # в”Ђв”Ђ Per-hero ability С„Р°Р№Р»С‹ (scripts/npc/heroes/*.txt) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    # VPK СЃРѕРґРµСЂР¶РёС‚ ~128 npc_dota_hero_<name>.txt вЂ” СЂР°СЃРєСЂС‹РІР°РµРј РІСЃРµ Рё Р·Р°Р»РёРІР°РµРј
    # СЃС‹СЂС‹РјРё РІ data/stats/{version}/heroes/. РўР°Рј Р»РµР¶Р°С‚ СЃРІРѕР№СЃС‚РІР° СЃРїРѕСЃРѕР±РЅРѕСЃС‚РµР№,
    # РІРєР»СЋС‡Р°СЏ СЃРєСЂС‹С‚С‹Рµ (Transfiguration Рё С‚.Рї.), РєРѕС‚РѕСЂС‹С… РЅРµС‚ РІ РєРѕСЂРЅРµРІРѕРј
    # npc_abilities.txt.
    print("\nв”Ђв”Ђ Per-hero ability С„Р°Р№Р»С‹ (heroes/*.txt) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ")
    hero_files: dict[str, bytes] = {}
    try:
        all_paths = list(pak)  # PAK РїРѕРґРґРµСЂР¶РёРІР°РµС‚ РёС‚РµСЂР°С†РёСЋ РїРѕ РїСѓС‚СЏРј
    except TypeError:
        # РЎС‚Р°СЂС‹Рµ РІРµСЂСЃРёРё vpk РЅРµ РёС‚РµСЂРёСЂСѓСЋС‚СЃСЏ вЂ” С„РѕР»Р±СЌРє С‡РµСЂРµР· РїСЂРёРІР°С‚РЅРѕРµ РїРѕР»Рµ.
        all_paths = list(getattr(pak, "tree", {}).keys())
    for path in all_paths:
        if (path.startswith(HEROES_VPK_DIR)
                and path.endswith(".txt")
                and "npc_dota_hero_" in path):
            local_name = path.rsplit("/", 1)[-1]
            try:
                hero_files[local_name] = read_vpk(path)
            except SystemExit:
                # read_vpk РІС‹Р·С‹РІР°РµС‚ stop() РЅР° РѕС€РёР±РєРµ; РїСЂРѕРїСѓСЃРєР°РµРј С„Р°Р№Р»
                continue
    print(f"   вњ“ РЅР°Р№РґРµРЅРѕ {len(hero_files)} hero-С„Р°Р№Р»РѕРІ")

    # в”Ђв”Ђ Р—Р°Р»РёРІР°РµРј РІ GitHub в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    print(f"\nвЃ  РЎРёРЅС…СЂРѕРЅРёР·РёСЂСѓСЋ СЃ {GITHUB_OWNER}/{GITHUB_REPO}...")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "patchnotes-sync",
    })

    api_base = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents"
    changes = []   # (repo_path, bytes) вЂ” РІСЃС‘ СЂРµР°Р»СЊРЅРѕ РёР·РјРµРЅРёРІС€РµРµСЃСЏ; Р·Р°Р»РёРІР°РµС‚СЃСЏ РћР”РќРРњ РєРѕРјРјРёС‚РѕРј

    print("\nв”Ђв”Ђ data/ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ")
    for fname, content in patchnotes.items():
        p = plan_file(session, api_base, f"data/{fname}", content, fname)
        if p: changes.append(p)

    print(f"\nв”Ђв”Ђ data/stats/{PATCH_VERSION}/ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ")
    for fname, content in stats.items():
        target = f"data/stats/{PATCH_VERSION}/{fname}"
        p = plan_file(session, api_base, target, content, f"{PATCH_VERSION}/{fname}")
        if p: changes.append(p)

    print(f"\nв”Ђв”Ђ data/stats/{PATCH_VERSION}/heroes/ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ")
    for fname, content in sorted(hero_files.items()):
        target = f"data/stats/{PATCH_VERSION}/heroes/{fname}"
        p = plan_file(session, api_base, target, content, f"{PATCH_VERSION}/heroes/{fname}")
        if p: changes.append(p)

    # в”Ђв”Ђ РС‚РѕРі: РѕРґРёРЅ РєРѕРјРјРёС‚ РЅР° РІСЃС‘ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    print()
    if not changes:
        print("вњ… РР·РјРµРЅРµРЅРёР№ РЅРµ Р±С‹Р»Рѕ вЂ” РІ СЂРµРїРѕ РЅРёС‡РµРіРѕ РЅРµ РѕС‚РїСЂР°РІР»РµРЅРѕ.")
    else:
        print(f"в¬† Р—Р°Р»РёРІР°СЋ {len(changes)} С„Р°Р№Р»(РѕРІ) РѕРґРЅРёРј РєРѕРјРјРёС‚РѕРј...")
        url = commit_batch(session, GITHUB_OWNER, GITHUB_REPO, changes,
                           f"sync {PATCH_VERSION}: {len(changes)} file(s) from VPK")
        print("вњ… Р“РѕС‚РѕРІРѕ.")
        if url:
            print(f"   {url}")

    _pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nРћС‚РјРµРЅРµРЅРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»РµРј.")
        sys.exit(1)
