"""Nothl Projection (Dazzle's new ultimate in 7.38) is an open ability card, not a row with a hidden tooltip (owner 2026-10-21)."""
from pathlib import Path


def test_nothl_projection_is_an_open_card():
    src = (Path(__file__).resolve().parents[1] / "content" / "p738.py").read_text(encoding="utf-8")
    start = src.index('name="Nothl Projection"')
    assert src.rfind("W(ability_change(", 0, start) > src.rfind('W(hero_header("Dazzle"))')
    assert 'W(ability("Nothl Projection"' not in src
    assert "aghs_shard_line(" in src[start:start + 3000]
