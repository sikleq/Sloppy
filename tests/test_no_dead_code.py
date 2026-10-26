"""No dead code in the site's library (audit 2026-10-26: _aghs_diff_html, get_latest_version, _abilities_at and copies
of patch/meta.py helpers nested in auto_components_change had no caller): every top-level function and class of patch/
and builders/ is named somewhere besides its own definition."""
import ast
import os
import re
import subprocess
from collections import Counter

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_every_library_function_has_a_caller():
    r = subprocess.run(["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        pytest.skip("not a git checkout")
    src = {}
    for f in r.stdout.split():
        with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
            src[f] = fh.read()
    words = Counter(w for s in src.values() for w in re.findall(r"[A-Za-z_]\w*", s))
    dead = [f"{f}:{n.lineno} {n.name}" for f, s in src.items() if f.startswith(("patch/", "builders/"))
            for n in ast.parse(s).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and words[n.name] <= 1]
    assert not dead, f"no caller (delete it, after a full search for its name): {dead}"
