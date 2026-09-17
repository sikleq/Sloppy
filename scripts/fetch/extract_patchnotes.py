"""
Dota 2 Patch Notes — Extractor & Auto-Uploader
==============================================
Достаёт из локального pak01_dir.vpk:
  • patchnotes_english.txt  → data/
  • patchnotes_russian.txt  → data/
  • npc_heroes.txt          → data/stats/{version}/
  • npc_units.txt           → data/stats/{version}/
  • items.txt               → data/stats/{version}/

и заливает в GitHub-репозиторий sikleq/Sloppy.

Запускать после каждого обновления Dota 2 (или по желанию).

ПЕРЕД ПЕРВЫМ ЗАПУСКОМ:
─────────────────────────────────────────────────────────
1. Установить Python:    https://python.org/downloads/
   (при установке поставь галочку "Add Python to PATH" !)

2. Открыть командную строку (Win+R → cmd) и выполнить:
       pip install vpk requests

3. Создать Personal Access Token:
   https://github.com/settings/tokens?type=beta
       Token name:               dota-patch-uploader
       Repository access:        Only select repositories
                                 → выбрать sikleq/Sloppy
       Repository permissions:   Contents = Read and write
       Generate token в†’ РЎРљРћРџРР РћР’РђРўР¬ (РїРѕРєР°Р·С‹РІР°РµС‚СЃСЏ РѕРґРёРЅ СЂР°Р·!)

4. Вставить токен в переменную GITHUB_TOKEN ниже.
5. Вставить текущую версию патча в PATCH_VERSION ниже.

ВАЖНО ⚠ : храни этот файл у себя на ПК. НЕ заливай его никуда —
там твой персональный токен. Если случайно засветил — отозвать
можно на той же странице токенов на GitHub.

ЗАПУСК:
─────────────────────────────────────────────────────────
   python extract_patchnotes.py

или просто двойной клик по этому файлу (если Python поставился
правильно и .py-файлы открываются им).
"""

import base64
import difflib
import os
import sys
from pathlib import Path

# Консоль Windows по умолчанию cp1251 — эмодзи в print() роняли скрипт.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _pause(msg: str = "\nНажми Enter чтобы закрыть окно..."):
    """Ждать Enter только при запуске из окна; из терминала/агента — не блокировать."""
    if sys.stdin is not None and sys.stdin.isatty():
        try:
            input(msg)
        except EOFError:
            pass

# ═════════════════════════════════════════════════════════════════
# РќРђРЎРўР РћР™РљР вЂ” РѕС‚СЂРµРґР°РєС‚РёСЂСѓР№ РїРµСЂРµРґ РєР°Р¶РґС‹Рј РїР°С‚С‡РµРј
# ═════════════════════════════════════════════════════════════════

# Personal Access Token из github.com/settings/tokens.
# НЕ хранить в файле: задай переменную окружения SLOPPY_GITHUB_TOKEN
#   PowerShell:  $env:SLOPPY_GITHUB_TOKEN = "github_pat_..."
#   постоянно:   setx SLOPPY_GITHUB_TOKEN "github_pat_..."
GITHUB_TOKEN = os.environ.get("SLOPPY_GITHUB_TOKEN", "")

# Версия патча — меняй при каждом новом патче, например "7.42"
PATCH_VERSION = "7.41f"

# Путь к папке dota (там, где pak01_dir.vpk).
# Если Steam стоит на другом диске — поправь.
DOTA_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota"

# Куда заливать в репо
GITHUB_OWNER  = "sikleq"
GITHUB_REPO   = "Sloppy"

# ═════════════════════════════════════════════════════════════════
# Дальше менять не надо
# ═════════════════════════════════════════════════════════════════

# Патчноуты + локализация (описания способностей/предметов) — в data/
PATCHNOTES_VPK_PATHS = [
    "resource/localization/patchnotes/patchnotes_english.txt",
    "resource/localization/patchnotes/patchnotes_russian.txt",
    # dota_english.txt держит DOTA_Tooltip_ability_<slug>_Description и
    # прочие тултипы — единственный источник описаний способностей в игре.
    # Заливаем только английскую версию: для UI достаточно, а 80 патчей × 4 МБ
    # русской версии хранить негде.
    "resource/localization/dota_english.txt",
    # abilities_english.txt — отдельный файл с описаниями способностей
    # неконтролируемых юнитов (creep auras, summons и т.п.), которых нет в
    # dota_english.txt. Тоже только английскую версию.
    "resource/localization/abilities_english.txt",
]

