"""Fixes from the 2026-10-05 audit, pinned so they don't come back.

- Neutral Abilities tooltips showed Valve's raw "%hero_stun_duration%" / "%damage_pct%%%" (8 tooltips).
- Lone Druid's hero page had an empty "Patch 7.41d" section: that patch changed only the Spirit Bear,
  which is a separate creep-hero block on the patch page.
- Hero Changes (a top-level page) used "../icons/..." for the record-holder faces: 15 broken images live.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders import creeps_abilities as ua
from builders import entity_changes as ec

ROOT = Path(__file__).resolve().parent.parent


def test_placeholders_take_the_ability_values():
    fields = {"av_stun": "1.0 1.5 2.0", "damage_pct": "25"}
    assert ua._fill_placeholders("Stuns for %stun% s.", fields) == "Stuns for 1 / 1.5 / 2 s."
    assert ua._fill_placeholders("Deals %damage_pct%%% more.", fields) == "Deals 25% more."


def test_unknown_placeholder_never_leaks_the_raw_key():
    assert ua._fill_placeholders("Lasts %missing_key% s.", {}) == "Lasts ? s."


def _block(kind, slug, name, body):
    return (f'<div class="entity-block">'
            f'<div class="entity hero-entity" id="dyn-{kind}-{slug}">'
            f'<img src="../icons/{slug}.png" alt="{name}"><div class="entity-name">{name}</div></div>'
            f'<ul><li>{body}</li></ul></div>')


def test_spirit_bear_rows_land_on_lone_druids_patch(tmp_path, monkeypatch):
    (tmp_path / "patches").mkdir()
    page = (_block("hero", "lone-druid", "Lone Druid", "")
            + _block("creep-hero", "spirit-bear", "Spirit Bear", "Bear armor +1"))
    (tmp_path / "patches" / "9.99.html").write_text(page, encoding="utf-8")
    monkeypatch.setattr(ec, "DIST", tmp_path)
    monkeypatch.setattr(ec, "PATCHES", [{"version": "9.99"}])
    monkeypatch.setattr(ec, "RELEASE_HISTORY", [{"version": "9.99", "date": "05.10.2026"}])

    ents = ec._collect()

    druid = ents[("hero", "lone-druid")]["patches"][0]["body"]
    assert "Bear armor +1" in druid
    assert 'class="ec-sub-entity"' in druid
    assert "Bear armor +1" in ents[("creep-hero", "spirit-bear")]["patches"][0]["body"]


def test_a_creep_hero_after_an_item_is_not_folded(tmp_path, monkeypatch):
    (tmp_path / "patches").mkdir()
    page = (_block("hero", "lone-druid", "Lone Druid", "")
            + _block("item", "blink-dagger", "Blink Dagger", "")
            + _block("creep-hero", "spirit-bear", "Spirit Bear", "Bear armor +1"))
    (tmp_path / "patches" / "9.99.html").write_text(page, encoding="utf-8")
    monkeypatch.setattr(ec, "DIST", tmp_path)
    monkeypatch.setattr(ec, "PATCHES", [{"version": "9.99"}])
    monkeypatch.setattr(ec, "RELEASE_HISTORY", [{"version": "9.99", "date": ""}])

    assert "Bear armor" not in ec._collect()[("hero", "lone-druid")]["patches"][0]["body"]


@pytest.mark.parametrize("page", ["hero_changes.html", "item_changes.html", "unit_changes.html"])
def test_top_level_pages_do_not_climb_out_of_the_site(page):
    f = ROOT / "dist" / page
    if not f.exists():
        pytest.skip("dist not built")
    assert 'src="../icons' not in f.read_text(encoding="utf-8")


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
}


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


def test_formula_start_is_the_tables_first_column():
    from patch.badges import bf
    # 7.41 twister: the table starts at Wex level 2, so does "start"
    _, badge, _ = bf(lambda w: 40 + 10 * w, lambda w: 30 + 10 * w, "30 + 10 x Wex Level", levels=list(range(2, 12)))
    assert badge.index(">-17%<") < badge.index(">start<")
    # a caller's own headline column is named, not called "start" (Wisdom Shrine #2)
    _, badge, _ = bf(lambda n: 280 * n, lambda n: 200 + 300 * (n - 1), "x", levels=[1, 2, 3], headline_level=2,
                     level_fmt=lambda n: f"#{n}")
    assert ">#2<" in badge and ">start<" not in badge


def test_nerf_formula_with_green_endpoints_shows_its_worst_level():
    """7.41 Monkey King Mischief: 0% at L1 and -21% (green) at L30 under a NERF tag; L20 is +21% (red)."""
    from patch.badges import bf, rank_step
    _, badge, _ = bf(rank_step([24.0, 20.0, 16.0, 12.0]), lambda L: 24.5 - 0.5 * L, "24.5s - 0.5s per level", l=True)
    assert 'data-force-left="nerf"' in badge
    assert '<span class="badge nerf5">+21%</span><span class="formula-endpoint-label">L20</span>' in badge


def test_every_page_head_has_the_phone_viewport_and_local_fonts():
    import builders.site_common as site
    head = site.head_common("../")
    assert head.count('name="viewport" content="width=device-width, initial-scale=1"') == 1
    for name in site.PRELOAD_FONTS:
        assert f'href="../src/fonts/{name}.woff2" as="font"' in head
        assert (ROOT / "src" / "fonts" / f"{name}.woff2").exists()


def test_no_page_builder_loads_google_fonts_or_the_steam_background():
    srcs = list((ROOT / "builders").glob("*.py")) + list((ROOT / "patch").glob("*.py")) + [ROOT / "styles.css"]
    needles = ("fonts.googleapis", "fonts.gstatic", "dota_react/backgrounds/featured.jpg")
    hits = [f.name for f in srcs if any(n in f.read_text(encoding="utf-8") for n in needles)]
    assert hits == []


def test_self_hosted_font_files_exist():
    import re
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    for path in set(re.findall(r"url\('(src/fonts/[^']+)'\)", css)):
        assert (ROOT / path).exists(), path
    assert (ROOT / "icons" / "ui" / "bg" / "patch_bg.jpg").exists()
