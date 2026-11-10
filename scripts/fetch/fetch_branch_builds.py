"""Dota 2's test servers, Experimental and Staging: when Valve push a new build to them (owner 2026-11-10).

They are separate Steam apps, not branches of app 570: Experimental 247040, Staging 2305270, the live game 570. Valve's own
keyless Web API gives each app's client version: api.steampowered.com/IGCVersion_<app>/GetClientVersion/v1 → active_version
(7505 = Experimental's build, 6973 = the live game's). A new number = a new build; its time = when the number was first seen.

Two sources, both written into data/branch_builds.json as one list of version changes (branch, from, version, time):
  * history — muk-as/DOTA2_WEB keeps a log of these numbers, steam_api/_HISTORY_by_date.txt, from 2023-11-16
    ("247040 - Dota 2 Experimental | [v] 7504 => 7505 | 2026-11-10 03:10:11 (UTC+3)"). Its times are minutes off at most:
    397 of 433 live builds since 2025-06 lie within 10 minutes of their GameTracking-Dota2 commit (2026-11-10).
  * our poll — the same Valve API, every 15 minutes (.github/workflows/branch-builds.yml); the window since the last
    check is kept (`after`), and the last checks live in a state file between runs (--state).

    python scripts/fetch/fetch_branch_builds.py                     # poll Valve once
    python scripts/fetch/fetch_branch_builds.py --history           # also read the muk-as log (GitHub API)
    python scripts/fetch/fetch_branch_builds.py --offline           # no network: check and re-sort the file

Raw answers are cached in .cache/branch_builds/ (gitignored); only data/branch_builds.json is committed.
"""
import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "branch_builds.json"
CACHE = ROOT / ".cache" / "branch_builds"
API = "https://api.steampowered.com/IGCVersion_{app}/GetClientVersion/v1/"
HISTORY_API = "https://api.github.com/repos/muk-as/DOTA2_WEB/contents/steam_api/_HISTORY_by_date.txt"
HISTORY_SOURCE = "muk-as/DOTA2_WEB"
POLL_SOURCE = "valve-api"

APPS = {247040: "experimental", 2305270: "staging", 570: "public"}
HISTORY_NAMES = {"247040 - Dota 2 Experimental": "experimental", "2305270 - Dota 2 Staging": "staging", "570 - Dota 2": "public"}
BRANCHES = ("experimental", "staging", "public")
TIME_FMT = "%Y-%m-%dT%H:%M:%SZ"
TIMED_WINDOW = timedelta(hours=3)
_HIST_LINE = re.compile(r"^(?P<name>[^|]+?) \| \[v\] (?P<old>None|\d+) => (?P<new>\d+) \| "
                        r"(?P<t>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \(UTC(?P<tz>[+-]\d+)\)$")


def utc_now():
    return datetime.now(timezone.utc).strftime(TIME_FMT)


def empty_data():
    return {"apps": {str(a): b for a, b in APPS.items()}, "checks": {}, "builds": []}


def load(path=DATA):
    if not path.exists():
        return empty_data()
    return json.loads(path.read_text(encoding="utf-8"))


def _key(b):
    return (b["branch"], b["from"], b["version"])


def validate(data):
    """The data as the page needs it; raises ValueError on anything broken (a bad poll must not look like "no builds")."""
    for key in ("apps", "checks", "builds"):
        if key not in data:
            raise ValueError(f"branch_builds.json: no '{key}'")
    seen = set()
    for b in data["builds"]:
        if b.get("branch") not in BRANCHES:
            raise ValueError(f"branch_builds.json: unknown branch in {b}")
        if not isinstance(b.get("version"), int) or not (b.get("from") is None or isinstance(b["from"], int)):
            raise ValueError(f"branch_builds.json: version is not a number in {b}")
        if b.get("source") not in (HISTORY_SOURCE, POLL_SOURCE):
            raise ValueError(f"branch_builds.json: unknown source in {b}")
        datetime.strptime(b["time"], TIME_FMT)
        if b.get("after") is not None and b["after"] > b["time"]:
            raise ValueError(f"branch_builds.json: 'after' later than 'time' in {b}")
        k = _key(b) + (b["time"],)
        if k in seen:
            raise ValueError(f"branch_builds.json: the same change twice: {b}")
        seen.add(k)
    return data


def _sorted(builds):
    return sorted(builds, key=lambda b: (b["time"], b["branch"], b["version"]))


def merge(data, polled, now):
    """Add a build for every app whose version moved since the last check. polled: {app: version}. The first check of an
    app only remembers its version: what it saw is not a new build."""
    out = {"apps": dict(data["apps"]), "checks": dict(data["checks"]), "builds": list(data["builds"])}
    for app, version in polled.items():
        key = str(app)
        last = out["checks"].get(key)
        if last is not None and last["version"] != version:
            b = {"branch": APPS[app], "from": last["version"], "version": version, "time": now, "after": last["checked"],
                 "source": POLL_SOURCE}
            b["timed"] = (_t(now) - _t(last["checked"])) <= TIMED_WINDOW
            if not _already_known(out["builds"], b):
                out["builds"].append(b)
        out["checks"][key] = {"version": version, "checked": now}
    out["builds"] = _sorted(out["builds"])
    return validate(out)


