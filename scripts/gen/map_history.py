"""Which map file each patch shipped, and the files themselves — from Steam's own depot history (the owner
2026-10-01: "make maps for every patch on the site, 7.38-7.41f with letter patches, later from 7.08").

game/dota/maps/dota.vpk lives in depot 373301 (Dota 2 Content). For every manifest of interest DepotDownloader
fetches only the manifest (`-manifest-only`, ~0.8 MB: the file list with every file's SHA-1); manifests whose
dota.vpk has the same SHA-1 carry the same map, so a map file is downloaded once per distinct SHA-1
(`-filelist`, ~30 MB). The manifest ids per patch come from the depot's manifest history (a CSV kept outside the
repo: seen_utc,manifest_id,branch).

Steam login: DepotDownloader needs an account that has Dota 2; log in once by QR code (`-qr -remember-password`,
scanned in the Steam mobile app) and set STEAM_USER to that account name — no password is stored or typed here.

    python scripts/gen/map_history.py hashes MANIFESTS.csv --from 7.38 --work D:\\oldbuilds
    python scripts/gen/map_history.py download --work D:\\oldbuilds
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from patch.meta import RELEASE_HISTORY  # noqa: E402

DD = os.environ.get("DEPOTDOWNLOADER", os.path.join(os.path.expanduser("~"), "tools", "depotdownloader",
                                                     "DepotDownloader.exe"))
APP, DEPOT = "570", "373301"
MAP_FILE = r"game\dota\maps\dota.vpk"
WINDOW_DAYS = 3                      # manifests within this many days after a release count as its release builds


def _ver_key(v):
    m = re.match(r"(\d+)\.(\d+)([a-z]?)", v)
    return int(m.group(1)), int(m.group(2)), m.group(3)


def patches(start):
    """[(version, release date)] oldest first, from patch/meta.py, from `start` on."""
    out = []
    for p in RELEASE_HISTORY:
        d = p.get("date")
        if d and _ver_key(p["version"]) >= _ver_key(start):
            out.append((p["version"], dt.datetime.strptime(d, "%d.%m.%Y").replace(tzinfo=dt.timezone.utc)))
    return sorted(out, key=lambda x: x[1])


def manifests(path):
    with open(path, encoding="utf-8") as f:
        rows = [(dt.datetime.fromisoformat(r["seen_utc"]), r["manifest_id"]) for r in csv.DictReader(f)
                if r["branch"] == "public"]
    return sorted(rows)


def candidates(pats, mans):
    """Per patch: its release builds (the first WINDOW_DAYS days) and its final build (the last before the next)."""
    out = {}
    for i, (ver, t0) in enumerate(pats):
        t1 = pats[i + 1][1] if i + 1 < len(pats) else dt.datetime.max.replace(tzinfo=dt.timezone.utc)
        win = [m for m in mans if t0 <= m[0] < min(t0 + dt.timedelta(days=WINDOW_DAYS), t1)]
        fin = [m for m in mans if m[0] < t1][-1:]
        out[ver] = {"release": [(t.isoformat(), mid) for t, mid in win], "final": [(t.isoformat(), mid) for t, mid in fin]}
    return out


def _dd(args, cwd):
    user = os.environ.get("STEAM_USER")
    if not user:
        raise SystemExit("set STEAM_USER (log in once with DepotDownloader -qr -remember-password)")
    cmd = [DD, "-app", APP, "-depot", DEPOT, "-username", user, "-remember-password"] + args
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def map_sha(work, mid):
    """SHA-1 and size of dota.vpk in a manifest (fetched once, kept in work/manifests)."""
    folder = os.path.join(work, "manifests")
    path = os.path.join(folder, f"manifest_{DEPOT}_{mid}.txt")
    for _ in range(6):
        if os.path.exists(path):
            break
        r = _dd(["-manifest", mid, "-manifest-only", "-dir", folder], work)
        if "RateLimitExceeded" not in (r.stdout + r.stderr):
            break
        print("rate limited, waiting 30 min", flush=True)
        time.sleep(1800)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 5 and parts[-1].lower() == MAP_FILE.lower():
                return {"sha1": parts[2], "size": int(parts[0])}
    return {"sha1": None, "size": 0}


def cmd_hashes(args):
    pats, mans = patches(args.start), manifests(args.manifests)
    cands = candidates(pats, mans)
    if args.until:
        cands = {v: c for v, c in cands.items() if _ver_key(v) < _ver_key(args.until)}
    if args.lean:
        # one login per manifest (DepotDownloader 3.4 takes one -depot/-manifest per run) and Steam rate-limits
        # logins: only the build a patch's map is taken from — its last release-day build, else the build before
        prev_final = None
        for ver, c in cands.items():
            c["release"], fin = c["release"][-1:], c["final"]
            if not c["release"] and prev_final:
                c["release"] = [prev_final]
            prev_final = fin[-1] if fin else prev_final
            c["final"] = []
    out_path = os.path.join(args.work, "map_history.json")
    hist = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {}
    for ver, c in cands.items():
        rows = []
        for role in ("release", "final"):
            for seen, mid in c[role]:
                fresh = not os.path.exists(os.path.join(args.work, "manifests", f"manifest_{DEPOT}_{mid}.txt"))
                info = map_sha(args.work, mid)
                if fresh:
                    time.sleep(args.pause)
                rows.append({"role": role, "seen": seen, "manifest": mid, **(info or {"sha1": "?"})})
        hist[ver] = rows
        shas = [r["sha1"] for r in rows]
        print(ver, " ".join((s or "-")[:8] for s in shas), flush=True)
        json.dump(hist, open(out_path, "w", encoding="utf-8"), indent=1)


def patch_maps(hist):
    """The map each patch shipped: the dota.vpk of the last build in its release window (the first build after a
    patch date is now and then still the old one — 7.41's map came a day later); a patch with no build in its
    window keeps the previous patch's last map. -> {version: {"sha1", "manifest"}} (versions in hist's order)."""
    out, prev = {}, None
    for ver, rows in hist.items():
        rel = [r for r in rows if r["role"] == "release" and r.get("sha1") not in (None, "?")]
        fin = [r for r in rows if r["role"] == "final" and r.get("sha1") not in (None, "?")]
        pick = rel[-1] if rel else prev
        if pick:
            out[ver] = {"sha1": pick["sha1"], "manifest": pick["manifest"]}
        prev = fin[-1] if fin else pick
    return out


def cmd_download(args):
    """One dota.vpk per distinct per-patch map, into work/maps/<sha1>.vpk; a pause between Steam logins (one login
    per manifest — ~110 logins in half an hour got 'RateLimitExceeded')."""
    hist = json.load(open(os.path.join(args.work, "map_history.json"), encoding="utf-8"))
    maps = patch_maps(hist)
    want = {}
    for ver, m in maps.items():
        if _ver_key(args.start) <= _ver_key(ver):
            want.setdefault(m["sha1"], m["manifest"])
    os.makedirs(os.path.join(args.work, "maps"), exist_ok=True)
    flist = os.path.join(args.work, "filelist.txt")
    open(flist, "w").write(MAP_FILE.replace("\\", "/") + "\n")
    for sha, mid in want.items():
        dest = os.path.join(args.work, "maps", f"{sha}.vpk")
        if os.path.exists(dest):
            continue
        tmp = os.path.join(args.work, "dl", mid)
        for attempt in range(6):
            r = _dd(["-manifest", mid, "-filelist", flist, "-dir", tmp], args.work)
            if "RateLimitExceeded" not in (r.stdout + r.stderr):
                break
            print("rate limited, waiting 30 min", flush=True)          # every retry is a login: wait it out
            time.sleep(1800)
        got = os.path.join(tmp, *MAP_FILE.split("\\"))
        if os.path.exists(got):
            os.replace(got, dest)
            print("got", sha[:8], "from", mid, flush=True)
        else:
            print("FAILED", sha[:8], mid, (r.stdout + r.stderr)[-300:], flush=True)
        time.sleep(args.pause)
    json.dump(maps, open(os.path.join(args.work, "patch_maps.json"), "w", encoding="utf-8"), indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hashes")
    h.add_argument("manifests")
    h.add_argument("--from", dest="start", default="7.38")
    h.add_argument("--work", required=True)
    h.add_argument("--until", help="stop before this patch")
    h.add_argument("--lean", action="store_true", help="only the build each patch's map comes from")
    h.add_argument("--pause", type=float, default=0, help="seconds between Steam logins")
    d = sub.add_parser("download")
    d.add_argument("--work", required=True)
    d.add_argument("--from", dest="start", default="7.38")
    d.add_argument("--pause", type=float, default=90, help="seconds between Steam logins")
    args = ap.parse_args()
    os.makedirs(args.work, exist_ok=True)
    {"hashes": cmd_hashes, "download": cmd_download}[args.cmd](args)


if __name__ == "__main__":
    main()
