"""One Terrain page per patch whose map file changed (the owner 2026-10-02: "the difference between the letter
patches has to be shown too, not just two major versions" — 7.39b's own changes were folded into 7.39 -> 7.40)."""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
import builders.map_versions as mv  # noqa: E402
import builders.terrain as terrain  # noqa: E402


def test_a_step_is_a_patch_whose_map_file_changed():
    pm = {"7.40": "a", "7.40b": "a", "7.40c": "b", "7.41": "c"}
    got = mv.steps(pm, {"7.40", "7.40c", "7.41"})
    assert got == [mv.Step("7.40c", "7.40b", "7.40", "7.40c"), mv.Step("7.41", "7.40c", "7.40c", "7.41")]


def test_a_step_needs_both_pictures():
    assert mv.steps({"7.37e": "x", "7.38": "y"}, {"7.38"}) == []


def test_the_site_has_every_letter_patch_from_738b_to_741f():
    got = [s.patch for s in mv.steps()]
    assert got == ["7.38b", "7.38c", "7.39", "7.39b", "7.39c", "7.39d", "7.39e", "7.40", "7.40c",
                   "7.41", "7.41a", "7.41c", "7.41d", "7.41e", "7.41f"]
    same = mv.same_file_as()
    assert same["7.40b"] == "7.40" and same["7.41b"] == "7.41a"


def test_every_step_has_its_pictures_objects_and_diff():
    for s in mv.steps():
        for pic in (s.old_pic, s.new_pic):
            assert os.path.exists(os.path.join(_ROOT, "icons", "maps", f"map_{pic}.webp")), pic
            assert os.path.exists(os.path.join(_ROOT, "data", "map", f"mapdata_{mv.code(pic)}.json")), pic
        with open(os.path.join(_ROOT, "data", f"terrain_diff_{s.patch}.json"), encoding="utf-8") as f:
            d = json.load(f)
        assert (d["oldVer"], d["newVer"]) == (s.old_pic, s.new_pic)


def test_what_moved_is_read_off_the_diff():
    diff = {"treesOld": [[0, 0], [1, 1], [2, 2]], "treesNew": [[0, 0], [5, 5]],
            "campsOld": [{"x": 0, "y": 0, "tier": 1}, {"x": 9, "y": 9, "tier": 2}],
            "campsNew": [{"x": 0, "y": 0, "tier": 2}, {"x": 8, "y": 9, "tier": 2}],
            "entities": {"watchers": {"old": [[1, 1]], "new": [[1, 1], [2, 2]]},
                         "towers": {"old": [[3, 3]], "new": [[3, 3]]}}}
    assert terrain._moved_summary(diff) == ["trees +1 −2", "camps moved: 1", "camp tiers changed: 1",
                                            "watchers +1 −0"]
    assert terrain._moved_summary(None) == []


def test_7_39b_moved_what_its_notes_say():
    """7.39b's notes: trees cut and planted, Bottom Radiant T1 moved, two camps, one watcher."""
    assert terrain._moved_summary(terrain._load_diff("7.39b")) == [
        "trees +38 −27", "camps moved: 2", "towers moved: 1", "watchers moved: 1"]


def _page(ver, quiet_after=()):
    steps = {s.patch: s for s in mv.steps()}
    return terrain._build_terrain_page(ver, list(steps), {}, steps[ver], terrain._load_diff(ver), "", quiet_after)


def test_a_patch_without_terrain_notes_says_so_and_shows_what_moved():
    html = _page("7.38b")
    assert 'class="terrain-no-notes"' in html
    assert "<b>Moved in the map file:</b> trees +2 −11" in html
    assert 'src="icons/maps/map_7.38.webp' in html and 'src="icons/maps/map_7.38b.webp' in html
    assert "← 7.38&nbsp; OLD" in html and "NEW &nbsp;7.38b →" in html


def _quiet_set():
    steps = {s.patch: s for s in mv.steps()}
    notes = terrain._terrain_notes_by_patch()
    return steps, notes, terrain._quiet(steps, notes, {p: terrain._load_diff(p) for p in steps})


def test_a_patch_that_changed_nothing_gets_no_page():
    """The owner: "if nothing changed in a patch, there's nothing to compare" — no object moved, no notes."""
    steps, notes, quiet = _quiet_set()
    assert quiet == {"7.39e", "7.40c", "7.41c", "7.41d", "7.41e", "7.41f"}
    pages = terrain._pages([p for p in steps if p not in quiet], notes)
    assert pages == ["7.41a", "7.41", "7.40", "7.39d", "7.39c", "7.39b", "7.39", "7.38c", "7.38b"]


def test_the_page_before_names_the_patches_that_changed_nothing():
    steps, notes, quiet = _quiet_set()
    pages = terrain._pages([p for p in steps if p not in quiet], notes)
    runs = terrain._quiet_runs(pages, mv.load_patch_maps(), quiet)
    assert runs["7.41a"] == ["7.41b", "7.41c", "7.41d", "7.41e", "7.41f"]
    assert runs["7.40"] == ["7.40b", "7.40c"] and runs["7.39d"] == ["7.39e"] and runs["7.39b"] == []
    html = _page("7.40", runs["7.40"])
    assert "7.40b – 7.40c changed nothing on the map." in html
    assert "7.39e changed nothing on the map." in _page("7.39d", runs["7.39d"])


def test_the_picker_lists_patches_not_ranges():
    html = terrain._picker_html(["7.39b", "7.39"], "7.39b")
    assert '<a class="version-item current" href="terrain_739b.html"' in html and "–" not in html


def test_a_patch_page_links_to_its_own_terrain_page():
    from patch.elements import plain_header
    assert 'href="../terrain_739b.html"' in plain_header("Terrain Changes", dynamics=False, terrain_link="7.39b")
