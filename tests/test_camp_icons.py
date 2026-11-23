"""Camps in tables (owner 2026-11-20): the type glyph a column of its own, the creeps as their portraits, a repeat its
portrait again; the glyph files are scripts/gen/gen_camp_icons.py's."""
import re
import sys
from pathlib import Path

import pytest

Image = pytest.importorskip("PIL.Image")    # CI has no Pillow: the icon checks run on the owner's PC only

from patch.camps import camp_faces, camp_kind, camp_ref, camp_table  # noqa: E402
from patch.mech_abilities import mech_table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "gen"))
import gen_camp_icons as gen  # noqa: E402

def test_generated_glyphs_are_crisp_and_the_dropped_faces_are_gone():
    for t in gen.TYPES:
        im = Image.open(ROOT / "icons" / "camps" / f"creepcamp_{t}_22.png")
        assert im.size == (22, 22)
        assert set(im.getchannel("A").getdata()) <= {0, 255}        # a hard edge: no blurred fringe
        assert Image.open(ROOT / "icons" / "camps" / f"creepcamp_{t}_22@2x.png").size == (44, 44)
    # owner 2026-11-20: our faces and count plates out, the game portraits instead
    assert not (ROOT / "icons" / "camps" / "faces").exists() and not list((ROOT / "icons" / "camps").glob("count_*"))


def test_small_camp_glyphs_use_the_crisp_file_of_their_size():
    """a 32 px creepcamp_*.png squeezed to 16-22 px blurs (owner 2026-11-19): every place that shows the glyph at a
    fixed small size takes creepcamp_<type>_<size>.png; only the Terrain map markers (they zoom) keep the 32 px file"""
    plain = re.compile(r'creepcamp_(?:small|mid|big|ancient)(?:\.png|"|\')')
    for rel in ("builders/creeps.py", "builders/entity_changes.py", "builders/terrain_stats.py", "patch/camps.py"):
        assert not plain.search((ROOT / rel).read_text(encoding="utf-8")), rel
    terrain = (ROOT / "builders" / "terrain.py").read_text(encoding="utf-8")
    # the layer button's img is 22 px by CSS (.tc-btn-icon img): its 22 px file (the visual check caught 16 stretched)
    assert '"creepcamp_mid_22", icon_dir="camps"' in terrain and '"camps/creepcamp_big_16"' in terrain
    for t in gen.TYPES:
        for size in gen.TYPE_SIZES:
            assert Image.open(ROOT / "icons" / "camps" / f"creepcamp_{t}_{size}.png").size == (size, size)


def test_a_repeated_creep_is_its_portrait_again_not_a_count():
    # owner 2026-11-20: "вместо x2 повторяющиеся иконки"; names only where the camps are new
    kind = camp_kind(3, "k.png")
    assert kind.count('<img src="k.png"') == 3 and "\u00d7" not in kind and "<b>" not in kind
    # the name plain after the portraits, not bold (owner 2026-11-20)
    assert camp_kind(2, "k.png", "Kobold").endswith(
        '<img src="k.png" alt="" width="28" height="16"><span class="camp-kind-name">Kobold</span></span>')


def test_camp_ref_puts_the_portraits_before_the_name_without_the_type_glyph():
    html = camp_ref("Wolf camp", [(2, "Giant Wolf", "w.png"), (1, "Alpha Wolf", "a.png")])
    assert html.index('src="a.png"') < html.index('<span class="camp-ref-name">Wolf camp</span>')
    assert html.count('src="w.png"') == 2 and "creepcamp_" not in html and "faces/" not in html and "<b>" not in html
    assert camp_ref("Nowhere camp", []) == "Nowhere camp"
    new = camp_ref("Wolf camp", [(2, "Giant Wolf", "w.png")], new=True)
    assert '<span class="camp-ref-name camp-ref-new">Wolf camp</span>' in new


def test_742_home_jungle_names_all_18_camps_with_their_portraits():
    # built from the game files since 2026-11-22 (patch/camps.py home_jungle_table, tests/test_camp_sides.py)
    import re
    from patch.camps import home_jungle_table
    html = home_jungle_table("7.42", "742-v3")
    assert html.count('class="camp-ref"') == 18 and "camp-jungle" in html
    assert "<br>" not in html                          # one camp a line comes from the cell's column, not a <br>
    # new camps in gold, not Valve's "(new!)"; the first column says the side (owner 2026-11-19)
    assert "(new!)" not in html and html.count("camp-ref-new") == 3 and ">Side<" in html
    # Kobold camp lost a Kobold (3 -> 2, Valve's note), Vhoul is 3 Assassins
    kobold = html.split(">Kobold camp<")[0].rsplit('class="camp-ref"', 1)[1]
    assert len(re.findall(r'neutral_kobold\.png', kobold)) == 2
    vhoul = html.split(">Vhoul camp<")[0].rsplit('class="camp-ref"', 1)[1]
    assert len(re.findall(r'neutral_gnoll_assassin\.png', vhoul)) == 3


