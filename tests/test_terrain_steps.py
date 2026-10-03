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


def _page(ver):
    steps = {s.patch: s for s in mv.steps()}
    return terrain._build_terrain_page(ver, list(steps), {}, steps[ver], terrain._load_diff(ver), "")


def test_a_patch_without_terrain_notes_says_nothing_and_shows_what_moved():
    """No "Patch notes / No terrain changes" (the owner 2026-10-03: "we won't write anything if there were no
    changes") — the empty list (the subpatch arrows hang off it), then the facts."""
    html = _page("7.38b")
    assert "Patch notes" not in html and "No terrain changes" not in html and "terrain-notes-none" not in html
    assert '<ul class="changes terrain-list">\n\n</ul>\n<div class="terrain-facts">' in html
    assert '<div class="tf-head">Changed in the map file<span class="tf-kinds">' in html
    assert ('alt="Trees" width="16" height="16"><span class="tm-add-text">+2</span> '
            '<span class="tm-rem-text">−11</span></button>') in html
    assert 'src="icons/maps/map_7.38_2k.webp' in html and 'src="icons/maps/map_7.38b_2k.webp' in html
    assert "← 7.38&nbsp; OLD" in html and "NEW &nbsp;7.38b →" in html


def test_the_page_opens_on_the_small_pictures_and_keeps_the_full_ones_for_zoom():
    """Each map picture opens as its 2048-px copy (~0.85 MB against ~4.2 MB; the owner 2026-10-03: "on weak
    computers it may lag"); the 4096 picture waits in data-full, and the lens images carry no src until the lens
    is switched on (scripts.js fitSrc)."""
    html = _page("7.41")
    old = '<img class="tc-img tc-old" src="icons/maps/map_7.40c_2k.webp?v='
    assert old in html and 'data-full="icons/maps/map_7.40c.webp?v=' in html
    assert '<img class="tc-img tc-new" src="icons/maps/map_7.41_2k.webp?v=' in html
    lens = html.split('<div class="tc-lens"', 1)[1].split("</div>", 1)[0]
    assert lens.count("<img ") == 2 and " src=" not in lens and lens.count("data-full=") == 2
    for ver in ("7.38", "7.41f"):
        assert os.path.exists(os.path.join(_ROOT, "icons", "maps", f"map_{ver}_2k.webp"))


def test_small_pictures_are_swapped_for_full_ones_only_when_drawn_bigger():
    """fitSrc swaps to data-full once the drawn width times the pixel ratio passes 2048, never back; the lens
    fits on switch-on, fullscreen zoom on every resize (updateTiles)."""
    js = open(os.path.join(_ROOT, "src", "scripts.js"), encoding="utf-8").read()
    fit = js.split("function fitSrc(img, cssW) {", 1)[1].split("\n    }\n", 1)[0]
    assert "devicePixelRatio" in fit and "SMALL_PX * 1.05" in fit and "img.dataset.sharp" in fit
    assert "if (loupeMode) { fitSrc(lensOld, w); fitSrc(lensNew, w); }" in js
    assert "if (fsActive && w) fitBase(w);" in js.split("function updateTiles() {", 1)[1][:200]


def _quiet_set():
    steps = {s.patch: s for s in mv.steps()}
    notes = terrain._terrain_notes_by_patch()
    return steps, notes, terrain._quiet(steps, notes, {p: terrain._load_diff(p) for p in steps})


def test_a_patch_that_changed_nothing_gets_no_page_but_the_newest_does():
    """The owner: "if nothing changed in a patch, there's nothing to compare" — no object moved, no notes. 2026-10-03:
    the newest patch keeps its page all the same, "or one could think the patch doesn't exist" (7.41f)."""
    steps, notes, quiet = _quiet_set()
    assert quiet == {"7.39e", "7.40c"}                   # 7.41c-e changed where wards can stand
    pages = terrain._pages([p for p in steps if p not in quiet], notes)
    assert pages == ["7.41f", "7.41e", "7.41d", "7.41c", "7.41a", "7.41", "7.40", "7.39d", "7.39c", "7.39b", "7.39",
                     "7.38c", "7.38b", "7.38"]
    html = terrain._build_terrain_page("7.41f", pages, notes, steps["7.41f"], terrain._load_diff("7.41f"), "")
    assert '<div class="tf-none">Nothing</div>' in html and "NEW &nbsp;7.41f →" in html


