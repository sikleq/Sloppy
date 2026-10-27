"""_dynamics.json is the same bytes whatever order the pages filled it in (audit 2026-10-26: two builds of one commit
gave the same values in a different key order, so dist/ could not be compared byte for byte)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patch.rosters import write_dynamics  # noqa: E402


def _payload(keys):
    ents = {k: {"name": k, "kind": "item", "patches": {"7.41": {"buff": 1}, "7.40": {"nerf": 2}}} for k in keys}
    return {"patches": [{"version": "7.41"}, {"version": "7.40"}], "entities": ents, "heroes": [{"name": "B"},
            {"name": "A"}], "items": [], "item_categories": ["Consumables", "Attributes"]}


def test_record_order_does_not_change_the_file(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    write_dynamics(a, _payload(["item|z", "item|a", "hero|m"]))
    write_dynamics(b, _payload(["hero|m", "item|a", "item|z"]))
    assert a.read_bytes() == b.read_bytes()


def test_arrays_keep_their_order(tmp_path):
    out = tmp_path / "d.json"
    write_dynamics(out, _payload(["item|a"]))
    text = out.read_text(encoding="utf-8")
    assert text.index('"B"') < text.index('"A"') and text.index('"Consumables"') < text.index('"Attributes"')
