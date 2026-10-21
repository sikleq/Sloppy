r"""A new Dota 2 patch on the site — the whole DATA side in one command (the owner 2026-10-21: "when a patch ships,
every page must pick up the new values by itself").

    python tools/new_patch.py 7.42 21.10.2026                    # the local game (default source)
    python tools/new_patch.py 7.42 21.10.2026 --source gametracking [--ref <sha>]
    python tools/new_patch.py 7.42 --dry-run                     # the plan only, nothing runs or changes
    python tools/new_patch.py 7.42 --from enchant                # resume at a step (after proofreading, a failure)

Runs, in the order of docs/workflow.md (each step says what it does; the first failure stops everything and says how
to resume):

  register      RELEASE_HISTORY row in patch/meta.py (version, date, filename), in its chronological place
  fetch         raw KV + localisation -> data/stats/<v>/, data/*.txt (local game: extract_patchnotes.py --local;
                backup: fetch_gametracking.py [--ref] — mind the build: GameTracking's newest can be LATER than the patch)
  slim          tools/slim_from_kv.py <v> -> heroes/items/units/abilities/ability_ids .json
  meta          build_site.py patch -> data/site_meta.json knows the new patch (BEFORE the top-ups, which map by date)
  npc_units … itemlist   the d2vpkr / datafeed top-ups (npc_units.json, heroes_raw.json, npc_abilities.json, itemlist.json)
  shops         scripts/fetch/extract_shops.py -> data/shops.txt (local game only)
  abilities_slim, herolist   the shared tables rebuilt from the new snapshot
  item_stat_lines, talent_slots   only where the KV history kept with the weights model is on this PC
  loc_history   tools/fetch_loc_history.py <prev> <v> (the new patch's tooltips, the previous one's closed by it;
                outside the repo)
  draft         generate_patch_code_v2.py <v> -> _generated_p_<v>_v2.py + data/normalized/patches/<v>.json, only while
                content/p<code>.py does not exist (a proofread page is never regenerated)
  enchant       scripts/gen/enchant_values.py + enchant_table.py <v>, only when content/p<code>.py has enchant_tier_box()
  build         python build_site.py (every page)
  check         tools/patch_check.py <v> (OK / MISSING / WARN; its exit code is this command's)

What stays human is printed at the end: proofreading the draft into content/p<code>.py (then rerun with
--from enchant), and the map / Terrain / Oldgrowth steps when the map file changed — those need the owner's PC (SFM
render, Source2Viewer, Steam depots). The map file counts as changed when the SHA-1 of the game's maps/dota.vpk
differs from the previous patch's row in data/map/patch_maps.json (local game), or when patch_maps.json already has
the patch with another SHA-1 than the patch before it.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
META = os.path.join(ROOT, "patch", "meta.py")
DOTA_PATH = os.environ.get("DOTA_PATH", r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota")
# the d2vpkr KV history kept with the weights model (git-ignored, the owner's PC): build_item_stat_lines.py
# (fit_item_prices.MODEL) and build_talent_slots.py (HIST) read the old patches from it
WEIGHTS_MODEL = os.path.join(ROOT, "outputs", "valve-revealed-weights-20260915")
PY = sys.executable
_VERSION = re.compile(r"^\d+\.\d+[a-z]?$")
_ENTRY = re.compile(r'^\s*\{"version":\s*"([^"]+)",\s*"date":\s*"(\d\d\.\d\d\.\d{4})"')
_CYCLE_COMMENT = re.compile(r"^\s*#\s*(\d+\.\d+) cycle\s*$")


# ── patch/meta.py: the RELEASE_HISTORY row ──────────────────────────────────────────────────────────────────────

def cycle(version):
    """'7.41f' -> '7.41'."""
    return re.match(r"^(\d+\.\d+)", version).group(1)


def _day(dmy):
    return datetime.datetime.strptime(dmy, "%d.%m.%Y").date()


def registered(text, version):
    """The date RELEASE_HISTORY gives `version`, or None."""
    for line in text.splitlines():
        m = _ENTRY.match(line)
        if m and m.group(1) == version:
            return m.group(2)
    return None


def entry_line(version, date):
    """In the file's own layout: `"7.41",  "date"` (versions without a letter get two spaces)."""
    pad = " " * (1 + max(0, 5 - len(version)))
    return f'    {{"version": "{version}",{pad}"date": "{date}", "filename": "patches/{version}.html"}},'


