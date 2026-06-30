"""check_icons.py — Verify every ability icon referenced in built HTML exists
as a local file under icons/abilities/. Run after build_site.py.

Scans dist/ HTML for <img src="...icons/abilities/..."> references and checks
that each corresponding file exists in the repo's icons/abilities/ directory.
Exits with code 1 if any icons are missing.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = ROOT / "dist"
ICONS_DIR = ROOT / "icons" / "abilities"

if not DIST_DIR.exists():
    print("dist/ not found. Run python build_site.py first.")
    sys.exit(1)

# Collect all ability icon slugs referenced in built HTML
slug_re = re.compile(r'icons/abilities/([^"\']+\.png)')
referenced = set()
for html_file in DIST_DIR.rglob("*.html"):
    text = html_file.read_text(encoding="utf-8", errors="replace")
    for m in slug_re.finditer(text):
        referenced.add(m.group(1))

print(f"Ability icon references found in dist/: {len(referenced)}")

missing = sorted(s for s in referenced if not (ICONS_DIR / s).exists())
ok_count = len(referenced) - len(missing)

print(f"OK:      {ok_count}")
print(f"Missing: {len(missing)}")

if missing:
    print("\nMissing local icon files (will show missing.svg fallback in browser):")
    for fname in missing:
        print(f"  MISSING  {fname}")
    sys.exit(1)

print("All referenced ability icons present locally.")
