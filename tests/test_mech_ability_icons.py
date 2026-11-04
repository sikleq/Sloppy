"""A reworked mechanic's list of abilities is rows of icons under the row, not a "?" (owner 2026-10-28: 7.40
Invulnerability Targeting, 7.38 Lifesteal, 7.41 Health Restoration / Lifesteal)."""
from patch.css_bundle import read_css
import os
import re

from patch import elements
from patch.mech_abilities import mech_table
from patch.state import _State, reset_page_state


def _mech_row(text, extra=None, new="Reworked mechanic", section="General Updates"):
    """text / extra: callables, run inside the page (its notes are the page's own)."""
    reset_page_state()
    _State.current_patch_version = "7.40"
    try:
        elements.section(section)
        elements.plain_header("Invulnerability Targeting", new=new)
        elements.ul_open()
        return elements.li(text(), '<span class="badge rework" data-tag="rework">REWORK</span>',
                           extra=extra() if extra else "")
    finally:
        reset_page_state()


_SENTENCES = ("Items — Nullifier's Nullify can no longer target invulnerable units<br>"
              "Neutral Creeps — Satyr Banisher's Purge can no longer target invulnerable units<br>Heroes<br>"
              "&nbsp;&nbsp;– Dark Seer's Vacuum no longer affects invulnerable units<br>"
              "&nbsp;&nbsp;– Ogre Magi's Bloodlust can no longer target invulnerable units "
              "<span class=\"pop-note\">(Can still target invulnerable buildings)</span><br>"
              "&nbsp;&nbsp;– Sniper's Assassinate can no longer target invulnerable units<br>"
              "<span class=\"pop-note\">All of these were changed</span>")


def test_abilities_with_the_same_sentence_share_one_row_of_icons():
    row = _mech_row(lambda: "The following spells have been changed",
                   extra=lambda: elements.inline_note(_SENTENCES))
    # the sentence first, the icons after it, under a header (owner 2026-10-28, like 7.38 Lifesteal's table)
    assert ('<span class="mech-abil-row mech-head"><span class="mech-cell mech-label">Change</span>'
            '<span class="mech-cell">Items and abilities</span></span>') in row
    assert row.count('class="mech-cell mech-icons"') == 2
    assert 'data-tooltip="Nullifier&#x27;s Nullify"' in row and "icons/items/nullifier.png" in row
    assert 'data-tooltip="Dark Seer&#x27;s Vacuum"' in row and "dark_seer_vacuum.png" in row
    same = row.split('<span class="mech-cell mech-label">Can no longer target invulnerable units')[1]
    same = same.split('class="mech-abil-row"')[0]
    assert "nullifier.png" in same and "ogre_magi_bloodlust.png" in same and "sniper_assassinate.png" in same
    assert "satyr_trickster_purge.png" in same          # a neutral creep's, by the game's own name of the creep
    # Bloodlust's own caveat: a "?" after the row's sentence naming whose it is, not among the icons where it read as
    # one more ability (owner 2026-10-28); the list's closing note stays a line under the rows
    icons = same.split('<span class="mech-cell mech-icons">', 1)[1]
    assert "info-tip" not in icons
    assert ("Can no longer target invulnerable units <!--TIP-->" in row
            and "Ogre Magi&#x27;s Bloodlust: Can still target invulnerable buildings" not in row
            and "Ogre Magi's Bloodlust: Can still target invulnerable buildings" in row)
    # the list's closing note: in one line with the row's text, not the table's last line (owner 2026-10-28)
    assert ('The following spells have been changed. <span class="mech-row-note">All of these were changed</span>'
            in row.split('<span class="mech-abils">')[0])
    assert "Items —" not in row and ">Heroes<" not in row


