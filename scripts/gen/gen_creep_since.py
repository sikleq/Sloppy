"""gen_creep_since.py — the first patch each neutral creep is in the game files (data/rules/creep_since.json).

Walks the patch-tagged store of game files (DOTA_FILES_DIR, git tags 7.08 … now, builds.json order) and notes, for
every npc_dota_neutral_* unit of the newest npc_units.txt, the first tag whose npc_units.txt defines it. A unit already
in the first tag (7.08) is left out: the store does not reach back to when it came. Neutral Stats shows it in the camp
cell's hover (owner 2026-11-19: "когда был введен/удален").

Run after a new patch lands in the store:
    python scripts/gen/gen_creep_since.py
"""
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "rules" / "creep_since.json"
UNITS = "files/scripts/npc/npc_units.txt"
UNIT_RE = re.compile(r'^\s*"(npc_dota_neutral_[a-z0-9_]+)"\s*$', re.M)


def _git(store, *args):
    return subprocess.run(["git", "-C", str(store), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", check=True).stdout


def main():
    store = Path(os.environ.get("DOTA_FILES_DIR", ""))
    if not (store / "builds.json").exists():
        raise SystemExit("DOTA_FILES_DIR does not point at the game-files store (no builds.json)")
    patches = list(json.loads((store / "builds.json").read_text(encoding="utf-8")))
    tags = set(_git(store, "tag").split())
    patches = [p for p in patches if p in tags]
    if len(patches) < 2:
        raise SystemExit("fewer than two patch tags in the store")
    seen, since = set(), {}
    for i, patch in enumerate(patches):
        try:
            units = set(UNIT_RE.findall(_git(store, "show", f"{patch}:{UNITS}")))
        except subprocess.CalledProcessError:
            continue
        for u in sorted(units - seen):
            if i > 0:
                since[u] = patch
        seen |= units
    if not since:
        raise SystemExit("no neutral creep came after the first patch: the walk found nothing")
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(dict(sorted(since.items())), indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, OUT)
    print(f"{len(since)} creeps with a first patch after {patches[0]} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
