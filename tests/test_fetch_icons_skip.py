"""fetch_icons.py never fetches back an icon the owner took out (7.42: it brought back 9, axe_one_man_army among them)."""
import os
import subprocess
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "fetch", "fetch_icons.py")


def _skip_set():
    src = open(SCRIPT, encoding="utf-8").read()
    head = src.split("_SKIP = removed_on_purpose()")[0]          # the module runs the fetch below this line
    mod = types.ModuleType("fetch_icons_head")
    mod.__file__ = SCRIPT
    exec(compile(head, SCRIPT, "exec"), mod.__dict__)
    return mod.removed_on_purpose()


def test_removed_icons_are_skipped():
    if subprocess.run(["git", "rev-parse"], cwd=ROOT, capture_output=True).returncode:
        pytest.skip("not a git checkout")
    skip = _skip_set()
    assert "axe_one_man_army" in skip          # deleted in git history (7.41 rework, unofficial)
    assert "dark_seer_aggrandize" in skip      # KNOWN_INNATE_NO_CDN_ICON
    assert "chaos_knight_armageddon" not in skip


def test_the_skip_is_applied_to_the_fetch_list():
    src = open(SCRIPT, encoding="utf-8").read()
    assert "if s not in _SKIP" in src
