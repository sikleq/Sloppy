"""The camp's own icon in camp_table (owner 2026-11-19): type glyph + each kind of creep's face + count of a repeat."""
import re
import sys
from pathlib import Path

import pytest

Image = pytest.importorskip("PIL.Image")    # CI has no Pillow: the icon checks run on the owner's PC only

from patch.camps import camp_icon, camp_ref, camp_table  # noqa: E402

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


def test_camp_ref_puts_faces_before_the_name_without_the_type_glyph():
    html = camp_ref("Wolf camp", [(2, "Giant Wolf", "../icons/units/npc_dota_neutral_tadpole.png")])
    assert html.index("faces/tadpole.png") < html.index('<span class="camp-ref-name">Wolf camp</span>')
    assert "creepcamp_" not in html and "count_2.png" in html
    assert camp_ref("Nowhere camp", [(1, "X", "x.png")]) == "Nowhere camp"   # no face: the name alone


def test_742_home_jungle_names_all_18_camps_with_their_faces():
    src = (ROOT / "content" / "p742.py").read_text(encoding="utf-8")
    line = next(s for s in src.splitlines() if "home jungle" in s)
    assert line.count("camp_ref(") == 18 and 'cls="camp-jungle"' in line
    assert "<br>" not in line                          # one camp a line comes from the cell's column, not a <br>
    # make-up read from server.dll 6984: Kobold camp lost a Kobold (3 -> 2, Valve's note), Vhoul is 3 Assassins
    assert 'camp_ref("Kobold camp", [(2, "Kobold"' in line and 'camp_ref("Vhoul camp", [(3, "Vhoul Assassin"' in line


def test_old_tables_get_the_type_from_the_camp_name():
    html = camp_table([("Small camp", [(3, "Pollywog", "../icons/units/npc_dota_neutral_tadpole.png")], 54, 90)])
    assert '<span class="camp-label iab-hint" data-tooltip="Small camp">Small camp</span>' in html
    assert "faces/tadpole.png" in html and "count_3.png" in html
    assert "--camp-kinds:1" in html and ">Side<" not in html
