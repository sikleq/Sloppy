"""A facet is drawn as its own patch had it: the colours and icons come from the game's files of that patch (2026-11-05)."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from patch import game_files
from patch.badges import FACETS, _facet_history, facet_look
from patch.state import _State

ROOT = Path(__file__).resolve().parent.parent


def test_the_look_follows_the_patch():
    assert facet_look("batrider_arsonist", "7.38")[1:] == ("Red0", "siege")
    assert facet_look("batrider_arsonist", "7.39")[1:] == ("Yellow1", "damage")
    assert facet_look("pudge_fresh_meat", "7.37e")[1] == "Green3"
    assert facet_look("pudge_fresh_meat", "7.38")[1] == "Red0"
    assert facet_look("chen_frog_convert", "7.38")[2] == "bubbles"


def test_a_patch_after_the_last_change_keeps_the_last_look():
    assert facet_look("batrider_arsonist", "7.41f")[1] == "Yellow1"


def test_no_version_takes_the_page_s_patch(monkeypatch):
    monkeypatch.setattr(_State, "current_patch_version", "7.38")
    assert facet_look("batrider_arsonist")[1] == "Red0"


def test_a_facet_the_files_do_not_have_keeps_the_registry():
    assert "abaddon_the_quickening" not in _facet_history()
    assert facet_look("abaddon_the_quickening", "7.38")[:2] == FACETS["abaddon_the_quickening"]


def test_every_icon_of_the_history_is_on_disk():
    for slug, runs in _facet_history().items():
        for _first, _colour, icon in runs:
            assert (ROOT / "icons" / "facets" / f"{icon}.png").exists(), (slug, icon)


def test_the_registry_colour_is_one_the_game_has_used():
    wrong = [s for s, (_n, c) in FACETS.items() if s in _facet_history() and c not in {r[1] for r in _facet_history()[s]}]
    assert wrong == []


@pytest.mark.skipif("7.38" not in game_files.versions(), reason="no game files")
def test_the_history_is_up_to_date_with_the_game_files():
    run = subprocess.run([sys.executable, os.path.join("scripts", "gen", "gen_facet_history.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout
