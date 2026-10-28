"""A reworked mechanic's list of abilities is rows of icons under the row, not a "?" (owner 2026-10-28: 7.40
Invulnerability Targeting, 7.38 Lifesteal, 7.41 Health Restoration / Lifesteal)."""
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
    css = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles.css"),
               encoding="utf-8").read()
    assert re.search(r"\.mech-abils\.mech-cols-icons \{ grid-template-columns: fit-content", css)


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
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css = open(os.path.join(root, "styles.css"), encoding="utf-8").read()
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
