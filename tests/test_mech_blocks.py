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


def test_general_rows_about_roshan_join_an_existing_roshan_block():
    """Owner 2026-11-18, 7.42: "Roshan gold per player decreased from 135 to 125" stood in Gold and Experience while
    Valve's own Roshan block was below it."""
    gold = 'W(li("Roshan gold per player decreased from 135 to 125", b(135, 125)))'
    lines = ['W(section("General Updates"))', 'W(subgroup("Gold and Experience"))', 'W(ul_open())',
             'W(li("Building bounty decreased", t("NERF")))', gold, 'W(ul_close())',
             g.ROSHAN_HEADER, 'W(ul_open())', 'W(li("Base respawn timer now decreases", t("MISC")))', 'W(ul_close())']
    out = g._postprocess_roshan_block(lines)
    k = out.index(g.ROSHAN_HEADER)
    assert gold not in out[:k] and out[k + 2:k + 5] == [lines[8], gold, 'W(ul_close())']
    assert out[:k] == lines[:4] + ['W(ul_close())']


def test_a_bosss_drops_by_death_are_a_table():
    """Owner 2026-11-18, 7.42 Tormentor "Now drops several items, similarly to Roshan": the list sat in the "?"."""
    row = ('W(li("Now drops several items, similarly to Roshan", t("NEW"), extra=inline_note("Now always drops '
           'Aghanim\'s Shard — New thing<br>Starting with the 2nd death, always drops Cheese with the same rules '
           '<span class=\\"pop-note\\">(Gold if everyone has it)</span>")))')
    out = g._postprocess_drop_table([row])[0]
    assert 'extra=mech_table(["When", "Drops", "Details"], [["Every death", item_link("Aghanim\'s Shard"), ' \
           '"New thing"], ["From the 2nd death", item_link("Cheese"), "With the same rules. Gold if everyone has it"]]' in out
    other = 'W(li("Now drops gold", t("NEW"), extra=inline_note("Only at night<br>And only once")))'
    assert g._postprocess_drop_table([other]) == [other]


def test_a_value_per_death_or_per_use_is_a_formula_table():
    """Owner 2026-11-18, 7.42 Tormentor: "175 to 125 + 50 per Tormentor's death" had no formula table."""
    gold = 'W(li("Gold reward per player changed from 175 to 125 + 50 per Tormentor\'s death", b(175, 125)))'
    out = g._postprocess_per_death([gold])[0]
    assert out.startswith('W(li_formula("Gold reward per player changed", "175", "125 + 50 per Tormentor\'s death", '
                          'lambda N: 175, lambda N: 125 + 50 * (N - 1), levels=[1, 2, 3, 4, 5, 6], '
                          'level_fmt=lambda N: f"#{N}"')    # the N-th kill: server.dll 6978 (2026-11-19)
    capped = ('W(li("Base damage reflection decreased from 35% to 15% + 5% per Tormentor death, up to 30%", b(35, 15), '
              'extra=inline_note("Still grows over time")))')
    out = g._postprocess_per_death([capped])[0]
    assert 'lambda N: min(30, 15 + 5 * (N - 1))' in out and 'value_fmt="{:g}%"' in out   # the cap on the whole base
    assert 'inline_note_text="Still grows over time"' in out
    shrine = ('W(li("Wisdom Shrine experience decreased from 200 + 300 per subsequent use to 200 + 200 per subsequent '
              'use", t("NERF")))')
    out = g._postprocess_per_death([shrine])[0]
    assert 'lambda N: 200 + 300 * (N - 1), lambda N: 200 + 200 * (N - 1)' in out and 'level_fmt=lambda N: f"#{N}"' in out
    plain = 'W(li("Gold reward per player decreased from 175 to 125", b(175, 125)))'
    assert g._postprocess_per_death([plain]) == [plain]


