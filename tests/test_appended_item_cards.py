"""7.38c Helm of the Dominator / Overlord: no item abilities card — the game's text only gained "and it can no longer
be killed by abilities that instantly kill creeps otherwise", which the card didn't mark, so the two boxes read the same;
the row "Dominated creep is now considered a creep-hero" says it (owner 2026-10-27). Not a rule for every appended
clause: Harpoon 7.41's card marks its added sentence and stays (owner 2026-10-17)."""
from patch.css_bundle import read_css
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


def test_the_enchant_cells_grey_note_keeps_its_space():
    """7.38c Vast: "Attack Range(Melee & Ranged)" — a flex cell drops the space before the game's <font> note."""
    assert ".ench-change .ench-stat > font { margin-left: 0.3em; }" in read_css()


def test_harpoon_741_keeps_its_card():
    assert _cards_under("p741.py", "Harpoon")


def test_a_card_that_marks_nothing_is_left_out():
    """Owner 2026-10-27 (7.39 Orb of Frost: "either the row or the card"): no row colours anything in the card ->
    no card, the row says it; one coloured number keeps it (7.39e Dominator's cooldown)."""
    from patch import cards_item_abilities as c
    from patch.state import reset_page_state
    reset_page_state()
    old = ["Passive: Frost. Reduces Healing, Health Regen and Lifesteal by 13%."]
    new = ["Passive: Frost. Reduces Health Restoration by 13%."]
    c._IAB_CARDS["item|orb|t"] = (old, new)
    assert c.render_iab_card("item|orb|t") == ""
    c._IAB_CARDS["item|helm|t"] = (["Active: Dominate. Takes control. Cooldown: 45s"],
                                   ["Active: Dominate. Takes control. Cannot be used for 3 seconds. Cooldown: 50s"])
    c._IAB_MARKS["item|helm|t"] = [("num", "50", "nerf", "", "dominate", "45")]
    assert "iab-change" in c.render_iab_card("item|helm|t")
    c._IAB_CARDS["item|gone|t"] = (["Passive: Old. Something."], [])  # a removed ability: its red frame says it
    assert "iab-removed" in c.render_iab_card("item|gone|t")
    reset_page_state()
