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


def test_the_site_has_every_map_file_from_738_to_741f():
    got = [s.patch for s in mv.steps()]
    assert got == ["7.38", "7.38b", "7.38c", "7.39", "7.39b", "7.39c", "7.39d", "7.39e", "7.40", "7.40c",
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
        "trees +38 −27", "camps moved: 2", "camp spawn boxes changed: 2", "towers moved: 1", "watchers moved: 1"]


def test_every_block_linked_to_the_map_is_read():
    """The owner: "check the changed terrain for other errors too" — 7.38b's map notes sat in the General list and
    7.38c's under "Dire Safe Lane Jungle" / "Top Roshan Pit" / "Bottom Lane", so both pages said "no terrain
    changes". A block with terrain_link= is map notes, whatever its title."""
    notes = terrain._terrain_notes_by_patch()
    assert len(notes["7.38b"]) == 2 and len(notes["7.38c"]) == 15
    assert {r[2] for r in notes["7.38c"]} == {"Dire Safe Lane Jungle", "Top Roshan Pit", "Bottom Lane"}
    assert all(r[2] != "Terrain Changes" for rows in notes.values() for r in rows)   # that title is no subgroup


def test_a_rows_inline_note_comes_along():
    """7.41's "Result:" lines are the Watcher row's inline note; the Terrain page shows them as the patch page does."""
    rows = terrain._terrain_notes_by_patch()["7.41"]
    watcher = next(r for r in rows if r[0].startswith("The watcher between"))
    assert watcher[3].startswith("Tormentor is on the low ground")
    html = terrain._changes_html([("7.41", [watcher])], skip_first_head=True)
    assert 'class="li-tail"' in html and 'class="info-tip"' in html and "Twin Gate highground" in html


def test_camp_tier_changes_follow_the_camp_not_its_name():
    """7.40 demoted 4 camps (2 of them also moved — an exact-position match read 2); 7.41 too. 7.38 renumbered its
    camps, so matching by name would call camps 12000 units apart the same camp."""
    for patch in ("7.40", "7.41"):
        assert "camp tiers changed: 4" in terrain._moved_summary(terrain._load_diff(patch))
    old = [{"x": 0, "y": 0, "tier": 2}, {"x": 5000, "y": 0, "tier": 1}]
    new = [{"x": 300, "y": 0, "tier": 1}, {"x": 5000, "y": 3000, "tier": 3}]
    assert terrain._retiered(old, new) == 1                       # the far one is another camp, not a promotion


def test_7_39d_bigger_triangle_ancient_boxes_show():
    """The owner: 7.39d "Increased spawnboxes of Triangle Ancient camps", yet the map showed no difference — the
    summary didn't count boxes, and the old dashed box hid a few px inside the new one."""
    diff = terrain._load_diff("7.39d")
    # + "Fixed a ward spot in Radiant safe lane hard camp": 10 gridnav cells turned no-ward
    assert terrain._moved_summary(diff) == ["trees +0 −3", "camp spawn boxes changed: 2", "no-ward cells +10 −0"]
    svg, _counts = terrain._markers_svg(diff, "739d")
    assert svg.count("tc-sb-new tc-sb-changed") == 2 and svg.count("tc-sb-old tc-sb-changed") == 2
    assert svg.count("tc-sb-same") == 26


def _page(ver, quiet_after=()):
    steps = {s.patch: s for s in mv.steps()}
    return terrain._build_terrain_page(ver, list(steps), {}, steps[ver], terrain._load_diff(ver), "", quiet_after)


def test_a_patch_without_terrain_notes_says_so_and_shows_what_moved():
    html = _page("7.38b")
    assert 'class="terrain-no-notes"' in html
    assert '<caption>Changed in the map file</caption>' in html
    assert ('Trees <span class="tm-add-text">+2</span> <span class="tm-rem-text">−11</span></span>') in html
    assert 'src="icons/maps/map_7.38.webp' in html and 'src="icons/maps/map_7.38b.webp' in html
    assert "← 7.38&nbsp; OLD" in html and "NEW &nbsp;7.38b →" in html


def _quiet_set():
    steps = {s.patch: s for s in mv.steps()}
    notes = terrain._terrain_notes_by_patch()
    return steps, notes, terrain._quiet(steps, notes, {p: terrain._load_diff(p) for p in steps})


def test_a_patch_that_changed_nothing_gets_no_page():
    """The owner: "if nothing changed in a patch, there's nothing to compare" — no object moved, no notes."""
    steps, notes, quiet = _quiet_set()
    assert quiet == {"7.39e", "7.40c", "7.41f"}          # 7.41c-e changed where wards can stand
    pages = terrain._pages([p for p in steps if p not in quiet], notes)
    assert pages == ["7.41e", "7.41d", "7.41c", "7.41a", "7.41", "7.40", "7.39d", "7.39c", "7.39b", "7.39",
                     "7.38c", "7.38b", "7.38"]


def test_7_38_has_its_page_and_its_map_notes():
    """The owner: "make the 7.37e picture so 7.38 has a page"; 7.38's map notes sit under "Wandering Waters" and
    "Other Terrain Changes", and its Lotus Pools were npc_dota_mango_tree before."""
    assert mv.Step("7.38", "7.37e", "7.37e", "7.38") in mv.steps()
    rows = terrain._terrain_notes_by_patch()["7.38"]
    assert {r[2] for r in rows} == {"Wandering Waters", "Other Terrain Changes"}
    moved = terrain._moved_summary(terrain._load_diff("7.38"))
    assert "lotus pools moved: 2" in moved and "wisdom runes +0 −2" in moved and "wisdom shrines +2 −0" in moved


