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
    html = w.waves_table_html({"lane_melee": "icons/units/m.png"})
    assert html.count("<tr data-melee=") == w.LAST_WAVE
    js = (ROOT / "src" / "js" / "creeps-upgrade.js").read_text(encoding="utf-8")
    assert "function waves()" in js and "killed}/${units}" in js
    pinned = (ROOT / "src" / "js" / "creeps-pinned.js").read_text(encoding="utf-8")
    assert "'view-waves'" in pinned
