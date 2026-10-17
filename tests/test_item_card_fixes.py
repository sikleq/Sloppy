"""Item card fixes (owner 2026-10-16, 7.41): 5+ level badges as "first … last" (Dagon), a "no longer …" row colours
the one word the old text lost (Refresher Shard "items"), a value kept for one kind of unit is added to the new
description (Crimson Guard "45 … on ranged heroes"), the ability a row starts with wins."""
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from patch import elements as e  # noqa: E402
from patch.badges import RANGE_FROM_LEVELS, b  # noqa: E402


def test_five_levels_show_first_and_last_only():
    out = b([700, 750, 800, 850, 900], 640)
    assert out.count('class="badge ') == 2 and "badge-range" in out
    assert "-9%" in out and "-29%" in out and "-20%" not in out
    assert 'data-overall="nerf"' in out
    four = b([10, 20, 30, 40], [12, 22, 32, 42])                      # 4 levels (heroes): every level stays
    assert four.count('class="badge ') == 4 and RANGE_FROM_LEVELS == 5


def test_the_ability_a_row_starts_with_wins():
    assert e._iab_row_ability("guard base damage block rescaled from 70", None, {"guard", "damage block"}) == "guard"
    assert e._iab_row_ability("damage block chance increased", None, {"guard", "damage block"}) == "damage block"


def test_header_levels_show_level_one_dotted_and_every_level_on_hover():
    # owner 2026-10-17, Dagon 7.41: "the level-1 value in the header, dotted — the popup has all levels"; a change at
    # one level is coloured in that popup
    ico = '<img class="iab-ico" src="../icons/ui/ability/cooldown.png" alt="">'
    chip = f'<span class="iab-m">{ico}27/24/21/18/15</span>'
    out = e._iab_compact_levels(chip)
    assert 'data-tooltip="Levels 1–5: 27 / 24 / 21 / 18 / 15">27</span>' in out and "iab-hint" in out
    pct = e._iab_compact_levels(f'<span class="iab-m">{ico}10/20/30/40/50%</span>')
    assert '">10%</span>' in pct                                                 # the unit of the last level
    four = f'<span class="iab-m">{ico}12/10/8/6</span>'
    assert e._iab_compact_levels(four) == four
    marked = e._iab_chip_mark(ico, "27/24/21/18/12", "27/24/21/18/15", "buff", "")
    assert 'class="iab-m iab-buff"' in marked and '">27</span></span>' in marked
    assert "18 / &lt;span class=&quot;iab-lv iab-buff&quot;&gt;12&lt;/span&gt;" in marked
    three = e._iab_chip_mark(ico, "12/10/6", "12/10/8", "buff", "")
    assert three.endswith('12/10/<span class="iab-lv iab-buff">6</span></span>')
    assert 'class="iab-m iab-nerf"' in e._iab_chip_mark(ico, "640", "700/750/800/850/900", "nerf", "")
    assert e._tone_cls('<span class="badge nerf3 rng-start">-9%</span>') == "badge nerf3 tone"


def _page(ver):
    p = os.path.join(ROOT, "dist", "patches", f"{ver}.html")
    if not os.path.exists(p):
        pytest.skip("site not built")
    return open(p, encoding="utf-8").read()


def _block(html, item):
    i = html.index(f'id="dyn-item-{item}"')
    return html[i:html.find('class="entity ', i + 50)]


def test_components_keep_the_old_sides_order():
    # owner 2026-10-17: Guardian Greaves 7.41 "1775 + 1400 → 1500 + 1775" read as a cheaper Mekansm
    assert e._in_old_order([("Mekansm", 1775), ("Arcane Boots", 1400)],
                           [("Arcane Boots", 1500), ("Mekansm", 1775), ("Chainmail", 500)]) == \
        [("Mekansm", 1775), ("Arcane Boots", 1500), ("Chainmail", 500)]
    seg = re.sub(r"<[^>]+>", " ", _block(_page("7.41"), "guardian-greaves"))
    assert re.search(r"1775\s+\+\s+1400\s+\+\s+1125\s+=\s+4300\s+→\s+1775\s+\+\s+1500\s+\+\s+1175", seg)