def test_the_page_before_names_the_patches_that_changed_nothing():
    steps, notes, quiet = _quiet_set()
    pages = terrain._pages([p for p in steps if p not in quiet], notes)
    runs = terrain._quiet_runs(pages, mv.load_patch_maps(), quiet)
    assert runs["7.41a"] == ["7.41b"] and runs["7.41e"] == ["7.41f"]
    assert runs["7.40"] == ["7.40b", "7.40c"] and runs["7.39d"] == ["7.39e"] and runs["7.39b"] == []
    html = _page("7.40", runs["7.40"])
    assert "7.40b – 7.40c changed nothing on the map." in html
    assert "7.39e changed nothing on the map." in _page("7.39d", runs["7.39d"])


def test_the_facts_are_two_small_tables():
    """The owner: the four lines of "Trees / Neutral camps / Moved in the map file / … changed nothing" should be
    laid out better — "On the map" (with camp icons) and "Changed in the map file", then the quiet patches."""
    diff = terrain._load_diff("7.40")
    _svg, counts = terrain._markers_svg(diff, "740")
    step = next(s for s in mv.steps() if s.patch == "7.40")
    html = terrain._facts_html(counts, step, diff, ["7.40b", "7.40c"])
    assert html.count('<table class="terrain-facts">') == 2
    assert '<caption>On the map</caption>' in html and 'icons/camps/creepcamp_ancient.png' in html
    assert '6 large <span class="tm-rem-text">−4</span>' in html and '14 medium <span class="tm-add-text">+4</span>' in html
    # grouped by what happened, each kind of object a chip with "n/of all" (the owner: "Bounty runes 1 moved (1/2)")
    moved = html[html.index('<td class="tf-label">Moved</td>'):]
    assert 'Camps <b>9/28</b>' in moved.split("</tr>")[0] and 'Towers <b>1/22</b>' in moved.split("</tr>")[0]
    changed = html[html.index('<td class="tf-label">Changed</td>'):].split("</tr>")[0]
    assert 'Camp tiers <b>4/28</b>' in changed and 'Camp spawn boxes <b>10/28</b>' in changed
    assert 'icons/ui/gothic/tc_towers.png' in html and html.count('class="tf-chip"') >= 6
    assert html.endswith('<p class="terrain-quiet">7.40b – 7.40c changed nothing on the map.</p>\n')
    assert "Nothing</td>" in terrain._facts_html({}, step, {"treesOld": [], "treesNew": []})


def test_the_zoom_tiles_are_named_on_the_slider(monkeypatch):
    """The owner: "is this quality normal when zoomed?" — fullscreen zoom lays 8192 tiles from Oldgrowth over the
    4096 pictures; the slider says where each side's tiles are, only for pictures that have them."""
    monkeypatch.setattr(terrain, "_tiled_pictures", lambda: {"7.39", "7.39b"})
    html = terrain._compare_html("7.39", "7.39b", "", "7.39", "7.39b")
    assert 'data-tiles-old="https://sikleq.github.io/Oldgrowth/tiles/7.39/"' in html
    assert 'data-tiles-new="https://sikleq.github.io/Oldgrowth/tiles/7.39b/"' in html
    monkeypatch.setattr(terrain, "_tiled_pictures", lambda: {"7.39b"})
    assert "data-tiles-old" not in terrain._compare_html("7.39", "7.39b", "", "7.39", "7.39b")


def test_map_tiles_cut_the_squeezed_square():
    pytest = __import__("pytest")
    Image = pytest.importorskip("PIL.Image")
    sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
    import map_tiles
    full = Image.new("RGB", (100, 120), (10, 20, 30))
    got = map_tiles.tiles(full, size=64, grid=4)
    assert len(got) == 16 and {im.size for _r, _c, im in got} == {(16, 16)}
    assert (got[5][0], got[5][1]) == (1, 1)


def test_an_all_layers_button_leads_the_layer_toggles():
    """The owner: add an "all" filter that turns every object layer on; its icon is drawn by the generator."""
    import re
    top, fs = terrain._controls_html(layers=True)
    for bar in (top, fs):
        layers = re.findall(r'data-layer="(\w+)"', bar)
        assert layers[0] == "all" and "trees" in layers and "nowards" in layers and len(layers) == 15
    assert 'src="icons/ui/gothic/tc_all.png"' in top
    assert os.path.exists(os.path.join(_ROOT, "icons", "ui", "gothic", "tc_all.png"))
    assert "data-layer" not in terrain._controls_html(layers=False)[0]


def test_the_picker_lists_patches_not_ranges():
    html = terrain._picker_html(["7.39b", "7.39"], "7.39b")
    assert '<a class="version-item current" href="terrain_739b.html"' in html and "–" not in html


def test_a_patch_page_links_to_its_own_terrain_page():
    from patch.elements import plain_header
    assert 'href="../terrain_739b.html"' in plain_header("Terrain Changes", dynamics=False, terrain_link="7.39b")
