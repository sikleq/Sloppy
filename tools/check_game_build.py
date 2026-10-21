"""Is there a game build newer than the newest snapshot? (scheduled by .github/workflows/game-build-watch.yml)

Compares the newest SteamTracking/GameTracking-Dota2 build with data/stats/<latest>/ (the root KV files) and
data/patchnotes_english.txt. Any difference = Valve shipped something after our snapshot: a new patch (new
DOTA_Patch_<v>_ keys -> python tools/new_patch.py) or a silent build (like client 6946's Necronomicon, 2026-10-07 —
the snapshot of the released patch must NOT be refreshed with it; it becomes the next patch's snapshot).

    python tools/check_game_build.py                 # print what differs, exit 0
    python tools/check_game_build.py --open-issue    # also open a GitHub issue (once per build; gh + GH_TOKEN)

Reads public files only; the only credential is the workflow's own GITHUB_TOKEN (issues: write).
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "fetch"))
TITLE = "Game build {build} changes the game files (newest snapshot: {latest})"


def _same(local_path, data):
    if not os.path.exists(local_path):
        return False
    with open(local_path, "rb") as f:
        return f.read().replace(b"\r\n", b"\n") == data.replace(b"\r\n", b"\n")


def changed_files(latest, download):
    """[(game path, local path)] whose content differs; `download(game path) -> bytes`."""
    import fetch_gametracking as gt
    pairs = [(p, os.path.join(ROOT, "data", "stats", latest, p.rsplit("/", 1)[-1])) for p in gt.STATS_VPK_PATHS]
    pairs.append((gt.PATCHNOTES_VPK_PATHS[0], os.path.join(ROOT, "data", "patchnotes_english.txt")))
    return [(p, local) for p, local in pairs if not _same(local, download(p))]


def _vkey(v):
    m = re.match(r"^(\d+)\.(\d+)([a-z]?)$", v)
    return (int(m.group(1)), int(m.group(2)), m.group(3)) if m else (0, 0, "")


def new_patch_keys(patchnotes, known):
    """Patch versions newer than every RELEASE_HISTORY one that have DOTA_Patch_<v>_ keys in the game's notes."""
    found = {m.replace("_", ".") for m in re.findall(r'"DOTA_Patch_(\d+_\d+[a-z]?)_', patchnotes)}
    top = max((_vkey(v) for v in known), default=(0, 0, ""))
    return sorted((v for v in found if _vkey(v) > top), key=_vkey)


def issue_body(build, sha, day, latest, changed, new_versions):
    lines = [f"GameTracking-Dota2 build **{build}** ({day}, `{sha[:10]}`) differs from `data/stats/{latest}/`:", ""]
    lines += [f"- `{p}`" for p, _ in changed]
    lines.append("")
    if new_versions:
        lines.append(f"The patch notes name a patch the site does not have: **{', '.join(new_versions)}**. Run "
                     f"`python tools/new_patch.py {new_versions[-1]} <dd.mm.yyyy>` (docs/workflow.md).")
    else:
        lines.append("No new patch in the notes: a build without patch notes. Do not refresh the "
                     f"`{latest}` snapshot with it; look for silent changes "
                     f"(`python scripts/fetch/fetch_gametracking.py {latest} --dry-run --ref {sha[:10]}`).")
    lines.append("")
    lines.append("Opened by .github/workflows/game-build-watch.yml.")
    return "\n".join(lines)


def _gh(args):
    out = subprocess.run(["gh"] + args, capture_output=True, text=True, encoding="utf-8")
    if out.returncode:
        raise RuntimeError(f"gh {' '.join(args[:2])}: {out.stderr.strip()}")
    return out.stdout


def main(argv):
    import fetch_gametracking as gt
    from patch.meta import RELEASE_HISTORY, latest_stats_version
    latest = latest_stats_version()
    sha, build, day = gt.resolve(None)
    cache = {}

    def download(path):
        if path not in cache:
            cache[path] = gt.download(sha, path)
        return cache[path]
    changed = changed_files(latest, download)
    print(f"{gt.REPO} {sha[:10]} build {build or '?'} ({day}) vs data/stats/{latest}: {len(changed)} file(s) differ")
    for p, _ in changed:
        print(f"  {p}")
    if not changed:
        return 0
    notes = download(gt.PATCHNOTES_VPK_PATHS[0]).decode("utf-8", "replace")
    new_versions = new_patch_keys(notes, [r["version"] for r in RELEASE_HISTORY])
    title = TITLE.format(build=build or sha[:10], latest=latest)
    if "--open-issue" not in argv:
        print(title)
        return 0
    issues = json.loads(_gh(["issue", "list", "--state", "all", "--search", f"{title} in:title", "--json", "title"]))
    if any(i["title"] == title for i in issues):
        print("an issue for this build exists already")
        return 0
    _gh(["issue", "create", "--title", title, "--body", issue_body(build, sha, day, latest, changed, new_versions)])
    print("issue opened:", title)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
