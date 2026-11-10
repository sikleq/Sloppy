"""Guards the card deck: the old/new card pairs that become one deck, the deck's values card (patch/card_deck,
deck_values, deck_extra) and what lights up in it.
"""

import os
import re
from patch import deck_extra, deck_values
from pathlib import Path

import pytest


@pytest.fixture
def no_names(monkeypatch):
    """The naming rules and the game's names on their own: the dictionary (data/rules/value_names.json) names a card's
    numbers over both, its own test checks it."""
    import patch.deck_text as deck_text
    monkeypatch.setattr(deck_text, "names", lambda: {})

ROOT = Path(__file__).resolve().parent.parent
_ROOT_1110 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HEAD = ('<div class="iab-head pane-head"><span class="iab-title"><b class="iab-kind">Active</b></span>'
         '<span class="iab-meta"><span class="iab-m"><img src="../icons/ui/ability/manacost.png" alt="">150</span>'
         '<span class="iab-m"><img src="../icons/ui/ability/cooldown.png" alt="">60/55/50</span></span></div>')


def _table(*rows):
    return '<div class="value-table">' + "".join(
        f'<div class="vt-l">{l}</div><div class="vt-v"><b class="iab-num">{v}</b></div>' for l, v in rows) + "</div>"


def test_an_old_new_card_on_7_38_is_a_deck_with_the_old_card_under():
    # owner 2026-11-09: "новая карточка была слева", the old one "появляется там же вместо новой" on a click; pixel steps
    from patch.card_deck import deck_cards as _deck_cards
    # the tab is a button reached by the keyboard (code review 2026-11-09); below it reads as its class and text
    def deck_cards(html, stem):
        out = _deck_cards(html, stem)
        out = re.sub(r'<button type="button" class="(deck-tab deck-tab-\w+)" aria-label="[^"]*">', r'<span class="\1">', out)
        return out.replace("</button>", "</span>")
    assert ('<button type="button" class="deck-tab deck-tab-new" aria-label="7.38: show 7.37e">7.38</button>'
            in _deck_cards('<div class="ability-change unified-panes"><div class="ability-change-pane ability-change-old">a'
                           '</div><div class="ability-change-pane ability-change-new">b</div></div>', "7.38"))
    pair = ('<div class="ability-change unified-panes aghs-change" data-tag="buff">'
            '<div class="ability-change-pane ability-change-old">a</div><span class="ability-change-arrow">x</span>'
            '<div class="ability-change-pane ability-change-new">b</div></div>')
    single = ('<div class="ability-change unified-panes is-single-new">'
              '<div class="ability-change-pane ability-change-new">c</div></div>')
    old_only = '<div class="ability-change unified-panes"><div class="ability-change-pane ability-change-old">d</div></div>'
    out = deck_cards(pair + single + old_only, "7.38")
    assert out.count("is-deck") == 1
    assert '<div class="ability-change unified-panes aghs-change is-deck" data-tag="buff">' in out
    assert '<div class="ability-change-pane ability-change-old deck-hid"><span class="deck-tab deck-tab-old">' in out
    assert '<div class="ability-change-pane ability-change-new"><span class="deck-tab deck-tab-new">7.38</span>b</div>' in out
    # every patch ("на все патчи"), each with its own previous patch on the old card's tab
    assert '<span class="deck-tab deck-tab-old">7.38c</span>' in deck_cards(pair, "7.39")
    from patch.card_deck import DECK_PAGES
    assert DECK_PAGES is None
    css = (ROOT / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    # the cards under it: thin edges starting well under the top, gold under the pointer — not a bronze slab running up
    # beside the patch tab ("улучши золотую подсветку … обрамление", "в углу ещё вот это")
    # ... one card under it, not two ("кажется будто сзади 2 карточки, а не 1")
    assert "--deck-under: 7px 7px 0 -4px #141312, 7px 7px 0 -3px var(--deck-e1);" in css and "--deck-e2" not in css
    # one value of a deck's card goes to the values card too (7.38 Reflect "Damage percentage: 50% + 2% per minute")
    from patch.value_tables import value_tables
    card = ('<div class="ability-change unified-panes"><div class="ability-change-pane ability-change-old">'
            '<div class="ability-change-body"><div class="ability-change-row">Reflects. Damage percentage: <b>90%</b>.</div>'
            '</div></div><span class="ability-change-arrow">x</span><div class="ability-change-pane ability-change-new">'
            '<div class="ability-change-body"><div class="ability-change-row">Reflects. Damage percentage: <b>50%</b>.</div>'
            '</div></div></div>')
    assert value_tables(card, decks=True).count('<div class="value-table">') == 2
    assert value_tables(card).count('<div class="value-table">') == 0      # elsewhere one value stays a sentence
    assert css.count("box-shadow: var(--deck-glow), var(--deck-under);") == 2 and "#6d5c30" not in css
    # "небольшое полупрозрачное жёлтое свечение у карточки с новой способностью"; none on the old one
    assert "--deck-glow: 0 0 14px 1px rgba(227, 196, 106, 0.16); }" in css
    assert ".ability-change.unified-panes.is-deck.deck-old { --deck-glow: 0 0 0 0 transparent; }" in css
    assert ".ability-change.unified-panes.is-deck > .deck-hid { display: none; }" in css
    assert "background-color: #121110; background-image: linear-gradient(rgba(150, 146, 137, 0.04)" in css   # solid
    # one column on a phone
    assert "  .ability-change.unified-panes.is-deck { grid-template-columns: minmax(0, 1fr); }" in css
    # which one is on top: its patch on a tab ("непонятно, где новая, а где старая")
    tabs = deck_cards(pair, "7.38")
    assert '<span class="deck-tab deck-tab-new">7.38</span>' in tabs and '<span class="deck-tab deck-tab-old">7.37e</span>' in tabs
    assert ".deck-tab { position: absolute; right: -1px; bottom: 100%;" in css
    # a value table: a card of its own beside the text ("описание отдельно, карточка значений рядом")
    vt = '<div class="value-table"><div class="vt-l">Damage</div><div class="vt-v">5</div></div>'
    with_vt = ('<div class="ability-change unified-panes"><div class="ability-change-pane ability-change-old">'
               '<div class="ability-change-body"><div class="ability-change-row">text</div>'
               f'<div class="ability-change-row">{vt}</div></div></div>'
               '<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
               f'<div class="acr-fold"><div class="ability-change-row">{vt}</div></div></div></div></div>')
    deck = deck_cards(with_vt, "7.38")
    assert ('ability-change-old deck-hid has-vals"><div class="deck-card"><span class="deck-tab deck-tab-old">7.37e</span>'
            '<div class="ability-change-body"><div class="ability-change-row">text</div></div></div>'
            f'<div class="deck-vals vt-side">{vt}</div></div>') in deck
    # ... from a folded text too (7.41 Marci Special Delivery: the new side's values stayed under the fade)
    assert ('ability-change-new has-vals"><div class="deck-card"><span class="deck-tab deck-tab-new">7.38</span>'
            '<div class="ability-change-body"><div class="acr-fold">') in deck
    # "как раньше … в 2 карточки рядом, только вторая карточка это блок ха-к": halves, as the old -> new pair
    assert "grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); column-gap: 47px;" in css
    # the hidden side stays hidden: a split card's grid rule beat display:none and the card never changed
    assert ".ability-change.unified-panes.is-deck > .ability-change-pane.has-vals:not(.deck-hid) { grid-column: 1 / -1; display: grid;" in css
    assert "> .ability-change-pane.has-vals {" not in css
    assert ".ability-change.unified-panes.is-deck { grid-template-columns: minmax(0, 1fr) 23px minmax(0, 1fr);" in css
    assert "padding: 0 10px; --pt: 0px; --px: 10px;" in css            # "надпись слишком близко к рамке"
    js = (ROOT / "src" / "js" / "card-deck.js").read_text(encoding="utf-8")
    assert "deck.classList.toggle('deck-old', toOld)" in js
    # only the patch tab swaps (owner 2026-11-10: a click anywhere fought the card's own buttons -> "да, ярлык"); the
    # card is no button: no pointer over it
    assert "const SKIP" not in js and "getSelection" not in js
    assert "border-radius: 0; cursor: pointer; position: relative;" not in css
    # the swap moves the top card out to the right and the one under it up, the deck's height following
    assert "rotate(2deg)" in js
    # code review 2026-11-09: a click on a folded text only opens it; the tab swaps (keyboard too) and keeps the focus;
    # the depth timer cleared; every kind of line redrawn; the incoming card's folds measured before it rises
    assert "if (t.closest('.deck-tab')) swap(deck);" in js and "tab.focus({ preventScroll: true })" in js
    assert "clearTimeout(under);" in js
    assert js.index("if (window.sloppyFoldSmall) window.sloppyFoldSmall();\n    if (still") > 0
    pp = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert "drawAbilityChangeConnectors(); drawBrewlingConnectors();" in pp     # no lines to a card right of its block
    # smooth on a long page ("очень лагает … Solar Guardian"): no height and no z-index in the keyframes — the height
    # once, the depth by a timer, only transform / opacity animated
    assert "deck.animate(" not in js and "zIndex:" not in js and "height:" not in js
    assert "deck.style.minHeight = Math.max(h0, h1) + 'px';" in js
    assert ".ability-change.unified-panes.is-deck.deck-moving > .has-vals > .deck-vals { transition: none; }" in css
    # the card coming up is solid and never lies over the rows below (7.38 Fire Dragon over "Corrosive Dragon")
    assert "opacity: 0.5" not in js
    assert "setTimeout(end, MS + 250);" in js and "if (!done)" in js     # never left "moving"
    # no clip while moving (a repaint in the first frames) — the taller height taken at once keeps the rows below clear;
    # at the end only the lines are redrawn, not a whole-page resize
    assert "clip-path: inset(-80px" not in css
    assert "window.sloppyDrawConnectors()" in js and "new Event('resize')" not in js
    lines_js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert "jobs.push([svg, path, block.getBoundingClientRect()" in lines_js       # measure all, then write
    assert "!newPane || card.classList.contains('is-deck')) return;" in lines_js
    # no room on the right (a phone): out to the left, the page does not grow wider
    assert "free >= 40" in js and "'translate(-24px, -8px) rotate(-2deg)'" in js
    from patch.js_bundle import JS_PARTS
    assert "card-deck" in JS_PARTS
    # the icon's line goes to the card on top
    page = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert page.count(".ability-change-old:not(.deck-hid)") == 3


def test_a_decks_new_values_card_lights_what_changed():
    # owner 2026-11-09, 7.38 Time Zone: "остальные значения не подкрашивать в карточке справа? (в new)" -> "да, так":
    # named by a change row -> its colour; changed with no row, or new -> gold; as it was -> plain; the old card plain
    from patch.deck_values import mark_new_values, rows_before
    cell = lambda l, v: f'<div class="vt-l">{l}</div><div class="vt-v"><b class="iab-num">{v}</b></div>'
    old = f'<div class="value-table">{cell("Duration", "5/5.5/6")}{cell("Radius", "500")}{cell("Speed", "50%")}</div>'
    new = (f'<div class="value-table">{cell("Duration", "3.75/4.25/4.75")}{cell("Radius", "500")}{cell("Speed", "60%")}'
           f'{cell("Cooldown acceleration", "400%")}</div>')
    rows = [("nerf", "duration decreased from 5/5.5/6s to 3.75/4.25/4.75s"), ("rework", "ability reworked.")]
    out = mark_new_values(new, old, rows)
    # ... with the change's % on hover ("при наведении … не всплывает ничего, а мы показываем % разницу")
    nerf = out[out.index("iab-hl-nerf"):]
    assert nerf.startswith("iab-hl-nerf iab-hl-num") and "iab-tip-pct" in nerf[:600] and "3.75/4.25/4.75" in nerf[:600]
    # 50% -> 60% with no row: its % too, and the colour of its way (owner 2026-11-10: gold over a green tip)
    assert "iab-tip-pct" in out[out.index('iab-hl-buff iab-hl-num'):out.index("400%")]
    assert '<div class="vt-v"><b class="iab-num">500</b></div>' in out                       # as it was
    assert '<div class="vt-v"><b class="iab-num">400%</b></div>' in out      # only new to the card: plain (2026-11-10)
    # a card's name for the value and the row's differ (Sonnet 2026-11-09, 7.41 Seaborn Sentinel, Invading Force,
    # Caustic Finale): the row's subject holding all the name's words still names it
    from patch.deck_values import _row_tag
    assert _row_tag("hp regen", [("nerf", "bonus hp regen changed from 6 to 2% max health")]) == "nerf"
    assert _row_tag("movespeed", [("buff", "movement speed bonus rescaled from 10% to 6/9/12%")]) == "buff"
    assert _row_tag("max health damage", [("nerf", "dying unit's max health as damage rescaled from 4% to 2%")]) == "nerf"
    assert _row_tag("duration", [("buff", "stun duration increased"), ("nerf", "slow duration decreased")]) is None
    css = (ROOT / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    assert ".ability-change.is-deck > .ability-change-old .value-table .iab-hl { color: inherit; background: none;" in css
    # a value its card lit already takes the way of the row naming it (7.38 Demonic Cleanse: red by mixed %, row BUFF)
    lit = ('<div class="value-table"><div class="vt-l">Cleanse heal</div><div class="vt-v"><span class="iab-hl '
           'iab-hl-nerf iab-hl-num">450</span></div></div>')
    cleanse = mark_new_values(lit, "", [("buff", "cleanse heal rescaled from 300/450/600 to 450")])
    assert 'iab-hl-buff iab-hl-num">' in cleanse and "iab-tip-pct" in cleanse and ">450</span>" in cleanse
    assert 'iab-hl-nerf iab-hl-num iab-hl-flat">450' in mark_new_values(lit, "", [])   # no % to show: no dotted line
    # no old table to compare with: only what a row names
    only = mark_new_values(new, "", rows)
    assert only.count("iab-hl-new") == 0 and only.count("iab-hl-nerf") == 1
    page = ('<div class="ability-change-block"><ul class="changes"><li data-tag="nerf" class="x"><span class="badge">N'
            '</span><span class="row-text">Duration decreased</span></li></ul>CARD')
    assert rows_before(page, page.index("CARD")) == [("nerf", "duration decreased")]
    # ... and the card's own rows under it (7.40 Clinkz "Spawn Interval improved", BUFF)
    under = page + '<ul class="changes"><li data-tag="buff"><span class="row-text">Spawn interval improved</span></li></ul>'
    assert ("buff", "spawn interval improved") in rows_before(under, under.index("CARD"))
    assert rows_before(under + '<div class="ability-block"><li data-tag="nerf"><span class="row-text">Other</span></li>',
                       under.index("CARD"))[-1] == ("buff", "spawn interval improved")      # not the next block's


def test_a_deck_pane_with_several_named_tables_moves_them_all_to_the_values_card():
    # owner 2026-11-09, 7.40 Clinkz Burning Army + Bone and Arrow: "почему тут не в 2 карточки? (1 с ха-ками справа)"
    from patch.card_deck import _split_values
    vt = lambda v: f'<div class="value-table"><div class="vt-l">X</div><div class="vt-v">{v}</div></div>'
    sub = lambda n: f'<span class="ac-sub"><img src="i.png"><b class="ac-sub-name">{n}</b></span>'
    inner = (f'<div class="ability-change-body"><div class="ability-change-row aghanim-scepter">{sub("Burning Army")}: '
             f'Grants. {vt(1)}</div><div class="ability-change-row aghanim-scepter">{sub("Skeleton Walk")}: More. {vt(2)}'
             '</div></div>')
    text, values = _split_values(inner)
    assert "value-table" not in text and "Grants." in text and "More." in text
    assert values == (f'<div class="deck-vals-head">{sub("Burning Army")}</div>{vt(1)}'
                      f'<div class="deck-vals-head">{sub("Skeleton Walk")}</div>{vt(2)}')
    # two tables with no names over them stay by their text
    plain = f'<div class="ability-change-row">a {vt(1)}</div><div class="ability-change-row">b {vt(2)}</div>'
    assert _split_values(plain) == (plain, None)


def test_a_decks_part_named_for_another_ability_reads_that_abilitys_rows():
    # Sonnet 2026-11-09, 7.40 Clinkz: the Scepter card's "Burning Army" part, its "Spawn Interval improved" (BUFF) row
    # under the hero's own Burning Army block
    from patch.deck_values import rows_of_named
    page = ('<div class="entity-block"><div class="ability-block"><h4 class="ability-title">Skeleton Walk</h4>CARD</div>'
            '<div class="ability-block"><div class="ability-icon-wrap"></div><h4 class="ability-title">Burning Army</h4>'
            '<ul class="changes"><li data-tag="buff"><span class="row-text">Spawn Interval improved</span></li></ul></div>'
            '<div class="ability-block"><h4 class="ability-title">Other</h4><li data-tag="nerf"><span class="row-text">X'
            '</span></li></div></div><div class="entity-block">')
    card = '<b class="ac-sub-name">Burning Army</b>'
    assert rows_of_named(page, page.index("CARD"), card) == [("buff", "spawn interval improved")]
    assert rows_of_named(page, page.index("CARD"), "no parts") == []


def test_a_deck_pane_gets_its_header_values_and_its_texts_numbers_as_rows(monkeypatch):
    # owner 2026-11-09, 7.40 Spirit Bear / Entangle's Scepter: "тут тоже можно карточки справа добавить" -> "числа из
    # текста и мана перезарядка": the header's values first, then each number the text says, named by the game
    from patch import deck_extra
    w = lambda *words: frozenset(words)          # the words around the number in the game's own sentence
    none = frozenset()                           # a name the game gives (a tooltip): no word of it needed nearby
    # the ability's own values (owner 2026-11-10: all of them the text says, the game's description or not)
    monkeypatch.setattr(deck_extra, "_game_values", lambda slug, version: (
        ("Leash range", "1100", True), ("Backlash damage", "20", True), ("Bear health", "1500", True),
        # a name made of the key with none of its words by the number: not used (7.40 Clinkz "Hero stacks")
        ("Enemy stacks", "20", False)) if slug == "lone_druid_spirit_bear" else ())
    monkeypatch.setattr(deck_extra, "_pairs", lambda slug, version, kind: (
        ("Stacks", "5", w("applies", "stacks"), none), ("Radius", "=450", w("radius"), none),
        ("Radius", "100", w("radius"), none)) if kind == "scepter" else ())
    meta = ('<div class="iab-head pane-head"><span class="iab-title"><b class="iab-kind">Active</b></span>'
            '<span class="iab-meta"><span class="iab-m"><img class="iab-ico" src="../icons/ui/ability/manacost.png" alt="">'
            '75</span><span class="iab-m"><img class="iab-ico" src="../icons/ui/ability/cooldown.png" alt="">120</span>'
            '</span></div>')
    body = ('<div class="ability-change-body"><div class="ability-change-row">If the bear moves <b class="iab-num">1100'
            '</b> away past its leash, Lone Druid suffers <b class="iab-num">20%</b> as backlash.</div></div>')
    labels = lambda html: [re.sub(r"<[^>]+>", "", m) for m in re.findall(r'<div class="vt-l[^"]*">(.*?)</div><div', html)]
    out = deck_extra.enrich(meta + body, "lone_druid_spirit_bear", "7.40")
    assert '<span class="iab-meta"></span></div>' in out                      # the header keeps only its kind
    assert labels(out) == ["Mana cost", "Cooldown", "Leash range", "Backlash damage"]
    assert "Bear health" not in out and "If the bear moves" in out              # only what the text says; text kept
    assert '<div class="vt-v"><b class="iab-num">20%</b></div>' in out          # as the text writes it, with its %
    assert '<div class="vt-v vt-first"><b class="iab-num">75</b></div>' in out  # a header number bold ("75" stood thin)
    css = (ROOT / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    assert ".value-table > .vt-l > .iab-ico:first-child { margin-right: 6px; top: 0; }" in css   # "иконка слишком близко"
    # a value lit by its card gets its % on hover from the row's "from X to" when the old card had none (Spirit Bear)
    from patch.deck_values import mark_new_values
    lit = ('<div class="value-table"><div class="vt-l">Cooldown</div><div class="vt-v"><span class="iab-hl iab-hl-buff '
           'iab-hl-num">120</span></div></div>')
    out = mark_new_values(lit, "", [("buff", "cooldown decreased from 150/140/130/120s to 120s")])
    assert "iab-tip-pct" in out and "iab-hl-buff iab-hl-num" in out
    aghs = ('<div class="ability-change-body"><div class="ability-change-row aghanim-scepter"><span class="ac-sub">'
            '<img src="../icons/_t/abilities/lone_druid_entangle.webp"><b class="ac-sub-name">Entangle</b></span>: '
            'applies <b class="iab-num">5</b> stacks, radius to <b class="iab-num">450</b>.</div></div>')
    out = deck_extra.enrich(aghs, "lone_druid_spirit_bear", "7.40")
    assert sorted(labels(out)) == ["Radius", "Stacks"] and '<b class="iab-num">450</b>' in out.split("value-table")[1]
    # a value with no tooltip of its own: named by its key, the hero's words off ("bear_attack_leash_range")
    from patch.deck_extra import _key_label, _norm
    assert _key_label("bear_attack_leash_range", "lone_druid_spirit_bear") == "Bear attack leash range"
    assert _key_label("lone_druid_counters_applied_tooltip", "lone_druid_entangle") == "Counters applied"
    assert _norm("20.0") == _norm("20%") == "20" and _norm("=450") == "450"
    # the ability is the card's own block's, by its icon's slug — never another block's (7.40 Spirit Bear read Lion's)
    from patch.card_deck import _block_slug
    page = ('<div class="ability-block"><div class="ability-icon-wrap"><img src="../icons/_t/abilities/lion_voodoo.webp">'
            '</div></div><div class="ability-change-block"><div class="ability-icon-wrap has-old-underlay"><img src="x.png" '
            'class="ability-icon-old-underlay"><img src="../icons/_t/abilities/lone_druid_spirit_bear.webp" '
            'class="ability-icon-img" data-slug="lone_druid_spirit_bear"></div>CARD')
    assert _block_slug(page, page.index("CARD")) == "lone_druid_spirit_bear"
    from patch.card_deck import _old_slug          # the old side's own ability, or none when its icon names none
    assert _old_slug(page, page.index("CARD"), "lone_druid_spirit_bear") is None
    gift = page.replace('src="x.png" class="ability-icon-old-underlay"',
                        'src="../icons/_t/abilities/lone_druid_gift_bearer.webp" class="ability-icon-old-underlay"')
    assert _old_slug(gift, gift.index("CARD"), "lone_druid_spirit_bear") == "lone_druid_gift_bearer"
    bare = '<div class="ability-block"><img src="../icons/_t/abilities/lion_voodoo.webp"></div><div class="ability-block">CARD'
    assert _block_slug(bare, bare.index("CARD")) is None
    # one number that may be several values: none named
    monkeypatch.setattr(deck_extra, "_pairs", lambda slug, version, kind: (
        ("Stack duration", "10", frozenset({"lasts"}), frozenset()), ("Buff duration", "10", frozenset({"lasts"}), frozenset())))
    two = '<div class="ability-change-body"><div class="ability-change-row">lasts <b class="iab-num">10</b>s.</div></div>'
    # ... named by its sentence instead (owner 2026-11-10: every number of the text has its row)
    out = deck_extra.enrich(two, "x_y", "7.40")
    assert "Stack duration" not in out and "Buff duration" not in out and 'vt-said">Duration</div>' in out
    # a header value the card's own table has already: not twice (7.41 Marci Special Delivery "Cooldown" twice)
    own = (meta + '<div class="ability-change-body"><div class="ability-change-row"><div class="value-table"><div class="vt-l '
           'vt-first">Cooldown</div><div class="vt-v vt-first">245s - 5s per level</div></div></div></div>')
    assert labels(deck_extra.enrich(own, "x_y", "7.40")) == ["Mana cost", "Cooldown"]


def test_header_values_leave_no_tag_in_the_cell():
    """The last header value took its closing "</span>" along: "60/55/50</span>", thin and with no % on hover."""
    inner, rows = deck_extra._meta_rows(_HEAD)
    assert [v for _, v in rows] == ['<b class="iab-num">150</b>', '<b class="iab-num">60/55/50</b>']
    assert inner.count("<span") == inner.count("</span>")


def test_values_card_lists_the_abilitys_own_values_the_text_says(no_names):
    """7.39e Entangling Claws: the game's description has no placeholder, its values have names — each one the text
    says gets a row."""
    if not deck_extra._game_values("lone_druid_spirit_bear_entangle", "7.39e"):
        return                                   # no game files for that patch here
    body = ('<div class="iab-head pane-head"><span class="iab-title"></span><span class="iab-meta"></span></div>'
            '<div class="ability-change-body"><div class="ability-change-row">Attacks have a '
            '<b class="iab-num">20%</b> chance (<b class="iab-num">30%</b> in True Form) to root the target for '
            '<b class="iab-num">1/1.6/2.2/2.8s</b>, dealing <b class="iab-num">30/40/50/60</b> damage per second '
            '(<b class="iab-num">3x</b> against creeps) within <b class="iab-num">777</b> range.</div></div>')
    out = deck_extra.enrich(body, "lone_druid_spirit_bear_entangle", "7.39e")
    for label, value in (("Damage per second", "30/40/50/60"), ("Bear entangle chance", "20%"),
                         ("Hero duration", "1/1.6/2.2/2.8s"), ("True Form entangle chance", "30%"),
                         ("Creep damage multiplier", "3x")):
        assert f'vt-said">{label}</div>' in out, label
        assert f'<b class="iab-num">{value}</b></div>' in out, value
    # a number that is no value of the ability: named by its sentence (owner 2026-11-10: every number has its row)
    assert 'vt-said">Range</div><div class="vt-v"><b class="iab-num">777</b>' in out


def test_key_named_value_needs_its_word_near_the_number():
    assert deck_extra._shares("Creep damage multiplier", {"against", "creeps"})
    assert not deck_extra._shares("Hero stacks", {"applies", "attack"})
    assert deck_extra._shares("Spread radius", {"units", "aoe"})       # 7.41 Doom "in a 66 AoE"


def test_changed_value_with_no_row_takes_the_colour_of_its_way():
    """7.40 Shadow Step: "Mana cost" 150 -> 60/65/70/75 stood gold over a green tip. Its colour is its way; gold stays
    for a value that is new."""
    old = _table(("Mana cost", "150"), ("Cooldown", "60/55/50"), ("Damage", "100"))
    new = _table(("Mana cost", "60/65/70/75"), ("Cooldown", "70"), ("Damage", "150"), ("Cast range", "700"))
    out = deck_values.mark_new_values(new, old, [])
    cells = dict(zip(("mana", "cd", "dmg", "range"), out.split('<div class="vt-l">')[1:]))
    assert "iab-hl-buff" in cells["mana"] and "iab-tip-pct" in cells["mana"]
    assert "iab-hl-nerf" in cells["cd"]
    assert "iab-hl-buff" in cells["dmg"]
    # a value only new to the card stays plain: the card lights what changed ("не нужно красить new цветом просто
    # новые значения")
    assert "iab-hl" not in cells["range"]


def test_lists_of_different_lengths_compare_first_and_last_level():
    """7.40 Shadow Step "Cooldown" 60/55/50 -> 32/28/24/20 had no % on hover: three levels against four."""
    out = deck_values.mark_new_values(_table(("Cooldown", "32/28/24/20")), _table(("Cooldown", "60/55/50")), [])
    assert "iab-hl-buff" in out and "iab-tip-pct" in out
    assert "-47%" in out and "-60%" in out


def test_a_number_equal_by_chance_names_no_value(monkeypatch):
    """Sonnet 2026-11-10: "3 bonus levels and 1 bonus health" read "Bonus hp = 3"; "10% of Strength" read "Max stacks";
    "from 20% to 40%" gave the old 20% as the value now; "Costs 5 souls" read "Max soul increase" beside "Soul cost"."""
    monkeypatch.setattr(deck_extra, "_game_values", lambda slug, version: (
        ("Bonus levels", "3", True), ("Bonus hp", "3", True), ("Max stacks", "10", True), ("Bonus speed", "20", True),
        ("Soul cost", "5", True), ("Max soul increase", "5", True), ("Spread radius", "66", True)))
    num = lambda v: f'<b class="iab-num">{v}</b>'
    body = ('<div class="iab-head pane-head"><span class="iab-title"></span><span class="iab-meta"></span></div>'
            f'<div class="ability-change-body"><div class="ability-change-row">Grants {num(3)} bonus levels. Status '
            f'Resistance equal to {num("10%")} of Strength. Speed raised from {num("20%")} to {num("40%")}. Costs '
            f'{num(5)} souls. Its damage grows by {num("66%")} each second while enemies stand within the spread radius '
            f'of {num(66)}.</div></div>')
    out = deck_extra.enrich(body, "x", "7.41")
    assert 'vt-said">Bonus levels</div>' in out and 'vt-said">Soul cost</div>' in out
    for wrong in ("Bonus hp", "Max stacks", "Bonus speed", "Max soul increase"):
        assert wrong not in out, wrong
    # written as the text writes it where it speaks of that value
    assert 'vt-said">Spread radius</div><div class="vt-v"><b class="iab-num">66</b>' in out


def test_an_upgrades_part_lists_the_values_the_upgrade_sets():
    """7.37 Blink's Scepter: only "5s" and "20%" had rows — its cooldown with the upgrade and its debuff's duration,
    which the text leaves bare ("(6)"), have theirs."""
    if not deck_extra._upgrade_values("antimage_blink", "7.37", "scepter"):
        return                                   # no game files for that patch here
    num = lambda v: f'<b class="iab-num">{v}</b>'
    body = ('<div class="iab-head pane-head"><span class="iab-title"></span><span class="iab-meta"></span></div>'
            '<div class="ability-change-body"><div class="ability-change-row aghanim-scepter"><span class="ac-sub">'
            '<img src="../icons/_t/abilities/antimage_blink.webp"><b class="ac-sub-name">Blink</b></span>: After casting '
            f'Blink, your next Mana Break within {num("5s")} burns an additional {num("20%")} max mana and prevents the '
            f'target from regenerating mana for a short duration ({num(6)}). Blink Cooldown ({num("12.5/10/7.5/5s")}) '
            f'reduced by {num("1s")}.</div></div>')
    out = deck_extra.enrich(body, "antimage_blink", "7.37")
    cells = dict(re.findall(r'<div class="vt-l[^"]*">([^<]+)</div><div class="vt-v[^"]*">(.*?)</div>(?=<div class="vt-l|</div>)', out))
    assert '<b class="iab-num">6s</b>' == cells["Debuff duration"]            # new with the upgrade: plain
    # the ability's own cooldown made shorter by the upgrade: a buff with its %, not a value new to the card
    assert "iab-hl-buff" in cells["Cooldown"] and "iab-tip-pct" in cells["Cooldown"] and "12.5/10/7.5/5s" in cells["Cooldown"]


def test_equal_lists_are_read_each_among_its_own_words(monkeypatch):
    """7.37 Brewmaster: "10/15/20/25/30% evasion" and "10/15/20/25/30 Attack Speed" in two rows gave "Attack speed …%"
    and a "Dodge chance" with no %."""
    monkeypatch.setattr(deck_extra, "_game_values", lambda slug, version: (
        ("Attack speed", "10 15 20 25 30".replace(" ", "/"), True), ("Dodge chance", "10/15/20/25/30", True)))
    num = lambda v: f'<b class="iab-num">{v}</b>'
    body = ('<div class="iab-head pane-head"><span class="iab-title"></span><span class="iab-meta"></span></div>'
            f'<div class="ability-change-body"><div class="ability-change-row">Storm: grants {num("10/15/20/25/30%")} '
            f'evasion and bonus move speed.</div><div class="ability-change-row">Fire: grants a critical strike and '
            f'{num("10/15/20/25/30")} Attack Speed.</div></div>')
    out = deck_extra.enrich(body, "x", "7.37")
    rows = dict(re.findall(r'<div class="vt-l[^"]*">([^<]+)</div><div class="vt-v[^"]*"><b class="iab-num">([^<]+)</b>', out))
    assert rows == {"Attack speed": "10/15/20/25/30", "Dodge chance": "10/15/20/25/30%"}


def test_a_lit_value_with_no_tip_has_no_dotted_line():
    """7.40 Shadow Step: the gold values new to the ability stood dotted, the line that says "a % on hover"."""
    out = deck_values.mark_new_values(_table(("Mana cost", "60"), ("Cast range", "700")), _table(("Mana cost", "150")),
                                      [("buff", "cast range improved")])
    mana, cast = out.split('<div class="vt-l">')[1:]
    assert "iab-tip-pct" in mana and "iab-hl-flat" not in mana
    assert 'iab-hl-buff iab-hl-num iab-hl-flat"' in cast            # lit by its row, no number to compare with
    css = open(os.path.join(_ROOT_1110, "src", "css", "patch-ability-change.css"), encoding="utf-8").read()
    assert ".value-table .iab-hl.iab-hl-num.iab-hl-flat { border-bottom-color: transparent; }" in css


def test_a_facet_cards_numbers_are_the_values_the_facet_sets(no_names):
    """A facet card (7.38 Starsurge on Starbreaker, Glacial Guard on Crystal Nova) had no values card: its numbers are
    its ability's values with the facet's own key, which the game names otherwise ("dawnbreaker_blaze")."""
    if not deck_extra._upgrade_values("crystal_maiden_crystal_nova", "7.38", "facet:crystal_maiden_glacial_guard"):
        return                                   # no game files for that patch here
    num = lambda v: f'<b class="iab-num">{v}</b>'
    body = ('<div class="iab-head pane-head"><span class="iab-title"><b class="iab-kind">Active:</b> '
            '<span class="iab-name">Crystal Nova</span></span><span class="iab-meta"></span></div>'
            f'<div class="ability-change-body"><div class="ability-change-row">Increases radius by {num(100)} and grants '
            f'allied heroes in the affected area a {num("40/70/100/130")} physical barrier for {num("4s")}.</div></div>')
    out = deck_extra.enrich(body, None, "7.38", facet="glacial_guard")
    cells = dict(re.findall(r'<div class="vt-l[^"]*">([^<]+)</div><div class="vt-v[^"]*"><b class="iab-num">([^<]+)</b>',
                            out))
    assert cells.get("Physical barrier amount") == "40/70/100/130" and cells.get("Barrier duration") == "4s"
    assert cells.get("Radius") == "+100"            # "by 100": the bonus, written as one
    assert deck_extra._facet_key(("dawnbreaker_fire_wreath",), "starsurge", "7.38") == "dawnbreaker_blaze"


def test_rows_of_one_number_under_one_name_are_one_row():
    """7.38 Demonic Cleanse: "Charge restore time" and "Base charge restore time", both 70/65/60s."""
    rows = [("Charge restore time", '<b class="iab-num">70/65/60s</b>'),
            ("Base charge restore time", '<b class="iab-num">70/65/60s</b>'), ("Radius", '<b class="iab-num">70/65/60s</b>')]
    assert [l for l, _ in deck_extra._dedupe(rows)] == ["Charge restore time", "Radius"]


def test_an_upgrades_value_against_levels_that_do_not_match_is_not_lit():
    """7.40 Rupture's Scepter "Increases initial damage to 13%" lit red against 10/12/14%."""
    html = '<b class="iab-num">13%</b>'
    assert deck_extra._against_base("Health damage", html, "10/12/14%") == html
    assert "iab-hl-buff" in deck_extra._against_base("Cooldown", '<b class="iab-num">12.5/10/7.5/5s</b>', "13.5/11/8.5/6")


def test_a_name_made_of_a_key_names_nothing_the_text_does_not_say():
    """7.38 Starsurge: "Movespeed bonus radius" for "allies within 700 radius gain bonus attack speed"."""
    assert deck_extra._foreign_stat("Movespeed bonus radius", {"allies", "within", "radius", "gain", "bonus", "attack"})
    assert deck_extra._foreign_stat("Self multiplier bonus max stacks", {"bonus", "max", "multiplier"})
    assert not deck_extra._foreign_stat("Creep damage multiplier", {"damage", "second", "against", "creeps"})
    assert not deck_extra._foreign_stat("Bear leash range", {"bear", "moves", "distance"})


def _said(text):
    from patch.deck_text import free_rows
    inner = f'<div class="ability-change-body"><div class="ability-change-row">{text}</div></div>'
    return free_rows(inner, set(), set(), deck_extra._norm)


def test_every_number_of_the_text_gets_a_row_named_by_its_sentence(no_names):
    """Owner 2026-11-10: "всё ещё неправильно определяешь, сколько и какие значения писать в правой карточке"."""
    num = lambda v: f'<b class="iab-num">{v}</b>'
    rows = dict(_said(f"Every {num(6.66)} minutes, duration is increased by {num('0.66s')} (doubled in Turbo). Damage per "
                      f"second is decreased from {num('30/50/70')} to {num('30/45/60')}"))
    assert rows == {"Interval": '<b class="iab-num">6.66 min</b>', "Duration": '<b class="iab-num">+0.66s</b>',
                    "Damage per second": '<b class="iab-num">30/45/60</b>'}              # 30/50/70 was the value before
    rows = dict(_said(f"Rolling over an allied hero grants the allied hero {num('15/20/25/30%')} bonus movespeed for "
                      f"{num('4s')}."))
    assert rows == {"Bonus movespeed": '<b class="iab-num">15/20/25/30%</b>', "Duration": '<b class="iab-num">4s</b>'}
    rows = dict(_said(f"Ember Spirit is continuously burning, dealing damage ({num('10/20/30/40')}) per second to all"))
    assert rows == {"Damage per second": '<b class="iab-num">10/20/30/40</b>'}
    rows = dict(_said(f"dealing damage ({num('3x')} against creeps)"))
    assert rows == {"Multiplier against creeps": '<b class="iab-num">3x</b>'}


def test_creeps_and_heroes_rows_of_one_value_are_one_row():
    """7.36c Astral Spirit: "Bonus speed (creeps)" and "Bonus speed (heroes)" in two rows each."""
    from patch.deck_text import merge_unit_pairs
    cell = lambda l, v: f'<div class="vt-l">{l}</div><div class="vt-v"><b class="iab-num">{v}</b></div>'
    table = ('<div class="value-table">' + cell("Damage", "50") + cell("Bonus speed (creeps)", "1.5%")
             + cell("Bonus speed (heroes)", "4/5/6/7/8%") + "</div>")
    out = merge_unit_pairs(table)
    assert out.count('<div class="vt-l') == 2
    assert ('<div class="vt-l">Bonus speed</div><div class="vt-v"><b class="iab-num">4/5/6/7/8%</b>'
            '<span class="vt-sub">creeps <b class="iab-num">1.5%</b></span></div>') in out
    css = (ROOT / "src" / "css" / "patch-ability-change.css").read_text(encoding="utf-8")
    assert ".value-table .vt-sub { display: block;" in css


def test_a_row_holding_the_table_still_gives_its_numbers():
    """7.37 Ghostship's Scepter: its text and its table in one row, only "Num cannon volleys 3" in the values card."""
    from patch.deck_text import free_rows
    num = lambda v: f'<b class="iab-num">{v}</b>'
    inner = (f'<div class="ability-change-body"><div class="ability-change-row">A fleet of {num(2)} ships on a {num(2.5)} '
             f"second interval deal {num('40%')} of Ghostship's damage." '<div class="value-table"><div class="vt-l">Volleys'
             '</div><div class="vt-v"><b class="iab-num">3</b></div></div></div></div>')
    assert dict(free_rows(inner, {"3"}, set(), deck_extra._norm)) == {
        "Ships": num(2), "Interval": num("2.5s"), "Damage": num("40%")}
    # "Label: value" names itself
    plain = '<div class="ability-change-body"><div class="ability-change-row">Cannonball projectile radius: ' + num(100) + '.</div></div>'
    assert dict(free_rows(plain, set(), set(), deck_extra._norm)) == {"Cannonball projectile radius": num(100)}


def test_a_pane_of_several_parts_gives_each_table_its_numbers():
    vt = lambda: '<div class="value-table"><div class="vt-l">X</div><div class="vt-v"><b class="iab-num">9</b></div></div>'
    num = lambda v: f'<b class="iab-num">{v}</b>'
    inner = ('<div class="ability-change-body">'
             f'<div class="ability-change-row">A: lasts for {num("4s")}. {vt()}</div>'
             f'<div class="ability-change-row">B: grants {num("20%")} bonus damage. {vt()}</div></div>')
    out = deck_extra.enrich(inner, None, "7.41")
    first, second = out.split('<div class="ability-change-row">')[1:]
    assert 'Duration</div><div class="vt-v"><b class="iab-num">4s</b>' in first and "20%" not in first.split("value-table")[1]
    assert 'Bonus damage</div><div class="vt-v"><b class="iab-num">20%</b>' in second


def test_an_aghanims_row_the_card_retells_is_hidden_and_its_rest_goes_in():
    """7.37 Ghostship: the Scepter row said the card again, its "projectile radius: 100" only in the row."""
    from patch.card_deck import retold_rows
    page = ('<div class="ability-block"><ul class="changes"><li data-tag="buff new" class="aghanim-scepter"><span '
            'class="badge new" data-tag="new">NEW</span><span '
            "class=\"row-text\">Now upgraded with Aghanim's Scepter. Creates a fleet of 2 ships at the target point. "
            'Cannonball projectile radius: 100.</span></li></ul><div class="ability-change unified-panes is-deck">'
            '<div class="ability-change-pane ability-change-new"><div class="ability-change-body"><div class="ability-'
            'change-row aghanim-scepter">Ghostship creates a fleet of <b class="iab-num">2</b> ships at the target point.'
            '</div></div></div></div></div><div class="ability-block">')
    out = retold_rows(page)
    assert 'class="iab-covered covered-card aghanim-scepter"' in out
    assert 'ships at the target point. Cannonball projectile radius: <b class="iab-num">100</b>.</div>' in out
    assert "NEW" not in out.split("ability-change-pane")[1]         # the row's badge and lead stay out of the card


def test_an_upgrade_the_card_has_no_part_for_becomes_its_part(no_names):
    """7.37 Immolation: "Can be upgraded with Aghanim's Shard. Increases damage by 10, radius by 175 …" stood under the
    card; owner 2026-11-10: "не нужно внутри левой карточки вставить?" — it goes into the card as its Shard part."""
    from patch.card_deck import retold_rows
    page = ('<div class="ability-block"><ul class="changes"><li data-tag="misc" class="aghanim-shard"><span class="badge '
            'misc" data-tag="misc">MISC</span><span class="row-text">Can be upgraded with Aghanim&#x27;s Shard. Increases '
            'damage by 10, radius by 175</span></li></ul><div class="ability-change unified-panes is-single-new">'
            '<div class="ability-change-pane ability-change-new"><div class="ability-change-body"><div class="ability-'
            'change-row">Burns.</div></div></div></div></div><div class="ability-block">').replace("&#x27;", "'")
    out = retold_rows(page)
    assert 'class="iab-covered covered-card aghanim-shard"' in out
    assert ('<div class="ability-change-row aghanim-shard"><span class="aghanim-marker shard"></span>Increases damage by '
            '<b class="iab-num">10</b>, radius by <b class="iab-num">175</b></div>') in out
    # ... the card above the row too, as on the page (its rows under the card)
    ul = page[page.index("<ul"):page.index("</ul>") + 5]
    under = page.replace(ul, "").replace('</div></div></div></div></div><div class="ability-block">',
                                         '</div></div></div></div>' + ul + '</div><div class="ability-block">')
    assert 'aghanim-marker shard"></span>Increases damage by' in retold_rows(under)
    # its [?] goes with it, whole, no stray "?" (7.37 Immolation "… level of Immolation?")
    tipped = page.replace("radius by 175</span>", 'radius by 175<span class="info-tip" tabindex="0">?<span '
                          'class="info-pop">Both hit</span></span></span>')
    assert 'radius by <b class="iab-num">175</b><span class="info-tip" tabindex="0">?' in retold_rows(tipped)
    # its numbers are the upgrade's: named so, and "by 175" is a change even beside a Radius 175
    from patch.deck_text import free_rows
    part = ('<div class="ability-change-body"><div class="ability-change-row">Burns.</div>'
            '<div class="ability-change-row aghanim-shard">Increases damage by '
            '<b class="iab-num">10</b>, radius by <b class="iab-num">175</b></div></div>')
    assert dict(free_rows(part, {"175"}, set(), deck_extra._norm)) == {
        "Damage (Shard)": '<b class="iab-num">+10</b>', "Radius (Shard)": '<b class="iab-num">+175</b>'}
    # ... a card that is all the upgrade needs no word for it (7.37 Ghostship's Scepter card)
    alone = part.replace('<div class="ability-change-row">Burns.</div>', "")
    assert dict(free_rows(alone, {"175"}, set(), deck_extra._norm)) == {
        "Damage": '<b class="iab-num">+10</b>', "Radius": '<b class="iab-num">+175</b>'}
    # a balance change of an upgrade stays a row
    change = page.replace("Can be upgraded with Aghanim's Shard. Increases", "Aghanim's Shard damage increased")
    assert "iab-covered" not in retold_rows(change)


def test_values_of_another_ability_are_not_compared():
    """7.37 Tidebringer -> Admiral's Rum: the new innate's "Cooldown 60" lit red with +275%…+1400% against Tidebringer's
    cooldown (owner 2026-11-10: "неправильно сравнивать перезарядки … это разные способности")."""
    from patch.card_deck import _deck
    cell = lambda l, v: f'<div class="vt-l">{l}</div><div class="vt-v"><b class="iab-num">{v}</b></div>'
    pane = lambda side, v: (f'<div class="ability-change-pane ability-change-{side}"><div class="ability-change-body">'
                            f'<div class="ability-change-row">Text.<div class="value-table">{cell("Cooldown", v)}</div>'
                            '</div></div></div>')
    card = '<div class="ability-change unified-panes">' + pane("old", "16/12/8/4") + pane("new", "60") + "</div>"
    versions = {"new": "7.37", "old": "7.36c"}
    assert "iab-hl" not in _deck(card, versions, (), {"new": "kunkka_admirals_rum", "old": "kunkka_tidebringer"}, True)
    assert "iab-hl" not in _deck(card, versions, (), {"new": "a", "old": "b"})
    assert "iab-hl-nerf" in _deck(card, versions, (), {"new": "a", "old": "a"})


def test_the_dictionary_of_names_names_a_number_first(monkeypatch):
    """Owner 2026-11-10: "словарь подписей" — a number's name written for its sentence wins over the game's and the
    sentence rule; "" leaves the number without a row."""
    from patch import deck_text
    num = lambda v: f'<b class="iab-num">{v}</b>'
    row = f"Grants allies {num('15%')} bonus movespeed for {num('4s')}. Example: Clarity restores {num(150)} mana"
    flat, spans = deck_text._spans(row)
    keys = [deck_text.name_key(flat, a, b) for a, b, _ in spans]
    assert keys[0] == "grants allies [#] bonus movespeed for #"          # its own and other numbers left out
    monkeypatch.setattr(deck_text, "names", lambda: {keys[0]: "Ally movement speed", keys[2]: ""})
    inner = f'<div class="ability-change-body"><div class="ability-change-row">{row}</div></div>'
    rows = dict(deck_text.free_rows(inner, set(), set(), deck_extra._norm))
    assert rows == {"Ally movement speed": num("15%"), "Duration": num("4s")}
    assert deck_text.written_numbers(inner, deck_extra._norm) == {"15", "150"}


def test_the_dictionary_file_is_names():
    import json
    path = ROOT / "data" / "rules" / "value_names.json"
    if not path.exists():
        return
    names = {k: v for k, v in json.loads(path.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    for key, name in names.items():
        assert "[#]" in key, key
        assert name == "" or (1 <= len(name.split()) <= 5 and "." not in name and name[0].isupper()), (key, name)


def test_values_card_rows_are_written_the_one_way():
    """Sonnet proofread 2026-11-10 of all 540 values cards: "Movement slow +35%" for "slowing … by 35%", "Duration 10"
    with no unit, "Hp regen", "Root Duration", "Scepter max level (Scepter)"."""
    from patch.value_tidy import tidy
    cell = lambda l, v: f'<div class="vt-l">{l}</div><div class="vt-v"><b class="iab-num">{v}</b></div>'
    text = ("Lasts 10 minutes. Grants Max Fervor stacks, increased by Debuff Duration bonuses. Spins with Blade Fury, "
            "deals damage per Quas")
    out = tidy(cell("Movement slow", "+35%") + cell("Cooldown reduction", "−10s") + cell("Max level penalty", "−1")
               + cell("Duration", "12") + cell("Torrent interval", "0.25") + cell("Consume time", "10")
               + cell("Damage reduction", "+5%") + cell("Leech slow", "+8/14%") + cell("Base Duration", "6s")
               + cell("Attack slow in water", "+2%") + cell("Root time by tree", "2")
               + cell("Blade fury radius", "250") + cell("Damage per quas", "5") + cell("Attack range buffer", "125")
               + cell("Hp regen", "24") + cell("Root Duration", "2s") + cell("Scepter max level (Scepter)", "10")
               + cell("Battle Trance Max Fervor Stacks", "15") + cell("Num cannon volleys", "3"), text)
    got = re.findall(r'<div class="vt-l">([^<]*)</div><div class="vt-v"><b class="iab-num">([^<]*)</b>', out)
    assert got == [("Movement slow", "35%"), ("Cooldown reduction", "10s"), ("Max level penalty", "−1"),
                   ("Duration", "12s"), ("Torrent interval", "0.25s"), ("Consume time", "10 min"),
                   ("Damage reduction", "+5%"), ("Leech slow", "8/14%"), ("Base duration", "6s"),
                   ("Attack slow in water", "2%"), ("Root time by tree", "2s"), ("Blade Fury radius", "250"),
                   ("Damage per Quas", "5"), ("Attack range buffer", "125"),
                   ("Health regen", "24"), ("Root duration", "2s"), ("Max level (Scepter)", "10"),
                   ("Max Fervor stacks", "15"), ("Cannon volleys", "3")]
    # a header value's row has its icon before the name (96 "Cooldown 45" rows had no "s")
    iconed = tidy('<div class="vt-l"><img class="iab-ico" src="cooldown.png" alt="">Cooldown</div>'
                  '<div class="vt-v"><b class="iab-num">45</b></div>', "")
    assert '<b class="iab-num">45s</b>' in iconed and 'alt="">Cooldown</div>' in iconed
    # ... and comes lit already, a span (7.38 Tempest Double "Cooldown 100/90/80")
    lit = tidy('<div class="vt-l">Cooldown</div><div class="vt-v"><span class="iab-hl iab-hl-nerf iab-hl-num">100/90/80'
               '</span></div>' + cell("Base attack time reduction", "0.25") + cell("Magic damage amp", "-20%"), "")
    assert ">100/90/80s</span>" in lit and ">0.25s</b>" in lit and ">20%</b>" in lit
    hinted = tidy('<div class="vt-l">Cooldown</div><div class="vt-v"><span class="iab-hl iab-hl-buff iab-hl-num"><span '
                  'class="iab-hint abil-ico-hint" data-t="&lt;b&gt;-40%&lt;/b&gt;">60/55/50</span></span></div>', "")
    assert '&lt;/b&gt;">60/55/50s</span></span>' in hinted
    # a plain name renamed only on its card ("Count" of Skeleton Walk's archers); Quas, Strength capitalised; a
    # lifesteal's %, an angle's degree; a slow written "3 / -6 / -9%"
    more = tidy(cell("Count", "6") + cell("Damage per quas", "25") + cell("Cast range per strength", "20%")
                + cell("Lifesteal", "12/16") + cell("Vision cone angle", "90") + cell("Slow", "3 / -6 / -9%")
                + cell("Magic resist reduction", "17%"), "Summons a row of Burning Skeleton Archers")
    got = re.findall(r'<div class="vt-l">([^<]*)</div><div class="vt-v"><b class="iab-num">([^<]*)</b>', more)
    assert got == [("Archers", "6"), ("Damage per Quas", "25"), ("Cast range per Strength", "20%"),
                   ("Lifesteal", "12/16%"), ("Vision cone angle", "90°"), ("Slow", "3/6/9%"),
                   ("Magic resistance reduction", "17%")]
    assert tidy(cell("Count", "6"), "Summons wolves") == cell("Count", "6")


def test_a_change_by_a_number_takes_the_way_of_its_verb(no_names):
    """"Reduces cooldown by 1s" is −1s, not +1s (7.41 Fireblast); "increases damage by 10, radius by 175" stays +."""
    num = lambda v: f'<b class="iab-num">{v}</b>'
    assert dict(_said(f"Reduces cooldown by {num('1s')}.")) == {"Cooldown": '<b class="iab-num">−1s</b>'}
    assert dict(_said(f"Increases damage by {num(10)}, radius by {num(175)}.")) == {
        "Damage": '<b class="iab-num">+10</b>', "Radius": '<b class="iab-num">+175</b>'}
    assert dict(_said(f"Increases damage reduction by {num('5%')}.")) == {
        "Damage reduction": '<b class="iab-num">+5%</b>'}