def register(text, version, date):
    """patch/meta.py text with the RELEASE_HISTORY row of `version` added in its chronological place (the list is
    newest first, grouped under "# 7.41 cycle" comments; a new cycle gets its own comment). Unchanged when the
    version is already there."""
    if registered(text, version):
        return text
    lines = text.split("\n")
    start = next(i for i, ln in enumerate(lines) if ln.startswith("RELEASE_HISTORY = ["))
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("]"))
    new_day, new_cycle = _day(date), cycle(version)
    at = end
    for i in range(start + 1, end):
        m = _ENTRY.match(lines[i])
        if m and _day(m.group(2)) < new_day:
            at = i
            break
    older = _ENTRY.match(lines[at]) if at < end else None
    comment = _CYCLE_COMMENT.match(lines[at - 1]) if at - 1 > start else None
    insert = [entry_line(version, date)]
    if comment and comment.group(1) != new_cycle:
        at -= 1                                    # above the older cycle's comment
        above = next((_ENTRY.match(lines[i]) for i in range(at - 1, start, -1) if _ENTRY.match(lines[i])), None)
        if not (above and cycle(above.group(1)) == new_cycle):
            insert = [f"    # {new_cycle} cycle"] + insert
    elif not comment and not (older and cycle(older.group(1)) == new_cycle):
        above = _ENTRY.match(lines[at - 1]) if at - 1 > start else None
        if not (above and cycle(above.group(1)) == new_cycle):
            insert = [f"    # {new_cycle} cycle"] + insert
    return "\n".join(lines[:at] + insert + lines[at:])


# ── conditions ───────────────────────────────────────────────────────────────────────────────────────────────────

def code(version):
    return version.replace(".", "")


def previous(version, date=None):
    """The patch released before `version` (by RELEASE_HISTORY date; `date` for one not registered yet)."""
    from patch.meta import RELEASE_HISTORY
    rows = {r["version"]: _day(r["date"]) for r in RELEASE_HISTORY}
    day = rows.get(version) or (_day(date) if date else datetime.date.max)
    older = [(d, v) for v, d in rows.items() if d < day and v != version]
    return max(older)[1] if older else None


def content_path(version):
    return os.path.join(ROOT, "content", f"p{code(version)}.py")


def has_enchant_blocks(version):
    path = content_path(version)
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as f:
        return "enchant_tier_box(" in f.read()


def _sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def map_status(version, source, dota_path=DOTA_PATH, patch_maps=None):
    """('changed' | 'same' | 'unknown', why). The map file is game/dota/maps/dota.vpk; patch_maps.json holds the SHA-1
    every patch shipped."""
    if patch_maps is None:
        with open(os.path.join(ROOT, "data", "map", "patch_maps.json"), encoding="utf-8") as f:
            patch_maps = json.load(f)["patches"]
    order = list(patch_maps)
    if version in patch_maps:
        i = order.index(version)
        if i == 0:
            return "changed", "the first patch in patch_maps.json"
        prev = order[i - 1]
        same = patch_maps[prev]["sha1"] == patch_maps[version]["sha1"]
        return ("same" if same else "changed"), f"patch_maps.json: {version} vs {prev}"
    vpk = os.path.join(dota_path, "maps", "dota.vpk")
    if source != "game" or not os.path.exists(vpk):
        return "unknown", ("no local game here: compare SHA-1 of game/dota/maps/dota.vpk with the last row of "
                           "data/map/patch_maps.json on the owner's PC")
    last = order[-1]
    sha = _sha1(vpk)
    return ("same" if sha == patch_maps[last]["sha1"] else "changed"), \
        f"maps/dota.vpk SHA-1 {sha[:10]} vs {last} {patch_maps[last]['sha1'][:10]}"


# ── the steps ────────────────────────────────────────────────────────────────────────────────────────────────────

class Step:
    def __init__(self, name, what, argv=None, func=None, skip=None):
        self.name, self.what, self.argv, self.func, self.skip = name, what, argv, func, skip


