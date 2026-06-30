"""fetch_npc_history.py — качает исторические npc_units.txt из dotabuff/d2vpkr
и сохраняет компактные per-patch JSON `data/stats/<patch>/npc_units.json` с
полями нейтралов. Нужно для истории магрезиста (и прочих npc-only статов),
которой нет в units.json.

Источник: github.com/dotabuff/d2vpkr — там npc_units.txt автоматически
коммитится каждый патч с 2015 года. Коммиты помечены номером билда
("Client NNNN"), а не версией патча, поэтому сопоставление патч↔коммит идёт
ПО ДАТЕ: для каждого нашего патча берётся последний d2vpkr-коммит, попавший
в окно жизни патча (до даты следующего патча). Даты патчей — из
`data/site_meta.json` (patch_dates), который пишет builders/patch.py.

Мы сохраняем СВОЮ копию данных (распарсенный JSON), чтобы не зависеть от
d2vpkr в момент сборки. Сырые .txt кэшируются по SHA в `.cache/d2vpkr/`,
чтобы не качать один и тот же блоб дважды (соседние патчи часто делят коммит).

Запуск:
    python scripts/fetch/fetch_npc_history.py           # добить недостающие + обновить свежий
    python scripts/fetch/fetch_npc_history.py --force    # перекачать все патчи

После выхода нового патча: создай `data/stats/<patch>/` (с units.json от
build-пайплайна) и запусти скрипт — он добьёт npc_units.json для новинки.
"""
import json
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
STATS_DIR = ROOT / "data" / "stats"
META_PATH = ROOT / "data" / "site_meta.json"
CACHE_DIR = ROOT / ".cache" / "d2vpkr"

REPO = "dotabuff/d2vpkr"
FILE_PATH = "dota/scripts/npc/npc_units.txt"
RAW_TMPL = "https://raw.githubusercontent.com/" + REPO + "/{sha}/" + FILE_PATH

# Поля, которые вынимаем из каждого npc-блока (надмножество того, что
# использует builders/creeps.py — храним с запасом, чтобы потом можно было
# завести историю и по другим статам без повторной перекачки).
NPC_FIELDS = (
    "StatusHealth", "StatusHealthRegen", "StatusMana", "StatusManaRegen",
    "ArmorPhysical", "MagicalResistance", "AttackDamageMin", "AttackDamageMax",
    "AttackRate", "BaseAttackSpeed", "AttackRange", "AttackCapabilities",
    "AttackAcquisitionRange", "MovementSpeed", "BountyGoldMin", "BountyGoldMax",
    "BountyXP", "VisionDaytimeRange", "VisionNighttimeRange",
    "CombatClassAttack", "CombatClassDefend", "AttackCapabilities",
    "AttackAnimationPoint", "MovementTurnRate", "ProjectileSpeed",
    "BoundsHullName", "RingRadius",
    "Ability1", "Ability2", "Ability3", "Ability4", "Ability5",
)
HEAD_RE = re.compile(
    r'^\s*"(npc_dota_(?:neutral_[a-z0-9_]+'
    r'|dark_troll_warlord_skeleton_warrior))"\s*$'
)
FIELD_RE = re.compile(r'^\s*"([A-Za-z_][A-Za-z0-9_]*)"\s+"([^"]+)"')


