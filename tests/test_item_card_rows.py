"""Owner 2026-09-27 (Heaven's Halberd 7.41): the stats card lists item STATS only. A removed or added
ability ("Damage Block (passive)") is a row of its own — "Removed <Name> ability" (DEL) — and the
abilities card shows its text; the generator only folds "+number stat" grants into the card."""
import ast
import pathlib
import re

CONTENT = pathlib.Path(__file__).resolve().parent.parent / "content"
_STAT_ROW = re.compile(r"^[+\-−]?\d")


def _card_labels():
    for path in sorted(CONTENT.glob("p7*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "properties_change"):
                continue
            sides = list(node.args) + [k.value for k in node.keywords if k.arg in ("old", "new")]
            for side in sides:
                for row in getattr(side, "elts", []):
                    elts = getattr(row, "elts", [])
                    if len(elts) >= 2 and isinstance(elts[1], ast.Constant) and isinstance(elts[1].value, str):
                        yield path.name, elts[1].value


def test_stats_cards_hold_stats_not_abilities():
    bad = [(f, label) for f, label in _card_labels()
           if re.search(r"\((?:passive|active)\)", label, re.I)]
    assert not bad, f"an ability in a stats card (make it a 'Removed <Name> ability' row): {bad}"


def test_generator_never_folds_an_ability_into_the_card():
    import generate_patch_code_v2 as g
    lines = ['W(item_header("Heaven\'s Halberd", changed=True))', "W(ul_open())",
             'W(li("No longer provides +275 Health", t("DEL")))',
             'W(li("Removed Damage Block ability", t("DEL")))', "W(ul_close())"]
    out = "\n".join(g._postprocess_properties_change(lines))
    card = out[out.find("properties_change("):out.find("W(ul_open())")]
    assert "+275 Health" in card and "Damage Block" not in card
    assert 'li("Removed Damage Block ability"' in out
