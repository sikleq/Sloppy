"""Our store of the game's plain-text files: one commit per patch, tagged with the version (private repo
dota-patch-files, local clone at env DOTA_FILES_DIR, default C:\\Users\\sikle\\dota-patch-files). Each patch = its own
build (first build with the patch's notes and without the next patch's, plus release-day fixes within 24 h; the store's
tools/builds.py). Paths are the game's below game/dota/[pak01_dir/]: scripts/npc/items.txt,
scripts/npc/heroes/npc_dota_hero_axe.txt, resource/localization/abilities_english.txt, scripts/shops.txt, …

Replaces the dotabuff/d2vpkr fetchers (which took "the last commit before the next patch" or "<= release + 4 days"
and so often held a neighbouring patch's state) and the GitHub archives read directly.
"""
import os
import subprocess
from functools import lru_cache
from pathlib import Path

STORE = Path(os.environ.get("DOTA_FILES_DIR", r"C:\Users\sikle\dota-patch-files"))


def available() -> bool:
    return (STORE / ".git").exists() and bool(versions())


@lru_cache(maxsize=1)
def versions() -> frozenset:
    """Versions in the store (its tags)."""
    r = subprocess.run(["git", "-C", str(STORE), "tag"], capture_output=True, text=True)
    return frozenset(r.stdout.split()) if r.returncode == 0 else frozenset()


