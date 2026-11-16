"""Hero Changes Min / Max rows show the hero as a portrait alone (owner 2026-11-16)."""
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / "builders" / "entity_changes.py").read_text(encoding="utf-8")


def test_min_max_hero_cell_has_no_name_text():
    who = SRC[SRC.index("    def who(w, val):"):SRC.index("    def row(label, cells):")]
    assert "<span>" not in who
    assert 'alt="{_esc(w["name"])}"' in who
