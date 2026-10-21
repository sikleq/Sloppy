"""Materials groups open their Changes page and list it first (owner 2026-10-21)."""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from builders import site_common as site


def test_each_group_opens_its_changes_page_and_lists_it_first():
    groups = {g[0]: g for g in site.MATERIALS_GROUPS}
    for key, page in (("heroes_grp", "hero_changes.html"), ("items_grp", "item_changes.html"),
                      ("creeps_grp", "unit_changes.html")):
        _key, _label, href, children = groups[key]
        assert href == page and children[0][2] == page


def test_materials_tab_opens_unit_changes():
    assert dict((k, h) for k, _l, h in site.NAV_TABS)["materials"] == "unit_changes.html"
    html = site.render_materials_subnav("hero_changes")
    assert html.index('href="hero_changes.html">Hero Changes') < html.index('href="heroes_stats.html">Hero Stats')
