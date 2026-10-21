"""Writers of the shared snapshot files that had none until 2026-10-21: tools/build_abilities_slim.py
(data/abilities_slim.json) and tools/build_herolist.py (data/herolist.json), plus scripts/fetch/extract_shops.py
writing into data/ (it wrote to scripts/data/) and extract_patchnotes.py --local."""
import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import build_abilities_slim as bas  # noqa: E402
from tools import build_herolist as bh  # noqa: E402

HERO_FILE = '''"DOTAHeroes"
{
	"npc_dota_hero_frog"
	{
		"Enabled"		"1"
		"HeroID"		"155"
		"Complexity"	"2"
		"AttributePrimary"	"DOTA_ATTRIBUTE_INTELLECT"
		"AbilityDefinitions"
		{
			"frog_croak"
			{
				"AbilityValues"
				{
					"radius"
					{
						"value"		"300 350"
						"special_bonus_unique_frog_1"	"+75"
					}
					"AbilityCooldown"
					{
						"value"		"12"
						"special_bonus_unique_frog_2"	"-2.0"
					}
				}
			}
			"frog_tongue"
			{
				"Innate"	"1"
			}
			"special_bonus_unique_frog_1"	{ }
			"special_bonus_unique_frog_2"	{ }
		}
	}
}
'''
DUMMY_FILE = '''"DOTAHeroes"
{
	"npc_dota_hero_target_dummy"
	{
		"Enabled"	"0"
		"HeroID"	"127"
	}
}
'''
ABILITIES = '''"DOTAAbilities"
{
	"Version"	"1"
	"special_bonus_hp_100"
	{
		"AbilityValues"
		{
			"value"	{ "value" "100" }
		}
	}
}
'''
LOC = '''"lang"
{
	"Tokens"
	{
		"npc_dota_hero_frog:n"	"Largo"
		"DOTA_Tooltip_ability_frog_croak"	"Croak"
		"DOTA_Tooltip_ability_frog_tongue"	"Tongue"
		"DOTA_Tooltip_ability_special_bonus_unique_frog_1"	"+{s:bonus_radius} Croak Radius"
		"DOTA_Tooltip_ability_special_bonus_unique_frog_2""-{s:bonus_AbilityCooldown}s Croak Cooldown"
		"DOTA_Tooltip_ability_special_bonus_hp_100"	"+{s:value} Health"
	}
}
'''


def _snapshot(tmp_path):
    stats = tmp_path / "stats"
    (stats / "heroes").mkdir(parents=True)
    (stats / "heroes" / "npc_dota_hero_frog.txt").write_text(HERO_FILE, encoding="utf-8")
    (stats / "heroes" / "npc_dota_hero_target_dummy.txt").write_text(DUMMY_FILE, encoding="utf-8")
    (stats / "npc_abilities.txt").write_text(ABILITIES, encoding="utf-8")
    (stats / "npc_heroes.txt").write_text(
        '"DOTAHeroes"\n{\n}\n#base "heroes/npc_dota_hero_target_dummy.txt"\n#base "heroes/npc_dota_hero_frog.txt"\n',
        encoding="utf-8")
    (tmp_path / "abilities_english.txt").write_text(LOC, encoding="utf-8")
    return str(stats), bas.load_loc(str(tmp_path))


def test_abilities_slim_names_fill_talent_numbers_and_mark_innates(tmp_path):
    stats, loc = _snapshot(tmp_path)
    table = bas.build(stats, loc, {})
    assert table["frog_croak"] == {"dname": "Croak"}
    assert table["frog_tongue"] == {"dname": "Tongue", "is_innate": True}
    # a talent's number lives in the ability it changes; the sign stays in the text, the number as the game writes it
    assert table["special_bonus_unique_frog_1"] == {"dname": "+75 Croak Radius"}
    assert table["special_bonus_unique_frog_2"] == {"dname": "-2.0s Croak Cooldown"}   # "key""text", no space
    assert table["special_bonus_hp_100"] == {"dname": "+100 Health"}                    # own AbilityValues
    assert "Version" not in table


def test_abilities_slim_keeps_abilities_gone_from_the_game_and_updates_changed_ones(tmp_path):
    stats, loc = _snapshot(tmp_path)
    current = {"old_removed_ability": {"dname": "Gone", "is_innate": True}, "frog_croak": {"dname": "Old Croak"}}
    table = bas.build(stats, loc, current)
    assert table["old_removed_ability"] == {"dname": "Gone", "is_innate": True}   # old pages still name it
    assert list(table)[:2] == ["old_removed_ability", "frog_croak"]                # existing order kept
    diff = dict((k, (o, n)) for k, o, n in bas.changes(current, table))
    assert diff["frog_croak"] == ({"dname": "Old Croak"}, {"dname": "Croak"})
    assert "old_removed_ability" not in diff
    assert json.loads(bas.dumps(table)) == table and "\n" not in bas.dumps(table)


def test_herolist_from_the_hero_files_in_game_order_without_disabled_heroes(tmp_path):
    stats, loc = _snapshot(tmp_path)
    heroes = bh.build(stats, loc)["result"]["data"]["heroes"]
    assert heroes == [{"id": 155, "name": "npc_dota_hero_frog", "name_loc": "Largo", "name_english_loc": "Largo",
                       "primary_attr": 2, "complexity": 2}]
    text = bh.dumps(bh.build(stats, loc))
    assert text.startswith('{\n"result": {\n"data": {\n"heroes": [\n{\n"id": 155,') and not text.endswith("\n")


def test_extract_shops_writes_into_data_not_scripts_data():
    sys.path.insert(0, os.path.join(ROOT, "scripts", "fetch"))
    import extract_shops
    assert extract_shops.OUT == Path(ROOT) / "data" / "shops.txt"


def test_extract_patchnotes_local_mode_writes_the_upload_targets(tmp_path, monkeypatch):
    sys.path.insert(0, os.path.join(ROOT, "scripts", "fetch"))
    monkeypatch.setattr(sys, "argv", ["extract_patchnotes.py", "7.99", "--local"])
    import importlib
    import extract_patchnotes as ep
    ep = importlib.reload(ep)
    assert ep.PATCH_VERSION == "7.99" and ep.LOCAL
    targets = ep.local_targets({"patchnotes_english.txt": b"a\r\n"}, {"items.txt": b'"x"\r\n'},
                               {"npc_dota_hero_frog.txt": b'"h"\r\n'})
    assert [t[0] for t in targets] == ["data/patchnotes_english.txt", "data/stats/7.99/items.txt",
                                       "data/stats/7.99/heroes/npc_dota_hero_frog.txt"]
    assert ep.write_local(targets, tmp_path) == 3
    assert (tmp_path / "data" / "stats" / "7.99" / "items.txt").read_bytes() == b'"x"\n'      # KV with LF
    assert (tmp_path / "data" / "patchnotes_english.txt").read_bytes() == b"a\r\n"            # loc byte for byte
    assert ep.write_local(targets, tmp_path) == 0                                               # nothing new