def test_742_camp_changes_are_one_table_valves_rows_covered():
    # owner 2026-11-19 "оформить таблицей": Camp / Before / Now; Valve's rows stay for their tags and weights
    src = (ROOT / "content" / "p742.py").read_text(encoding="utf-8")
    line = next(s for s in src.splitlines() if 'mech_story("Neutral camps changed"' in s)
    # the type glyph a column of its own (owner 2026-11-20)
    assert 'mech_table(["", "Camp", "Before", "Now"]' in line and 'cls="camp-changes"' in line
    assert line.count("camp_glyph(") == 5
    # the removed camps: their old make-up (server.dll 6976) in Before, the same portraits grey in Now, no red mark
    assert "camp-gone" not in line and line.count("camp_faces(") == 10 and line.count("gone=True") == 3
    assert "'—'" not in line
    for row in ("Satyr Banisher in Large Satyr camp replaced", "Amount of Kobolds in Kobold camp",
                "Medium Centaur camp removed", "Large Warpine Raider camp removed", "Ancient Thunderhide camp removed"):
        valve = next(s for s in src.splitlines() if row in s)
        assert "covered=True" in valve, row


def test_a_removed_camps_portraits_are_grey_not_a_red_mark():
    # owner 2026-11-19: "removed выделяет от сайта, может просто серые иконки, как мы делаем с удаленными предметами"
    creeps = [(2, "Kobold", "../icons/units/npc_dota_neutral_kobold.png")]
    assert 'class="camp-crew camp-crew-gone"' in camp_faces(creeps, gone=True)
    assert "camp-crew-gone" not in camp_faces(creeps)


def test_a_wide_last_column_table_keeps_a_phone_page_its_width():
    # 7.42 Tormentor drops on a phone: "Greater Horn of Battle" in one line left "Details" 54 px and the page grew 13 px
    # (owner 2026-11-20 "лишние 10px на телефоне поправь"); an item name wraps, a long word breaks
    phones = (ROOT / "src" / "css" / "phones.css").read_text(encoding="utf-8")
    assert ".mech-abils.mech-wide-last .mech-item { white-space: normal; min-width: 0; }" in phones
    # the item column as wide as its icon and longest word: at fit-content(20%) "Aghanim's" stuck out of 66 px
    assert ".mech-abils.mech-cols-3.mech-wide-last { grid-template-columns: fit-content(28%) min-content minmax(0, 1fr); }" in phones
    assert ".mech-abils.mech-wide-last > .mech-abil-row > .mech-cell { min-width: 0; overflow-wrap: break-word; }" in phones


def test_radiant_and_dire_are_always_in_their_colours():
    # owner 2026-11-20: "Radiant и Dire всегда выделяем цветами"
    html = mech_table(["Side", "Camps"], [["Radiant", "x"], ["Dire", "y"], ["Both", "z"]])
    assert '<span class="side-word side-radiant">Radiant</span>' in html
    assert '<span class="side-word side-dire">Dire</span>' in html and "side-both" not in html


def test_old_tables_get_the_type_from_the_camp_name():
    html = camp_table([("Small camp", [(3, "Pollywog", "../icons/units/npc_dota_neutral_tadpole.png")], 54, 90)])
    # the glyph a column of its own, the name plain (owner 2026-11-20: "убираем подсказки с camp")
    assert '<span class="camp-name camp-type-col"><span class="camp-type"><img src="../icons/camps/creepcamp_small_22.png"' in html
    assert '<span class="camp-cell camp-label-cell">Small camp</span>' in html and "data-tooltip" not in html
    assert html.count('src="../icons/units/npc_dota_neutral_tadpole.png"') == 3 and '<span class="camp-kind-name">Pollywog</span>' in html and "<b>" not in html
    assert "--camp-kinds:1" in html and ">Side<" not in html


def test_the_camp_head_has_no_line_before_it():
    # owner 2026-11-21: "вертикальная линия лишь кусочек перед camp" — the rows have no line between glyph and name
    from patch.camps import camp_table
    html = camp_table([("Small camp", [(3, "Pollywog", "x.png")], 54, 90, "small", "Radiant")])
    assert '<span class="camp-cell camp-label-cell camp-head">Camp</span>' in html
    assert html.count("camp-label-cell") == 2