def test_valves_old_and_new_lists_over_the_same_keys_are_a_before_after_table():
    """Owner 2026-11-18, 7.42 Siege creep spawn count: the OLD / NEW game-time spans sat in the "?"."""
    row = ('W(li("Reworked Siege creep spawn count", t("REWORK"), extra=inline_note("OLD:<br>&nbsp;&nbsp;– 0:00-29:59: '
           'Every 5 minutes, 1 spawns<br>&nbsp;&nbsp;– 60:00+: Every 5 minutes, 3 spawn<br>NEW:<br>&nbsp;&nbsp;– '
           '0:00-29:59: Every 5 minutes, 1 spawns<br>&nbsp;&nbsp;– 60:00+: Every 2.5 minutes, 2 spawn"), '
           'also_dyn=[\'unit|siege-creep\']))')
    out = g._postprocess_old_new_table([row])[0]
    assert out == ('W(li("Reworked Siege creep spawn count", t("REWORK"), extra=mech_before_after("Game time", '
                   '[("0:00-29:59", "Every 5 minutes, 1 spawns", "Every 5 minutes, 1 spawns"), '
                   '("60:00+", "Every 5 minutes, 3 spawn", "Every 2.5 minutes, 2 spawn")]), '
                   'also_dyn=[\'unit|siege-creep\']))')
    other = 'W(li("Reworked", t("REWORK"), extra=inline_note("OLD:<br>A: 1<br>NEW:<br>B: 2")))'
    assert g._postprocess_old_new_table([other]) == [other]


def test_a_units_reworked_and_renamed_ability_is_an_old_new_card():
    """Owner 2026-11-18, 7.42 Ancient Black Dragon: Fireball → Searing Swoop stood as plain rows."""
    import pytest
    from patch.aghs_text import ability_text
    if not (ability_text("black_dragon_fireball", "7.41f") and ability_text("black_dragon_fireball", "7.42")):
        pytest.skip("no game files of 7.41f / 7.42 here")
    assert ability_text("black_dragon_fireball", "7.41f").startswith("Hurls a fire blast on the ground")
    head = 'W(ability("Searing Swoop", icon_url="../icons/abilities/black_dragon_fireball.png"))'
    lines = [head, 'W(ul_open())', 'W(li("Now causes the Black Dragon to take flight", t("NEW")))',
             'W(li("Duration decreased from 8/9/10/12s to 5/6/7/9s", b([8, 9, 10, 12], [5, 6, 7, 9])))',
             'W(li("Fireball ability renamed into Searing Swoop", t("MISC")))', 'W(ul_close())']
    out = g._postprocess_renamed_unit_ability(lines, "7.42")
    assert out[0] == '_black_dragon_fireball_old, _black_dragon_fireball_new = game_ability_pair("black_dragon_fireball", "7.42")'
    text = "\n".join(out)
    assert 'old=dict(name="Fireball", icon_url="../icons/abilities/black_dragon_fireball.png", desc=_black_dragon_fireball_old)' in text
    assert 'li("Fireball ability renamed into Searing Swoop", t("MISC"), covered=True),' in text
    assert 'li("Duration decreased from 8/9/10/12s to 5/6/7/9s", b([8, 9, 10, 12], [5, 6, 7, 9])),' in text
    assert head not in out
    plain = [head, 'W(ul_open())', lines[3], 'W(ul_close())']                 # no rename row: an ability's block
    assert g._postprocess_renamed_unit_ability(plain, "7.42") == plain


def test_a_neutral_creeps_general_label_keeps_its_own_rows():
    """7.42 proofread 2026-11-18: "General changes" of Neutral Creep Updates carried 24 rows (home jungles, removed
    camps) and the page showed none — the label was emitted without them."""
    out = g._render_neutral_creep({"name": "#DOTA_Patch_7_42_General_changes_Title", "localized_name": "General changes",
                                   "is_general_note": True, "neutral_creep_notes": [
                                       {"indent_level": 1, "note": "Medium Centaur camp removed"},
                                       {"indent_level": 1, "hide_dot": True, "note": "<br>"},
                                       {"indent_level": 1, "note": "Amount of Kobolds in Kobold camp decreased from 3 to 2"}]})
    text = "\n".join(out)
    assert 'W(plain_header("General changes", dynamics=False))' in text
    assert 'W(li("Medium Centaur camp removed", t("DEL")))' in text and "Kobolds in Kobold camp" in text
    label = g._render_neutral_creep({"name": "#x", "localized_name": "Flooded Camps", "is_general_note": True})
    assert [l for l in label if l.startswith("W(")] == ['W(plain_header("Flooded Camps", dynamics=False))']


