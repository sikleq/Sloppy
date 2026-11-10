"""Guards the layout of cards: pairs, folds by height, captions and rows under a card, header lines.
"""
from pathlib import Path

import pathlib
import sys
from patch import cards_aghs, cards_item_abilities
from patch.cards_rows import FOLD_CHARS, TABLE_ROW_CHARS, _side_weight, fold_long_rows
from patch.css_bundle import read_css

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
NEW = ('<div class="ability-block facet-block"><h4 class="ability-title">{}</h4><ul class="changes ability-change-summary-ul">'
       '<li data-tag="new">New facet</li></ul><div class="ability-change unified-panes is-single-new" data-tag="new">'
       '<div class="ability-change-pane ability-change-new"><div class="ability-change-body"><div class="ability-change-row">'
       'Text</div></div></div></div></div>')


def _row(text):
    return f'<div class="ability-change-row">{text}</div>'


def _as_hero(hero, fn, *args):
    from patch.state import _State
    keep = _State.current_hero
    _State.current_hero = hero
    try:
        return fn(*args)
    finally:
        _State.current_hero = keep


def test_two_new_cards_in_a_row_stand_as_a_pair_and_three_in_one_line():
    from patch.card_pairs import pair_new_cards
    two = NEW.format("A") + "\n" + NEW.format("B")
    out = pair_new_cards(two, "7.38")
    assert out.count('<div class="card-pair">') == 1
    assert out.index('class="card-pair"') < out.index(">A<") < out.index(">B<")
    # every patch after the 7.38 trial (owner 2026-11-06: "Одиночные карточки для всех патчей включи")
    assert pair_new_cards(two, "7.41").count('<div class="card-pair">') == 1
    # exactly three: one line of three (owner 2026-11-06, 7.38 Invoker: "как ты аспекта эти 3 рядом расположил")
    three = two + "\n" + NEW.format("C")
    out = pair_new_cards(three, "7.38")
    assert out.count('<div class="card-pair card-trio">') == 1 and '<div class="card-pair">' not in out
    assert out.index("card-trio") < out.index(">A<") < out.index(">B<") < out.index(">C<")
    four = pair_new_cards(three + "\n" + NEW.format("D"), "7.38")      # four: two pairs
    assert four.count('<div class="card-pair">') == 2 and "card-trio" not in four


def test_a_block_with_rows_of_its_own_or_two_cards_does_not_pair():
    from patch.card_pairs import pair_new_cards
    rows = NEW.format("A").replace("</div></div></div></div></div>",
                                   '</div></div></div></div><ul class="changes"><li data-tag="buff">Row</li></ul></div>')
    assert pair_new_cards(rows + NEW.format("B"), "7.38") == rows + NEW.format("B")
    covered = rows.replace('<li data-tag="buff">', '<li data-tag="buff" class="iab-covered covered-card">')
    assert '<div class="card-pair">' in pair_new_cards(covered + NEW.format("B"), "7.38")


