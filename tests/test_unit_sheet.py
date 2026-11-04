"""Owner 2026-11-04, 7.38: new and returning units as the game shows them (variant 3 of the mock), their numbers from the
game's files; a returning unit's changes in the tiles."""
import html as _html
import os
import re

import pytest

from patch import game_files, unit_numbers as us
from patch.badges import b, br, t
from patch.elements import camp_table
from patch.static_has import add_static_has_classes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_UNITS = '''"DOTAUnits"
{
	"npc_dota_units_base"
	{
		"Level"		"1"
		"StatusHealth"		"150"
		"StatusHealthRegen"		"0"
		"StatusMana"		"0"
		"StatusManaRegen"		"0"
		"ArmorPhysical"		"0"
		"MagicalResistance"		"0"
		"AttackDamageMin"		"1"
		"AttackDamageMax"		"1"
		"AttackRate"		"1.7"
		"BaseAttackSpeed"		"100"
		"AttackAnimationPoint"		"0.75"
		"AttackRange"		"600"
		"AttackAcquisitionRange"		"800"
		"MovementSpeed"		"300"
		"MovementTurnRate"		"0.5"
		"VisionDaytimeRange"		"575"
		"VisionNighttimeRange"		"575"
		"BountyGoldMin"		"0"
		"BountyGoldMax"		"0"
		"BountyXP"		"0"
	}
	"npc_dota_neutral_frog"
	{
		"Level"		"4"
		"StatusHealth"		"700"
		"StatusHealthRegen"		"0.5"
		"StatusMana"		"300"
		"StatusManaRegen"		"1.0"
		"AttackDamageMin"		"22"
		"AttackDamageMax"		"24"
		"BountyGoldMin"		"25"
		"BountyGoldMax"		"29"
		"BountyXP"		"42"
		"VisionDaytimeRange"		"800"
		"VisionNighttimeRange"		"400"
	}
	"npc_dota_neutral_nomana"
	{
		"StatusHealth"		"100"
	}
}
'''


def html_in_a_list(li_html):
    return f'<ul class="changes">{li_html}</ul>'


def _read(*path):
    with open(os.path.join(ROOT, *path), encoding="utf-8") as f:
        return f.read()


def test_numbers_come_from_the_unit_and_the_base_fills_what_it_omits():
    nums = us.numbers(_UNITS, "npc_dota_neutral_frog")
    assert nums["Health"] == "700" and nums["Mana Regen"] == "1" and nums["Damage"] == "22-24"
    assert nums["Gold"] == "25-29" and nums["XP"] == "42" and nums["Level"] == "4"
    assert nums["Turn Rate"] == "0.5" and nums["BAT"] == "1.7s" and nums["Magic Res"] == "0%"
    assert nums["Vision"] == "800/400"


def test_a_unit_the_patch_does_not_have_stops_the_build():
    with pytest.raises(ValueError, match="npc_dota_neutral_ghost"):
        us.numbers(_UNITS, "npc_dota_neutral_ghost")


def test_a_new_unit_has_bars_tiles_and_the_new_filter():
    html = us.render(us.numbers(_UNITS, "npc_dota_neutral_frog"))
    assert '<li class="unit-sheet" data-tag="buff new">' in html
    assert 'us-bar us-hp' in html and 'us-bar us-mp' in html and '<span class="us-regen">+0.5</span>' in html
    assert len(re.findall(r'class="us-tile[ "]', html)) == len(us.TILES) == 14
    assert "li-notext" not in add_static_has_classes(html_in_a_list(html))      # no tag chip of its own beside the bars
    assert '<span class="us-tile us-gold">' in html and '<span class="us-tile us-xp">' in html


def test_a_unit_without_mana_has_no_mana_bar():
    assert "us-mp" not in us.render(us.numbers(_UNITS, "npc_dota_neutral_nomana"))


def test_a_changed_number_is_the_new_one_coloured_and_dotted_the_old_on_hover():
    nums = us.numbers(_UNITS, "npc_dota_neutral_frog")
    html = us.render(nums, changes={"Health": (600, b(600, 700)), "Gold": ("52-58", br(52, 58, 25, 29)), "Level": (5, t("MISC"))})
    plain = _html.unescape(html)
    assert '<b class="us-v iab-buff"><span class="iab-hint abil-ico-hint" data-tooltip="' in html
    assert '600 \u2192 700 <span class="iab-num iab-buff">(+17%)</span>' in plain      # the % in the tag's colour
    assert '52-58 \u2192 25-29 <span class="iab-num iab-nerf">(-' in plain
    assert '<b class="us-v"><span class="iab-hint abil-ico-hint" data-tooltip="5 \u2192 4">4</span></b>' in html  # a text tag has no %
    tags = re.search(r'data-tag="([^"]+)"', html).group(1).split()
    assert {"buff", "nerf", "misc"} <= set(tags) and "new" not in tags


