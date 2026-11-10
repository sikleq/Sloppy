"""Guards mechanic blocks, creep tables and map notes: lists as tables, paragraphs, Roshan, neutral creeps and their
abilities, the terrain note pictures and the terrain stats page links.
"""

import os
import pathlib
import pytest
import sys
import tools.generate_patch_code_v2 as g
from builders import creeps_abilities as ua, entity_changes as ec
from patch import terrain_notes
from patch.state import reset_page_state

ROOT = pathlib.Path(__file__).resolve().parents[1]
_ROOT_1110 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT_1110)
sys.path.insert(0, os.path.join(_ROOT_1110, "tools"))


def _note(level, text):
    return {"indent_level": level, "note": text}


def _block(kind, slug, name, body):
    return (f'<div class="entity-block">'
            f'<div class="entity hero-entity" id="dyn-{kind}-{slug}">'
            f'<img src="../icons/{slug}.png" alt="{name}"><div class="entity-name">{name}</div></div>'
            f'<ul><li>{body}</li></ul></div>')


def _red(img, xy):
    r, g, _ = img.getpixel(xy)
    return r > 150 and g < 120


def _light(img, xy):
    r, g, b = img.getpixel(xy)
    return r > 30 and abs(r - g) < 12 and abs(g - b) < 15


def test_abilities_each_doing_something_make_a_table():
    # 7.38 Lifesteal Amp as the table above it (owner 2026-11-06): the list rule of abilities gives each its icon
    from patch.mech_abilities import ability_list_rows
    raw = "<br>".join(["Lifestealer's Open Wounds heals attackers for a percentage of the damage done",
                       "Meepo's Ransack heals all Meepos a flat amount for each strike",
                       '<span class="pop-note">Holding Alt will describe it</span>'])
    rows, notes = ability_list_rows(raw, least=1)
    assert "life_stealer_open_wounds" in rows and "meepo_ransack" in rows
    assert "Heals all Meepos a flat amount for each strike" in rows and notes == ["Holding Alt will describe it"]
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert ("can benefit from Lifesteal Amp\", t(\"REWORK\"), extra=inline_list(\"Lifestealer's Open Wounds" in p738)


def test_a_story_opens_its_list_before_a_new_row():
    # owner 2026-11-07, 7.38 Roshan: "Now has +25% base Slow Resistance" stood above the REWORK story, "должна быть там,
    # где и другие"
    from patch.page import _sort_changes_li
    new = '<li data-tag="buff new"><span class="badge new" data-tag="new">NEW</span><span class="row-text">n</span></li>'
    story = ('<li class="mech-desc li-notag mech-story" data-tag="rework"><span class="row-tag-empty"></span>'
             '<span class="row-text">s</span></li>')
    nerf = '<li data-tag="nerf"><span class="badge nerf-text" data-tag="nerf">NERF</span><span class="row-text">k</span></li>'
    out = _sort_changes_li(f'<ul class="changes">{story}{new}{nerf}</ul>')
    assert out.index("mech-story") < out.index(">NEW<") < out.index(">NERF<")


def test_how_neutrals_cast_a_new_ability_goes_under_its_question_mark():
    # "это по сути не изменение, а доп. информация механики нейтральных крипов" (7.38 Boglet, Marshmage)
    from tools.patchgen.post_general import _postprocess_neutral_cast_notes
    lines = ['    W(li("Active: Creates a barrier bubble. Cooldown: 16s"))',
             '    W(li("Neutrals will cast this ability on a random ally that is below 50% health", t("MISC")))']
    assert _postprocess_neutral_cast_notes(lines) == [
        '    W(li("Active: Creates a barrier bubble. Cooldown: 16s", extra=inline_note("Neutrals will cast this ability '
        'on a random ally that is below 50% health")))']
    # after a change row it is a change of its own and stays (7.38 Petrify)
    changed = ['    W(li("DPS increased from 75 to 100", b(75, 100)))',
               '    W(li("Neutrals will autocast this ability only if the Shaman has less than 90% health", t("MISC")))']
    assert _postprocess_neutral_cast_notes(changed) == changed
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert 'W(li("Neutrals will cast this ability' not in p738


