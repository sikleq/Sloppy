"""Build products live in .cache/, terrain diffs in data/terrain/ (2026-10-24): nothing writes or reads the old places."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import build_site  # noqa: E402

_PRODUCTS = ("_dynamics.json", "_ability_icons.txt")
_CODE_DIRS = ("builders", "patch", "tools", "scripts")


def _code_files():
    yield os.path.join(ROOT, "build_site.py")
    for d in _CODE_DIRS:
        for r, _, fs in os.walk(os.path.join(ROOT, d)):
            yield from (os.path.join(r, f) for f in fs if f.endswith(".py"))


def test_every_path_to_a_build_product_goes_through_dot_cache():
    bad = []
    for p in _code_files():
        with open(p, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                for name in _PRODUCTS:
                    # a quoted file name used as a path (not the dist/ name in a dict key or a docstring mention)
                    if re.search(rf"""['"]{re.escape(name)}['"]\s*[),]""", line) and not re.search(r"[._]cache", line):
                        bad.append(f"{os.path.relpath(p, ROOT)}:{n}")
    assert bad == []


def test_the_patch_step_still_rebuilds_the_pages_that_read_dynamics():
    assert {"lab", "hdyn", "idyn", "echg"} <= set(build_site.DEPENDENTS["patch"])


def test_terrain_diffs_sit_in_data_terrain_only():
    data = os.path.join(ROOT, "data")
    assert not [f for f in os.listdir(data) if f.startswith("terrain_diff_")]
    assert [f for f in os.listdir(os.path.join(data, "terrain")) if f.startswith("terrain_diff_")]
