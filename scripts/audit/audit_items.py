"""audit_items.py — Verify every item_header() display name in
content/p<version>.py matches the live Valve in-game name.

Flags items where:
  - display name doesn't match Valve's name_loc for the corresponding engine slug
  - the display name has no matching engine slug at all (typo or rename)
  - the ITEM_SLUG-resolved engine slug has no matching local PNG

Fetches the live datafeed automatically. Run after editing item_header()
calls or before publishing a new patch:

    python scripts/audit/audit_items.py
"""
import json
import re
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
DATAFEED = "https://www.dota2.com/datafeed/itemlist?language=english"

print("Fetching live Valve item datafeed...")
try:
    with urlopen(DATAFEED, timeout=15) as r:
        items_data = json.loads(r.read().decode("utf-8"))
except Exception as e:
    print(f"X cannot fetch datafeed: {e}")
    sys.exit(1)
valve = {}
for it in items_data["result"]["data"]["itemabilities"]:
    eng = it["name"]
    if not eng.startswith("item_"):
        continue
    slug = eng[5:]  # strip 'item_'
    valve[slug] = it["name_loc"]

# Reverse map: display name -> engine slug
display_to_slug = {}
for slug, name in valve.items():
    if not name:
        continue
    display_to_slug.setdefault(name, slug)

# ITEM_SLUG lives in the patch/ package; item_header() calls live in content/.
sys.path.insert(0, str(ROOT))
from patch.images import ITEM_SLUG as item_slug_map

content_src = "\n".join(p.read_text(encoding="utf-8")
                        for p in sorted((ROOT / "content").glob("*.py")))

# Pull every item_header("...") call
calls = sorted(set(re.findall(r'item_header\("([^"]+)"', content_src)))
print(f"item_header() calls referencing {len(calls)} unique display names")
print(f"ITEM_SLUG overrides: {len(item_slug_map)}\n")

icons_dir = ROOT / "icons" / "items"

problems = []
for display in calls:
    # Resolved slug: ITEM_SLUG override OR naive derivation
    if display in item_slug_map:
        resolved_slug = item_slug_map[display]
    else:
        resolved_slug = display.lower().replace("'", "").replace(" ", "_").replace("-", "_")

    # Lookup live display for resolved slug
    valve_display = valve.get(resolved_slug)
    icon_present = (icons_dir / f"{resolved_slug}.png").exists()

    if valve_display is None:
        # Slug doesn't exist in Valve data at all
        problems.append((display, resolved_slug, valve_display, icon_present, "slug NOT in Valve data"))
    elif valve_display != display:
        # Slug exists but live name differs
        problems.append((display, resolved_slug, valve_display, icon_present, f"renamed → '{valve_display}'"))
    elif not icon_present:
        problems.append((display, resolved_slug, valve_display, icon_present, "icon missing locally"))

if not problems:
    print("All clean.")
    sys.exit(0)

print(f"{len(problems)} problems:\n")
for display, slug, valve_d, icon, note in problems:
    print(f"  [{note}]")
    print(f"    display in content/        : {display}")
    print(f"    resolved engine slug      : {slug}")
    print(f"    valve live name           : {valve_d}")
    print(f"    icon present              : {icon}")
    print()
