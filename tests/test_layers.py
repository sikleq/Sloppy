"""patch/ is the core: it never imports builders/ or tools/ (audit 2026-10-26 #6). Before, patch/ reached up into
builders.site_common (which imported builders.terrain lazily — a cycle) and into tools.game_files / loc_history /
item_ability_text; those now live in patch/ and tools/ keeps only command lines."""
import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPPER = ("builders", "tools", "scripts", "content")


def _imports(path):
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):                          # every level: an import inside a function counts too
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module


def test_patch_imports_nothing_above_it():
    bad = []
    for name in sorted(os.listdir(os.path.join(ROOT, "patch"))):
        if name.endswith(".py"):
            bad += [f"patch/{name}: {m}" for m in _imports(os.path.join(ROOT, "patch", name))
                    if m.split(".")[0] in UPPER]
    assert not bad, "\n".join(bad)


def test_tools_game_files_is_only_the_command_line():
    with open(os.path.join(ROOT, "tools", "game_files.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    assert not [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    assert "patch.game_files" in set(_imports(os.path.join(ROOT, "tools", "game_files.py")))


def test_moved_modules_are_gone_from_their_old_homes():
    for old in ("builders/site_common.py", "builders/map_versions.py", "tools/loc_history.py",
                "tools/item_ability_text.py", "generate_patch_code_v2.py"):
        assert not os.path.exists(os.path.join(ROOT, old)), old


def test_the_generator_runs_from_tools_and_reads_the_repo_root():
    """generate_patch_code_v2.py moved from the repo root to tools/ (audit 2026-10-26): its data paths still start at
    the root, and it starts as a script."""
    import subprocess
    import sys
    import tools.generate_patch_code_v2 as g
    assert os.path.samefile(g._HERE, ROOT)
    r = subprocess.run([sys.executable, os.path.join("tools", "generate_patch_code_v2.py")], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode != 0 and "Usage: python tools/generate_patch_code_v2.py" in r.stderr