def test_the_sheet_has_no_tag_chips_but_keeps_its_tags_for_filters():
    nums = us.numbers(_UNITS, "npc_dota_neutral_frog")
    for html in (us.render(nums), us.render(nums, changes={"Health": (600, b(600, 700)), "Gold": ("52-58", br(52, 58, 25, 29))})):
        assert 'class="badge' not in html and "us-chips" not in html
    assert 'data-tag="buff new"' in us.render(nums)
    assert re.search(r"ul\.changes li\.unit-sheet \{\s*display: grid; grid-template-columns: 130px", _read("styles.css"))  # short bars


def test_the_rows_under_the_sheet_keep_the_patch_cells_counted():
    src = _read("content", "p738.py").replace("\r\n", "\n")
    start = src.index('W(unit_header("Ancient Prowler Acolyte"')
    block = src[start:src.index("W(ul_close())", start)]
    assert 'W(li("Health increased from 600 to 750", b(600, 750), covered=True))' in block


def test_a_tile_that_does_not_exist_stops_the_build():
    with pytest.raises(ValueError, match="Mana Cost"):
        us.render(us.numbers(_UNITS, "npc_dota_neutral_frog"), changes={"Mana Cost": (1, b(1, 2))})


def test_gold_and_xp_have_the_colours_of_the_creeps_table():
    css = _read("styles.css")
    gold = re.search(r"([^{}]*\.creeps-table td\.col-gold[^{]*)\{ color: #e3b341; \}", css).group(1)
    xp = re.search(r"([^{}]*\.creeps-table td\.col-xp[^{]*)\{ color: #8bb8d6; \}", css).group(1)
    assert ".us-gold .us-v" in gold and ".camp-table .camp-gold" in gold
    assert ".us-xp .us-v" in xp and ".camp-table .camp-xp" in xp


def test_the_name_is_centred_on_the_icon_when_nothing_else_stands_beside_it():
    css = _read("styles.css")
    rule = re.search(r"\.ability-block\.ab-card-only > \.ability-title \{([^}]*)\}", css).group(1)
    assert "align-self: center" in rule and "grid-row: 1" in rule
    assert ".ability-block.ab-card-only > .ability-icon-wrap { grid-row: 1; }" in css
    html = add_static_has_classes('<div class="ability-block"><h4 class="ability-title">Aura</h4><ul class="changes ability-card-rows"><li>x</li></ul></div>')
    assert "ab-card-only" in html
    plain = add_static_has_classes('<div class="ability-block"><h4 class="ability-title">Aura</h4><ul class="changes"><li>x</li></ul></div>')
    assert "ab-card-only" not in plain


def test_camps_show_gold_and_xp_in_columns_and_no_question_mark():
    html = camp_table([("Small camp", [(3, "Pollywog", "a.png")], 54, 90), ("Medium camp", [(2, "Boglet", "b.png"), (1, "Mage", "c.png")], 81, 126)])
    assert "info-tip" not in html and "--camp-cols:4" in html
    assert '<span class="camp-cell camp-num camp-gold">54</span><span class="camp-cell camp-num camp-xp">90</span>' in html
    assert "Average Gold" in html and "Average XP" in html and "grid-column: span 2" in html


def test_every_new_unit_of_the_content_has_its_sheet():
    src = _read("content", "p738.py")
    assert "new_stats" not in src
    heads = list(re.finditer(r'W\(unit_header\("([^"]+)", [^\n]*new="New [^\n]*\n', src))
    assert len(heads) == 7
    for m in heads:
        assert src[m.end():].lstrip().startswith("W(ul_open())\n    W(unit_sheet(".replace("\n", os.linesep)) or \
            re.match(r"\s*W\(ul_open\(\)\)\s+W\(unit_sheet\(", src[m.end():]), m.group(1)


def test_returning_prowlers_tell_the_changes_in_the_tiles_and_keep_valves_rows():
    src = _read("content", "p738.py")
    for unit, rows in (("Ancient Prowler Acolyte", 7), ("Ancient Prowler Shaman", 8)):
        start = src.index(f'W(unit_header("{unit}"')
        block = src[start:src.index("W(ul_close())", start)]
        assert "general=False" in block and "W(unit_sheet(" in block
        assert block.count("covered=True") == rows