def test_valves_text_tables_in_a_note_become_tables():
    # owner 2026-11-19, 7.42: the experience per level ("Level -- Old -- New -- …"), the building bounty list and the
    # neutral tier timings were long "?" lists
    xp = ('W(li("Total experience increased from 1 to 2", b(1, 2), extra=inline_note("Level -- Old -- New<br>2 -- 240 -- '
          '250<br>3 -- 400 -- 400<br>4 -- 520 -- 550<br>An easy way is to use this formula: 0.5x^2 + 3 where X is the level")))')
    out = g._postprocess_dash_table([xp])[0]
    assert 'extra=mech_table(["Level", "Old", "New"], [["2", "240", "250"], ["3", "400", "400"], ["4", "520", "550"], ' \
           '"An easy way is to use this formula: " + mech_formula("0.5x^2 + 3") + " " + "where X is the level"], ' \
           'labels=False)' in out
    tiers = ('W(li("Number of item tiers decreased from 5 to 4", t("REWORK"), extra=inline_note("Tier 1 - 0:00<br>Tier 2 - '
             '15:00<br>Infinite Madstone - 65:00")))')
    assert 'mech_table(["Tier", "Available at"], [["Tier 1", "<b>0:00</b>"], ["Tier 2", "<b>15:00</b>"], ' \
           '["Infinite Madstone", "<b>65:00</b>"]])' in g._postprocess_dash_table([tiers])[0]
    bounty = ('W(li("Building bounty decreased", t("NERF"), extra=inline_note("Tier 1 tower gold decreased from 110-130 to '
              '100<br>Tier 2 tower gold decreased from 90 to 75<br>Barracks gold rescaled from 90-135 to 100")))')
    assert 'extra=mech_before_after("Change", [("Tier 1 tower gold", "110-130", "100"), ' \
           '("Tier 2 tower gold", "90", "75"), ("Barracks gold", "90-135", "100")])' in g._postprocess_from_to_list([bounty])[0]


def test_long_level_tables_lie_across_and_shared_values_pivot():
    # owner 2026-11-19: the 29-row experience column and the ten building lines were still "массивные"
    rows = "<br>".join(f"{n} -- {n * 10} -- {n * 10 + (5 if n % 2 else 0)} -- {n}" for n in range(2, 14))
    xp = f'W(li("Experience increased", b(1, 2), extra=inline_note("Level -- Old -- New -- Total Increase<br>{rows}")))'
    out = g._postprocess_dash_table([xp])[0]
    assert 'extra=mech_level_table(["Level", "2", "3",' in out and '["Old", "20", "30",' in out
    assert '["Total Increase", "2", "3",' in out
    from patch.mech_abilities import mech_level_table
    html = mech_level_table(["Level", "2", "3"], [["Old", "20", "30"], ["New", "20", "35"]])
    assert 'style="--mech-lv:2"' in html and '<span class="iab-lv iab-buff mech-lv-changed">35</span>' in html and \
        'mech-lv-changed">20</span>' not in html
    bounty = ('W(li("Building bounty decreased", t("NERF"), extra=inline_note("Tier 1 tower last hit gold decreased from '
              '110-130 to 100<br>Tier 1 tower gold per player decreased from 90 to 75<br>Tier 2 tower last hit gold '
              'decreased from 130-150 to 125<br>Tier 2 tower gold per player decreased from 110 to 100<br>Barracks last '
              'hit gold rescaled from 90-135 to 100")))')
    out = g._postprocess_from_to_list([bounty])[0]
    assert 'extra=mech_table(["", "Last hit gold", "Gold per player"], [["Tier 1 tower", mech_change_cell("110-130", ' \
           '"100"), mech_change_cell("90", "75")], ["Tier 2 tower", ' in out
    assert '["Barracks", mech_change_cell("90-135", "100"), "–"]' in out and 'cls="mech-grid"' in out