def test_the_map_square_opens_over_the_terrain_stats_page():
    js = (ROOT / "src" / "js" / "terrain-stats-rows.js").read_text(encoding="utf-8")
    assert "closest('a.ts-thumb')" in js and "e.preventDefault()" in js


def test_creep_nested_notes_stay_under_their_parent():
    """A nested note goes with its parent's ability, whatever words it has itself: "Now burns 100 mana" under "Mana
    Burn reworked" stood as the unit's own row, the deeper ones under other rows."""
    from patchgen import entities
    lines = entities._render_neutral_creep({
        "name": "npc_dota_neutral_satyr_soulstealer", "localized_name": "Satyr Mindstealer",
        "neutral_creep_notes": [_note(1, "Mana Burn reworked"), _note(2, "Now burns 100 mana"),
                                _note(3, "Deals damage equal to mana burned"), _note(4, "Illusions take full damage"),
                                _note(1, "Health increased from 600 to 700")]})
    rework = [x for x in lines if "Mana Burn reworked" in x]
    assert len(rework) == 1
    for child in ("Now burns 100 mana", "Deals damage equal to mana burned", "Illusions take full damage"):
        assert child in rework[0], child
        assert sum(child in x for x in lines) == 1, child
    health = next(i for i, x in enumerate(lines) if "Health increased" in x)
    ability = next(i for i, x in enumerate(lines) if x.startswith("W(ability("))
    assert health < ability                      # the unit's own row stays the unit's


def test_creep_nested_note_naming_another_ability_stays_with_parent():
    from patchgen import entities
    pairs = entities.CREEP_ABILS.get("npc_dota_neutral_satyr_soulstealer", [])
    names = [(entities.ABILS_SLIM.get(s) or {}).get("dname") for s in pairs]
    names = [n for n in names if n]
    if len(names) < 1:
        return
    lines = entities._render_neutral_creep({
        "name": "npc_dota_neutral_satyr_soulstealer", "localized_name": "Satyr Mindstealer",
        "neutral_creep_notes": [_note(1, "Health reworked"), _note(2, f"No longer scales with {names[0]}")]})
    assert not any(x.startswith("W(ability(") for x in lines)


def test_general_rows_about_roshan_go_in_his_block():
    """Owner 2026-10-30: "Starting from his second death, Roshan now always drops Roshan's Banner" — in the Roshan
    block; "Teleport time to Roshan's outposts" stays a map row."""
    lines = ['W(section("General Updates"))', 'W(ul_open())',
             'W(li("Starting from his second death, Roshan now always drops Roshan\'s Banner", t("NEW")))',
             'W(li("Teleport time to Roshan\'s outposts decreased from 6s to 4s", b(6, 4)))', 'W(ul_close())', '',
             '# ===== NEUTRAL CREEP UPDATES =====', 'W(section("Neutral Creep Updates"))']
    out = g._postprocess_roshan_block(lines)
    k = out.index(g.ROSHAN_HEADER)
    assert "Roshan now always drops" in out[k + 2] and "outposts" not in "".join(out[k:])
    assert out.index('# ===== NEUTRAL CREEP UPDATES =====') > k


def test_a_general_subgroup_of_lists_is_a_mechanic_block():
    lines = ['W(section("General Updates"))', 'W(subgroup("Teleport Classification"))', 'W(ul_open())',
             'W(li("The following are considered a Teleport", t("MISC"), extra=inline_list("Twin Gates<br>Chen: Divine '
             'Favor")))', 'W(ul_close())', 'W(subgroup("Breakability Update"))', 'W(ul_open())',
             'W(li("The following are now Fully Disabled by Break", t("NERF"), extra=inline_list("Batrider: Smoldering '
             'Resin")))', 'W(ul_close())']
    out = g._postprocess_mechanic_lists(lines)
    # no tags in a mechanic block (owner 2026-10-30: "везде убрать теги")
    assert out[1] == 'W(plain_header("Teleport Classification", new="New mechanic", one_box=True))'
    assert out[5] == 'W(plain_header("Breakability Update", new="Reworked mechanic", one_box=True))'