def test_names_alone_are_one_row_of_icons_and_with_scepter_its_own():
    row = _mech_row(lambda: "Spells now only modify Health Restoration " + elements.info_tip(
        "Eye of Skadi's Cold Attack", "Sange", "Pudge's Rot with Aghanim's Scepter", "Audacious Enchantment",
        header="Affected spells:"))
    assert "items/skadi.png" in row and "items/sange.png" in row and "enhancement_audacious.png" in row
    assert "pudge_rot.png" in row
    assert "info-tip" not in row and "Affected spells:" not in row
    # next to a condition the plain ones are a row in the same columns, "Always", first: across the whole table they
    # stood apart and the icons column shrank to the Scepter's one icon (owner 2026-10-28, 7.41 "криво"); the
    # condition is the first column, the icons the second, under a header (owner, the same day)
    assert "mech-abil-only" not in row and 'class="mech-abils mech-cols-icons"' in row
    labels = re.findall(r'<span class="mech-cell mech-label">([^<]*)</span>', row)
    assert labels == ["Condition", "Always", "With Aghanim's Scepter"]
    assert '<span class="mech-cell">Items and abilities</span>' in row
    always = row.split('<span class="mech-cell mech-label">Always</span>')[1].split('class="mech-abil-row"')[0]
    assert "items/skadi.png" in always and "pudge_rot.png" not in always
    css = read_css()
    assert re.search(r"\.mech-abils\.mech-cols-icons \{ grid-template-columns: fit-content", css)


def test_reflected_damage_sources_are_a_table_of_icons():
    """7.41 "All sources of reflection damage now have an ALT-note": the [?] list as a table (owner 2026-10-28)."""
    # Valve's whole list, word for word: one name without an icon and the table falls back to a "?" (it did:
    # Retaliate is centaur_return, "Scream of Pain" has a small "of")
    row = _mech_row(lambda: "All sources of reflection damage now have an ALT-note " + elements.info_tip(
        "Tormentor's Reflect ability", "Blade Mail (both active and passive)", "Chipped Vest", "Rattlecage",
        "Axe's Counter Helix", "Bristleback's Quill Spray triggered by Bristleback passive",
        "Centaur Warrunner's Retaliate", "Nyx Assassin's Spiked Carapace", "Queen of Pain's Scream of Pain",
        "Razor's Storm Surge", "Shadow Demon's Disseminate", "Spectre's Dispersion",
        "Tidehunter's Anchor Smash triggered by Kraken Shell passive", "Viper's Corrosive Skin",
        "Warlock's Fatal Bonds",
        header="The following items and abilities deal reflected damage:"))
    assert row.count('class="ability-chip"') == 15
    assert "miniboss_reflect.png" in row and "items/blade_mail.png" in row and "bristleback_quill_spray.png" in row
    assert "centaur_return.png" in row and "queenofpain_scream_of_pain.png" in row
    row = "".join(re.split(r'(?=<span class="mech-cell mech-label">Triggered by Kraken)', row)[:1])
    labels = re.findall(r'<span class="mech-cell mech-label">([^<]*)', row)
    assert labels == ["Condition", "Always ", "Triggered by Bristleback passive"]
    assert "Blade Mail: Both active and passive" in row                  # its caveat: a "?" after "Always"


def test_one_box_block_puts_every_row_in_one_box_without_chips():
    """7.41 Reflected Damage (owner 2026-10-28): "всё это в одном блоке без тегов + таблица"."""
    from patch import page
    from patch.badges import t
    reset_page_state()
    _State.current_patch_version = "7.41"
    try:
        html = elements.section("General Updates") + elements.plain_header("Mechanics Changes")
        html += elements.subgroup("Reflected Damage", new="Reworked mechanic", one_box=True) + elements.ul_open()
        html += elements.li("Lifesteal doesn't apply to reflected damage", t("REWORK"))
        html += elements.li("Reflected damage cannot be reflected back", t("DEL"))
        html += elements.li("All sources now have an ALT-note " + elements.info_tip(
            "Axe's Counter Helix", "Bristleback's Quill Spray triggered by Bristleback passive"), t("QoL"))
        html += elements.ul_close()
    finally:
        reset_page_state()
    out = page._new_mech_rows(html)
    # one paragraph, the sentences through a full stop, not a line each (owner 2026-10-28: "глупо смотрится")
    lis = re.findall(r"<li\b[^>]*>", out)
    assert len(lis) == 1 and "mech-desc mech-first mech-last" in lis[0]
    assert ('<span class="row-text">Lifesteal doesn\'t apply to reflected damage. Reflected damage cannot be '
            'reflected back. All sources now have an ALT-note') in out
    chips = [out[m.start() - 80:m.start() + 60] for m in re.finditer('class="badge', out)]
    assert not chips and 'data-tag="rework del nerf qol"' in lis[0]   # no chips; every row's tag kept for the filters
    assert 'class="mech-abils mech-cols-icons"' in out.split("ALT-note", 1)[1]    # the table after the paragraph