def test_a_list_of_summons_is_written_as_hero_and_ability():
    # owner 2026-11-19: the Pip Health list was a column of words, not the icons and pairs of columns of the others
    assert g._owner_form("Gyrocopter's Homing Missile") == "Gyrocopter: Homing Missile"
    assert g._owner_form("Clinkz' Skeleton Archers") == "Clinkz: Skeleton Archers"
    assert g._owner_form("Roshan's Banner") == "Roshan's Banner"                 # an item's own name
    assert g._owner_form("Couriers") == "Couriers"
    from patch.mech_abilities import _item_icon, _parse_line
    assert _item_icon("Observer Wards") and _parse_line("Techies: M.A.D.") and _parse_line("Tidehunter: Dead in the Water")


def test_every_item_a_mechanic_row_names_is_an_icon():
    # owner 2026-11-19: "Slark's Pounce — тоже должно быть иконкой. Voodoo Masks …, a Tier 4 Evolved Enchantment, a Desolator"
    lines = ['W(plain_header("Item Potency", new="Reworked mechanic"))', 'W(ul_open())',
             'W(li("Any hero attacking with a Tier 4 Evolved Enchantment, so if they have a Desolator", t("REWORK")))',
             'W(li("Spell Lifesteal from two Voodoo Masks will provide +30%", t("REWORK")))', 'W(ul_close())',
             'W(plain_header("Global Mechanics"))', 'W(li("A Desolator elsewhere", t("MISC")))']
    out = g._postprocess_mechanic_name_icons(lines)
    assert out[2].endswith(", examples={'Evolved Enchantment': 'Evolved Enchantment', 'Desolator': 'Desolator'}))")
    assert ", examples={'Voodoo Masks': 'Voodoo Mask" in out[3] and "'Lifesteal'" not in out[3]   # a stat, no icon
    assert out[6] == lines[6]                                                          # not a mechanic block


def test_round_three_rules_of_the_742_proofread():
    # owner 2026-11-19, third round on 7.42
    # Glyph under Valve's Subtitle -> Team Abilities, after the whole category (not between its cards)
    lines = ['W(plain_header("Lane Creeps, Towers and Bases"))', 'W(subgroup("Glyph of Fortification"))', 'W(ul_open())',
             'W(li("Now has 2 charges", t("NEW")))', 'W(ul_close())', 'W(unit_header("Courier", "x.png"))',
             'W(ul_open())', 'W(li("Couriers now have fragile pip health", t("NEW")))', 'W(ul_close())',
             'W(plain_header("Map Objectives"))']
    out = g._postprocess_team_abilities(lines)
    k = out.index('W(plain_header("Team Abilities"))')
    assert out[k - 1] == 'W(ul_close())' and out[k - 4].startswith('W(unit_header("Courier"')
    assert out[k + 3] == 'W(li("Now has 2 charges", t("NEW")))' and out[-1] == 'W(plain_header("Map Objectives"))'
    # a rune named without Valve's colon -> its block with the rune's icon
    runes = ['W(section("General Updates"))', 'W(ul_open())',
             'W(li("Invisibility Rune now also provides Disguise buff", t("NEW")))',
             'W(li("Illusions created by Illusion Rune now have 40% Item Potency", t("MISC")))', 'W(ul_close())']
    text = "\n".join(g._postprocess_rune_rows(runes))
    assert 'W(ability("Invisibility Rune", icon_url="../icons/runes/invisibility.png"' in text
    assert 'W(li("Now also provides Disguise buff", t("NEW")))' in text
    assert 'W(ability("Illusion Rune", icon_url="../icons/runes/illusion.png"' in text
    # a changed value in a table: dim old, coloured new with its %
    from patch.mech_abilities import mech_change_cell, mech_level_table
    cell = mech_change_cell("110-130", "100")
    assert '<span class="mech-old">110-130</span>' in cell and 'iab-nerf' in cell and '−17%' in cell
    assert 'iab-buff' in mech_change_cell("90", "100")
    # more experience to a level is worse: red with l=True
    html = mech_level_table(["Level", "2"], [["Old", "240"], ["New", "250"]], l=True)
    assert 'iab-lv iab-nerf mech-lv-changed">250<' in html


