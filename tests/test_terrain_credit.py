"""The credit line under the Terrain slider (the owner 2026-10-01): the idea comes from Leamare's and devilesk's
interactive maps, linked to their repositories, in as few words as possible; a version whose map is still
borrowed is named, so the line never claims more than is true."""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
import builders.terrain as terrain  # noqa: E402


def test_both_names_link_to_their_repositories():
    html = terrain._source_html("7.40", "7.41")
    assert '<a href="https://github.com/leamare/dota-interactive-map"' in html and ">Leamare</a>" in html
    assert '<a href="https://github.com/devilesk/dota-interactive-map"' in html and ">devilesk</a>" in html
    assert html.count("<a ") == 2 and len(html) < 400                # kept to the minimum (the owner)


def test_a_page_whose_parts_are_all_ours_names_nothing_borrowed(monkeypatch):
    monkeypatch.setattr(terrain, "_own_pictures", lambda: {"7.40", "7.41"})
    monkeypatch.setattr(terrain, "_own_entities", lambda v: True)
    assert "for now" not in terrain._source_html("7.40", "7.41")


def test_borrowed_parts_are_named(monkeypatch):
    monkeypatch.setattr(terrain, "_own_pictures", lambda: {"7.41"})
    monkeypatch.setattr(terrain, "_own_entities", lambda v: v == "7.41")
    html = terrain._source_html("7.40", "7.41")
    assert "7.40: Leamare’s map for now" in html and "7.41:" not in html


def test_the_7_41_picture_is_ours():
    assert "7.41" in terrain._own_pictures()
