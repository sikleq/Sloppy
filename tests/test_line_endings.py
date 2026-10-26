"""LF in the index for every text file (audit 2026-10-26, .gitattributes `* text=auto`); only the game's own texts
(data/*_english.txt) keep the CRLF Valve ships."""
import fnmatch
import os
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        pytest.skip("not a git checkout")
    return r.stdout


def test_no_crlf_in_the_index_but_the_game_texts():
    bad = [ln.split("\t")[-1] for ln in _git("ls-files", "--eol").splitlines()
           if ln.split()[0] in ("i/crlf", "i/mixed") and not fnmatch.fnmatch(ln.split("\t")[-1], "data/*_english.txt")]
    assert not bad, bad


def test_sources_are_text_auto_and_game_texts_untouched():
    out = _git("check-attr", "text", "--", "patch/elements.py", ".gitignore", "data/dota_english.txt")
    attrs = dict(ln.split(": text: ") for ln in out.splitlines())
    assert attrs == {"patch/elements.py": "auto", ".gitignore": "auto", "data/dota_english.txt": "unset"}
