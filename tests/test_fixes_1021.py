"""Generator fixes of 2026-10-21 (owner's 7.41 review)."""
from patch import elements as el


def test_bold_mana_and_cooldown_labels_go_to_the_head():
    # "<b>Mana Cost:</b> 50." stayed in the text under a head that already showed 50 (7.41 Zealot)
    values, desc = el._iab_take_meta("Teleports units. <b>Mana Cost:</b> 50. <b>Cooldown:</b> 10s.")
    assert values == {"manacost": "50", "cooldown": "10"}
    assert desc == "Teleports units."


def test_a_renamed_ability_shows_old_arrow_new_in_its_header():
    html = el.ability("Summon Razorback", slug="beastmaster_summon_razorback", old_title="Call of the Wild Boar")
    assert ('<span class="ability-title-old">Call of the Wild Boar</span><span class="ability-title-arrow">→</span>'
            '<span class="ability-title-new">Summon Razorback</span>') in html


def test_the_boar_card_opens_summon_razorback():
    from builders import entity_changes as ec
    assert ec._SUMMON_PARENT["npc_dota_beastmaster_boar"] == ("heroes/beastmaster.html", "Summon Razorback")


def test_enchant_change_table_heads_its_stats_column():
    import re
    from pathlib import Path
    import pytest
    page = Path(__file__).resolve().parents[1] / "dist" / "patches" / "7.41.html"
    if not page.exists():
        pytest.skip("site not built")
    html = page.read_text(encoding="utf-8")
    assert re.search(r'class="ench-tiers ench-change"><span class="ench-row-h"><span class="ench-stat-h">Stats</span>',
                     html)


def test_a_covered_row_is_hidden_but_keeps_its_tag():
    from patch.badges import t
    html = el.li("Now also increases Battery Assault radius to 330", t("NEW"), covered=True)
    assert 'class="iab-covered covered-card"' in html and 'data-tag="buff new"' in html


def test_sub_ability_shows_the_ability_icon_and_name():
    html = el.sub_ability("rattletrap_jetpack", "Jetpack")
    assert 'src="../icons/abilities/rattletrap_jetpack.png"' in html and ">Jetpack</b>" in html


def test_talents_after_a_scepter_ability_get_no_aghanim_stripe():
    # Clockwerk 7.41: the talents under Overclocking (granted by Aghanim's Scepter) were marked as Scepter rows
    from patch.state import _State
    _State.current_ability_slug = "rattletrap_overclocking"
    el.subgroup("Talents")
    assert _State.current_ability_slug is None


def test_filter_keeps_a_header_only_ability_apart_from_its_rows():
    # Brewmaster 7.41: Primal Split (rows live in the Brewling blocks under it) stayed hidden after the Heroes
    # category filter was switched off
    from pathlib import Path
    js = (Path(__file__).resolve().parents[1] / "src" / "scripts.js").read_text(encoding="utf-8")
    assert "if (!ul) { headerOnly.push(block); return; }" in js


def test_talent_swap_marks_removed_new_and_moved_talents():
    # Batrider 7.41: Smoldering Resin moved L20 +4s -> L10 +1s; the rest are removed / brand-new talents
    from patch import talent_marks as tm
    swaps = [(10, "+50 Flamebreak Knockback Distance", "+1s Smoldering Resin Duration"),
             (20, "+4s Smoldering Resin Duration", "Attacks apply 1 Stack of Sticky Napalm")]
    tm._cache["x"] = {"Batrider": swaps}
    tm._content_file = lambda: "x"
    try:
        assert tm.mark("Level 10 Talent: +50 Flamebreak Knockback Distance replaced with +1s Smoldering Resin Duration",
                       "Batrider")[:2] == ("gone", "moved")
        assert tm.mark("Level 20 Talent: +4s Smoldering Resin Duration replaced with Attacks apply 1 Stack of Sticky Napalm",
                       "Batrider")[:2] == ("moved", "fresh")
    finally:
        del tm._content_file
        import importlib
        importlib.reload(tm)


