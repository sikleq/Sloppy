"""Checks inside a pipeline step: an error instead of a silent "0 results" (robust-tests, owner 2026-11-13, from
sqlite.org/testing.html). A plain raise, NOT assert: `python -O` drops every assert and the check silently vanishes.
More helpers (non-empty, same count, in range) live in ~/.claude/skills/robust-tests/templates/checks.py: copy one
here only together with its first caller (tests/test_no_dead_code.py)."""
from __future__ import annotations


class PipelineCheckError(RuntimeError):
    """A pipeline step got an impossible result."""


def ensure(condition: object, message: str) -> None:
    if not condition:
        raise PipelineCheckError(message)
