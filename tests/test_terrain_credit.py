"""The credit line under the Terrain slider (the owner 2026-10-01): the idea comes from Leamare's and devilesk's
interactive maps, linked to their repositories; the pictures, the data and the rest are ours — and whatever on a
page is still borrowed is named, so the line never claims more than is true."""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
import builders.terrain as terrain  # noqa: E402


def test_both_names_link_to_their_repositories():
    html = terrain._source_html("7.40", "7.41")
    assert '<a href="https://github.com/leamare/dota-interactive-map"' in html and ">Leamare</a>" in html
    assert '<a href="https://github.com/devilesk/dota-interactive-map"' in html and ">devilesk</a>" in html
    assert "our own work" in html


def test_a_page_whose_parts_are_all_ours_names_nothing_borrowed(monkeypatch):
    monkeypatch.setattr(terrain, "_own_pictures", lambda: {"7.40", "7.41"})
    monkeypatch.setattr(terrain, "_own_entities", lambda v: True)
    assert "For now" not in terrain._source_html("7.40", "7.41")


def test_borrowed_parts_are_named(monkeypatch):
    monkeypatch.setattr(terrain, "_own_pictures", lambda: {"7.41"})
    monkeypatch.setattr(terrain, "_own_entities", lambda v: v == "7.41")
    html = terrain._source_html("7.40", "7.41")
    assert "For now the 7.40 picture and the 7.40 map objects are Leamare’s" in html


def test_the_7_41_picture_is_ours():
    assert "7.41" in terrain._own_pictures()
