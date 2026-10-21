"""
fetch_stats.py — Скачивает базу статов героев/предметов из muk-as/DOTA2_CLIENT
для каждого патча в RELEASE_HISTORY и сохраняет локально + в репо.

КАК РАБОТАЕТ:
  1. Получает все коммиты из muk-as/DOTA2_CLIENT (пагинацией)
  2. Для каждого патча находит первый коммит на дату ≥ дата релиза
  3. Скачивает npc_heroes.txt, npc_units.txt, items.txt с того SHA
  4. Парсит KV → JSON (только нужные поля)
  5. Сохраняет локально в OUT_DIR/{version}/heroes.json и т.д.
  6. Опционально заливает в GitHub-репо (по флагу UPLOAD_TO_GITHUB)

УСТАНОВИТЬ:   pip install requests
ЗАПУСК:       python tools/fetch_stats.py

Файлы появятся в .cache/fetch_stats/ (не в git; копия сайта — data/stats/).
Потом запусти extract_patchnotes.py, чтобы залить их в GitHub.
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════

# Куда сохранять JSON-файлы локально (в .gitignore репо)
OUT_DIR = Path(__file__).resolve().parent.parent / ".cache" / "fetch_stats"

# Если True, items.json для каждого патча будет перезагружен и перепарсен,
# даже если уже существует. Остальные файлы (heroes/units/abilities/ids) — нет.
# Используется когда ITEM_FIELDS изменился (например — добавлен ItemRequirements
# для расчёта старых рецептов).
REFRESH_ITEMS_ONLY = False


def github_token() -> str:
    """Токен GitHub API (без него 60 запросов/час, с ним 5000): переменная окружения SLOPPY_GITHUB_TOKEN, иначе
    вход GitHub CLI (`gh auth token`). В файлах токен не храним."""
    token = os.environ.get("SLOPPY_GITHUB_TOKEN", "")
    if token:
        return token
    try:
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


# Репо-источник статов
SOURCE_OWNER = "muk-as"
SOURCE_REPO  = "DOTA2_CLIENT"
SOURCE_FILES = {
    "heroes":      "game/dota/pak01_dir/scripts/npc/npc_heroes.txt",
    "units":       "game/dota/pak01_dir/scripts/npc/npc_units.txt",
    "items":       "game/dota/pak01_dir/scripts/npc/items.txt",
    "abilities":   "game/dota/pak01_dir/scripts/npc/npc_abilities.txt",
    "ability_ids": "game/dota/pak01_dir/scripts/npc/npc_ability_ids.txt",
}

# Per-hero ability files. Содержат все служебные/скрытые абилки (Monkey King
# Transfiguration, prismata-like линки и т.п.), которых нет в корневом
# npc_abilities.txt. Храним сырые .txt — git хорошо жмёт дельты между патчами,
# и для diff'а свойств способностей это самый честный источник.
HEROES_DIR_PATH = "game/dota/pak01_dir/scripts/npc/heroes"

# Патчи которые нас интересуют: все из patch/meta.py RELEASE_HISTORY (один список на весь проект — новый патч
# сюда не вписывать), только те, что покрыты muk-as (с 7.33, апрель 2023). Порядок: от новых к старым.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from patch.meta import RELEASE_HISTORY as _ALL_RELEASES, _parse_date  # noqa: E402

MUK_AS_FIRST = "20.04.2023"
RELEASE_HISTORY = sorted((p for p in _ALL_RELEASES if _parse_date(p["date"]) >= _parse_date(MUK_AS_FIRST)),
                         key=lambda p: _parse_date(p["date"]), reverse=True)

# Поля которые извлекаем из npc_heroes.txt для каждого героя
HERO_FIELDS = {
    "AttributePrimary", "AttributeBaseStrength", "AttributeStrengthGain",
    "AttributeBaseAgility", "AttributeAgilityGain",
    "AttributeBaseIntelligence", "AttributeIntelligenceGain",
    "ArmorPhysical", "MagicalResistance",
    "AttackDamageMin", "AttackDamageMax", "AttackRate", "AttackRange",
    "MovementSpeed", "StatusHealth", "StatusHealthRegen",
    "StatusMana", "StatusManaRegen",
    "Ability1", "Ability2", "Ability3", "Ability4",
    "Ability5", "Ability6", "Ability7", "Ability8",
    "AbilityDraftAbilities",
}

# Поля для items.txt
# ItemRecipe/ItemResult/ItemRequirements — для item_recipe_* блоков,
# дают список компонентов для каждого крафтящегося предмета. Используются
# build_patch.py для авто-генерации блоков components_change(old=..., new=...).
ITEM_FIELDS = {
    "ItemCost", "ItemCooldown", "AbilityManaCost",
    "AbilityCooldown", "AbilityDuration", "AbilityDamage",
    "ItemRecipe", "ItemResult", "ItemRequirements",
}

# DEEP item fields — live nested inside the item's "AbilityValues" subblock
# (sometimes one more level down as {"value": "X"}). Needed for the Mana
# Items table's per-patch history on Intelligence / Mana / Mana-regen
# columns. extract_items walks AbilityValues for these and flattens them
# alongside the top-level ITEM_FIELDS.
DEEP_ITEM_FIELDS = {
    # Intelligence (and all-stats, which includes Int)
    "bonus_intellect", "bonus_int", "bonus_intelligence", "bonus_all_stats",
    # Max mana
    "bonus_mana", "max_mana",
    # Passive mana regen (Valve's inconsistent spellings)
    "bonus_mana_regen", "mana_regen", "bonus_mp_regen", "mp_regen",
    "aura_mana_regen",
    # Mana-regen multiplier (Kaya family, Meteor Hammer)
    "mana_regen_multiplier",
    # Active mana grants (amortised as regen by build_mana_items)
    "mana_gain", "replenish_amount", "mana_restore", "mana_pool",
    "mana_amount",
}

# Поля slim-извлечения для npc_abilities.txt и npc_units.txt
ABILITY_FIELDS = {"AbilityType", "AbilityBehavior", "AbilityCastRange",
                  "AbilityCooldown", "AbilityManaCost"}
UNIT_FIELDS = {"ArmorPhysical", "AttackDamageMin", "AttackDamageMax",
               "AttackRate", "AttackRange", "MovementSpeed",
               "StatusHealth", "StatusMana"}

# ═══════════════════════════════════════════════════════════
# KV ПАРСЕР (Valve KeyValues format)
# ═══════════════════════════════════════════════════════════

def parse_kv(text: str) -> dict:
    """
    Парсит Valve KeyValues формат в Python dict.
    Поддерживает вложенность, комментарии //, строки с пробелами.
    Не поддерживает #include (игнорирует такие строки).
    """
    tokens = _tokenize_kv(text)
    pos = [0]

    def peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def consume():
        t = tokens[pos[0]]
        pos[0] += 1
        return t

    def parse_value():
        result = {}
        while pos[0] < len(tokens):
            key = peek()
            if key is None or key == "}":
                return result
            consume()
            val = peek()
            if val is None:
                break
            if val == "{":
                consume()  # eat {
                result[key] = parse_value()
                if peek() == "}":
                    consume()  # eat }
            elif val != "}":
                consume()
                # Multiple values for same key → keep last
                result[key] = val
        return result

    # Top-level: expect one root key then its block
    root_key = consume()
    if peek() == "{":
        consume()
        data = parse_value()
        if peek() == "}":
            consume()
        return {root_key: data}
    return {}


def _tokenize_kv(text: str) -> list:
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        # Skip whitespace
        if c in " \t\r\n":
            i += 1
        # Skip line comments
        elif c == "/" and i + 1 < n and text[i+1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        # Skip #base / #include directives
        elif c == "#":
            while i < n and text[i] != "\n":
                i += 1
        # Braces
        elif c in "{}":
            tokens.append(c)
            i += 1
        # Quoted string
        elif c == '"':
            i += 1
            j = i
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    j += 2
                else:
                    j += 1
            tokens.append(text[i:j])
            i = j + 1
        # Unquoted token (rare in KV but handle it)
        else:
            j = i
            while j < n and text[j] not in " \t\r\n{}\"":
                j += 1
            if j > i:
                tokens.append(text[i:j])
            i = j
    return tokens


def extract_heroes(kv: dict) -> dict:
    """Достаёт только нужные поля для каждого npc_dota_hero_*."""
    root = kv.get("DOTAHeroes") or next(iter(kv.values()), {})
    out = {}
    for key, val in root.items():
        if not key.startswith("npc_dota_hero_"):
            continue
        if not isinstance(val, dict):
            continue
        filtered = {k: _coerce(v) for k, v in val.items() if k in HERO_FIELDS}
        if filtered:
            out[key] = filtered
    return out


def _walk_deep_item_fields(node, out):
    """Recursively collect DEEP_ITEM_FIELDS values from nested AbilityValues
    subblocks. A value can be a bare scalar string, or a {"value": "X", ...}
    block (Valve uses both forms). First occurrence wins."""
    if not isinstance(node, dict):
        return
    for k, v in node.items():
        if k in DEEP_ITEM_FIELDS and k not in out:
            if isinstance(v, str):
                out[k] = _coerce(v)
            elif isinstance(v, dict) and isinstance(v.get("value"), str):
                out[k] = _coerce(v["value"])
        if isinstance(v, dict):
            _walk_deep_item_fields(v, out)


def extract_items(kv: dict) -> dict:
    """Достаёт поля предметов (item_*) — top-level ITEM_FIELDS плюс
    вложенные DEEP_ITEM_FIELDS из AbilityValues (для Mana Items истории)."""
    root = kv.get("DOTAAbilities") or next(iter(kv.values()), {})
    out = {}
    for key, val in root.items():
        if not key.startswith("item_"):
            continue
        if not isinstance(val, dict):
            continue
        filtered = {k: _coerce(v) for k, v in val.items() if k in ITEM_FIELDS}
        # Pull nested mana-relevant fields up to the flat per-item dict so
        # the slim items.json stays a single flat level per slug.
        _walk_deep_item_fields(val, filtered)
        if filtered:
            out[key] = filtered
    return out


def extract_abilities(kv: dict) -> dict:
    """Slim parse npc_abilities.txt — keep only ABILITY_FIELDS per slug."""
    root = next(iter(kv.values()), {}) if kv else {}
    out = {}
    for key, val in root.items():
        if not isinstance(val, dict):
            continue
        if key.startswith("Version") or key.startswith("ability_base") or "_" not in key:
            continue
        filtered = {k: _coerce(v) for k, v in val.items() if k in ABILITY_FIELDS}
        if filtered:
            out[key] = filtered
    return out


def extract_units(kv: dict) -> dict:
    """Slim parse npc_units.txt — keep only UNIT_FIELDS per npc_dota_*."""
    root = next(iter(kv.values()), {}) if kv else {}
    out = {}
    for key, val in root.items():
        if not key.startswith("npc_dota_") or not isinstance(val, dict):
            continue
        filtered = {k: _coerce(v) for k, v in val.items() if k in UNIT_FIELDS}
        if filtered:
            out[key] = filtered
    return out


def extract_ability_ids(kv: dict) -> dict:
    """npc_ability_ids.txt — DOTAAbilityIDs > UnitAbilities > <Group> > {slug: id}.
    Walk all nesting and collect every {slug: numeric_id_string} pair."""
    out = {}
    def walk(node):
        if not isinstance(node, dict):
            return
        for k, v in node.items():
            if isinstance(v, dict):
                walk(v)
            elif isinstance(v, str) and v.isdigit():
                out[v] = k
    walk(kv)
    return out


def _coerce(v):
    """Пробует преобразовать строку в число."""
    if not isinstance(v, str):
        return v
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


# ═══════════════════════════════════════════════════════════
# GITHUB API HELPERS
# ═══════════════════════════════════════════════════════════

def make_session():
    try:
        import requests
    except ImportError:
        print("❌ pip install requests")
        sys.exit(1)
    s = requests.Session()
    token = github_token()
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    s.headers["Accept"] = "application/vnd.github+json"
    s.headers["X-GitHub-Api-Version"] = "2022-11-28"
    s.headers["User-Agent"] = "sloppy-stats-fetcher"
    return s


def get_all_commits(session) -> list:
    """Скачивает все коммиты из SOURCE_REPO (пагинация по 100)."""
    all_commits = []
    page = 1
    print("📋 Загружаю список коммитов из muk-as/DOTA2_CLIENT...")
    while True:
        url = (f"https://api.github.com/repos/{SOURCE_OWNER}/{SOURCE_REPO}"
               f"/commits?per_page=100&page={page}")
        r = session.get(url)
        if r.status_code == 403:
            # Rate limit — подождём
            reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(1, reset - int(time.time())) + 5
            print(f"   ⏳ Rate limit, жду {wait}s...")
            time.sleep(wait)
            continue
        if r.status_code != 200:
            print(f"   ⚠ GitHub вернул {r.status_code} на странице {page}, останавливаюсь.")
            break
        batch = r.json()
        if not batch:
            break
        for c in batch:
            dt_str = c["commit"]["committer"]["date"]
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            all_commits.append({
                "sha": c["sha"],
                "date": dt,
                "message": c["commit"]["message"][:80],
            })
        print(f"   страница {page}: {len(batch)} коммитов "
              f"({all_commits[-1]['date'].strftime('%Y-%m-%d')} ... "
              f"{all_commits[0]['date'].strftime('%Y-%m-%d')})")
        if len(batch) < 100:
            break
        page += 1
        time.sleep(0.3)
    print(f"   Итого: {len(all_commits)} коммитов\n")
    return all_commits  # newest first


PATCHNOTES_PATH = "game/dota/pak01_dir/resource/localization/patchnotes/patchnotes_english.txt"
# how many builds after the release day may still be the patch's own. Counted in builds, not days: the archive's
# commit dates are when it was archived (5713, out 2023-05-14 per GameTracking, sits there on 2023-05-24)
MAX_NOTES_LAG_BUILDS = 6


def has_patch_notes(text: bytes | None, version: str) -> bool:
    """В патчноутах сборки уже есть ключи DOTA_Patch_<version>_ — значит, это сборка самого патча."""
    return bool(text) and f'"DOTA_Patch_{version.replace(".", "_")}_'.encode() in text


def find_patch_build(session, commits: list, version: str, patch_date_str: str) -> dict | None:
    """Первая сборка не раньше даты патча, в которой уже есть его патчноуты (2026-10-21: правило «первый коммит
    в день выхода» брало сборку ДО патча у 14 патчей — 7.41 = 6726, сам патч — 6728). Не дальше
    MAX_NOTES_LAG_BUILDS сборок от первой в день выхода — тогда None."""
    day = datetime.strptime(patch_date_str, "%d.%m.%Y").replace(tzinfo=timezone.utc).date()
    after = [c for c in reversed(commits) if c["date"].date() >= day]      # oldest first
    for c in after[:MAX_NOTES_LAG_BUILDS + 1]:
        if has_patch_notes(download_raw(session, c["sha"], PATCHNOTES_PATH), version):
            return c
    return None


def find_commit_for_patch(commits: list, patch_date_str: str) -> dict | None:
    """
    Находит первый коммит на дату >= patch_date (самый ранний после релиза).
    commits отсортированы: новые → старые. Это может быть сборка ДО патча — main() берёт find_patch_build.
    """
    day = datetime.strptime(patch_date_str, "%d.%m.%Y").replace(tzinfo=timezone.utc)
    # Идём с конца (самые старые) и берём последний, который >= day
    candidate = None
    for c in reversed(commits):
        if c["date"].date() >= day.date():
            candidate = c
        else:
            break
    # Если не нашли таким способом — ищем первый коммит >= day
    if candidate is None:
        for c in reversed(commits):
            if c["date"].date() >= day.date():
                return c
    return candidate


def list_dir(session, sha: str, dir_path: str) -> list | None:
    """Возвращает список файлов в директории SOURCE_REPO на указанном SHA.
    Каждый элемент — dict с ключами name/path/sha/size. None при ошибке."""
    url = (f"https://api.github.com/repos/{SOURCE_OWNER}/{SOURCE_REPO}/"
           f"contents/{dir_path}?ref={sha}")
    for attempt in range(3):
        r = session.get(url)
        if r.status_code == 200:
            data = r.json()
            return data if isinstance(data, list) else None
        if r.status_code in (429, 403):
            wait = 30 * (attempt + 1)
            print(f"      ⏳ Rate limit ({r.status_code}), жду {wait}s...")
            time.sleep(wait)
        else:
            return None
    return None


def download_raw(session, sha: str, internal_path: str) -> bytes | None:
    """Скачивает файл из SOURCE_REPO по SHA коммита."""
    url = f"https://raw.githubusercontent.com/{SOURCE_OWNER}/{SOURCE_REPO}/{sha}/{internal_path}"
    for attempt in range(3):
        r = session.get(url)
        if r.status_code == 200:
            return r.content
        if r.status_code == 429 or r.status_code == 403:
            wait = 30 * (attempt + 1)
            print(f"      ⏳ Rate limit ({r.status_code}), жду {wait}s...")
            time.sleep(wait)
        else:
            return None
    return None


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Sloppy Stats Fetcher")
    print("=" * 60)

    session = make_session()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Кэшируем список коммитов локально
    commits_cache = OUT_DIR / "_commits.json"
    if commits_cache.exists():
        print("📦 Использую кэшированный список коммитов (_commits.json)")
        raw = json.loads(commits_cache.read_text(encoding="utf-8"))
        commits = [
            {"sha": c["sha"], "date": datetime.fromisoformat(c["date"]), "message": c["message"]}
            for c in raw
        ]
    else:
        commits = get_all_commits(session)
        commits_cache.write_text(
            json.dumps([{"sha": c["sha"], "date": c["date"].isoformat(), "message": c["message"]}
                        for c in commits], indent=2),
            encoding="utf-8"
        )
        print(f"   💾 Кэш сохранён в {commits_cache}\n")

    # Обрабатываем каждый патч
    total = len(RELEASE_HISTORY)
    skipped = 0
    fetched = 0

    for i, patch in enumerate(RELEASE_HISTORY):
        ver  = patch["version"]
        date = patch["date"]
        ver_dir = OUT_DIR / ver

        # Проверяем — уже есть?
        heroes_json = ver_dir / "heroes.json"
        items_json  = ver_dir / "items.json"
        heroes_dir  = ver_dir / "heroes"
        items_need_refresh = REFRESH_ITEMS_ONLY  # форсируем перезагрузку items.json
        # Скипаем целиком ТОЛЬКО если есть ВСЁ: slim JSON-ы + папка heroes/
        # с per-hero ability файлами. Без неё нужно дойти до шага скачивания.
        if (heroes_json.exists() and items_json.exists()
                and heroes_dir.exists() and any(heroes_dir.iterdir())
                and not items_need_refresh):
            print(f"[{i+1:2}/{total}] {ver}  ✓ уже есть")
            skipped += 1
            continue

        # Находим коммит
        commit = find_patch_build(session, commits, ver, date)
        if commit is None:
            print(f"[{i+1:2}/{total}] {ver}  ⚠ нет сборки с патчноутами {ver} в 2 днях от {date} — пропущен")
            continue

        print(f"[{i+1:2}/{total}] {ver}  →  {commit['date'].strftime('%Y-%m-%d')}  "
              f"{commit['sha'][:8]}  \"{commit['message'][:40]}\"")

        ver_dir.mkdir(parents=True, exist_ok=True)

        # Скачиваем и парсим npc_heroes.txt (только если нет, и не в refresh-items-only режиме)
        if not heroes_json.exists():
            print(f"         ↓ npc_heroes.txt...", end=" ", flush=True)
            raw_heroes = download_raw(session, commit["sha"], SOURCE_FILES["heroes"])
            if raw_heroes:
                text = _decode(raw_heroes)
                kv = parse_kv(text)
                heroes_data = extract_heroes(kv)
                heroes_json.write_text(json.dumps(heroes_data, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
                print(f"{len(heroes_data)} героев")
            else:
                print("ОШИБКА")

        # Скачиваем и парсим items.txt (если нет ИЛИ запрошен refresh-items)
        if not items_json.exists() or items_need_refresh:
            print(f"         ↓ items.txt...", end=" ", flush=True)
            raw_items = download_raw(session, commit["sha"], SOURCE_FILES["items"])
            if raw_items:
                text = _decode(raw_items)
                kv = parse_kv(text)
                items_data = extract_items(kv)
                items_json.write_text(json.dumps(items_data, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
                print(f"{len(items_data)} предметов")
            else:
                print("ОШИБКА")

        # npc_units.txt (slim JSON)
        units_json = ver_dir / "units.json"
        if not units_json.exists():
            print(f"         ↓ npc_units.txt...", end=" ", flush=True)
            raw = download_raw(session, commit["sha"], SOURCE_FILES["units"])
            if raw:
                data = extract_units(parse_kv(_decode(raw)))
                units_json.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
                print(f"{len(data)} юнитов")
            else:
                print("ОШИБКА")

        # npc_abilities.txt (slim JSON)
        abilities_json = ver_dir / "abilities.json"
        if not abilities_json.exists():
            print(f"         ↓ npc_abilities.txt...", end=" ", flush=True)
            raw = download_raw(session, commit["sha"], SOURCE_FILES["abilities"])
            if raw:
                data = extract_abilities(parse_kv(_decode(raw)))
                abilities_json.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
                print(f"{len(data)} способностей")
            else:
                print("ОШИБКА")

        # npc_ability_ids.txt (id → slug)
        ability_ids_json = ver_dir / "ability_ids.json"
        if not ability_ids_json.exists():
            print(f"         ↓ npc_ability_ids.txt...", end=" ", flush=True)
            raw = download_raw(session, commit["sha"], SOURCE_FILES["ability_ids"])
            if raw:
                data = extract_ability_ids(parse_kv(_decode(raw)))
                ability_ids_json.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
                print(f"{len(data)} id")
            else:
                print("ОШИБКА")

        # Per-hero ability files (npc_dota_hero_<name>.txt). Сырыми, чтобы
        # сохранить все поля (включая AbilityBehavior для скрытых абилок типа
        # Monkey King Transfiguration). Папка наполняется один раз — если
        # heroes/ уже есть, шаг пропускается.
        heroes_dir = ver_dir / "heroes"
        if not heroes_dir.exists():
            print(f"         ↓ heroes/ ...", end=" ", flush=True)
            listing = list_dir(session, commit["sha"], HEROES_DIR_PATH)
            if listing is None:
                print("ОШИБКА (не получили список папки)")
            else:
                heroes_dir.mkdir(parents=True, exist_ok=True)
                ok = 0
                for entry in listing:
                    name = entry.get("name", "")
                    if (not name.startswith("npc_dota_hero_")
                            or not name.endswith(".txt")):
                        continue
                    raw = download_raw(session, commit["sha"],
                                       f"{HEROES_DIR_PATH}/{name}")
                    if raw:
                        (heroes_dir / name).write_bytes(raw)
                        ok += 1
                    time.sleep(0.1)  # быть вежливее к raw.githubusercontent
                print(f"{ok} hero-файлов")

        fetched += 1
        time.sleep(0.5)  # Вежливая пауза между патчами

    print(f"\n{'='*60}")
    print(f"  Готово: {fetched} скачано, {skipped} уже были")
    print(f"  Файлы в: {OUT_DIR}")
    print(f"\n  Следующий шаг: запусти upload_stats.py чтобы залить в GitHub")
    print("=" * 60)
    input("\nНажми Enter чтобы закрыть окно...")


def _decode(data: bytes) -> str:
    if data.startswith(b"\xff\xfe"):
        return data[2:].decode("utf-16-le", errors="replace")
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8", errors="replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nОтменено.")
        sys.exit(1)
