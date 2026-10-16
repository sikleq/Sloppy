"""Item card fixes (owner 2026-10-16, 7.41): 5+ level badges as "first … last" (Dagon), a "no longer …" row colours
the one word the old text lost (Refresher Shard "items"), a value kept for one kind of unit is added to the new
description (Crimson Guard "45 … on ranged heroes"), the ability a row starts with wins."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from patch import elements as e  # noqa: E402
from patch.badges import RANGE_FROM_LEVELS, b  # noqa: E402


def test_five_levels_show_first_and_last_only():
    out = b([700, 750, 800, 850, 900], 640)
    assert out.count('class="badge ') == 2 and "badge-range" in out
    assert "-9%" in out and "-29%" in out and "-20%" not in out
    assert 'data-overall="nerf"' in out
    four = b([10, 20, 30, 40], [12, 22, 32, 42])                      # 4 levels (heroes): every level stays
    assert four.count('class="badge ') == 4 and RANGE_FROM_LEVELS == 5


def test_the_ability_a_row_starts_with_wins():
    assert e._iab_row_ability("guard base damage block rescaled from 70", None, {"guard", "damage block"}) == "guard"
    assert e._iab_row_ability("damage block chance increased", None, {"guard", "damage block"}) == "damage block"


def _page(ver):
    p = os.path.join(ROOT, "dist", "patches", f"{ver}.html")
    if not os.path.exists(p):
        pytest.skip("site not built")
    return open(p, encoding="utf-8").read()


def _block(html, item):
    i = html.index(f'id="dyn-item-{item}"')
    return html[i:html.find('class="entity ', i + 50)]


def test_refresher_shard_colours_the_lost_word():
    seg = _block(_page("7.41"), "refresher-shard")
    assert '<span class="iab-hl iab-hl-del" data-tag="del">items</span>' in seg


def test_crimson_guard_gets_the_ranged_value_in_the_card():
    seg = _block(_page("7.41"), "crimson-guard")
    assert "base damage block on ranged heroes</span>" in seg and '<b class="iab-num">45</b>' in seg
