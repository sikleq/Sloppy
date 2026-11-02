"""Shared pytest fixtures for the Sloppy patch-builder test suite.

Three tests that read every patch carry @pytest.mark.slow. CI and the check before a commit run everything (~2 min in
a row, ~40 s with -n auto, 2026-11-02); a quick loop while editing:  python -m pytest -q -n auto -m "not slow"
"""
import importlib
import os
import socket

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: reads every patch (~5-25 s); skipped by -m \"not slow\"")


@pytest.fixture(autouse=True, scope="session")
def project_root():
    """Ensure the working directory is the project root so relative data paths work."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """No test goes online, and an attempt fails the test even when the code swallows the error (audit 2026-11-02:
    the audit_abilities test failed without dota2.com; generate() fetched the previous patch's notes into data/). The
    live checks are .github/workflows/audit-live.yml. Yields the hosts tried, for the test of this very guard."""
    tried = []

    def refuse(host, *args, **kwargs):
        tried.append(host)
        raise OSError(f"a test must not touch the network: {host}")
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    yield tried
    assert not tried, f"this test went online: {tried}"


@pytest.fixture(autouse=True)
def reset_output():
    """Clear H before and after every test so output never bleeds between tests."""
    from patch.output import reset_output as _reset
    _reset()
    yield
    _reset()


@pytest.fixture(autouse=True)
def reset_state():
    """Every _State field and every per-page card cache back to its default between tests (patch/state.py — the
    same reset save_html does after each page, plus the build's totals)."""
    importlib.import_module("patch.elements")  # registers its page caches
    from patch.state import reset_build_state
    reset_build_state()
    yield
    reset_build_state()
