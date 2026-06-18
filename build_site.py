"""Single build entrypoint for the Sloppy static site.

Run:  python build_site.py
      python build_site.py patch creeps   # build only specific pages

Pages are built in dependency order:
  patch   -- index, calendar, and all patch changelogs (writes data/site_meta.json)
  silent  -- silent-changes sub-pages (depends on patch for meta)
  creeps  -- neutral stats + abilities tables
  mana    -- mana items table
  stats   -- hero stats table
  lab     -- hero lab calculator
  hdyn    -- hero dynamics matrix
  idyn    -- item dynamics matrix
  terrain -- terrain comparison
"""

import subprocess
import sys
import time

STEPS = [
    ("patch",   "builders/patch.py",       "Patch pages (index + calendar + changelogs)"),
    ("silent",  "builders/silent.py",       "Silent changes pages"),
    ("creeps",  "builders/creeps.py",       "Neutral Stats / Abilities tables"),
    ("mana",    "builders/mana_items.py",   "Mana Items table"),
    ("stats",   "builders/heroes_stats.py", "Hero Stats table"),
    ("lab",     "builders/hero_lab.py",     "Hero Lab calculator"),
    ("hdyn",    "builders/heroes_dyn.py",   "Hero Dynamics matrix"),
    ("idyn",    "builders/items_dyn.py",    "Item Dynamics matrix"),
    ("terrain", "builders/terrain.py",      "Terrain comparison"),
]

SEP  = "-" * 60
SEP2 = "=" * 60

def main() -> int:
    filter_keys = set(sys.argv[1:])
    steps = [(k, s, d) for k, s, d in STEPS if not filter_keys or k in filter_keys]

    if not steps:
        known = ", ".join(k for k, _, _ in STEPS)
        print(f"Unknown page key(s). Known: {known}", file=sys.stderr)
        return 1

    t0 = time.monotonic()
    failed = []

    for key, script, desc in steps:
        print(f"\n{SEP}")
        print(f"  {desc}")
        print(SEP)
        t = time.monotonic()
        result = subprocess.run([sys.executable, script])
        elapsed = time.monotonic() - t
        status = "OK" if result.returncode == 0 else "FAIL"
        print(f"  [{status}] {elapsed:.1f}s")
        if result.returncode != 0:
            failed.append(desc)

    total = time.monotonic() - t0
    print(f"\n{SEP2}")
    if failed:
        print(f"  FAILED ({len(failed)}/{len(steps)} steps):")
        for f in failed:
            print(f"    x {f}")
        print(f"  Total: {total:.1f}s")
        print(SEP2)
        return 1

    print(f"  All {len(steps)} steps OK -- {total:.1f}s total")
    print(SEP2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