def test_a_mechanic_blocks_plain_sentences_go_under_the_table_they_speak_of():
    """'"Breakable: Yes" … partially or fully …' → the Fully table; "… partially disabled … alt+tooltip …" → the
    Partially table; "The breakability rules … updated" → the first table. The rows themselves go."""
    lines = ['W(section("General Updates"))', 'W(subgroup("Breakability Update"))', 'W(ul_open())',
             'W(li("The following are now Fully Disabled by Break", t("NERF"), extra=inline_list("Batrider: Smoldering '
             'Resin")))',
             'W(li("The following are now Partially Disabled by Break", t("NERF"), extra=inline_list("Ember Spirit: '
             'Immolation")))',
             'W(li("The breakability rules have been updated", t("MISC")))',
             'W(li("\\"Breakable: Yes\\" has been added to all abilities that are partially or fully disabled", t("MISC")))',
             'W(li("All abilities that are partially disabled by Break have an alt+tooltip line", t("MISC")))',
             'W(ul_close())']
    out = g._postprocess_mechanic_lists(lines)
    fully = next(ln for ln in out if "Fully Disabled" in ln)
    part = next(ln for ln in out if "Partially Disabled" in ln)
    assert "rules have been updated" in fully and "Breakable: Yes" in fully and "alt+tooltip" in part
    # owner 2026-10-30: sentences about the game's tooltips are a "?" on the table's words, the rest a line of it
    assert 'pop-lead\\">The breakability rules' in fully and 'pop-tip\\">\\"Breakable: Yes' in fully
    assert 'pop-tip\\">All abilities that are partially' in part
    assert not any("t(\"MISC\")" in ln for ln in out)


def test_a_hero_ability_list_is_a_table_led_by_its_row_with_items_on_a_line_of_their_own():
    """Owner 2026-10-30: the row's words lead the table, items are not heroes, no "How" column (a "?" on the ability),
    a long list in two pairs of columns."""
    import patch.mech_abilities as ma
    from patch.state import _State
    keep = _State.current_patch_version
    _State.current_patch_version = "7.37"
    try:
        html, notes = ma.hero_ability_rows("Town Portal Scroll<br>Chen: Divine Favor<br>Visage: Summon Familiars "
                                           "recall (Faithful Followers)", row_text="The following are considered a "
                                           "Teleport")
        long_raw = "<br>".join(["Alchemist: Greevil's Greed", "Batrider: Smoldering Resin", "Bloodseeker: Thirst",
                                "Bounty Hunter: Jinada", "Chaos Knight: Reins of Chaos", "Clockwerk: Armor Power",
                                "Crystal Maiden: Cold Comfort", "Dark Seer: Heart of Battle", "Dark Willow: Pixie Dust",
                                "Death Prophet: Witchcraft", "Enigma: Gravity Well", "Faceless Void: Distortion Field"])
        long_html, _n = ma.hero_ability_rows(long_raw)
        # one row per hero, his abilities side by side (owner 2026-10-30: "не дублируй героя")
        oracle, _n = ma.hero_ability_rows("Oracle: Clairvoyant Curse<br>Oracle: Clairvoyant Cure")
    finally:
        _State.current_patch_version = keep
    assert "The following are considered a Teleport:" in html and "mech-captioned" in html
    # items are rows as heroes are (owner 2026-10-30), the header says both
    assert 'mech-hero mech-hero-item' in html and "Town Portal Scroll" in html and ">Hero or item<" in html
    # a short list: Visage's "recall (Faithful Followers)" in a Details column (owner 2026-10-30); a long one in two
    # pairs keeps it behind a "?"
    assert ">How<" not in html and ">Details<" in html and "mech-cols-hero3" in html
    assert ">Details<" not in long_html
    assert "mech-cols-hero4" in long_html
    assert oracle.count('class="mech-hero"') == 1 and "Clairvoyant Curse" in oracle and "Clairvoyant Cure" in oracle
    # an item's own active from the game's tooltip (owner 2026-10-30: "у предметов тоже есть способности")
    assert '>Teleport</span>' in html


