"""Unit Stats, View: Waves — the lane wave make-up of the current patch (owner 2026-11-26; server.dll 6997, read by
the IDA researcher: thresholds melee {15:00, 45:00}, ranged {35:00}, siege {60:00}; flagbearer replaces a melee)."""
from pathlib import Path

import pytest

from builders import creeps_waves as w

ROOT = Path(__file__).resolve().parents[1]

# wave → (melee, flagbearer, ranged, siege), the researcher's examples
CASES = {
    1: (3, 0, 1, 0), 4: (3, 0, 1, 0), 5: (2, 1, 1, 0), 6: (3, 0, 1, 0), 11: (2, 1, 1, 1), 12: (3, 0, 1, 0),
    30: (3, 0, 1, 0), 31: (3, 1, 1, 1), 32: (4, 0, 1, 0), 60: (4, 0, 1, 0), 61: (3, 1, 1, 1), 62: (3, 1, 1, 0),
    66: (3, 1, 1, 1), 70: (3, 1, 1, 0), 71: (3, 1, 2, 1), 90: (3, 1, 2, 0), 91: (4, 1, 2, 1), 116: (4, 1, 2, 1),
    120: (4, 1, 2, 0), 121: (4, 1, 2, 2), 122: (4, 1, 2, 0), 126: (4, 1, 2, 2),
}


@pytest.mark.parametrize("n,want", sorted(CASES.items()))
def test_wave_make_up_matches_the_game_code(n, want):
    c = w.wave_composition(n)
    assert (c["melee"], c["flag"], c["ranged"], c["siege"]) == want


def test_wave_time_and_step():
    assert [w.wave_time(n) for n in (1, 2, 121)] == [0, 30, 3600]
    assert [w.wave_step(n) for n in (1, 15, 16, 121)] == [0, 0, 1, 8]     # 7:00 → 0, 7:30 → 1, 60:00 → 8
    with pytest.raises(ValueError):
        w.wave_composition(0)


def test_waves_view_on_the_page():
    from builders import creeps
    assert 'value="waves"' in creeps._STATS_TOOLBAR
    # owner 2026-11-26: like Timeline — one row per make-up, the wave sums at every 7:30 step
    kinds = w.wave_kinds()
    assert sum(len(ns) for _c, ns in kinds) == w.LAST_WAVE
    assert len({tuple(c.values()) for c, _ns in kinds}) == len(kinds)
    html = w.waves_table_html({"lane_melee": "icons/units/m.png"})
    assert html.count("<tr data-melee=") == len(kinds)
    assert html.count('class="wv-hp-') == len(kinds) * len(w.STEPS)
    assert '<th class="wv-t" data-cat="wv-hp">60:00</th>' in html      # data-cat: the page sets group colspans
    # the Timeline's stats too (owner 2026-11-26): armor and attack speed as the wave's mean
    assert [k for k, _l in w.WAVE_STATS] == ["hp", "dmg", "gold", "xp"]
    # armor and attack speed do not grow: one "Avg" column each (owner 2026-11-26)
    assert 'class="wv-armor-0 col-sep"' in html and 'class="wv-as-0"' in html
    assert 'wv-armor-1' not in html and 'wv-as-8' not in html and '>Avg</th>' in html
    assert "sum.armor / units" in (ROOT / "src" / "js" / "creeps-upgrade.js").read_text(encoding="utf-8")
    # the Timeline view's look: a .creeps-table with the two-storey head (owner 2026-11-26)
    assert 'class="creeps-table waves-table"' in html and '<tr class="cat-row">' in html and '<tr class="col-row">' in html
    first = kinds[0]
    assert first[0] == {"melee": 3, "flag": 0, "ranged": 1, "siege": 0} and first[1][0] == 1
    js = (ROOT / "src" / "js" / "creeps-upgrade.js").read_text(encoding="utf-8")
    assert "function waves()" in js and "${killed} of ${units} die" in js      # the hint's head
    # any unit, only in its own row: grey and out of that row's sums (owner 2026-11-26)
    assert "tr.dataset.off" in js and "off.has(k)" in js and "siegeOff" not in js
    # the flagbearer's aura leaves with a switched-off flagbearer (2026-11-26)
    assert "Number(tr.dataset.flag) > 0 && !off.has('flag')" in js
    # no Upgrade box in Waves: every step is a column (owner 2026-11-26, tried and taken out again)
    css = (ROOT / "src" / "css" / "creeps-table.css").read_text(encoding="utf-8")
    assert "body.view-waves .upg-group" in css and "wv-cur" not in js
    pinned = (ROOT / "src" / "js" / "creeps-pinned.js").read_text(encoding="utf-8")
    assert "'view-waves'" in pinned
