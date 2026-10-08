"""What a patch still misses on the site — the steps of the new-patch routine (docs/workflow.md, the project skill
sloppy-patch), checked one by one (the owner 2026-10-08: the skill describes the order but nothing checked it).

    python tools/patch_check.py            # the newest patch in patch/meta.py RELEASE_HISTORY
    python tools/patch_check.py 7.41f      # a given one

Each line: OK, MISSING (a step not done — exit code 1) or WARN (can't be checked here, e.g. a file only on the
owner's PC, or a reminder). Nothing is written.
"""
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OLDGROWTH = os.environ.get("OLDGROWTH_DIR", os.path.join(os.path.expanduser("~"), "Documents", "Oldgrowth"))
STATS_FILES = ("items.txt", "items.json", "units.json", "npc_units.txt", "npc_units.json", "npc_abilities.txt",
               "npc_abilities.json", "npc_heroes.txt", "heroes.json", "heroes_raw.json", "abilities.json",
               "ability_ids.json")


def _p(*parts):
    return os.path.join(ROOT, *parts)


def _json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _code(ver):
    return ver.replace(".", "")


def check_meta(ver):
    from patch.meta import RELEASE_HISTORY
    from patch.page import PATCH_ENTRY_COUNTS
    entry = next((e for e in RELEASE_HISTORY if e["version"] == ver), None)
    yield ("Registration", "RELEASE_HISTORY (patch/meta.py)",
           ("OK", entry["date"]) if entry else ("MISSING", "add version + date"))
    yield ("Registration", "PATCH_ENTRY_COUNTS (patch/page.py)",
           ("OK", str(PATCH_ENTRY_COUNTS[ver])) if ver in PATCH_ENTRY_COUNTS else ("MISSING", "calendar highlight"))


def _latest():
    from patch.meta import RELEASE_HISTORY
    return RELEASE_HISTORY[0]["version"]


def _strict(ver, note):
    """CI demands the full file set and the normalized JSON of the NEWEST patch only; older ones only warn."""
    return ("MISSING", note) if ver == _latest() else ("WARN", note + " (older patch: not required by CI)")


def check_stats(ver):
    folder = _p("data", "stats", ver)
    if not os.path.isdir(folder):
        yield ("Game data", f"data/stats/{ver}/", ("MISSING", "no folder: extract_patchnotes / fetch_gametracking"))
        return
    missing = [f for f in STATS_FILES if not os.path.exists(os.path.join(folder, f))]
    yield ("Game data", "the required file set", _strict(ver, ", ".join(missing)) if missing else ("OK", f"{len(STATS_FILES)} files"))
    heroes_dir = os.path.join(folder, "heroes")
    have = {f[len("npc_dota_hero_"):-4] for f in os.listdir(heroes_dir)} if os.path.isdir(heroes_dir) else set()
    try:
        heroes = _json(os.path.join(folder, "heroes.json"))
        names = [h if isinstance(h, str) else h.get("name", "") for h in (heroes if isinstance(heroes, list) else heroes.keys())]
        # npc_dota_hero_base is the parent template, not a hero (extract_patchnotes skips its file)
        want = {re.sub(r"^npc_dota_hero_", "", n) for n in names if n} - {"base"}
    except (OSError, ValueError, AttributeError):
        want = set()
    lost = sorted(want - have) if want else []
    yield ("Game data", "heroes/ — a file per hero",
           ("MISSING", ", ".join(lost[:6])) if lost else ("OK", f"{len(have)} files") if have else ("MISSING", "no heroes/"))


def check_globals(ver):
    key = "DOTA_Patch_" + ver.replace(".", "_") + "_"
    try:
        with open(_p("data", "patchnotes_english.txt"), encoding="utf-8-sig", errors="replace") as f:
            n = f.read().count(key)
    except OSError:
        n = 0
    yield ("Game data", "patchnotes_english.txt has its keys", ("OK", f"{n} keys") if n else ("MISSING", "refresh it"))
    feed = _p("data", f"{ver}_datafeed.json")
    yield ("Game data", "Valve datafeed cached", ("OK", "") if os.path.exists(feed) else ("WARN", "generate_patch_code_v2 fetches it"))


