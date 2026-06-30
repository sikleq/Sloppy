"""audit_all.py — Run the full validation pipeline:
   1. audit_heroes.py     — hero_header() display names + icons
   2. audit_items.py      — item_header() display names + ITEM_SLUG + icons
   3. audit_abilities.py  — ability() / ability_change() slugs + names

Run after builders/patch.py before publishing a patch.
"""
import subprocess
import sys
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ["audit_heroes.py", "audit_items.py", "audit_abilities.py"]

failures = []
for s in SCRIPTS:
    print(f"\n{'=' * 60}\n{s}\n{'=' * 60}")
    r = subprocess.run([sys.executable, str(AUDIT_DIR / s)], cwd=str(REPO_ROOT))
    if r.returncode != 0:
        print(f"X {s} failed with exit code {r.returncode}")
        failures.append(s)

if failures:
    print(f"\n{'=' * 60}")
    print(f"FAILED: {', '.join(failures)}")
    sys.exit(1)