# Статы героев/юнитов/предметов — в data/stats/{version}/
STATS_VPK_PATHS = [
    "scripts/npc/npc_heroes.txt",
    "scripts/npc/npc_units.txt",
    "scripts/npc/items.txt",
    "scripts/npc/npc_abilities.txt",
    "scripts/npc/npc_ability_ids.txt",
]

# Per-hero ability файлы — каталог в VPK, перечисляем при запуске.
# Заливаются в data/stats/{version}/heroes/npc_dota_hero_<name>.txt
HEROES_VPK_DIR = "scripts/npc/heroes/"


def stop(msg: str):
    print(f"\n❌ {msg}")
    _pause()
    sys.exit(1)


def decode_valve_text(data: bytes) -> str:
    """Valve localization-файлы обычно в UTF-16 LE с BOM, иногда UTF-8."""
    if data.startswith(b"\xff\xfe"):
        return data[2:].decode("utf-16-le", errors="replace")
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8", errors="replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-16-le", errors="replace")


def diff_stats(old: bytes, new: bytes):
    """Возвращает (added_lines, removed_lines) или (None, None) если не вышло."""
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
    """Единая обработка ответов GitHub: 401/403 — понятная подсказка, прочее — текст."""
    if r.status_code in (200, 201):
        return r
    if r.status_code == 401:
        stop("GitHub отказал: 401 Unauthorized.\n"
             "   Невалидный токен. Проверь переменную окружения SLOPPY_GITHUB_TOKEN.")
    if r.status_code == 403:
        stop("GitHub отказал: 403 Forbidden.\n"
             "   У токена нет прав на запись. Пересоздай токен с правами\n"
             "   Contents = Read and write для репо sikleq/Sloppy.")
    stop(f"GitHub вернул {r.status_code} при {what}:\n   {r.text[:300]}")


def _normalize_kv(target_path: str, data: bytes) -> bytes:
    """KV-файлы (data/stats/**) сравниваем и пишем с LF.

    VPK отдаёт CRLF, а локальные коммиты (autocrlf=true) кладут в индекс LF.
    Без нормализации каждый запуск переворачивал переводы строк во всех
    ~130 файлах героев и давал 130 «изменений» без единой правки по сути.
    Лок-файлы в data/ (patchnotes и т.п.) НЕ трогаем — байт в байт.
    """
    if not target_path.startswith("data/stats/"):
        return data
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):   # UTF-16 — не текст для нас
        return data
    return data.replace(b"\r\n", b"\n")


def plan_file(session, api_base: str, target_path: str, new_bytes: bytes, label: str):
    """Сравнивает файл с репо. Возвращает (target_path, bytes_to_write) при
    реальном изменении, иначе None. Ничего НЕ заливает."""
    r = session.get(f"{api_base}/{target_path}")
    existing_bytes = None
    if r.status_code == 200:
        d = r.json()
        if d.get("encoding") == "none" or not d.get("content"):
            # Файлы > 1 МБ: Contents API не отдаёт content (encoding='none').
            # Раньше это читалось как «пусто ≠ файл» → перезалив тех же байт
            # и пустой коммит на каждом запуске. Берём blob по sha (до 100 МБ).
            blob_url = api_base.rsplit("/contents", 1)[0] + f"/git/blobs/{d['sha']}"
            b = _check(session.get(blob_url), f"чтении blob {target_path}").json()
            existing_bytes = base64.b64decode(b["content"])
        else:
            existing_bytes = base64.b64decode(d["content"])
    elif r.status_code != 404:
        _check(r, f"чтении {target_path}")

    new_norm = _normalize_kv(target_path, new_bytes)
    old_norm = _normalize_kv(target_path, existing_bytes) if existing_bytes is not None else None

    if old_norm == new_norm:
        print(f"  📄 {label}: изменений не было.")
        return None

    if existing_bytes is None:
        print(f"  ✨ {label}: новый файл.")
    else:
        print(f"  🔄 {label}: содержимое изменилось.")
        added, removed = diff_stats(old_norm, new_norm)
        if added is not None:
            print(f"      +{added} строк   −{removed} строк")
        print(f"      размер: было {len(existing_bytes):,} → стало {len(new_norm):,} байт")
    return (target_path, new_norm)


