"""Owner 2026-11-04, 7.38: a mechanic block reads as one paragraph with its key values bold and its map in sight (variant 4
of the mock); map pictures have thin outlines with many dashes and show the currents with arrows; Glyph and Scan are
abilities, each with an ability's header."""
import ast
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "gen"))
from patch.mech_abilities import mech_story, mech_table, story_side_width  # noqa: E402
from patch.page import _new_mech_rows, _sort_changes_li  # noqa: E402
from patch.state import _State, reset_page_state  # noqa: E402
import terrain_shots as ts  # noqa: E402


def _content(name):
    with open(os.path.join(ROOT, "content", name), encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def patch_738():
    reset_page_state()
    _State.current_patch_version = "7.38"
    yield
    reset_page_state()


def test_a_story_keeps_the_tags_the_filters_read(patch_738):
    assert 'data-tag="buff new"' in mech_story("Text.")
    assert 'data-tag="rework"' in mech_story("Text.", tags=("rework",))
    assert 'data-tag="buff new rework"' in mech_story("Text.", tags=("new", "rework"))


def test_one_map_stands_beside_the_text_two_go_under_it(patch_738):
    one = mech_story("Text.", maps=["Tormentor spawns repositioned to the corners of the map"])
    two = mech_story("Text.", maps=["Shrines of Wisdom are located in the offlane side jungles"])
    assert "mech-story-side" in one and one.count("<img ") == 1
    assert "mech-story-side" not in two and two.count("<img ") == 2
    assert ' hidden' not in one and 'class="tshots mech-story-maps"' in one
    assert "--story-side:" in one and "--story-side:" not in two


def test_the_picture_beside_the_text_grows_with_the_text_and_stays_within_it():
    short, long_text = story_side_width(["word " * 60]), story_side_width(["word " * 130])
    assert short < long_text <= 480
    assert story_side_width(["word"]) == 300                # the smallest picture still readable
    per_line = (954 - 16 - long_text) / 7.0
    lines = -(-650 // per_line)
    assert long_text * 360 / 726 <= lines * 24              # no taller than the text


def test_paragraphs_stay_apart_and_a_word_is_found_in_any_of_them(patch_738):
    out = mech_story(["First.", "Radiant and Dire main jungles now."],
                     buttons=[("main jungles", "Radiant and Dire main jungles now also have a stream with moderate current")])
    assert out.count('class="mech-story-p"') == 2
    assert out.index('class="tshots-btn"') > out.index("First.")


def test_a_story_opens_a_list_with_lesser_tags(patch_738):
    nerf = '<li data-tag="nerf"><span class="badge nerf" data-tag="nerf">NERF</span><span class="row-text">Row</span></li>'
    out = _sort_changes_li('<ul class="changes">' + nerf + mech_story("Story.", tags=("rework",)) + "</ul>")
    assert out.index("Story.") < out.index("Row")


def test_a_line_of_values_has_no_label_column():
    out = mech_table(["Radius", "Time"], [["350", "1.5s"]], labels=False)
    assert "mech-label" not in out and "mech-cols-2" in out


def test_a_word_of_the_text_opens_its_pictures_on_a_click(patch_738):
    out = mech_story("Radiant and Dire main jungles now.",
                     buttons=[("main jungles", "Radiant and Dire main jungles now also have a stream with moderate current")])
    assert '<button type="button" class="tshots-btn" data-part="0" aria-expanded="false">main jungles</button>' in out
    assert '<span class="tshots" data-part="0" hidden>' in out


def test_a_story_refuses_a_map_or_a_word_that_is_not_there(patch_738):
    with pytest.raises(ValueError):
        mech_story("Text.", maps=["No such note"])
    with pytest.raises(ValueError):
        mech_story("Text.", buttons=[("missing words", "These streams have a current")])


def test_the_table_goes_under_the_text_without_its_markers(patch_738):
    out = mech_story("Text.", table=mech_table(["A", "B"], [["1", "2"]]))
    assert "MECHTABLE" not in out and out.index("Text.") < out.index('class="mech-abils')


def test_words_round_a_bold_value_stay_one_item_of_the_cell():
    out = mech_table(["A", "B"], [["Time", "takes <b>1.5s</b>, then <b>1s</b>"], ["Plain", "no markup"]])
    assert '<span class="mech-cell"><span>takes <b>1.5s</b>, then <b>1s</b></span></span>' in out
    assert '<span class="mech-cell">no markup</span>' in out


def test_a_covered_map_note_takes_no_number(patch_738):
    from patch.badges import t
    from patch.elements import li
    _State.terrain_rows = 0
    li("Hidden note", t("NEW"), covered=True)
    assert 'class="badge tnum">1<' in li("Shown note", t("REWORK"))


def _block(*rows):
    return '<ul class="changes"><!--NEWMECH:new-->' + "".join(rows) + "</ul>"


_CHIP = '<span class="badge new" data-tag="new" data-overall="buff">NEW</span>'
_DEL = '<li data-tag="del nerf"><span class="badge del" data-tag="del">DEL</span><span class="row-text">Gone</span></li>'
_COVERED = f'<li class="iab-covered covered-card" data-tag="buff new">{_CHIP}<span class="row-text">Hidden</span></li>'
_ROW = f'<li data-tag="buff new">{_CHIP}<span class="row-text">Shown</span></li>'


def test_the_story_leads_its_list_and_a_covered_row_opens_no_box(patch_738):
    out = _new_mech_rows(_block(_DEL, _COVERED, mech_story("Story.")))
    assert out.index("Story.") < out.index("Gone") < out.index("Hidden")
    assert 'class="iab-covered covered-card"' in out          # the hidden row keeps its class: no mech-first on it


def test_a_story_after_box_rows_stays_after_them(patch_738):
    out = _new_mech_rows(_block(_ROW, mech_story("Story.")))
    assert out.index("Shown") < out.index("Story.")


def test_outlines_are_thin_with_many_dashes():
    assert [s[3] for s in ts.SIZES] == [2, 3]
    side = 2 * 170.0
    dash, gap = ts.dash_gap(170.0)
    assert side / (dash + gap) >= 5                      # was 2.8 dashes a side (s / 3, s / 5)


def test_arrows_follow_the_current_downstream():
    points = ts.flow_points([(0, 0), (1000, 0), (1000, 1000)], 500)
    assert points[0] == (250, 0, 1, 0)                   # first at half a step, along the first leg
    assert points[-1][2:] == (0, 1)                      # the last on the second leg points along it
    assert len(points) == 4


def test_the_738_stream_notes_show_the_currents():
    with open(os.path.join(ROOT, "data", "terrain_spots.json"), encoding="utf-8") as f:
        entries = json.load(f)["7.38"]
    for start in ("The top and bottom outer rim", "These streams have a current", "Radiant and Dire main jungles"):
        entry = next(e for e in entries if e["match"].startswith(start))
        assert "currents" in entry["show"], start


@pytest.mark.parametrize("name, title, icon, row", [
    ("p738.py", "Glyph of Fortification", "hud_glyph.png", "Creep duration decreased from 4s to 3s"),
    ("p739e.py", "Scan", "hud_scan.png", "No longer triggers on creep heroes"),
])
def test_glyph_and_scan_are_abilities_not_lines(name, title, icon, row):
    src = _content(name)
    assert f'W(plain_header("Team Abilities"))\n    W(ability("{title}", icon_url="../icons/abilities/{icon}"' in src
    assert row in src
    assert f'li("{title}' not in src
    assert os.path.exists(os.path.join(ROOT, "icons", "abilities", icon))


def test_the_generator_moves_glyph_and_scan_to_their_own_category():
    import tools.generate_patch_code_v2 as g
    out = g._postprocess_team_abilities([
        'W(plain_header("Major Mechanics"))',
        'W(ul_open())',
        'W(li("Scan no longer triggers on creep heroes", t("DEL")))',
        'W(li("Glyph of Fortification: Creep duration decreased from 4s to 3s", b(4, 3)))',
        'W(li("Something else", t("MISC")))',
        'W(ul_close())',
        'W(plain_header("Next"))',
    ])
    assert out[:4] == ['W(plain_header("Major Mechanics"))', 'W(ul_open())', 'W(li("Something else", t("MISC")))', 'W(ul_close())']
    assert out[4] == 'W(plain_header("Team Abilities"))'
    assert out[5].startswith('W(ability("Glyph of Fortification", icon_url="../icons/abilities/hud_glyph.png"')
    assert out[7] == 'W(li("Creep duration decreased from 4s to 3s", b(4, 3)))'
    assert out[9].startswith('W(ability("Scan", icon_url="../icons/abilities/hud_scan.png"')
    assert out[11] == 'W(li("No longer triggers on creep heroes", t("DEL")))'
    assert out[-1] == 'W(plain_header("Next"))'


def test_the_generator_gathers_rows_of_several_lists_and_drops_an_emptied_one():
    import tools.generate_patch_code_v2 as g
    out = g._postprocess_team_abilities([
        'W(plain_header("Only Glyph"))', 'W(ul_open())', 'W(li("Glyph cooldown decreased", b(300, 200)))', 'W(ul_close())',
        'W(plain_header("Other"))', 'W(ul_open())', 'W(li("Row", t("MISC")))',
        'W(li("The Glyph of Fortification now lasts longer", t("BUFF")))', 'W(ul_close())',
    ])
    assert 'W(plain_header("Only Glyph"))' not in out
    assert out[0] == 'W(plain_header("Team Abilities"))'
    assert out.count('W(plain_header("Team Abilities"))') == 1
    assert sum(line.startswith('W(ability("Glyph of Fortification"') for line in out) == 1
    assert 'W(li("Cooldown decreased", b(300, 200)))' in out and 'W(li("Now lasts longer", t("BUFF")))' in out


def test_a_patch_without_glyph_or_scan_is_left_alone():
    import tools.generate_patch_code_v2 as g
    lines = ['W(ul_open())', 'W(li("Crystal Ball: Clairvoyance Scan duration increased", b(4, 5)))', 'W(ul_close())']
    assert g._postprocess_team_abilities(lines) is lines


def test_every_patch_keeps_glyph_and_scan_in_their_category():
    """Guards the patches written by hand too: no such row in a list, each header under the category."""
    import glob
    import re
    for path in glob.glob(os.path.join(ROOT, "content", "p*.py")):
        calls = [line.strip() for line in open(path, encoding="utf-8") if line.strip().startswith("W(")]
        for i, call in enumerate(calls):
            assert not re.match(r'W\(li\("(The )?(Glyph|Scan)\b', call), f"{path}: {call[:70]}"
            if re.match(r'W\(ability\("(Glyph of Fortification|Scan)"', call):
                back = next(c for c in reversed(calls[:i]) if c.startswith(("W(plain_header(", "W(section(")))
                assert back == 'W(plain_header("Team Abilities"))', f"{path}: {call[:70]}"


def _mech_rows(src, header):
    """The li() calls of the block under a header of p738 (its source lines up to ul_close)."""
    tree_lines = src.splitlines()
    start = next(i for i, line in enumerate(tree_lines) if header in line)
    end = next(i for i in range(start, len(tree_lines)) if "W(ul_close())" in tree_lines[i])
    return tree_lines[start:end]


@pytest.mark.parametrize("header", ['"Wandering Waters"', '"Shrines of Wisdom", new=', '"Tormentor", "../icons',
                                    '"Flooded Camps"', '"Obtaining Madstone"', '"Item Tiers"', '"Crafting"',
                                    '"Madstone Limits"', '"Turbo"'])
def test_738_mechanic_blocks_are_stories_over_covered_rows(header):
    lines = _mech_rows(_content("p738.py"), header)
    assert any("mech_story(" in line for line in lines), header
    # every NEW / REWORK description row of the block is hidden under the story; others keep their chip
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('W(li("') and ('t("NEW")' in stripped or 't("REWORK")' in stripped):
            if "Tormentor now grants 250 gold" in stripped or "Watchers, camps and pathways" in stripped:
                continue
            assert "covered=True" in stripped, stripped[:70]


def test_738_lotus_note_is_a_table_not_a_question_mark():
    src = _content("p738.py")
    start = src.index('W(subgroup("Lotus Pools"))')
    block = src[start:src.index('W(subgroup("Shrines of Wisdom"')]
    assert "W(mech_story([" in block and "table=mech_table(" in block and 'maps=["Changed the way Healing Lotuses"]' in block
    # the note behind the "?" is in the paragraph now, the rows stay for tags and weights
    assert "All remaining lotuses" in block.split("W(li(")[0]
    assert block.count("covered=True") == 2
    ast.parse(src)


def test_roshan_738_is_a_story_as_wandering_waters():
    lines = _mech_rows(_content("p738.py"), 'unit_header("Roshan"')
    joined = "\n".join(lines)
    assert 'maps=["Roshan is back in the river"]' in joined
    assert 'W(li("Roshan is back in the river, with one pit located near each sidelane", t("REWORK"), covered=True))' in joined


def test_team_abilities_with_no_list_closing_after_them_do_not_double_the_page():
    import tools.generate_patch_code_v2 as g
    out = g._postprocess_team_abilities(['W(section("General"))', 'W(li("Glyph of Fortification: Creep duration decreased", b(4, 3)))'])
    assert out.count('W(section("General"))') == 1
    assert out[-1] == "W(ul_close())" and sum("plain_header" in line for line in out) == 1


def test_741_scaling_and_lifesteal_are_stories_and_their_rows_stay_for_tags():
    src = _content("p741.py").replace("\r\n", "\n")
    start = src.index('W(plain_header("Scaling with Hero Level"')
    block = src[start:src.index("W(ul_close())", start)]
    assert 'W(mech_story([' in block and 'tags=("rework", "misc", "qol")' in block and block.count("covered=True") == 4
    assert 'force_tag="rework misc", covered=True' in block and 'force_tag="rework qol", covered=True' in block
    start = src.index('W(subgroup("Lifesteal and Damage Manipulations"')
    block = src[start:src.index("W(ul_close())", start)]
    assert "table=mech_list(_lifesteal_sources)" in block and block.count("covered=True") == 2
    # the note behind the "?" is in the paragraph too
    assert "increased damage against illusions." in block.split("W(li(")[0]


def test_a_story_answers_every_filter_its_hidden_rows_answer():
    from patch.mech_abilities import mech_story
    html = mech_story("Text.", tags=("rework", "misc", "qol"))
    assert 'data-tag="rework misc qol"' in html


def test_mech_list_gives_the_icons_and_stops_on_what_it_cannot_read(monkeypatch):
    from patch.elements import info_tip
    from patch.mech_abilities import mech_list
    from patch.state import _State
    import pytest
    monkeypatch.setattr(_State, "current_patch_version", "7.41")
    html = mech_list(info_tip("Aeon Disk", "Bloodstone", "Veil of Discord", header="This affects the following:"))
    assert "mech-abils" in html and "ability-chip" in html
    with pytest.raises(ValueError):
        mech_list(info_tip("Just one sentence of explanation with no abilities in it."))


def test_739_health_restoration_and_heal_amplification_are_stories():
    src = _content("p739.py").replace("\r\n", "\n")
    start = src.index('W(plain_header("Health Restoration"')
    block = src[start:src.index("W(ul_close())", start)]
    assert 'tags=("new", "del")' in block and block.count("covered=True") == 4
    stories = block.split("W(li(")[0]
    # the formula and the example stand in blocks of their own, not in a flat paragraph (owner 2026-11-04)
    assert stories.count("W(mech_story(") == 3
    assert 'mech_formula("1 - (1 - n0) * (1 - n1) * ...")' in stories and "<b>32.8%</b>" in stories
    start = src.index('W(plain_header("Heal Amplification"')
    block = src[start:src.index("W(ul_close())", start)]
    assert block.count("covered=True") == 2 and "Incoming Heal Amplification and Outgoing" in block.split("W(li(")[0]


def test_a_mechanic_formula_has_the_look_of_the_sites_formulas():
    from patch.mech_abilities import mech_formula
    html = mech_formula("1 - (1 - n0)")
    assert html.startswith('<code class="formula-expr">') and 'class="f-var"' in html and 'class="f-num"' in html


def test_a_table_of_values_alone_has_equal_columns():
    from patch.css_bundle import read_css
    from patch.mech_abilities import mech_table
    assert "mech-values" in mech_table(["Lowest", "Highest"], [["1", "2"]], labels=False)
    assert "mech-values" not in mech_table(["Sources", "Total"], [["1", "2"]])
    css = read_css()
    assert ".mech-abils.mech-cols-2.mech-values { grid-template-columns: repeat(2, minmax(0, 1fr)); }" in css
    assert ".mech-abils.mech-cols-3.mech-values { grid-template-columns: repeat(3, minmax(0, 1fr)); }" in css


def test_an_example_has_its_icon_and_a_name_without_one_stops_the_build(monkeypatch):
    from patch.mech_abilities import mech_example
    from patch.state import _State
    import pytest
    monkeypatch.setattr(_State, "current_patch_version", "7.39")
    # the icon alone, its name on hover (owner 2026-11-06)
    assert 'src="../icons/items/sange.png"' in mech_example("Sange") and 'data-tooltip="Sange"' in mech_example("Sange")
    assert 'src="../icons/items/enhancement_crude.png"' in mech_example("Crude Enchantment")
    assert 'src="../icons/items/aeon_disk.png"' in mech_example("Aeon Disk's Combo Breaker")
    with pytest.raises(ValueError):
        mech_example("Attacks against a hero")


def test_examples_in_mechanic_paragraphs_have_icons():
    for name, needle, chips in (("p739.py", "For example, a ", ("Sange", "Crude Enchantment")),
                                ("p741.py", "(like attacks against a hero affected by ", ("Aeon Disk's Combo Breaker",))):
        src = _content(name)
        i = next(k for k, line in enumerate(src.splitlines()) if needle in line and "covered=True" not in line)
        line = src.splitlines()[i]
        assert all(chip in line and "mech_example(" in line for chip in chips), line[:100]


def test_an_example_name_stays_on_the_line_of_the_words_around_it():
    # inline-flex put the name on the icon's centre: it stood off the text line
    from patch.css_bundle import read_css
    css = read_css()
    assert ".ac-sub { white-space: nowrap; margin-right: 2px; }" in css and "vertical-align: -5px" in css


def test_738_examples_have_icons():
    src = _content("p738.py")
    # Lifesteal Amp's three abilities are a table now (owner 2026-11-06), tests/test_mech_blocks.py
    for name in ("Linken's Sphere",):
        assert f'mech_example("{name}")' in src, name


def test_the_title_of_a_formula_has_the_type_of_a_row():
    from patch.css_bundle import read_css
    import re
    rule = re.search(r"\.formula-change-title \{[^}]*\}", read_css()).group(0)
    assert "font-size: 15px" in rule and "font-weight: 400" in rule and "var(--text-main)" in rule


def test_an_icon_named_in_a_text_grows_on_hover_as_the_others():
    from patch.css_bundle import read_css
    import re
    css = read_css()
    rule = re.search(r"\.ac-sub:hover > \.ac-sub-ico \{[^}]*\}", css).group(0)
    assert "transform: scale(2.6)" in rule
    assert ".ac-sub:hover { position: relative; z-index: 101; }" in css           # above the words next to it


def test_an_icon_in_a_text_keeps_its_proportions():
    # 7.41 Aeon Disk's icon is 88x64: squeezed into the 20px square it looked flattened (owner 2026-11-05)
    from patch.css_bundle import read_css
    import re
    rule = re.search(r"^\.ac-sub-ico \{[^}]*\}", read_css(), re.M).group(0)
    assert "object-fit: cover" in rule