def test_7_38_has_its_page_and_its_map_notes():
    """The owner: "make the 7.37e picture so 7.38 has a page"; 7.38's map notes sit under "Wandering Waters" and
    "Other Terrain Changes", and its Lotus Pools were npc_dota_mango_tree before."""
    assert mv.Step("7.38", "7.37e", "7.37e", "7.38") in mv.steps()
    rows = terrain._terrain_notes_by_patch()["7.38"]
    assert {r[2] for r in rows} == {"Wandering Waters", "Other Terrain Changes"}
    moved = terrain._moved_summary(terrain._load_diff("7.38"))
    assert "lotus pools moved: 2" in moved and "wisdom runes +0 −2" in moved and "wisdom shrines +2 −0" in moved


def test_the_patches_that_changed_nothing_are_not_mentioned():
    """The owner 2026-10-02: "remove 'Unchanged in 7.41f'" — no page and no line about them."""
    steps, notes, quiet = _quiet_set()
    pages = terrain._pages([p for p in steps if p not in quiet], notes)
    html = terrain._build_terrain_page("7.39d", pages, notes, steps["7.39d"], terrain._load_diff("7.39d"), "")
    body = html.split('<div class="terrain-wrap">')[1]
    assert "7.39e" not in body and "Unchanged" not in body
    assert 'href="terrain_739e.html"' not in html


def test_the_facts_read_like_the_list():
    """The owner: four lines of text "should be laid out better", then the tables "aren't harmonious" — headings like
    the list's subgroup heads, five tiles (trees, then camps small → ancient), the changes as "icon: change" chips
    with "n/of all" ("Bounty runes 1 moved (1/2)"; not "Added / removed: No-ward cells +2")."""
    diff = terrain._load_diff("7.40")
    _svg, counts = terrain._markers_svg(diff, "740")
    step = next(s for s in mv.steps() if s.patch == "7.40")
    html = terrain._facts_html(counts, step, diff)
    assert "<table" not in html and html.count('<div class="tf-head">') == 2
    first = html.split('<div class="tf-tiles tf-tiles-more">')[0]
    assert first.count('<div class="tf-tile">') == 5 and 'icons/camps/creepcamp_ancient.png' in first
    names = [n.split(" ")[0].split("<")[0] for n in first.split('<div class="tf-name">')[1:]]
    assert names == ["trees", "small", "medium", "large", "ancient"]
    assert '<div class="tf-name">large <span class="tm-rem-text">−4</span></div>' in html
    assert '<div class="tf-name">medium <span class="tm-add-text">+4</span></div>' in html
    assert "tf-verb" not in html and "Moved</div>" not in html
    assert 'alt="Camps" width="16" height="16"><b>9/28</b> moved</button>' in html
    assert 'alt="Towers" width="16" height="16"><b>1/22</b> moved</button>' in html
    assert 'alt="Camp tiers" width="16" height="16"><b>4/28</b> re-tiered</button>' in html
    assert 'alt="Camp spawn boxes" width="16" height="16"><b>10/28</b> resized</span>' in html
    assert '<div class="tf-none">Nothing</div>' in terrain._facts_html({}, step, {"treesOld": [], "treesNew": []})


def test_every_kind_of_object_has_a_tile_under_trees_and_camps():
    """The owner 2026-10-03: "add all the other objects the way you show trees and camps — only with a gap, so trees
    and camps stand on one row and everything else on the others"."""
    diff = terrain._load_diff("7.40")
    _svg, counts = terrain._markers_svg(diff, "740")
    step = next(s for s in mv.steps() if s.patch == "7.40")
    html = terrain._facts_html(counts, step, diff)
    first, more = html.split('<div class="tf-tiles">')[1].split('<div class="tf-tiles tf-tiles-more">')
    assert first.count('<div class="tf-tile">') == 5
    names = [n.split(" <")[0].split("<")[0] for n in more.split('<div class="tf-name">')[1:]]
    assert names == ["towers", "lotus pools", "twin gates", "Tormentors", "bounty runes", "power runes",
                     "wisdom shrines", "outposts", "watchers", "Roshan pits"]
    assert 'tc_towers.png" alt="" width="16" height="16">22</div><div class="tf-name">towers</div>' in more
    assert '<div class="tf-name">watchers <span class="tm-rem-text">−4</span></div>' in more    # 7.40: 14 -> 10


