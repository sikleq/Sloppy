"""The camp's own icon in camp_table (owner 2026-11-19): type glyph + each kind of creep's face + count of a repeat."""
import re
import sys
from pathlib import Path

import pytest

Image = pytest.importorskip("PIL.Image")    # CI has no Pillow: the icon checks run on the owner's PC only

from patch.camps import camp_faces, camp_icon, camp_kind, camp_ref, camp_table  # noqa: E402
from patch.mech_abilities import mech_table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "gen"))
import gen_camp_icons as gen  # noqa: E402

CAMP_CREEP = re.compile(r'\(\d+, "[^"]+", (?:_NC_CDN|NEUTRAL_CDN) \+ "(\w+)\.png"\)')


def test_every_creep_a_camp_table_shows_has_its_face():
    slugs = set()
    for path in (ROOT / "content").glob("p*.py"):
        src = path.read_text(encoding="utf-8")
        if "camp_table(" in src:
            slugs |= set(CAMP_CREEP.findall(src))
    assert slugs, "no camp_table creeps found in content/"
    assert slugs <= set(gen.FACE_CX), f"add to gen_camp_icons.FACE_CX and rerun it: {sorted(slugs - set(gen.FACE_CX))}"
    for s in slugs:
        assert (ROOT / "icons" / "camps" / "faces" / f"{s}.png").exists(), s


def test_generated_pictures_are_crisp_and_sized():
    for t in gen.TYPES:
        im = Image.open(ROOT / "icons" / "camps" / f"creepcamp_{t}_22.png")
        assert im.size == (22, 22)
        assert set(im.getchannel("A").getdata()) <= {0, 255}        # a hard edge: no blurred fringe
        assert Image.open(ROOT / "icons" / "camps" / f"creepcamp_{t}_22@2x.png").size == (44, 44)
    for s in gen.FACE_CX:
        assert Image.open(ROOT / "icons" / "camps" / "faces" / f"{s}.png").size == (34, 22)   # wider: whole faces
    for n in gen.DIGITS:
        assert Image.open(ROOT / "icons" / "camps" / f"count_{n}.png").size == (9, 11)


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


def test_icon_is_type_glyph_then_a_face_per_kind_with_the_count_of_a_repeat():
    html = camp_icon("Medium", [(2, "Boglet", "../icons/units/npc_dota_neutral_froglet.png"),
                                (1, "Marshmage Apprentice", "../icons/units/npc_dota_neutral_froglet_mage.png")])
    assert html.index("creepcamp_mid_22.png") < html.index("faces/froglet.png") < html.index("faces/froglet_mage.png")
    assert "data-tooltip" not in html                     # the size's words hover over the camp's name, not the glyph
    assert html.count('class="camp-face"') == 2
    assert html.count('class="camp-count"') == 1 and "count_2.png" in html and "count_1" not in html          # only the repeated creep shows a count
    assert 'srcset="../icons/camps/faces/froglet.png 1x, ../icons/camps/faces/froglet@2x.png 2x"' in html
    assert "creepcamp_mid_22.png" in html


def test_without_faces_only_the_type_glyph_stays():
    html = camp_icon("Ancient", [(1, "Unknown", "x.png")])
    assert "creepcamp_ancient_22.png" in html and "camp-face" not in html
    assert camp_icon("", [(1, "Unknown", "x.png")]) == ""


def test_a_repeated_creep_is_its_portrait_again_not_a_count():
    # owner 2026-11-20: "вместо x2 повторяющиеся иконки"; names only where the camps are new
    kind = camp_kind(3, "k.png")
    assert kind.count('<img src="k.png"') == 3 and "\u00d7" not in kind and "<b>" not in kind
    assert camp_kind(2, "k.png", "Kobold").endswith('<img src="k.png" alt="" width="28" height="16"><b>Kobold</b></span>')


def test_camp_ref_puts_the_portraits_before_the_name_without_the_type_glyph():
    html = camp_ref("Wolf camp", [(2, "Giant Wolf", "w.png"), (1, "Alpha Wolf", "a.png")])
    assert html.index('src="a.png"') < html.index('<span class="camp-ref-name">Wolf camp</span>')
    assert html.count('src="w.png"') == 2 and "creepcamp_" not in html and "faces/" not in html and "<b>" not in html
    assert camp_ref("Nowhere camp", []) == "Nowhere camp"
    new = camp_ref("Wolf camp", [(2, "Giant Wolf", "w.png")], new=True)
    assert '<span class="camp-ref-name camp-ref-new">Wolf camp</span>' in new


def test_742_home_jungle_names_all_18_camps_with_their_faces():
    src = (ROOT / "content" / "p742.py").read_text(encoding="utf-8")
    line = next(s for s in src.splitlines() if "home jungle" in s)
    assert line.count("camp_ref(") == 18 and 'cls="camp-jungle"' in line
    assert "<br>" not in line                          # one camp a line comes from the cell's column, not a <br>
    # new camps in gold, not Valve's "(new!)"; the first column says the side (owner 2026-11-19)
    assert "(new!)" not in line and line.count("new=True") == 3 and 'mech_table(["Side", ' in line
    # make-up read from server.dll 6984: Kobold camp lost a Kobold (3 -> 2, Valve's note), Vhoul is 3 Assassins
    assert 'camp_ref("Kobold camp", [(2, "Kobold"' in line and 'camp_ref("Vhoul camp", [(3, "Vhoul Assassin"' in line


def test_742_camp_changes_are_one_table_valves_rows_covered():
    # owner 2026-11-19 "оформить таблицей": Camp / Before / Now; Valve's rows stay for their tags and weights
    src = (ROOT / "content" / "p742.py").read_text(encoding="utf-8")
    line = next(s for s in src.splitlines() if 'mech_story("Neutral camps changed"' in s)
    # the type glyph a column of its own (owner 2026-11-20)
    assert 'mech_table(["", "Camp", "Before", "Now"]' in line and 'cls="camp-changes"' in line
    assert line.count("camp_glyph(") == 5
    # the removed camps: their old make-up (server.dll 6976) in Before, the same faces grey in Now, no red mark
    assert "camp-gone" not in line and line.count("camp_faces(") == 10 and line.count("gone=True") == 3
    assert "'—'" not in line
    for row in ("Satyr Banisher in Large Satyr camp replaced", "Amount of Kobolds in Kobold camp",
                "Medium Centaur camp removed", "Large Warpine Raider camp removed", "Ancient Thunderhide camp removed"):
        valve = next(s for s in src.splitlines() if row in s)
        assert "covered=True" in valve, row


def test_a_removed_camps_faces_are_grey_not_a_red_mark():
    # owner 2026-11-19: "removed выделяет от сайта, может просто серые иконки, как мы делаем с удаленными предметами"
    creeps = [(2, "Kobold", "../icons/units/npc_dota_neutral_kobold.png")]
    assert 'class="camp-crew camp-crew-gone"' in camp_faces(creeps, gone=True)
    assert "camp-crew-gone" not in camp_faces(creeps)


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
    assert html.count('src="../icons/units/npc_dota_neutral_tadpole.png"') == 3 and "<b>Pollywog</b>" in html
    assert "--camp-kinds:1" in html and ">Side<" not in html
