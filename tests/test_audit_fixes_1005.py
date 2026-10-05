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


def test_silent_pages_use_in_game_names():
    from builders import silent
    assert silent._hero_display("npc_dota_hero_zuus") == "Zeus"
    assert silent._hero_display("npc_dota_hero_nevermore") == "Shadow Fiend"
    assert silent._ability_display("abaddon_aphotic_shield") == "Aphotic Shield"
    assert silent._ability_display("no_such_ability_slug") == "no_such_ability_slug"
