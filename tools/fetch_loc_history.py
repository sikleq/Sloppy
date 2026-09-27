r"""The game's localization (tooltips of abilities, items, talents, facets; hero texts) as it was in EVERY
patch -> ~/outputs/loc_history/<version>/{abilities,dota}_english.txt.gz + index.json (owner 2026-09-27:
"why don't we have the descriptions of every patch?"). Old tooltips are then read from the game's own
files instead of hunting a d2vpkr commit by hand. Outside the repo (≈ 100+ MB); read with
tools/loc_history.py.

Source: dotabuff/d2vpkr history. A patch's text = the last commit of the file BEFORE the next patch came
out (the latest patch: the newest commit). Paths: since Dec 2018 (7.20) `dota/resource/localization/
abilities_english.txt` / `dota_english.txt`; before that everything is in `dota/resource/dota_english.txt`.

Usage:  python tools/fetch_loc_history.py            # missing versions only
        python tools/fetch_loc_history.py 7.38 7.41f # these versions (re-fetch)
"""
import datetime as dt
import gzip
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from patch.meta import RELEASE_HISTORY  # noqa: E402

OUT = os.path.join(os.path.expanduser("~"), "outputs", "loc_history")
REPO = "dotabuff/d2vpkr"
FILES = {  # name -> candidate paths, newest layout first
    "abilities": ["dota/resource/localization/abilities_english.txt", "dota/resource/dota_english.txt"],
    "dota": ["dota/resource/localization/dota_english.txt", "dota/resource/dota_english.txt"],
}


def _date(s):
    return dt.datetime.strptime(s, "%d.%m.%Y").replace(tzinfo=dt.timezone.utc)


def _last_commit(path, until):
    q = f"repos/{REPO}/commits?path={path}&per_page=1" + (f"&until={until:%Y-%m-%dT%H:%M:%SZ}" if until else "")
    r = subprocess.run(["gh", "api", q, "--jq", ".[0] | [.sha, .commit.committer.date] | @tsv"],
                       capture_output=True, text=True, timeout=120)
    line = r.stdout.strip()
    return line.split("\t") if line else None


def _decode(raw):
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def fetch(version, until):
    folder = os.path.join(OUT, version)
    os.makedirs(folder, exist_ok=True)
    info = {}
    for name, paths in FILES.items():
        for path in paths:
            c = _last_commit(path, until)
            if c:
                break
        if not c:
            print(f"  {version} {name}: no commit")
            continue
        sha, date = c
        url = f"https://raw.githubusercontent.com/{REPO}/{sha}/{path}"
        raw = urllib.request.urlopen(url, timeout=300).read()
        with gzip.open(os.path.join(folder, f"{name}_english.txt.gz"), "wt", encoding="utf-8") as f:
            f.write(_decode(raw))
        info[name] = {"path": path, "sha": sha, "date": date}
    return info


def main():
    rel = [(r["version"], _date(r["date"])) for r in RELEASE_HISTORY if r.get("date")]
    rel.sort(key=lambda x: x[1])
    want = set(sys.argv[1:])
    idx_path = os.path.join(OUT, "index.json")
    index = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}
    for i, (v, d) in enumerate(rel):
        if (want and v not in want) or (not want and v in index):
            continue
        until = rel[i + 1][1] if i + 1 < len(rel) else None
        index[v] = fetch(v, until)
        print(v, {k: x["date"][:10] for k, x in index[v].items()}, flush=True)
        json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1)
    print("versions:", len(index))


if __name__ == "__main__":
    main()
