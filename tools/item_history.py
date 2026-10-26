"""Full item data of any patch since 7.08 from our store of the game's plain-text files (private repo
dota-patch-files: one commit per patch, tagged with the version; how each patch's build is chosen — its
tools/builds.py). data/stats/<v>/items.json keeps only a few item fields; this reads the whole items.txt,
neutral_items.txt and shops.txt of the patch and prints what changed for an item against the previous patch of
RELEASE_HISTORY: every KV field (old -> new) and the shop categories.

usage: python tools/item_history.py <item_name> <version> [<version> ...] [--show]
       item_name: internal name (item_skadi) or a substring of it; --show also prints the item's full block.
Store: env DOTA_FILES_DIR, default ~/dota-patch-files.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import game_files  # noqa: E402
from tools.fetch_stats import parse_kv  # noqa: E402

STORE = game_files.STORE
store_file = game_files.read
_SHOP_SECTION = re.compile(r'^\s*"([^"]+)"\s*$')
_SHOP_ITEM = re.compile(r'^\s*"item"\s+"([^"]+)"')


def store_versions() -> set[str]:
    return set(game_files.versions())


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


class Patches:
    def __init__(self):
        from patch.meta import RELEASE_HISTORY
        self.history = RELEASE_HISTORY
        self.versions = store_versions()
        p = STORE / "builds.json"
        self.builds = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        self._kv: dict[str, dict] = {}

    def items(self, version: str) -> dict:
        if version not in self._kv:
            merged = {}
            for name in ("items.txt", "neutral_items.txt"):
                text = store_file(version, "scripts/npc/" + name)
                if text:
                    for root in parse_kv(text).values():
                        merged.update({k: v for k, v in root.items() if isinstance(v, dict)})
            self._kv[version] = {"kv": merged, "shops": shop_sections(store_file(version, "scripts/shops.txt") or "")}
        return self._kv[version]

    def label(self, version: str | None) -> str:
        b = self.builds.get(version or "")
        if not b:
            return "-"
        note = " — patch notes not in the game, first build of the release day" if b.get("how") == "date" else ""
        return f"{b['archive']} {b['sha'][:9]}{note}"


def report(pt: Patches, name: str, version: str, show: bool) -> list[str]:
    prev = previous_version(version, pt.history)
    if version not in pt.versions:
        return [f"## {version}: not in the store"]
    has_prev = prev in pt.versions
    new = pt.items(version)
    old = pt.items(prev) if has_prev else {"kv": {}, "shops": {}}
    names = [name] if name in new["kv"] else sorted(k for k in new["kv"] if name in k)
    out = []
    for item in names or [name]:
        a, n = flatten(old["kv"].get(item, {})), flatten(new["kv"].get(item, {}))
        out.append(f"## {version} {item}  ({pt.label(version)}; previous {prev}: {pt.label(prev)})")
        rows = diff(a, n) if has_prev else ["(previous patch is not in the store)"]
        sa, sb = old["shops"].get(item, []), new["shops"].get(item, [])
        if has_prev and sa != sb:
            rows.append(f"shop: {sa} -> {sb}")
        out += rows or ["(no change)"]
        out.append(f"shop now: {sb or '-'}")
        if show:
            out += [f"  {k} = {v}" for k, v in n.items()]
    return out


def main(argv: list[str]) -> int:
    show = "--show" in argv
    args = [a for a in argv if a != "--show"]
    if len(args) < 2:
        print(__doc__)
        return 2
    if not (STORE / ".git").exists():
        print(f"no store at {STORE} (set DOTA_FILES_DIR)", file=sys.stderr)
        return 2
    pt = Patches()
    for v in args[1:]:
        print("\n".join(report(pt, args[0], v, show)))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