def test_a_system_block_is_told_as_a_paragraph():
    # owner 2026-11-19, Pip Health: the intro and the rules as people say them, the units a table of icons
    group = [{"indent_level": 1, "note": "Standardized rules for units that take a fixed number of hits"},
             {"indent_level": 1, "note": "All units are now able to damage units with health bar pips",
              "info": "* Couriers<br>* Gyrocopter's Homing Missile"},
             {"indent_level": 2, "note": "Attacks from heroes deal 1 full pip per attack"},
             {"indent_level": 2, "note": "Attacks from illusions and creeps deal 1/4 pip per attack"},
             {"indent_level": 1, "note": "Some units have a Fragile debuff", "info": "Courier and Roshan's Banner"}]
    from tools.patchgen import general
    story = general._story_of(group, "REWORK")
    assert story.startswith('W(mech_story(["Standardized rules for units that take a fixed number of hits. All units are '
                            'now able to damage units with health bar pips: attacks from heroes deal 1 full pip per '
                            'attack; attacks from illusions and creeps deal 1/4 pip per attack.", "Some units have a '
                            'Fragile debuff (" + mech_example("Courier", label="Courier")')
    assert 'table=mech_list(info_tip("Couriers", "Gyrocopter: Homing Missile"))' in story


def test_map_file_changes_no_note_names_get_rows():
    from tools.patchgen.post_terrain import map_file_rows, _postprocess_map_file_rows
    diff = {"entities": {"heroSpawns": {"old": [[-6700, -6700], [6836, 6554]], "new": [[-6568, -6552], [6312, 6088]]},
                         "couriers": {"old": [[7010, 6387]], "new": [[6600, 5992]]}},
            "currentAreas": {"old": [1, 2], "new": [1, 2, 3]}, "wards": {"lost": "10", "gained": "4"}}
    rows = dict((t.split()[0], t) for _k, t in map_file_rows(diff))
    assert rows["Hero"] == "Hero spawn points moved: Dire 701 units, Radiant 198 units"
    assert rows["Streams"] == "Streams have 1 more sections with a current (3 instead of 2)"
    assert rows["No-ward"] == "No-ward ground changed: 10 cells became no-ward, 4 became wardable"
    page = ['W(plain_header("Terrain Changes", terrain_link="7.42"))', 'W(subgroup("Miscellaneous"))', 'W(ul_open())',
            'W(li("Dire fountain moved toward the Ancient", t("REWORK")))', 'W(ul_close())']
    out = _postprocess_map_file_rows(page, "7.42")          # the real 7.42 diff: "toward" is not a word about wards
    assert any(l.startswith('W(li("No-ward ground changed:') for l in out) and out[-1] == 'W(ul_close())'


def test_a_teaser_row_has_its_own_chip_and_no_place_in_the_cells():
    from patch.badges import t
    from patch.row_scores import _DYN_TAG_WHITELIST
    assert t("TEASER") == '<span class="badge teaser" data-tag="teaser">TEASER</span>'
    assert "teaser" not in _DYN_TAG_WHITELIST
    assert g._guess_tag("Y'ai 'ng'ngah, Shuggoth h'ee. Shuggoth fhtagn. Shuggoth ftaghu") == "TEASER"
    import pathlib                                    # its tile on the patch pages has an icon of its own
    css = (pathlib.Path(__file__).resolve().parents[1] / "src" / "css" / "patch-tag-marks.css").read_text(encoding="utf-8")
    assert '.tag-marks .badge[data-tag~="teaser"] { --tm: url(' in css


def test_valves_starred_list_is_a_list_the_block_opens():
    row = 'W(li("Abilities that pierce", t("REWORK"), extra=inline_note("* Batrider: Flaming Lasso <br> * Pudge: Dismember")))'
    assert g._postprocess_star_lists([row])[0] == \
        'W(li("Abilities that pierce", t("REWORK"), extra=inline_list("Batrider: Flaming Lasso<br>Pudge: Dismember")))'


