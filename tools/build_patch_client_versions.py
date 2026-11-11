"""data/patch_client_versions.json: the live client version each patch came out with (owner 2026-11-11: "из билдов").

A patch's release build is the first build of the game that already has the patch's own notes (and not the next
patch's) — the same first step as the game-files store's tools/builds.py, before its release-night fixes. Its
ClientVersion (game/dota/steam.inf) is looked up in data/branch_builds.json's live-game log, which gives the minute the
patch went live (patch/branch_builds.patch_moments). "The first live build of the patch's day" was wrong for 17 of 46
patches: a hotfix of the previous patch came out earlier that day (7.41: 24.03 00:00 was 7.40c's, 7.41 came at 23:49),
or the site's date was a day off (7.36b, 7.38b).

Needs the store and its archives on this PC (DOTA2_CLIENT, GameTracking — see the store's tools/builds.py), so CI never
runs it; the JSON is committed. Usage:
  python tools/build_patch_client_versions.py            every patch of RELEASE_HISTORY the archives hold
  python tools/build_patch_client_versions.py 7.42       one patch (tools/new_patch.py runs this)
  python tools/build_patch_client_versions.py --set 7.42=7001   by hand (e.g. steam.inf of the installed game)
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "data" / "patch_client_versions.json"
STORE = Path(os.environ.get("DOTA_FILES_DIR", Path.home() / "dota-patch-files"))
STEAM_INF = "game/dota/steam.inf"
_CLIENT_VERSION = re.compile(r"ClientVersion=(\d+)")


def client_version(steam_inf):
    """The ClientVersion number of a steam.inf text, or None."""
    m = _CLIENT_VERSION.search(steam_inf or "")
    return int(m.group(1)) if m else None


def first_notes_build(clone, version, day, next_version, max_gap_days):
    """The ClientVersion of the first build in `clone` with `version`'s notes and without `next_version`'s, or None."""
    for sha, d in clone.commits:
        if not -1 <= (d.date() - day).days <= max_gap_days:
            continue
        if clone.has_notes(sha, version):
            if next_version and clone.has_notes(sha, next_version):
                return None
            return client_version(clone.file(sha, STEAM_INF))
    return None


def find_all(versions=None):
    """{version: ClientVersion} for the patches the archives hold (all of RELEASE_HISTORY, or only `versions`)."""
    sys.path.insert(0, str(STORE / "tools"))
    import builds as store_builds                       # the store's own module: archives, Clone.has_notes
    b = store_builds.Builds()
    names = [p["version"] for p in b.history]           # newest first
    out = {}
    for v in versions or names:
        k = names.index(v)
        nxt = names[k - 1] if k > 0 else None
        for clone in b.clones():
            cv = first_notes_build(clone, v, b.dates[v], nxt, store_builds.MAX_GAP_DAYS)
            if cv:
                out[v] = cv
                break
    return out


def merge(old, new):
    """The table with `new` written over `old`, oldest client version first (stable for diffs)."""
    both = {**old, **new}
    return dict(sorted(both.items(), key=lambda kv: kv[1]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("versions", nargs="*")
    ap.add_argument("--set", action="append", default=[], metavar="V=N", help="write a version by hand")
    args = ap.parse_args(argv)
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    new = {}
    for pair in args.set:
        v, n = pair.split("=", 1)
        new[v.strip()] = int(n)
    if not args.set:
        if not STORE.exists():
            print(f"the game-files store ({STORE}) is not on this PC: nothing to do", file=sys.stderr)
            return 1
        new = find_all(args.versions or None)
        missing = [v for v in args.versions if v not in new]
        if missing:
            print("no build with the notes of: " + ", ".join(missing), file=sys.stderr)
    OUT.write_text(json.dumps(merge(old, new), indent=1) + "\n", encoding="utf-8")
    print(f"{len(new)} patch(es) -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
