""""Damage at level 1 …" goes into the (?) of the base attribute / base damage row it follows from (owner 2026-10-04,
shown Magnus 7.41 as its own row and Broodmother 7.41b in the "?": "сделай с ?"). generate_patch_code_v2.
fold_damage_l1_src does it for the generator and for content/p*.py; patch/elements scores the note like the row
it was. docs/agent-rules/content-rules.md "«Damage at level 1» и «Damage gain per level»"."""
import glob
import os
import re

import pytest

from generate_patch_code_v2 import fold_damage_l1_src
from patch.badges import b, br
from patch.state import _State

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _block(*rows, card=False):
    head = ['W(hero_header("Magnus"))', "W(ul_open())"] + (["W(hero_stat_card())"] if card else [])
    return "\n".join(head + list(rows) + ["W(ul_close())", 'W(hero_header("Marci"))'])


def test_plain_attribute_row_gets_the_damage_as_its_note():
    src = _block('W(li("Base Agility increased from 12 to 14", b(12, 14)))',
                 'W(li("Damage at level 1 increased from 55–63 to 56–64", br(55, 63, 56, 64)))')
    out = fold_damage_l1_src(src)
    assert ('W(li("Base Agility increased from 12 to 14", b(12, 14), '
            'extra=inline_note("Damage at level 1 increased from 55–63 to 56–64")))') in out
    assert "br(55, 63, 56, 64)" not in out


def test_note_box_parent_keeps_its_box_and_gains_the_note():
    src = _block('W(li("Base Damage increased by 10", bstat_h("Lifestealer", "AttackDamageMin", "7.40c", 10),\n'
                 '     extra=note_box(hero="Lifestealer", field="AttackDamageMin", before_patch="7.40c")))',
                 'W(li("Base Movement Speed increased from 315 to 320", b(315, 320)))',
                 'W(li("Damage at level 1 increased from 39–45 to 49–55", br(39, 45, 49, 55)))')
    out = fold_damage_l1_src(src)
    assert ('extra=note_box(hero="Lifestealer", field="AttackDamageMin", before_patch="7.40c") + '
            'inline_note("Damage at level 1 increased from 39–45 to 49–55")))') in out
    assert out.count("W(li(") == 2


def test_the_rows_own_note_follows_the_damage_line():
    src = _block('W(li("Max Base damage increased by 1", b(60, 61)))',
                 'W(li("Damage at level 1 increased from 49-61 to 53-62", br(49, 61, 53, 62), '
                 'extra=inline_note("Damage spread decreased from 12 to 9")))')
    out = fold_damage_l1_src(src)
    assert 'inline_note("Damage at level 1 increased from 49-61 to 53-62<br>Damage spread decreased from 12 to 9")' in out


def test_parent_listed_after_the_damage_line_is_used():
    # Invoker 7.39: Valve listed "Damage at level 1" before "Base damage increased by 4"
    src = _block('W(li("Damage at level 1 increased from 35–41 to 39–45", br(35, 41, 39, 45)))',
                 'W(li("Intelligence gain decreased from 4.7 to 4.0", b(4.7, 4)))',
                 'W(li("Base damage increased by 4", b(1, 5)))')
    out = fold_damage_l1_src(src)
    assert 'W(li("Base damage increased by 4", b(1, 5), extra=inline_note("Damage at level 1 increased' in out


@pytest.mark.parametrize("rows, card", [
    # a hero_stat_card hero: the rows are hidden and feed the card
    (['W(li("Base Damage increased by 26", b(24, 50)))',
      'W(li("Damage at level 1 increased by 5 (from 49-55 to 54-60)", br(49, 55, 54, 60)))'], True),
    # Valve's wrong word + a correction note: it must stay in sight
    (['W(li("Base damage increased by 1", b(1, 2)))',
      'W(li(\'Damage at level 1 <span class="wrong-word">decreased</span> from 46–50 to 47–51\', br(46, 50, 47, 51), '
      'extra=note_box(\'The patch text says "decreased", but the values actually went up.\')))'], False),
    # nothing it follows from: the line is the change itself
    (['W(li("Base Movement Speed increased from 315 to 320", b(315, 320)))',
      'W(li("Damage at level 1 increased from 60–62 to 61–63", br(60, 62, 61, 63)))'], False),
])
def test_kept_as_a_row(rows, card):
    src = _block(*rows, card=card)
    assert fold_damage_l1_src(src) == src


def test_no_content_file_has_a_foldable_row_left():
    """Every patch went through the fold (2026-10-04); a new hand edit must not bring a foldable row back."""
    left = []
    for f in glob.glob(os.path.join(ROOT, "content", "p7*.py")):
        src = open(f, encoding="utf-8").read()
        if fold_damage_l1_src(src) != src:
            left.append(os.path.basename(f))
    assert not left, left


def test_folded_note_weighs_what_the_row_weighed():
    """The weights must not move: a "Damage at level 1" note scores like the br() row it replaced, and the
    "Base Damage" row next to it still drops out (damage rows counted once, 2026-09-26). Tag tallies count rows,
    so the note adds no tag."""
    from patch.elements import hero_header, li, ul_open, ul_close, inline_note
    _State.current_patch_version = "7.41"
    cells = []
    for folded in (False, True):
        _State.dynamics.pop("hero|lifestealer", None)
        hero_header("Lifestealer")
        ul_open()
        if folded:
            li("Base Damage increased by 10", b(20, 30),
               extra=inline_note("Damage at level 1 increased from 39–45 to 49–55"))
        else:
            li("Base Damage increased by 10", b(20, 30))
            li("Damage at level 1 increased from 39–45 to 49–55", br(39, 45, 49, 55))
        ul_close()
        hero_header("Lina")                                       # ends the block
        cells.append(dict(_State.dynamics["hero|lifestealer"]["patches"]["7.41"]))
    row, note = cells
    assert note["w"] == pytest.approx(row["w"]) and note["v"] == pytest.approx(row["v"])
    assert row["buff"] == 2 and note["buff"] == 1


def test_generator_folds_its_own_output():
    import generate_patch_code_v2 as g
    lines = _block('W(li("Base Strength increased from 20 to 22", b(20, 22)))',
                   'W(li("Damage at level 1 increased from 50–56 to 52–58", br(50, 56, 52, 58)))').split("\n")
    out = "\n".join(g._postprocess_fold_damage_l1(lines))
    assert re.search(r'Base Strength increased from 20 to 22", b\(20, 22\), extra=inline_note\("Damage at level 1', out)
