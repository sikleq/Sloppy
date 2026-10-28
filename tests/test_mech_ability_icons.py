"""A reworked mechanic's list of abilities is rows of icons under the row, not a "?" (owner 2026-10-28: 7.40
Invulnerability Targeting, 7.38 Lifesteal, 7.41 Health Restoration / Lifesteal)."""
from patch import elements
from patch.state import _State, reset_page_state


def _mech_row(text, extra=None, new="Reworked mechanic"):
    """text / extra: callables, run inside the page (its notes are the page's own)."""
    reset_page_state()
    _State.current_patch_version = "7.40"
    try:
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
    assert row.count('class="mech-abil-text"') == 2
    assert 'data-tooltip="Nullifier&#x27;s Nullify"' in row and "icons/items/nullifier.png" in row
    assert 'data-tooltip="Dark Seer&#x27;s Vacuum"' in row and "dark_seer_vacuum.png" in row
    same = row.split('<span class="mech-abil-text">Can no longer target invulnerable units</span>')[0]
    assert "nullifier.png" in same and "ogre_magi_bloodlust.png" in same and "sniper_assassinate.png" in same
    assert "satyr_trickster_purge.png" in same          # a neutral creep's, by the game's own name of the creep
    # Bloodlust's own caveat: a "?" after the row's sentence naming whose it is, not among the icons where it read as
    # one more ability (owner 2026-10-28); the list's closing note stays a line under the rows
    icons = same.rsplit('<span class="mech-abil-icons">', 1)[1]
    assert "info-tip" not in icons
    assert ("Can no longer target invulnerable units <!--TIP-->" in row
            and "Ogre Magi&#x27;s Bloodlust: Can still target invulnerable buildings" not in row
            and "Ogre Magi's Bloodlust: Can still target invulnerable buildings" in row)
    assert '<span class="mech-abil-note">All of these were changed</span>' in row
    assert "Items —" not in row and ">Heroes<" not in row


def test_names_alone_are_one_row_of_icons_and_with_scepter_its_own():
    row = _mech_row(lambda: "Spells now only modify Health Restoration " + elements.info_tip(
        "Eye of Skadi's Cold Attack", "Sange", "Pudge's Rot with Aghanim's Scepter", "Audacious Enchantment",
        header="Affected spells:"))
    assert 'class="mech-abil-row mech-abil-only"' in row
    assert "items/skadi.png" in row and "items/sange.png" in row and "enhancement_audacious.png" in row
    assert '<span class="mech-abil-text">With Aghanim\'s Scepter</span>' in row and "pudge_rot.png" in row
    assert "info-tip" not in row and "Affected spells:" not in row


def test_a_list_with_an_ability_without_an_icon_stays_a_note():
    row = _mech_row(lambda: "Spells changed " + elements.info_tip("Sniper's Assassinate", "Sniper's Imaginary Shot"))
    assert "mech-abils" not in row and "info-tip" in row


def test_outside_a_mechanic_block_the_list_stays_a_note():
    row = _mech_row(lambda: "Spells changed " + elements.info_tip("Sniper's Assassinate", "Dark Seer's Vacuum"),
                    new=None)
    assert "mech-abils" not in row and "info-tip" in row
