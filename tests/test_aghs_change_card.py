"""'Aghanim's Shard reworked: …' rows -> an old -> new card of the upgrade under the ability's rows (owner 2026-10-24):
old = the previous patch's game tooltip, new = this patch's, each with the upgrade's own numbers; the row is hidden."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patch import aghs_text as at  # noqa: E402
from patch import elements as el  # noqa: E402
from patch.badges import t  # noqa: E402
from patch.state import _State  # noqa: E402

LABELS = {"dota_tooltip_ability_x_radius": "RADIUS:", "dota_tooltip_ability_x_shield_pct": "%DAMAGE TO BARRIER:",
          "dota_tooltip_ability_x_armor": "PASSIVE BONUS ARMOR:"}


def _tip(key, version):
    return LABELS.get(key.lower())


def test_upgrade_numbers_are_listed_like_the_game():
    block = {"AbilityValues": {"radius": {"value": "600", "special_bonus_shard": "+100"},
                               "shield_pct": {"special_bonus_shard": "+50", "RequiresShard": "1"},
                               "armor": {"value": "0", "special_bonus_shard": "+0"},
                               "nolabel": {"special_bonus_shard": "5"}}}
    lines = at._value_lines(block, "shard", "x", "7.41", _tip)
    # a bonus on a base value keeps its sign; an upgrade-only value is bare; "+0" and unlabelled ones are left out
    assert lines == ["Radius: +100.", "Damage to barrier: 50%."]


def test_a_decrease_never_says_minus():
    assert at._DECREASE_RE.sub(r"\1", "Decreases cooldown by -2s.") == "Decreases cooldown by 2s."
    assert at._DECREASE_RE.sub(r"\1", "Deals -2 armor.") == "Deals -2 armor."


def test_numbers_line_is_compared_by_label():
    vo, vn = el._aghs_values_html("Bonus speed: +3%. Passive radius: 1200.", "Bonus speed: +3%. Radius: +200.")
    assert vo == "Bonus speed: +3%. " + el.hl("Passive radius: 1200", "del") + "."
    assert vn == "Bonus speed: +3%. " + el.hl("Radius: +200", "new") + "."
    vo, vn = el._aghs_values_html("Duration: 5.", "Duration: 6.")
    assert vn == "Duration: " + el.hl("6", "rework") + "."


def test_row_becomes_a_hidden_card(monkeypatch):
    texts = {"7.40c": "Gives 100 bonus radius when cast during Duel.\nRadius bonus in duel: 100.",
             "7.41": "Overwhelming Odds has larger radius.\nRadius: +100."}
    monkeypatch.setattr(at, "aghs_text", lambda slug, kind, v: texts.get(v))
    monkeypatch.setattr(_State, "current_ability_slug", "legion_commander_overwhelming_odds")
    monkeypatch.setattr(_State, "current_patch_version", "7.41")
    monkeypatch.setattr(_State, "aghs_cards", [])
    row = el.li("Aghanim's Shard reworked: Increases radius by 100", t("REWORK"))
    assert "iab-covered" in row
    out = el.ul_close()
    assert out.startswith("</ul>") and 'class="ability-change unified-panes aghs-change"' in out
    assert "aghanim-shard" in out and "Gives" in out and "Overwhelming Odds has larger" in out
    assert _State.aghs_cards == []


def test_no_old_tooltip_stops_the_build(monkeypatch):
    # owner 2026-10-24: "ты всегда должен знать, как было и как стало" — no row is left without its card
    monkeypatch.setattr(at, "aghs_text", lambda slug, kind, v: None if v != "7.41" else "New text.")
    monkeypatch.setattr(_State, "current_ability_slug", "nyx_assassin_vendetta")
    monkeypatch.setattr(_State, "current_patch_version", "7.41")
    monkeypatch.setattr(_State, "aghs_cards", [])
    with pytest.raises(RuntimeError, match="no 7.40c text"):
        el.li("Aghanim's Shard reworked: Decreases cooldown by 10s", t("REWORK"))


def _moved(monkeypatch, old_h, new_h, slug):
    monkeypatch.setattr(at, "holders", lambda hero, kind, v: old_h if v == "7.40c" else new_h)
    monkeypatch.setattr(at, "aghs_text", lambda s, kind, v: f"{s} upgrade, {'old' if v == '7.40c' else 'new'}.")
    monkeypatch.setattr(at, "ability_name", lambda s, v: s.title())
    monkeypatch.setattr(_State, "current_hero", "arc_warden")
    monkeypatch.setattr(_State, "current_ability_slug", slug)
    monkeypatch.setattr(_State, "current_patch_version", "7.41")
    monkeypatch.setattr(_State, "aghs_cards", [])


def test_upgrade_moved_to_another_ability_becomes_a_card(monkeypatch):
    # owner 2026-10-25: 7.41 Arc Warden's Shard moved from Spark Wraith to Tempest Double
    _moved(monkeypatch, ["arc_warden_spark_wraith"], ["arc_warden_tempest_double"], "arc_warden_tempest_double")
    row = el.li("Aghanim's Shard: The Tempest Double is infused with the bonuses of runes", t("NEW"))
    assert "iab-covered" in row
    out = el.ul_close()
    assert "arc_warden_spark_wraith upgrade, old" in out and "arc_warden_tempest_double upgrade, new" in out
    assert out.count('class="ac-sub"') == 2                       # whose upgrade: icon + name on both sides
    assert "iab-hl" not in out                                    # two abilities: no word diff


def test_upgrade_only_added_stays_a_row(monkeypatch):
    # 7.41 Tinker: March of the Machines gets a Scepter part, Laser keeps its own -> no move, no card
    _moved(monkeypatch, ["tinker_laser"], ["tinker_laser", "tinker_march_of_the_machines"], "tinker_march_of_the_machines")
    row = el.li("Aghanim's Scepter: Robots heal allies", t("NEW"))
    assert "iab-covered" not in row and _State.aghs_cards == []
    # 7.38 Slardar: the part lives in Seaborn Sentinel's text, Corrosive Haze holds no upgrade by the game's flags
    _moved(monkeypatch, ["slardar_scepter"], ["slardar_seaborn_sentinel"], "slardar_amplify_damage")
    assert "iab-covered" not in el.li("Aghanim's Scepter: Increases trail duration", t("NEW"))


def test_granted_ability_text_and_upgrade_bonus_placeholders():
    blk = {"IsGrantedByShard": "1"}
    assert at._granted(blk, "shard") and not at._granted(blk, "scepter")
    assert at._granted({"AbilityValues": {"enabled": {"value": "0", "special_bonus_scepter": "+1"}}}, "scepter")
    vals = at._values({"AbilityCastRange": "700", "AbilityValues": {
        "bonus_spell_damage": {"value": "0", "special_bonus_shard": "+25"}}}, "shard")
    assert vals["shard_bonus_spell_damage"] == "25" and vals["abilitycastrange"] == "700"   # 7.37 Lina, 7.41 Gyro


def test_bonus_placeholder_is_the_upgrades_own_bonus():
    # "%bonus_AbilityCooldown%" / "%bonus_open_wounds_duration_pct%" (7.41 Vendetta, 7.40 Infest)
    vals = at._values({"AbilityValues": {"AbilityCooldown": {"value": "70", "special_bonus_shard": "-10"},
                                         "open_wounds_duration_pct": {"special_bonus_shard": "50"}}}, "shard")
    assert vals["bonus_abilitycooldown"] == "-10" and vals["bonus_open_wounds_duration_pct"] == "50"
