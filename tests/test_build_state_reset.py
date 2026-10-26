"""One reset for the build state (audit 2026-10-26): save_html leaves nothing of a page for the next one, and an
Aghanim's card still to draw never moves to the next hero, item or block."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patch import aghs_text as at  # noqa: E402
from patch import elements as el  # noqa: E402
from patch import state as st  # noqa: E402
from patch.state import _State, reset_build_state, reset_page_state  # noqa: E402

PAGE_CACHES = ("_HS_CARDS", "_GRANTED_CARDS", "_AGHS_SHOWN", "_CARD_CONFIRMED", "_IAB_NOTES", "_IAB_CARDS",
               "_IAB_MARKS", "_IAB_HL", "_COST_CARDS", "_COST_MARKS")


def _dirty_everything():
    for key in st._DEFAULTS:
        cur = getattr(_State, key)
        if isinstance(cur, set):
            cur.add("left over")
        elif isinstance(cur, dict):
            cur["left over"] = 1
        elif isinstance(cur, list):
            cur.append("left over")
        else:
            setattr(_State, key, "left over")
    st.state.block_open = "instance left over"
    for name in PAGE_CACHES:
        cache = getattr(el, name)
        cache.add("left over") if isinstance(cache, set) else cache.__setitem__("left over", 1)
    el._CARD_SEQ[0] = 41


def test_page_reset_brings_every_field_and_cache_back():
    _dirty_everything()
    reset_page_state()
    for key, default in st._DEFAULTS.items():
        if key in st._BUILD_TOTALS:
            assert "left over" in getattr(_State, key), f"{key} is a build total: the next page adds to it"
        else:
            assert getattr(st.state, key) == default, f"_State.{key} survived the page"
    for name in PAGE_CACHES:
        assert not getattr(el, name), f"{name} survived the page"
    assert el._CARD_SEQ == [0]


def test_build_reset_clears_the_totals_too():
    _dirty_everything()
    reset_build_state()
    assert not _State.dynamics and not _State.ability_icons


def test_every_card_cache_is_registered():
    registered = {id(c) for c, _ in st._PAGE_CACHES}
    for name in PAGE_CACHES + ("_CARD_SEQ",):
        assert id(getattr(el, name)) in registered, name


def _pending_card(monkeypatch, hero="centaur", slug="centaur_horsepower"):
    """An ability block whose old -> new Aghanim's card is still to draw (7.41 Centaur: the block has no rows)."""
    monkeypatch.setattr(at, "holders", lambda h, kind, v: ["centaur_stampede"] if kind == "scepter" and v == "7.40c"
                        else ([slug] if kind == "scepter" else []))
    monkeypatch.setattr(at, "aghs_text", lambda s, kind, v: {"centaur_stampede": "Old upgrade.",
                                                             slug: "New upgrade."}.get(s) if kind == "scepter" else None)
    monkeypatch.setattr(at, "ability_name", lambda s, v: s.title())
    _State.current_patch_version = "7.41"
    _State.aghs_part_slug = (slug, hero)


@pytest.mark.parametrize("header", [lambda: el.hero_header("Chaos Knight"),
                                    lambda: el.item_header("Blink Dagger"),
                                    lambda: el.plain_header("Tormentor")])
def test_pending_card_is_drawn_before_the_next_block_not_inside_it(monkeypatch, header):
    _pending_card(monkeypatch)
    out = header()
    assert "New upgrade." in out, "the card of the closed ability must be drawn"
    assert out.index("New upgrade.") < out.index('class="entity-block'), "the card moved into the next block"
    assert _State.aghs_part_slug is None


def test_pending_card_does_not_reach_the_next_page(monkeypatch):
    _pending_card(monkeypatch)
    reset_page_state()
    assert _State.aghs_part_slug is None
    _State.current_patch_version = "7.41"
    assert el.ul_close() == "</ul>"