def commit_batch(session, owner: str, repo: str, changes, message: str) -> str:
    """РћР”РРќ РєРѕРјРјРёС‚ РЅР° РІСЃРµ РёР·РјРµРЅС‘РЅРЅС‹Рµ С„Р°Р№Р»С‹ (Git Data API: blobs в†’ tree в†’ commit в†’ ref).
    Возвращает html_url коммита."""
    api = f"https://api.github.com/repos/{owner}/{repo}"

    head = _check(session.get(f"{api}/git/ref/heads/main"), "чтении ref main").json()["object"]["sha"]
    base_tree = _check(session.get(f"{api}/git/commits/{head}"), "чтении HEAD-коммита").json()["tree"]["sha"]

    tree = []
    for path, content in changes:
        blob = _check(session.post(f"{api}/git/blobs", json={
            "content": base64.b64encode(content).decode("ascii"),
            "encoding": "base64",
        }), f"создании blob {path}").json()["sha"]
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": blob})

    new_tree = _check(session.post(f"{api}/git/trees", json={
        "base_tree": base_tree, "tree": tree,
    }), "создании tree").json()["sha"]
    if new_tree == base_tree:
        # Все blob'ы совпали с тем, что уже в репо — коммитить нечего.
        print("   дерево не изменилось (байты совпали) — коммит не создаю.")
        return ""
    commit = _check(session.post(f"{api}/git/commits", json={
        "message": message, "tree": new_tree, "parents": [head],
    }), "создании коммита").json()
    _check(session.patch(f"{api}/git/refs/heads/main", json={"sha": commit["sha"]}),
           "обновлении ref main")
    return commit.get("html_url", "")


