"""The GameTracking backup (scripts/fetch/fetch_gametracking.py) fetches the very files extract_patchnotes.py extracts
from the local game, into the same places — the lists are compared without importing the extractor (it needs the
game's VPK library)."""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "fetch"))

import fetch_gametracking as gt  # noqa: E402


def _extractor_lists():
    with open(os.path.join(ROOT, "scripts", "fetch", "extract_patchnotes.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("PATCHNOTES_VPK_PATHS", "STATS_VPK_PATHS", "HEROES_VPK_DIR"):
                out[name] = ast.literal_eval(node.value)
    return out


def test_the_backup_fetches_what_the_local_extractor_extracts():
    lists = _extractor_lists()
    assert gt.PATCHNOTES_VPK_PATHS == lists["PATCHNOTES_VPK_PATHS"]
    assert gt.STATS_VPK_PATHS == lists["STATS_VPK_PATHS"]
    assert gt.HEROES_VPK_DIR == lists["HEROES_VPK_DIR"]


def test_localization_gets_the_games_crlf_back_and_equal_files_are_not_rewritten(tmp_path):
    assert gt.crlf(b"a\nb\r\nc\n") == b"a\r\nb\r\nc\r\n"
    p = tmp_path / "items.txt"
    p.write_bytes(b'"x"\r\n{\r\n}\r\n')
    assert gt._same(p, b'"x"\n{\n}\n') and not gt._same(p, b'"y"\n')
    assert not gt._same(tmp_path / "missing.txt", b"")
