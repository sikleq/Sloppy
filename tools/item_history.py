"""Full item data of any patch from a local clone of muk-as/DOTA2_CLIENT (the same archive tools/fetch_stats.py
reads, which keeps only a few item fields in data/stats/<v>/items.json).

For each requested patch it finds the patch's own build (first commit on or after the release day whose
patchnotes already have DOTA_Patch_<version>_ keys, as in fetch_stats.find_patch_build), reads items.txt,
neutral_items.txt and shops.txt at that commit, and prints what changed for the item against the previous patch
of RELEASE_HISTORY: every KV field (old -> new) and the shop categories.

The archive's history of these files starts 2023-03 (7.33); older patches print "no build".

usage: python tools/item_history.py <item_name> <version> [<version> ...] [--show]
       item_name: internal name (item_skadi) or a substring of it; --show also prints the item's full block.
Clone path: env DOTA2_CLIENT_DIR, default C:\\Program Files\\GitHub\\DOTA2_CLIENT.
Commits found per version are cached in .cache/item_history/builds.json.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.fetch_stats import MAX_NOTES_LAG_BUILDS, PATCHNOTES_PATH, parse_kv  # noqa: E402

CLONE = Path(os.environ.get("DOTA2_CLIENT_DIR", r"C:\Program Files\GitHub\DOTA2_CLIENT"))
ITEMS = "game/dota/pak01_dir/scripts/npc/items.txt"
NEUTRALS = "game/dota/pak01_dir/scripts/npc/neutral_items.txt"
SHOPS = "game/dota/pak01_dir/scripts/shops.txt"
CACHE = ROOT / ".cache" / "item_history" / "builds.json"
_SHOP_SECTION = re.compile(r'^\s*"([^"]+)"\s*$')
_SHOP_ITEM = re.compile(r'^\s*"item"\s+"([^"]+)"')


def _git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(CLONE), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:300]}")
    return r.stdout


def file_at(sha: str, path: str) -> str | None:
    try:
        return _git("show", f"{sha}:{path}")
    except RuntimeError:
        return None


def flatten(node, prefix: str = "") -> dict:
    """Nested KV dict -> {"AbilityValues.bonus_mana.value": "150", ...}."""
    out = {}
    for k, v in node.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


def diff(old: dict, new: dict) -> list[str]:
    """Changed, added and removed fields of two flattened blocks, sorted by field name."""
    rows = []
    for k in sorted(set(old) | set(new)):
        a, b = old.get(k), new.get(k)
        if a != b:
            rows.append(f"{k}: {a!r} -> {b!r}")
    return rows


def shop_sections(text: str) -> dict[str, list[str]]:
    """shops.txt -> {item: [sections]}. parse_kv keeps only the last of repeated "item" keys, so read it by lines."""
    out: dict[str, list[str]] = {}
    section = None
    for line in text.splitlines():
        line = line.split("//")[0]
        m = _SHOP_ITEM.match(line)
        if m and section:
            out.setdefault(m.group(1), []).append(section)
            continue
        m = _SHOP_SECTION.match(line)
        if m and m.group(1) != "dota_shops":
            section = m.group(1)
    return out


def previous_version(version: str, history: list[dict]) -> str | None:
    """history is newest-first (patch.meta.RELEASE_HISTORY)."""
    names = [p["version"] for p in history]
    i = names.index(version)
    return names[i + 1] if i + 1 < len(names) else None


def _commits() -> list[tuple[str, datetime]]:
    rows = _git("log", "--format=%H %cI", "--", ITEMS, PATCHNOTES_PATH).split("\n")
    out = [(sha, datetime.fromisoformat(d).astimezone(timezone.utc)) for sha, d in
           (r.split(" ", 1) for r in rows if r.strip())]
    return list(reversed(out))                                      # oldest first


def find_build(version: str, date_str: str, commits: list) -> str | None:
    day = datetime.strptime(date_str, "%d.%m.%Y").date()
    key = f'"DOTA_Patch_{version.replace(".", "_")}_'
    after = [sha for sha, d in commits if d.date() >= day]
    for sha in after[:MAX_NOTES_LAG_BUILDS + 1]:
        notes = file_at(sha, PATCHNOTES_PATH)
        if notes and key in notes:
            return sha
    return None


class Archive:
    def __init__(self):
        from patch.meta import RELEASE_HISTORY
        self.history = RELEASE_HISTORY
        self.dates = {p["version"]: p["date"] for p in RELEASE_HISTORY}
        self._commits = None
        self._builds = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
        self._kv: dict[str, dict] = {}

    def build(self, version: str) -> str | None:
        if version not in self._builds:
            if self._commits is None:
                self._commits = _commits()
            self._builds[version] = find_build(version, self.dates[version], self._commits)
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_text(json.dumps(self._builds, indent=1), encoding="utf-8")
        return self._builds[version]

    def items(self, sha: str) -> dict:
        if sha not in self._kv:
            merged = {}
            for path in (ITEMS, NEUTRALS):
                text = file_at(sha, path)
                if text:
                    for root in parse_kv(text).values():
                        merged.update({k: v for k, v in root.items() if isinstance(v, dict)})
            text = file_at(sha, SHOPS) or ""
            self._kv[sha] = {"kv": merged, "shops": shop_sections(text)}
        return self._kv[sha]

    def resolve(self, sha: str, name: str) -> list[str]:
        kv = self.items(sha)["kv"]
        return [name] if name in kv else sorted(k for k in kv if name in k)


def report(arch: Archive, name: str, version: str, show: bool) -> list[str]:
    prev = previous_version(version, arch.history)
    sha, psha = arch.build(version), arch.build(prev) if prev else None
    if not sha:
        return [f"## {version}: no build in the archive"]
    out = []
    for item in arch.resolve(sha, name) or [name]:
        new = arch.items(sha)
        old = arch.items(psha) if psha else {"kv": {}, "shops": {}}
        a, b = flatten(old["kv"].get(item, {})), flatten(new["kv"].get(item, {}))
        out.append(f"## {version} {item}  (build {sha[:9]}, previous {prev} {psha[:9] if psha else '-'})")
        rows = diff(a, b) if psha else ["(previous patch has no build in the archive)"]
        sa, sb = old["shops"].get(item, []), new["shops"].get(item, [])
        if sa != sb:
            rows.append(f"shop: {sa} -> {sb}")
        out += rows or ["(no change)"]
        out.append(f"shop now: {sb or '-'}")
        if show:
            out += [f"  {k} = {v}" for k, v in b.items()]
    return out


def main(argv: list[str]) -> int:
    show = "--show" in argv
    args = [a for a in argv if a != "--show"]
    if len(args) < 2:
        print(__doc__)
        return 2
    if not (CLONE / ".git").exists():
        print(f"no clone at {CLONE} (set DOTA2_CLIENT_DIR)", file=sys.stderr)
        return 2
    arch = Archive()
    for v in args[1:]:
        if v not in arch.dates:
            print(f"## {v}: unknown version")
            continue
        print("\n".join(report(arch, args[0], v, show)))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
