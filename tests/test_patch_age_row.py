"""A patch page says how long after the previous patch it came and how long it ran (or has been live) — one source,
patch/meta._patch_meta_parts, drawn by patch/page.write_head in the toolbar row. A second copy (_patch_age_line ->
.patch-age, with its CSS and a script) was never put on a page; removed 2026-10-27."""
import os

from patch.meta import RELEASE_HISTORY, _parse_date, _patch_meta_parts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_an_older_patch_says_the_gap_and_how_long_it_ran():
    by_date = sorted(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]))
    prev, cur, nxt = by_date[-4], by_date[-3], by_date[-2]
    after, age = _patch_meta_parts(cur["version"])
    gap = (_parse_date(cur["date"]) - _parse_date(prev["date"])).days
    ran = (_parse_date(nxt["date"]) - _parse_date(cur["date"])).days
    assert after == f'<b>{gap}</b> days after <b>{prev["version"]}</b>'
    assert age == f"Ran: <b>{ran}</b> days"


def test_the_newest_patch_says_it_is_live():
    newest = max(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]))
    _, age = _patch_meta_parts(newest["version"])
    assert age.startswith("Live: ") or age == "Released today"


def test_the_unused_second_copy_stays_gone():
    for rel in ("styles.css", os.path.join("src", "scripts.js"), os.path.join("patch", "meta.py")):
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            text = f.read()
        assert "patch-age" not in text and "_patch_age_line" not in text, rel