def test_two_changes_of_an_ability_bring_its_card():
    # owner 2026-10-17: Ash Legion Shield 7.41 "2 changes of the ability — shouldn't it be a card?"
    seg = re.sub(r'</?b(?: class="iab-num")?>', "", _block(_page("7.41"), "ash-legion-shield"))
    assert "iab-change" in seg and '<span class="iab-name">Shield Wall</span>' in seg
    shown = [li for li in seg.split("<li")[1:] if "iab-covered" not in li.split(">", 1)[0]]
    assert not shown                                                      # both rows went into the card


def test_an_item_only_taken_out_says_so_in_its_label():
    # owner 2026-10-17: "Neutral Item cycled out" in the DEL colour where "Returning Tier 2 Artifact" stands, the tag
    # hidden for the filters
    seg = _block(_page("7.39"), "pig-pole")
    assert '<span class="entity-removed-type">Neutral Item cycled out</span>' in seg and 'data-tag="del' in seg
    assert '<span class="entity-removed-type">Item removed</span>' in _block(_page("7.41"), "cornucopia")
    css = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()
    assert ".entity-block.is-removed ul.changes { display: none !important; }" in css
    assert "html.cb-mode .entity-name .entity-removed-type" in css


def test_refresher_shard_colours_the_lost_word():
    seg = _block(_page("7.41"), "refresher-shard")
    assert '<span class="iab-hl iab-hl-del" data-tag="del">items</span>' in seg


def test_dagon_header_shows_level_one_values_on_both_sides():
    seg = _block(_page("7.41"), "dagon")
    card = seg[seg.index("iab-change"):]
    assert card.count('data-tooltip="Levels 1–5: 120 / 140 / 160 / 180 / 200">120</span>') == 2   # mana, both sides
    assert card.count('data-tooltip="Levels 1–5: 27 / 24 / 21 / 18 / 15">27</span>') == 2         # cooldown
    assert 'data-tooltip="Levels 1–5: 700 / 750 / 800 / 850 / 900">700</span>' in card              # old cast range
    assert not re.search(r'class="iab-m[^"]*"><img[^>]*>\d+(?:/\d+){4}<', card)    # no header shows the full list


def test_rows_the_card_shows_go_into_it():
    # owner 2026-10-17, 7.41: "переведи в карточки" — the card colours the text, the row is hidden (still counted)
    html = _page("7.41")
    expect = {
        "drum-of-endurance": ['data-tag="new">and 2.5 health regeneration</span>',
                              'data-tag="nerf">Shares a cooldown with Boots of Bearing</span>.'],
        "boots-of-bearing": ['data-tag="nerf">Shares a cooldown with Drum of Endurance</span>.'],
        "pipe-of-insight": ['data-tag="del">2.5 health regeneration</span>'],
        "mask-of-madness": ['data-tag="new">and 30% slow resistance</span>',
                            'data-tag="rework">8% / 12% movement speed (ranged/melee)</span>'],
        "harpoon": ['data-tag="new">Targeting a tree always pulls you all the way to that tree</span>',
                    'data-tag="new">Destroys all trees on the way</span>.'],
        "weighted-dice": ['data-tag="new">Increases your base damage maximum by 6</span>'],
    }
    for item, spans in expect.items():
        seg = re.sub(r'</?b(?: class="iab-num")?>', "", _block(html, item))        # the card's numbers are bold
        for span in spans:
            assert span in seg, (item, span)
        shown = [li for li in seg.split("<li")[1:] if "iab-covered" not in li.split(">", 1)[0]]
        assert not any(w in li for li in shown for w in ("Health Regen", "health regen", "shares cooldown",
                                                         "Slow Resistance", "Movement Speed changed",
                                                         "target trees", "max base damage")), item


