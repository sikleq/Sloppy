"""Hero Lab hides percent rows where both compared heroes sit at 0%.

Owner 2026-11-16: Slow Resist, Spell Amp and the like at 0% on both heroes
only add noise. Armor, both resists and regens always show, even at 0.
"""
import re
from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / "src" / "js" / "hero-lab.js").read_text(encoding="utf-8")

HIDDEN = {
    "Spell Amp": "spellAmp", "Lifesteal": "lifesteal", "Spell Lifesteal": "spellLifesteal",
    "Status Resist": "statusRes", "Slow Resist": "slowRes", "Evasion": "evasion",
    "Health Restoration": "healthRestoration", "Cooldown Reduction": "cooldownReduction",
    "Item CDR": "itemCdr",
}
ALWAYS = ["armor", "armorPct", "mr", "hpr", "mpr"]


def _zero_set():
    m = re.search(r"const HIDE_WHEN_BOTH_ZERO = new Set\(\[([^\]]*)\]\)", JS)
    if not m:
        raise AssertionError("HIDE_WHEN_BOTH_ZERO not found in hero-lab.js")
    return set(re.findall(r"'(\w+)'", m.group(1)))


def test_zero_set_lists_percent_stats_only():
    keys = _zero_set()
    assert keys == set(HIDDEN.values())
    for key in ALWAYS:
        assert key not in keys


def test_hero_panel_rows_pass_their_key():
    for label, key in HIDDEN.items():
        row = re.search(r"statRow\('" + re.escape(label) + r"', .*\n", JS)
        assert row, label
        assert row.group(0).rstrip().endswith(f", '{key}'),"), label


def test_hero_panel_checks_the_other_hero():
    assert "renderTotals(panels[0], a, aState, b);" in JS
    assert "renderTotals(panels[1], b, bState, a);" in JS
    assert "heroLabStatIsZero(key, vals, base, otherVals)" in JS


def test_difference_list_skips_rows_zero_on_both():
    assert "if (HIDE_WHEN_BOTH_ZERO.has(key) && heroLabStatIsZero(key, a, b)) return '';" in JS
