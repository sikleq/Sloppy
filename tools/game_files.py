"""Our store of the game's plain-text files: one commit per patch, tagged with the version (private repo
dota-patch-files, local clone at env DOTA_FILES_DIR, default C:\\Users\\sikle\\dota-patch-files). Each patch = its own
build (first build with the patch's notes and without the next patch's, plus release-night fixes; the store's
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


def path(version: str, rel: str) -> str | None:
    """A file path for tools that open files: files/<rel> of a patch copied once to .cache/game_files/<version>/,
    or None when the patch or file is not in the store."""
    dst = CACHE / version / rel
    if dst.exists():
        return str(dst)
    if version not in versions():
        return None
    data = read_bytes(version, rel)
    if data is None:
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    return str(dst)


def npc(version: str, name: str) -> str | None:
    """scripts/npc/<name> of a patch (items.txt, npc_heroes.txt, npc_units.txt, npc_abilities.txt, …)."""
    return read(version, "scripts/npc/" + name)