def test_a_card_shows_only_the_abilities_that_changed():
    # owner 2026-10-17: "Harpoon — why the active and the passive, when only Draw Forth changed"; Mask of Madness too
    html = _page("7.41")
    for item, gone, kept in (("harpoon", "Echo Strike", "Draw Forth"), ("mask-of-madness", "Lifesteal", "Berserk"),
                             ("crimson-guard", "Damage Block", "Guard")):
        card = _block(html, item).split("iab-change", 1)[1]
        assert f'<span class="iab-name">{gone}</span>' not in card and f'<span class="iab-name">{kept}</span>' in card
    drum = _block(html, "drum-of-endurance").split("iab-change", 1)[1]
    assert '<span class="iab-name">Endurance</span>' in drum            # same text, but a row added a sentence


def test_what_an_old_tooltip_never_said_goes_after_it_in_red():
    # owner 2026-10-17, Pipe of Insight 7.41: the Barrier row into the card; Dagon's "instantly kills" the same way
    html = _page("7.41")
    assert ('data-tag="del">Affects units that have been affected by Barrier within Pipe of Insight\'s cooldown</span>'
            in _block(html, "pipe-of-insight"))
    assert 'data-tag="del">Instantly kills non-ancient creeps</span>' in _block(html, "dagon")


def test_refresher_orb_has_its_stats_card_cooldown_and_marked_mana_cost():
    # owner 2026-10-17: "no stats card, no cooldown in the header, the new mana cost not marked"
    seg = _block(_page("7.41"), "refresher-orb")
    assert re.search(r'class="properties-change(?! iab-change)', seg) and "+14 Health Regen" in seg
    new = seg.split("pane-new", 2)[-1]
    assert re.search(r'class="iab-m iab-buff[^"]*">\s*<img[^>]*manacost\.png[^>]*>(?:<[^>]+>)*325<', new)
    assert re.search(r'class="iab-m iab-buff[^"]*">\s*<img[^>]*cooldown\.png[^>]*>', new)
    assert "180/190/200/210" in seg.split("pane-old", 2)[-1]
    shown = [li for li in seg.split("<li")[1:] if "iab-covered" not in li.split(">", 1)[0]]
    assert not shown


def test_owner_tags_of_7_41_rows():
    html = _page("7.41")
    for text, tag in (("has switched — now begins in the Bottom Chasm", "rework"),
                      ("has switched — now begins in the Top Pit", "rework"),
                      ("Transmute no longer prevents camp-clearing", "misc"), ("Burn toggling no longer breaks", "qol")):
        li = html[html.rfind("<li", 0, html.index(text)):html.index(text)]
        assert f'data-tag="{tag}"' in li, text


def test_enchant_chips_hover_the_patch_own_numbers():
    # owner 2026-10-17, 7.41: the chips' hover took one table for every patch (Vital +2.25 against the row's +2)
    assert e._enchant_desc("Vital", "7.41") == {1: ["+2 Health Regen"]}
    assert e._enchant_desc("Alert", "7.41")[4] == ["+31 Attack Speed", "+300 Bonus Night Vision", "+100 Attack Range"]
    assert e._enchant_desc("Vital", "6.00") == e._ENCHANT_DESC["Vital"]             # no data: the table
    html = _page("7.41")
    assert 'alt="Vital"' in html and 'data-tooltip="+2 Health Regen"' in html and "+2.25 Health Regen" not in html


def test_every_patch_with_enchant_boxes_has_its_own_numbers():
    # without its entry a patch's chips would quietly fall back to the shared table (scripts/gen/enchant_values.py)
    import glob
    import json
    with open(os.path.join(ROOT, "data", "rules", "enchant_values.json"), encoding="utf-8") as f:
        have = set(json.load(f))
    for path in glob.glob(os.path.join(ROOT, "content", "p*.py")):
        if "enchant_tier_box(" in open(path, encoding="utf-8").read():
            code = os.path.basename(path)[1:-3]
            ver = f"{code[0]}.{code[1:3]}{code[3:]}"
            assert ver in have, f"run: python scripts/gen/enchant_values.py {ver}"


def test_crimson_guard_gets_the_ranged_value_in_the_card():
    seg = _block(_page("7.41"), "crimson-guard")
    assert "base damage block on ranged heroes</span>" in seg and '<b class="iab-num">45</b>' in seg
