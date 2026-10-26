"""CI runs the unit tests after `Build site` (audit 2026-10-26): eight tests read dist/ and skip themselves when it is
missing, so before the build they never ran in CI."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _step_names():
    with open(os.path.join(ROOT, ".github", "workflows", "build.yml"), encoding="utf-8") as f:
        return re.findall(r"^\s*- name:\s*(.+?)\s*$", f.read(), re.M)


def test_unit_tests_run_after_the_build():
    names = _step_names()
    assert names.index("Run unit tests") > names.index("Build site")
