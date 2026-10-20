"""The GitHub token of tools/fetch_stats.py and scripts/fetch/extract_patchnotes.py: SLOPPY_GITHUB_TOKEN first, else
the GitHub CLI's own login (`gh auth token`), never a token written in a file (owner 2026-10-20: a token sat in plain
text in a script outside the repo)."""
import importlib.util
import os
import subprocess

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = [os.path.join(_ROOT, "tools", "fetch_stats.py"), os.path.join(_ROOT, "scripts", "fetch", "extract_patchnotes.py")]


def _module(path):
    spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(path))[0], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(params=_SCRIPTS, ids=["fetch_stats", "extract_patchnotes"])
def mod(request):
    return _module(request.param)


def _gh_answers(monkeypatch, mod, returncode=0, stdout="", raises=None):
    calls = []

    def fake_run(argv, **kw):
        calls.append(argv)
        if raises:
            raise raises
        return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr="")
    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    return calls


def test_the_environment_variable_wins_and_gh_is_not_asked(monkeypatch, mod):
    monkeypatch.setenv("SLOPPY_GITHUB_TOKEN", "from-env")
    calls = _gh_answers(monkeypatch, mod, stdout="from-gh\n")
    assert mod.github_token() == "from-env" and calls == []


def test_without_the_variable_the_gh_login_is_used(monkeypatch, mod):
    monkeypatch.delenv("SLOPPY_GITHUB_TOKEN", raising=False)
    calls = _gh_answers(monkeypatch, mod, stdout="from-gh\n")
    assert mod.github_token() == "from-gh" and calls == [["gh", "auth", "token"]]


@pytest.mark.parametrize("answer", [{"returncode": 1, "stdout": "not logged in"}, {"raises": FileNotFoundError()},
                                    {"raises": subprocess.TimeoutExpired("gh", 15)}])
def test_no_variable_and_no_gh_login_gives_an_empty_token(monkeypatch, mod, answer):
    monkeypatch.delenv("SLOPPY_GITHUB_TOKEN", raising=False)
    _gh_answers(monkeypatch, mod, **answer)
    assert mod.github_token() == ""


@pytest.mark.parametrize("path", _SCRIPTS, ids=["fetch_stats", "extract_patchnotes"])
def test_no_script_carries_a_token(path):
    text = open(path, encoding="utf-8").read()
    assert "github_pat_11" not in text and "ghp_" not in text
