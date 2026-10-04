"""Shared by fetch_hero_history.py and fetch_ability_history.py: patch dates, and which dotabuff/d2vpkr commit of a
KV file was current at a patch's end. Both scripts used to carry byte-identical copies (audit 2026-10-04)."""
import json
import subprocess
import urllib.request
from datetime import date


def load_patch_dates(meta_path):
    """{version: date} from data/site_meta.json's patch_dates ("dd.mm.yyyy")."""
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    out = {}
    for ver, ds in meta.get("patch_dates", {}).items():
        try:
            d, mth, y = (int(x) for x in ds.split("."))
            out[ver] = date(y, mth, d)
        except (ValueError, AttributeError):
            continue
    return out


def _fetch_page(repo, file_path, page):
    api = "repos/{}/commits?path={}&per_page=100&page={}".format(repo, file_path, page)
    try:
        res = subprocess.run(["gh", "api", api], capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    with urllib.request.urlopen("https://api.github.com/" + api) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_commit_index(repo, file_path):
    """[(commit date, sha)] of every commit that touched file_path, oldest first."""
    data, page = [], 1
    while True:
        chunk = _fetch_page(repo, file_path, page)
        if not chunk:
            break
        data.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    idx = []
    for c in data:
        sha = c.get("sha")
        ds = c.get("commit", {}).get("author", {}).get("date", "")[:10]
        if not sha or not ds:
            continue
        y, mth, d = (int(x) for x in ds.split("-"))
        idx.append((date(y, mth, d), sha))
    idx.sort()
    return idx


def commit_for_window(commit_idx, win_end):
    """The last commit strictly before win_end (the next patch's date), or None."""
    chosen = None
    for cdate, sha in commit_idx:
        if cdate < win_end:
            chosen = sha
        else:
            break
    return chosen
