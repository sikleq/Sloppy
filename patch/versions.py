"""The order of patch versions, in one place (code audit 2026-11-10: twelve sort keys, each a little different, one
crashing on a name that is no version).

Imports nothing of the project: any module may use it.
"""
import re

_VERSION_RE = re.compile(r"(\d+)\.(\d+)([a-z]*)(?:-v(\d+))?")


def version_key(v):
    """'7.36' < '7.36a' < '7.37' < '7.40b': the numbers as numbers, then the letter. A map file Valve shipped inside a
    patch in a client update is keyed '<patch>-v<N>' (the patch's own file is v1) and sorts right after its patch:
    '7.42' < '7.42-v2' < '7.42-v3' < '7.42a' (2026-11-19, the Terrain page picks them). A name that is no version
    (None, a folder of another kind) sorts before every version, by its own text."""
    m = _VERSION_RE.match(v or "")
    if not m:
        return (0, 0, str(v or ""))
    key = (int(m.group(1)), int(m.group(2)), m.group(3))
    return key + (int(m.group(4)),) if m.group(4) else key        # a longer tuple sorts right after its prefix


def map_update(v):
    """'7.42-v3' -> ('7.42', 3); a patch of its own -> (v, None)."""
    m = re.fullmatch(r"(\d+\.\d+[a-z]*)-v(\d+)", v or "")
    return (m.group(1), int(m.group(2))) if m else (v, None)
