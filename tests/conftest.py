"""Shared pytest fixtures for the Sloppy patch-builder test suite."""
import os
import pytest


@pytest.fixture(autouse=True, scope="session")
def project_root():
    """Ensure the working directory is the project root so relative data paths work."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)


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
    import patch.elements  # noqa: F401  registers its page caches
    from patch.state import reset_build_state
    reset_build_state()
    yield
    reset_build_state()