@pytest.mark.skipif(not game_files.available(), reason="no game-files store")
def test_the_real_numbers_of_7_38_match_valves_rows():
    text = game_files.read("7.38", "scripts/npc/npc_units.txt")
    acolyte = us.numbers(text, "npc_dota_neutral_prowler_acolyte")
    assert (acolyte["Health"], acolyte["XP"], acolyte["BAT"], acolyte["Attack Speed"], acolyte["Attack Point"],
            acolyte["Turn Rate"], acolyte["Gold"]) == ("750", "95", "2s", "135", "0.3s", "0.9", "37-43")
    shaman = us.numbers(text, "npc_dota_neutral_prowler_shaman")
    assert (shaman["Level"], shaman["Health"], shaman["XP"], shaman["Gold"]) == ("6", "1400", "124", "76-80")
    frog = us.numbers(text, "npc_dota_neutral_froglet")
    assert (frog["Health"], frog["Damage"], frog["Move Speed"], frog["Turn Rate"]) == ("700", "22-24", "290", "0.5")


def test_the_generator_makes_a_creep_new_in_the_files_a_new_unit_with_its_sheet(monkeypatch):
    import tools.generate_patch_code_v2 as g
    now = _UNITS.replace('"npc_dota_neutral_nomana"', '"npc_dota_neutral_oldie"').replace(
        '"StatusHealth"\t\t"700"', '"StatusHealth"\t\t"700"\n\t\t"AttackCapabilities"\t\t"DOTA_UNIT_CAP_RANGED_ATTACK"\n\t\t"IsAncient"\t\t"1"')
    before = now.replace('"npc_dota_neutral_frog"', '"npc_dota_neutral_gone"')
    monkeypatch.setattr(game_files, "read", lambda version, rel: now if version == "7.38" else before)
    out = g._postprocess_new_units(['W(unit_header("Frog", NEUTRAL_CDN + "frog.png"))',
                                    'W(unit_header("Oldie", NEUTRAL_CDN + "oldie.png"))', "W(ul_open())"], "7.38")
    assert out[0] == 'W(unit_header("Frog", NEUTRAL_CDN + "frog.png", new="New Level 4 Ancient Ranged Creep"))'
    assert out[1:4] == ["W(ul_open())", 'W(unit_sheet("frog", version="7.38"))', "W(ul_close())"]
    assert out[4] == 'W(unit_header("Oldie", NEUTRAL_CDN + "oldie.png"))'        # the previous patch has it


def test_the_prowler_camp_is_told_as_flooded_camps():
    src = _read("content", "p738.py").replace("\r\n", "\n")
    start = src.index('W(plain_header("Ancient Prowlers"')
    block = src[start:src.index("# Ancient Prowler Acolyte", start)]
    assert 'new="Returning camp"' in block and "W(mech_story(" in block and "table=camp_table([" in block
    assert "(158, 179.5, b(179.5, 158)), (314, 195, b(195, 314))" in block and block.count("covered=True") == 1
    assert "Previously average bounty" not in block.split("W(li(")[0]       # in the table's dotted numbers now


def test_a_camp_number_that_changed_is_coloured_and_dotted():
    html = camp_table([("Ancient camp", [(2, "Acolyte", "a.png")], (158, 179.5, b(179.5, 158)), (314, 195, b(195, 314)))])
    assert '<b class="camp-v iab-nerf"><span class="iab-hint' in html and '<b class="camp-v iab-buff"><span class="iab-hint' in html
    assert '179.5 \u2192 158 <span class="iab-num iab-nerf">(-12%)</span>' in _html.unescape(html)


def test_no_row_repeats_the_name_of_its_ability():
    # 7.38 "Petrify: DPS increased from 75 to 100" under the Petrify header (owner 2026-11-04)
    import glob
    ability = re.compile(r'^\s*W\(ability\("([^"]+)"')
    other = re.compile(r'^\s*W\((hero_header|item_header|unit_header|plain_header|facet_header|subgroup|section|new_facet|facet_change|ability_change)\(')
    bad = []
    for path in glob.glob(os.path.join(ROOT, "content", "p*.py")):
        cur = None
        for line in open(path, encoding="utf-8"):
            m = ability.match(line)
            if m:
                cur = m.group(1)
            elif other.match(line):
                cur = None
            elif cur and f'W(li("{cur}: '.lower() in line.lower():
                bad.append(line.strip()[:80])
    assert not bad, bad


