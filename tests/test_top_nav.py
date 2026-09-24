"""Header: only the active main button carries the ember sparks."""
import re

from builders.site_common import render_top_nav


def test_only_the_active_tab_smoulders():
    html = render_top_nav("changelogs", "patches/7.41.html")
    tabs = re.findall(r'<a class="nav-tab( active)?"[^>]*>(.*?)</a>', html)
    assert tabs, "no nav tabs rendered"
    for active, inner in tabs:
        assert inner.count('class="nav-ember"') == (4 if active else 0), inner
