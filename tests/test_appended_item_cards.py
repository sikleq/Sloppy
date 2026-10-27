"""7.38c Helm of the Dominator / Overlord: no item abilities card — the game's text only gained "and it can no longer
be killed by abilities that instantly kill creeps otherwise", which the card didn't mark, so the two boxes read the same;
the row "Dominated creep is now considered a creep-hero" says it (owner 2026-10-27). Not a rule for every appended
clause: Harpoon 7.41's card marks its added sentence and stays (owner 2026-10-17)."""
import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cards_under(path, header):
    with open(os.path.join(ROOT, "content", path), encoding="utf-8") as f:
        body = [st for fn in ast.parse(f.read()).body if isinstance(fn, ast.FunctionDef) for st in fn.body]
    calls = [st.value.args[0] for st in body if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call)
             and getattr(st.value.func, "id", None) == "W" and st.value.args and isinstance(st.value.args[0], ast.Call)]
    out, under = [], False
    for c in calls:
        name = getattr(c.func, "id", None)
        if name == "item_header":
            under = c.args and isinstance(c.args[0], ast.Constant) and c.args[0].value == header
        elif under and name == "item_abilities_change":
            out.append(c.lineno)
    return out


def test_dominator_and_overlord_738c_have_no_abilities_card():
    assert not _cards_under("p738c.py", "Helm of the Dominator")
    assert not _cards_under("p738c.py", "Helm of the Overlord")


def test_harpoon_741_keeps_its_card():
    assert _cards_under("p741.py", "Harpoon")
