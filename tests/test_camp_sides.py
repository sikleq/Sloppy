"""Owner 2026-11-22: which side a creep spawns on comes from the game files — the map's spawn ranges
(mapdata_<code>.json minSpawnType / maxSpawnType) and server.dll's camp table (data/rules/camp_table.json)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from patch.camp_sides import creep_sides, growth, home_side, spawners  # noqa: E402


def test_742_home_jungle_ranges_from_the_map():
    for side, size, first, last in spawners("742-v3"):
        if size == 3:
            assert (first, last) == (1, 5)                           # ancients: both sides, all five
        elif (first, last) != (7, 7):                                # 7 = the flooded camps
            # Dire's small camp by the top lane: 5-6 only (Ghost, Harpy — no Vhoul; a row of the 7.42 page)
            ok = [(1, 3)] if side == "radiant" else [(4, 6)] + ([(5, 6)] if size == 0 else [])
            assert (first, last) in ok, (side, size, first, last)


def test_742_sides_of_known_creeps():
    hs = home_side("7.42", "742-v3")
    assert hs["npc_dota_neutral_kobold"] == "radiant" and hs["npc_dota_neutral_radigull"] == "radiant"
    assert hs["npc_dota_neutral_mud_golem"] == "dire" and hs["npc_dota_neutral_odobenus_footman"] == "dire"
    both = {n for n, s in creep_sides("7.42", "742-v3").items() if len(s) == 2}
    assert {"npc_dota_neutral_black_dragon", "npc_dota_neutral_ogre_seal", "npc_dota_neutral_froglet"} <= both


def test_the_742_page_home_jungle_table_is_built_from_the_game():
    # owner 2026-11-22 "научи автоматически": the page calls the generator, its creeps per side are the game's
    sys.path.insert(0, str(ROOT / "builders"))
    from patch.camps import home_jungle_table
    src = (ROOT / "content" / "p742.py").read_text(encoding="utf-8")
    assert 'extra=home_jungle_table("7.42", "742-v3")' in src
    html = home_jungle_table("7.42", "742-v3")
    radiant, dire = html.split(">Dire<")
    icons = lambda part: {"npc_dota_neutral_" + m for m in re.findall(r'npc_dota_neutral_([a-z_]+)\.png', part)}  # noqa: E731
    hs = home_side("7.42", "742-v3")
    assert icons(radiant) == {n for n, s in hs.items() if s == "radiant"}
    assert icons(dire) == {n for n, s in hs.items() if s == "dire"}
    new = set(re.findall(r'camp-ref-new">([^<]+)<', html))
    assert new == {"Radigull camp", "Eimermole camp", "Odobenus camp"}          # not Kobold (3 -> 2 Kobolds)


def test_742_flooded_camps_grow_from_the_game():
    # owner 2026-11-22: "знать эволюцию жаб"
    g = {t: (side, stages) for t, side, stages in growth("7.42", "742-v3")}
    assert len(g) == 6
    side, stages = g["neutralcamp_good_4"]
    assert side == "radiant" and [s[0] for s in stages] == [
        "npc_dota_neutral_froglet_mage", "npc_dota_neutral_grown_frog_mage", "npc_dota_neutral_ancient_frog_mage"]
    assert g["neutralcamp_evil_11"][1] == [["npc_dota_neutral_tadpole"] * 3,
                                          ["npc_dota_neutral_froglet_mage", "npc_dota_neutral_froglet",
                                           "npc_dota_neutral_froglet"]]


def test_the_camp_table_is_read_from_server_dll_by_its_shape():
    # owner 2026-11-22: "нельзя автоматически научить?" — no IDA, no address
    import json
    import pytest
    sys.path.insert(0, str(ROOT / "scripts" / "gen"))
    import camp_table as ct
    if not Path(ct.DLL).exists():
        pytest.skip("no installed game")
    rva, tiers = ct.find_table(ct.Image(ct.DLL))
    stored = json.loads((ROOT / "data" / "rules" / "camp_table.json").read_text(encoding="utf-8"))
    latest = [v for v in stored if not v.startswith("_")][-1]
    if stored[latest]["table_rva"] == hex(rva):          # the installed game is the stored patch's build
        assert tiers == stored[latest]["tiers"]
