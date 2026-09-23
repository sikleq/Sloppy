"""properties_change(old=[...], new=[...]): stats present on BOTH sides come first and in the same
order, so a stat sits on the same line in the OLD and NEW panes (7.38 Gleipnir had +75 AoE / +200 Mana
first on the right, pushing +450 Health off the line of +275 Health)."""
import ast
import glob
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _key(node):
    if not (isinstance(node, ast.Tuple) and len(node.elts) >= 2 and isinstance(node.elts[1], ast.Constant)):
        return ""
    t = re.sub(r"<[^>]+>", "", node.elts[1].value).strip()
    t = re.sub(r"^[+\-−x×]?[\d.,/%\s]+%?\s*", "", t)
    return re.sub(r"\s*\(.*?\)\s*$", "", t).lower().strip()


@pytest.mark.parametrize("path", sorted(glob.glob(os.path.join(ROOT, "content", "p*.py"))))
def test_shared_properties_first_and_aligned(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    bad = []
    for call in ast.walk(tree):
        if not (isinstance(call, ast.Call) and getattr(call.func, "id", "") == "properties_change"):
            continue
        kw = {k.arg: k.value for k in call.keywords}
        if not isinstance(kw.get("old"), ast.List) or not isinstance(kw.get("new"), ast.List):
            continue
        ok_, nk = [_key(e) for e in kw["old"].elts], [_key(e) for e in kw["new"].elts]
        shared = [k for k in ok_ if k and k in nk]
        if ok_[:len(shared)] != shared or nk[:len(shared)] != shared:
            bad.append(f"line {call.lineno}: old={ok_} new={nk}")
    assert not bad, os.path.basename(path) + ": " + "; ".join(bad)