def test_items_in_a_hero_table_show_their_own_active():
    """Town Portal Scroll → Teleport, Boots of Travel (an upgrade of the scroll) → Teleport, Book of Shadows → Shadows,
    Force Boots → Force; Twin Gates, a map object the game names no ability of: a short dash."""
    import patch.mech_abilities as ma
    from patch.state import _State
    keep = _State.current_patch_version
    _State.current_patch_version = "7.37"
    try:
        names = {n: ma._item_ability(n, "7.37") for n in ("Town Portal Scroll", "Boots of Travel", "Boots of Travel 2",
                                                          "Book of Shadows", "Force Boots", "Twin Gates")}
        html, _n = ma.hero_ability_rows("Twin Gates<br>Chen: Divine Favor")
    finally:
        _State.current_patch_version = keep
    assert names == {"Town Portal Scroll": "Teleport", "Boots of Travel": "Teleport", "Boots of Travel 2": "Teleport",
                     "Book of Shadows": "Shadows", "Force Boots": "Force", "Twin Gates": None}
    assert '<span class="mech-none">–</span>' in html


def test_roshans_drops_link_to_their_changes_pages():
    row = ('W(li("Starting from his third death Roshan now drops Refresher Shard and Cheese during daytime or '
           'Aghanim\'s Blessing during night", t("REWORK")))')
    out = g._link_items(row)
    assert out.count("item_link(") == 3 and 'item_link("Aghanim\'s Blessing")' in out
    from patch.item_links import item_page
    assert item_page("Aghanim's Blessing") == "ultimate-scepter-2" and item_page("Refresher Shard") == "refresher-shard"


@pytest.mark.parametrize("line, label", [
    ("Chen: Divine Favor", "Chen: Divine Favor"),                     # Valve's 7.37 form "Hero: Ability"
    ("Twin Gates", "Twin Gates"),                                     # a map object among items
    ("Town Portal Scroll", "Town Portal Scroll"),
    ("Batrider: Smoldering Resin", "Batrider: Smoldering Resin"),     # a 7.37 innate gone since: the patch's files
    ("Dark Seer: Heart of Battle", "Dark Seer: Heart of Battle"),     # a facet's ability: the facet's icon
    ("Rubick: Might and Magus", "Rubick: Might and Magus"),           # "and" inside a name
    ("Beastmaster: Call of the Wild Hawk Dive Bomb", "Beastmaster: Call of the Wild Hawk"),
    ("Lone Druid: Spirit Bear's Return", "Lone Druid: Spirit Bear's Return"),
])
def test_7_37_list_lines_get_an_icon(line, label):
    import patch.mech_abilities as ma
    from patch.state import _State
    keep = _State.current_patch_version
    _State.current_patch_version = "7.37"
    try:
        parsed = ma._parse_line(line)
    finally:
        _State.current_patch_version = keep
    assert parsed and parsed[0] == label and parsed[1]


def test_drunken_brawlers_stance_rows_are_stance_blocks():
    """Owner 2026-10-30: "у нас вроде для drunken brawler stances есть отдельное оформление" — as 7.40's stance blocks,
    each its icon, the row without the stance's name; the parent keeps its other rows."""
    lines = ['W(ability("Drunken Brawler", slug="brewmaster_drunken_brawler"))', "W(ul_open())",
             'W(li("Earth Brawler bonus armor rescaled from 1/3/5/7/9 to 1/3/5/7", b([3, 5, 7, 9], [1, 3, 5, 7])))',
             'W(li("No longer an innate ability", t("REWORK")))',
             'W(li("Void Brawler bonus status resistance now stacks with other sources", t("BUFF")))', "W(ul_close())"]
    out = g._postprocess_stance_blocks(lines)
    assert out[:4] == [lines[0], lines[1], lines[3], lines[5]]
    assert out[4] == 'W(ability("Earth Brawler", slug="brewmaster_drunken_brawler_earth"))'
    assert out[6].startswith('W(li("Bonus armor rescaled from')
    assert 'W(ability("Void Brawler", slug="brewmaster_drunken_brawler_void"))' in out
    assert any(ln.startswith('W(li("Bonus status resistance now stacks') for ln in out)


