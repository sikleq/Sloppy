"""The site changelog data must stay loadable: valid dates, known categories, existing shots."""
import os

from builders import changelog as clog


def test_changelog_entries_are_valid_and_newest_first():
    entries = clog.load_entries()
    assert entries, "data/changelog.json has no entries"
    dates = [e["date"] for e in entries]
    assert dates == sorted(dates, reverse=True)
    for e in entries:
        assert e["title"], e
        if not e.get("minor"):
            assert e.get("items"), e                        # a feature entry says what it gives
        for shot in e.get("shots", []):
            assert os.path.exists(os.path.join(clog._HERE, shot)), shot


def test_changelog_renders_features_and_small_changes():
    entries = clog.load_entries()
    html = clog.render(entries)
    assert 'class="clog-rail"' in html and 'class="clog-chip active"' in html
    assert html.count('<article class="clog-entry') == sum(1 for e in entries if not e.get("minor"))
    assert html.count('<li data-cat=') >= sum(1 for e in entries if e.get("minor"))


def test_many_small_changes_fold_under_a_toggle():
    few = [{"date": "2026-01-01", "category": "Site", "title": f"x{i}", "minor": True} for i in range(3)]
    many = few + [{"date": "2026-01-01", "category": "Site", "title": "x9", "minor": True}]
    assert "<details" not in clog._minor_html("2026-01-01", few)
    assert "<details" in clog._minor_html("2026-01-01", many)


def test_fixes_carry_the_bug_marker_and_the_rail_lists_only_features():
    entries = [{"date": "2026-01-02", "category": "Site", "title": "Thing", "items": ["x"], "fix": True},
               {"date": "2026-01-02", "category": "Site", "title": "Small", "minor": True, "fix": True},
               {"date": "2026-01-02", "category": "Site", "title": "Other", "minor": True}]
    html = clog.render(entries)
    assert html.count('class="clog-bug"') == 2
    rail = html[html.index('class="clog-rail"'):html.index("</nav>")]
    assert "Thing" in rail and "Small" not in rail and "Smaller changes" not in rail


def test_every_roster_item_gets_a_page_even_without_changes():
    from builders import entity_changes as ec
    dyn = {"items": [{"key": "item|circlet", "name": "Circlet", "icon": "circlet"},
                     {"key": "item|blink", "name": "Blink Dagger", "icon": "blink"}]}
    have = [{"kind": "item", "slug": "blink", "name": "Blink Dagger", "icon": "", "patches": [{"version": "7.41"}]}]
    extra = ec._unchanged_items(have, dyn)
    assert [e["slug"] for e in extra] == ["circlet"] and extra[0]["patches"] == []


def test_a_day_links_to_the_same_page_only_once():
    """Owner 2026-09-26: five entries of one day all linked patches/7.38.html — only the first keeps it."""
    from builders.changelog import _one_link_per_patch
    g = [{"title": "a", "link": "patches/7.38.html"}, {"title": "b", "link": "patches/7.38.html"},
         {"title": "c", "link": "patches/7.39.html"}, {"title": "d"}]
    out = _one_link_per_patch(g)
    assert [e.get("link") for e in out] == ["patches/7.38.html", None, "patches/7.39.html", None]
    assert g[1]["link"] == "patches/7.38.html"          # the data itself is not changed
