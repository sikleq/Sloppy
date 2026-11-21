"""notes_refresh.py — Valve's patch notes today vs our stored snapshot (data/<v>_datafeed.json).

Valve edits the notes after a release: 7.42's Kez "Base Damage 40/70/100 to 40/80/120" became "to 50/100/150", three
Nyx Assassin lines went away, a Brewmaster line came in (owner 2026-11-21: "снимок да, обновить и научить"). The
snapshot is fetched once (tools/patchgen/normalize.fetch_datafeed) and was never compared again, so the page kept
Valve's first wording. Run this on every proofread and before a release:

    python tools/notes_refresh.py 7.42 [7.41f …]       # report: lines changed, added, removed, with their hero/item
    python tools/notes_refresh.py 7.42 --write          # + store today's notes as the snapshot (the old one in git)

A line that changed or came in goes onto the page in Valve's current words; a removed line is checked in the game files
of the latest build of the patch before the page drops it (a revert, or text Valve only took out).
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.dota2.com/datafeed/patchnotes?version={v}&language=english"


def fetch(version):
    """Today's notes from Valve (one request; a "null" answer is an error, not empty notes)."""
    req = urllib.request.Request(URL.format(v=version), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    d = json.loads(raw)
    if not isinstance(d, dict):
        raise RuntimeError(f"{version}: Valve answered {raw[:40]!r} instead of patch notes")
    if "result" in d and "patch_notes" in d.get("result", {}):
        d = d["result"]["patch_notes"]
    return d


def _names():
    def load(name, key):
        try:
            data = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))["result"]["data"][key]
            return {x["id"]: x["name_english_loc"] for x in data}
        except (OSError, KeyError, ValueError):
            return {}
    return load("herolist.json", "heroes"), load("itemlist.json", "itemabilities")


def notes(feed):
    """[(note text, where)] in order; `where`: the hero / item / section the note sits under."""
    heroes, items = _names()
    out = []

    def walk(x, where):
        if isinstance(x, dict):
            w = where
            if "hero_id" in x:
                w = heroes.get(x["hero_id"], str(x["hero_id"]))
            elif "ability_id" in x and not where:
                w = items.get(x["ability_id"], str(x["ability_id"]))
            elif isinstance(x.get("title"), str) and not where:
                w = x["title"]
            for k, y in x.items():
                if k == "note" and isinstance(y, str):
                    out.append((y, w))
                else:
                    walk(y, w)
        elif isinstance(x, list):
            for y in x:
                walk(y, where)
    walk(feed, "")
    return out


def diff(stored, live):
    """(removed, added): note lines only in the stored snapshot / only in today's notes, each with where it sits.
    A changed line shows as one removed + one added under the same hero/item."""
    a, b = notes(stored), notes(live)
    sa, sb = {t for t, _ in a}, {t for t, _ in b}
    removed = [(t, w) for t, w in a if t not in sb]
    added = [(t, w) for t, w in b if t not in sa]
    # Valve now writes the ability / aspect before the line ("Drums of Slom: Drum Hit Damage …"): the same note
    same = {(t, u) for t, _ in removed for u, _ in added if u.endswith(": " + t)}
    gone = {t for t, _ in same} | {u for _, u in same}
    return [(t, w) for t, w in removed if t not in gone], [(t, w) for t, w in added if t not in gone]


def main(argv):
    write = "--write" in argv
    versions = [a for a in argv if not a.startswith("--")]
    if not versions:
        print(__doc__)
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    for v in versions:
        path = ROOT / "data" / f"{v}_datafeed.json"
        if not path.exists():
            print(f"# {v}: no stored snapshot")
            continue
        live = fetch(v)
        removed, added = diff(json.loads(path.read_text(encoding="utf-8")), live)
        print(f"# {v}: removed {len(removed)}, added {len(added)}")
        for t, w in removed:
            print(f"  - [{w}] {t}")
        for t, w in added:
            print(f"  + [{w}] {t}")
        if write and (removed or added):
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(live, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(path)
            print(f"  wrote {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
