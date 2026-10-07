"""The game's data files of a patch from SteamTracking/GameTracking-Dota2 — the BACKUP to extract_patchnotes.py (which
reads them from the local game) when that is not at hand (the owner 2026-10-07: "добавь в запасной источник"):

  data/patchnotes_english.txt, data/dota_english.txt, data/abilities_english.txt
  data/stats/<version>/{npc_heroes,npc_units,items,npc_abilities,npc_ability_ids}.txt
  data/stats/<version>/heroes/npc_dota_hero_<name>.txt          (what Silent Changes diffs)

the same files, the same places as extract_patchnotes.py writes (lists checked equal by tests/test_fetch_gametracking.py).
GameTracking dumps every game build (its commit subjects start with the build number, "6951 | 334 files | …") under
game/dota/pak01_dir/ since 2026-10-07; its text is byte-for-byte the game's, with LF line ends (data/stats is LF in
git anyway; the localization files in data/ get the game's CRLF back). Writes only files whose content changed, and
pushes nothing — commit as usual.

    python scripts/fetch/fetch_gametracking.py 7.42                 # the newest build
    python scripts/fetch/fetch_gametracking.py 7.42 --ref <sha>     # a given commit
    python scripts/fetch/fetch_gametracking.py 7.42 --dry-run       # only list what would change
"""
import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = "SteamTracking/GameTracking-Dota2"
BASE = "game/dota/pak01_dir/"
# the same lists as extract_patchnotes.py (PATCHNOTES_VPK_PATHS -> data/, STATS_VPK_PATHS -> data/stats/<v>/,
# HEROES_VPK_DIR -> data/stats/<v>/heroes/)
PATCHNOTES_VPK_PATHS = [
    "resource/localization/patchnotes/patchnotes_english.txt",
    "resource/localization/dota_english.txt",
    "resource/localization/abilities_english.txt",
]
STATS_VPK_PATHS = [
    "scripts/npc/npc_heroes.txt",
    "scripts/npc/npc_units.txt",
    "scripts/npc/items.txt",
    "scripts/npc/npc_abilities.txt",
    "scripts/npc/npc_ability_ids.txt",
]
HEROES_VPK_DIR = "scripts/npc/heroes/"


def _gh(api):
    out = subprocess.run(["gh", "api", api], capture_output=True, text=True, encoding="utf-8")
    if out.returncode:
        raise RuntimeError(f"gh api {api}: {out.stderr.strip()}")
    return json.loads(out.stdout)


def resolve(ref):
    """(full sha, build number, date) of a GameTracking commit (default: the newest)."""
    c = _gh(f"repos/{REPO}/commits/{ref or 'HEAD'}")
    subject = c["commit"]["message"].split("\n", 1)[0]
    build = subject.split(" |", 1)[0].strip() if " | " in subject else ""
    return c["sha"], build, c["commit"]["author"]["date"][:10]


def hero_files(sha):
    """The per-hero ability files of that commit (npc_dota_hero_base.txt — the 7.41f+ parent template — left out,
    as extract_patchnotes.py does)."""
    tree = _gh(f"repos/{REPO}/git/trees/{sha}:{BASE}{HEROES_VPK_DIR.rstrip('/')}")
    return sorted(f"{HEROES_VPK_DIR}{t['path']}" for t in tree["tree"]
                  if t["type"] == "blob" and t["path"].startswith("npc_dota_hero_") and t["path"].endswith(".txt")
                  and t["path"] != "npc_dota_hero_base.txt")


def download(sha, path):
    url = f"https://raw.githubusercontent.com/{REPO}/{sha}/{BASE}{path}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def crlf(data):
    """LF -> CRLF (the game's line ends), leaving existing CRLF alone."""
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def plan(version, sha):
    """[(local path, bytes)] of every file to write."""
    out = [(ROOT / "data" / p.rsplit("/", 1)[-1], crlf(download(sha, p))) for p in PATCHNOTES_VPK_PATHS]
    stats = ROOT / "data" / "stats" / version
    out += [(stats / p.rsplit("/", 1)[-1], download(sha, p)) for p in STATS_VPK_PATHS]
    out += [(stats / "heroes" / p.rsplit("/", 1)[-1], download(sha, p)) for p in hero_files(sha)]
    return out


def _same(path, data):
    """Equal to what is on disk, line ends aside (data/stats is LF in git, CRLF in a checkout from the game)."""
    if not path.exists():
        return False
    return path.read_bytes().replace(b"\r\n", b"\n") == data.replace(b"\r\n", b"\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version", help="the patch the files are for, e.g. 7.42 (data/stats/<version>/)")
    ap.add_argument("--ref", help="a GameTracking commit (default: the newest)")
    ap.add_argument("--dry-run", action="store_true", help="list what would change, write nothing")
    args = ap.parse_args()
    sha, build, day = resolve(args.ref)
    print(f"{REPO} {sha[:10]} (build {build or '?'}, {day})")
    files = plan(args.version, sha)
    changed = [(p, d) for p, d in files if not _same(p, d)]
    for p, d in changed:
        print(("would write " if args.dry_run else "wrote ") + str(p.relative_to(ROOT)), f"({len(d):,} bytes)")
        if not args.dry_run:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(d)
    print(f"{len(files)} files, {len(changed)} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
