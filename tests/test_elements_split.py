"""patch/elements.py is cut into card modules (audit 2026-10-26 #8: 4805 lines in one file). Each card module imports
its helpers from elements, and elements imports the cards back at its end; patch/__init__.py loads elements first,
so a caller may import any of them first."""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = ("cards_hero_stats", "cards_item_abilities", "cards_item_stats", "cards_aghs", "cards_ability_change")


def _lines(name):
    with open(os.path.join(ROOT, "patch", f"{name}.py"), encoding="utf-8") as f:
        return sum(1 for _ in f)


def test_elements_stays_cut():
    assert _lines("elements") < 2600
    assert all(_lines(m) < 1200 for m in CARDS)


@pytest.mark.parametrize("first", ("elements", "api") + CARDS)
def test_any_module_can_be_imported_first(first):
    code = f"import patch.{first}; from patch.api import ability_change, item_abilities_change, hero_stat_card, li"
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]


def test_the_cards_depend_on_each_other_one_way():
    """Card modules import elements and the cards before them in CARDS, never one after — no cycle to trip on."""
    import ast
    for i, mod in enumerate(CARDS):
        with open(os.path.join(ROOT, "patch", f"{mod}.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        later = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level == 1} & set(CARDS[i:])
        assert not later, f"{mod} imports {later}"
