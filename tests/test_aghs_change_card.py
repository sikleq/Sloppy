"""'Aghanim's Shard reworked: …' rows -> an old -> new card of the upgrade under the ability's rows (owner 2026-10-24):
old = the previous patch's game tooltip, new = this patch's, each with the upgrade's own numbers; the row is hidden."""
import os
import re
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
    # owner 2026-10-25: "Added Aghanim's Shard." (NEW), no blue strip on the caption: the card's lines have it
    assert "Added Aghanim&#x27;s Shard." in out or "Added Aghanim's Shard." in out
    assert '<li data-tag="new">' in out


def test_reworked_card_shows_the_old_parts_other_abilities_lost(monkeypatch):
    # owner 2026-10-25, 7.41 Wraith King: the old Shard was also "Reincarnation has no mana cost" — the Mortal Strike
    # card shows it on the old side, each part with its icon + name
    _moved(monkeypatch, ["skeleton_king_mortal_strike", "skeleton_king_reincarnation"],
           ["skeleton_king_mortal_strike"], "skeleton_king_mortal_strike")
    assert "iab-covered" in el.li("Aghanim's Shard reworked: Mortal Strike hits curse their target", t("REWORK"))
    out = el.ul_close()
    old_side = out[out.index("ability-change-old"):out.index("ability-change-arrow")]
    assert "skeleton_king_reincarnation upgrade, old" in old_side and "skeleton_king_mortal_strike upgrade, old" in old_side
    assert old_side.count('class="ac-sub"') == 2 and out.count('class="ac-sub"') == 3
    # a part another ability keeps: not on the old side
    _moved(monkeypatch, ["skeleton_king_mortal_strike", "skeleton_king_reincarnation"],
           ["skeleton_king_mortal_strike", "skeleton_king_reincarnation"], "skeleton_king_mortal_strike")
    el.li("Aghanim's Shard reworked: Mortal Strike hits curse their target", t("REWORK"))
    out = el.ul_close()
    assert "skeleton_king_reincarnation" not in out and 'class="ac-sub"' not in out


def _parts(monkeypatch, old, new, slug, hero="windrunner"):
    """old / new: {ability: upgrade text} of the hero in 7.40c / 7.41."""
    monkeypatch.setattr(at, "holders", lambda h, kind, v: sorted(old if v == "7.40c" else new) if kind == "scepter" else [])
    monkeypatch.setattr(at, "aghs_text", lambda s, kind, v: (old if v == "7.40c" else new).get(s))
    monkeypatch.setattr(at, "ability_name", lambda s, v: s.title())
    monkeypatch.setattr(_State, "current_patch_version", "7.41")
    monkeypatch.setattr(_State, "aghs_part_slug", (slug, hero))
    monkeypatch.setattr(el, "_AGHS_SHOWN", set())


def test_upgrade_gone_to_an_ability_without_a_card_gets_one(monkeypatch):
    # owner 2026-10-25, group A: 7.41 Windrun's Scepter -> Tailwind; the card sits under Tailwind
    _parts(monkeypatch, {"windrun": "Grants invisibility."}, {"tailwind": "Attacks grant Tailwind."}, "tailwind")
    out = el._aghs_parts_cards()
    assert "Added Aghanim's Scepter." in out and "Grants invisibility." in out and "Attacks grant Tailwind." in out
    assert out.count('class="ac-sub"') == 2
    assert el._aghs_parts_cards() == ""                 # drawn once


def test_part_gone_and_the_rest_changed_is_one_reworked_card(monkeypatch):
    # group B: 7.41f Pit of Malice's part gone, Fiend's Gate's -10s -> -20s
    _parts(monkeypatch, {"gate": "Reduces cooldown by 10s.", "pit": "Increases radius."},
           {"gate": "Reduces cooldown by 20s."}, "gate", hero="abyssal_underlord")
    out = el._aghs_parts_cards()
    old_side = out[out.index("ability-change-old"):out.index("ability-change-arrow")]
    assert "Aghanim's Scepter reworked." in out and "Increases radius." in old_side and "iab-hl" in out


def test_part_gone_and_the_rest_the_same_is_a_card_under_the_ability_that_lost_it(monkeypatch):
    # group C: 7.39 Glaives of Wisdom's part gone, Brain Drain's the same. Till 2026-10-26 only the "Removed" row,
    # which read as the hero having no Shard left (owner, 7.40b Necromastery): now the whole old -> what is left
    _parts(monkeypatch, {"drain": "Steals more.", "glaives": "Steal duration."}, {"drain": "Steals more."}, "drain",
           hero="silencer")
    assert el._aghs_parts_cards() == ""                 # not under the ability that kept its part
    monkeypatch.setattr(_State, "aghs_part_slug", ("glaives", "silencer"))
    out = el._aghs_parts_cards()
    old_side = out[out.index("ability-change-old"):out.index("ability-change-arrow")]
    new_side = out[out.index("ability-change-new"):]
    # no caption: the "Removed Aghanim's Scepter." row above says it ("reworked" made one change two rows)
    assert "reworked" not in out and "under-rows-caption" not in out
    assert "Steals more." in old_side and "Steal duration." in old_side
    assert "Steals more." in new_side and "Steal duration." not in new_side
    assert "iab-hl" not in out                          # the kept part is the same: nothing coloured