def _hl(svg, key, side="old"):
    parts = svg.split(f"tm-hl-{key} tm-{side}")
    return parts[1].split("</svg>")[0] if len(parts) > 1 else ""


def test_a_chip_outlines_removed_on_the_old_map_added_on_the_new_moved_on_both():
    """The owner 2026-10-02: pressing a "Changed in the map file" chip outlines the changed places — not for spawn
    boxes, their layer already shows them. 2026-10-03: in the object's own shape (a square like the tree itself),
    red = removed (old map), green = added (new map), yellow = moved — where it stood on the old map and where it
    stands on the new one; the chip turns its layer on."""
    diff = terrain._load_diff("7.39b")
    svg, counts = terrain._markers_svg(diff, "739b")
    step = next(s for s in mv.steps() if s.patch == "7.39b")
    html = terrain._facts_html(counts, step, diff)
    assert 'class="tf-chip tf-chip-btn" data-hl="towers" data-layer="towers"' in html
    assert 'data-hl="trees" data-layer="trees"' in html
    assert 'alt="Camp spawn boxes"' in html and "data-hl=\"camp" not in html.split('alt="Camp spawn boxes"')[0][-90:]
    old, new = _hl(svg, "towers", "old"), _hl(svg, "towers", "new")       # the offlane tier 2 tower moved
    assert 'fill="#ffd23f" mask="url(#tm-hl-mask-towers-old-moved)"' in old and "<circle" in old
    assert 'fill="#ffd23f" mask="url(#tm-hl-mask-towers-new-moved)"' in new
    assert "#ff4d4d" not in old + new and "#5dff8a" not in old + new
    t_old, t_new = _hl(svg, "trees", "old"), _hl(svg, "trees", "new")
    assert "<rect" in t_old and "<circle" not in t_old                   # squares, like the trees
    assert "#ff4d4d" in t_old and "#5dff8a" not in t_old and "#5dff8a" in t_new and "#ff4d4d" not in t_new
    assert 'data-layer="trees"' in svg.split("tm-hl-trees tm-old")[1][:40]


def test_moved_removed_added_switches_sit_by_the_heading():
    """The owner 2026-10-03: "somehow choose what to show: moved, removed or added"."""
    diff = terrain._load_diff("7.39b")
    _svg, counts = terrain._markers_svg(diff, "739b")
    step = next(s for s in mv.steps() if s.patch == "7.39b")
    html = terrain._facts_html(counts, step, diff)
    head = html.split('<div class="tf-head">Changed in the map file')[1].split("</div>")[0]
    assert [k.split('"')[0] for k in head.split('data-kind="')[1:]] == ["moved", "removed", "added"]
    assert 'aria-pressed="true"' in head and "tf-kind-sw tf-kind-moved" in head


def test_no_ward_cells_added_are_green_and_removed_red_filled():
    """The owner 2026-10-03: 7.41d's "+23" no-ward cells were drawn red — "it should be green, since they were
    added" — and filled half-transparent like the magenta layer, not outlined; 7.41c's 149 cells that turned
    wardable are the removed ones, red on the old map."""
    d_svg = terrain._markers_svg(terrain._load_diff("7.41d"), "741d")[0]
    c_svg = terrain._markers_svg(terrain._load_diff("7.41c"), "741c")[0]
    added, removed = _hl(d_svg, "nowards", "new"), _hl(c_svg, "nowards", "old")
    assert 'fill="#5dff8a" fill-opacity="0.55"' in added and added.count("Z") == 23
    assert 'fill="#ff4d4d" fill-opacity="0.55"' in removed and removed.count("Z") == 149
    assert _hl(d_svg, "nowards", "old") == "" and _hl(c_svg, "nowards", "new") == ""


