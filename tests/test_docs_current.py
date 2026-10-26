"""Docs that went stale (audit 2026-10-26) stay current: the rule map knows every rule module, the patch workflow is
tools/new_patch.py, no file names the owner's home folder."""
import subprocess
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*rel):
    with open(os.path.join(ROOT, *rel), encoding="utf-8") as f:
        return f.read()


def test_rule_map_lists_every_rule_module():
    agents = _read("AGENTS.md")
    for name in os.listdir(os.path.join(ROOT, "docs", "agent-rules")):
        if name.endswith(".md"):
            assert f"docs/agent-rules/{name}" in agents, f"AGENTS.md rule map misses {name}"


def test_pipeline_doc_describes_the_current_workflow():
    doc = _read("docs", "agent-rules", "pages-and-pipeline.md")
    assert "tools/new_patch.py" in doc
    assert "кроме dist/patches" not in doc            # the whole dist/ is ignored
    assert "добавить в PATCHES" not in doc             # PATCHES comes from RELEASE_HISTORY


def test_no_tracked_file_names_the_owners_home_folder():
    """A public repo: defaults are ~/…, not C:\\Users\\<owner>\\… (audit 2026-10-26)."""
    r = subprocess.run(["git", "grep", "-l", "-i", "-E", r"users[/\\]+sikle"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode not in (0, 1):
        import pytest
        pytest.skip("not a git checkout")
    assert r.stdout.split() == []


def test_icon_fetcher_does_not_promise_an_onerror_fallback():
    assert "onerror" not in _read("scripts", "fetch", "fetch_icons.py")