def main():
    print("=" * 62)
    print("  Dota Patch Notes & Stats Sync")
    print(f"  Патч: {PATCH_VERSION}")
    print("=" * 62)

    # ── Проверка библиотек ──────────────────────────────────────
    try:
        import vpk
    except ImportError:
        stop("не установлена библиотека vpk.\n"
             "   В командной строке выполни:  pip install vpk")
    try:
        import requests
    except ImportError:
        stop("не установлена библиотека requests.\n"
             "   В командной строке выполни:  pip install requests")

    # ── Проверка токена ─────────────────────────────────────────
    if not GITHUB_TOKEN:
        stop("не задан GitHub Token.\n"
             "   Создай его на https://github.com/settings/tokens?type=beta\n"
             "   (Contents = Read and write для sikleq/Sloppy) и положи в переменную\n"
             "   окружения:  setx SLOPPY_GITHUB_TOKEN \"github_pat_...\"\n"
             "   (после setx перезапусти окно/терминал).")

    if not PATCH_VERSION or PATCH_VERSION == "X.XX":
        stop("не указана версия патча.\n"
             "   Впиши текущую версию в переменную PATCH_VERSION,\n"
             "   например:  PATCH_VERSION = \"7.42\"")

    # ── Проверка пути к VPK ─────────────────────────────────────
    vpk_file = Path(DOTA_PATH) / "pak01_dir.vpk"
    if not vpk_file.exists():
        stop(f"не найден pak01_dir.vpk по пути:\n   {vpk_file}\n\n"
             "Проверь переменную DOTA_PATH в начале скрипта.\n"
             "Если Steam стоит на другом диске или в нестандартной папке —\n"
             "поправь путь.")

    # ── Открываем VPK ───────────────────────────────────────────
    print(f"\n📦 Читаю {vpk_file.name}...")
    try:
        pak = vpk.open(str(vpk_file))
    except Exception as e:
        stop(f"не получилось открыть VPK-архив:\n   {e}")

    def read_vpk(internal_path: str) -> bytes:
        try:
            f = pak.get_file(internal_path)
            content = f.read()
            f.close()
            return content
        except KeyError:
            stop(f"в VPK не найден файл: {internal_path}\n"
                 "   Valve мог поменять путь — напиши, разберёмся.")

    # в”Ђв”Ђ РР·РІР»РµРєР°РµРј РїР°С‚С‡РЅРѕСѓС‚С‹ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    print("\n── Патчноуты ──────────────────────────────────────────")
    patchnotes = {}
    for internal in PATCHNOTES_VPK_PATHS:
        content = read_vpk(internal)
        local_name = internal.rsplit("/", 1)[-1]
        patchnotes[local_name] = content
        print(f"   ✓ {local_name}  ({len(content):,} байт)")

    # в”Ђв”Ђ РР·РІР»РµРєР°РµРј СЃС‚Р°С‚С‹ РіРµСЂРѕРµРІ/СЋРЅРёС‚РѕРІ/РїСЂРµРґРјРµС‚РѕРІ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    print("\n── Статы героев / юнитов / предметов ─────────────────")
    stats = {}
    for internal in STATS_VPK_PATHS:
        content = read_vpk(internal)
        local_name = internal.rsplit("/", 1)[-1]
        stats[local_name] = content
        print(f"   ✓ {local_name}  ({len(content):,} байт)")

    # ── Per-hero ability файлы (scripts/npc/heroes/*.txt) ──────
    # VPK содержит ~128 npc_dota_hero_<name>.txt — раскрываем все и заливаем
    # сырыми в data/stats/{version}/heroes/. Там лежат свойства способностей,
    # включая скрытые (Transfiguration и т.п.), которых нет в корневом
    # npc_abilities.txt.
    print("\n── Per-hero ability файлы (heroes/*.txt) ─────────────")
    hero_files: dict[str, bytes] = {}
    try:
        all_paths = list(pak)  # PAK поддерживает итерацию по путям
    except TypeError:
        # Старые версии vpk не итерируются — фолбэк через приватное поле.
        all_paths = list(getattr(pak, "tree", {}).keys())
    for path in all_paths:
        if (path.startswith(HEROES_VPK_DIR)
                and path.endswith(".txt")
                and "npc_dota_hero_" in path
                and not path.endswith("npc_dota_hero_base.txt")):   # 7.41f+: parent template, not a hero
            local_name = path.rsplit("/", 1)[-1]
            try:
                hero_files[local_name] = read_vpk(path)
            except SystemExit:
                # read_vpk вызывает stop() на ошибке; пропускаем файл
                continue
    print(f"   ✓ найдено {len(hero_files)} hero-файлов")

    # ── Заливаем в GitHub ────────────────────────────────────────
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

    print("\n── data/ ───────────────────────────────────────────────")
    for fname, content in patchnotes.items():
        p = plan_file(session, api_base, f"data/{fname}", content, fname)
        if p: changes.append(p)

    print(f"\n── data/stats/{PATCH_VERSION}/ ─────────────────────────────────")
    for fname, content in stats.items():
        target = f"data/stats/{PATCH_VERSION}/{fname}"
        p = plan_file(session, api_base, target, content, f"{PATCH_VERSION}/{fname}")
        if p: changes.append(p)

    print(f"\n── data/stats/{PATCH_VERSION}/heroes/ ─────────────────────────")
    for fname, content in sorted(hero_files.items()):
        target = f"data/stats/{PATCH_VERSION}/heroes/{fname}"
        p = plan_file(session, api_base, target, content, f"{PATCH_VERSION}/heroes/{fname}")
        if p: changes.append(p)

    # в”Ђв”Ђ РС‚РѕРі: РѕРґРёРЅ РєРѕРјРјРёС‚ РЅР° РІСЃС‘ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    print()
    if not changes:
        print("вњ… РР·РјРµРЅРµРЅРёР№ РЅРµ Р±С‹Р»Рѕ вЂ” РІ СЂРµРїРѕ РЅРёС‡РµРіРѕ РЅРµ РѕС‚РїСЂР°РІР»РµРЅРѕ.")
    else:
        print(f"⬆ Заливаю {len(changes)} файл(ов) одним коммитом...")
        url = commit_batch(session, GITHUB_OWNER, GITHUB_REPO, changes,
                           f"sync {PATCH_VERSION}: {len(changes)} file(s) from VPK")
        print("✅ Готово.")
        if url:
            print(f"   {url}")

    _pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем.")
        sys.exit(1)
