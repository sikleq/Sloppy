"""The site changelog data must stay loadable: valid dates, known categories, existing shots."""
import os

from builders import changelog as clog


def test_changelog_entries_are_valid_and_newest_first():
    entries = clog.load_entries()
    assert entries, "data/changelog.json has no entries"
    dates = [e["date"] for e in entries]
    assert dates == sorted(dates, reverse=True)
    for e in entries:
        assert e["title"] and e.get("items"), e
        for shot in e.get("shots", []):
            assert os.path.exists(os.path.join(clog._HERE, shot)), shot


def test_changelog_renders_rail_chips_and_entries():
    html = clog.render(clog.load_entries())
    assert 'class="clog-rail"' in html and 'class="clog-chip active"' in html
    assert html.count('<article class="clog-entry') == len(clog.load_entries())
