"""Guards the version picker: every generated patch page must be selectable.

Regression: 7.38 was generated (content/p738.py → patches/7.38.html) but its
RELEASE_HISTORY entry had no `filename`, so PATCHES (and thus the dropdown)
silently dropped it. `filename` is now auto-derived from the content page's
existence; these tests fail loudly if that ever breaks again.
"""
import os
import re
import sys
import pathlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patch.meta import PATCHES, RELEASE_HISTORY

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_STEM_RE = re.compile(r'^p(\d)(\d{2})([a-z]?)$')


def _content_page_versions():
    """Versions that have a content/p*.py patch page on disk."""
    out = set()
    for path in (_ROOT / "content").glob("p*.py"):
        m = _STEM_RE.match(path.stem)
        if m:
            out.add(f"{m.group(1)}.{m.group(2)}{m.group(3)}")
    return out


def test_every_content_page_is_in_the_picker():
    """The exact bug that hid 7.38: a built page missing from PATCHES."""
    picker = {p["version"] for p in PATCHES}
    missing = sorted(_content_page_versions() - picker)
    assert not missing, f"patch pages missing from the version picker: {missing}"


def test_738_is_selectable():
    picker = {p["version"] for p in PATCHES}
    assert "7.38" in picker


def test_picker_entries_point_at_a_real_content_page():
    """No dangling dropdown links: every picked version has a content page."""
    pages = _content_page_versions()
    dangling = sorted(p["version"] for p in PATCHES if p["version"] not in pages)
    assert not dangling, f"picker lists versions with no content/p*.py: {dangling}"


def test_picker_filenames_follow_the_convention():
    for p in PATCHES:
        assert p["filename"] == f"patches/{p['version']}.html", p
