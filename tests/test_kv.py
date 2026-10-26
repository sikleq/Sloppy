"""One Valve KV parser for the whole project, patch/kv.py (audit 2026-10-26: three copies had grown in builders/silent.py,
builders/mana_items.py and tools/fetch_stats.py)."""
import ast
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from patch.kv import _decode_bytes, parse_kv  # noqa: E402

KV = '''// a comment
#base "heroes/npc_dota_hero_x.txt"
"DOTAAbilities"
{
    "Version"   "1"
    "ability_x"
    {
        "AbilityCooldown"   "12 10 8"   // trailing comment
        "Note"  "say \\"hi\\""
        "AbilityCooldown"   "9"
        bare    token
    }
}
'''


def test_parses_blocks_comments_and_includes():
    kv = parse_kv(KV)
    x = kv["DOTAAbilities"]["ability_x"]
    assert kv["DOTAAbilities"]["Version"] == "1"
    assert x["AbilityCooldown"] == "9"                  # a repeated key: the last one wins
    assert x["Note"] == 'say \\"hi\\"' and x["bare"] == "token"


def test_empty_and_odd_input():
    assert parse_kv("") == {} and parse_kv("// only a comment") == {}
    assert parse_kv('"root" { "a" { "b" "1" }') == {"root": {"a": {"b": "1"}}}      # unbalanced braces


def test_decodes_the_encodings_valve_ships():
    assert _decode_bytes(b"\xff\xfe" + '"a" "1"'.encode("utf-16-le")) == '"a" "1"'
    assert _decode_bytes(b"\xef\xbb\xbf\"a\"") == '"a"'


def test_the_project_has_one_kv_parser():
    r = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode:
        pytest.skip("not a git checkout")
    defs = []
    for f in r.stdout.split():
        with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        defs += [f for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("parse_kv", "_tokenize_kv")]
    assert sorted(defs) == ["patch/kv.py", "patch/kv.py"]


def test_kv_module_needs_only_the_standard_library():
    with open(os.path.join(ROOT, "patch", "kv.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    mods = {n.module if isinstance(n, ast.ImportFrom) else a.name
            for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
            for a in (n.names if isinstance(n, ast.Import) else [n])}
    assert all(m.split(".")[0] in sys.stdlib_module_names for m in mods if m), mods
