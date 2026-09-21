"""Guards facet icons: every registered facet must render an icon overlay.

Regression: a generated patch adds facet slugs to patch/badges.py FACETS, but
nothing adds their icon to data/facets_icons.json. patch/elements.py then omits
the <img class="facet-icon-overlay"> silently, so the facet shows only its
colored gradient (7.38's Power Capture and 14 others). These tests fail loudly
when a facet has no icon, or points at an icon PNG that isn't on disk.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from patch.badges import FACETS

with open(os.path.join(_ROOT, "data", "facets_icons.json"), encoding="utf-8") as f:
    _FACET_ICONS = json.load(f)

_ICON_DIR = os.path.join(_ROOT, "icons", "facets")
_ICONS_ON_DISK = {os.path.splitext(n)[0] for n in os.listdir(_ICON_DIR)}


def _icon_name(entry):
    """facets_icons.json stores [color, icon_name]; return icon_name or None."""
    return entry[1] if isinstance(entry, list) and len(entry) > 1 else None


def test_every_registered_facet_has_an_icon():
    """The exact bug: a FACETS slug with no facets_icons.json entry → no overlay."""
    missing = sorted(s for s in FACETS if not _icon_name(_FACET_ICONS.get(s)))
    assert not missing, (
        "facets registered in badges.py with no icon in facets_icons.json "
        f"(add [color, icon_name]): {missing}"
    )


def test_facet_icon_names_point_at_a_real_png():
    """No dangling icon references: every icon_name must exist in icons/facets/."""
    dangling = sorted(
        {n for n in (_icon_name(v) for v in _FACET_ICONS.values())
         if n and n not in _ICONS_ON_DISK}
    )
    assert not dangling, f"icon_name(s) with no PNG in icons/facets/: {dangling}"
