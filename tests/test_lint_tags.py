"""The canonical-phrase tag linter (.claude/skills/sloppy-patch/lint_tags.py) reads EVERY li() row (2026-10-16: its
regex skipped 448 of 1100 rows of 7.41 — a row without t() swallowed the next one, so Pipe of Insight's
"no longer affects" NERF went unseen)."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINTER = os.path.join(ROOT, ".claude", "skills", "sloppy-patch")
if not os.path.exists(os.path.join(LINTER, "lint_tags.py")):          # .claude is not in git: CI has no linter
    pytest.skip("the sloppy-patch skill is local only", allow_module_level=True)
sys.path.insert(0, LINTER)
import lint_tags  # noqa: E402

SRC = '''
def build():
    W(li("Recipe Cost decreased from 800 to 675", b(800, 675, l=True)))
    W(li("Barrier no longer affects units that were affected by Barrier", t("NERF")))
    W(li("Cast Range increased from 500 to 600", b(500, 600)))
    W(li("Tier 1 availability changed from 5:00 to 0:00", t("BUFF")))
    W(li("Now a Unit Vector Target Spell", t("NEW")))
'''


def test_a_row_after_a_badge_row_is_still_linted(tmp_path):
    path = tmp_path / "p799.py"
    path.write_text(SRC, encoding="utf-8")
    rows = list(lint_tags.li_rows(str(path)))
    assert len(rows) == 5
    found = {(text.split()[0], declared, guessed) for _n, text, declared, guessed in lint_tags.lint_file(str(path))}
    assert ("Barrier", "NERF", "DEL") in found
    assert ("Tier", "BUFF", "REWORK") in found


def test_badge_rows_are_skipped(tmp_path):
    path = tmp_path / "p799.py"
    path.write_text('def build():\n    W(li("Recipe Cost decreased from 800 to 675", b(800, 675), t("MISC")))\n',
                    encoding="utf-8")
    assert lint_tags.lint_file(str(path)) == []
