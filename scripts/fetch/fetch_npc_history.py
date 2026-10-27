"""fetch_npc_history.py — npc_units.txt каждого патча из нашего хранилища файлов игры (patch/game_files.py:
сборка самого патча) → компактные per-patch JSON `data/stats/<patch>/npc_units.json` с полями нейтралов.
Нужно для истории магрезиста (и прочих npc-only статов), которой нет в units.json.

До 2026-10-24 источником был dotabuff/d2vpkr («последний коммит до даты следующего патча» — состояние конца
патча, а не самого патча; сырые .txt лежали в `.cache/d2vpkr/`).

Запуск:
    python scripts/fetch/fetch_npc_history.py           # добить недостающие + обновить свежий
    python scripts/fetch/fetch_npc_history.py --force    # пересобрать все патчи

После выхода нового патча: добавь его в хранилище, создай `data/stats/<patch>/` и запусти скрипт.
"""
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from patch.meta import RELEASE_HISTORY  # noqa: E402
from patch import game_files  # noqa: E402

STATS_DIR = ROOT / "data" / "stats"

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


def main():
    force = "--force" in sys.argv
    if not game_files.available():
        print(f"X нет хранилища файлов игры: {game_files.STORE}")
        return 1
    patches = [p["version"] for p in reversed(RELEASE_HISTORY) if (STATS_DIR / p["version"]).is_dir()]
    if not patches:
        print("X нет папок data/stats/<patch>/ — нечего заполнять")
        return 1
    written = skipped = missing = 0
    latest = patches[-1]
    for ver in patches:
        out_path = STATS_DIR / ver / "npc_units.json"
        if out_path.exists() and not force and ver != latest:
            skipped += 1
            continue
        raw = game_files.npc(ver, "npc_units.txt")
        if raw is None or "#base" in raw[:4096]:
            print("  - {}: нет npc_units.txt в хранилище".format(ver))
            missing += 1
            continue
        parsed = parse_npc_units(raw)
        out_path.write_text(
            json.dumps(parsed, ensure_ascii=False, indent=0,
                       separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )
        written += 1
        print("  + {} ({} юнитов)".format(ver, len(parsed)))
    print("Готово: записано {}, пропущено {}, без данных {}".format(
        written, skipped, missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