def test_named_ability_icon_is_downloaded_and_has_a_fallback(monkeypatch):
    # CI icon audit 2026-10-25: Silencer's old Brain Drain has no art; Parting Shot was never downloaded
    monkeypatch.setattr(_State, "ability_icons", set())
    html = el.sub_ability("muerta_parting_shot", "Parting Shot")
    assert "innate_icon.png" in html and any("muerta_parting_shot.png" in u for u in _State.ability_icons)


def test_upgrade_only_added_is_a_new_side_card(monkeypatch):
    # 7.41 Tinker: March of the Machines gets a Scepter part, Laser keeps its own -> no move: "Added" with the new
    # text alone (since 2026-10-25; it was a row before)
    _moved(monkeypatch, ["tinker_laser"], ["tinker_laser", "tinker_march_of_the_machines"], "tinker_march_of_the_machines")
    row = el.li("Aghanim's Scepter: Robots heal allies", t("NEW"))
    assert "iab-covered" in row and "Added Aghanim's Scepter." in el.ul_close()
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


def test_numbers_go_into_the_description_line():
    # owner 2026-10-25: "Increases range. / Range: +150." in one line
    assert el._aghs_inline("Increases range.\nRange: +150.") == "Increases range (+150)."
    assert (el._aghs_inline("Increases Blade Fury radius, and slows enemies by 35%.\nRadius: +100.")
            == "Increases Blade Fury radius (+100), and slows enemies by 35%.")
    # no word of the label in the text: after the description, same line; a number the text says: not twice
    assert el._aghs_inline("Lasts longer.\nDuration: +2.") == "Lasts longer. Duration: +2."
    assert el._aghs_inline("Grants 6 armor to allies.\nPassive bonus armor: 6.") == "Grants 6 armor to allies."


def test_number_highlight_is_a_number_change_not_a_strip():
    html = el.mark_number_highlights(el.hl("45/40/35/30s", "nerf") + " " + el.hl("Dispellable", "nerf"))
    assert 'class="iab-hl iab-hl-nerf iab-hl-num">45/40/35/30s' in html
    assert 'class="iab-hl iab-hl-nerf">Dispellable' in html
    # the new side's number gets the old one's % on hover
    out = el._pair_number_tips(el.hl("20", "del"), el.hl("25", "buff"))
    assert "iab-hl-num" in out and "iab-hint" in out and "+25%" in out


def test_rework_colours_only_changed_numbers_of_the_same_words():
    # owner 2026-10-25: a rewritten meaning stays plain; only a values-only change is coloured, numbers only
    o, n = el._rework_diff_html("Gives 100 bonus radius when cast during Duel.",
                                "Overwhelming Odds has larger radius (+100).")
    assert "iab-hl" not in o and "iab-hl" not in n
    o, n = el._rework_diff_html("Increases radius (+100). Duration: 5s.", "Increases radius (+150). Duration: 5s.")
    assert o == "Increases radius (" + el.hl("+100", "nerf") + "). Duration: 5s."
    assert n == "Increases radius (" + el.hl("+150", "buff") + "). Duration: 5s."
    _, n = el._rework_diff_html("Lowers cooldown (-2s).", "Lowers cooldown (-3s).")
    assert el.hl("-3s", "buff") in n                    # a cooldown: lower is better


def test_huskar_inner_fire_numbers_are_right():
    # owner 2026-10-25: "на сколько снижается кулдаун? почему 10% heal?" — the cooldown has no tooltip label
    # (AbilityCooldown -3) and two labels end in "heal": none of them goes after the word
    line = el._aghs_inline("Lowers Inner Fire cooldown and causes it to apply a movement speed slow and heal Huskar."
                           "\nCooldown: -3s. Movement slow: 50%. Hero damage as heal: 50%. Non-hero damage as heal: 10%.")
    assert line == ("Lowers Inner Fire cooldown (-3s) and causes it to apply a movement speed slow (50%) and heal "
                    "Huskar. Hero damage as heal: 50%. Non-hero damage as heal: 10%.")
    assert at._HEADER_LABELS["abilitycooldown"] == "Cooldown" and at._num("-50%") == "-50%"


