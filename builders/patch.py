"""
Main build orchestrator — runs all patch + support page generators.
Auto-discovers content/p*.py modules and builds them in chronological order
derived from patch/meta.py RELEASE_HISTORY.
"""
import importlib
import re
import sys
import io
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from patch.meta import RELEASE_HISTORY, _parse_date
from patch.rosters import build_rosters
from patch.calendar import save_calendar_html
from patch.index_page import save_index_html

_STEM_RE = re.compile(r'^p(\d)(\d{2})([a-z]?)$')


def _stem_to_version(stem):
    """p741d → '7.41d', p708 → '7.08'."""
    m = _STEM_RE.match(stem)
    if not m:
        return None
    major, minor, letter = m.group(1), m.group(2), m.group(3)
    return f"{major}.{minor}{letter}"


def _discover_modules():
    """Return content modules sorted oldest-first by RELEASE_HISTORY date."""
    by_date = {p["version"]: _parse_date(p["date"]) for p in RELEASE_HISTORY}
    modules = []
    for path in sorted(Path(_HERE / "content").glob("p*.py")):
        stem = path.stem
        ver = _stem_to_version(stem)
        if ver is None:
            continue
        mod = importlib.import_module(f"content.{stem}")
        if not hasattr(mod, "build"):
            continue
        date = by_date.get(ver)
        modules.append((date, ver, mod))
    modules.sort(key=lambda x: (x[0] or __import__("datetime").date.min, x[1]))
    return modules


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    all_modules = _discover_modules()

    if "--latest" in sys.argv:
        if all_modules:
            _, ver, mod = all_modules[-1]
            mod.build()
    else:
        for _, ver, mod in all_modules:
            mod.build()

        build_rosters()
        save_calendar_html()
        save_index_html()
