"""Golden snapshot test — catches unintended regressions in built patch HTML.

Compares structural metrics (entity count, tag counts, file size) of a built
patch page against known-good values. If a change is intentional, update the
EXPECTED dict below.
"""
import re
import sys
import os
import pytest
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

PATCH_FILE = _HERE / "dist" / "patches" / "7.41d.html"

# Known-good metrics for 7.41d. Update when patch content changes intentionally.
EXPECTED = {
    "entity_names": 102,
    "badge_buff": 401,
    "badge_nerf": 205,
    "badge_new": 1,
    "badge_del": 5,
    "badge_rework": 2,
    "badge_misc": 3,
}

# Allowed drift: small changes from formatting/whitespace tweaks are OK
SIZE_TOLERANCE = 0.05  # 5%


def _extract_metrics(html):
    return {
        "entity_names": len(re.findall(r'class="entity-name"', html)),
        "badge_buff": html.count("badge buff"),
        "badge_nerf": html.count("badge nerf"),
        "badge_new": html.count("badge new"),
        "badge_del": html.count("badge del"),
        "badge_rework": html.count("badge rework"),
        "badge_misc": html.count("badge misc"),
    }


@pytest.fixture(scope="class")
def metrics():
    html = PATCH_FILE.read_text(encoding="utf-8")
    return _extract_metrics(html)


@pytest.mark.skipif(not PATCH_FILE.exists(), reason="dist/patches/7.41d.html not built")
class TestSnapshot:

    @pytest.mark.parametrize("key", EXPECTED.keys())
    def test_metric(self, metrics, key):
        actual = metrics[key]
        expected = EXPECTED[key]
        assert actual == expected, (
            f"{key}: expected {expected}, got {actual}. "
            f"If intentional, update EXPECTED in test_snapshot.py"
        )
