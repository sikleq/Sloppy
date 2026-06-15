"""audit_all.py — Run the full validation pipeline:
   1. audit_heroes.py     — hero_header() display names + icons
   2. audit_items.py      — item_header() display names + ITEM_SLUG + icons
   3. audit_abilities.py  — ability() / ability_change() slugs + names
   4. fetch_icons.py      — auto-download any missing ability PNGs

Run after builders/patch.py before publishing a patch.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ["audit_heroes.py", "audit_items.py", "audit_abilities.py", "fetch_icons.py"]

for s in SCRIPTS:
    path = ROOT / s
    print(f"\n{'=' * 60}\n{s}\n{'=' * 60}")
    r = subprocess.run([sys.executable, str(path)], cwd=ROOT.parent)
    if r.returncode != 0:
        print(f"X {s} failed with exit code {r.returncode}")
