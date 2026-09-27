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


_GRANT = re.compile(r"\+[\d./]+%?\s+[A-Za-z' ]+")


def _item_blocks():
    """(file, version, item name, lower-case text of its card rows + every "+N stat" its rows mention)"""
    for path in sorted(CONTENT.glob("p7*.py")):
        m = re.match(r"p(\d)(\d\d)([a-z]?)\.py$", path.name)
        version = f"{m.group(1)}.{m.group(2)}{m.group(3)}"
        src = path.read_text(encoding="utf-8")
        for block in re.split(r"(?=W\((?:item|hero|unit|plain)_header\(|W\(section\()", src):
            hm = re.match(r'W\(item_header\("((?:[^"\\]|\\.)*)"(?P<rest>[^\n]*)', block)
            if not hm or "new=" in hm.group("rest") or "properties_change(" not in block:
                continue
            name = hm.group(1).replace("\\'", "'")
            card = block[block.find("properties_change("):]
            card = card[:card.find("item_abilities_change(")] if "item_abilities_change(" in card else card
            rows = " ".join(re.findall(r'\(\s*"[^"]*"\s*,\s*"([^"]*)"', card))
            grants = " ".join(_GRANT.findall(" ".join(re.findall(r'li\(\s*"([^"]*)"', block))))
            yield path.name, version, name, (rows + " " + grants).lower()


def test_item_cards_show_every_stat_the_game_changed():
    # Gleipnir 7.38 lost +25 Damage and +25 Attack Speed, Heaven's Halberd 7.41 +5 All Attributes, and the
    # patch notes said nothing: the game's items.txt of both patches is the truth (owner 2026-09-27)
    from patch.elements import silent_stat_changes
    missing = []
    for f, version, name, named in _item_blocks():
        removed, added, changed = silent_stat_changes(name, version, named)
        if removed or added or changed:
            missing.append((f, name, removed, added, changed))
    assert not missing, f"stats the game changed but the card doesn't show (rerun the generator pass): {missing}"


def test_generator_adds_the_stats_the_notes_kept_quiet_about():
    import generate_patch_code_v2 as g
    lines = ['W(item_header("Gleipnir", changed="Item Reworked"))', 'W(auto_components_change("Gleipnir", "7.38"))',
             'W(properties_change(old=[("BUFF", "+275 Health"), ("NERF", "+24 Intelligence")], '
             'new=[("", "+450 Health", b(275, 450)), ("", "+15 Intelligence", b(24, 15)), '
             '("NEW", "+75 AoE Bonus"), ("NEW", "+200 Mana")]))',
             "W(ul_open())", 'W(li("Eternal Chains no longer deals damage", t("DEL")))', "W(ul_close())"]
    out = g._postprocess_silent_stats(lines, "7.38")
    card = out[2]
    assert '("DEL", "+25 Damage")' in card and '("DEL", "+25 Attack Speed")' in card   # a li's "damage" isn't a stat
    assert card.count("+450 Health") == 1 and out[3:] == lines[3:]
    assert g._postprocess_silent_stats(out, "7.38") == out                              # idempotent


def test_generator_never_folds_an_ability_into_the_card():
    import generate_patch_code_v2 as g
    lines = ['W(item_header("Heaven\'s Halberd", changed=True))', "W(ul_open())",
             'W(li("No longer provides +275 Health", t("DEL")))',
             'W(li("Removed Damage Block ability", t("DEL")))', "W(ul_close())"]
    out = "\n".join(g._postprocess_properties_change(lines))
    card = out[out.find("properties_change("):out.find("W(ul_open())")]
    assert "+275 Health" in card and "Damage Block" not in card
    assert 'li("Removed Damage Block ability"' in out
