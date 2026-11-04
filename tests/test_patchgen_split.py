"""The generator is cut into tools/patchgen (owner 2026-11-04). The door stays tools/generate_patch_code_v2.py: everything is
reachable through it, the parts stay short, and they import each other one way, so a new rule cannot tie them in a knot."""
import ast
from pathlib import Path

import tools.generate_patch_code_v2 as g

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "tools" / "patchgen"
_LIMIT = 800


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level == 1 and n.module}


def test_the_parts_stay_short_and_the_door_stays_thin():
    for path in PARTS.glob("*.py"):
        assert path.read_text(encoding="utf-8").count("\n") < _LIMIT, path.name
    door = (ROOT / "tools" / "generate_patch_code_v2.py").read_text(encoding="utf-8")
    assert door.count("\n") < 100 and "\ndef " not in door


def test_the_parts_import_each_other_one_way():
    graph = {p.stem: _imports(p) for p in PARTS.glob("*.py")}
    seen, stack = set(), []

    def visit(name):
        assert name not in stack, f"a circle of imports: {stack + [name]}"
        if name in seen:
            return
        stack.append(name)
        for dep in graph.get(name, ()):
            visit(dep)
        stack.pop()
        seen.add(name)
    for name in graph:
        visit(name)


def test_every_part_is_loaded_through_the_door():
    parts = {p.stem for p in PARTS.glob("*.py")} - {"__init__", "cli"}
    assert parts == set(g._PARTS)


def test_every_name_of_every_part_is_reachable_through_the_door():
    for path in PARTS.glob("*.py"):
        if path.stem in ("__init__", "cli"):
            continue
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                assert hasattr(g, node.name), f"{path.stem}.{node.name}"


def test_data_paths_start_at_the_repo_root():
    assert Path(g._HERE) == ROOT