def test_a_tooltips_named_parts_are_paragraphs():
    """Drunken Brawler's tooltip: a line per stance, named in colour — a paragraph each, the name bold (owner
    2026-10-30: "раздели на абзацы, тут слишком сплошной текст")."""
    from patch.cards_ability_change import _named_parts, game_ability_desc
    paras = game_ability_desc("brewmaster_drunken_brawler", "7.36c")
    assert len(paras) == 5 and paras[0].startswith("Brewmaster can switch stances")
    assert paras[1].startswith("<b>Earth Brawler</b> — Grants") and paras[4].startswith("<b>Void Brawler</b>")
    assert _named_parts("Deals damage. Slows - enemies.") == ["Deals damage. Slows - enemies."]


def test_an_existing_roshan_blocks_items_link_too():
    """Owner 2026-10-30, 7.38 "Roshan no longer drops Aghanim's Blessing": a link, as 7.37's drops."""
    lines = ['W(section("General Updates"))', g.ROSHAN_HEADER, 'W(ul_open())',
             'W(li("Roshan no longer drops Aghanim\'s Blessing", t("DEL")))', 'W(ul_close())',
             'W(li("Aghanim\'s Blessing is elsewhere", t("MISC")))']
    out = g._postprocess_roshan_block(lines)
    assert out[3] == 'W(li("Roshan no longer drops " + item_link("Aghanim\'s Blessing"), t("DEL")))'
    assert out[5] == lines[5]                                  # only the Roshan block's rows


def test_mech_text_is_paragraphs_in_the_rows_box():
    """Owner 2026-10-30, 7.38 Roshan's pits: "не таблицей, а абзацем"."""
    from patch.mech_abilities import mech_text
    out = mech_text("Roshan starts in the <b>Bottom pit</b>.")
    assert out.startswith("<!--MECHTABLE-->") and "mech-head" not in out and "mech-cell" not in out
    assert '<span class="mech-abil-line">Roshan starts in the <b>Bottom pit</b>.</span>' in out


def test_placeholders_take_the_ability_values():
    fields = {"av_stun": "1.0 1.5 2.0", "damage_pct": "25"}
    assert ua._fill_placeholders("Stuns for %stun% s.", fields) == "Stuns for 1 / 1.5 / 2 s."
    assert ua._fill_placeholders("Deals %damage_pct%%% more.", fields) == "Deals 25% more."


def test_unknown_placeholder_never_leaks_the_raw_key():
    assert ua._fill_placeholders("Lasts %missing_key% s.", {}) == "Lasts ? s."


def test_spirit_bear_rows_land_on_lone_druids_patch(tmp_path, monkeypatch):
    (tmp_path / "patches").mkdir()
    page = (_block("hero", "lone-druid", "Lone Druid", "")
            + _block("creep-hero", "spirit-bear", "Spirit Bear", "Bear armor +1"))
    (tmp_path / "patches" / "9.99.html").write_text(page, encoding="utf-8")
    monkeypatch.setattr(ec, "DIST", tmp_path)
    monkeypatch.setattr(ec, "PATCHES", [{"version": "9.99"}])
    monkeypatch.setattr(ec, "RELEASE_HISTORY", [{"version": "9.99", "date": "05.10.2026"}])

    ents = ec._collect()

    druid = ents[("hero", "lone-druid")]["patches"][0]["body"]
    assert "Bear armor +1" in druid
    assert 'class="ec-sub-entity"' in druid
    assert "Bear armor +1" in ents[("creep-hero", "spirit-bear")]["patches"][0]["body"]


def test_a_creep_hero_after_an_item_is_not_folded(tmp_path, monkeypatch):
    (tmp_path / "patches").mkdir()
    page = (_block("hero", "lone-druid", "Lone Druid", "")
            + _block("item", "blink-dagger", "Blink Dagger", "")
            + _block("creep-hero", "spirit-bear", "Spirit Bear", "Bear armor +1"))
    (tmp_path / "patches" / "9.99.html").write_text(page, encoding="utf-8")
    monkeypatch.setattr(ec, "DIST", tmp_path)
    monkeypatch.setattr(ec, "PATCHES", [{"version": "9.99"}])
    monkeypatch.setattr(ec, "RELEASE_HISTORY", [{"version": "9.99", "date": ""}])

    assert "Bear armor" not in ec._collect()[("hero", "lone-druid")]["patches"][0]["body"]


