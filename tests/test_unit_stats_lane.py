"""Unit Stats (was Neutral Stats) with the lane creeps and the Neutrals / Lane / Summons switches (owner 2026-11-26:
"neutral_stats.html - переименовать в units_stats, добавить lane melee, ranged, siege, flagbearer … чекбоксы
neutrals, lane, summons. по умолчанию включены все. учитывать, как апгрейды применяются на лайновых крипов")."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_lane_creeps_are_rows_after_the_neutrals():
    from builders import creeps
    src = creeps.load_sources()
    rows = creeps.lane_rows(src)
    assert [r["data"]["createhero"] for r in rows] == ["lane_melee", "lane_ranged", "lane_siege", "lane_flagbearer"]
    melee = rows[0]["data"]
    # npc_units.txt 7.42a: 550 HP, 19-23 damage, 2 armor; no camp (owner 2026-11-26: "Camp должен быть с прочерком")
    assert (melee["hp"], melee["dmg_min"], melee["dmg_max"], melee["armor"], melee["camp"]) == \
        ("550", "19", "23", "2", "")
    assert rows[2]["data"]["attack_type"] == "Siege"
    html = creeps._stats_row_html(rows[0], src, {})
    assert 'class="ua-dash"' in html.split('col-camp')[1].split("</td>")[0]


def test_lane_creep_passives_say_what_they_do_from_the_game_values():
    import json
    from builders import creeps_abilities as ua
    cur = json.loads((ROOT / "data" / "stats" / "7.42a" / "npc_abilities.json").read_text(encoding="utf-8"))
    assert ua.abil_props("creep_irresolute", cur)["effect"] == "-25% damage to heroes"
    siege = ua.abil_props("creep_siege", cur)
    assert siege["effect"] == "+150% damage to buildings and siege creeps"
    assert siege["effect2"] == "-50% attack damage from heroes"
    flag = ua.abil_props("flagbearer_creep_aura_effect", cur)
    assert flag["effect"] == "+3 HP regen to allied creeps"
    assert flag["effect2"] == "+4% magic resistance every 7:30, up to 15 times"


def test_every_row_has_a_group_and_lane_rows_their_upgrade_rule():
    from builders import creeps
    from builders.creeps_common import unit_group
    assert unit_group("lane_siege") == "lane" and unit_group("skeleton_warrior") == "summon"
    assert unit_group("kobold") == "neutral"
    src = creeps.load_sources()
    html = creeps._stats_row_html(creeps.lane_rows(src)[1], src, {})
    assert 'data-group="lane"' in html
    upg = json.loads(re.search(r'data-upg="([^"]+)"', html).group(1).replace("&quot;", '"'))
    assert upg == {"hp": 12, "dmg": 2, "gold": 3, "xp": 8, "cap": 30}       # ranged creep per 7:30 step


def test_switches_on_both_pages_start_on():
    from builders import creeps, creeps_abilities
    for bar in (creeps._STATS_TOOLBAR, creeps_abilities._UA_TOOLBAR):
        for key in ("neutral", "lane", "summon"):
            assert re.search(rf'data-unit-group="{key}" checked', bar), key


def test_lane_rows_grow_by_their_own_rule_in_the_script():
    js = (ROOT / "src" / "js" / "creeps-upgrade.js").read_text(encoding="utf-8")
    assert "tr.dataset.group !== 'lane'" in js           # neutrals keep neutral_upgrade
    assert "Math.min(L, u.cap" in js                     # lane HP / damage stop at the cap
    assert "(u.gold || 0) * L" in js and "(u.xp || 0) * L" in js     # gold and XP do not
    pinned = (ROOT / "src" / "js" / "creeps-pinned.js").read_text(encoding="utf-8")
    assert "input[data-unit-group]" in pinned and "mr-group-out" in pinned


def test_old_addresses_lead_to_the_new_pages():
    from builders import creeps, creeps_abilities
    assert "neutral_stats.html" in creeps._STATS_REDIRECT_PAGES
    assert "url=units_stats.html" in creeps._STATS_REDIRECT_HTML
    assert "url=units_abilities.html" in creeps_abilities.UA_REDIRECT_HTML
    from patch import site_common
    nav = repr(site_common.__dict__)
    assert "units_stats.html" in nav and "units_abilities.html" in nav


def test_history_files_carry_the_lane_creeps():
    npc = json.loads((ROOT / "data" / "stats" / "7.08" / "npc_units.json").read_text(encoding="utf-8"))
    assert npc["npc_dota_goodguys_siege"]["StatusHealth"] == "875"      # 935 since 7.27
