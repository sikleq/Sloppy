"""A facet's talent is written under the hero's Talents with the facet's chip, not under the facet (owner 2026-10-27,
7.39 Nature's Prophet: two facets change the same level 15 talent in two ways)."""
import ast
import glob
import os
import re

import tools.generate_patch_code_v2 as g
from patch.elements import li
from patch.state import _State

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_row_shows_the_facet_chip_before_its_text():
    _State.current_hero = "Nature's Prophet"
    html = li("Level 15 Talent +100 Teleportation Barrier replaced with +30% Sprout Heal Per Second", "",
              facet="furion_soothing_saplings")
    # a square with the facet's icon, no words (owner 2026-10-27): the name only on hover
    m = re.search(r'<span class="row-text">(<span class="facet-chip"[^>]*>(.*?)</span>) Level 15 Talent', html)
    assert m and 'data-tooltip="Soothing Saplings"' in m.group(1)
    assert re.fullmatch(r'(?:<img [^>]*icons/facets/[^>]*>)?', m.group(2))


def test_the_generator_moves_a_facets_talents_to_talents():
    rows = ['W(li("Level 15 Talent +100 Teleportation Barrier replaced with +1 Gold Bag", t("SWAP")))']
    assert g._with_facet(rows, "furion_natures_profit") == [
        'W(li("Level 15 Talent +100 Teleportation Barrier replaced with +1 Gold Bag", t("SWAP"), '
        'facet="furion_natures_profit"))']
    assert g._ul_inner(["W(ul_open())", "W(li(\"x\"))", "W(ul_close())"]) == ['W(li("x"))']


def test_no_talent_row_sits_under_a_facet_in_the_content():
    starts = re.compile(r'^\s*W\((?:facet_header|new_facet|facet_change)\(')
    ends = re.compile(r'^\s*W\((?:ability|subgroup|hero_header|ability_change|item_header|plain_header|section)\(')
    bad = []
    for path in glob.glob(os.path.join(ROOT, "content", "p*.py")):
        in_facet = False
        with open(path, encoding="utf-8") as f:
            for no, line in enumerate(f, 1):
                if starts.match(line):
                    in_facet = True
                elif ends.match(line):
                    in_facet = False
                elif in_facet and re.search(r'li\("(?:[^"]*: )?Level \d+ Talent', line):
                    bad.append(f"{os.path.basename(path)}:{no}")
                elif re.search(r'li\("[A-Z][^":]*: Level \d+ Talent', line):     # "Old Blood: Level 10 Talent …"
                    bad.append(f"{os.path.basename(path)}:{no} (facet in the text: use facet=)")
    assert not bad, bad


def test_every_facet_keyword_names_a_known_facet():
    from patch.badges import FACETS
    for path in glob.glob(os.path.join(ROOT, "content", "p*.py")):
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "li":
                for k in n.keywords:
                    if k.arg == "facet":
                        assert k.value.value in FACETS, (path, n.lineno, k.value.value)
