"""Guards the health of the code base: regexes that must fail fast, errors that must not be swallowed, shared helpers,
private names in public files, audits and self-hosted assets.
"""

import importlib.util
import os
import pytest
import re
import sys
import time
from patch.css_bundle import read_css
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _script():
    pytest.importorskip("PIL")
    spec = importlib.util.spec_from_file_location("boss_icons", ROOT / "scripts" / "fetch" / "extract_vpk_boss_icons.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# b() zips its two lists: with different lengths the extra values are dropped silently. Reviewed rows where
# that is right (levels added at the end, compared level by level); anything new must be looked at.
_UNEQUAL_OK = {
    # 7.38 Invoker: Quas/Wex/Exort got levels 9 and 10
    "b([3, 6, 9, 12, 15, 18, 21, 24], [2, 4, 6, 8, 10, 12, 14, 16, 18, 20])",
    "b([-15, -10, -5, 0, 5, 10, 15, 20], [-20, -15, -10, -5, 0, 5, 10, 15, 20, 25])",
    "b([20, 30, 40, 50, 60, 70, 80, 90], [10, 20, 30, 40, 50, 60, 70, 80, 90, 100])",
    "b([22, 32, 42, 52, 62, 72, 82, 92], [20, 30, 40, 50, 60, 70, 80, 90, 100, 110])",
    "b([3, 4.5, 6, 7.5, 9, 10.5, 12], [3, 4, 5, 6, 7, 8, 9, 10, 11, 12])",
    "b([6, 12, 18, 24, 30, 36, 42, 48], [8, 16, 24, 32, 40, 48, 56, 64, 72, 80])",
    "b([60, 100, 140, 180, 220, 260, 300, 340], [70, 110, 150, 190, 230, 270, 310, 350, 390, 430])",
    "b([0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6], [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2])",
    "b([1.25, 2, 2.75, 3.5, 4.25, 5, 5.75, 6.5], [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6])",
    # 7.38 Night Stalker Voidbringer: Void gets a 5th level
    "b([2.5, 3, 3.5, 4], [2, 2.5, 3, 3.5, 4])",
    # 7.37e Tusk Bitter Chill: scaled with Tag Team (0-4), now with the ultimate Walrus Punch (0-3)
    "b([20, 30, 40, 50, 60], [15, 35, 55, 75])",
}
_ROOT_audit_1110 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT_audit_1110)
_ROOT_card_fixes_1026 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ability_audit():
    import importlib.util
    spec = importlib.util.spec_from_file_location("audit_abilities", ROOT / "scripts" / "audit" / "audit_abilities.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _from_audit():
    import importlib.util
    spec = importlib.util.spec_from_file_location("audit_from_values", ROOT / "scripts" / "audit" / "audit_from_values.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_icon_script_does_not_rewrite_a_picture_it_already_has(tmp_path):
    pytest.importorskip("PIL")
    mod = _script()
    from PIL import Image
    dst = tmp_path / "a.png"
    Image.new("RGBA", (4, 4), (10, 20, 30, 255)).save(dst)
    assert mod.same_picture(Image.new("RGBA", (4, 4), (10, 20, 30, 255)), dst)
    assert not mod.same_picture(Image.new("RGBA", (4, 4), (11, 20, 30, 255)), dst)
    # a portrait keeps the size the site has for it (the Tormentor's is square)
    assert mod.unit_portrait(Image.new("RGBA", (128, 72)), dst).size == (4, 4)


@pytest.mark.parametrize("page", ["hero_changes.html", "item_changes.html", "unit_changes.html"])
def test_top_level_pages_do_not_climb_out_of_the_site(page):
    f = ROOT / "dist" / page
    if not f.exists():
        pytest.skip("dist not built")
    assert 'src="../icons' not in f.read_text(encoding="utf-8")


def test_badge_lists_of_different_length_are_reviewed():
    import ast
    found = set()
    for f in sorted((ROOT / "content").glob("p*.py")):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "b" and len(node.args) >= 2:
                a, c = node.args[:2]
                if (isinstance(a, ast.List) and isinstance(c, ast.List)
                        and len(a.elts) != len(c.elts) and min(len(a.elts), len(c.elts)) > 1):
                    found.add(ast.unparse(node))
    assert found <= _UNEQUAL_OK, f"b() lists differ in length (pad the old list or align the levels): {sorted(found - _UNEQUAL_OK)}"


def test_silent_pages_use_in_game_names():
    from builders import silent
    assert silent._hero_display("npc_dota_hero_zuus") == "Zeus"
    assert silent._hero_display("npc_dota_hero_nevermore") == "Shadow Fiend"
    assert silent._ability_display("abaddon_aphotic_shield") == "Aphotic Shield"
    assert silent._ability_display("no_such_ability_slug") == "no_such_ability_slug"


def test_full_build_prunes_pages_it_did_not_write(tmp_path):
    import os
    import time
    import build_site
    (tmp_path / "patches").mkdir()
    (tmp_path / "icons").mkdir()
    old_page, new_page, icon_page = tmp_path / "patches" / "7.20.html", tmp_path / "patches" / "7.41.html", tmp_path / "icons" / "x.html"
    for f in (old_page, new_page, icon_page):
        f.write_text("x", encoding="utf-8")
    past = time.time() - 3600
    os.utime(old_page, (past, past))
    os.utime(icon_page, (past, past))          # copied folders keep their source mtimes
    build_site._prune_stale_pages(tmp_path, time.time() - 60)
    assert not old_page.exists() and new_page.exists() and icon_page.exists()


def test_no_page_builder_loads_google_fonts_or_the_steam_background():
    srcs = list((ROOT / "builders").glob("*.py")) + list((ROOT / "patch").glob("*.py")) + list((ROOT / "src" / "css").glob("*.css"))
    needles = ("fonts.googleapis", "fonts.gstatic", "dota_react/backgrounds/featured.jpg")
    hits = [f.name for f in srcs if any(n in f.read_text(encoding="utf-8") for n in needles)]
    assert hits == []


def test_self_hosted_font_files_exist():
    import re
    css = read_css()
    for path in set(re.findall(r"url\('(src/fonts/[^']+)'\)", css)):
        assert (ROOT / path).exists(), path
    assert (ROOT / "icons" / "ui" / "bg" / "patch_bg.jpg").exists()


def test_trailing_note_regex_fails_fast_on_many_tags():
    """A bracket of a dozen inline tags before more text took seconds to fail: each tag was read two ways."""
    from patch.value_tables import _TRAILING_NOTE_RE
    start = time.perf_counter()
    assert _TRAILING_NOTE_RE.search("(" + "<b>x</b>" * 40 + ") tail") is None
    assert time.perf_counter() - start < 0.5
    m = _TRAILING_NOTE_RE.search("450 (was <b>300</b> before)")
    assert m and m.group(1) == "was <b>300</b> before"


def test_kv_value_regex_fails_fast_on_a_long_number():
    sys.path.insert(0, os.path.join(_ROOT_audit_1110, "scripts", "audit"))
    src = open(os.path.join(_ROOT_audit_1110, "scripts", "audit", "audit_from_values.py"), encoding="utf-8").read()
    num = re.search(r'^_NUM1 = r"(.+)"$', src, re.M).group(1)
    kv_val = re.compile(rf'"\s*({num}(?:\s+{num})*)\s*"')
    start = time.perf_counter()
    assert kv_val.search('"' + "1" * 40 + "x") is None
    assert time.perf_counter() - start < 0.5
    assert kv_val.search('"=40 =60"').group(1) == "=40 =60"
    assert kv_val.search('".5"').group(1) == ".5"
    assert kv_val.search('"8 10 12 "').group(1) == "8 10 12"


def test_map_history_version_key_takes_a_name_that_is_no_version():
    sys.path.insert(0, os.path.join(_ROOT_audit_1110, "scripts", "gen"))
    src = open(os.path.join(_ROOT_audit_1110, "scripts", "gen", "map_history.py"), encoding="utf-8").read()
    body = src[src.index("def _ver_key(v):"):]
    scope = {"re": re}
    exec(body[:body.index("\n\n\n")], scope)
    key = scope["_ver_key"]
    assert key("7.41f") == (7, 41, "f") and key("7.40") < key("7.41") < key("7.41b")
    assert key("notes") == (0, 0, "notes")


def test_no_private_name_or_session_in_the_public_files():
    """The repository is public: the owner's first name stood in three files, a logged-in Telegram session and a
    launcher with an api hash lay inside the project folder (ignored by git, carried by any copy of the folder)."""
    name = bytes.fromhex("d094d0b5d0bdd0b8d181").decode("utf-8")
    for rel in ("docs/weights.md", "docs/weights-review.md", "patch/weights.py", "AGENTS.md", "README.md"):
        path = os.path.join(_ROOT_audit_1110, rel)
        if os.path.exists(path):
            assert name not in open(path, encoding="utf-8").read(), rel
    assert not os.path.exists(os.path.join(_ROOT_audit_1110, "run_signatures.ps1"))
    assert not os.path.exists(os.path.join(_ROOT_audit_1110, "scripts", ".tg_signatures.session"))
    src = open(os.path.join(_ROOT_audit_1110, "scripts", "fetch", "fetch_signatures.py"), encoding="utf-8").read()
    assert 'Path.home() / ".sloppy"' in src


def test_no_whole_script_bundle_is_built():
    src = open(os.path.join(_ROOT_audit_1110, "build_site.py"), encoding="utf-8").read()
    assert '"scripts.js").write_text' not in src


def test_shared_helpers_have_one_home():
    """The end of a <div>, tags stripped, the order of versions: one function each (they were 4, 67 and 12)."""
    from patch.html_util import div_end, plain, strip_tags
    from patch.versions import version_key
    html = '<div class="a"><div>x</div><b>y</b></div><div>z</div>'
    assert html[:div_end(html, 0)] == '<div class="a"><div>x</div><b>y</b></div>'
    assert div_end("<div><div></div>", 0) == len("<div><div></div>")
    try:
        div_end("<div><div></div>", 0, strict=True)
        raise AssertionError("an unclosed div passed")
    except ValueError:
        pass
    assert strip_tags("a <b>b</b>  c") == "a b  c" and plain(" a <b>b</b>  c ") == "a b c"
    names = ["7.41", "7.36a", "7.40b", "7.36", "7.4", "7.40", "notes", None]
    assert sorted(names, key=version_key) == [None, "notes", "7.4", "7.36", "7.36a", "7.40", "7.40b", "7.41"]
    for rel, word in (("patch/value_tables.py", "def _div_end"), ("patch/deck_extra.py", "def _div_end"),
                      ("builders/entity_changes.py", "def _balanced_div"), ("patch/stats.py", "num += c"),
                      ("builders/heroes_stats.py", "num += c")):
        assert word not in open(os.path.join(_ROOT_audit_1110, rel), encoding="utf-8").read(), rel


def test_builders_do_not_swallow_every_error():
    """A missing or broken input printed nothing and gave an empty page with exit code 0: each reader names what it
    catches (and says so), none catches Exception to return an empty result in silence."""
    silent = re.compile(r"except Exception:\s*\n\s*(?:pass|continue|return (?:\{\}|None|\[\]|\(\)))\s*\n")
    for rel in ("builders/hero_lab.py", "builders/aoe_increase.py", "builders/mana_items.py", "builders/creeps_history.py",
                "builders/heroes_stats.py", "builders/creeps.py", "builders/terrain.py", "tools/patchgen/pipeline.py",
                "tools/patchgen/post_items.py"):
        src = open(os.path.join(_ROOT_audit_1110, rel), encoding="utf-8").read()
        assert not silent.search(src), rel


def test_icons_missing_on_the_cdn_are_looked_for_in_the_game_files():
    src = open(os.path.join(_ROOT_card_fixes_1026, "scripts", "fetch", "fetch_icons.py"), encoding="utf-8").read()
    assert "AbilityTextureName" in src and "from_vpk" in src
    from patch.known_exceptions import KNOWN_INNATE_NO_CDN_ICON
    # 7.41 Squee's Scope draws Stasis Trap's icon (KV AbilityTextureName): found, not an exception
    assert "techies_squees_scope" not in KNOWN_INNATE_NO_CDN_ICON
    assert os.path.exists(os.path.join(_ROOT_card_fixes_1026, "icons", "abilities", "techies_squees_scope.png"))
    # PNG_RGBA8888 (16): spell icons are PNG files inside; read, not imported — CI has no numpy
    vpk = open(os.path.join(_ROOT_card_fixes_1026, "scripts", "fetch", "extract_vpk_icons.py"), encoding="utf-8").read()
    assert re.search(r"^EMBEDDED = \{[^}]*\b16\b", vpk, re.M)


def test_ability_audit_ignores_sub_ability_slugs():
    # audit-live 2026-10-22 failed: sub_ability("rattletrap_jetpack", "Jetpack") was read as ability("rattletrap_jetpack").
    # A stub of Valve's answer: this test ran the live audit, so it failed offline and on any rename on Valve's side
    # (.github/workflows/audit-live.yml runs that one)
    a = _ability_audit()
    src = 'W(hero_header("Clockwerk"))\nW(sub_ability("rattletrap_jetpack", "Jetpack"))\nW(ability("Cogs"))\n'
    calls = a.find_calls([("p9.py", src)])
    assert [c[:2] for c in calls] == [("Clockwerk", "Cogs")]
    assert a.find_problems(calls, {"Clockwerk": {"rattletrap_cogs": "Cogs"}}) == []
    assert a.report([]) == 0


def test_ability_audit_still_reports_a_renamed_ability_and_a_bad_slug(capsys):
    a = _ability_audit()
    src = 'W(hero_header("Axe"))\nW(ability("Old Name", slug="axe_x"))\nW(ability("Lost", slug="axe_lost"))\n'
    problems = a.find_problems(a.find_calls([("p9.py", src)]), {"Axe": {"axe_x": "New Name"}})
    assert [p[6] for p in problems] == ["renamed -> 'New Name'", "slug not in hero's ability list"]
    assert a.report(problems) == 1
    assert "[Axe] 'Old Name' -> 'New Name'" in capsys.readouterr().out


def test_ability_audit_owner_of_a_card_is_the_header_of_its_own_file():
    # Tormentor's cards at the top of p738.py were blamed on the previous file's last hero, Windranger
    a = _ability_audit()
    calls = a.find_calls([("p1.py", 'W(hero_header("Windranger"))\n'),
                          ("p2.py", 'W(ability_change(old=dict(name="A"), new=dict(name="B")))\n')])
    assert calls == []


def test_the_ability_audit_imports_without_the_network():
    assert _ability_audit().HEROLIST.startswith("https://")


def test_a_test_cannot_reach_the_network(no_network):
    from urllib.request import urlopen
    with pytest.raises(OSError):
        urlopen("https://www.dota2.com/", timeout=1)
    assert no_network == ["www.dota2.com"]
    no_network.clear()          # the guard's teardown would fail this test


def test_audit_live_still_runs_the_ability_audit():
    assert "audit_all.py" in (ROOT / ".github" / "workflows" / "audit-live.yml").read_text(encoding="utf-8")
    assert "audit_abilities.py" in (ROOT / "scripts" / "audit" / "audit_all.py").read_text(encoding="utf-8")


def test_from_value_audit_reads_heads_and_facet_values():
    a = _from_audit()
    assert a._norm("20/18/16/14") == (20, 18, 16, 14) and a._norm("14/14/14") == (14,)
    assert a._known((14, 16, 18, 20), {(14, 16, 18, 20, 20)})         # Valve lists 4 of the KV's 5 levels
    assert not a._known((20, 18, 16, 14), {(20, 17, 14, 11)})


def test_from_value_audit_catches_a_stale_value_and_reads_game_names(tmp_path, monkeypatch):
    # Valve's 7.41 Kinetic Fence row without the wrong-word mark; the hero's page id has a hyphen
    # (ancient-apparition) and an item's differs from the game's name (battle-fury = bfury): the header icon names it
    a = _from_audit()
    row = ('<li><span class="row-text">Cooldown decreased from 20/18/16/14s to 14s</span></li>')
    page = ('<div class="entity hero-entity" id="dyn-hero-disruptor"><div class="entity-icon hero-icon">'
            '<img src="../icons/_t/heroes/disruptor.webp"></div></div><h4 class="subgroup">Abilities</h4>'
            '<div class="ability-block"><div class="ability-icon-wrap"><img alt="Kinetic Fence" '
            'class="ability-icon-img" data-slug="disruptor_kinetic_fence"></div><ul class="changes">' + row + '</ul></div>')
    (tmp_path / "7.41.html").write_text(page, encoding="utf-8")
    monkeypatch.setattr(a, "PAGES", tmp_path)
    assert [r[2] for r in a.audit_page("7.41", "7.40c")] == ["disruptor_kinetic_fence"]
    ctx = a._contexts('<div class="entity item-entity" id="dyn-item-battle-fury"><div class="entity-icon item-icon">'
                      '<img src="../icons/_t/items/bfury.webp"></div></div>')
    assert ctx[-1][1] == ("item", "bfury")


@pytest.mark.slow
def test_every_from_value_matches_the_previous_patch():
    # owner 2026-10-22: Valve's "from" can be stale (7.41 Kinetic Fence quoted pre-7.38 20/18/16/14s);
    # such rows carry wrong-word + the real change in a note
    import pytest
    if not (ROOT / "dist" / "patches" / "7.41.html").exists():
        pytest.skip("site not built")
    a = _from_audit()
    vers = a._versions()
    found = [r for v in vers[1:] for r in a.audit_page(v, vers[vers.index(v) - 1])]
    assert found == []
