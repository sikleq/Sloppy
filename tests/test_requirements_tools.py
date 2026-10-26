"""Every third-party package a tracked script imports is declared (audit 2026-10-26: requests, numpy, Pillow,
playwright, scipy were used and declared nowhere): the build's and the tests' in requirements-dev.txt, the scripts'
in requirements-tools.txt."""
import ast
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# import name -> pip name, where they differ
PIP_NAME = {"PIL": "pillow", "telethon": "telethon"}
NOT_FROM_PIP = {"bpy", "mathutils",          # Blender's own modules (scripts/gen/render_map_blender.py)
                "lint_tags",                  # the local sloppy-patch skill (.claude/, not in git)
                "pixelstudio"}                # the pixel-art-studio skill (tools/pixel_icons/build.py)


def _declared():
    out = set()
    for name in ("requirements-dev.txt", "requirements-tools.txt"):
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            out |= {re.split(r"[<>=!~\s]", ln.strip(), 1)[0].lower() for ln in f if ln.strip() and ln[0] != "#"}
    return out


def _third_party_imports():
    r = subprocess.run(["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        pytest.skip("not a git checkout")
    files = r.stdout.split()
    own = {os.path.splitext(os.path.basename(f))[0] for f in files} | {f.split("/")[0] for f in files}
    found = {}
    for f in files:
        with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                names = [n.module]
            else:
                continue
            for m in names:
                top = m.split(".")[0]
                if top not in sys.stdlib_module_names and top not in own and not top.startswith("_"):
                    found.setdefault(top, f)
    return found


def test_every_third_party_import_is_declared():
    declared = _declared()
    missing = {m: f for m, f in _third_party_imports().items()
               if m not in NOT_FROM_PIP and PIP_NAME.get(m, m).lower() not in declared}
    assert not missing, f"declare in requirements-tools.txt: {missing}"
