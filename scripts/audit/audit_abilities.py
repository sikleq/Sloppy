"""audit_abilities.py — Verify every ability() call in content/p<version>.py
resolves to a valid engine slug whose live Valve in-game name matches
the display name used in code.

For each hero referenced via hero_header(), fetch the hero's ability
list from /datafeed/herodata?hero_id=N and check that for each
ability("X") emitted under that hero, the resolved slug matches one
of Valve's slugs AND Valve's name_loc for that slug equals "X".

Also checks `ability_change(...)` blocks (old.name + new.name, with
optional explicit slug).

Run before publishing:

    python scripts/audit/audit_abilities.py
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
HEROLIST = "https://www.dota2.com/datafeed/herolist?language=english"
HERODATA = "https://www.dota2.com/datafeed/herodata?language=english&hero_id={}"


def fetch_json(url):
    with urlopen(url, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


print("Fetching live Valve hero list...")
herolist = fetch_json(HEROLIST)["result"]["data"]["heroes"]

# Map: localized hero name -> id
hero_id_for_loc = {h["name_loc"]: h["id"] for h in herolist}

# Slug maps live in the patch/ package; the ability()/hero_header() calls being
# audited live in content/p<version>.py.
sys.path.insert(0, str(ROOT))
from patch.images import HERO_SLUG
from patch.elements import HERO_TO_ABIL_PREFIX, ABILITY_DISPLAY_TO_SLUG as abi_disp_to_slug

# Shared allowlists. Located in patch/ rather than scripts/audit/ so
# builders/ can also import the same source of truth.
from patch.known_exceptions import (  # noqa: E402
    KNOWN_HISTORICAL_RENAMES,
    KNOWN_NON_DATAFEED_ABILITIES,
    KNOWN_DISPLAY_NAME_OVERRIDES,
    KNOWN_ICON_URL_PSEUDO_SLUGS,
    KNOWN_SYNTHETIC_SUBBLOCKS,
    KNOWN_INNATE_NO_CDN_ICON,  # noqa: F401
)

_content_files = sorted((ROOT / "content").glob("*.py"))
_file_bounds = []  # (start_offset, filename)
_chunks = []
_offset = 0
for p in _content_files:
    text = p.read_text(encoding="utf-8")
    _file_bounds.append((_offset, p.name))
    _chunks.append(text)
    _offset += len(text) + 1  # +1 for the "\n" join separator
src = "\n".join(_chunks)


def file_at(pos):
    """Return the content/*.py filename whose source spans byte offset `pos`."""
    name = _file_bounds[0][1]
    for start, fname in _file_bounds:
        if start > pos:
            break
        name = fname
    return name


def derive_ability_part(title):
    return (title.lower()
            .replace("'", "")
            .replace("-", "_")
            .replace(" ", "_")
            .replace(".", "")
            .replace("(", "")
            .replace(")", ""))


# Walk the source linearly, tracking current_hero. For each ability("X")
# under that hero, emit a (hero, display, explicit_slug, kind, icon_url_present, filename) tuple.
calls = []
current_hero = None
i = 0
lines = src.splitlines()
hero_re = re.compile(r'hero_header\("([^"]+)"\)')
abil_re = re.compile(r'ability\("([^"]+)"(?:\s*,\s*slug\s*=\s*"([^"]+)")?')
ach_old_re = re.compile(r'\bold\s*=\s*dict\(\s*name\s*=\s*"([^"]+)"(?:.*?slug\s*=\s*"([^"]+)")?', re.S)
ach_new_re = re.compile(r'\bnew\s*=\s*dict\(\s*name\s*=\s*"([^"]+)"(?:.*?slug\s*=\s*"([^"]+)")?', re.S)

# Use regex over full source preserving order
for m in re.finditer(
    r'hero_header\("([^"]+)"\)'
    r'|unit_header\(|plain_header\(|item_header\(|section\(|subgroup\(|enchant_header\('
    r'|ability\("([^"]+)"(?:\s*,\s*slug\s*=\s*"([^"]+)")?',
    src):
    if m.group(1):
        current_hero = m.group(1)
    elif m.group(2):
        # ability() call — scan forward to this call's closing paren and
        # check whether icon_url= appears anywhere inside the full argument
        # list (handles icon_url appearing after slug= or innate=).
        depth = 0
        j = m.start()
        while j < len(src):
            if src[j] == '(':
                depth += 1
            elif src[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        call_block = src[m.start():j + 1]
        has_icon_url = "icon_url=" in call_block
        if current_hero:
            calls.append((current_hero, m.group(2), m.group(3) or None, "ability",
                          has_icon_url, file_at(m.start())))
    elif m.group(0).startswith(('unit_header', 'plain_header', 'item_header', 'enchant_header')):
        # These reset the hero context (mirror patch/elements.py's
        # _State.current_hero = None behavior inside those header
        # functions). Without this, neutral-creep / item abilities
        # right after a hero block get misattributed to the previous
        # hero and produce false positives.
        current_hero = None

# Also catch ability_change old/new pairs (each may have explicit slug=)
for m in re.finditer(r'W\(ability_change\(', src):
    # Find matching paren and extract the block, then find current hero by walking back
    start = m.start()
    # Owner = the LAST header before this call IN THE SAME content file. A unit/item/plain
    # header in between means it is not a hero ability (Tormentor's cards at the top of
    # p738.py were blamed on the previous file's last hero, Windranger).
    last_hdr = None
    for hm in re.finditer(r'hero_header\("([^"]+)"\)|unit_header\(|plain_header\(|item_header\('
                          r'|enchant_header\(', src[:start]):
        last_hdr = hm
    if (not last_hdr or not last_hdr.group(1)
            or file_at(last_hdr.start()) != file_at(start)):
        continue
    hero = last_hdr.group(1)
    # Extract block
    depth = 0
    j = start + len("W(ability_change(") - 1
    while j < len(src):
        if src[j] == '(':
            depth += 1
        elif src[j] == ')':
            depth -= 1
            if depth == 0:
                break
        j += 1
    block = src[start:j + 2]
    fname = file_at(start)
    for side_re, kind in [(ach_old_re, "ach.old"), (ach_new_re, "ach.new")]:
        mm = side_re.search(block)
        if mm:
            has_icon_url = "icon_url=" in mm.group(0)
            calls.append((hero, mm.group(1), mm.group(2), kind, has_icon_url, fname))

print(f"Total ability references to verify: {len(calls)}")
print(f"Unique heroes referenced: {len({c[0] for c in calls})}\n")

# Fetch hero datafeeds in parallel
unique_heroes = sorted({c[0] for c in calls if c[0] in hero_id_for_loc})
unknown_heroes = {c[0] for c in calls if c[0] not in hero_id_for_loc}
if unknown_heroes:
    print(f"[X] {len(unknown_heroes)} heroes used in ability() not found in Valve hero list:")
    for h in sorted(unknown_heroes):
        print(f"    {h}")
    print()

print(f"Fetching herodata for {len(unique_heroes)} heroes...")


def fetch_abilities(hero_loc):
    hid = hero_id_for_loc[hero_loc]
    try:
        data = fetch_json(HERODATA.format(hid))
        h = data["result"]["data"]["heroes"][0]
        return hero_loc, {a["name"]: a["name_loc"] for a in h.get("abilities", [])}
    except Exception as e:
        return hero_loc, str(e)


valve_abilities = {}  # hero_loc -> {engine_slug: name_loc}
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(fetch_abilities, h): h for h in unique_heroes}
    for f in as_completed(futs):
        hero, result = f.result()
        if isinstance(result, dict):
            valve_abilities[hero] = result
        else:
            print(f"  X {hero}: {result}")

print()

icons_dir = ROOT / "icons" / "abilities"

problems = []
for hero, display, explicit_slug, kind, has_icon_url, fname in calls:
    if hero not in valve_abilities:
        continue  # already reported as unknown hero

    abis = valve_abilities[hero]  # {engine_slug: name_loc}

    # Resolve slug (engine name) the same way patch/elements.py does
    if explicit_slug:
        resolved = explicit_slug
    else:
        prefix = HERO_TO_ABIL_PREFIX.get(hero, HERO_SLUG.get(hero, hero.lower().replace(" ", "_")))
        if (hero, display) in abi_disp_to_slug:
            part = abi_disp_to_slug[(hero, display)]
        else:
            part = derive_ability_part(display)
        resolved = f"{prefix}_{part}"

    # Calls that supply their own icon_url= (e.g. synthetic pseudo-unit
    # slugs) or are explicitly listed as such bypass datafeed validation
    # entirely — they were never meant to resolve to a real ability slug.
    if (has_icon_url
            or resolved in KNOWN_ICON_URL_PSEUDO_SLUGS
            or resolved in KNOWN_SYNTHETIC_SUBBLOCKS):
        continue

    if resolved not in abis:
        # Search by display name across the hero's abilities to suggest a fix
        match_slug = next((s for s, n in abis.items() if n == display), None)
        # Manually confirmed real ability that Valve's live herodata simply
        # doesn't surface (innate abilities hidden from the public API).
        if (hero, resolved) in KNOWN_NON_DATAFEED_ABILITIES:
            continue
        problems.append((hero, display, kind, resolved, match_slug, abis.get(resolved), "slug not in hero's ability list", fname))
        continue

    valve_name = abis[resolved]
    if valve_name != display:
        # Intentional display-name override (e.g. a facet-applied effect
        # name layered on top of the base ability's tooltip name).
        if (hero, display, resolved) in KNOWN_DISPLAY_NAME_OVERRIDES:
            continue
        problems.append((hero, display, kind, resolved, None, valve_name, f"renamed -> '{valve_name}'", fname))

if not problems:
    print("All clean.")
    sys.exit(0)

# Categorize for clearer reporting.
# ach.old references describe pre-patch abilities (often renamed/removed in
# 7.41) — those are intentional historical references, not bugs. Surface
# them in a separate section so we can ignore them by default.
historical = [p for p in problems if p[2] == "ach.old"]
current = [p for p in problems if p[2] != "ach.old"]

# Within current, split renames from slug mismatches.
renamed = [p for p in current if p[6].startswith("renamed")]
slug_miss = [p for p in current if not p[6].startswith("renamed")]

# Renames in KNOWN_HISTORICAL_RENAMES are correct names in older patch content,
# scoped to the specific content file where the historical name is correct.
renamed_actionable = [p for p in renamed if (p[0], p[1], p[7]) not in KNOWN_HISTORICAL_RENAMES]
renamed_suppressed = [p for p in renamed if (p[0], p[1], p[7]) in KNOWN_HISTORICAL_RENAMES]

print(f"== CURRENT-STATE ISSUES (action required) ==")
suppressed_note = f"  ({len(renamed_suppressed)} suppressed as known historical)" if renamed_suppressed else ""
print(f"Renamed abilities (display name out of date): {len(renamed_actionable)}{suppressed_note}")
print(f"Slug mismatches (icon won't load): {len(slug_miss)}\n")

if renamed_actionable:
    print("--- RENAMED ---")
    for hero, display, kind, slug, suggest, valve_name, note, fname in renamed_actionable:
        print(f"  [{hero}] '{display}' -> '{valve_name}'  (slug={slug}, file={fname})")
    print()

if slug_miss:
    print("--- SLUG MISMATCH (suggest explicit slug= or ABILITY_DISPLAY_TO_SLUG entry) ---")
    for hero, display, kind, slug, suggest, valve_name, note, fname in slug_miss:
        suggestion = f"slug=\"{suggest}\"" if suggest else "?? (no Valve ability with this display name)"
        print(f"  [{hero}] '{display}' resolved to '{slug}' (file={fname}) -- fix: {suggestion}")
    print()

if historical:
    print(f"== HISTORICAL REFERENCES (ach.old side — usually intentional) ==")
    print(f"{len(historical)} entries skipped by default.")
    print("Run with --include-historical to inspect them.\n")
    if "--include-historical" in sys.argv:
        for hero, display, kind, slug, suggest, valve_name, note, fname in historical:
            print(f"  [{hero}] OLD-pane references '{display}' (was renamed/removed in 7.41, file={fname}) -- {note}")

if renamed_actionable or slug_miss:
    sys.exit(1)