def test_before_and_after_the_patch_is_a_table():
    from patch.mech_abilities import mech_before_after
    html = mech_before_after("Stat", [("Health Restoration", "Applies to all life gain except incoming heals",
                                       "Applies to all forms of life gain")])
    assert ('<span class="mech-cell mech-label">Stat</span><span class="mech-cell">Before</span>'
            '<span class="mech-cell">After</span>') in html
    assert '<span class="mech-cell mech-label">Health Restoration</span>' in html
    assert 'class="mech-abils mech-cols-3 mech-ba"' in html             # Before and After one width
    css = read_css()
    assert re.search(r"\.mech-cols-3\.mech-ba \{ grid-template-columns: fit-content\(30%\) minmax\(0, 1fr\) "
                     r"minmax\(0, 1fr\)", css)


def test_every_mechanic_list_of_7_41_is_a_table_on_the_page():
    """The built page: Health Restoration (2), Lifesteal (1), Reflected Damage (1) — none fell back to a "?"."""
    import pytest
    page = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist", "patches", "7.41.html")
    if not os.path.exists(page):
        pytest.skip("site not built")
    html = open(page, encoding="utf-8").read()
    assert html.count('class="mech-abils mech-cols-icons"') == 4
    assert "Tormentor&#x27;s Reflect" in html and 'Reflected Damage <span class="subgroup-new-type">' in html


def test_the_icons_column_says_what_its_icons_are():
    row = _mech_row(lambda: "Spells changed " + elements.info_tip(
        "Sniper's Assassinate", "Pudge's Rot with Aghanim's Scepter", header="Affected spells:"))
    assert '<span class="mech-cell">Abilities</span>' in row


def test_names_alone_without_a_condition_stay_one_row_across():
    row = _mech_row(lambda: "Spells now only modify Health Restoration " + elements.info_tip(
        "Eye of Skadi's Cold Attack", "Sange", header="Affected spells:"))
    assert 'class="mech-abil-row mech-abil-only"' in row and "Always" not in row


def test_a_list_with_an_ability_without_an_icon_is_not_drawn_as_icons():
    """No mixing: one line without an icon -> the list's lines as text rows (a Reworked mechanic), or a "?"."""
    note = lambda: elements.inline_list("Sniper's Assassinate<br>Sniper's Imaginary Shot")  # noqa: E731
    row = _mech_row(lambda: "Spells changed", extra=note)
    assert "ability-chip" not in row and '<span class="mech-abil-line">Sniper\'s Imaginary Shot</span>' in row
    row = _mech_row(lambda: "Spells changed", extra=note, new="New mechanic")
    assert "mech-abils" not in row and "info-tip" in row


_SOURCES = ('Attacks that do not proc Attack Modifiers <span class="pop-note">(Examples: Cleave)</span><br>'
            'Reflected damage<br>Any damage dealt to self or allies')


def test_a_reworked_mechanic_shows_a_plain_list_open_as_a_table():
    """7.38 Lifesteal "The following sources and targets do not provide any lifesteal" (owner 2026-10-28)."""
    row = _mech_row(lambda: "The following sources and targets do not provide any lifesteal",
                    extra=lambda: elements.inline_list(_SOURCES))
    # its examples are a column of icons, with a header (owner 2026-10-28: "в примерах нет иконок")
    assert 'class="mech-abils mech-cols-ex"' in row and '<span class="mech-cell">Examples</span>' in row
    assert '<span class="mech-cell mech-label">Reflected damage</span>' in row
    assert ('<span class="mech-cell mech-label">Attacks that do not proc Attack Modifiers</span>'
            '<span class="mech-cell mech-ex"><span class="ability-chip" data-tooltip="Cleave"') in row
    assert "info-tip" not in row
    # every column titled, an empty examples cell a short dash (owner 2026-10-28)
    assert '<span class="mech-cell mech-label">Sources and targets</span>' in row
    assert ('<span class="mech-cell mech-label">Reflected damage</span><span class="mech-cell mech-ex">–</span>'
            in row)


