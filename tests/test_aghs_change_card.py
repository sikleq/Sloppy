"""'Aghanim's Shard reworked: …' rows -> an old -> new card of the upgrade under the ability's rows (owner 2026-10-24):
old = the previous patch's game tooltip, new = this patch's, each with the upgrade's own numbers; the row is hidden."""
import os
import sys

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


def test_no_old_tooltip_keeps_the_row(monkeypatch):
    monkeypatch.setattr(at, "aghs_text", lambda slug, kind, v: None if v != "7.41" else "New text.")
    monkeypatch.setattr(_State, "current_ability_slug", "nyx_assassin_vendetta")
    monkeypatch.setattr(_State, "current_patch_version", "7.41")
    monkeypatch.setattr(_State, "aghs_cards", [])
    row = el.li("Aghanim's Shard reworked: Decreases cooldown by 10s", t("REWORK"))
    assert "iab-covered" not in row and el.ul_close() == "</ul>"