def _t(s):
    return datetime.strptime(s, TIME_FMT).replace(tzinfo=timezone.utc)


def _already_known(builds, b, within=timedelta(days=2)):
    """The same change (from → version of the same server) seen by the other source close in time."""
    return any(_key(x) == _key(b) and abs(_t(x["time"]) - _t(b["time"])) <= within for x in builds)


def parse_history(text):
    """The version changes of the three apps in the muk-as log, times in UTC. The first line of each app ("None => N")
    is where its log starts, not a build."""
    out = []
    for line in text.splitlines():
        m = _HIST_LINE.match(line.strip())
        if not m or m["name"] not in HISTORY_NAMES or m["old"] == "None":
            continue
        t = datetime.strptime(m["t"], "%Y-%m-%d %H:%M:%S") - timedelta(hours=int(m["tz"]))
        out.append({"branch": HISTORY_NAMES[m["name"]], "from": int(m["old"]), "version": int(m["new"]),
                    "time": t.strftime(TIME_FMT), "source": HISTORY_SOURCE, "timed": True})
    return out


def merge_history(data, history):
    """The log's builds that are not in the file yet (our own poll of the same change wins when it was first)."""
    builds = list(data["builds"])
    for b in history:
        same = [x for x in builds if _key(x) == _key(b) and abs(_t(x["time"]) - _t(b["time"])) <= timedelta(days=2)]
        if not same:
            builds.append(b)
        elif all(x["source"] == POLL_SOURCE for x in same) and _t(b["time"]) < min(_t(x["time"]) for x in same):
            builds = [x for x in builds if x not in same] + [b]           # the log saw it earlier: its time is closer
    return validate(dict(data, builds=_sorted(builds)))


def _get(url, cache_name, accept=None):
    headers = {"User-Agent": "sloppy-site-fetch"}
    if accept:
        headers["Accept"] = accept
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
        raw = r.read()
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / cache_name).write_bytes(raw)
    return raw


def poll_app(app):
    """The app's client version from Valve's Web API, raw answer cached."""
    body = json.loads(_get(API.format(app=app), f"{app}.json"))
    res = body.get("result") or {}
    if not res.get("success") or not isinstance(res.get("active_version"), int):
        raise RuntimeError(f"app {app}: no version in Valve's answer {body}")
    return res["active_version"]


def fetch_history():
    return _get(HISTORY_API, "muk-as_steam_api_history.txt", accept="application/vnd.github.raw").decode("utf-8")


def newer_checks(data, state):
    """The committed checks with any later one from the state file (the scheduled job keeps its last checks there, so a
    commit is needed only for a new build, not every run)."""
    out = dict(data, checks=dict(data["checks"]))
    for app, chk in state.items():
        cur = out["checks"].get(app)
        if app in out["apps"] and (cur is None or chk["checked"] > cur["checked"]):
            out["checks"][app] = chk
    return out


def save(data, path=DATA):
    """One build per line, so a new build is a one-line diff."""
    head = {k: v for k, v in data.items() if k != "builds"}
    lines = ",\n".join("  " + json.dumps(b, ensure_ascii=False) for b in data["builds"])
    text = json.dumps(head, indent=1, ensure_ascii=False)[:-2] + ',\n "builds": [\n' + lines + "\n ]\n}\n"
    path.write_text(text, encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", action="store_true", help="no network: check and re-sort the committed file")
    ap.add_argument("--history", action="store_true", help="also read the muk-as/DOTA2_WEB log through the GitHub API")
    ap.add_argument("--state", type=Path, help="a file with the last checks, read before and written after the poll")
    args = ap.parse_args(argv)
    data = validate(load(DATA))           # DATA read at call time: a test points it at a temporary file
    if args.state and args.state.exists():
        data = newer_checks(data, json.loads(args.state.read_text(encoding="utf-8")))
    if args.offline:
        data["builds"] = _sorted(data["builds"])
    else:
        if args.history:
            data = merge_history(data, parse_history(fetch_history()))
        data = merge(data, {app: poll_app(app) for app in APPS}, utc_now())
        if args.state:
            args.state.parent.mkdir(parents=True, exist_ok=True)
            args.state.write_text(json.dumps(data["checks"], indent=1) + "\n", encoding="utf-8")
    save(data, DATA)
    print(f"branch_builds.json: {len(data['builds'])} builds: "
          + ", ".join(f"{b} {sum(1 for x in data['builds'] if x['branch'] == b)}" for b in BRANCHES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
