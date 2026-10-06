"""Rows linked to other entities (li(also_dyn=...) -> data-also) show on those entities' pages (owner 2026-10-06:
the 7.41 lane creep rows sat only in General Updates, the Melee / Ranged / Flagbearer / Siege cards had no page)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders import entity_changes as ec

FLAG = "unit|creep-goodguys-flagbearer"


def _page(*rows):
    return '<h2 class="section" data-section="general">General Updates</h2><ul class="changes">' + "".join(rows) + "</ul>"


def _row(text, keys):
    return f'<li data-tag="buff" data-also="{keys}"><span class="row-text">{text}</span><ul class="subnotes"><li>sub</li></ul></li>'


def _collect(tmp_path, monkeypatch, pages):
    (tmp_path / "patches").mkdir()
    for ver, html in pages.items():
        (tmp_path / "patches" / f"{ver}.html").write_text(html, encoding="utf-8")
    monkeypatch.setattr(ec, "DIST", tmp_path)
    monkeypatch.setattr(ec, "PATCHES", [{"version": v} for v in pages])
    monkeypatch.setattr(ec, "RELEASE_HISTORY", [{"version": v, "date": ""} for v in sorted(pages, reverse=True)])
    return ec._collect()


def test_a_lane_creep_gets_a_page_from_general_rows(tmp_path, monkeypatch):
    ents = _collect(tmp_path, monkeypatch, {
        "9.41": _page(_row("Flagbearer XP 57 to 60", FLAG), '<li><span class="row-text">Roshan</span></li>',
                      _row("Meeting point moved", f"{FLAG} unit|creep-goodguys-melee")),
        "9.40": _page(_row("Flagbearer radius 1200 to 1500", FLAG))})
    flag = ents[("unit", "creep-goodguys-flagbearer")]
    assert flag["name"] == "Flagbearer Creep" and flag["icon"].endswith("npc_dota_creep_goodguys_flagbearer.png")
    assert [p["version"] for p in flag["patches"]] == ["9.41", "9.40"]          # newest first
    body = flag["patches"][0]["body"]
    assert body.count('<h4 class="subgroup">General Updates</h4>') == 1          # one heading per section
    assert "Flagbearer XP" in body and "Meeting point" in body and "Roshan" not in body
    assert body.count("<li") == body.count("</li>") == 4                         # whole rows, sub-notes included
    assert "Meeting point" in ents[("unit", "creep-goodguys-melee")]["patches"][0]["body"]


def test_an_unknown_key_without_a_page_only_feeds_the_squares(tmp_path, monkeypatch):
    ents = _collect(tmp_path, monkeypatch, {"9.41": _page(_row("Skeleton rally", "unit|skeleton-warrior"))})
    assert ("unit", "skeleton-warrior") not in ents