def test_bug_note_is_a_bug_box_not_a_question_mark():
    html = el.bug_note("Kept the old bonus")
    assert 'class="info-tip bug-tip"' in html and 'class="bug-ico"' in html and ">?<" not in html
    # the owner's silhouette as a CSS mask (2026-10-22); the picture must ship with the site
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert (root / "icons" / "ui" / "bug.png").exists()
    assert "url('icons/ui/bug.png')" in (root / "styles.css").read_text(encoding="utf-8")


def test_a_brand_new_talent_is_gold_but_the_row_stays_swap():
    # as NEW the swap scored as a buff: 7.38's net went +54 -> +86
    from patch import talent_marks as tm
    from patch.badges import t
    from patch.state import _State
    tm._content_file = lambda: "z"
    tm._cache["z"] = {"Batrider": [(15, "+20 Movement Speed", "+30 Firefly Damage Per Second")]}
    _State.current_hero_title = "Batrider"
    try:
        text, badge, _ = el._mark_talent_swap("Level 15 Talent: +20 Movement Speed replaced with +30 Firefly Damage Per Second",
                                              t("SWAP"), "")
        assert 'iab-hl-new' in text and 'iab-hl-del' in text and 'data-tag="swap"' in badge
    finally:
        del tm._content_file
        import importlib
        importlib.reload(tm)


def test_same_talent_in_another_form_is_neither_removed_nor_new():
    # Arc Warden 7.41 "+50% Spark Wraith Damage -> +200 Spark Wraith Damage", Viper "+30 -> +20/40 Nethertoxin"
    from patch import talent_marks as tm
    tm._content_file = lambda: "y"
    tm._cache["y"] = {}
    try:
        assert tm.mark("Level 15 Talent: +30 Nethertoxin Min/Max Damage replaced with +20/40 Nethertoxin Min/Max Damage",
                       "Viper") == ("same", "same", "")
    finally:
        del tm._content_file
        import importlib
        importlib.reload(tm)


def test_plural_talent_is_the_same_talent():
    from patch import talent_marks as tm
    assert tm.key("+1 Acorn Shot Bounce") == tm.key("+2 Acorn Shot Bounces")


def test_game_checked_move_overrides_the_text_guess():
    # Rubick 7.41: the notes never say where Telekinesis Landing Damage went; the game files put it on Level 20
    from patch import talent_marks as tm
    from patch.state import _State
    tm._content_file = lambda: "w"
    tm._cache["w"] = {}
    _State.current_patch_version = "7.41"
    try:
        fate = tm.mark("Level 10 Talent: +165 Telekinesis Landing Damage replaced with -2s Telekinesis Cooldown", "Rubick")
        assert fate[0] == "moved" and "Level 20" in fate[2]
    finally:
        del tm._content_file
        import importlib
        importlib.reload(tm)


def test_facet_named_talent_row_is_a_swap():
    from patch import talent_marks as tm
    assert tm.SWAP_RE.match("Old Blood: Level 10 Talent +15% Bloodrage Spell Amplification replaced with +15% Amp")


def test_aghanim_upgrade_goes_in_brackets_before_the_summary_full_stop():
    html = el.ability_change(old=dict(name="X", slug="rattletrap_overclocking", desc=["Active (Aghanim's Scepter upgrade). A."]),
                             new=dict(name="X", slug="rattletrap_overclocking", desc=["B."]),
                             summary="Ability reworked.", tag="rework")
    assert "Ability reworked <span class=\"ac-aghs\">(Aghanim's Scepter upgrade)</span>." in html
    assert "Active (Aghanim" not in html


def test_aghanim_upgrade_words_move_from_card_text_to_its_summary():
    spec, kind = el._take_aghs({"desc": ["Active (Aghanim's Scepter upgrade). All abilities are supercharged:"]})
    assert kind == "scepter" and spec["desc"] == ["All abilities are supercharged:"]
    spec, kind = el._take_aghs({"desc": ["Granted by Aghanim's Scepter. Unit-targeted.", "x"]})
    assert kind == "scepter" and spec["desc"] == ["Unit-targeted.", "x"]