def parse_npc_units(text):
    """Распарсить npc_units.txt → {npc_key: {field: value}} для нейтралов
    и surfaced summoned-юнитов. Зеркалит парсер из builders/creeps.py."""
    lines = text.splitlines()
    n = len(lines)
    out = {}
    i = 0
    while i < n:
        m = HEAD_RE.match(lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        j = i + 1
        while j < n and "{" not in lines[j]:
            j += 1
        if j >= n:
            break
        depth = lines[j].count("{") - lines[j].count("}")
        j += 1
        entry = {}
        while j < n and depth > 0:
            line = lines[j]
            if depth == 1:
                fm = FIELD_RE.match(line)
                if fm and fm.group(1) in NPC_FIELDS:
                    entry[fm.group(1)] = fm.group(2)
            depth += line.count("{") - line.count("}")
            j += 1
        out[name] = entry
        i = j
    return out


def load_patch_dates():
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    raw = meta.get("patch_dates", {})
    out = {}
    for ver, ds in raw.items():
        try:
            d, mth, y = (int(x) for x in ds.split("."))
            out[ver] = date(y, mth, d)
        except (ValueError, AttributeError):
            continue
    return out


def _fetch_page(page):
    """Одна страница (до 100 коммитов) для FILE_PATH. Сначала пробуем
    авторизованный `gh api` (5000/час), иначе публичный API (60/час)."""
    api = "repos/{}/commits?path={}&per_page=100&page={}".format(
        REPO, FILE_PATH, page)
    try:
        res = subprocess.run(
            ["gh", "api", api],
            capture_output=True, text=True, check=True,
        )
        return json.loads(res.stdout)
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    with urllib.request.urlopen("https://api.github.com/" + api) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_commit_index():
    """[(commit_date, sha), ...] по возрастанию даты для FILE_PATH."""
    data = []
    page = 1
    while True:
        chunk = _fetch_page(page)
        if not chunk:
            break
        data.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    idx = []
    for c in data:
        sha = c.get("sha")
        ds = c.get("commit", {}).get("author", {}).get("date", "")[:10]
        if not sha or not ds:
            continue
        y, mth, d = (int(x) for x in ds.split("-"))
        idx.append((date(y, mth, d), sha))
    idx.sort()
    return idx


def fetch_raw(sha):
    """Сырой npc_units.txt на коммите sha (с дисковым кэшем по sha)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / (sha + ".txt")
    if cached.exists():
        return cached.read_text(encoding="utf-8")
    with urllib.request.urlopen(RAW_TMPL.format(sha=sha)) as r:
        text = r.read().decode("utf-8")
    cached.write_text(text, encoding="utf-8")
    return text


def commit_for_window(commit_idx, win_end):
    """Последний коммит строго раньше win_end (даты следующего патча).
    Это состояние файла, актуальное в течение жизни патча."""
    chosen = None
    for cdate, sha in commit_idx:
        if cdate < win_end:
            chosen = sha
        else:
            break
    return chosen


def main():
    force = "--force" in sys.argv
    if not META_PATH.exists():
        print("X data/site_meta.json не найден — сначала запусти builders/patch.py")
        return 1
    patch_dates = load_patch_dates()
    # Только патчи, для которых у нас есть папка в data/stats/.
    patches = sorted(
        (v for v in patch_dates if (STATS_DIR / v).is_dir()),
        key=lambda v: patch_dates[v],
    )
    if not patches:
        print("X нет папок data/stats/<patch>/ — нечего заполнять")
        return 1
    print("Индексирую коммиты d2vpkr…")
    commit_idx = fetch_commit_index()
    if not commit_idx:
        print("X не удалось получить список коммитов d2vpkr")
        return 1
    print("  {} коммитов, {}—{}".format(
        len(commit_idx), commit_idx[0][0], commit_idx[-1][0]))

    far_future = date(9999, 1, 1)
    written = skipped = missing = 0
    latest = patches[-1]
    for i, ver in enumerate(patches):
        out_path = STATS_DIR / ver / "npc_units.json"
        # Свежий патч всегда обновляем (в нём данные ещё могут доезжать).
        if out_path.exists() and not force and ver != latest:
            skipped += 1
            continue
        win_end = patch_dates[patches[i + 1]] if i + 1 < len(patches) else far_future
        sha = commit_for_window(commit_idx, win_end)
        if not sha:
            print("  - {}: нет коммита до {}".format(ver, win_end))
            missing += 1
            continue
        try:
            parsed = parse_npc_units(fetch_raw(sha))
        except Exception as e:  # noqa: BLE001 — сетевой/парсинг, продолжаем
            print("  ! {}: ошибка {}".format(ver, e))
            missing += 1
            continue
        out_path.write_text(
            json.dumps(parsed, ensure_ascii=False, indent=0,
                       separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )
        written += 1
        print("  + {} ← d2vpkr {} ({} юнитов)".format(ver, sha[:7], len(parsed)))
    print("Готово: записано {}, пропущено {}, без данных {}".format(
        written, skipped, missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
