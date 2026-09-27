"""Owner 2026-09-27: an item whose ability changed gets an abilities before -> after card (generator pass
tools/item_ability_text.insert_cards); a duplicate description row hides and its (?) moves into the card."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import item_ability_text as iat  # noqa: E402
from patch import elements as el  # noqa: E402
from patch.state import _State  # noqa: E402

BLOCK = ['    W(item_header("Orb of Venom"))',
         '    W(ul_open())',
         '    W(li("Poison Attack now has a 9s cooldown", t("NEW")))',
         '    W(li("Poison Attack no longer slows movement speed", t("DEL")))',
         '    W(ul_close())']
TEXTS = {"7.37e": ["Passive: Poison Attack. Poisons the target, dealing 2 magical damage per second and slowing movement."],
         "7.38": ["Passive: Poison Attack. Poisons the target, dealing 10 magical damage per second. Cooldown: 9s"]}


def test_a_changed_item_ability_gets_a_card(monkeypatch):
    monkeypatch.setattr(iat, "item_abilities", lambda slug, v: TEXTS.get(v))
    out = iat.insert_cards(BLOCK, "7.38", "7.37e", {"Orb of Venom": "orb_of_venom"})
    joined = "\n".join(out)
    assert "W(item_abilities_change(" in joined and joined.index("item_abilities_change") < joined.index("ul_open")
    assert iat.insert_cards(out, "7.38", "7.37e", {"Orb of Venom": "orb_of_venom"}) == out      # idempotent


def test_only_numbers_changed_or_a_new_item_gets_no_card(monkeypatch):
    monkeypatch.setattr(iat, "item_abilities", lambda slug, v: ["Passive: X. Deals %s damage." % (2 if v == "a" else 5)])
    assert iat.insert_cards(BLOCK, "b", "a", {"Orb of Venom": "orb_of_venom"}) == BLOCK
    new_item = [BLOCK[0].replace('"))', '", new="New Tier 1 Artifact"))')] + BLOCK[1:]
    monkeypatch.setattr(iat, "item_abilities", lambda slug, v: TEXTS.get({"b": "7.38", "a": "7.37e"}[v]))
    assert iat.insert_cards(new_item, "b", "a", {"Orb of Venom": "orb_of_venom"}) == new_item


def test_a_duplicate_description_row_hides_and_keeps_its_note():
    saved = (_State.current_entity_key, _State.current_patch_version, getattr(_State, "iab_card", None))
    try:
        _State.current_entity_key, _State.current_patch_version = "item|x", "7.38"
        el.item_abilities_change(old=["Toggle: Old. Something."], new=["Passive: Phantom Critical. Grants a 30% chance."])
        tip = "<!--INLINETIP--><span>note</span><!--/INLINETIP-->"
        assert el._iab_shown_in_card("Passive: Phantom Critical. Grants a 30% chance", tip)
        assert el._IAB_NOTES["item|x|7.38|phantom critical"] == "<span>note</span>"
        assert not el._iab_shown_in_card("Passive: Other Thing. Text", "")
    finally:
        _State.current_entity_key, _State.current_patch_version, _State.iab_card = saved
