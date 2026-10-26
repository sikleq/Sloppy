"""The Aghanim's texts audit runs by itself (owner 2026-10-25: "Я не буду это сам запускать, генератор должен уметь"):
a build_site.py step for the patches with cards, a CI step for every patch."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import build_site  # noqa: E402


def test_build_runs_the_audit_for_the_site_patches():
    steps = {key: script for key, script, _ in build_site.STEPS}
    assert steps.get("aghs") == "scripts/audit/check_aghs_texts.py --site"


def test_audit_without_the_store_fails_loudly(monkeypatch, capsys):
    """No store: an error with what to do and exit 2, not "0 patches, 0 problem(s)" and exit 0 (audit 2026-10-26)."""
    sys.path.insert(0, os.path.join(ROOT, "scripts", "audit"))
    import check_aghs_texts
    monkeypatch.setattr(check_aghs_texts.game_files, "versions", lambda: frozenset())
    for argv in ([], ["--site"]):
        assert check_aghs_texts.main(argv) == 2
        err = capsys.readouterr().err
        assert "DOTA_FILES_DIR" in err and "0 problem" not in err


def test_ci_runs_the_full_audit():
    with open(os.path.join(ROOT, ".github", "workflows", "build.yml"), encoding="utf-8") as f:
        assert "run: python scripts/audit/check_aghs_texts.py\n" in f.read()