def check_content(ver):
    content = _p("content", f"p{_code(ver)}.py")
    if not os.path.exists(content):
        yield ("Patch page", f"content/p{_code(ver)}.py", ("MISSING", "generate + proofread"))
        return
    with open(content, encoding="utf-8") as f:
        text = f.read()
    yield ("Patch page", f"content/p{_code(ver)}.py", ("OK", ""))
    yield ("Patch page", "no TODO[ markers left", ("MISSING", f"{text.count('TODO[')} left") if "TODO[" in text else ("OK", ""))
    yield ("Patch page", "save_html at its end", ("OK", "") if "save_html(" in text else ("MISSING", "the page is never written"))
    yield ("Patch page", "normalized JSON", ("OK", "") if os.path.exists(_p("data", "normalized", "patches", f"{ver}.json"))
           else _strict(ver, "generate_patch_code_v2 writes it"))
    page = _p("dist", "patches", f"{ver}.html")
    yield ("Patch page", "dist page built", ("OK", "") if os.path.exists(page)
           else ("WARN", "run python build_site.py") if not os.path.isdir(_p("dist")) else ("MISSING", "build did not write it"))


def check_map(ver):
    patches = _json(_p("data", "map", "patch_maps.json"))["patches"]
    if ver not in patches:
        yield ("Map", "patch_maps.json row", ("MISSING", "map file of the patch"))
        return
    order = list(patches)
    i = order.index(ver)
    new_file = i == 0 or patches[order[i - 1]]["sha1"] != patches[ver]["sha1"]
    if not new_file:
        yield ("Map", "map file", ("OK", f"same as {order[i - 1]} — nothing to do"))
        return
    yield ("Map", "map file", ("OK", "a new map file"))
    yield ("Map", f"mapdata_{_code(ver)}.json", ("OK", "") if os.path.exists(_p("data", "map", f"mapdata_{_code(ver)}.json"))
           else ("MISSING", "extract_map_entities.py --store"))
    yield ("Map", f"terrain_diff_{ver}.json", ("OK", "") if os.path.exists(_p("data", f"terrain_diff_{ver}.json"))
           else ("MISSING", "build_terrain_diff.py"))
    pics = _json(_p("data", "map", "renders.json")).get("pictures", {})
    yield ("Map", "own picture (renders.json + icons/maps)",
           ("OK", pics[ver]) if ver in pics and os.path.exists(_p("icons", "maps", f"map_{ver}.webp")) else ("MISSING", "render + map_<ver>.webp"))
    folder = os.path.join(OLDGROWTH, "versions", ver)
    if not os.path.isdir(os.path.join(OLDGROWTH, "versions")):
        yield ("Map", "Oldgrowth", ("WARN", "the Oldgrowth folder is not here"))
        return
    want = ["info.json", "mapdata.json", "entities.json.gz", "gridnav.bin.gz", "elev.bin.gz", "fow.bin.gz"]
    lost = [f for f in want if not os.path.exists(os.path.join(folder, f))]
    yield ("Map", "Oldgrowth: data + entities + 3 grids",
           ("MISSING", ", ".join(lost) + " — oldgrowth_mapdata.py") if lost else ("OK", ""))


def check_release(ver):
    from patch.meta import RELEASE_HISTORY
    entry = next((e for e in RELEASE_HISTORY if e["version"] == ver), None)
    if not entry:
        return
    day = datetime.datetime.strptime(entry["date"], "%d.%m.%Y").date()
    rules = _p("data", "rules", "ability_priority.json")
    if os.path.exists(rules):
        updated = datetime.date.fromtimestamp(os.path.getmtime(rules))
        due = day + datetime.timedelta(days=14)
        if updated < day and datetime.date.today() >= due:
            yield ("Release", "weights data (refresh_weights_data.py)", ("WARN", f"last refresh {updated}, due since {due}"))
        else:
            yield ("Release", "weights data (refresh_weights_data.py)", ("OK", f"updated {updated}"))
    log = _json(_p("data", "changelog.json"))["entries"]
    mention = any(ver in json.dumps(e) for e in log)
    yield ("Release", "site changelog mentions the patch", ("OK", "") if mention else ("WARN", "a new patch page is worth an entry"))


CHECKS = (check_meta, check_stats, check_globals, check_content, check_map, check_release)


def run(ver):
    rows = []
    for check in CHECKS:
        rows += list(check(ver))
    return rows


def main(argv):
    from patch.meta import RELEASE_HISTORY
    ver = argv[0] if argv else RELEASE_HISTORY[0]["version"]
    rows = run(ver)
    width = max(len(r[1]) for r in rows)
    print(f"Patch {ver}")
    for group, what, (status, note) in rows:
        print(f"  {status:8} {group:13} {what:{width}}  {note}")
    missing = sum(1 for r in rows if r[2][0] == "MISSING")
    print(f"{missing} missing, {sum(1 for r in rows if r[2][0] == 'WARN')} warnings")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
