"""Each facet's colour and icon by patch, from the game's own npc_heroes.txt (data/rules/facet_history.json).

The registry patch/badges.FACETS has one colour for all patches, but the game changes them: Batrider's Arsonist is Red in 7.36-7.38c and
Yellow from 7.39. The pages draw a facet as its own patch had it, from this file, so a build needs no game files.

    python scripts/gen/gen_facet_history.py          # rewrite the file
    python scripts/gen/gen_facet_history.py --check  # exit 1 when it is out of date
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "data", "rules", "facet_history.json")


def build():
    """{facet slug: [[first patch, colour, icon], ...]}: a new entry only where the look changes."""
    from patch import game_files
    from patch.ability_kv import parse_kv
    from patch.meta import RELEASE_HISTORY
    have = set(game_files.versions())
    runs = {}
    for version in reversed([p["version"] for p in RELEASE_HISTORY]):
        if version not in have:
            continue
        text = game_files.npc(version, "npc_heroes.txt")
        if not text or '"Facets"' not in text:
            continue
        for root in parse_kv(text).values():
            if not isinstance(root, dict):
                continue
            for key, hero in root.items():
                if not key.startswith("npc_dota_hero_") or not isinstance(hero, dict):
                    continue
                for slug, facet in (hero.get("Facets") or {}).items():
                    if not isinstance(facet, dict) or facet.get("Deprecated"):
                        continue
                    colour = f"{facet.get('Color', 'Gray')}{facet.get('GradientID', '0')}"
                    icon = facet.get("Icon", "")
                    seen = runs.setdefault(slug, [])
                    if not seen or seen[-1][1:] != [colour, icon]:
                        seen.append([version, colour, icon])
    return dict(sorted(runs.items()))


def main():
    fresh = json.dumps(build(), ensure_ascii=False, indent=0)
    if "--check" in sys.argv:
        with open(OUT, encoding="utf-8") as f:
            same = f.read().strip() == fresh.strip()
        print("up to date" if same else "OUT OF DATE")
        return 0 if same else 1
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(fresh + "\n")
    print(f"{OUT}: {fresh.count(chr(91) + chr(10))} facets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
