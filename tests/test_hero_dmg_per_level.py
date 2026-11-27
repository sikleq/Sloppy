"""Hero Stats Expanded: "Dmg lvl" beside Dmg min / max — the attack damage a level-up adds through attribute gains
(owner 2026-11-27)."""
from pathlib import Path

import pytest

from builders import heroes_stats as hs

ROOT = Path(__file__).resolve().parent.parent
HERO = "npc_dota_hero_axe"


@pytest.fixture(autouse=True)
def restore_version_context():
    previous = hs._CTX_VERSION[0]
    yield
    hs._set_ctx_version(previous)


def snap(primary):
    return {HERO: {"AttributePrimary": primary, "AttributeStrengthGain": 3.4,
                   "AttributeAgilityGain": 2.2, "AttributeIntelligenceGain": 1.6}}


def test_primary_hero_gains_its_primary_attribute_gain():
    hs._set_ctx_version("7.42")
    assert hs._dmg_per_level(snap("DOTA_ATTRIBUTE_STRENGTH"), HERO, {}) == 3.4
    assert hs._dmg_per_level(snap("DOTA_ATTRIBUTE_AGILITY"), HERO, {}) == 2.2


def test_universal_hero_gains_the_multiplier_on_all_three():
    hs._set_ctx_version("7.42")
    assert hs._dmg_per_level(snap("DOTA_ATTRIBUTE_ALL"), HERO, {}) == round(0.45 * 7.2, 2)


def test_column_sits_after_dmg_max_in_expanded():
    keys = [c["key"] for c in hs.COLUMNS]
    assert keys.index("dlvl") == keys.index("dmax") + 1
    col = next(c for c in hs.COLUMNS if c["key"] == "dlvl")
    assert col["mode"] == "extra" and col["label"] == "Dmg\nlvl" and col["cat"] == "attack"
    js = (ROOT / "src" / "js" / "hero-stats.js").read_text(encoding="utf-8")
    assert "case 'dlvl': return [dmgPerLevel(s), g1];" in js
