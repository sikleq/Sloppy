"""pyflakes finds nothing in the project's Python (audit 2026-10-26: 40 findings had piled up — unused locals and
imports, f-strings without placeholders, an undefined NoReturn). patch/api.py and patch/__init__.py re-export the
page API, so their "imported but unused" lines are the point of those files."""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = ["patch", "builders", "tools", "scripts", "tests", "build_site.py", "generate_patch_code_v2.py"]
REEXPORTS = (os.path.join("patch", "api.py"), os.path.join("patch", "__init__.py"))


def _allowed(line):
    path = os.path.normpath(line.split(":", 1)[0])
    return path in REEXPORTS and ("imported but unused" in line or "unable to detect undefined names" in line)


def test_pyflakes_finds_nothing():
    pytest.importorskip("pyflakes")
    targets = [t for t in TARGETS if os.path.exists(os.path.join(ROOT, t))]
    r = subprocess.run([sys.executable, "-m", "pyflakes", *targets], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    found = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.strip() and not _allowed(ln)]
    assert not found, "\n".join(found)
