"""Hero Stats' Starting values follow each patch's attribute rules, not today's (owner 2026-10-22, after PR #14
did the same for HP): armor per Agility, mana per Intelligence, regen, magic resistance from Strength /
Intelligence, movement speed per Agility and the 7.13–7.20 +25% primary bonus."""
import pytest

from builders import heroes_stats as hs

HERO = "npc_dota_hero_test"


@pytest.fixture(autouse=True)
def restore_version_context():
    previous = hs._CTX_VERSION[0]
    yield
    hs._set_ctx_version(previous)


def snap(primary):
    return {HERO: {
        "AttributePrimary": primary, "AttributeBaseStrength": 20, "AttributeBaseAgility": 20,
        "AttributeBaseIntelligence": 20, "StatusHealth": 200, "StatusHealthRegen": 1.0, "StatusMana": 75,
        "StatusManaRegen": 1.0, "ArmorPhysical": 0, "MagicalResistance": 25, "MovementSpeed": 300,
    }}


AGI, STR, INT = "DOTA_ATTRIBUTE_AGILITY", "DOTA_ATTRIBUTE_STRENGTH", "DOTA_ATTRIBUTE_INTELLECT"


@pytest.mark.parametrize("version, primary, armor", [
    ("7.12", AGI, 3.4),      # 0.17 per Agility
    ("7.13", AGI, 4.0),      # 0.16 x 1.25 for an Agility hero
    ("7.13", STR, 3.2),
    ("7.21", AGI, 3.2),
    ("7.27", AGI, 3.3),      # 1/6
])
def test_armor(version, primary, armor):
    hs._set_ctx_version(version)
    assert hs._armor_l1(snap(primary), HERO, {}) == armor


@pytest.mark.parametrize("version, primary, mr", [
    ("7.12", STR, 28.0),     # Intelligence gave 0.15%
    ("7.13", STR, 27.0),     # Strength 0.08% x 1.25 for a Strength hero, Intelligence nothing
    ("7.13", AGI, 26.6),
    ("7.26", STR, 25.0),     # neither
    ("7.33", STR, 27.0),     # Intelligence 0.1%
])
def test_magic_resistance(version, primary, mr):
    hs._set_ctx_version(version)
    assert hs._mr_l1(snap(primary), HERO, {}) == mr


def test_attribute_headers_carry_their_rule_history(monkeypatch):
    # owner 2026-10-22: hovering STR / AGI / INT / Attr shows what one point gave by patch; a new history row
    # in patch/game_constants.py appears there by itself
    from patch import game_constants as gc
    agi = gc.attribute_history("agi")
    assert "7.27|28.06.2020|F|Armor|0.16|0.167|hi" in agi
    assert gc.attribute_today("str") == ('Per Strength<span class="tip-now">22 HP</span>'
                                         '<span class="tip-now">0.1 HP regen</span>')
    # one value per line: the long "attr" header made the window too wide (owner 2026-10-23)
    assert gc.attribute_today("attr").count('class="tip-now"') == 2
    monkeypatch.setitem(gc.ATTRIBUTE_RULES, "agi", gc.ATTRIBUTE_RULES["agi"]
                        + (("Test", (("7.42", "01.01.2027", 0, 1),), ""),))
    assert gc.attribute_history("agi").endswith("7.42|01.01.2027|F|Test|0|1|hi")
    head = hs._attr_hist("int")
    assert 'data-name="Per Intelligence&lt;span class=&quot;tip-now&quot;&gt;12 Mana' in head and "7.33|20.04.2023|F|Magic resistance|0%|0.1%" in head


def test_mana_regen_and_speed_before_and_after_the_rules_changed():
    hs._set_ctx_version("7.13")
    assert hs._mp_l1(snap(INT), HERO, {}) == 75 + 20 * 15                     # 12 x 1.25
    assert hs._mpreg_l1(snap(AGI), HERO, {}) == pytest.approx(round(1.0 * (1 + 20 * 1.8 / 100), 2))
    assert hs._hpreg_l1(snap(STR), HERO, {}) == pytest.approx(round(1.0 * (1 + 20 * 0.6875 / 100), 2))
    assert hs._ms_l1(snap(AGI), HERO, {}) == round(300 * (1 + 20 * 0.0625 / 100))
    hs._set_ctx_version("7.26")
    assert hs._mpreg_l1(snap(INT), HERO, {}) == pytest.approx(1.0 + 20 * 0.05)
    assert hs._ms_l1(snap(AGI), HERO, {}) == 300