def plan(version, date, source="game", ref=None, dota_path=DOTA_PATH):
    """[Step] in the documented order; `skip` is the reason a step does not apply, or None."""
    content = os.path.exists(content_path(version))
    local_game = os.path.exists(os.path.join(dota_path, "pak01_dir.vpk"))
    history = os.path.isdir(WEIGHTS_MODEL)
    fetch = ([PY, "scripts/fetch/extract_patchnotes.py", version, "--local"] if source == "game" else
             [PY, "scripts/fetch/fetch_gametracking.py", version] + (["--ref", ref] if ref else []))
    no_hist = "the KV history of the weights model (outputs/valve-revealed-weights-20260915) is not on this PC"
    with open(META, encoding="utf-8") as f:
        have = registered(f.read(), version)
    return [
        Step("register", f"RELEASE_HISTORY row {version} {date or have or '(date missing!)'} in patch/meta.py",
             func="register", skip=f"already registered ({have})" if have and (not date or date == have) else None),
        Step("fetch", ("game files from the local game" if source == "game" else
                       f"game files from GameTracking-Dota2 ({ref or 'newest build — check it is the patch build'})")
             + f" -> data/stats/{version}/, data/*_english.txt", fetch,
             skip=None if source != "game" or local_game else f"no pak01_dir.vpk under {dota_path} (use --source gametracking)"),
        Step("slim", f"slim JSONs of data/stats/{version}/", [PY, "tools/slim_from_kv.py", version]),
        Step("meta", "data/site_meta.json with the new patch (before the top-ups)", [PY, "build_site.py", "patch"]),
        Step("npc_units", "npc_units.json top-up", [PY, "scripts/fetch/fetch_npc_history.py"]),
        Step("heroes_raw", "heroes_raw.json top-up", [PY, "scripts/fetch/fetch_hero_history.py"]),
        Step("npc_abilities", "npc_abilities.json top-up", [PY, "scripts/fetch/fetch_ability_history.py"]),
        Step("itemlist", "data/itemlist.json from Valve's datafeed", [PY, "scripts/fetch/fetch_itemlist.py"]),
        Step("shops", "data/shops.txt from the game", [PY, "scripts/fetch/extract_shops.py", dota_path],
             skip=None if local_game else "no local game: data/shops.txt stays — rerun on the owner's PC"),
        Step("abilities_slim", "data/abilities_slim.json from the new snapshot", [PY, "tools/build_abilities_slim.py"]),
        Step("herolist", "data/herolist.json from the new snapshot", [PY, "tools/build_herolist.py"]),
        Step("item_stat_lines", "data/rules/item_stat_lines.json", [PY, "tools/build_item_stat_lines.py"],
             skip=None if history else no_hist),
        Step("talent_slots", "data/rules/talent_slots.json", [PY, "tools/build_talent_slots.py"],
             skip=None if history else no_hist),
        Step("loc_history", f"the patch's tooltips + the previous patch's (now closed by {version}) -> outputs/loc_history",
             [PY, "tools/fetch_loc_history.py"] + [v for v in (previous(version, date), version) if v]),
        Step("draft", f"generator draft _generated_p_{version}_v2.py + data/normalized/patches/{version}.json",
             [PY, "generate_patch_code_v2.py", version],
             skip=f"content/p{code(version)}.py exists (proofread pages are never regenerated)" if content else None),
        Step("enchant_values", f"data/rules/enchant_values.json for {version}",
             [PY, "scripts/gen/enchant_values.py", version],
             skip=None if has_enchant_blocks(version) else "no enchant_tier_box() in the content file"),
        Step("enchant_table", f"data/rules/enchant_tables.json for {version}",
             [PY, "scripts/gen/enchant_table.py", version],
             skip=None if has_enchant_blocks(version) else "no enchant_tier_box() in the content file"),
        Step("build", "the whole site", [PY, "build_site.py"]),
        Step("check", f"tools/patch_check.py {version}", [PY, "tools/patch_check.py", version]),
    ]


