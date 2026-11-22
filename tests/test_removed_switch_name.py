"""Owner 2026-11-22: "Show deleted везде переименовать по аналогии" — the switch that shows what left the game is called
"Removed" on every page, as Neutral Stats' button."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_builder_names_the_switch_deleted():
    for name in ("dyn_matrix_common.py", "entity_changes.py", "items_dyn.py", "creeps.py", "item_potency.py"):
        src = (ROOT / "builders" / name).read_text(encoding="utf-8")
        assert ">Show deleted" not in src and "'Deleted'" not in src and "<strong>Deleted</strong>" not in src, name
