"""The order of patch versions, in one place (code audit 2026-11-10: twelve sort keys, each a little different, one
crashing on a name that is no version).

Imports nothing of the project: any module may use it.
"""
import re

_VERSION_RE = re.compile(r"(\d+)\.(\d+)([a-z]*)")


def version_key(v):
    """'7.36' < '7.36a' < '7.37' < '7.40b': the numbers as numbers, then the letter. A name that is no version (None,
    a folder of another kind) sorts before every version, by its own text."""
    m = _VERSION_RE.match(v or "")
    return (int(m.group(1)), int(m.group(2)), m.group(3)) if m else (0, 0, str(v or ""))