def test_the_boar_card_opens_summon_razorback():
    from builders import entity_changes as ec
    assert ec._SUMMON_PARENT["npc_dota_beastmaster_boar"] == ("heroes/beastmaster.html", "Summon Razorback")


def test_same_worded_rows_take_their_own_spots(monkeypatch):
    rows = [("Several additional tree", ["738c_5.webp"], "tree"), ("Several additional tree", ["738c_9.webp"], "tree")]
    monkeypatch.setattr(terrain_notes, "_terrain_spot_index", lambda: {"7.38c": rows})
    reset_page_state()
    text = "Several additional tree and visual adjustments have been made to this area"
    assert "738c_5.webp" in terrain_notes.terrain_note("7.38c", text)[1]
    assert "738c_9.webp" in terrain_notes.terrain_note("7.38c", text)[1]
    reset_page_state()                                          # the next page counts from the first again
    assert "738c_5.webp" in terrain_notes.terrain_note("7.38c", text)[1]


def test_a_second_row_without_a_spot_of_its_own_gets_none(monkeypatch):
    rows = [("Several additional tree", ["738c_5.webp"], "tree")]
    monkeypatch.setattr(terrain_notes, "_terrain_spot_index", lambda: {"7.38c": rows})
    reset_page_state()
    text = "Several additional tree and visual adjustments have been made to this area"
    assert terrain_notes.terrain_note("7.38c", text)[1]
    assert terrain_notes.terrain_note("7.38c", text) == ("", "")      # Bottom Lane's: all its trees are in other pictures


def test_a_tree_note_shows_the_trees_layer_and_the_removed_tree_only_on_the_old_side():
    """7.38b "Removed several trees around camps" (owner 2026-10-27): "just show the trees layer, both pictures, and
    outline the removed trees red dashed on the left" — no mark on the right, the gap in the layer says it."""
    pytest.importorskip("PIL")
    from PIL import Image
    import scripts.gen.terrain_shots as ts
    groups = {"trees": {"removed": [(0, 0)], "added": [], "moved": []}}
    layer = {"old": [(0, 0), (300, 0)], "new": [(300, 0)]}           # the tree at (0, 0) is gone in the new map
    sides = {}
    for side in ("old", "new"):
        sides[side] = Image.new("RGB", (360, 360))
        ts._tree_layer(sides[side], 0, 0, 500, layer[side], 360)
        ts._outlines(sides[side], 0, 0, 500, groups, side, {"trees"}, 360, 3)
    # the layer is a neutral light square per tree (owner 2026-10-28: red / green mean old / new only)
    assert _light(sides["old"], (180, 180)) and not _light(sides["new"], (180, 180))
    assert _light(sides["new"], (180 + 108, 180))                   # the tree that stays: on both sides
    assert any(_red(sides["old"], (x, 180 - 23)) for x in range(160, 200))
    raw = sides["new"].tobytes()
    assert not any(raw[i] > 150 and raw[i + 1] < 120 for i in range(0, len(raw), 3))   # nothing red on the right


def test_a_terrain_row_with_a_percent_tints_its_number():
    """7.40 "Watcher night vision range decreased from 800 to 450" -44% (owner 2026-10-27): the number chip lightly in
    the % colour; a row with a text tag only keeps the plain number."""
    from patch.badges import b
    assert terrain_notes.terrain_num_chip(4, b(800, 450)) == '<span class="badge tnum tnum-nerf">4</span>'
    assert terrain_notes.terrain_num_chip(5, b(450, 800)) == '<span class="badge tnum tnum-buff">5</span>'
    tag = '<span class="badge del" data-tag="del" data-overall="nerf">DEL</span>'
    assert terrain_notes.terrain_num_chip(1, tag) == '<span class="badge tnum">1</span>'


def test_the_738c_gate_row_opens_the_picture_of_its_two_cells():
    # the row had no picture until 2026-11-05: two gridnav cells at the left of the Dire gate were blocked in 7.38b
    reset_page_state()
    phrase, shots = terrain_notes.terrain_note("7.38c", "Fixed unnecessary pathing blockers at the left of the entrance to the Dire Base through the team only gate")
    assert phrase == "pathing blockers"
    assert "738c_11.webp" in shots
