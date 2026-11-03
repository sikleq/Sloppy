"""CI runs the unit tests after `Build site` (audit 2026-10-26): eight tests read dist/ and skip themselves when it is
missing, so before the build they never ran in CI."""
import ast
import glob
import importlib
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGING = {"PIL", "numpy", "scipy", "contourpy"}             # not in requirements-dev.txt: CI skips what needs them


def _imported(node):
    """The top-level libraries a function imports itself (nested functions count)."""
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            out |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module.split(".")[0])
    return out


def _skipped(node):
    """The libraries importorskip names inside this node."""
    return {n.args[0].value.split(".")[0] for n in ast.walk(node)
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "importorskip"
            and n.args and isinstance(n.args[0], ast.Constant)}


def test_a_test_importing_an_imaging_library_skips_itself_without_it():
    # audit 2026-11-02: two rune tests imported Pillow bare, so CI would have failed on them
    bad = []
    for path in glob.glob(os.path.join(ROOT, "tests", "*.py")):
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        at_top = _skipped(tree) - {lib for n in tree.body if isinstance(n, ast.FunctionDef) for lib in _skipped(n)}
        for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
            missing = (_imported(fn) & IMAGING) - _skipped(fn) - at_top
            if missing:
                bad.append(f"{os.path.basename(path)}::{fn.name} {sorted(missing)}")
    assert not bad, f'add pytest.importorskip(...) before the import: {bad}'


@pytest.mark.parametrize("module, test", [
    ("test_runes_and_two_colours", "test_the_power_rune_icon_is_the_generators_bunch_of_three_runes"),
    ("test_runes_and_two_colours", "test_the_terrain_power_layer_button_is_our_power_rune_icon"),
    ("test_terrain_note_parts", "test_cliffs_are_lines_gone_and_new_not_a_stream_bank"),
])
def test_these_tests_skip_without_pillow(module, test, monkeypatch):
    fn = getattr(importlib.import_module(f"tests.{module}"), test)
    monkeypatch.setitem(sys.modules, "PIL", None)         # what `import PIL` meets on a machine without Pillow
    with pytest.raises(pytest.skip.Exception):
        fn()


def _step_names():
    with open(os.path.join(ROOT, ".github", "workflows", "build.yml"), encoding="utf-8") as f:
        return re.findall(r"^\s*- name:\s*(.+?)\s*$", f.read(), re.M)


def test_slow_tests_are_marked_and_ci_still_runs_them(pytestconfig):
    """@pytest.mark.slow is a registered marker for the quick local loop; CI never deselects it (audit 2026-10-26)."""
    assert any(m.startswith("slow:") for m in pytestconfig.getini("markers"))
    with open(os.path.join(ROOT, ".github", "workflows", "build.yml"), encoding="utf-8") as f:
        assert "not slow" not in f.read()


def test_ci_runs_the_tests_in_parallel_with_the_declared_plugin():
    with open(os.path.join(ROOT, ".github", "workflows", "build.yml"), encoding="utf-8") as f:
        assert "python -m pytest tests/ -v -n auto" in f.read()
    with open(os.path.join(ROOT, "requirements-dev.txt"), encoding="utf-8") as f:
        assert "pytest-xdist" in f.read()


def test_unit_tests_run_after_the_build():
    names = _step_names()
    assert names.index("Run unit tests") > names.index("Build site")
