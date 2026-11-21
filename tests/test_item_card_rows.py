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


_CHANGE_ROW = re.compile(r"^([A-Z][A-Za-z'/ ]+?)\s+(?:bonus\s+)?(?:increased|decreased|rescaled|changed)\s+from\b")


def _item_blocks():
    """(file, version, item name, lower-case text of its card rows + every "+N stat" its rows mention + the stat
    of every "<Stat> bonus increased from A to B" row) — cards or rows alike (owner 2026-09-28: no card
    without a build change)"""
    for path in sorted(CONTENT.glob("p7*.py")):
        m = re.match(r"p(\d)(\d\d)([a-z]?)\.py$", path.name)
        version = f"{m.group(1)}.{m.group(2)}{m.group(3)}"
        src = path.read_text(encoding="utf-8")
        for block in re.split(r"(?=W\((?:item|hero|unit|plain)_header\(|W\(section\()", src):
            hm = re.match(r'W\(item_header\("((?:[^"\\]|\\.)*)"(?P<rest>[^\n]*)', block)
            # an item out of the game keeps its file changes as a comment, not on the page (owner 2026-11-21)
            if not hm or "new=" in hm.group("rest") or "# Out of the game, not shown" in block:
                continue
            name = hm.group(1).replace("\\'", "'")
            card = block[block.find("properties_change("):] if "properties_change(" in block else ""
            card = card[:card.find("item_abilities_change(")] if "item_abilities_change(" in card else card
            rows = " ".join(re.findall(r'\(\s*"[^"]*"\s*,\s*"([^"]*)"', card))
            # either quote; markup stripped (Bloodstone 7.41c: '<span class="wrong-word">Health bonus …</span>')
            lis = [re.sub(r"<[^>]+>", "", mm.group(2)) for mm in re.finditer(r"""li\(\s*(["'])(.*?)(?<!\\)\1""", block, re.S)]
            grants = " ".join(_GRANT.findall(" ".join(lis)))
            changes = " ".join(mm.group(1) for t in lis for mm in [_CHANGE_ROW.match(t)] if mm)
            yield path.name, version, name, (rows + " " + grants + " " + changes).lower()


def test_no_stats_card_without_a_build_change():
    # Sange and Yasha 7.38: one changed stat drawn as a whole card — the card comes only with the components
    # card; otherwise the stats are rows (owner 2026-09-28) — or with an abilities card (owner 2026-10-17, Refresher
    # Orb 7.41: "no stats card") — or when the item trades one stat for another, a NEW one and a DEL one (owner
    # 2026-10-30, 7.37 Bracer: "тут разве не карточкой надо?")
    bad = []
    for path in sorted(CONTENT.glob("p7*.py")):
        for block in re.split(r"(?=W\((?:item|hero|unit|plain)_header\(|W\(section\()", path.read_text(encoding="utf-8")):
            swap = '("NEW", "+' in block and '("DEL", "+' in block
            # an item moved to another neutral tier: a build change of its kind (owner 2026-10-30, 7.37 Vambrace)
            swap = swap or 'new="Now a Tier' in block.split("\n", 1)[0]
            # a stat split by melee / ranged, old -> new (owner 2026-11-19, 7.42 Phase Boots: "карточками old/new")
            swap = swap or ' (Melee/Ranged)", ' in block
            if (block.startswith("W(item_header(") and "properties_change(" in block and "components_change(" not in block
                    and "item_abilities_change(" not in block and not swap):
                bad.append((path.name, re.match(r'W\(item_header\("((?:[^"\\]|\\.)*)"', block).group(1)))
    assert not bad, f"a stats card without a components card: {bad}"


def test_item_cards_show_every_stat_the_game_changed():
    # Gleipnir 7.38 lost +25 Damage and +25 Attack Speed, Heaven's Halberd 7.41 +5 All Attributes, and the
    # patch notes said nothing: the game's items.txt of both patches is the truth (owner 2026-09-27)
    from patch.cards_item_stats import silent_stat_changes
    missing = []
    for f, version, name, named in _item_blocks():
        removed, added, changed = silent_stat_changes(name, version, named)
        if removed or added or changed:
            missing.append((f, name, removed, added, changed))
    assert not missing, f"stats the game changed but the card doesn't show (rerun the generator pass): {missing}"


def test_generator_adds_the_stats_the_notes_kept_quiet_about():
    import tools.generate_patch_code_v2 as g
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


def test_generator_invents_no_stat_row_the_notes_already_say_or_for_a_gone_item():
    # 7.42 proofread 2026-11-18: Phase Boots got "Now also provides +15 Damage" beside Valve's own Damage row, and the
    # cycled-out Dagger of Ristul "Damage bonus increased from +25 to +30"
    import pytest
    import tools.generate_patch_code_v2 as g
    from patch.cards_item_stats import item_stats_pair
    if not item_stats_pair("Phase Boots", "7.42"):
        pytest.skip("no items.txt of 7.41f / 7.42 here")
    phase = ['W(item_header("Phase Boots"))', 'W(ul_open())',
             'W(li("Damage bonus changed from +18/12 for melee/ranged heroes to +15 for any wearer", t("REWORK")))',
             'W(li("Movement Speed bonus changed from +50 to +45/55 for Ranged/Melee Heroes", b(50, [45, 55])))',
             'W(ul_close())']
    assert g._postprocess_silent_stats(phase, "7.42") == phase
    gone = ['W(item_header("Dagger of Ristul"))', 'W(ul_open())', 'W(li("Item Cycled Out", t("DEL")))', 'W(ul_close())']
    # an item out of the game: the file's change is no row (it touches no match), a comment keeps it for when the item
    # returns (owner 2026-11-21: "если выведено, то нет смысла показывать, но знать полезно, что поменяли")
    out = g._postprocess_silent_stats(gone, "7.42")
    assert out[-1] == ("# Out of the game, not shown; changed in items.txt (for when it returns): "
                       "+25 Damage -> +30 Damage") and out[:-1] == gone
    assert g._postprocess_silent_stats(out, "7.42") == out                              # once
    assert 'removed="Item cycled out"' in g._postprocess_removed_label(out)[0]          # the label still comes
    labelled = ['W(item_header("Duelist Gloves", removed="Neutral Item cycled out"))'] + gone[1:]
    assert "W(li(" not in g._postprocess_silent_stats(labelled, "7.42")[1]


def test_generator_never_folds_an_ability_into_the_card():
    import tools.generate_patch_code_v2 as g
    lines = ['W(item_header("Heaven\'s Halberd", changed=True))', 'W(auto_components_change("Heaven\'s Halberd", "7.41"))',
             "W(ul_open())", 'W(li("No longer provides +275 Health", t("DEL")))',
             'W(li("Removed Damage Block ability", t("DEL")))', "W(ul_close())"]
    out = "\n".join(g._postprocess_properties_change(lines))
    card = out[out.find("properties_change("):out.find("W(ul_open())")]
    assert "+275 Health" in card and "Damage Block" not in card
    assert 'li("Removed Damage Block ability"' in out


def test_generator_keeps_stat_rows_when_the_build_did_not_change():
    # Sange and Yasha 7.38: no components card -> the row stays a row (owner 2026-09-28)
    import tools.generate_patch_code_v2 as g
    lines = ['W(item_header("Sange and Yasha"))', "W(ul_open())",
             'W(li("Status Resistance bonus decreased from +25% to +20%", b(25, 20)))', "W(ul_close())"]
    assert g._postprocess_properties_change(lines) == lines
