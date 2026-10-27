"""Card fixes of 2026-10-26 (owner, 7.41 / 7.38 proofreading): "Shares level with X" and "granted by Aghanim's X" go to
the card's header, "Has only one level" is never said; a granted ability's card is an ability card from the game files
(7.38 Demonic Cleanse, 7.41 Warp Flare); an ability's own text lists no Aghanim's-only value; Aghanim's cards keep an
even inner padding; an icon missing on the CDN is looked for in the game files."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patch import elements as el  # noqa: E402
from patch.state import _State  # noqa: E402
from patch import cards_ability_change  # noqa: E402
from patch import cards_aghs  # noqa: E402
from patch import cards_item_abilities  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _title(head):
    return re.sub(r"<[^>]+>", "", re.search(r'<span class="iab-title">(.*?)</span><span class="iab-meta">', head).group(1))


def test_shares_level_goes_to_the_header():
    head, body = cards_item_abilities._pane_parts([el.hl("Shares level with Kinetic Field", "del") + ".", "Creates a wall."],
                                {"kind": "Active"})
    assert _title(head) == "Active – shares level with Kinetic Field"
    assert "Shares level" not in body and "Creates a wall." in body


def test_only_one_level_is_never_said_and_granted_is_in_the_header():
    head, body = cards_item_abilities._pane_parts([el.hl("Has only one level", "new") + ".", "Creates a wall."], {"kind": "Active"},
                                granted="shard")
    assert _title(head) == "Active – granted by Aghanim's Shard"
    assert "one level" not in body


def test_granted_and_shares_level_together():
    head, _ = cards_item_abilities._pane_parts(["Shares level with Demonic Purge.", "Cleanses."], {"kind": "Active"}, granted="shard")
    assert _title(head) == "Active – granted by Aghanim's Shard, shares level with Demonic Purge"


def test_kinetic_fence_card_says_it_in_the_headers_not_the_summary():
    _State.current_patch_version = "7.41"
    try:
        html = cards_ability_change.ability_change(
            old=dict(name="Kinetic Fence", slug="disruptor_kinetic_fence",
                     desc=[el.hl("Shares level with Kinetic Field", "del") + ".", "Wall."]),
            new=dict(name="Kinetic Fence", slug="disruptor_kinetic_fence",
                     desc=["Granted by Aghanim's Shard. " + el.hl("Has only one level", "new") + ".", "Wall."]),
            summary="Ability reworked.", tag="rework")
    finally:
        el._close_ability_block()
        _State.current_patch_version = None
    titles = [_title(h) for h in re.findall(r'<div class="iab-head pane-head">.*?</div>', html)]
    assert titles == ["Active – shares level with Kinetic Field", "Active – granted by Aghanim's Shard"]
    assert "(Aghanim's Shard upgrade)" not in html and 'aghanim-marker shard' in html
    assert "one level" not in html


def test_shares_level_comes_from_the_game_files():
    assert cards_aghs._shares_level("shadow_demon_demonic_cleanse", "7.37e") == "Demonic Purge"
    assert cards_aghs._shares_level("shadow_demon_demonic_cleanse", "7.38") is None      # one level since 7.38


def test_game_ability_pair_colours_numbers_and_says_the_shared_level():
    old, new = cards_ability_change.game_ability_pair("shadow_demon_demonic_cleanse", "7.38")
    assert old[0] == "Shares level with Demonic Purge." and len(new) == 1
    assert "300/450/600" in old[-1] and "450" in new[-1]


def test_base_text_lists_no_aghanims_only_value():
    from patch.aghs_text import ability_text
    text = ability_text("shadow_demon_demonic_cleanse", "7.37e")
    assert "Max charges" not in text and "charge restore" not in text.lower()
    assert "Cleanse heal: 300/450/600." in text
    # the Scepter's own text still has them
    assert "Max charges: 2" in ability_text("shadow_demon_demonic_cleanse", "7.37e", kind="scepter")


def test_granted_card_is_an_ability_card_with_headers():
    _State.current_patch_version, _State.current_ability_slug = "7.41", "tinker_warp_grenade"
    _State.aghs_cards = []
    cards_aghs._GRANTED_CARDS.discard(("7.41", "tinker_warp_grenade"))
    try:
        assert cards_aghs._granted_card({"rework"})
        card = _State.aghs_cards[-1]
    finally:
        _State.aghs_cards, _State.card_meta = [], {}
        _State.current_patch_version = _State.current_ability_slug = None
    assert "Ability reworked.<span class=\"aghanim-marker shard\"></span>" in card
    titles = [_title(h) for h in re.findall(r'<div class="iab-head pane-head">.*?</div>', card)]
    assert titles == ["Active – granted by Aghanim's Shard"] * 2
    assert "Grants this ability" not in card and "teleported further the closer" in card


def test_aghanims_cards_keep_even_padding_inside_an_ability_change_block():
    css = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()
    rule = re.search(r"\.ability-change-block \.ability-change\.unified-panes\.aghs-change > \.ability-change-pane"
                     r"\s*\{([^}]*)\}", css)
    assert rule and "padding: 10px 14px" in rule.group(1) and "--pt: 10px" in rule.group(1)


def test_removed_items_grey_aghs_panes_on_top_and_a_gone_enchant_value_struck():
    css = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()
    # an item taken out of the game: icon and name greyed (the label and the patch strip keep their colours)
    assert re.search(r"\.entity-block\.is-removed \.entity-icon img \{[^}]*grayscale", css)
    assert re.search(r"\.entity-block\.is-removed \.entity-name > \.entity-link", css)
    # Aghanim's card panes top-anchored: the caption stays by the card (7.41 Techies)
    rule = re.search(r"\.ability-change-block \.ability-change\.unified-panes\.aghs-change > \.ability-change-pane"
                     r"\s*\{([^}]*)\}", css)
    assert "align-self: start" in rule.group(1)
    # a bonus an enchantment lost: its old value struck, no "→ —" (7.41 Mystical Cast Range)
    assert '" → —"' not in css
    assert re.search(r"\.ench-tiers\.ench-change \.iab-lv\.iab-del \{[^}]*line-through", css)
    # ... and its name struck too, no cross before it; "was" and "now" one size (owner, the same day, 7.39 Alert)
    assert not re.search(r"\.ench-gone::before \{[^}]*content", css)
    assert re.search(r"\.ench-change \.ench-stat\.ench-gone \{[^}]*line-through", css)
    assert re.search(r"\.ench-change \.ench-was \{[^}]*font-size: inherit", css)
    # the Aghanim's card arrow stands at the old pane's middle (7.41 Techies)
    js = open(os.path.join(ROOT, "src", "scripts.js"), encoding="utf-8").read()
    assert ".ability-change.aghs-change" in js and "arrow.style.marginTop" in js


def test_older_enchant_tables_take_the_patchs_own_labels_and_tiers():
    import json
    have = json.load(open(os.path.join(ROOT, "data", "rules", "enchant_tables.json"), encoding="utf-8"))
    mystical = {s["label"]: s for s in have["7.39"]["Mystical"]["stats"]}
    # 7.39's third value is Cast Range (today's text says Mana Cost/Loss Reduction there)
    assert mystical["Cast Range"]["new"]["4"] == "+100" and "Mana Cost/Loss Reduction" not in mystical
    assert have["7.39"]["Vampiric"]["tiers_new"] == [2, 3, 4]        # from neutral_items.txt, no tier boxes on the page


def test_icons_missing_on_the_cdn_are_looked_for_in_the_game_files():
    src = open(os.path.join(ROOT, "scripts", "fetch", "fetch_icons.py"), encoding="utf-8").read()
    assert "AbilityTextureName" in src and "from_vpk" in src
    from patch.known_exceptions import KNOWN_INNATE_NO_CDN_ICON
    # 7.41 Squee's Scope draws Stasis Trap's icon (KV AbilityTextureName): found, not an exception
    assert "techies_squees_scope" not in KNOWN_INNATE_NO_CDN_ICON
    assert os.path.exists(os.path.join(ROOT, "icons", "abilities", "techies_squees_scope.png"))
    # PNG_RGBA8888 (16): spell icons are PNG files inside; read, not imported — CI has no numpy
    vpk = open(os.path.join(ROOT, "scripts", "fetch", "extract_vpk_icons.py"), encoding="utf-8").read()
    assert re.search(r"^EMBEDDED = \{[^}]*\b16\b", vpk, re.M)
