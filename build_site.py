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

import shutil
import subprocess
import sys
import time
from pathlib import Path


def _minify_assets(dist: Path):
    """Minify CSS and JS files in dist/ (source files untouched)."""
    try:
        import rcssmin
        css = dist / "styles.css"
        if css.exists():
            raw = css.read_text(encoding="utf-8")
            mini = rcssmin.cssmin(raw)
            css.write_text(mini, encoding="utf-8")
            pct = (1 - len(mini) / len(raw)) * 100 if raw else 0
            print(f"  minified styles.css: {len(raw):,} -> {len(mini):,} ({pct:.0f}% smaller)")
    except ImportError:
        print("  [skip] rcssmin not installed -- CSS not minified")
    try:
        import rjsmin
        js = dist / "src" / "scripts.js"
        if js.exists():
            raw = js.read_text(encoding="utf-8")
            mini = rjsmin.jsmin(raw)
            js.write_text(mini, encoding="utf-8")
            pct = (1 - len(mini) / len(raw)) * 100 if raw else 0
            print(f"  minified scripts.js: {len(raw):,} -> {len(mini):,} ({pct:.0f}% smaller)")
    except ImportError:
        print("  [skip] rjsmin not installed -- JS not minified")

STEPS = [
    ("patch",   "builders/build_patches.py",       "Patch pages (index + calendar + changelogs)"),
    ("silent",  "builders/silent.py",       "Silent changes pages"),
    ("creeps",  "builders/creeps.py",       "Neutral Stats / Abilities tables"),
    ("mana",    "builders/mana_items.py",   "Mana Items table"),
    ("stats",   "builders/heroes_stats.py", "Hero Stats table"),
    ("aoe",     "builders/aoe_increase.py", "AoE Increase table"),
    ("lab",     "builders/hero_lab.py",     "Hero Lab calculator"),
    ("hdyn",    "builders/heroes_dyn.py",   "Hero Dynamics matrix"),
    ("idyn",    "builders/items_dyn.py",    "Item Dynamics matrix"),
    ("terrain", "builders/terrain.py",      "Terrain comparison"),
]

# Map: artifact filename -> key of the step that produces it.
_PRODUCERS = {
    "_dynamics.json": "patch",
}

def _build_dependents() -> dict[str, list[str]]:
    """Auto-detect step dependencies by scanning builder scripts for artifact references.

    For each artifact in _PRODUCERS, find every other builder script that
    references that filename — those steps must rebuild whenever the producer runs.
    """
    root = Path(__file__).parent
    step_scripts = {key: root / script for key, script, _ in STEPS}
    result: dict[str, list[str]] = {}
    for artifact, producer_key in _PRODUCERS.items():
        consumers = []
        for key, path in step_scripts.items():
            if key == producer_key:
                continue
            try:
                if artifact in path.read_text(encoding="utf-8"):
                    consumers.append(key)
            except OSError:
                pass
        if consumers:
            result[producer_key] = consumers
    return result

DEPENDENTS = _build_dependents()

SEP  = "-" * 60
SEP2 = "=" * 60

def main() -> int:
    args = sys.argv[1:]
    latest = "--latest" in args
    filter_keys = set(a for a in args if not a.startswith("-"))
    # --latest with no explicit keys: only the patch step (skips creeps/terrain/etc.)
    if latest and not filter_keys:
        filter_keys = {"patch"}
    # Expand filter_keys with any dependents that must rebuild when a dep changes.
    if filter_keys:
        extra = set()
        for key in filter_keys:
            extra.update(DEPENDENTS.get(key, []))
        filter_keys = filter_keys | (extra - filter_keys)
    steps = [(k, s, d) for k, s, d in STEPS if not filter_keys or k in filter_keys]

    if not steps:
        known = ", ".join(k for k, _, _ in STEPS)
        print(f"Unknown page key(s). Known: {known}", file=sys.stderr)
        return 1

    if latest:
        print(f"  [--latest] building only the newest patch page (patch step only)")

    t0 = time.monotonic()
    failed = []

    for key, script, desc in steps:
        print(f"\n{SEP}")
        print(f"  {desc}")
        print(SEP)
        t = time.monotonic()
        cmd = [sys.executable, script]
        if latest and key == "patch":
            cmd.append("--latest")
        result = subprocess.run(cmd, cwd=Path(__file__).parent, timeout=300)
        elapsed = time.monotonic() - t
        status = "OK" if result.returncode == 0 else "FAIL"
        print(f"  [{status}] {elapsed:.1f}s")
        if result.returncode != 0:
            failed.append(desc)

    # Copy static assets into dist/ so local `python -m http.server --directory dist` works.
    # CI does the same in the "Copy static assets" workflow step.
    _root = Path(__file__).parent
    _dist = _root / "dist"
    print(f"\n{SEP}")
    print("  Copying static assets into dist/")
    print(SEP)
    for name in ("styles.css", "_dynamics.json"):
        src = _root / name
        if src.exists():
            shutil.copy2(src, _dist / name)
    for name in ("src", "icons"):
        src = _root / name
        if src.exists():
            dst = _dist / name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    # Minify CSS and JS copies in dist/ (source files stay readable)
    _minify_assets(_dist)
    print("  [OK]")

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