def test_a_lone_card_stands_under_its_block_with_its_values_beside_it():
    """A one-sided card no longer stands right of its block with a line to it: under the block on the left, as a deck's
    card, its values a card of their own on the right (owner 2026-11-10, 7.41 Ready to Roll: "не по правую часть с
    линией до карточки, а как и раньше слева")."""
    from patch import card_pairs, page
    assert not hasattr(card_pairs, "single_cards_right")
    assert "single_cards_right" not in (Path(page.__file__)).read_text(encoding="utf-8")
    css = (Path(page.__file__).parent.parent / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    assert ".single-right" not in css and ".sr-line" not in css
    from patch.card_deck import _solo
    card = ('<div class="ability-change unified-panes is-single-new" data-tag="new"><div class="ability-change-pane '
            'ability-change-new"><div class="iab-head pane-head"><span class="iab-title"></span><span class="iab-meta">'
            '<span class="iab-m"><img src="../icons/ui/ability/cooldown.png" alt="">12</span></span></div>'
            '<div class="ability-change-body"><div class="ability-change-row">Does a thing.</div></div></div></div>')
    out = _solo(card, "7.41", None, [])
    assert 'is-single-new has-vt-side"' in out
    assert out.index("Does a thing.") < out.index('<div class="vt-side">')
    assert "Cooldown" in out.split('<div class="vt-side">')[1]


def test_rows_led_by_ability_icons_are_sections_with_their_own_heads():
    from patch.card_sections import card_sections
    chip = lambda name, slug: (f'<span class="acr-lead-chips"><span class="ability-chip" data-tooltip="{name}" role="img">'
                               f'<img src="../icons/_t/abilities/{slug}.webp" alt=""></span></span>')
    pane = ('<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
            '<div class="ability-change-row">' + chip("Runic Infusion", "arc_warden_runic_infusion") + "Gains stats.</div>"
            '<div class="ability-change-row">' + chip("Magnetic Field", "arc_warden_magnetic_field") + "Pulls runes.</div>"
            "</div></div>")
    out = card_sections(pane, "7.38")
    # the head is the strip of a card's own head (owner 2026-11-06: "Шапка Power Capture не такая, как везде")
    assert out.count('class="ability-change-row acr-sec') == 2 and out.count('class="iab-head acr-sec-head"') == 2
    assert out.count("acr-sec-top") == 1                           # the first head on the pane's top edge
    assert '<span class="iab-name">Magnetic Field</span>' in out and 'class="iab-kind">Active:</b>' in out
    one = pane.replace("Runic Infusion", "Magnetic Field").replace("arc_warden_runic_infusion", "arc_warden_magnetic_field")
    assert "acr-sec-head" not in card_sections(one, "7.38")       # one ability: lines, no heads


def test_a_sub_ability_named_in_the_text_gets_a_line_above_it():
    from patch.card_sections import card_sections
    pane = ('<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
            '<div class="ability-change-row">A creep with the Martyrdom ability. Respawn time: 60s.</div>'
            '<div class="ability-change-row"><b>Martyrdom:</b> sacrifices itself.</div>'
            '<div class="ability-change-row"><b>Cast Point:</b> 0.3s.</div></div></div>')
    out = card_sections(pane, "7.41")
    assert '<div class="ability-change-row acr-sec"><b>Martyrdom:</b>' in out
    assert '<div class="ability-change-row"><b>Cast Point:</b>' in out          # a value's label is no sub-ability


def test_a_row_going_on_with_the_rework_above_joins_it():
    from tools.patchgen.post_general import _postprocess_rework_continuation
    lines = ['    W(li("Both are now available. They have a shared cooldown", t("REWORK")))',
             '    W(li("This results in swapping special attacks: Frost first", t("REWORK")))',
             '    W(li("As a result of the changes, X", t("REWORK")))']
    out = _postprocess_rework_continuation(lines)
    assert out[0] == ('    W(li("Both are now available. They have a shared cooldown. This results in swapping special '
                      'attacks: Frost first", t("REWORK")))') and len(out) == 2
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert 'W(li("This results in swapping' not in text


def test_a_long_side_with_no_short_intro_folds_whole():
    from patch.cards_rows import fold_long_rows
    long_first = '<div class="ability-change-row">' + "word " * 150 + "</div>"
    rest = '<div class="ability-change-row">' + "more " * 30 + "</div>"
    out = fold_long_rows([long_first, rest])
    assert out[0].startswith('<div class="acr-fold acr-fold-whole">')
    # 7.38 Roshan's Throw, ~700 characters in one long row: stays open (owner 2026-10-30)
    short = '<div class="ability-change-row">' + "word " * 125 + "</div>"
    assert fold_long_rows([short, '<div class="ability-change-row">x y</div>'])[0] == short


def test_a_head_never_moves_its_values_to_another_line():
    from patch.css_bundle import read_css
    css = read_css()
    assert "line-height: 18px; flex-wrap: nowrap;" in css
    assert ".iab-head { display: flex; align-items: flex-start;" in css     # values on the title's first line
    assert ".iab-title { white-space: normal; flex: 1 1 auto; min-width: 0; }" in css


def test_three_cards_in_a_line_start_their_parts_on_one_line_and_do_not_fold():
    # owner 2026-11-06, 7.38 Invoker: "Сделай на сайте как ты аспекта эти 3 рядом расположил"
    from patch.css_bundle import read_css
    from patch.js_bundle import JS_PARTS, read_js
    css, js = read_css(), read_js()
    assert ".card-pair.card-trio { grid-template-columns: repeat(3, minmax(0, 1fr)); column-gap: 18px; }" in css
    # each folds on its own, no heights evened (owner 2026-11-06: "Лучше дать возможность сворачивать/разворачивать
    # карточки по отдельности … не обязательно одинаковой высоты")
    assert ".card-trio .acr-fold-toggle" not in css and ".card-trio .acr-fold > .acr-fold-body" not in css
    assert "card-trio" not in JS_PARTS and ".card-trio" not in js
    assert ".card-pair, .card-pair.card-trio { grid-template-columns: minmax(0, 1fr); }" in css     # a phone
    # a card open beside two folded ones folds too, after its first row ("в свёрнутом состоянии одинаковые")
    from patch.card_pairs import pair_new_cards
    folded = NEW.format("A").replace('<div class="ability-change-row">Text</div>',
                                     '<div class="ability-change-row">One</div><div class="acr-fold"><div class="acr-fold-body">'
                                     '<div class="ability-change-row">Two</div></div></div>')
    open_ = NEW.format("C").replace('<div class="ability-change-row">Text</div>',
                                    '<div class="ability-change-row">One</div><div class="ability-change-row">Two</div>')
    out = pair_new_cards(folded + folded.replace(">A<", ">B<") + open_, "7.38")
    assert out.count('<div class="acr-fold">') == 3 and out.count("acr-fold-toggle") == 1


def test_a_lone_cards_block_rows_stay_in_its_block():
    """The rows of a lone card's block went under the card while the card stood on the right (7.38 Voidbringer); the
    card stands under the block now, the rows stay where they are, above it."""
    from patch import page
    assert "_rows_under(left)" not in (Path(page.__file__).parent / "card_pairs.py").read_text(encoding="utf-8")


def test_values_that_become_a_table_weigh_by_their_rows():
    # 7.38 Arcane Curse: 379 characters of text and a six-row table stood open ("карточка достаточно высокая")
    values = _row("Initial Damage: 20/40/60/80. Damage: 16/24/32/40. Base Duration: 6s. Movement Slow: 16/19/22/25%. "
                  "Penalty Duration: 2s. Silenced Multiplier: 1.5x")
    assert _side_weight(values) == 6 * TABLE_ROW_CHARS


def test_a_side_with_short_text_and_a_tall_table_folds():
    text = _row("x " * 190)
    values = _row("Initial Damage: 20/40/60/80. Damage: 16/24/32/40. Base Duration: 6s. Movement Slow: 16/19/22/25%. "
                  "Penalty Duration: 2s. Silenced Multiplier: 1.5x")
    assert sum(len(r) for r in (text, values)) < FOLD_CHARS + 200     # by characters alone it stayed open
    out = fold_long_rows([text, values])
    assert out[0] == text and 'class="acr-fold' in out[1]


def test_a_plain_text_row_weighs_its_characters():
    assert _side_weight(_row("Grants +1 Leap charge.")) == len("Grants +1 Leap charge.")


def test_the_arrow_stands_at_the_shorter_side_of_top_aligned_cards():
    # 7.38 Mirana Leap: "стрелочка в пустоту указывает, а не блок новой карточки из-за разницы в размерах"
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert "document.querySelectorAll('.ability-change.unified-panes').forEach((card) => {" in js
    assert "const p = o.height <= n.height ? o : n;" in js


def test_many_values_of_a_one_sided_card_stand_beside_it():
    # owner 2026-11-07, 7.38 Throw, variant A: "отдельным соседним блоком-таблицей"
    from patch.value_tables import SIDE_TABLE_ROWS, tables_beside_single_cards
    cells = "".join(f'<div class="vt-l">a{i}</div><div class="vt-v">{i}</div>' for i in range(SIDE_TABLE_ROWS))
    card = ('<div class="ability-change unified-panes is-single-new"><div class="ability-change-pane"><div class="ability-change-row">'
            f'Text <div class="value-table">{cells}</div></div></div></div>')
    out = tables_beside_single_cards(card)
    assert out.endswith(f'<div class="vt-side"><div class="value-table">{cells}</div></div></div>')
    assert "is-single-new has-vt-side" in out
    # the text that folded for the table's weight opens again
    folded = ('<div class="ability-change unified-panes is-single-new"><div class="ability-change-pane">'
              '<div class="acr-fold"><div class="acr-fold-body"><div class="ability-change-row">'
              f'Text <div class="value-table">{cells}</div></div></div>'
              '<button class="acr-fold-toggle"></button></div></div></div>')
    out = tables_beside_single_cards(folded)
    assert "acr-fold" not in out and '<div class="ability-change-row">Text </div></div><div class="vt-side">' in out
    assert out.count("value-table") == 1
    few = card.replace('<div class="vt-l">a0</div><div class="vt-v">0</div>', "")
    assert tables_beside_single_cards(few) == few
    css = (ROOT / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    assert ".ability-change.unified-panes.is-single-new > .vt-side { grid-column: 3; grid-row: 1; }" in css


def test_a_lone_card_keeps_its_caption_when_a_hidden_row_stands_first():
    # 7.40 Searing Arrows: "Returning as a base ability." went under the card
    from patch.card_pairs import _rows_under
    block = ('<div class="ability-block"><ul class="changes ability-change-summary-ul">'
             '<li data-tag="new" class="iab-covered covered-card">hidden</li>'
             '<li data-tag="new"><span class="row-text">Returning as a base ability.</span></li></ul></div>')
    kept, under = _rows_under(block)
    assert under == "" and "Returning as a base ability." in kept


def test_a_paired_blocks_own_row_goes_under_its_card():
    # 7.38 Magnus Diminishing Return: the -14% row stood between "New facet" and the card
    from patch.card_pairs import _rows_after_card
    block = ('<div class="ability-block"><ul class="changes ability-change-summary-ul">'
             '<li data-tag="new"><span class="row-text">New facet</span></li>'
             '<li data-tag="nerf" class="li-bg"><span class="row-text">Number decreased</span></li></ul>'
             '<div class="ability-change unified-panes is-single-new">card</div></div>')
    out = _rows_after_card(block)
    assert out.index("card</div>") < out.index("Number decreased")
    assert '<ul class="changes pair-under">' in out


def test_a_fold_hiding_under_two_lines_stays_open():
    # 7.40 Liquid Courage: "тут так мало прячется, что будто и не нужно сворачивать"; "видно выделение от мышки"
    js = (ROOT / "src" / "js" / "fold-small.js").read_text(encoding="utf-8")
    assert "body.scrollHeight - body.clientHeight < LINES * line" in js
    from patch.js_bundle import JS_PARTS
    assert JS_PARTS.index("fold-small") == JS_PARTS.index("patch-page") + 1
    css = (ROOT / "src" / "css" / "patch-entity-labels.css").read_text(encoding="utf-8")
    assert ".acr-fold.fold-off > .acr-fold-toggle { display: none; }" in css
    assert ".acr-fold.is-open .acr-fold-toggle:hover { background-color: transparent; }" in css


def test_a_long_card_side_folds():
    """Owner 2026-10-30: "для таких длинных описаний может сделаем свёрнутый вид?", then "раскатай на весь сайт": a side
    over FOLD_CHARS folds — Drunken Brawler's short intro stays open; a side with no short first row folds whole and
    taller; a short side stays as it is."""
    from patch.cards_rows import FOLD_CHARS, fold_long_rows
    row = lambda s: f'<div class="ability-change-row">{s}</div>'
    long = "Grants 1/3/5/7/9 armor and 4/8/12/16/20% Magic Resistance. Bonuses are 2.5x when Brewed Up. " * 2
    rows = [row("Brewmaster can switch stances."), *(row(f"<b>{n} Brawler</b> — {long}")
                                                    for n in ("Earth", "Storm", "Fire", "Void"))]
    out = fold_long_rows(rows)
    assert out[0] == rows[0] and len(out) == 2
    # its first lines fade out, a click opens it (owner 2026-10-30: "нижняя часть блока полупрозрачная"); a button of
    # soft glass shows it opens and folds it back ("видно, что оно разворачиваться может … свернуть обратно"; no
    # chevron, no pollen: "эффект стекла снизу … плавный … чтобы не нагружало страницу")
    assert out[1].startswith('<div class="acr-fold"><div class="acr-fold-body">')
    assert out[1].count("ability-change-row") == 4 and "<summary>" not in out[1]
    assert '<button type="button" class="acr-fold-toggle" aria-expanded="false"' in out[1] and "<svg" not in out[1]
    # no short intro: stays open (owner 2026-10-30, 7.38 Roshan's Throw: "можно и не сворачивать")
    one = [row("x" * (FOLD_CHARS + 50))]
    assert fold_long_rows(one) == one
    short = [row("Deals damage."), row("Slows enemies.")]
    assert fold_long_rows(short) == short
    assert fold_long_rows(out) == out                       # folded once
    # a "?" popup's hidden words don't count (7.39 Changing of the Guard: 414 shown, 420 in its popup)
    tipped = [row("Shown words. " * 30 + '<span class="info-tip">?<span class="info-pop"><span class="pop-li">'
                  + "hidden " * 200 + "</span></span></span>")]
    assert fold_long_rows(tipped) == tipped


def test_a_card_rows_closing_tip_never_wraps_alone():
    """Owner 2026-10-30, 7.38 E.M.P.: the [?] stood on a line of its own — "у нас в правилах это запрещено"."""
    from patch.cards_item_abilities import _pane_parts
    from patch.elements import inline_note
    _, body = _as_hero("invoker", _pane_parts, [
        "E.M.P.: Pulls units to its center at 150 units per second " + inline_note("Unchanged from previous Shard")])
    import re
    assert re.search(r'<span class="li-tail">second(?:<!--INLINETIP-->)?(?:<!--TIP-->)?<span class="info-tip"', body)


def test_a_card_summary_does_not_repeat_its_header():
    """The header says what the ability levels with ("Passive – levels with Duel"); the summary is the canonical
    "Innate reworked." / "Ability reworked." (owner 2026-10-27, Outfight Them! 7.39 said "levels up with Duel" twice)."""
    import ast
    import glob
    import os
    import re
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = []
    for path in glob.glob(os.path.join(root, "content", "p*.py")):
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "ability_change":
                s = next((k.value.value for k in n.keywords if k.arg == "summary" and isinstance(k.value, ast.Constant)), "")
                if re.search(r"\b(?:levels? up with|scales with|shares level)\b", s or "", re.I):
                    bad.append(f"{os.path.basename(path)}:{n.lineno} {s}")
    assert not bad, bad


def test_header_skips_a_radius_the_text_names_and_a_cast_range_equal_to_it():
    props = {"kind": "Active", "aoe": "625/550/475/400", "castrange": "625/550/475/400", "manacost": "50",
             "cooldown": "45"}
    head, _ = cards_item_abilities._pane_parts(["Phantom Assassin blurs her body. Vanish radius: 625/550/475/400."], props)
    assert "aoe.png" not in head and "castrange.png" not in head
    assert "manacost.png" in head and "cooldown.png" in head
    head, _ = cards_item_abilities._pane_parts(["Shields allies nearby."], {"kind": "Active", "aoe": "1200", "castrange": "1200"})
    assert head.count("iab-ico") == 1 and "aoe.png" in head
    head, _ = cards_item_abilities._pane_parts(["Throws a flare."], {"kind": "Active", "aoe": "300", "castrange": "700"})
    assert "aoe.png" in head and "castrange.png" in head


def test_card_without_caption_has_no_caption_row():
    html = cards_aghs._under_rows_card(None, "rework", "", "scale-change", "<div>o</div>", "<div>n</div>")
    assert "under-rows-caption" not in html and "scale-change" in html


def test_bold_mana_and_cooldown_labels_go_to_the_head():
    # "<b>Mana Cost:</b> 50." stayed in the text under a head that already showed 50 (7.41 Zealot)
    values, desc = cards_item_abilities._iab_take_meta("Teleports units. <b>Mana Cost:</b> 50. <b>Cooldown:</b> 10s.")
    assert values == {"manacost": "50", "cooldown": "10"}
    assert desc == "Teleports units."


def test_bug_note_is_a_bug_box_not_a_question_mark():
    from patch.note_boxes import bug_note
    html = bug_note("Kept the old bonus")
    assert 'class="info-tip bug-tip"' in html and 'class="bug-ico"' in html and ">?<" not in html
    # the owner's silhouette as a CSS mask (2026-10-22); the picture must ship with the site
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert (root / "icons" / "ui" / "bug.png").exists()
    assert "url('icons/ui/bug.png')" in read_css()
