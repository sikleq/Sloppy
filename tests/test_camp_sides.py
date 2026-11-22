"""Owner 2026-11-22: which side a creep spawns on comes from the game files — the map's spawn ranges
(mapdata_<code>.json minSpawnType / maxSpawnType) and server.dll's camp table (data/rules/camp_table.json)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from patch.camp_sides import creep_sides, home_side, spawners  # noqa: E402


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


def test_the_742_page_home_jungle_table_matches_the_game():
    # the page's table is written by hand (camp names); its creeps per side must be the game's
    src = (ROOT / "content" / "p742.py").read_text(encoding="utf-8")
    line = next(ln for ln in src.splitlines() if 'now has a \\"home jungle\\"' in ln)
    radiant, dire = line.split('["Radiant",')[1].split('["Dire",')
    icons = lambda part: {"npc_dota_neutral_" + m for m in re.findall(r'NEUTRAL_CDN \+ "([a-z_]+)\.png"', part)}  # noqa: E731
    hs = home_side("7.42", "742-v3")
    assert icons(radiant) == {n for n, s in hs.items() if s == "radiant"}
    assert icons(dire) == {n for n, s in hs.items() if s == "dire"}