def test_examples_find_their_icons_and_the_rest_stays_a_question_mark():
    from patch.mech_abilities import _split_examples
    pre, chips = _split_examples("Effects that don't break Blink Dagger, like Orb of Venom or Necrophos' "
                                 "Heartstopper Aura")
    assert pre == "Effects that don't break Blink Dagger"
    assert "items/orb_of_venom.png" in chips[0] and "necrolyte_heartstopper_aura.png" in chips[1]
    _pre, chips = _split_examples("Example: Blade Mail return damage")
    assert "items/blade_mail.png" in chips[0] and 'data-tooltip="Blade Mail return damage"' in chips[0]
    _pre, chips = _split_examples("Examples: Cleave, Luna's Bouncing Glaives")
    assert "luna_moon_glaive.png" in chips[1]


def test_mech_table_lays_out_columns_under_the_row():
    row = _mech_row(lambda: "Lifesteal mechanics are now consistent across every ability",
                    extra=lambda: mech_table(["", "Applies to"],
                                             [["Lifesteal", "Attacks"], "Neither applies to pure damage"]))
    text = row.split('<span class="row-text">', 1)[1]
    assert text.startswith("Lifesteal mechanics are now consistent across every ability<span class=\"mech-abils "
                           "mech-cols-2\">")
    assert '<span class="mech-cell mech-label">Lifesteal</span><span class="mech-cell">Attacks</span>' in text
    assert '<span class="mech-abil-line">Neither applies to pure damage</span>' in text


def test_a_new_mechanic_keeps_its_plain_list_behind_the_question_mark():
    row = _mech_row(lambda: "The following sources and targets do not provide any lifesteal",
                    extra=lambda: elements.inline_list(_SOURCES), new="New mechanic")
    assert "mech-abil-line" not in row and "info-tip" in row


def test_clarifications_stay_behind_the_question_mark():
    """7.38 Tormentor "Or at Dire side in Turbo<br>Due to this …": notes, not a list the row introduces."""
    row = _mech_row(lambda: "Tormentor is also dependent on the day and night cycle",
                    extra=lambda: elements.inline_note(_SOURCES))
    assert "mech-abil-line" not in row and "info-tip" in row


def test_icons_grow_on_hover():
    css = read_css()
    assert re.search(r"\.ability-chip:hover > img \{[^}]*transform: scale\(", css)


def test_outside_general_updates_the_list_stays_a_note():
    """Mechanics live in General Updates; the rules do not reach other parts of the site (owner 2026-10-28)."""
    row = _mech_row(lambda: "Spells changed " + elements.info_tip("Sniper's Assassinate", "Dark Seer's Vacuum"),
                    section="Neutral Creep Updates")
    assert "mech-abils" not in row and "info-tip" in row


def test_two_tables_side_by_side_keep_their_rows_level():
    from patch.mech_abilities import mech_pair
    html = mech_pair(mech_table(["Type", "Physical damage"], [["Lifesteal", "From attacks"]]),
                     mech_table(["Against non-heroes"], [["Reduced by 40%"]]))
    assert 'class="mech-pair" style="--mech-rows:2"' in html
    assert '<span class="mech-cell">Reduced by 40%</span>' in html        # one column: centred, not a label


def test_outside_a_mechanic_block_the_list_stays_a_note():
    row = _mech_row(lambda: "Spells changed " + elements.info_tip("Sniper's Assassinate", "Dark Seer's Vacuum"),
                    new=None)
    assert "mech-abils" not in row and "info-tip" in row
