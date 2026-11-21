"""tools/notes_refresh.py: a line Valve changed, added or removed after the release is found, with its hero / item.
Owner 2026-11-21: 7.42 Kez "to 40/80/120" was Valve's first wording, today's notes say "to 50/100/150"."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.notes_refresh import diff  # noqa: E402


def _feed(kez, nyx=True, brew=False):
    heroes = [{"hero_id": 145, "abilities": [{"ability_id": 1501, "ability_notes": [{"note": kez}]}]}]
    if nyx:
        heroes.append({"hero_id": 88, "hero_notes": [{"note": "Base Health Regen decreased by 1.0"}]})
    if brew:
        heroes.append({"hero_id": 78, "abilities": [{"ability_id": 1681, "ability_notes": [{"note": "Added to HUD"}]}]})
    return {"heroes": heroes, "general_notes": [{"title": "Global Mechanics", "generic": [{"note": "Leashes …"}]}]}


def test_changed_added_and_removed_lines_are_found():
    stored = _feed("Base Damage increased from 40/70/100 to 40/80/120")
    live = _feed("Base Damage increased from 40/70/100 to 50/100/150", nyx=False, brew=True)
    removed, added = diff(stored, live)
    assert [t for t, _ in removed] == ["Base Damage increased from 40/70/100 to 40/80/120",
                                       "Base Health Regen decreased by 1.0"]
    assert [t for t, _ in added] == ["Base Damage increased from 40/70/100 to 50/100/150", "Added to HUD"]


def test_the_same_notes_give_no_difference():
    assert diff(_feed("x"), _feed("x")) == ([], [])
    # 7.41c: Valve now writes the ability first ("Drums of Slom: …") — the same note
    assert diff(_feed("Drum Hit Damage decreased from 80 to 70"),
                _feed("Drums of Slom: Drum Hit Damage decreased from 80 to 70")) == ([], [])
