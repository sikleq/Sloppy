"""fetch_facets.py — Extract facet metadata for a given patch from
Valve's live patchnotes datafeed and emit a Python dict snippet ready
to paste into patch/badges.py's FACETS table.

Usage:
    python scripts/fetch/fetch_facets.py 7.40c
    python scripts/fetch/fetch_facets.py 7.39b 7.39c 7.39d
"""
import json
import sys
from urllib.request import urlopen

ENDPOINT = "https://www.dota2.com/datafeed/patchnotes?version={}&language=english"

if len(sys.argv) < 2:
    print("Usage: python scripts/fetch/fetch_facets.py <version> [<version> ...]")
    sys.exit(1)

seen = {}
for version in sys.argv[1:]:
    print(f"\n# Fetching {version}...")
    try:
        with urlopen(ENDPOINT.format(version), timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  X {e}")
        continue

    for hero in data.get("heroes", []):
        for sub in hero.get("subsections", []):
            if sub.get("style") != "hero_facet":
                continue
            slug = sub.get("facet")
            title = sub.get("title")
            color = sub.get("facet_color", "Gray0")
            if not slug or slug in seen:
                continue
            seen[slug] = (title, color, version)

print(f"\n# Found {len(seen)} unique facets across {len(sys.argv) - 1} patch(es).\n")
print("FACETS = {")
for slug, (title, color, ver) in sorted(seen.items()):
    print(f'    "{slug}": ("{title}", "{color}"),  # {ver}')
print("}")
