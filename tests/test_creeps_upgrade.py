"""Owner 2026-11-23: Neutral Stats takes an upgrade number (0-30, a step every 7:30) and shows the stats at it — the
formula of neutral_upgrade read from server.dll 6989 (flat per step; gold min/max alternate)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_the_toolbar_has_the_upgrade_box():
    from builders import creeps
    assert 'id="upgrade-step"' in creeps._STATS_TOOLBAR and 'max="30"' in creeps._STATS_TOOLBAR


def test_the_steps_match_the_games_values():
    js = (ROOT / "src" / "js" / "creeps-upgrade.js").read_text(encoding="utf-8")
    kv = (ROOT / "data" / "stats" / "7.42" / "npc_abilities.txt")
    if kv.exists():
        block = kv.read_text(encoding="utf-8").split('"neutral_upgrade"')[1].split('"AbilityCastAnimation"')[0]
        vals = dict(re.findall(r'"(\w+)"\s+"([\d.]+)"', block))
        assert vals["max_level"] == "30" and vals["increase_time"] == "450"
        for key, js_bit in (("increase_health", "30 * L"), ("increase_armor", "0.5 * L"), ("increase_aspd", "5 * L"),
                            ("increase_damage", "3 * L"), ("increase_xp", "4 * L")):
            assert js_bit.split(" ")[0] == vals[key], key
    for bit in ("30 * L", "0.5 * L", "5 * L", "3 * L", "4 * L", "Math.floor(L / 2)", "Math.floor((L + 1) / 2)",
                "MAX = 30, STEP_S = 450"):
        assert bit in js, bit
