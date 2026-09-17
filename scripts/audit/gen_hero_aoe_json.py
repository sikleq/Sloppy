from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "builders"))

from builders.aoe_increase import (  # noqa: E402
    _find_aoe_radii,
    _load_hero_kits,
    _strip_backslash_lines,
)
from builders.heroes_stats import (  # noqa: E402
    STATS_DIR,
    _EXCLUDE,
    _display_name,
    _load_display_names,
)
from builders.mana_items import parse_kv  # noqa: E402


def build(version: str) -> list[dict]:
    hero_dir = STATS_DIR / version / "heroes"
    display_names = _load_display_names()
    kits = _load_hero_kits(version)
    out: list[dict] = []

    for path in sorted(hero_dir.glob("npc_dota_hero_*.txt")):
        if path.name == "npc_dota_hero_base.txt": continue   # parent template (7.41f+), not a hero
        hero_id = path.stem
        if hero_id in _EXCLUDE:
            continue
        hero_slug = hero_id.replace("npc_dota_hero_", "")
        text = _strip_backslash_lines(path.read_text(encoding="utf-8", errors="replace"))
        try:
            root = parse_kv(text).get("DOTAAbilities", {})
        except Exception:
            continue

        abilities: list[dict] = []
        current_kit = kits.get(hero_slug, set())
        for ability_slug, block in root.items():
            if ability_slug == "Version" or not isinstance(block, dict):
                continue
            if ability_slug.startswith("special_bonus_"):
                continue
            radii = _find_aoe_radii(block, ability_slug)
            if not radii:
                continue
            abilities.append(
                {
                    "ability_slug": ability_slug,
                    "in_current_kit": ability_slug in current_kit,
                    "aoe_rows": radii,
                }
            )

        if not abilities:
            continue

        out.append(
            {
                "hero_slug": hero_slug,
                "hero_name": _display_name(hero_id, display_names),
                "source_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "abilities": abilities,
            }
        )

    out.sort(key=lambda row: row["hero_name"].lower())
    return out


def main() -> None:
    version = sys.argv[1] if len(sys.argv) > 1 else "7.41d"
    payload = {
        "version": version,
        "heroes": build(version),
    }
    out_path = ROOT / "data" / f"hero_aoe_audit_{version}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