def test_old_kv_layout_numbers_are_listed(monkeypatch):
    # owner 2026-10-25: 7.08-7.30 too — "AbilitySpecial" entries marked "RequiresScepter" are the upgrade's numbers
    block = {"AbilitySpecial": {"01": {"var_type": "FIELD_INTEGER", "damage": "100"},
                                "02": {"var_type": "FIELD_INTEGER", "damage_scepter": "200", "RequiresScepter": "1"}},
             "AbilityValues": {"radius": {"value": "700", "RequiresScepter": "1"}}}
    tips = {"dota_tooltip_ability_x_damage_scepter": "SCEPTER DAMAGE:", "dota_tooltip_ability_x_radius": "RADIUS:"}
    lines = at._value_lines(block, "scepter", "x", "7.20", lambda k, v: tips.get(k.lower()))
    assert lines == ["Radius: 700.", "Scepter damage: 200."]


def test_placeholder_from_another_ability_of_the_hero(monkeypatch):
    # 7.22 Nature's Prophet: the Scepter text names values of Nature's Call
    blocks = {"furion_wrath_of_nature": {"AbilityValues": {}},
              "furion_force_of_nature": {"AbilityValues": {"treant_large_hp_bonus": "325"}},
              "lina_dragon_slave": {"AbilityValues": {"treant_large_hp_bonus": "1"}}}
    monkeypatch.setattr(at, "_blocks", lambda v: blocks)
    vals = at._with_kin_values("Treants get %treant_large_hp_bonus% hp.", {}, "furion_wrath_of_nature", "scepter", "7.22h")
    assert vals["treant_large_hp_bonus"] == "325"                 # another hero's ability is never asked


def test_store_has_old_patches_hero_data():
    # 7.08-7.34 had no data/stats/<v>/heroes: the store's npc_abilities.txt is read instead
    from patch.ability_kv import _hero_blocks
    from tools import game_files
    if "7.20" not in game_files.versions():
        pytest.skip("no game-files store here")
    blocks = _hero_blocks("7.20")
    assert "axe_culling_blade" in blocks and sum(1 for b in blocks.values() if b.get("HasScepterUpgrade") == "1") > 50


def test_added_upgrade_is_a_card_and_removed_one_a_row(monkeypatch):
    # owner 2026-10-25: 7.41 Press the Attack's Scepter "не сделано в виде карточки"; a removed one is only the row
    # "Removed Aghanim's Shard." (7.41 Reincarnation: "Хватит просто строки Removed Aghanim's Shard")
    _moved(monkeypatch, ["legion_commander_duel"], ["legion_commander_duel", "legion_commander_press_the_attack"],
           "legion_commander_press_the_attack")
    assert "iab-covered" in el.li("Aghanim's Scepter: Increases bonus movement speed by 12%", t("NEW"))
    out = el.ul_close()
    assert "Added Aghanim's Scepter." in out and "is-single-new" in out and "ability-change-old" not in out
    _moved(monkeypatch, ["legion_commander_duel", "legion_commander_overwhelming_odds"],
           ["legion_commander_overwhelming_odds"], "legion_commander_duel")
    plain = lambda h: re.sub(r"<[^>]+>", "", h)
    row = el.li("No longer upgraded with Aghanim's Shard", t("DEL"))
    # the hero keeps the Shard on Overwhelming Odds: only this ability's part is gone (owner 2026-10-26)
    assert ("iab-covered" not in row and plain(row).endswith("Removed Aghanim's Shard bonus from this ability.")
            and "No longer" not in row)
    assert "ability-change" not in el.ul_close()
    # moved to another ability: the same row
    _moved(monkeypatch, ["arc_warden_spark_wraith"], ["arc_warden_tempest_double"], "arc_warden_spark_wraith")
    row = el.li("No longer upgraded with Aghanim's Shard", t("DEL"))
    assert "iab-covered" not in row and plain(row).endswith("Removed Aghanim's Shard bonus from this ability.")
    # nothing of it left on the hero: the whole upgrade is gone
    _moved(monkeypatch, ["arc_warden_spark_wraith"], [], "arc_warden_spark_wraith")
    row = el.li("No longer upgraded with Aghanim's Shard", t("DEL"))
    assert plain(row).endswith("Removed Aghanim's Shard.")
    # two upgrades in one row stay as the patch note says them (7.40)
    assert "No longer upgraded" in el.li("No longer upgraded with Aghanim's Shard or Aghanim's Scepter", t("DEL"))


def test_a_number_the_text_says_is_not_repeated():
    # 7.41 Arena of Blood: "Lowers cooldown (-10s) by 10s"
    assert el._aghs_inline("Lowers cooldown by 10s.\nCooldown: -10s.") == "Lowers cooldown by 10s."


def test_bonus_placeholder_is_the_upgrades_own_bonus():
    # "%bonus_AbilityCooldown%" / "%bonus_open_wounds_duration_pct%" (7.41 Vendetta, 7.40 Infest)
    vals = at._values({"AbilityValues": {"AbilityCooldown": {"value": "70", "special_bonus_shard": "-10"},
                                         "open_wounds_duration_pct": {"special_bonus_shard": "50"}}}, "shard")
    assert vals["bonus_abilitycooldown"] == "-10" and vals["bonus_open_wounds_duration_pct"] == "50"