def read_bytes(version: str, rel: str) -> bytes | None:
    r = subprocess.run(["git", "-C", str(STORE), "show", f"{version}:files/{rel}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


@lru_cache(maxsize=512)
def read(version: str, rel: str) -> str | None:
    """files/<rel> of a patch as text, or None (no such patch or file)."""
    data = read_bytes(version, rel)
    if data is None:
        return None
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", "replace")
    return data.decode("utf-8-sig", "replace")


def listing(version: str, rel_dir: str) -> list[str]:
    """Paths (relative to files/) under rel_dir in a patch."""
    r = subprocess.run(["git", "-C", str(STORE), "ls-tree", "-r", "--name-only", version, "--", f"files/{rel_dir}"],
                       capture_output=True, text=True, encoding="utf-8")
    return [p[len("files/"):] for p in r.stdout.splitlines()] if r.returncode == 0 else []


CACHE = Path(__file__).resolve().parent.parent / ".cache" / "game_files"


@lru_cache(maxsize=None)
def commit_of(version: str) -> str | None:
    """The store commit a version's tag points at (a rebuilt store retags every patch)."""
    r = subprocess.run(["git", "-C", str(STORE), "rev-parse", f"{version}^{{commit}}"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def path(version: str, rel: str) -> str | None:
    """A file path for tools that open files: files/<rel> of a patch copied once to
    .cache/game_files/<version>@<commit>/, or None when the patch or file is not in the store. Keyed by the commit too:
    after the store was rebuilt (2026-10-24, release-day window 12 -> 24 h) a folder per version served old files."""
    if version not in versions():
        return None
    dst = CACHE / f"{version}@{commit_of(version)[:12]}" / rel
    if dst.exists():
        return str(dst)
    data = read_bytes(version, rel)
    if data is None:
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    return str(dst)


def npc(version: str, name: str) -> str | None:
    """scripts/npc/<name> of a patch (items.txt, npc_heroes.txt, npc_units.txt, npc_abilities.txt, …)."""
    return read(version, "scripts/npc/" + name)


# ── the raw KV files builders read from data/stats/<v>/ (not in git since 2026-10-24: copied from the store) ──
STATS = Path(__file__).resolve().parent.parent / "data" / "stats"
RAW_TXT_SINCE = "7.41c"    # from here on data/stats/<v>/ also keeps the root KV files (slim_from_kv input)
RAW_TXT = ("items.txt", "npc_abilities.txt", "npc_ability_ids.txt", "npc_heroes.txt", "npc_units.txt")
HERO_BASE = "scripts/npc/heroes/npc_dota_hero_base.txt"


def _order() -> dict:
    from patch.meta import RELEASE_HISTORY
    return {p["version"]: i for i, p in enumerate(reversed(RELEASE_HISTORY))}      # oldest = 0


def missing_raw(version: str, stats: Path = STATS) -> list[str]:
    """The raw files of `version` the site build reads that are not laid out in data/stats/<version>/ — a clone
    without the store, or materialize not run yet. Static: the store is not asked."""
    d = stats / version
    missing = []
    if _order().get(version, -1) >= _order()[RAW_TXT_SINCE]:
        missing += [n for n in ("items.txt", "npc_abilities.txt", "npc_heroes.txt", "npc_units.txt")
                    if not (d / n).exists()]
    if not any((d / "heroes").glob("npc_dota_hero_*.txt")):
        missing.append("heroes/")
    return missing


NO_RAW_FILES = """The raw game files are not laid out in data/stats/{version}/ (missing: {missing}).
They come from the private game-files store (repo dota-patch-files), not from git:
  1. clone the store and point DOTA_FILES_DIR at it (now: {store})
  2. python tools/game_files.py materialize"""


def tree(version: str, rel_dir: str) -> dict[str, bytes]:
    """{path under files/: content} of everything under files/<rel_dir> of a patch — one `git archive` call."""
    import io
    import tarfile
    r = subprocess.run(["git", "-C", str(STORE), "archive", "--format=tar", version, "--", f"files/{rel_dir}"],
                       capture_output=True)
    if r.returncode != 0:
        return {}
    with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
        return {m.name[len("files/"):]: t.extractfile(m).read() for m in t.getmembers() if m.isfile()}


def raw_plan(version: str, files: dict[str, bytes] | None = None) -> dict[str, str]:
    """{path under data/stats/<version>/: path under the store's files/} — the raw files of one patch:
    heroes/npc_dota_hero_*.txt wherever the patch has per-hero files (7.34e+), the root KV files from RAW_TXT_SINCE,
    npc_dota_hero_base.txt where npc_heroes.txt is only an include list (7.41f+). `files`: the patch's scripts/npc
    tree (tree()), else the store is asked file by file."""
    get = (lambda rel: files.get(rel)) if files is not None else (lambda rel: read_bytes(version, rel))
    names = ([p for p in files if p.startswith("scripts/npc/heroes/")] if files is not None
             else listing(version, "scripts/npc/heroes"))
    plan = {}
    for rel in names:
        name = rel.rsplit("/", 1)[1]
        if name.startswith("npc_dota_hero_") and name.endswith(".txt") and rel != HERO_BASE:
            plan["heroes/" + name] = rel
    order = _order()
    if order.get(version, -1) >= order[RAW_TXT_SINCE]:
        plan.update({name: "scripts/npc/" + name for name in RAW_TXT if get("scripts/npc/" + name)})
        heroes_kv = files.get("scripts/npc/npc_heroes.txt", b"").decode("utf-8", "replace") if files is not None \
            else (read(version, "scripts/npc/npc_heroes.txt") or "")
        if "#base" in heroes_kv[:4096] and get(HERO_BASE):
            plan["npc_dota_hero_base.txt"] = HERO_BASE
    return plan


def materialize(only: list[str] | None = None) -> tuple[int, int]:
    """Write the raw files of every patch that has a data/stats/<v>/ folder (or of `only`) from the store, with LF
    line ends. Returns (written, unchanged)."""
    written = same = 0
    for v in sorted(versions()):
        if (only and v not in only) or not (STATS / v).is_dir():
            continue
        files = tree(v, "scripts/npc")
        for dst_rel, src_rel in raw_plan(v, files).items():
            data = files[src_rel].replace(b"\r\n", b"\n")
            dst = STATS / v / dst_rel
            if dst.exists() and dst.read_bytes() == data:
                same += 1
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            written += 1
    return written, same


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    if sys.argv[1:2] != ["materialize"]:
        print("usage: python tools/game_files.py materialize [<version> ...]   (env DOTA_FILES_DIR = the store)")
        sys.exit(2)
    if not available():
        print(f"no game-files store at {STORE} (set DOTA_FILES_DIR)", file=sys.stderr)
        sys.exit(1)
    w, s = materialize(sys.argv[2:] or None)
    print(f"raw game files: {w} written, {s} unchanged")