def test_the_old_map_is_left_of_the_handle_under_its_chip():
    """The owner 2026-10-03 read a change outlined on 7.41c as "drawn on 7.41d": the new map was revealed from the
    left while the corner chips said "← OLD" left, "NEW →" right. Now the sides match the chips."""
    css = open(os.path.join(_ROOT, "styles.css"), encoding="utf-8").read()
    assert ".tm-old { clip-path: inset(0 calc(100% - var(--pos)) 0 0); }" in css
    assert ".tm-new { clip-path: inset(0 0 0 var(--pos)); }" in css
    assert ".tc-lens-new { clip-path: inset(0 0 0 var(--pos)); }" in css
    new_layer = css.split(".tc-new-layer {")[1].split("}")[0]
    assert "clip-path: inset(0 0 0 var(--pos));" in new_layer


def test_overlapping_outlines_merge_into_one():
    """The owner 2026-10-03 (a slightly moved object showed "two frames"): each shape is drawn widened by half the
    stroke and cut by itself narrowed by half the stroke, so overlapping ones leave one outer contour."""
    svg = terrain._outline_union("tm-hl-mask-w", "moved", [(100, 100), (100, 108)], ("circle", 19), "#ffd23f")
    assert '<circle cx="100" cy="100" r="20.2"/>' in svg and '<circle cx="100" cy="108" r="17.8"/>' in svg
    assert svg.startswith('<g class="tm-hl-g tm-hl-g-moved">')
    assert svg.index("<mask") < svg.index('mask="url(#tm-hl-mask-w)"')
    sq = terrain._outline_union("m", "removed", [(10, 10)], ("rect", 5), "#ff4d4d", 2)
    assert '<rect x="4.0" y="4.0" width="12.0" height="12.0"/>' in sq
    assert '<rect x="6.0" y="6.0" width="8.0" height="8.0"/>' in sq
    assert terrain._outline_union("unused", "added", [], ("circle", 19), "#5dff8a") == ""
    removed, added, moved = terrain._pair_moves([(0, 0), (500, 500)], [(10, 0), (900, 900)], 38)
    assert (removed, added, moved) == ([(500, 500)], [(900, 900)], [((0, 0), (10, 0))])


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


def test_fullscreen_has_a_folding_panel_with_the_change_filters():
    """The owner 2026-10-03: the "Changed in the map file" filters in fullscreen too, in "a separate panel that opens
    and closes" — the same chips and switches as under the list."""
    steps = {s.patch: s for s in mv.steps()}
    html = terrain._build_terrain_page("7.40", list(steps), {}, steps["7.40"], terrain._load_diff("7.40"), "")
    panel = html.split('<div class="tc-fs-bar"')[1].split('<div class="terrain-list-box">')[0]
    assert 'class="tc-btn tc-btn-icon tc-fsp-toggle" aria-expanded="true"' in panel
    assert '<div class="tc-fsp-title">Layers</div>' in panel and 'data-layer="nowards"' in panel
    assert '<div class="tc-fsp-title">Changed in the map file</div>' in panel
    facts = html.split('<div class="terrain-facts">')[1]
    for key in ("trees", "camps", "towers", "nowards"):
        assert panel.count(f'data-hl="{key}"') == 1 and facts.count(f'data-hl="{key}"') == 1
    assert panel.count('class="tf-kind"') == facts.count('class="tf-kind"') == 3
    assert 'class="tc-sep"' not in panel                    # the grid needs no separators


def test_the_slider_writes_clip_paths_not_an_inherited_property():
    """2026-10-03 probe: setting --pos on the stage re-styled every marker under it on each move (13 s of style
    recalc per drag on a 4x-throttled CPU); the slider now writes each split element's clip-path itself."""
    js = open(os.path.join(_ROOT, "src", "scripts.js"), encoding="utf-8").read()
    apply = js.split("function apply(p) {")[1].split("apply(pos);")[0]
    assert "setProperty('--pos'" not in apply and "el.style.clipPath = clipNew" in apply
    assert "handle.style.left = pos + '%'" in apply


