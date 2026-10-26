"""build_site.py runs each builder with UTF-8 output and turns a hung step into a FAIL line (audit 2026-10-26)."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import build_site  # noqa: E402


class _Done:
    returncode = 0


def test_builders_get_utf8_output(monkeypatch):
    seen = {}
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: seen.update(kw) or _Done())
    assert build_site._run_step(["x"]) is True
    assert seen["env"]["PYTHONIOENCODING"] == "utf-8" and seen["timeout"] == build_site.STEP_TIMEOUT


def test_a_step_past_the_timeout_fails_without_a_traceback(monkeypatch, capsys):
    def hang(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw["timeout"])
    monkeypatch.setattr(subprocess, "run", hang)
    assert build_site._run_step(["x"]) is False
    assert "stopped" in capsys.readouterr().err