def remaining(version, source, map_state):
    """The human steps left after a run."""
    out = []
    if not os.path.exists(content_path(version)):
        out.append(f"proofread _generated_p_{version}_v2.py, save it as content/p{code(version)}.py (the skill's "
                   f"annotate.md gates; python .claude/skills/sloppy-patch/lint_tags.py content/p{code(version)}.py), "
                   f"then: python tools/new_patch.py {version} --from enchant_values")
    state, why = map_state
    if state != "same":
        out.append(f"map file {'CHANGED' if state == 'changed' else 'not checked'} ({why}); patch_check's Map rows "
                   "show what is still missing. On the owner's PC: map store + patch_maps.json row, "
                   "extract_map_entities.py, build_terrain_diff.py, SFM render + renders.json, terrain_audit.py, "
                   "Oldgrowth versions/<v> with the three grids (skill reference map.md)")
    out.append("new heroes/items: HERO_SLUG / ITEM_SLUG in patch/images.py, fetch_icons.py, \"Updated item icons\" via "
               "extract_vpk_icons.py; python scripts/audit/check_icons.py")
    out.append("2-3 weeks later: python tools/refresh_weights_data.py")
    if source == "gametracking":
        out.append("GameTracking: make sure the build fetched is the patch's own (rerun with --ref if not)")
    return out


def _run(step, version, date):
    if step.func == "register":
        with open(META, encoding="utf-8", newline="") as f:
            raw = f.read()
        eol = "\r\n" if "\r\n" in raw else "\n"           # keep the checkout's line ends
        text = raw.replace("\r\n", "\n")
        have = registered(text, version)
        if have:
            if date and have != date:
                raise SystemExit(f"  {version} is in RELEASE_HISTORY with {have}, not {date} — fix patch/meta.py by hand")
            print(f"  already registered ({have})")
            return 0
        if not date:
            raise SystemExit(f"  {version} is not in RELEASE_HISTORY: give its release date (dd.mm.yyyy)")
        with open(META, "w", encoding="utf-8", newline="") as f:
            f.write(register(text, version, date).replace("\n", eol))
        print("  " + entry_line(version, date).strip())
        return 0
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(step.argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL).returncode


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):            # the Windows console is cp1251
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version")
    ap.add_argument("date", nargs="?", help="release date dd.mm.yyyy (needed when the patch is not registered yet)")
    ap.add_argument("--source", choices=("game", "gametracking"), default="game")
    ap.add_argument("--ref", help="GameTracking commit (with --source gametracking)")
    ap.add_argument("--from", dest="start", help="start at this step (names: see --dry-run)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, run and change nothing")
    args = ap.parse_args(argv)
    if not _VERSION.match(args.version):
        ap.error(f"version like 7.42 or 7.41g, not {args.version!r}")
    if args.date:
        try:
            _day(args.date)
        except ValueError:
            ap.error(f"date as dd.mm.yyyy, not {args.date!r}")
    steps = plan(args.version, args.date, args.source, args.ref)
    names = [s.name for s in steps]
    if args.start and args.start not in names:
        ap.error(f"--from: one of {', '.join(names)}")
    first = names.index(args.start) if args.start else 0
    print(f"New patch {args.version} ({args.source}){' — DRY RUN, nothing runs' if args.dry_run else ''}")
    last = 0
    for n, step in enumerate(steps, 1):
        label = f"[{n:2}/{len(steps)}] {step.name:15} {step.what}"
        if n - 1 < first:
            print(f"{label}\n         skipped (--from {args.start})")
            continue
        if step.skip:
            print(f"{label}\n         skipped: {step.skip}")
            continue
        cmd = "edit patch/meta.py" if step.func else subprocess.list2cmdline(["python"] + step.argv[1:])
        print(f"{label}\n         $ {cmd}", flush=True)
        if args.dry_run:
            continue
        code_ = _run(step, args.version, args.date)
        if code_ and step.name != "check":
            print(f"\nFAILED at step '{step.name}' (exit {code_}). Fix it, then resume:\n"
                  f"  python tools/new_patch.py {args.version}{' ' + args.date if args.date else ''} "
                  f"--source {args.source}{' --ref ' + args.ref if args.ref else ''} --from {step.name}")
            return 1
        last = code_
    state = map_status(args.version, args.source)
    print("\nStill human (this command cannot do it):")
    for line in remaining(args.version, args.source, state):
        print(f"  - {line}")
    if last:
        print("\npatch_check reports MISSING steps (above) — the human steps listed here close them.")
    return 0 if args.dry_run else last


if __name__ == "__main__":
    sys.exit(main())