def test_a_terrain_note_shows_its_micro_screenshots():
    """The owner 2026-10-03: terrain rows were "all under one tag, mush — maybe micro-screenshots". A row matched in
    data/terrain_spots.json carries its old | new pictures under a "Show where" button (hidden until pressed, no link
    to the Terrain page — "View on map" is for that); a click opens the large copy; every picture exists twice."""
    from patch.elements import terrain_shots_html, _terrain_spot_index
    row = "The tier 1 safe lane towers have been moved slightly away from their pull camps and where the creeps meet"
    html = terrain_shots_html("7.41", row)
    assert html.startswith('<span class="tshots-wrap"><button type="button" class="tshots-btn" aria-expanded="false">'
                           'Show where</button><span class="tshots" hidden>')
    assert html.count("<img") == 2 and "<a " not in html and 'data-large="../icons/terrain/741_' in html
    assert terrain_shots_html("7.41", "Some row no spot matches") == ""
    li = terrain._change_li(row, "REWORK", None, "7.41")
    assert '<img src="icons/terrain/741_' in li and 'data-large="icons/terrain/741_' in li and "<a " not in li
    for patch, rows in _terrain_spot_index().items():
        for _match, names in rows:
            for n in names:
                assert os.path.exists(os.path.join(_ROOT, "icons", "terrain", n)), n
                assert os.path.exists(os.path.join(_ROOT, "icons", "terrain", n[:-5] + "_lg.webp")), n


def test_a_note_outlines_only_its_own_objects():
    """The owner 2026-10-03: "a camps note shows only the camps, not the trees and everything else" — the first
    object word decides; the ground (cliff, ramp, path) gives none; 'show' in terrain_spots.json overrides."""
    sys.path.insert(0, os.path.join(_ROOT, "scripts", "gen"))
    import terrain_shots as ts
    assert ts.show_keys("Moved the safelane medium amphibian neutral camp closest to the Tier 2 tower") == set(ts.CAMP_KEYS)
    assert ts.show_keys("Removed several trees from Dire Safelane small pull camp") == {"trees"}
    assert ts.show_keys("The tier 1 safe lane towers have been moved slightly away from their pull camps") == {"towers"}
    assert ts.show_keys("The ramp leading to the river and the Roshan Pit from the Dire Safe Lane pull area") == set()
    assert ts.show_keys("The cliff above the Dire Safe Lane small camp has been extended") == set()
    assert ts.show_keys("Twin Gates slightly moved away from the stairs") == {"twinGates"}
    assert ts.spot_keys({"match": "Cleared up some areas around the Tormentor locations", "show": ["trees"]}) == {"trees"}


def test_a_chip_turns_off_the_layer_it_turned_on():
    """The owner 2026-10-03: a chip that switched its layer on switches it off again with the chip; a layer the viewer
    had on (or clicked meanwhile, "All" too) stays."""
    js = open(os.path.join(_ROOT, "src", "scripts.js"), encoding="utf-8").read()
    block = js.split("function initChangeHighlights() {", 1)[1].split("\n  }\n", 1)[0]
    assert "autoLayers[layer] = true;" in block
    assert "!on && autoLayers[layer] && !layerChipsOn(layer)" in block
    assert "if (!chipClick) {" in block and "b.dataset.layer !== 'all'" in block


def test_note_pictures_open_large_and_fold_under_the_button():
    js = open(os.path.join(_ROOT, "src", "scripts.js"), encoding="utf-8").read()
    block = js.split("Terrain note pictures", 1)[1][:3000]
    assert ".tshots-btn" in block and "pics.hidden = !open" in block and "img.dataset.large" in block
    css = open(os.path.join(_ROOT, "styles.css"), encoding="utf-8").read()
    assert ".tshots[hidden] { display: none; }" in css and "cursor: zoom-in" in css


def test_patch_pages_add_decoding_only_where_an_image_lacks_it():
    """patch/page.py gives every <img> decoding="async"; one that already has it (the terrain micro-screenshots)
    must not get it twice (2026-10-03)."""
    src = open(os.path.join(_ROOT, "patch", "page.py"), encoding="utf-8").read()
    assert "out.replace('<img ', '<img decoding=\"async\" ')" not in src
    import re
    rx = re.compile(r'<img (?![^>]*\bdecoding=)')
    html = '<img src="a.png"><img src="b.webp" loading="lazy" decoding="async">'
    assert rx.sub('<img decoding="async" ', html).count("decoding=") == 2


def test_the_picker_lists_patches_not_ranges():
    html = terrain._picker_html(["7.39b", "7.39"], "7.39b")
    assert '<a class="version-item current" href="terrain_739b.html"' in html and "–" not in html


def test_a_patch_page_links_to_its_own_terrain_page():
    from patch.elements import plain_header
    assert 'href="../terrain_739b.html"' in plain_header("Terrain Changes", dynamics=False, terrain_link="7.39b")
