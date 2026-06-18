"""Download neutral-creep portrait icons from Valve CDN to icons/units/.
Source path: dota_react/units/npc_dota_neutral_<slug>.png."""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests"); sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
UNITS_DIR = ROOT / "icons" / "units"
UNITS_DIR.mkdir(parents=True, exist_ok=True)
CDN = "https://cdn.steamstatic.com/apps/dota2/images/dota_react/units/"

units = json.loads((ROOT / "data" / "stats" / "7.41c" / "units.json").read_text(encoding='utf-8'))
slugs = sorted(k for k in units if k.startswith('npc_dota_neutral_'))

# Hero-summoned units we surface alongside neutrals in the creeps table.
# Add new entries here whenever the table grows.
slugs += [
    'npc_dota_dark_troll_warlord_skeleton_warrior',
]

missing = [s for s in slugs if not (UNITS_DIR / f"{s}.png").exists()]
print(f"Total neutrals: {len(slugs)}  Missing locally: {len(missing)}")

def fetch(slug):
    url = f"{CDN}{slug}.png"
    out = UNITS_DIR / f"{slug}.png"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and r.content:
            out.write_bytes(r.content)
            return slug, "OK", len(r.content)
        return slug, str(r.status_code), 0
    except Exception as e:
        return slug, str(e), 0

ok, fail = 0, []
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(fetch, s): s for s in missing}
    for fut in as_completed(futures):
        slug, status, size = fut.result()
        if status == "OK":
            ok += 1
            print(f"  + {slug}  ({size:,} bytes)")
        else:
            fail.append((slug, status))

print(f"\nDownloaded: {ok}  Failed: {len(fail)}")
for slug, status in fail:
    print(f"  {status:>3}  {slug}")