def test_renames_are_old_new_headers():
    # owner 2026-11-19: "все ренеймы оформляем по одному типу" — a unit as an ability: "Old → New", no rename row
    lines = ['W(unit_header("Dark Troll Trapper", NEUTRAL_CDN + "dark_troll.png"))', 'W(ul_open())',
             'W(li("Hill Troll (from Dark Troll camp) renamed to Dark Troll Trapper", t("MISC")))', 'W(ul_close())',
             'W(item_header("Tranquil Boots"))', 'W(item_abilities_change(', '    old=["Passive: Break. Lose regen."],',
             '    new=["Passive: Respite. Lose regen."]))', 'W(ul_open())',
             'W(li("Break renamed to Respite", t("MISC")))', 'W(ul_close())']
    out = g._postprocess_renames(lines)
    assert out[0] == 'W(unit_header("Dark Troll Trapper", NEUTRAL_CDN + "dark_troll.png", old_title="Hill Troll"))'
    assert out[1] == 'W(item_header("Tranquil Boots"))'                       # the unit's empty list went
    assert 'W(li("Break renamed to Respite", t("MISC"), covered=True))' in out


def test_new_creep_abilities_are_new_ability_cards():
    import pytest
    from patch.aghs_text import ability_text
    if not ability_text("odobenus_blight", "7.42"):
        pytest.skip("no game files of 7.42 here")
    lines = ['W(unit_header("Odobenus Footman", NEUTRAL_CDN + "odobenus_footman.png", new="New Level 3 Melee Creep"))',
             'W(ul_open())', 'W(unit_sheet("odobenus_footman", version="7.42"))',
             'W(li("New Level 3 Melee Creep", t("MISC"), extra=inline_note("500 Health")))',
             'W(li("Odobenus Blight: Passive Ability", t("MISC"), extra=inline_note("Attacks reduce armor")))', 'W(ul_close())']
    out = g._postprocess_new_creep_abilities(lines, "7.42")
    assert out[3] == 'W(li("New Level 3 Melee Creep", t("MISC"), extra=inline_note("500 Health"), covered=True))'
    assert out[4:8] == ['W(ul_close())', 'W(new_ability("Odobenus Blight", "odobenus_blight", version="7.42", '
                        'icon_url="../icons/abilities/odobenus_footman_odobenus_blight.png"))', 'W(ul_open())',
                        'W(li("Odobenus Blight: Passive Ability", t("MISC"), extra=inline_note("Attacks reduce armor"), '
                        'covered=True))']


def test_a_replaced_or_reworked_unit_ability_is_a_card():
    import pytest
    from patch.aghs_text import ability_text
    if not ability_text("mud_golem_hurl_boulder", "7.41f"):
        pytest.skip("no game files of 7.41f / 7.42 here")
    mud = ['W(ability("Hurl Boulder", icon_url="../icons/abilities/mud_golem_hurl_boulder.png"))', 'W(ul_open())',
           'W(li("Hurl Boulder ability replaced with Hurl Big Boulder", t("REWORK")))', 'W(ul_close())']
    text = "\n".join(g._postprocess_renamed_unit_ability(mud, "7.42"))
    assert 'desc=game_ability_desc("mud_golem_hurl_boulder", "7.41f")' in text
    assert 'new=dict(name="Hurl Big Boulder"' in text and 'desc=game_ability_desc("mud_golem_hurl_big_boulder", "7.42")' in text
    assert 'summary="New ability."' in text
    kobold = ['W(ability("Steal Weapon", icon_url="../icons/abilities/kobold_disarm.png"))', 'W(ul_open())',
              'W(li("Ability Reworked", t("REWORK")))', 'W(ul_close())']
    text = "\n".join(g._postprocess_renamed_unit_ability(kobold, "7.42"))
    assert 'game_ability_pair("kobold_disarm", "7.42")' in text and 'summary="Ability reworked."' in text


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
