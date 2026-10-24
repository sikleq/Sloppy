"""Full item data of any patch since 7.08 from local clones of two archives of the game's files:
- SteamTracking/GameTracking-Dota2 — extracted pak01 files 2016-12 … 2023-02-16 (7.08 … 7.32d);
- muk-as/DOTA2_CLIENT — 2023-03-22 … now (7.33 …; tools/fetch_stats.py reads the same archive, but keeps only a few
  item fields in data/stats/<v>/items.json).
Both keep every plain-text file of pak01 (KV, shops, localization); only compiled assets are missing.

For each requested patch it finds the patch's own build — the first commit on or after the release day that already
has the patch's notes (patchnotes_english.txt keys DOTA_Patch_<v>_ since 7.19, scripts/patchnotes/patch_<v>.txt
before) — reads items.txt, neutral_items.txt and shops.txt there and prints what changed for the item against the
previous patch of RELEASE_HISTORY: every KV field (old -> new) and the shop categories.
7.32e falls between the archives' dates, but DOTA2_CLIENT archived older builds on its first day (5480…5630 on
2023-03-22), so the notes rule finds it there (5630). Commit dates are archiving dates, not build dates.
Patches whose notes never shipped in the game (7.20, 7.20b, 7.23, 7.28) take the first items.txt change of the
release day and are marked so.

usage: python tools/item_history.py <item_name> <version> [<version> ...] [--show]
       item_name: internal name (item_skadi) or a substring of it; --show also prints the item's full block.
Clones: env DOTA2_CLIENT_DIR (default C:\\Program Files\\GitHub\\DOTA2_CLIENT) and GAMETRACKING_DIR (default
C:\\Users\\sikle\\dota2-ida-researcher\\state\\gt-dota2; a partial clone fetches file contents on first read).
The remote-tracking branch is read, so `git fetch` in a clone is enough to update it.
Builds found per version are cached in .cache/item_history/builds.json.
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

from tools.fetch_stats import PATCHNOTES_PATH, parse_kv  # noqa: E402

NPC_DIRS = ("game/dota/pak01_dir/scripts/npc/", "game/dota/scripts/npc/")
ITEMS = NPC_DIRS[0] + "items.txt"
NEUTRALS = NPC_DIRS[0] + "neutral_items.txt"
SHOPS = "game/dota/pak01_dir/scripts/shops.txt"
OLD_NOTES_DIR = "game/dota/pak01_dir/scripts/patchnotes"          # patch_708.txt … until 7.18
NOTES_PATHS = (PATCHNOTES_PATH,                                    # since 7.19
               "game/dota/panorama/localization/patchnotes/patchnotes_english.txt")   # 2018: 7.08 … 7.18
MAX_GAP_DAYS = 30          # a build further than this from the release day is not that patch's (archive gaps)
NOTES_FALLBACK_DAYS = 2    # patches whose notes never shipped in the game: first items.txt change this close
HOTFIX_HOURS = 12          # builds this soon after the patch's first build are its release-night fixes
CACHE = ROOT / ".cache" / "item_history" / "builds.json"
ARCHIVES = [   # newest first: the first archive whose history starts on or before the release day is used
    ("DOTA2_CLIENT", Path(os.environ.get("DOTA2_CLIENT_DIR", r"C:\Program Files\GitHub\DOTA2_CLIENT"))),
    ("GameTracking", Path(os.environ.get("GAMETRACKING_DIR",
                                         r"C:\Users\sikle\dota2-ida-researcher\state\gt-dota2"))),
]
_SHOP_SECTION = re.compile(r'^\s*"([^"]+)"\s*$')
_SHOP_ITEM = re.compile(r'^\s*"item"\s+"([^"]+)"')


def _git(clone: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(clone), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:300]}")
    return r.stdout


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


def old_notes_file(version: str) -> str:
    """7.08 -> .../patch_708.txt, 7.13b -> .../patch_713b.txt (patch-notes files before 7.19)."""
    return f"{OLD_NOTES_DIR}/patch_{version.replace('.', '')}.txt"


def pick_archive(day, starts: list) -> tuple[int, bool]:
    """Index of the archive for a release day and whether it starts after that day (gap between archives).
    starts: first build date of each archive, newest archive first."""
    for i, start in enumerate(starts):
        if start <= day:
            return i, False
    return len(starts) - 1, True


class Clone:
    def __init__(self, name: str, path: Path):
        self.name, self.path = name, path
        self.ref = _git(path, "rev-parse", "--abbrev-ref", "@{upstream}").strip() or "HEAD"
        self.commits = self._log(ITEMS, *NOTES_PATHS, OLD_NOTES_DIR)          # oldest first
        self.item_commits = self._log(ITEMS)

    def _log(self, *paths: str) -> list:
        rows = _git(self.path, "log", self.ref, "--format=%H %cI", "--", *paths)
        return [(sha, datetime.fromisoformat(d).astimezone(timezone.utc)) for sha, d in
                (r.split(" ", 1) for r in reversed(rows.splitlines()) if r.strip())]

    def file(self, sha: str, path: str) -> str | None:
        try:
            return _git(self.path, "show", f"{sha}:{path}")
        except RuntimeError:
            return None

    def npc(self, sha: str, name: str) -> str | None:
        """scripts/npc/<name>: pak01_dir/ in most builds; npc_heroes / npc_units / npc_abilities sat in
        game/dota/scripts/npc/ until about 2022 in GameTracking."""
        for d in NPC_DIRS:
            text = self.file(sha, d + name)
            if text is not None:
                return text
        return None

    def has_notes(self, sha: str, version: str) -> bool:
        key = f'"DOTA_Patch_{version.replace(".", "_")}_'
        for path in NOTES_PATHS:
            notes = self.file(sha, path)
            if notes and key in notes:
                return True
        return self.file(sha, old_notes_file(version)) is not None

    def _after_hotfixes(self, builds: list, first, next_version) -> str:
        """The last build within HOTFIX_HOURS of the patch's first build: release-night fixes bring the values to
        what the notes say (7.27 Veil of Discord cooldown 20 in 4313, 25 in 4316 three hours later; 7.31 Radiance)."""
        sha = builds[0][0]
        for s, d in builds[1:]:
            if (d - first).total_seconds() > HOTFIX_HOURS * 3600:
                break
            if next_version and self.has_notes(s, next_version):
                break
            sha = s
        return sha

    def find_build(self, version: str, day, until=None, next_version=None) -> tuple[str, str] | None:
        """(sha, how). how = "notes": the first build that has this patch's notes and not yet the next patch's;
        "date": the patch's notes never shipped in the game in time (7.20, 7.23, 7.28 — website only), so the first
        items.txt change within NOTES_FALLBACK_DAYS of the release day and before the next patch's day.
        Commit dates are archiving dates, not build dates (DOTA2_CLIENT archived builds 5480…5630 of 12.2022–03.2023
        on 2023-03-22), so the notes rule does not rely on them beyond a lower bound."""
        # a build may be dated the evening before in UTC (7.41a: 6743, 2026-03-27 22:20 UTC)
        after = [(sha, d) for sha, d in self.commits if -1 <= (d.date() - day).days <= MAX_GAP_DAYS]
        for n, (sha, d) in enumerate(after):
            if self.has_notes(sha, version):
                if next_version and self.has_notes(sha, next_version):
                    break                       # already the next patch's build: this one has none of its own
                return self._after_hotfixes(after[n:], d, next_version), "notes"
        return next(((sha, "date") for sha, d in self.item_commits
                     if 0 <= (d.date() - day).days <= NOTES_FALLBACK_DAYS and (until is None or d.date() < until)),
                    None)


class Archive:
    def __init__(self):
        from patch.meta import RELEASE_HISTORY
        self.history = RELEASE_HISTORY
        self.dates = {p["version"]: datetime.strptime(p["date"], "%d.%m.%Y").date() for p in RELEASE_HISTORY}
        self._clones: list[Clone] | None = None
        self._builds = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
        self._kv: dict[str, dict] = {}

    def clones(self) -> list[Clone]:
        if self._clones is None:
            self._clones = [Clone(n, p) for n, p in ARCHIVES]
        return self._clones

    def build(self, version: str) -> dict | None:
        """{"archive", "sha", "how", "late"} or None. The archive covering the release day first; a patch inside
        a gap between archives (7.32e) takes the next archive's first build, marked "late"."""
        if version not in self._builds:
            clones = self.clones()
            day = self.dates[version]
            names = [p["version"] for p in self.history]
            k = names.index(version)
            nxt = names[k - 1] if k > 0 else None
            until = self.dates[nxt] if nxt else None
            i, late = pick_archive(day, [c.commits[0][1].date() for c in clones])
            order = [i] + [j for j in range(len(clones)) if j != i]
            self._builds[version] = None
            for j in order:
                found = clones[j].find_build(version, day, until, nxt)
                if found:
                    self._builds[version] = {"archive": clones[j].name, "sha": found[0], "how": found[1],
                                             "late": late or j != i}
                    break
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_text(json.dumps(self._builds, indent=1), encoding="utf-8")
        return self._builds[version]

    def clone(self, name: str) -> Clone:
        return next(c for c in self.clones() if c.name == name)

    def items(self, b: dict) -> dict:
        if b["sha"] not in self._kv:
            c = self.clone(b["archive"])
            merged = {}
            for name in ("items.txt", "neutral_items.txt"):
                text = c.npc(b["sha"], name)
                if text:
                    for root in parse_kv(text).values():
                        merged.update({k: v for k, v in root.items() if isinstance(v, dict)})
            self._kv[b["sha"]] = {"kv": merged, "shops": shop_sections(c.file(b["sha"], SHOPS) or "")}
        return self._kv[b["sha"]]

    def resolve(self, b: dict, name: str) -> list[str]:
        kv = self.items(b)["kv"]
        return [name] if name in kv else sorted(k for k in kv if name in k)


def _label(b: dict | None) -> str:
    if not b:
        return "-"
    note = (" — patch notes not in the game, first build of the release day" if b.get("how") == "date" else "") + \
           (" — from the other archive" if b["late"] else "")
    return f"{b['archive']} {b['sha'][:9]}{note}"


def report(arch: Archive, name: str, version: str, show: bool) -> list[str]:
    prev = previous_version(version, arch.history)
    b, pb = arch.build(version), arch.build(prev) if prev else None
    if not b:
        return [f"## {version}: no build with this patch's notes in the archives"]
    out = []
    for item in arch.resolve(b, name) or [name]:
        new = arch.items(b)
        old = arch.items(pb) if pb else {"kv": {}, "shops": {}}
        a, n = flatten(old["kv"].get(item, {})), flatten(new["kv"].get(item, {}))
        out.append(f"## {version} {item}  ({_label(b)}; previous {prev}: {_label(pb)})")
        rows = diff(a, n) if pb else ["(previous patch has no build in the archives)"]
        sa, sb = old["shops"].get(item, []), new["shops"].get(item, [])
        if pb and sa != sb:
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
    for name, path in ARCHIVES:
        if not (path / ".git").exists():
            print(f"no {name} clone at {path}", file=sys.stderr)
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