def test_the_generator_strips_the_ability_name_from_every_row_of_a_creep(monkeypatch):
    import tools.generate_patch_code_v2 as g
    monkeypatch.setitem(g.CREEP_ABILS, "npc_dota_neutral_frog", ["frog_petrify"])
    monkeypatch.setitem(g.ABILS_SLIM, "frog_petrify", {"dname": "Petrify"})
    out = g._render_neutral_creep({"name": "npc_dota_neutral_frog", "localized_name": "Frog", "neutral_creep_notes": [
        {"indent_level": 0, "note": "Petrify: DPS increased from 75 to 100"},
        {"indent_level": 0, "note": "Petrify: Duration decreased from 2s to 1s"}]})
    rows = [line for line in out if line.startswith("W(li(")]
    assert len(rows) == 2 and not any('"Petrify:' in row for row in rows)


def test_a_patch_s_new_creeps_are_found():
    now = _UNITS.replace('"BountyXP"\t\t"42"', '"BountyXP"\t\t"42"')
    before = _UNITS.replace('"npc_dota_neutral_frog"', '"npc_dota_neutral_gone"')
    assert us.neutrals(now) == {"npc_dota_neutral_frog"}          # a unit without experience is no camp creep
    assert us.neutrals(before) == {"npc_dota_neutral_gone"}


def test_new_patch_tells_what_is_left_for_a_new_creep(monkeypatch):
    import tools.new_patch as np
    before = _UNITS.replace('"npc_dota_neutral_frog"', '"npc_dota_neutral_gone"')
    monkeypatch.setattr(game_files, "read", lambda version, rel: _UNITS if version == "9.01" else before)
    monkeypatch.setattr("patch.weights._prev_version", lambda version: "9.00")
    lines = np.new_creep_steps("9.01")
    assert len(lines) == 1 and "(frog)" in lines[0] and "CREEP_CAMP" in lines[0] and "creeps_raw.csv" in lines[0]


@pytest.mark.skipif(not game_files.available(), reason="no game-files store")
def test_every_creep_of_the_latest_patch_is_listed_for_the_neutral_creeps_table():
    # a new creep missing here would silently not appear in the Neutral Creeps table
    from builders import creeps
    from patch.meta import RELEASE_HISTORY
    text = game_files.read(RELEASE_HISTORY[0]["version"], "scripts/npc/npc_units.txt")
    if not text:
        pytest.skip("the store has no such patch yet")
    listed = set(creeps.CREEP_NAME_TO_NPC.values()) | set(creeps.NOT_CAMP_UNITS)
    assert not us.neutrals(text) - listed
    short = {v: k for k, v in creeps.CREEP_NAME_TO_NPC.items()}
    for npc in us.neutrals(text) - set(creeps.NOT_CAMP_UNITS):
        assert npc in creeps.CREEP_DISPLAY_NAMES and short[npc] in creeps.CREEP_CAMP, npc


def test_a_unit_block_ends_at_any_next_unit_of_the_file():
    text = _UNITS.replace('"npc_dota_neutral_nomana"', '"dota_fountain"\n\t{\n\t\t"StatusHealth"\t\t"9"\n\t\t"BountyXP"\t\t"5"\n\t}\n\t"npc_dota_neutral_nomana"')
    assert us.numbers(text, "npc_dota_neutral_nomana")["Health"] == "100"
    frog = _UNITS.replace('"BountyXP"\t\t"42"\n', '').replace('"npc_dota_neutral_nomana"', '"dota_fountain"\n\t{\n\t\t"BountyXP"\t\t"5"\n\t}\n\t"npc_dota_neutral_nomana"')
    assert "npc_dota_neutral_frog" not in us.neutrals(frog)        # the next unit's experience is not the frog's


def test_new_patch_says_when_new_creeps_could_not_be_checked(monkeypatch):
    import tools.new_patch as np
    monkeypatch.setattr(game_files, "read", lambda version, rel: None)
    monkeypatch.setattr("patch.weights._prev_version", lambda version: "9.00")
    assert "NOT CHECKED" in np.new_creep_steps("9.01")[0]


def test_the_generator_warns_when_new_creeps_could_not_be_checked(monkeypatch, capsys):
    import tools.generate_patch_code_v2 as g
    monkeypatch.setattr(game_files, "read", lambda version, rel: None)
    lines = ['W(unit_header("Frog", NEUTRAL_CDN + "frog.png"))']
    assert g._postprocess_new_units(lines, "7.38") is lines
    assert "not checked" in capsys.readouterr().out
